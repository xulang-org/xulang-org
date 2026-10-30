"""API navigation must cover every released API page on disk."""

import importlib.util
from html.parser import HTMLParser
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('site_layout', ROOT / 'scripts/site_layout.py')
site_layout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(site_layout)


class SidebarLinks(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.hrefs = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.hrefs.append(dict(attrs)['href'])


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
                        'encoding/asn1', 'ui/widgets', 'ui/widgets/button',
                        'alpha', 'archive/tar', 'index/suffixarray', 'zeta']
            for en, prefix, label in ((True, '', 'Other'), (False, '/zh', '其他')):
                with self.subTest(language=prefix or 'en'):
                    rendered = site_layout.sidebar(prefix + '/api', en, root=root)
                    self.assertEqual(SidebarLinks(rendered).hrefs,
                                     [prefix + '/api', *[prefix + '/api/' + p for p in expected]])
                    self.assertIn(f'<span>{label}</span>', rendered)


if __name__ == '__main__':
    unittest.main()
