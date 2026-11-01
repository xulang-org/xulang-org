"""Pinned desktop declarations and explicit browser adaptations are verifiable."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('widget_sync', ROOT / 'scripts/sync-playground-widgets.py')
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class WidgetSourceTests(unittest.TestCase):
    def test_browser_adaptations_preserve_upstream_bodies_and_reproduce_the_snapshot(self):
        directory = ROOT / 'playground/stdlib'
        manifest = json.loads((directory / 'desktop-sources.json').read_text())
        adaptation_bytes = (directory / manifest['adaptations']['path']).read_text(encoding='utf-8').encode()
        self.assertEqual(hashlib.sha256(adaptation_bytes).hexdigest(), manifest['adaptations']['sha256'])
        adaptations = json.loads(adaptation_bytes)
        self.assertEqual(adaptations['upstream_commit'], manifest['commit'])
        self.assertEqual(adaptations['schema'], 2)
        expected = {(d['module'], d['signature']): d for d in manifest['declarations'] if 'upstream_sha256' in d}
        self.assertEqual(set(expected), {(d['module'], d['signature']) for d in adaptations['declarations']})
        for entry in adaptations['declarations']:
            with self.subTest(signature=entry['signature']):
                self.assertTrue(entry['reason'])
                if 'source_commit' in entry:
                    self.assertRegex(entry['source_commit'], r'^[a-f0-9]{40}$')
                record = expected[(entry['module'], entry['signature'])]
                self.assertEqual(record['upstream_sha256'], entry['upstream_sha256'])
                self.assertEqual(record['sha256'], entry['sha256'])
                source = (directory / ('desktop_' + entry['module'] + '.xu')).read_text()
                current = dict(sync.declarations(source))[entry['signature']].split('\n// Upstream:')[0].rstrip()
                upstream = current
                for replacement in reversed(entry['replacements']):
                    self.assertEqual(upstream.count(replacement['after']), 1)
                    upstream = upstream.replace(replacement['after'], replacement['before'], 1)
                self.assertEqual(hashlib.sha256(upstream.encode()).hexdigest(), entry['upstream_sha256'])
                self.assertEqual(sync.apply_adaptation(upstream, entry), current)
                with self.assertRaisesRegex(ValueError, 'upstream drift'):
                    sync.apply_adaptation(upstream + '\n// unexpected edit', entry)

    def test_vendored_declarations_match_manifest(self):
        directory = ROOT / 'playground/stdlib'
        manifest = json.loads((directory / 'desktop-sources.json').read_text())
        self.assertRegex(manifest['commit'], r'^[a-f0-9]{40}$')
        actual = {}
        for file in directory.glob('desktop_*.xu'):
            for signature, chunk in sync.declarations(file.read_text()):
                # The source annotation between declarations is provenance.
                chunk = chunk.split('\n// Upstream:')[0].rstrip()
                actual[(file.stem.removeprefix('desktop_'), signature)] = hashlib.sha256(chunk.encode()).hexdigest()
        expected = {(d['module'], d['signature']): d['sha256'] for d in manifest['declarations']}
        self.assertEqual(actual, expected)
        signatures = [d['signature'] for d in manifest['declarations']]
        for kind in ('Button', 'Checkbox', 'Switch', 'Slider', 'Radio', 'ListBox', 'Tabs'):
            self.assertTrue(any('&' + kind + ') paint(' in s for s in signatures), kind)
            self.assertTrue(any('$&' + kind + ') input(' in s for s in signatures), kind)
        self.assertTrue(any('button_size(' in s for s in signatures))
        for kind in ('Card', 'Badge', 'Progress', 'Editor'):
            self.assertTrue(any(('$&' if kind == 'Editor' else '&') + kind + ') paint(' in s for s in signatures), kind)
        self.assertTrue(any('StyledLabel) paint_text_styled(' in s for s in signatures))
        self.assertTrue(any('Scroll) begin(' in s for s in signatures))
        self.assertFalse(any('pub struct Screen' in s or 'pub struct Host' in s for s in signatures))

    def test_subset_extraction_keeps_complete_functions(self):
        text = 'pub fn first() int {\n if true { << 1 }\n << 0\n}\n// next\npub fn second() int { << 2 }\n'
        declarations = list(sync.declarations(text))
        self.assertEqual(len(declarations), 2)
        self.assertTrue(declarations[0][1].endswith('<< 0\n}'))
