"""Integration coverage for Pages routes, assets, and independent builds."""

import importlib.util
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('build_static', ROOT / 'scripts/build-static.py')
site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(site)


class StaticSiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.workspace = Path(cls.temp.name)
        cls.source = cls.workspace / 'source'
        cls.source.mkdir()
        # Match a clean GitHub checkout: no compiler, binaries, or ignored WASM.
        for directory in ('content', 'templates', 'www'):
            shutil.copytree(ROOT / directory, cls.source / directory,
                            ignore=shutil.ignore_patterns('releases', 'xu-play.wasm', '.DS_Store'))
        shutil.copyfile(ROOT / 'xu.xun', cls.source / 'xu.xun')

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_root_build_from_clean_checkout(self):
        output = self.workspace / 'root'
        count = site.build(self.source, output)
        self.assertEqual(count, len(list((self.source / 'content').rglob('*.html'))))
        for page in ('index.html', 'en/index.html', 'docs/start/index.html',
                     'en/api/net/http/index.html', 'api/index.html', 'blog/index.html', '404.html'):
            self.assertTrue((output / page).is_file(), page)
        home = (output / 'index.html').read_text()
        self.assertIn('href="/docs/start/"', home)
        self.assertIn('data-wasm-available="false"', home)
        self.assertNotIn('href="http://127.0.0.1', home)
        self.assertIn('https://github.com/xulang-org/xu/releases', (output / 'download/index.html').read_text())
        self.assertFalse((output / 'releases').exists())
        self.assertTrue((output / '.nojekyll').exists())

    def test_project_path_and_rebuild_remove_stale_pages(self):
        output = self.workspace / 'project'
        site.build(self.source, output, '/xulang-org/')
        home = (output / 'en/index.html').read_text()
        self.assertIn('href="/xulang-org/en/docs/start/"', home)
        self.assertIn('src="/xulang-org/xu-play.js"', home)
        self.assertIn('href="/xulang-org/site.css"', home)
        self.assertIn('href="/xulang-org/"', home)
        (output / 'stale.html').write_text('old page')
        site.build(self.source, output, '/xulang-org')
        self.assertFalse((output / 'stale.html').exists())

    def test_rewrite_preserves_examples_queries_and_fragments(self):
        parser = site.RewriteHTML('/repo', {'/api'}, False)
        parser.feed('<a href="/api?q=a&amp;b=c#item">API</a><a href="//example.org/x">External</a>'
                    '<pre>&lt;a href="/api"&gt;</pre><script>var x = \'href="/api"\';</script>')
        result = ''.join(parser.parts)
        self.assertIn('href="/repo/api/?q=a&amp;b=c#item"', result)
        self.assertIn('href="//example.org/x"', result)
        self.assertIn('<pre>&lt;a href="/api"&gt;</pre>', result)
        self.assertIn('var x = \'href="/api"\'', result)

    def test_missing_asset_fails_build(self):
        source = self.workspace / 'broken'
        shutil.copytree(self.source, source)
        (source / 'www/site.css').unlink()
        with self.assertRaisesRegex(ValueError, 'missing /site.css'):
            site.build(source, self.workspace / 'broken-output')

    def test_publication_requires_real_playground_asset(self):
        with self.assertRaisesRegex(ValueError, 'WASM is required'):
            site.build(self.source, self.workspace / 'required-output', require_playground=True)
        source = self.workspace / 'with-wasm'
        shutil.copytree(self.source, source)
        wasm = source / 'www/xu-play.wasm'
        wasm.write_bytes(b'not a wasm module')
        with self.assertRaisesRegex(ValueError, 'invalid.*WASM'):
            site.build(source, self.workspace / 'invalid-output', require_playground=True)
        # A minimal valid module verifies packaging; actual Xu ABI is exercised
        # by the production-runtime tests in test_playground.mjs.
        wasm.write_bytes(b'\x00asm\x01\x00\x00\x00')
        output = self.workspace / 'with-wasm-output'
        site.build(source, output, '/repo', require_playground=True)
        self.assertIn('data-wasm-available="true"', (output / 'index.html').read_text())
        for asset in ('xu-play-worker.js', 'xu-play-runtime.mjs', 'xu-play-examples.json', 'xu-play.wasm'):
            self.assertTrue((output / asset).is_file(), asset)

    def test_refuses_source_or_unowned_output(self):
        with self.assertRaises(ValueError):
            site.build(self.source, self.source / 'content')
        with self.assertRaises(ValueError):
            site.build(self.source, self.workspace)
        self.assertTrue((self.source / 'content/zh/home.html').exists())
        for base in ('https://example.org', '../docs', '/repo?x=1'):
            with self.assertRaises(ValueError):
                site.normalize_base(base)

    def test_versions(self):
        manifest = (ROOT / 'xu.xun').read_text()
        self.assertIn('version: !ver ' + (ROOT / 'VERSION').read_text().strip(), manifest)
        self.assertRegex(manifest, r'(?m)^xu: !ver \d+\.\d+\.\d+$')


if __name__ == '__main__':
    unittest.main()
