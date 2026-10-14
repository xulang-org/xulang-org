"""Public API extraction and companion package generation."""

import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('gen_api', ROOT / 'scripts/gen-api.py')
api = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = api
spec.loader.exec_module(api)


class APIGenerationTests(unittest.TestCase):
    def test_current_contracts_and_external_module_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'xu/src'
            public = source / 'io'
            public.mkdir(parents=True)
            (source.parent / 'VERSION').write_text('0.8.4\n')
            (public / 'mod.xu').write_text('''@io
pub enum ReadResult {
    Data(string)
    End
}
pub struct@ Reader {
    fn read_n(int) string
}
pub struct Options {
    hidden int
    pub:
    size int
}
pub fn read#T: Reader(src &mut T) string {
    << src.read_n(1)
}
fn private_helper() {}
''')
            (public / 'test.contract.xu').write_text('pub const test_only = 1\n')
            internal = source / 'internal/secret'
            internal.mkdir(parents=True)
            (internal / 'mod.xu').write_text('pub const private_data = 1\n')
            external = root / 'packages'
            (external / 'mysql').mkdir(parents=True)
            (external / 'xu.xun').write_text('module: "github.com/xulang-org/packages"\nversion: !ver 0.1.1\nxu: !ver 0.8.3\n')
            (external / 'mysql/mod.xu').write_text('@"github.com/xulang-org/packages/mysql"\npub fn driver() int { << 1 }\n')
            site = root / 'site'
            css = site / 'www/site.css'
            css.parent.mkdir(parents=True)
            styles = '/* —— stdlib API pages —— */\n.api-item {}\n.custom-rule { color: red; }\n'
            css.write_text(styles)
            (site / 'xu.xun').write_text('module: xu/site\nversion: !ver 0.5.2\nxu: !ver 0.8.3\n')
            (site / 'VERSION').write_text('0.5.2\n')
            runtime = site / 'playground/runtime/xu.xun'
            runtime.parent.mkdir(parents=True)
            runtime.write_text('module: xu/site/playground\nversion: !ver 0.1.1\nxu: !ver 0.8.3\n')
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(api.main(['--src', str(source), '--packages', str(external), '--site', str(site)]), 0)
            for lang in ('zh', 'en'):
                page = (site / f'content/{lang}/api/io.html').read_text()
                self.assertIn('ReadResult', page)
                self.assertIn('iface-Reader', page)
                self.assertIn('struct-Options', page)
                self.assertIn('size', page)
                self.assertIn('id="read"', page)
                for private_name in ('hidden', 'test_only', 'private_helper', 'private_data', 'v0.1.0'):
                    self.assertNotIn(private_name, page)
                package = (site / f'content/{lang}/api/packages/mysql.html').read_text()
                self.assertIn('mysql #github.com/xulang-org/packages/mysql', package)
                self.assertIn('0.1.1', package)
                self.assertIn('<!--xu-api-version: 0.8.4-->', package)
                self.assertIn('Xu {{xu_version}}', package)
                index = (site / f'content/{lang}/api/index.html').read_text()
                self.assertIn('/api/packages/mysql', index)
                self.assertNotIn('/api/internal', index)
            self.assertEqual(css.read_text(), styles)
            self.assertIn('version: !ver 0.8.4\nxu: !ver 0.8.4', (site / 'xu.xun').read_text())
            self.assertEqual((site / 'VERSION').read_text().strip(), '0.8.4')
            self.assertIn('version: !ver 0.1.1\nxu: !ver 0.8.4', runtime.read_text())
            parsed = api.load_package(str(source), 'io')
            self.assertEqual((parsed.n_fn, parsed.n_type, parsed.n_iface), (1, 2, 1))


if __name__ == '__main__':
    unittest.main()
