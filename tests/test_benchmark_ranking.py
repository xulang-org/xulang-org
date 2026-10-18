"""Coverage and comparability contracts for the generated benchmark UI."""
from copy import deepcopy
from html import unescape
from html.parser import HTMLParser
import importlib.util
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('benchmarks', ROOT / 'scripts/gen-benchmarks.py')
benchmarks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmarks)


class BarAttributes(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.rows = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get('class', '').split()
        if tag == 'div' and 'bench-bar-fill' in classes:
            self.rows.append(attrs)


def bars(platforms, metric='wall_ms', language='swift', en=False):
    source = benchmarks.render_workload_bars_matrix('startup', platforms, en)
    rows = BarAttributes(source).rows
    panel = next(i for i, cfg in enumerate(benchmarks.BENCH_METRICS_CONFIG) if cfg['key'] == metric)
    selected = rows[panel * 5:(panel + 1) * 5]
    return next(row for row in selected if 'fill-' + language in row['class'].split())


def median_cell(platforms, metric='wall_ms', language='swift', en=False):
    cfg = next(cfg for cfg in benchmarks.BENCH_METRICS_CONFIG if cfg['key'] == metric)
    source = benchmarks.render_workload_metric_table('startup', platforms, cfg, en)
    row = next(row for row in re.findall(r'<tr[^>]*>.*?</tr>', source, re.S)
               if 'bench-bar-lang ' + language + '"' in row)
    return re.search(r'<td[^>]*bench-cell-median[^>]*>.*?</td>', row, re.S)[0]


class BenchmarkRankingTests(unittest.TestCase):
    def fixture(self):
        platforms = {}
        for cfg in benchmarks.PLATFORMS_CONFIG:
            impls = {name: {'wall_ms': val, 'cpu_ms': val, 'rss_mib': val, 'bytes': val * 1024}
                     for name, val in [('Xu', 5), ('clang -O3', 7), ('rustc -O3', 8),
                                       ('swiftc -O', 1), ('go build', 9)]}
            platforms[cfg['id']] = {'benches': [{'name': 'startup', 'implementations': impls}]}
        return platforms

    def test_reported_swift_bug_cannot_win_all_architectures(self):
        # Reproduce the original four-of-six coverage bug independently of
        # the latest published measurements, which change on each release.
        data = self.fixture()
        for pid, wall in [('macos-arm64', 2.9), ('linux-arm64', 2.3),
                          ('macos-x64', 3.1), ('linux-x64', 2.5)]:
            data[pid]['benches'][0]['implementations']['swiftc -O']['wall_ms'] = wall
        for pid in ('windows-arm64', 'windows-x64'):
            data[pid]['benches'][0]['implementations'].pop('swiftc -O')
        row = bars(data)
        self.assertEqual(row['data-pct-all'], '0.0')
        self.assertIn('4/6', row['data-txt-all'])
        self.assertNotIn('bench-bar-badge-best', row['data-txt-all'])
        cell = median_cell(data)
        self.assertIn('4/6', cell)
        self.assertNotIn('bench-cell-best', cell)
        self.assertNotIn('2.70ms', cell)
        self.assertIn('2.90 ms', row['data-txt-macos-arm64'])
        self.assertEqual(row['data-txt-windows-arm64'], '—')

    def test_missing_platform_cannot_shrink_the_required_cohort(self):
        data = self.fixture()
        del data['windows-arm64']
        self.assertIn('5/6', bars(data, language='xu')['data-txt-all'])
        self.assertNotIn('bench-cell-best', median_cell(data, language='xu'))

    def test_all_missing_results_have_no_bar_or_winner(self):
        data = self.fixture()
        for p in data.values():
            p['benches'][0]['implementations'].pop('swiftc -O')
        row = bars(data)
        self.assertEqual(row['data-pct-all'], '0.0')
        self.assertIn('0/6', row['data-txt-all'])
        self.assertNotIn('badge-best', row['data-txt-all'])

    def test_complete_fastest_language_still_wins_both_views(self):
        data = self.fixture()
        self.assertIn('bench-bar-badge-best', bars(data)['data-txt-all'])
        self.assertIn('bench-cell-best', median_cell(data))
        self.assertIn('1.00', bars(data)['data-txt-all'])

    def test_zero_cpu_is_displayed_without_a_bar_ratio_or_best_badge(self):
        data = self.fixture()
        for p in data.values():
            for name, impl in p['benches'][0]['implementations'].items():
                if name != 'go build':
                    impl['cpu_ms'] = 0
        row = bars(data, 'cpu_ms', 'xu')
        self.assertEqual(row['data-pct-windows-arm64'], '0.0')
        self.assertIn('0.00', row['data-txt-windows-arm64'])
        self.assertNotIn('×', row['data-txt-windows-arm64'])
        self.assertNotIn('badge-best', row['data-txt-windows-arm64'])
        self.assertNotIn('badge-best', bars(data, 'cpu_ms', 'go')['data-txt-windows-arm64'])
        self.assertNotIn('bench-cell-best', median_cell(data, 'cpu_ms', 'go'))

    def test_invalid_metrics_are_missing_and_never_ranked(self):
        for invalid in (None, -1, float('nan'), float('inf'), '1.2', True):
            with self.subTest(invalid=invalid):
                b = {'implementations': {'Xu': {'wall_ms': invalid}}}
                self.assertIsNone(benchmarks.get_bench_impl_metric(b, 'Xu', 'wall_ms'))

    def test_selected_c_and_rust_artifacts_match_the_fastest_wall_time(self):
        for lang, prefix in [('c', 'clang'), ('rust', 'rustc')]:
            with self.subTest(lang=lang):
                b = {'implementations': {
                    prefix + ' -O1': {'wall_ms': 2, 'rss_mib': 11},
                    prefix + ' -O2': {'wall_ms': 1, 'rss_mib': 13},
                    prefix + ' -O3': {'wall_ms': 3, 'rss_mib': 7},
                }}
                self.assertEqual(benchmarks.get_bench_impl_metric(b, lang, 'wall_ms'), 1)
                self.assertEqual(benchmarks.get_bench_impl_metric(b, lang, 'rss_mib'), 13)

    def test_incomplete_results_are_excluded_for_each_metric_and_locale(self):
        data = self.fixture()
        del data['windows-x64']['benches'][0]['implementations']['swiftc -O']
        for cfg in benchmarks.BENCH_METRICS_CONFIG:
            for en in (False, True):
                with self.subTest(metric=cfg['key'], en=en):
                    row = bars(data, cfg['key'], en=en)
                    self.assertEqual(row['data-pct-all'], '0.0')
                    self.assertIn('5/6', row['data-txt-all'])
                    self.assertNotIn('badge-best', row['data-txt-all'])
                    self.assertIn('5/6', median_cell(data, cfg['key'], en=en))


if __name__ == '__main__':
    unittest.main()
