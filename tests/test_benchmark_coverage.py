"""The website must keep every canonical workload in a measured suite."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('benchmark_sync', ROOT / 'scripts/sync_all_benches.py')
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)
spec = importlib.util.spec_from_file_location('benchmark_import', ROOT / 'scripts/import-benchmarks.py')
importer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(importer)


class BenchmarkCoverageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'bench'
        (self.repo / 'scripts').mkdir(parents=True)
        (self.repo / 'tests/bench/cross').mkdir(parents=True)
        self.names = ['startup', 'fib', 'osprey_fib', 'http_concurrent']
        self.registry = self.repo / 'scripts/bench_crosslang.py'
        self.registry.write_text('raise RuntimeError("do not execute the registry")\n'
                                 'BENCHES: list[Bench] = [\n' + ''.join(
                                     f'    Bench({name!r}, "", "fixture", CORE),\n'
                                     for name in self.names) + ']\n')
        self.source = '// Osprey original workload; see tests/bench/osprey/README.md.\n@main\n'
        for name in self.names:
            (self.repo / f'tests/bench/{name}.xu').write_text(self.source + '// ' + name + '\n')
            for ext in ('go', 'c', 'rs', 'swift'):
                (self.repo / f'tests/bench/cross/{name}.{ext}').write_text('// ' + name + '\n')
        self.data = {
            'metadata': {'total_benches': len(self.names)},
            'benches': [{'name': name} for name in self.names],
            'platforms': {target: {'benches': [{'name': name} for name in self.names]}
                          for target in ('macos-arm64', 'linux-arm64', 'windows-arm64',
                                         'macos-x64', 'linux-x64', 'windows-x64')},
        }
        self.data_file = self.root / 'benchmarks.json'
        self.data_file.write_text(json.dumps(self.data))
        self.sources = self.root / 'bench_sources.json'

    def export(self):
        with patch.multiple(sync, BENCH_REPO=self.repo, SOURCES_FILE=self.sources,
                            DATA_FILE=self.data_file, create=True), \
             patch.multiple(sync, BENCH_TESTS_DIR=self.repo / 'tests/bench',
                            CROSS_DIR=self.repo / 'tests/bench/cross', create=True):
            sync.sync_sources()
        return json.loads(self.sources.read_text())

    def test_exports_every_registered_case_without_aliasing_similar_workloads(self):
        sources = self.export()
        self.assertEqual(list(sources), self.names)
        self.assertNotEqual(sources['fib']['xu'], sources['osprey_fib']['xu'])

    def test_export_preserves_measured_data_and_upstream_source_provenance(self):
        before = self.data_file.read_bytes()
        sources = self.export()
        self.assertEqual(self.data_file.read_bytes(), before)
        self.assertEqual(sources['osprey_fib']['xu'], self.source + '// osprey_fib\n')

    def test_rejects_a_cohort_that_silently_drops_a_registered_case(self):
        reduced = deepcopy(self.data)
        reduced['metadata']['total_benches'] -= 1
        reduced['benches'].pop(0)
        for platform in reduced['platforms'].values():
            platform['benches'].pop(0)
        self.data_file.write_text(json.dumps(reduced))
        with self.assertRaisesRegex(ValueError, 'workload'):
            self.export()
        self.assertFalse(self.sources.exists())

    def test_rejects_one_incomplete_platform(self):
        self.data['platforms']['windows-arm64']['benches'].pop()
        self.data_file.write_text(json.dumps(self.data))
        with self.assertRaisesRegex(ValueError, 'windows-arm64'):
            self.export()

    def test_missing_registered_source_fails_before_overwriting_the_export(self):
        self.sources.write_text('previous verified export')
        (self.repo / 'tests/bench/osprey_fib.xu').unlink()
        with self.assertRaisesRegex(ValueError, 'osprey_fib'):
            self.export()
        self.assertEqual(self.sources.read_text(), 'previous verified export')

    def test_duplicate_registry_ids_are_rejected(self):
        self.registry.write_text('BENCHES = [Bench("fib", "", "", CORE), Bench("fib", "", "", CORE)]')
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            self.export()

    def measured_artifacts(self, names):
        artifacts = self.root / 'artifacts'
        for target in sync.TARGETS:
            folder = artifacts / ('benchmark-reports-' + target)
            folder.mkdir(parents=True)
            identity = {'target': target, 'xu_commit': 'a' * 40, 'bench_commit': 'b' * 40,
                        'xu_version': '0.11.2', 'fixed_point_pair': 'gen2_gen3',
                        'source_closure_sha256': 'c' * 64, 'compiler_sha256': 'd' * 64}
            (folder / 'compiler-identity.json').write_text(json.dumps(identity))
            metadata = {'platform_id': target, 'xu_version': '0.11.2', 'total_benches': len(names),
                        'toolchains': {name: None for name in ('clang', 'rustc', 'go', 'swiftc')}}
            rows = [{'name': name, 'xu_wall_ms': 1,
                     'implementations': {'Xu': {'wall_ms': 1, 'rss_mib': 1, 'bytes': 100}}}
                    for name in names]
            (folder / f'benchmarks-{target}.json').write_text(json.dumps(
                {'metadata': metadata, 'benches': rows, 'categories': {}}))
            (folder / 'crosslang.txt').write_text(''.join(
                f'Xu {name} 1.0 1.0 1.0 1.0 100 OK\n' for name in names))
        return artifacts

    def test_import_preserves_the_complete_six_platform_registry(self):
        with patch.object(importer, 'require_bench_commit') as check_commit:
            data = importer.load(self.measured_artifacts(self.names), '0.11.2', 'a' * 40,
                                 '123', '2026-11-02', self.repo)
        check_commit.assert_called_once_with(self.repo, 'b' * 40)
        self.assertEqual([row['name'] for row in data['benches']], self.names)

    def test_import_rejects_matching_platforms_that_all_omit_the_same_workload(self):
        with patch.object(importer, 'require_bench_commit'), self.assertRaisesRegex(ValueError, 'full registered'):
            importer.load(self.measured_artifacts(self.names[1:]), '0.11.2', 'a' * 40,
                          '123', '2026-11-02', self.repo)

    def failure_artifacts(self):
        artifacts = self.measured_artifacts(self.names)
        target = 'macos-arm64'
        folder = artifacts / ('benchmark-reports-' + target)
        path = folder / f'benchmarks-{target}.json'
        data = json.loads(path.read_text())
        row = data['benches'][1]
        failure = dict(status='compile_failed', error='index out of bounds')
        row.update(xu_status='compile_failed', xu_error=failure['error'], xu_wall_ms=None)
        row['implementations']['Xu'] = failure
        path.write_text(json.dumps(data))
        raw = ''.join(f'Xu {name} 1.0 1.0 1.0 1.0 100 OK\n' for name in self.names if name != row['name'])
        raw += '\n'.join('# result: ' + json.dumps(dict(bench=b['name'], impl='Xu', **b['implementations']['Xu']))
                         for b in data['benches'])
        (folder / 'crosslang.txt').write_text(raw)
        return artifacts, path

    def test_import_retains_raw_evidenced_failures_without_metrics(self):
        artifacts, _ = self.failure_artifacts()
        with patch.object(importer, 'require_bench_commit'):
            data = importer.load(artifacts, '0.11.2', 'a' * 40, '123', '2026-11-02', self.repo)
        row = data['benches'][1]
        self.assertEqual([b['name'] for b in data['benches']], self.names)
        self.assertEqual(row['xu_status'], 'compile_failed')
        self.assertIsNone(row['xu_wall_ms'])
        self.assertIsNone(row['ratio_vs_c'])
        self.assertEqual(data['metadata']['xu_failed_cases'], 1)

    def test_import_rejects_failure_without_matching_raw_evidence(self):
        artifacts, path = self.failure_artifacts()
        data = json.loads(path.read_text())
        data['benches'][1]['implementations']['Xu']['error'] = 'different error'
        path.write_text(json.dumps(data))
        with patch.object(importer, 'require_bench_commit'), self.assertRaisesRegex(ValueError, 'runtime evidence'):
            importer.load(artifacts, '0.11.2', 'a' * 40, '123', '2026-11-02', self.repo)

    def test_import_rejects_metrics_attached_to_failure(self):
        artifacts, path = self.failure_artifacts()
        data = json.loads(path.read_text())
        data['benches'][1]['xu_wall_ms'] = 0.1
        path.write_text(json.dumps(data))
        with patch.object(importer, 'require_bench_commit'), self.assertRaisesRegex(ValueError, 'measured Xu failure'):
            importer.load(artifacts, '0.11.2', 'a' * 40, '123', '2026-11-02', self.repo)


if __name__ == '__main__':
    unittest.main()
