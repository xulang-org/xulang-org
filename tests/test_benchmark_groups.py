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
        self.assertEqual(len(groups), len(group_workloads(rows)))
        self.assertEqual(len(groups), 102)
        self.assertEqual(sum(len(g['variants']) for g in groups), len(expected))
        multi_count = sum(1 for g in groups if len(g['variants']) > 1)
        for en in (True, False):
            sections = ''.join(benchmarks.render_category_integrated_section(c, data['platforms'], en)
                               for c in benchmarks.CATEGORIES_CONFIG)
            ids = re.findall(r'id="workload-([^"]+)"', sections)
            self.assertEqual(len(ids), len(expected))
            self.assertEqual(set(ids), expected)
            self.assertEqual(sections.count('<details class="bench-workload-group"'), multi_count)
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

    def test_failures_remain_visible_and_are_excluded_from_metrics(self):
        data = json.loads((ROOT / 'www/benchmarks.json').read_text())
        platform = data['platforms']['macos-arm64']
        prior_failures = sum(b.get('xu_status', 'ok') != 'ok' for p in data['platforms'].values() for b in p['benches'])
        row = next(b for b in platform['benches'] if b['name'] == 'fib')
        row.update(xu_status='compile_failed', xu_error='<script>bad</script>', xu_wall_ms=None)
        row['implementations']['Xu'] = dict(status='compile_failed', error=row['xu_error'], wall_ms=0.01)
        self.assertIsNone(benchmarks.get_bench_impl_metric(row, 'Xu', 'wall_ms'))
        for en in (True, False):
            section = benchmarks.render_category_integrated_section(benchmarks.CATEGORIES_CONFIG[0], data['platforms'], en)
            self.assertIn('id="workload-fib"', section)
            self.assertIn('Compile failed' if en else '编译失败', section)
            self.assertIn('&lt;script&gt;bad&lt;/script&gt;', section)
            self.assertNotIn('<script>bad</script>', section)
            notice = benchmarks.render_outcome_summary(data['platforms'], en)
            self.assertIn(f'data-failed-count="{prior_failures + 1}"', notice)
        # The entire page, including coverage/footprint/metadata, accepts a
        # genuine null-metric failure rather than dropping it or crashing.
        row['implementations']['Xu'].pop('wall_ms')
        for lang in ('en', 'zh'):
            page = benchmarks.render_page(data, lang)
            self.assertIn('id="workload-fib"', page)
            self.assertNotIn('bench-radar-svg', page)

    def test_extended_suite_families_group_without_pooling(self):
        data = json.loads((ROOT / 'www/benchmarks.json').read_text(encoding='utf-8'))
        rows = deepcopy(next(iter(data['platforms'].values()))['benches'])
        extra = [
            ('avl_tree', 'data'), ('chacha20_stream', 'crypto'), ('huffman_coding', 'algo'),
            ('json_tokenizer', 'string'), ('lzw_codec', 'string'),
            ('plb2_nqueen', 'algo'), ('plb2_sudoku', 'algo'), ('plb2_bedcov', 'data'),
            ('thread_ring', 'concurrency'), ('skynet', 'concurrency'),
            ('scimark_montecarlo', 'algo'), ('scimark_sor', 'algo'), ('scimark_lu', 'algo'),
            ('scimark_sparse', 'algo'), ('scimark_fft', 'algo'),
            ('awfy_richards', 'control'), ('awfy_json_parser', 'string'), ('brainfuck_vm', 'control'),
            ('regex_nfa', 'string'), ('treap_ops', 'data'), ('astar_maze', 'algo'),
            ('levenshtein_dp', 'string'), ('csv_aggregate', 'string'),
        ]
        existing = {r['name'] for r in rows}
        for name, category in extra:
            if name not in existing:
                rows.append({'name': name, 'category': category, 'desc_en': name, 'desc_zh': name})
                existing.add(name)
        groups = group_workloads(rows)
        self.assertGreaterEqual(len(groups), 76)
        self.assertEqual(sum(len(g['variants']) for g in groups), len(rows))
        multi = {g['id']: [v['bench']['name'] for v in g['variants']] for g in groups if len(g['variants']) > 1}
        self.assertGreaterEqual(len(multi), 11)
        self.assertEqual(multi['plb2-backtracking'], ['plb2_nqueen', 'plb2_sudoku'])
        self.assertEqual(
            multi['scimark2'],
            ['scimark_montecarlo', 'scimark_sor', 'scimark_lu', 'scimark_sparse', 'scimark_fft'],
        )
        self.assertEqual(multi['balanced-trees'], ['avl_tree', 'treap_ops'])
        self.assertEqual(multi['json-processing'], ['json_tokenizer', 'awfy_json_parser'])

    def test_category_descriptions_track_present_workloads(self):
        by_key = {cfg['key']: cfg for cfg in benchmarks.CATEGORIES_CONFIG}
        algo_base_en = benchmarks.render_category_desc(by_key['algo'], {'matmul', 'sort_lcg'}, True)
        self.assertNotIn('SciMark2', algo_base_en)
        algo_ext_en = benchmarks.render_category_desc(by_key['algo'], {'matmul', 'scimark_fft'}, True)
        self.assertIn('SciMark2', algo_ext_en)

        ctrl_base_zh = benchmarks.render_category_desc(by_key['control'], {'startup', 'fib'}, False)
        self.assertNotIn('Richards', ctrl_base_zh)
        ctrl_ext_zh = benchmarks.render_category_desc(by_key['control'], {'startup', 'awfy_richards'}, False)
        self.assertIn('Richards', ctrl_ext_zh)

        conc_base_en = benchmarks.render_category_desc(by_key['concurrency'], {'chan_ping'}, True)
        self.assertNotIn('thread_ring', conc_base_en)
        conc_ext_en = benchmarks.render_category_desc(by_key['concurrency'], {'chan_ping', 'thread_ring'}, True)
        self.assertIn('thread_ring', conc_ext_en)

    def test_eleven_domain_taxonomy_and_interactive_ui_controls(self):
        self.assertEqual(benchmarks.CATEGORIES_CONFIG[0]['key'], 'control')
        keys = [cfg['key'] for cfg in benchmarks.CATEGORIES_CONFIG]
        self.assertEqual(len(keys), 11)
        self.assertEqual(len(set(keys)), 11)
        for req in ('web', 'storage', 'systems', 'graphics', 'ai', 'crypto', 'concurrency'):
            self.assertIn(req, keys)

        data = json.loads((ROOT / 'www/benchmarks.json').read_text(encoding='utf-8'))
        for lang in ('en', 'zh'):
            page = benchmarks.render_page(data, lang)
            self.assertIn('data-cat="all"', page)
            self.assertIn('id="bench-domain-directory"', page)
            self.assertIn('id="bench-compact-btn"', page)
            self.assertIn('id="bench-groups-toggle-btn"', page)
            self.assertIn('id="bench-filter-status"', page)
            self.assertIn('id="bench-workloads-root"', page)
            self.assertIn('id="bench-empty-state"', page)
            for ck in ('control', 'algo', 'data', 'string', 'crypto', 'concurrency'):
                self.assertIn(f'class="bench-cat-section bench-sec-{ck}" id="cat-{ck}" data-category="{ck}"', page)
                self.assertIn(f'onclick="selectBenchCategory(\'{ck}\', true)"', page)

    def test_web_domain_and_hmac_renders_cleanly_when_present(self):
        data = json.loads((ROOT / 'www/benchmarks.json').read_text(encoding='utf-8'))
        sample = deepcopy(data)
        base_categories = {'control', 'algo', 'data', 'string', 'crypto', 'concurrency'}
        for p in sample['platforms'].values():
            p['benches'] = [
                b for b in p['benches']
                if b['category'] in base_categories and b['name'] not in ('hmac_pbkdf2', 'x25519_dh')
            ]
            p['benches'].append({
                'name': 'http_router_parse',
                'desc_zh': 'HTTP/1.1 解析与 Trie 动态路由',
                'desc_en': 'HTTP/1.1 parsing & trie router',
                'category': 'web',
                'xu_status': 'ok',
                'xu_wall_ms': 12.0,
                'xu_bytes': 40960,
                'implementations': {'Xu': {'wall_ms': 12.0, 'best_ms': 11.5, 'rss_mib': 4.0, 'cpu_ms': 10.0, 'bytes': 40960}},
            })
            p['benches'].append({
                'name': 'hmac_pbkdf2',
                'desc_zh': 'HMAC-SHA256 与 PBKDF2 派生',
                'desc_en': 'HMAC-SHA256 & PBKDF2 key derivation',
                'category': 'crypto',
                'xu_status': 'ok',
                'xu_wall_ms': 15.0,
                'xu_bytes': 38000,
                'implementations': {'Xu': {'wall_ms': 15.0, 'best_ms': 14.0, 'rss_mib': 4.0, 'cpu_ms': 12.0, 'bytes': 38000}},
            })
        page_en = benchmarks.render_page(sample, 'en')
        self.assertIn('id="cat-web" data-category="web"', page_en)
        self.assertIn('id="workload-http_router_parse"', page_en)
        self.assertIn('data-cat="web"', page_en)
        self.assertIn('PBKDF2 key derivation', page_en)
        self.assertIn('7 Domains', page_en)

    def test_full_11_domains_and_batch_e_to_g_descriptions_render_cleanly(self):
        data = json.loads((ROOT / 'www/benchmarks.json').read_text(encoding='utf-8'))
        sample = deepcopy(data)
        synthetic = [
            ('http_router_parse', 'web', 'HTTP/1.1 parsing & trie router', 'HTTP/1.1 解析与 Trie 动态路由'),
            ('btree_index', 'storage', 'Order-32 B+ tree insert, lookup & range scan', 'Order-32 B+ 树插查与范围扫描'),
            ('lz4_block_codec', 'systems', 'LZ4 block hash-match compression codec', 'LZ4 块压缩与重叠解压编解码'),
            ('raytrace_sphere', 'graphics', '3D ray-sphere tracer with shadows & reflections', '3D 球体光线追踪与反射'),
            ('mlp_inference', 'ai', '3-layer dense MLP forward inference (ReLU)', '三层稠密 MLP 神经网络推理'),
            ('hmac_pbkdf2', 'crypto', 'HMAC-SHA256 & PBKDF2 key derivation', 'HMAC-SHA256 与 PBKDF2 派生'),
            ('x25519_dh', 'crypto', 'RFC 7748 Curve25519 / X25519 DH ladder', 'Curve25519 / X25519 密钥交换'),
            ('parallel_mapreduce', 'concurrency', '8-worker parallel MapReduce channel pipeline', '多 Worker 并发 MapReduce'),
        ]
        for p in sample['platforms'].values():
            existing_names = {b['name'] for b in p['benches']}
            for name, category, desc_en, desc_zh in synthetic:
                if name in existing_names:
                    continue
                p['benches'].append({
                    'name': name,
                    'desc_zh': desc_zh,
                    'desc_en': desc_en,
                    'category': category,
                    'xu_status': 'ok',
                    'xu_wall_ms': 10.0,
                    'xu_bytes': 40960,
                    'implementations': {'Xu': {'wall_ms': 10.0, 'best_ms': 9.5, 'rss_mib': 4.0, 'cpu_ms': 8.0, 'bytes': 40960}},
                })
        page_en = benchmarks.render_page(sample, 'en')
        page_zh = benchmarks.render_page(sample, 'zh')
        self.assertIn('11 Domains', page_en)
        self.assertIn('11 个领域', page_zh)
        for key in ('control', 'algo', 'data', 'string', 'web', 'storage', 'systems', 'graphics', 'ai', 'crypto', 'concurrency'):
            self.assertIn(f'id="cat-{key}" data-category="{key}"', page_en)
            self.assertIn(f'id="cat-{key}" data-category="{key}"', page_zh)
        for token in ('X25519', 'parallel_mapreduce', 'MLP'):
            self.assertIn(token, page_en)
            self.assertIn(token, page_zh)
        self.assertNotIn('Transformer', page_en)
        self.assertNotIn('Transformer', page_zh)
