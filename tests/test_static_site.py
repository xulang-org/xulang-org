"""Integration coverage for Pages routes, assets, and independent builds."""

import importlib.util
import hashlib
from html import unescape
import json
from pathlib import Path
import re
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
        for page in ('index.html', 'zh/index.html', 'docs/start/index.html',
                     'benchmarks/index.html', 'zh/benchmarks/index.html', 'benchmarks.json',
                     'zh/api/net/http/index.html', 'api/index.html', 'blog/index.html', '404.html'):
            self.assertTrue((output / page).is_file(), page)
        for asset in ('sitemap.xml', 'robots.txt', 'llms.txt', 'llms-full.txt'):
            self.assertTrue((output / asset).is_file(), asset)
        home = (output / 'index.html').read_text()
        self.assertIn('<html lang="en"', home)
        self.assertIn('href="/docs/start/"', home)
        self.assertIn('href="/zh/" hreflang="zh-CN"', home)
        self.assertIn('>中文</a>', home)
        self.assertIn('<link rel="canonical" href="https://xulang.org/">', home)
        self.assertIn('<meta name="description"', home)
        self.assertIn('<meta name="keywords"', home)
        self.assertIn('<meta property="og:title"', home)
        self.assertIn('<script type="application/ld+json">', home)
        self.assertIn('SoftwareApplication', home)
        sitemap = (output / 'sitemap.xml').read_text()
        self.assertIn('<loc>https://xulang.org/</loc>', sitemap)
        self.assertIn('<loc>https://xulang.org/zh/</loc>', sitemap)
        self.assertNotIn('<lastmod>', sitemap)
        robots = (output / 'robots.txt').read_text()
        self.assertIn('User-agent: GPTBot', robots)
        self.assertIn('Sitemap: https://xulang.org/sitemap.xml', robots)
        llms = (output / 'llms.txt').read_text()
        self.assertIn('# Xu Programming Language', llms)
        chinese = (output / 'zh/index.html').read_text()
        self.assertIn('<html lang="zh-CN"', chinese)
        self.assertIn('href="/zh/docs/start/"', chinese)
        self.assertIn('href="/" hreflang="en"', chinese)
        self.assertIn('<link rel="canonical" href="https://xulang.org/zh/">', chinese)
        self.assertIn('SoftwareApplication', chinese)
        for page, expected in ((home, 4), (chinese, 4),
                               ((output / 'docs/faq/index.html').read_text(), 19),
                               ((output / 'zh/docs/faq/index.html').read_text(), 19)):
            schema = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.DOTALL)[1])
            faq = next(item for item in schema['@graph'] if item['@type'] == 'FAQPage') if '@graph' in schema else schema
            questions = re.findall(r'<summary><h3>(.*?)</h3></summary>', page)
            self.assertEqual(len(faq['mainEntity']), expected)
            self.assertEqual([item['name'] for item in faq['mainEntity']], questions)
            self.assertTrue(all(item['acceptedAnswer']['text'] for item in faq['mainEntity']))
        for page, destination in ((home, '/playground/'), (chinese, '/zh/playground/')):
            self.assertIn(f'class="btn pri" href="{destination}?example=chan-workers"', page)
            self.assertNotIn('id="xu-play-src"', page)
            self.assertNotIn('xu-play.js', page)
            self.assertNotIn('xu-play.wasm', page)
        self.assertIn('data-wasm-available="false"', (output / 'playground/index.html').read_text())
        for page in ('playground', 'zh/playground'):
            html = (output / page / 'index.html').read_text()
            # The controller must mount on the published pages, not just a test fixture.
            experience = re.search(r'<section\b[^>]*id="widget-experience".*?</section>', html, re.DOTALL)
            self.assertIsNotNone(experience, page)
            for control in ('data-widget-list', 'data-widget-detail', 'data-widget-count',
                            'type="search"', '<select'):
                self.assertIn(control, experience[0], page)
            self.assertRegex(html, r'src="/widget-experience\.js\?v=[0-9a-f]{16}"')
        for page in ('docs/tutorial/01', 'zh/docs/tutorial/01', 'api/fmt', 'zh/api/fmt', 'playground'):
            html = (output / page / 'index.html').read_text()
            self.assertEqual(html.count('src="/xu-play.js?'), 1, page)
            self.assertIn('data-wasm-available="false"', html, page)
        self.assertNotIn('href="http://127.0.0.1', home)
        self.assertIn('https://github.com/xulang-org/xu/releases', (output / 'download/index.html').read_text())
        history = output / 'releases/index.html'
        self.assertTrue(history.is_file())
        self.assertEqual({p.relative_to(output / 'releases').as_posix()
                          for p in (output / 'releases').rglob('*') if p.is_file()}, {'index.html'})
        self.assertIn('0.10.5', history.read_text())
        downloads = (output / 'download/index.html').read_text()
        self.assertNotIn('0.10.5', downloads)
        self.assertIn('/releases/', downloads)
        self.assertTrue((output / '.nojekyll').exists())
        version = re.search(r'(?m)^xu: !ver (\S+)', (self.source / 'xu.xun').read_text())[1]
        for page in (home, chinese):
            hero = page.split('<div class="hero home-hero">', 1)[1].split('<section', 1)[0]
            self.assertIn('class="hero-install"', hero)
            for platform in ('unix', 'win'):
                self.assertIn(f'data-tab="{platform}"', hero)
                self.assertIn(f'data-pane="{platform}"', hero)
            self.assertIn(f'curl -fsSL https://xulang.org/install.sh | bash -s -- --online --version {version} --yes', unescape(hero))
            self.assertIn(f'& ([scriptblock]::Create((irm https://xulang.org/install.ps1))) -Online -Version "{version}"', unescape(hero))
            self.assertIn('src="/theme.js"', page)
            self.assertIn('href="/site.css"', page)
        self.assertNotIn('<span class="badge">v', home)
        self.assertNotIn('XU v' + version, home)
        self.assertIn('XU v' + version, downloads)
        self.assertNotIn('{{xu_version}}', home)
        self.assertIn('/releases/tag/v' + version, (output / 'download/index.html').read_text())
        self.assertIn('Xu ' + version + ' API', (output / 'api/net/http/index.html').read_text())
        self.assertIn('Xu ' + version, (output / 'docs/status/index.html').read_text())
        counts = site.shared_content(self.source)['en']
        for lang, prefix in (('en', ''), ('zh', 'zh/')):
            status = (output / (prefix + 'docs/status/index.html')).read_text()
            self.assertNotIn('{{api_', status)
            self.assertIn(counts['api_standard_count'], status)
            self.assertIn(counts['api_external_count'], status)
            banner = re.search(r'<p class="banner">(.*?)</p>', (output / (prefix + 'index.html')).read_text())[1]
            self.assertNotRegex(banner, r'\d+\.\d+\.\d+')
            self.assertIn('id="language-switch"', (output / (prefix + 'index.html')).read_text())
            releases = (output / (prefix + 'releases/index.html')).read_text()
            for entry in json.loads((self.source / 'templates/releases.json').read_text()):
                self.assertIn('id="v' + entry['version'].replace('.', '-') + '"', releases)
            self.assertNotIn('{{release_', releases)

    def test_shared_inventory_changes_counts_without_counting_widget_pages(self):
        from site_layout import shared_content
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'templates').mkdir()
            (root / 'templates/releases.json').write_text('[]')
            for lang in ('en', 'zh'):
                api = root / f'content/{lang}/api'
                (api / 'ui/widgets').mkdir(parents=True)
                (api / 'packages').mkdir()
                for name in ('fmt', 'ui/widgets/button', 'packages/transport'):
                    (api / (name + '.html')).touch()
                (api / 'index.html').write_text('<a href="/api/fmt">fmt</a>')
            self.assertEqual(shared_content(root)['en']['api_standard_count'], '1')
            self.assertEqual(shared_content(root)['zh']['api_external_count'], '0')
            for lang in ('en', 'zh'):
                index = root / f'content/{lang}/api/index.html'
                index.write_text(index.read_text() + '<a href="/api/packages/transport">transport</a>')
            self.assertEqual(shared_content(root)['en']['api_external_count'], '1')
            index.write_text(index.read_text() + '<a href="/api/fmt#examples">example</a>')
            self.assertEqual(shared_content(root)['en']['api_standard_count'], '1')
            index.write_text(index.read_text() + '<a href="/api/ui/widgets/button">button</a>')
            with self.assertRaisesRegex(ValueError, 'inventories.*match'):
                shared_content(root)
            index.write_text('<a href="/api/missing">missing</a>')
            with self.assertRaisesRegex(ValueError, 'missing package'):
                shared_content(root)

    def test_release_metadata_drives_both_indexes_and_sidebar(self):
        from site_layout import shared_content, sidebar
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(self.source / 'content', root / 'content')
            (root / 'templates').mkdir()
            entry = {'version': '0.99.1', 'notes': {'en': '<p>New release</p>', 'zh': '<p>新版本</p>'},
                     'blog_entry': {'en': '<a href="/blog/xu-0-99-1">New release</a>',
                                    'zh': '<a href="/blog/xu-0-99-1">新版本</a>'}}
            (root / 'templates/releases.json').write_text(json.dumps([entry]))
            shared = shared_content(root)
            for lang, prefix in (('en', ''), ('zh', '/zh')):
                self.assertIn('id="v0-99-1"', shared[lang]['release_notes'])
                self.assertIn(entry['notes'][lang], shared[lang]['release_notes'])
                self.assertIn('/blog/xu-0-99-1', shared[lang]['release_blog_entries'])
                self.assertIn(prefix + '/blog/xu-0-99-1', sidebar(prefix + '/blog', lang == 'en', root=root))

    def test_xacp_seo_keeps_the_selected_release_identity_and_limits(self):
        from site_layout import get_seo_meta
        for en, route, limit in ((True, '/api/xacp', 'unverified'), (False, '/zh/api/xacp', '待验')):
            description = get_seo_meta(route, '#xacp', en, '0.99.1')['meta_description']
            self.assertIn('v0.99.1', description)
            self.assertIn(limit, description)
            self.assertNotIn('dev.', description)

    def test_project_path_and_rebuild_remove_stale_pages(self):
        output = self.workspace / 'project'
        site.build(self.source, output, '/xulang-org/')
        home = (output / 'index.html').read_text()
        self.assertIn('href="/xulang-org/docs/start/"', home)
        self.assertIn('href="/xulang-org/zh/" hreflang="zh-CN"', home)
        self.assertRegex((output / 'playground/index.html').read_text(), r'src="/xulang-org/xu-play\.js\?v=[0-9a-f]{16}"')
        self.assertRegex((output / 'zh/api/fmt/index.html').read_text(), r'src="/xulang-org/xu-play\.js\?v=[0-9a-f]{16}" defer data-wasm-available="false"')
        self.assertIn('href="/xulang-org/site.css"', home)
        self.assertIn('class="btn pri" href="/xulang-org/playground/?example=chan-workers"', home)
        self.assertIn('class="btn pri" href="/xulang-org/zh/playground/?example=chan-workers"', (output / 'zh/index.html').read_text())
        self.assertIn('href="/xulang-org/"', home)
        chinese = (output / 'zh/docs/start/index.html').read_text()
        self.assertIn('href="/xulang-org/docs/start/" hreflang="en"', chinese)
        (output / 'stale.html').write_text('old page')
        site.build(self.source, output, '/xulang-org')
        self.assertFalse((output / 'stale.html').exists())

    def test_released_ui_navigation_and_legacy_preview_bookmarks(self):
        output = self.workspace / 'released-ui'
        site.build(self.source, output, '/repo')
        packages = ('ui', 'ui/draw', 'ui/layout', 'ui/widgets', 'ui/webview')
        for prefix in ('', '/zh'):
            for package in ('', *packages):
                route = prefix + '/api' + ('/' + package if package else '')
                page = (output / route.strip('/') / 'index.html').read_text()
                sidebar = page.split('<aside', 1)[1].split('</aside>', 1)[0]
                for target in packages:
                    self.assertIn(f'href="/repo{prefix}/api/{target}/"', sidebar)
                self.assertNotIn('/api/preview', sidebar)
            for suffix in ('', *packages):
                legacy = prefix + '/api/preview' + ('/' + suffix if suffix else '')
                destination = '/repo' + prefix + '/api' + ('/' + suffix if suffix else '') + '/'
                alias = (output / legacy.strip('/') / 'index.html').read_text()
                self.assertIn(f'location.replace("{destination}" + location.search + location.hash)', alias)
                self.assertIn('content="noindex"', alias)
                self.assertNotIn('unreleased', alias)
        self.assertNotIn('/api/preview', (output / 'sitemap.xml').read_text())

    def test_rewrite_preserves_examples_queries_and_fragments(self):
        parser = site.RewriteHTML('/repo', {'/api'}, False)
        parser.feed('<a href="/api?q=a&amp;b=c#item">API</a><a href="//example.org/x">External</a>'
                    '<pre>&lt;a href="/api"&gt;</pre><script>var x = \'href="/api"\';</script>')
        result = ''.join(parser.parts)
        self.assertIn('href="/repo/api/?q=a&amp;b=c#item"', result)
        self.assertIn('href="//example.org/x"', result)
        self.assertIn('<pre>&lt;a href="/api"&gt;</pre>', result)
        self.assertIn('var x = \'href="/api"\'', result)

    def test_language_switches_and_legacy_english_bookmarks(self):
        output = self.workspace / 'languages'
        site.build(self.source, output)
        for source in (self.source / 'content/en').rglob('*.html'):
            route = site.content_route(source.relative_to(self.source / 'content/en'), 'en')
            english = (output / route.strip('/') / 'index.html').read_text()
            chinese_route = '/zh' + route.rstrip('/')
            chinese = (output / chinese_route.strip('/') / 'index.html').read_text()
            self.assertIn(f'href="{chinese_route}/" hreflang="zh-CN"', english, route)
            self.assertIn(f'href="{route.rstrip("/")}/" hreflang="en"', chinese, route)
            self.assertIn('<html lang="en"', english, route)
            self.assertIn('<html lang="zh-CN"', chinese, route)
            self.assertNotIn('href="/en/', english, route)
            legacy = (output / 'en' / route.strip('/') / 'index.html').read_text()
            self.assertIn(f'location.replace("{route.rstrip("/")}/" + location.search + location.hash)', legacy, route)

        english_play = (output / 'playground/index.html').read_text()
        chinese_play = (output / 'zh/playground/index.html').read_text()
        self.assertIn('optgroup label="Coroutines &amp; chan"', english_play)
        self.assertIn('optgroup label="协程与 chan"', chinese_play)
        self.assertIn('href="/zh/docs/tutorial/10/"', chinese_play)

        parser = site.RewriteHTML('/repo', {'/', '/zh', '/api', '/zh/api'}, False, content_lang='zh')
        parser.feed('<a href="/api?q=a&amp;b=c#item">API</a><a href="/en/api#item">English</a>'
                    '<a href="/api" hreflang="en">EN</a><img src="/xu_classic.svg">'
                    '<pre>&lt;a href="/api"&gt;</pre>')
        result = ''.join(parser.parts)
        self.assertIn('href="/repo/zh/api/?q=a&amp;b=c#item"', result)
        self.assertIn('href="/repo/api/#item"', result)
        self.assertIn('href="/repo/api/" hreflang="en"', result)
        self.assertIn('src="/repo/xu_classic.svg"', result)
        self.assertIn('<pre>&lt;a href="/api"&gt;</pre>', result)

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
        wasm = source / 'build/playground/xu-play.wasm'
        wasm.parent.mkdir(parents=True)
        wasm.write_bytes(b'not a wasm module')
        with self.assertRaisesRegex(ValueError, 'invalid.*WASM'):
            site.build(source, self.workspace / 'invalid-output', require_playground=True)
        # A minimal valid module verifies packaging; actual Xu ABI is exercised
        # by the production-runtime tests in test_playground.mjs.
        wasm.write_bytes(b'\x00asm\x01\x00\x00\x00')
        version = re.search(r'(?m)^xu: !ver (\S+)', (source / 'xu.xun').read_text())[1]
        record = wasm.parent / 'build.json'
        stamp = {'xu_version': version, 'wasm_sha256': hashlib.sha256(wasm.read_bytes()).hexdigest()}
        record.write_text(json.dumps(stamp))
        output = self.workspace / 'with-wasm-output'
        site.build(source, output, '/repo', require_playground=True)
        for page in ('index.html', 'zh/index.html'):
            home = (output / page).read_text()
            self.assertNotIn('xu-play.js', home)
            self.assertNotIn('xu-play.wasm', home)
        self.assertIn('data-wasm-available="true"', (output / 'playground/index.html').read_text())
        self.assertRegex((output / 'playground/index.html').read_text(),
                         r'<link rel="preload" href="/repo/xu-play\.wasm\?v=[0-9a-f]{16}" as="fetch" type="application/wasm" crossorigin>')
        for asset in ('xu-play-worker.js', 'xu-play-runtime.mjs', 'xu-play-examples.json', 'xu-play.wasm'):
            self.assertTrue((output / asset).is_file(), asset)

        # The generated artifact contributes to the cache key; stale binaries
        # in www/ must never enable or replace the current runtime.
        before = (output / 'playground/index.html').read_text()
        wasm.write_bytes(b'\x00asm\x01\x00\x00\x00\x00\x02\x01x')
        with self.assertRaisesRegex(ValueError, 'WASM build checksum does not match'):
            site.build(source, output, require_playground=True)
        stamp['wasm_sha256'] = hashlib.sha256(wasm.read_bytes()).hexdigest()
        record.write_text(json.dumps(stamp))
        site.build(source, output, '/repo', require_playground=True)
        self.assertNotEqual(
            re.search(r'xu-play\.js\?v=([0-9a-f]{16})', before)[1],
            re.search(r'xu-play\.js\?v=([0-9a-f]{16})', (output / 'playground/index.html').read_text())[1],
        )
        stamp['xu_version'] = '0.8.99'
        record.write_text(json.dumps(stamp))
        with self.assertRaisesRegex(ValueError, 'WASM version does not match'):
            site.build(source, output, require_playground=True)
        wasm.unlink()
        (source / 'www/xu-play.wasm').write_bytes(b'old runtime')
        site.build(source, output)
        self.assertFalse((output / 'xu-play.wasm').exists())
        self.assertIn('data-wasm-available="false"', (output / 'playground/index.html').read_text())

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

    def test_older_measurements_keep_their_actual_version(self):
        output = self.workspace / 'historical-benchmarks'
        site.build(self.source, output)
        measured = json.loads((self.source / 'www/benchmarks.json').read_text())['metadata']['xu_version']
        page = (output / 'benchmarks/index.html').read_text()
        self.assertIn('Measured Xu v' + measured, page)
        self.assertEqual((output / 'benchmarks.json').read_bytes(),
                         (self.source / 'www/benchmarks.json').read_bytes())

    def test_future_or_relabelled_benchmarks_are_rejected(self):
        source = self.workspace / 'invalid-benchmarks'
        shutil.copytree(self.source, source)
        data = source / 'www/benchmarks.json'
        original = data.read_text()
        future = json.loads(original)
        future['metadata']['xu_version'] = '999.0.0'
        data.write_text(json.dumps(future))
        with self.assertRaisesRegex(ValueError, 'Benchmark version.*newer'):
            site.build(source, self.workspace / 'future-benchmark-output')
        data.write_text(original)
        page = source / 'content/en/benchmarks.html'
        page.write_text(page.read_text().replace('Measured Xu v', 'Relabelled Xu v'))
        with self.assertRaisesRegex(ValueError, 'Benchmark measurement label'):
            site.build(source, self.workspace / 'relabelled-benchmark-output')

    def test_mismatched_api_snapshot_cannot_be_relabelled_as_another_release(self):
        with self.assertRaisesRegex(ValueError, 'API version does not match'):
            site.build(self.source, self.workspace / 'wrong-version', xu_version='0.8.99')
        with self.assertRaisesRegex(ValueError, 'invalid Xu release version'):
            site.build(self.source, self.workspace / 'invalid-version', xu_version='<script>')


if __name__ == '__main__':
    unittest.main()
