#!/usr/bin/env python3
"""Import one complete, identity-verified six-platform Actions benchmark run."""
import argparse
from datetime import date
import json
import math
from pathlib import Path
import re
from sync_all_benches import registered_benches, require_bench_commit
from benchmark_results import FAILURES, METRICS, validate_failure

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ('macos-arm64', 'linux-arm64', 'windows-arm64',
           'macos-x64', 'linux-x64', 'windows-x64')


def positive(value):
    return isinstance(value, (int, float)) and math.isfinite(value) and value > 0


def load(artifacts, version, commit, run_id, measured_date, bench_root=None):
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('website benchmarks must use a final release')
    if not re.fullmatch(r'[0-9a-f]{40}', commit) or not run_id.isdigit():
        raise ValueError('a complete Xu commit and Actions run ID are required')
    date.fromisoformat(measured_date)
    bench_root = Path(bench_root or ROOT.parent / 'bench')
    registered = registered_benches(bench_root)
    platforms, identities = {}, {}
    names = closure = bench_commit = fixed_point = categories = None
    for target in TARGETS:
        folder = artifacts / ('benchmark-reports-' + target)
        identity = json.loads((folder / 'compiler-identity.json').read_text(encoding='utf-8'))
        if (identity['target'] != target or identity['xu_commit'] != commit
                or identity['xu_version'] != version
                or identity['fixed_point_pair'] not in ('gen2_gen3', 'gen3_gen4')):
            raise ValueError(f'{target}: compiler identity mismatch')
        for field, width in [('source_closure_sha256', 64), ('compiler_sha256', 64),
                             ('bench_commit', 40)]:
            if not re.fullmatch(r'[0-9a-f]{' + str(width) + '}', identity[field]):
                raise ValueError(f'{target}: missing {field}')
        closure = closure or identity['source_closure_sha256']
        bench_commit = bench_commit or identity['bench_commit']
        fixed_point = fixed_point or identity['fixed_point_pair']
        if names is None:
            require_bench_commit(bench_root, bench_commit)
        if (closure != identity['source_closure_sha256'] or bench_commit != identity['bench_commit']
                or fixed_point != identity['fixed_point_pair']):
            raise ValueError(f'{target}: mixed source closures, benchmark commits or bootstrap fixed points')
        data = json.loads((folder / f'benchmarks-{target}.json').read_text(encoding='utf-8'))
        meta = data['metadata']
        if meta['xu_version'] != version or meta['platform_id'] != target:
            raise ValueError(f'{target}: result identity mismatch')
        raw = (folder / 'crosslang.txt').read_text(encoding='utf-8')
        toolchains = meta.get('toolchains')
        if not isinstance(toolchains, dict):
            raise ValueError(f'{target}: missing measured toolchain versions')
        for name in ('clang', 'rustc', 'go', 'swiftc'):
            match = re.search(r'^# ' + name + r': (.+)$', raw, re.M)
            actual = match.group(1).strip() if match else None
            if toolchains.get(name) != actual:
                raise ValueError(f'{target}: {name} version differs from measurement log')
            if actual is None:
                labels = {'clang': 'clang ', 'rustc': 'rustc ', 'go': 'go build', 'swiftc': 'swiftc '}
                if any(any(impl.startswith(labels[name]) for impl in item['implementations'])
                       for item in data['benches']):
                    raise ValueError(f'{target}: measured {name} without a version')
        current = [item['name'] for item in data['benches']]
        if tuple(current) != registered:
            raise ValueError(f'{target}: workload matrix differs from the full registered suite')
        names = names or current
        if current != names or len(set(current)) != len(current) or len(current) != meta['total_benches']:
            raise ValueError(f'{target}: incomplete workload matrix')
        records = {}
        for encoded in re.findall(r'^# result: (.+)$', raw, re.M):
            record = json.loads(encoded)
            pair = (record.pop('bench'), record.pop('impl'))
            if pair in records:
                raise ValueError(f'{target}: duplicate runtime outcome')
            validate_failure(record)
            records[pair] = record
        if records and set(records) != {(b['name'], label) for b in data['benches'] for label in b['implementations']}:
            raise ValueError(f'{target}: incomplete runtime implementation outcomes')
        verified = re.findall(r'^Xu\s+(\S+)\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+\d+\s+OK\b', raw, re.M)
        successful = [b['name'] for b in data['benches'] if b.get('xu_status', 'ok') == 'ok']
        if sorted(verified) != sorted(successful):
            raise ValueError(f'{target}: missing verified stdout')
        for item in data['benches']:
            impls = item['implementations']
            status = item.get('xu_status', 'ok')
            for label, result in impls.items():
                validate_failure(result)
                if records and records.get((item['name'], label)) != result:
                    raise ValueError(f'{target}/{item["name"]}: {label} differs from runtime evidence')
            xu = impls['Xu']
            if xu.get('status', 'ok') != status:
                raise ValueError(f'{target}/{item["name"]}: Xu outcome mismatch')
            if status == 'ok':
                if not positive(xu['wall_ms']) or xu['wall_ms'] != item['xu_wall_ms']:
                    raise ValueError(f'{target}/{item["name"]}: invalid Xu median')
            else:
                if (not records or status not in FAILURES or item.get('xu_error') != xu.get('error')
                        or any(item.get('xu_' + key) is not None for key in METRICS)):
                    raise ValueError(f'{target}/{item["name"]}: unverified or measured Xu failure')
            for prefix, key in [('clang', 'c'), ('rustc', 'rust')]:
                choices = [(name, impls[name]['wall_ms']) for name in
                           (f'{prefix} -O{i}' for i in (1, 2, 3))
                           if name in impls and positive(impls[name].get('wall_ms'))]
                chosen = min(choices, key=lambda pair: pair[1]) if choices else (None, None)
                item[key + '_implementation'], item[key + '_wall_ms'] = chosen
            for name, key in [('go build', 'go'), ('swiftc -O', 'swift')]:
                item[key + '_wall_ms'] = impls.get(name, {}).get('wall_ms')
            for key in ('c', 'rust', 'go', 'swift'):
                peer = item[key + '_wall_ms']
                item['ratio_vs_' + key] = item['xu_wall_ms'] / peer if positive(item['xu_wall_ms']) and positive(peer) else None
        rss_validated = not target.startswith('linux-') or meta.get('rss_method') == 'linux-post-exec-vmhwm-v1'
        footprint = []
        for impl, label in [('Xu', 'Xu'), ('clang -O3', 'Clang -O3'),
                            ('rustc -O3', 'rustc -O3'), ('swiftc -O', 'Swift -O'),
                            ('go build', 'Go build')]:
            samples = [b['implementations'][impl] for b in data['benches'] if impl in b['implementations']]
            if not samples:
                continue
            record = {'impl': label}
            for source, key, scale in [('rss_mib', 'rss', 1), ('bytes', 'size', 1024)]:
                values = [s[source] / scale for s in samples if positive(s.get(source))]
                if values and (key != 'rss' or rss_validated):
                    record[key] = f'{min(values):.2f} – {max(values):.2f}'
            footprint.append(record)
        failed = len(current) - len(successful)
        if meta.get('xu_failed_benches', failed) != failed:
            raise ValueError(f'{target}: wrong failure count')
        platforms[target] = {**meta, 'xu_failed_benches': failed, 'rss_validated': rss_validated,
                             'rss_note': '' if rss_validated else 'Invalid legacy wait4 peak includes launcher memory; pending retest',
                             'benches': data['benches'], 'footprint': footprint}
        identities[target] = identity
        categories = categories or data['categories']
        if categories != data['categories']:
            raise ValueError(f'{target}: mixed category definitions')
    return {'metadata': {'date': measured_date, 'xu_version': version, 'xu_commit': commit,
                         'bench_commit': bench_commit, 'source_closure_sha256': closure,
                         'fixed_point_pair': fixed_point,
                         'run_url': f'https://github.com/xulang-org/bench/actions/runs/{run_id}',
                         'platforms': list(TARGETS), 'total_benches': len(names),
                         'xu_failed_cases': sum(p['xu_failed_benches'] for p in platforms.values()),
                         'methodology': '7 whole-program wall-time samples; median; verified stdout; '
                                        'Xu / minimum same-platform clang/rustc O1/O2/O3 median'},
            'default_platform': 'macos-arm64', 'categories': categories,
            'compiler_identities': identities, 'platforms': platforms,
            'benches': platforms['macos-arm64']['benches']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts', required=True, type=Path)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--date', required=True, help='Actions run date (YYYY-MM-DD)')
    parser.add_argument('--bench-root', type=Path, help='checkout pinned to the measured bench_commit')
    args = parser.parse_args()
    data = load(args.artifacts, (ROOT / 'VERSION').read_text(encoding='utf-8').strip(),
                args.commit, args.run_id, args.date, args.bench_root)
    (ROOT / 'www/benchmarks.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Imported {data["metadata"]["total_benches"]} workloads × {len(TARGETS)} verified platforms')


if __name__ == '__main__':
    main()
