"""Keep the homepage proof, bilingual task paths and integration limits aligned."""

from html import unescape
import json
from pathlib import Path
import re
import unittest
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def source(lang, route):
    return (ROOT / 'content' / lang / route).read_text()


class HomeTaskTests(unittest.TestCase):
    def assert_links_resolve(self, markup, lang):
        for href in re.findall(r'href="([^"]+)"', markup):
            url = urlsplit(unescape(href))
            if url.scheme or not url.path.startswith('/'):
                continue
            route = re.sub(r'^/(en|zh)(?=/)', '', url.path).strip('/')
            target = ROOT / 'content' / lang / (route + '.html')
            self.assertTrue(target.is_file(), (lang, href))
            if url.fragment:
                self.assertRegex(target.read_text(), rf'id=[\'"]{re.escape(url.fragment)}[\'"]', href)

    def test_home_example_matches_every_catalog_file_and_primary_cta(self):
        catalog = json.loads((ROOT / 'www/xu-play-examples.json').read_text())['projects']
        for lang in ('en', 'zh'):
            home = source(lang, 'home.html')
            hero = home.split('<section', 1)[0]
            ctas = re.findall(r'<a class="btn (pri|ghost)" href="([^"]+)"', hero)
            self.assertEqual(len(ctas), 2)
            primary = urlsplit(ctas[0][1])
            self.assertEqual(primary.path, '/playground')
            selected = parse_qs(primary.query)['example'][0]
            project = catalog[selected]
            self.assertEqual(ctas[1], ('ghost', '/docs/start'))
            preview = re.search(r'<section class="home-example xu-project-example".*?</section>', home, re.S)[0]
            self.assertIn(f'data-playground-example="{selected}"', preview)
            files = {name: unescape(code) for name, code in re.findall(
                r'<code class="language-xu" data-source-file="([^"]+)">(.*?)</code>', preview, re.S)}
            self.assertEqual(files, project['files'])
            self.assertIn(f'<samp>{project["expected"]["value"].strip()}</samp>', preview)
            inputs = ' '.join(project['files'])
            self.assertIn(f'xu check {inputs}', preview)
            self.assertIn(f'xu run {inputs}', preview)
            self.assertLess(home.index('</section>'), home.index('<section class="pillars">'))
            self.assertIn('WASM', preview)
            self.assert_links_resolve(home, lang)

    def test_four_task_paths_have_steps_api_links_and_limits_in_both_languages(self):
        for lang in ('en', 'zh'):
            home = source(lang, 'home.html')
            cards = dict(re.findall(r'<article class="task-card" data-task="([^"]+)">(.*?)</article>', home, re.S))
            self.assertEqual(set(cards), {'cli', 'http', 'db', 'ui'})
            for name, card in cards.items():
                self.assertEqual(card.count('<li>'), 3, (lang, name))
                self.assertRegex(card, r'href="/api/[^\"]+"')
                self.assertIn('Result:' if lang == 'en' else '结果：', card)
                self.assertIn('Support / limits:' if lang == 'en' else '支持 / 限制：', card)
                self.assertNotIn('xacp', card.lower())
            self.assertIn('WASM', cards['ui'])
            self.assertIn('WebView', cards['ui'])
            selected = parse_qs(urlsplit(re.search(r'href="(/playground[^\"]+)"', cards['ui'])[1]).query)['example'][0]
            catalog = json.loads((ROOT / 'www/xu-play-examples.json').read_text())['projects']
            self.assertEqual(catalog[selected]['group'], 'ui')

    def test_matrix_covers_all_integrations_and_transport_with_explicit_unknowns(self):
        expected = {p.stem for p in (ROOT / 'content/en/api/packages').glob('*.html')}
        unknowns = {}
        for lang in ('en', 'zh'):
            page = source(lang, 'docs/packages.html')
            table = re.search(r'<table id="integration-matrix".*?</table>', page, re.S)[0]
            self.assertEqual(table.count('<th>'), 9)
            rows = re.findall(r'<tr data-package="([^"]+)">(.*?)</tr>', table, re.S)
            self.assertEqual(len(rows), 30)
            self.assertEqual({name for name, _ in rows}, expected)
            unknown = 'unknown' if lang == 'en' else '未知'
            unknowns[lang] = {}
            for name, row in rows:
                cells = re.findall(r'<td>(.*?)</td>', row, re.S)
                self.assertEqual(len(cells), 9, (lang, name))
                self.assertTrue(all(cell.strip() for cell in cells), (lang, name))
                self.assertIn(unknown, cells[-1], (lang, name))
                unknowns[lang][name] = [unknown in cell for cell in cells[5:]]
            self.assertIn('tls_connect_config', page)
            self.assertIn('1.0.0', page)
            self.assertIn('1.0.2', page)
            self.assert_links_resolve(table, lang)
        self.assertEqual(unknowns['en'], unknowns['zh'])

    def test_download_and_ui_explain_browser_and_native_platform_boundaries(self):
        for lang in ('en', 'zh'):
            for route in ('download.html', 'docs/ui.html'):
                page = source(lang, route)
                self.assertIn('id="platform-boundaries"', page)
                self.assertIn('WASM', page)
                self.assertIn('WebView', page)
                self.assertIn('unverified' if lang == 'en' else '待验', page)
                self.assertIn('href="/playground', page)


if __name__ == '__main__':
    unittest.main()
