#!/usr/bin/env python3
"""Import one complete, identity-verified six-platform Actions benchmark run."""
import argparse
from datetime import date
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ('macos-arm64', 'linux-arm64', 'windows-arm64',
           'macos-x64', 'linux-x64', 'windows-x64')


def positive(value):
    return isinstance(value, (int, float)) and math.isfinite(value) and value > 0


def load(artifacts, version, commit, run_id, measured_date):
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('website benchmarks must use a final release')
    if not re.fullmatch(r'[0-9a-f]{40}', commit) or not run_id.isdigit():
        raise ValueError('a complete Xu commit and Actions run ID are required')
    date.fromisoformat(measured_date)
    platforms, identities = {}, {}
    names = closure = bench_commit = categories = None
    for target in TARGETS:
        folder = artifacts / ('benchmark-reports-' + target)
        identity = json.loads((folder / 'compiler-identity.json').read_text())
        if (identity['target'] != target or identity['xu_commit'] != commit
                or identity['xu_version'] != version
                or identity['fixed_point_pair'] != 'gen2_gen3'):
            raise ValueError(f'{target}: compiler identity mismatch')
        for field, width in [('source_closure_sha256', 64), ('compiler_sha256', 64),
                             ('bench_commit', 40)]:
            if not re.fullmatch(r'[0-9a-f]{' + str(width) + '}', identity[field]):
                raise ValueError(f'{target}: missing {field}')
        closure = closure or identity['source_closure_sha256']
        bench_commit = bench_commit or identity['bench_commit']
        if closure != identity['source_closure_sha256'] or bench_commit != identity['bench_commit']:
            raise ValueError(f'{target}: mixed source closures or benchmark commits')
        data = json.loads((folder / f'benchmarks-{target}.json').read_text())
        meta = data['metadata']
        if meta['xu_version'] != version or meta['platform_id'] != target:
            raise ValueError(f'{target}: result identity mismatch')
        current = [item['name'] for item in data['benches']]
        names = names or current
        if current != names or len(set(current)) != len(current) or len(current) != meta['total_benches']:
            raise ValueError(f'{target}: incomplete workload matrix')
        verified = re.findall(r'^Xu\s+(\S+)\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+\d+\s+OK\b',
                              (folder / 'crosslang.txt').read_text(), re.M)
        if sorted(verified) != sorted(current):
            raise ValueError(f'{target}: missing verified stdout')
        for item in data['benches']:
            impls = item['implementations']
            if not positive(impls['Xu']['wall_ms']) or impls['Xu']['wall_ms'] != item['xu_wall_ms']:
                raise ValueError(f'{target}/{item["name"]}: invalid Xu median')
            for prefix, key in [('clang', 'c'), ('rustc', 'rust')]:
                choices = [(name, impls[name]['wall_ms']) for name in
                           (f'{prefix} -O{i}' for i in (1, 2, 3))
                           if name in impls and positive(impls[name]['wall_ms'])]
                chosen = min(choices, key=lambda pair: pair[1]) if choices else (None, None)
                item[key + '_implementation'], item[key + '_wall_ms'] = chosen
            for name, key in [('go build', 'go'), ('swiftc -O', 'swift')]:
                item[key + '_wall_ms'] = impls.get(name, {}).get('wall_ms')
            for key in ('c', 'rust', 'go', 'swift'):
                peer = item[key + '_wall_ms']
                item['ratio_vs_' + key] = item['xu_wall_ms'] / peer if positive(peer) else None
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
        platforms[target] = {**meta, 'rss_validated': rss_validated,
                             'rss_note': '' if rss_validated else 'Invalid legacy wait4 peak includes launcher memory; pending retest',
                             'benches': data['benches'], 'footprint': footprint}
        identities[target] = identity
        categories = categories or data['categories']
        if categories != data['categories']:
            raise ValueError(f'{target}: mixed category definitions')
    return {'metadata': {'date': measured_date, 'xu_version': version, 'xu_commit': commit,
                         'bench_commit': bench_commit, 'source_closure_sha256': closure,
                         'run_url': f'https://github.com/xulang-org/bench/actions/runs/{run_id}',
                         'platforms': list(TARGETS), 'total_benches': len(names),
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
    args = parser.parse_args()
    data = load(args.artifacts, (ROOT / 'VERSION').read_text().strip(),
                args.commit, args.run_id, args.date)
    (ROOT / 'www/benchmarks.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print(f'Imported {data["metadata"]["total_benches"]} workloads × {len(TARGETS)} verified platforms')


if __name__ == '__main__':
    main()
