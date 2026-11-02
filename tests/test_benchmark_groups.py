"""Presentation grouping must preserve every variant's identity and results."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from benchmark_groups import group_workloads, platform_groups

spec = importlib.util.spec_from_file_location('grouped_benchmarks', ROOT / 'scripts/gen-benchmarks.py')
benchmarks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmarks)


class BenchmarkGroupTests(unittest.TestCase):
    def test_cross_category_family_preserves_rows_and_singletons(self):
        rows = [dict(name='fib', category='control'), dict(name='startup', category='control'),
                dict(name='osprey_fib', category='algo')]
        original = deepcopy(rows)
        groups = group_workloads(rows)
        self.assertEqual([g['id'] for g in groups], ['fibonacci', 'startup'])
        self.assertEqual(groups[0]['category'], 'control')
        self.assertEqual([v['bench']['name'] for v in groups[0]['variants']], ['fib', 'osprey_fib'])
        self.assertIs(groups[0]['variants'][1]['bench'], rows[2])
        self.assertEqual(rows, original)

    def test_all_measured_variants_are_rendered_once_with_their_own_metrics(self):
        data = json.loads((ROOT / 'www/benchmarks.json').read_text())
        original = deepcopy(data)
        rows = next(iter(data['platforms'].values()))['benches']
        expected = {b['name'] for b in rows}
        groups = platform_groups(data['platforms'])
        self.assertEqual(len(groups), 60)
        self.assertEqual(sum(len(g['variants']) for g in groups), len(expected))
        for en in (True, False):
            sections = ''.join(benchmarks.render_category_integrated_section(c, data['platforms'], en)
                               for c in benchmarks.CATEGORIES_CONFIG)
            ids = re.findall(r'id="workload-([^"]+)"', sections)
            self.assertEqual(len(ids), len(expected))
            self.assertEqual(set(ids), expected)
            self.assertEqual(sections.count('<details class="bench-workload-group"'), 7)
            self.assertIn('id="group-fibonacci"', sections)
            self.assertIn('fib(34)', sections)
            self.assertIn('fib(35)', sections)
            for name in expected:
                # Compare with the existing per-case renderer: no pooling or alias lookup.
                self.assertIn(benchmarks.render_workload_metric_table(name, data['platforms'],
                              benchmarks.BENCH_METRICS_CONFIG[0], en), sections)
                self.assertIn(f"openBenchCodeModal('{name}',", sections)
        self.assertEqual(data, original)

    def test_partial_family_does_not_invent_measurements(self):
        groups = group_workloads([dict(name='osprey_fib', category='algo')])
        self.assertEqual(len(groups), 1)
        self.assertEqual([v['bench']['name'] for v in groups[0]['variants']], ['osprey_fib'])
