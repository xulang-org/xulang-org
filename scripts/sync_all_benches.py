#!/usr/bin/env python3
"""Export every canonical workload's source without rewriting measurements."""
import argparse
import ast
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BENCH_REPO = ROOT.parent / 'bench'
DATA_FILE = ROOT / 'www/benchmarks.json'
SOURCES_FILE = ROOT / 'www/bench_sources.json'
TARGETS = ('macos-arm64', 'linux-arm64', 'windows-arm64',
           'macos-x64', 'linux-x64', 'windows-x64')


def registered_benches(bench_root: Path) -> tuple[str, ...]:
    """Read the pinned suite's registry as data, without executing its imports."""
    source = bench_root / 'scripts/bench_crosslang.py'
    tree = ast.parse(source.read_text(encoding='utf-8'), filename=str(source))
    values = []
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
        if any(isinstance(target, ast.Name) and target.id == 'BENCHES' for target in targets):
            values.append(node.value)
    if len(values) != 1 or not isinstance(values[0], (ast.List, ast.Tuple)):
        raise ValueError('expected one explicit BENCHES workload registry')
    names = []
    for item in values[0].elts:
        if not isinstance(item, ast.Call) or not isinstance(item.func, ast.Name) or item.func.id != 'Bench' or not item.args:
            raise ValueError('invalid entry in BENCHES workload registry')
        name = ast.literal_eval(item.args[0])
        if not isinstance(name, str) or not re.fullmatch(r'[a-z][a-z0-9_]*', name):
            raise ValueError(f'invalid workload name: {name!r}')
        if name in names:
            raise ValueError(f'duplicate workload: {name}')
        names.append(name)
    if not names:
        raise ValueError('empty workload registry')
    return tuple(names)


def require_bench_commit(bench_root: Path, expected: str):
    actual = subprocess.check_output(['git', '-C', str(bench_root), 'rev-parse', 'HEAD'], text=True).strip()
    if actual != expected:
        raise ValueError(f'benchmark source commit mismatch: expected {expected}, got {actual}; use a pinned checkout')


def validate_dataset(data: dict, names):
    """All six platforms must preserve the registry's distinct workload IDs."""
    names = tuple(names)
    if not names or len(set(names)) != len(names):
        raise ValueError('empty or duplicate workload catalog')
    if data['metadata']['total_benches'] != len(names):
        raise ValueError('benchmark workload count differs from the full registry')
    if tuple(row['name'] for row in data['benches']) != names:
        raise ValueError('benchmark workload list differs from the full registry')
    if set(data['platforms']) != set(TARGETS):
        raise ValueError('benchmark workload matrix requires all six platforms')
    for target in TARGETS:
        if tuple(row['name'] for row in data['platforms'][target]['benches']) != names:
            raise ValueError(f'{target}: benchmark workload list differs from the full registry')


def sync_sources(bench_root=None, sources_file=None, data_file=None, check=False):
    bench_root = Path(bench_root or BENCH_REPO)
    sources_file = Path(sources_file or SOURCES_FILE)
    data_file = Path(data_file or DATA_FILE)
    names = registered_benches(bench_root)
    data = json.loads(data_file.read_text(encoding='utf-8'))
    validate_dataset(data, names)
    if commit := data['metadata'].get('bench_commit'):
        require_bench_commit(bench_root, commit)
    sources = {}
    base = bench_root / 'tests/bench'
    for name in names:
        xu = base / (name + '.xu')
        if not xu.is_file():
            raise ValueError(f'{name}: registered Xu workload source is missing')
        ports = {'xu': xu.read_text(encoding='utf-8')}
        for language, extension in [('c', 'c'), ('rust', 'rs'), ('go', 'go'), ('swift', 'swift')]:
            path = base / 'cross' / (name + '.' + extension)
            if path.is_file():
                ports[language] = path.read_text(encoding='utf-8')
        sources[name] = ports
    if check:
        if json.loads(sources_file.read_text(encoding='utf-8')) != sources:
            raise ValueError('exported benchmark sources differ from the pinned full registry')
    else:
        sources_file.write_text(json.dumps(sources, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Verified {len(names)} canonical workloads; measurement data preserved')
    return sources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bench-root', type=Path, default=BENCH_REPO, help='checkout pinned to the measured bench_commit')
    parser.add_argument('--data', type=Path, default=DATA_FILE)
    parser.add_argument('--sources', type=Path, default=SOURCES_FILE)
    parser.add_argument('--check', action='store_true', help='verify the source export without writing it')
    args = parser.parse_args()
    sync_sources(args.bench_root, args.sources, args.data, args.check)


if __name__ == '__main__':
    main()
