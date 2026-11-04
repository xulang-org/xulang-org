"""API navigation must cover every released API page on disk."""

import importlib.util
from html.parser import HTMLParser
from pathlib import Path
import tempfile
import unittest
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('site_layout', ROOT / 'scripts/site_layout.py')
site_layout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(site_layout)


class SidebarLinks(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.hrefs = []
        self.details = []
        self.buckets = []
        self.link_buckets = {}
        self.visible_links = {}
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'details':
            self.details.append(attrs)
            if 'data-api-section' in attrs:
                self.buckets.append((attrs['data-api-section'], len(self.details)))
        elif tag == 'a':
            href = attrs['href']
            self.hrefs.append(href)
            self.link_buckets[href] = next((d['data-api-section'] for d in reversed(self.details)
                                           if 'data-api-section' in d), None)
            self.visible_links[href] = all('open' in d for d in self.details)

    def handle_endtag(self, tag):
        if tag == 'details':
            self.details.pop()


class APISidebarTests(unittest.TestCase):
    def test_api_sidebar_covers_all_packages(self):
        api_root = ROOT / 'content/en/api'
        on_disk = sorted(
            page.relative_to(api_root).with_suffix('').as_posix()
            for page in api_root.rglob('*.html')
            if page.name != 'index.html' and 'preview' not in page.relative_to(api_root).parts
        )
        listed = [
            package
            for _icon, _zh, _en, packages in site_layout.API_GROUPS
            for package in packages if package
        ]
        self.assertEqual(
            sorted(listed), on_disk,
            f'Sidebar packages: listed={len(listed)}, on disk={len(on_disk)}',
        )

    def test_every_released_sidebar_has_three_buckets_and_full_localized_coverage(self):
        for lang, prefix in (('en', ''), ('zh', '/zh')):
            api_root = ROOT / f'content/{lang}/api'
            on_disk = {p.relative_to(api_root).with_suffix('').as_posix()
                       for p in api_root.rglob('*.html')
                       if p.name != 'index.html' and 'preview' not in p.relative_to(api_root).parts}
            for current in ('', '/fmt', '/ui', '/ui/widgets', '/ui/widgets/button', '/packages/mysql'):
                route = prefix + '/api' + current
                with self.subTest(lang=lang, route=route):
                    rendered = site_layout.sidebar(route, lang == 'en')
                    parsed = SidebarLinks(rendered)
                    self.assertEqual(parsed.buckets, [('standard-library', 2), ('ui', 2), ('extensions', 2)])
                    self.assertIn('id="api-directory" open', rendered)
                    expected = {prefix + '/api/' + p for p in on_disk}
                    self.assertEqual(set(parsed.hrefs), {prefix + '/api'} | expected)
                    self.assertEqual(len(parsed.hrefs), len(on_disk) + 1)
                    for package in on_disk:
                        bucket = ('extensions' if package.startswith('packages/') else
                                  'ui' if package == 'ui' or package.startswith('ui/') else 'standard-library')
                        self.assertEqual(parsed.link_buckets[prefix + '/api/' + package], bucket)
                    self.assertTrue(parsed.visible_links[route], 'The active page must be visible without JS')
                    self.assertIn('aria-current="page"', rendered)
                    for label in (('Standard library', 'UI', 'Extensions') if lang == 'en' else ('标准库', 'UI', '扩展包')):
                        self.assertIn('<span>' + label + '</span>', rendered)

    def test_disk_updates_preserve_curated_order_and_localized_routes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            api_root = root / 'content/en/api'

            def add_page(package):
                page = api_root / (package + '.html')
                page.parent.mkdir(parents=True, exist_ok=True)
                page.write_text('<p>API reference</p>', encoding='utf-8')

            for package in ('index', 'fmt', 'errors', 'encoding/json', 'encoding/hex',
                            'encoding/asn1', 'net/http2', 'ui/widgets', 'ui/widgets/button',
                            'zeta', 'archive/tar', 'index/suffixarray', 'preview/hidden',
                            'net/preview/hidden', 'nested/index'):
                add_page(package)

            groups = site_layout.api_groups(root)
            by_label = {en: (zh, packages) for _icon, zh, en, packages in groups}
            self.assertEqual(by_label['Core'][1], ['errors', 'fmt'])
            self.assertEqual(by_label['Encoding'][1], ['encoding/json', 'encoding/hex', 'encoding/asn1'])
            self.assertEqual(by_label['Net'][1], ['net/http2'])
            self.assertEqual(by_label['UI'][1], ['ui/widgets', 'ui/widgets/button'])
            self.assertEqual(by_label['Other'], ('其他', ['archive/tar', 'index/suffixarray', 'zeta']))
            self.assertEqual([en for _icon, _zh, en, _packages in groups],
                             ['API', 'Core', 'Net', 'Encoding', 'UI', 'Other'])

            # A subsequent build must pick up new pages without reimporting the module.
            add_page('alpha')
            expected = ['errors', 'fmt', 'net/http2', 'encoding/json', 'encoding/hex',
                        'encoding/asn1', 'alpha', 'archive/tar', 'index/suffixarray', 'zeta',
                        'ui/widgets', 'ui/widgets/button']
            for en, prefix, label in ((True, '', 'Other'), (False, '/zh', '其他')):
                with self.subTest(language=prefix or 'en'):
                    rendered = site_layout.sidebar(prefix + '/api', en, root=root)
                    self.assertEqual(SidebarLinks(rendered).hrefs,
                                     [prefix + '/api', *[prefix + '/api/' + p for p in expected]])
                    self.assertIn(f'<span>{label}</span>', rendered)

            # Newly released UI and extension namespaces stay in their own buckets.
            add_page('packages/future')
            add_page('ui/future')
            parsed = SidebarLinks(site_layout.sidebar('/api/packages/future', True, root=root))
            self.assertEqual(parsed.link_buckets['/api/packages/future'], 'extensions')
            self.assertEqual(parsed.link_buckets['/api/ui/future'], 'ui')
            self.assertTrue(parsed.visible_links['/api/packages/future'])

    def test_breadcrumbs_only_link_to_real_parent_packages(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            parent = root / 'content/zh/api/ui.html'
            parent.parent.mkdir(parents=True)
            parent.write_text('<h1>UI</h1>')
            rendered = site_layout.api_tools('/zh/api/ui/widgets/button', False, root)
            self.assertIn('href="/zh/api/ui"', rendered)
            self.assertNotIn('href="/zh/api/ui/widgets"', rendered)
            self.assertIn('aria-current="page">button', rendered)
            (parent.parent / 'index.html').write_text('<h1>API index</h1>')
            rendered = site_layout.api_tools('/zh/api/index/suffixarray', False, root)
            self.assertNotIn('href="/zh/api/index"', rendered)
            self.assertIn('<span>index</span>', rendered)

    def test_search_assets_and_tools_are_scoped_and_versioned(self):
        rendered = site_layout.render(ROOT, '#strings', '/zh/api/strings', '<h1>#strings</h1>', '0.11.2')
        self.assertRegex(rendered, r'/api-browser\.js\?v=[a-f0-9]{16}')
        self.assertIn('class="doc api-page"', rendered)
        self.assertIn('data-api-search hidden', rendered)
        self.assertIn('data-api-copy hidden', rendered)
        other = site_layout.render(ROOT, 'Docs', '/zh/docs/start', '<h1>Docs</h1>', '0.11.2')
        self.assertNotIn('/api-browser.', other)
        self.assertNotIn('data-api-search', other)
        component = site_layout.render(ROOT, 'Button', '/zh/api/ui/widgets/button',
                                       '<nav class="widget-crumb">Old trail</nav><h1>Button</h1>', '0.11.2')
        self.assertNotIn('class="widget-crumb"', component)
        self.assertIn('class="api-breadcrumbs"', component)

    @unittest.skipUnless(shutil.which('node'), 'Node is optional for static builds')
    def test_search_matches_packages_receivers_and_localized_descriptions(self):
        result = subprocess.run(['node', '--test', str(ROOT / 'tests/test_api_browser.mjs')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
