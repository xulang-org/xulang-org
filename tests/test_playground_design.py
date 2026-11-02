"""Design updates invalidate the actual assets loaded by a prefixed deployment."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('design_site', ROOT / 'scripts/build-static.py')
site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(site)
design_spec = importlib.util.spec_from_file_location('design_adapter', ROOT / 'scripts/sync-playground-design.py')
design = importlib.util.module_from_spec(design_spec)
design_spec.loader.exec_module(design)


class DesignCacheTests(unittest.TestCase):
    def test_pinned_design_snapshot_is_portable_and_rejects_token_drift(self):
        tokens = (ROOT / 'playground/design/tokens.json').read_text(encoding='utf-8')
        source = (ROOT / 'playground/design/source.json').read_text(encoding='utf-8')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root / 'playground/design'
            directory.mkdir(parents=True)
            (directory / 'source.json').write_text(source, encoding='utf-8')
            # Git may check out CRLF on Windows; hashes refer to canonical UTF-8/LF.
            (directory / 'tokens.json').write_bytes(tokens.replace('\n', '\r\n').encode('utf-8'))
            with patch.object(design, 'ROOT', root):
                self.assertEqual(design.load_tokens()['version'], json.loads(source)['version'])
                changed = json.loads(tokens)
                changed['themes']['light']['brand'] = '#000000'
                (directory / 'tokens.json').write_text(json.dumps(changed), encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'snapshot does not match'):
                    design.generate_css()

    def test_preview_controls_are_versioned_under_a_base_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'www').mkdir()
            controller = root / 'www/xu-play-preview.js'
            controller.write_text('first')
            old = site.playground_asset_key(root, root / 'unused.wasm')
            controller.write_text('updated')
            new = site.playground_asset_key(root, root / 'unused.wasm')
            self.assertNotEqual(old, new)
            parser = site.RewriteHTML('/repo', {'/playground'}, True, new)
            parser.feed('<script src="/xu-play-preview.js" defer></script>')
            self.assertIn(f'/repo/xu-play-preview.js?v={new}', ''.join(parser.parts))

    def test_design_update_changes_styles_controller_and_catalog_cache_key(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'www').mkdir()
            css = root / 'www/playground-design.css'
            css.write_text(':root { --xu-focus: blue; }')
            wasm = root / 'unused.wasm'
            old = site.playground_asset_key(root, wasm)
            css.write_text(':root { --xu-focus: red; }')
            new = site.playground_asset_key(root, wasm)
            self.assertNotEqual(old, new)
            parser = site.RewriteHTML('/repo', {'/playground'}, True, new)
            parser.feed('<link rel="stylesheet" href="/playground-design.css">'
                        '<link rel="stylesheet" href="/widgets.css">'
                        '<script src="/widget-experience.js"></script>')
            html = ''.join(parser.parts)
            for asset in ('playground-design.css', 'widgets.css', 'widget-experience.js'):
                self.assertIn(f'/repo/{asset}?v={new}', html)
            # widget-experience.js forwards its versioned script URL's search to widgets.json.


if __name__ == '__main__':
    unittest.main()
