"""Design updates invalidate the actual assets loaded by a prefixed deployment."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('design_site', ROOT / 'scripts/build-static.py')
site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(site)


class DesignCacheTests(unittest.TestCase):
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
