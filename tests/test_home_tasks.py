"""Keep the homepage proof, bilingual task paths and integration limits aligned."""
from __future__ import annotations

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
    def test_research_guides_sit_between_hero_and_feature_modules(self):
        for page in sorted((ROOT / 'content').glob('*/home.html')):
            lang = page.parent.name
            with self.subTest(lang=lang):
                home = page.read_text()
                research = home.split('id="research"', 1)[1].split('</section>', 1)[0]
                prefix = '/zh' if lang == 'zh-tw' else ''
                self.assertEqual(re.findall(r'class="research-link" href="([^"]+)"', research),
                                 [prefix + '/docs/os', prefix + '/docs/ai'])
                for capability in ('x64-none', 'arm64-none', 'riscv64-none', 'GGUF', 'Safetensors'):
                    self.assertIn(f'<code>{capability}</code>', research)
                self.assertLess(home.index('class="hero-install"'), home.index('id="research"'))
                self.assertLess(home.index('id="research"'), home.index('class="pillars"'))
                if lang in ('en', 'zh'):
                    self.assertEqual(home.count('class="pillar"'), 9)

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

    def test_oneclick_install_stays_in_both_home_heroes(self):
        commands = {
            'unix': 'curl -fsSL https://xulang.org/install.sh | bash -s -- --online --version {{xu_version}} --yes',
            'win': '& ([scriptblock]::Create((irm https://xulang.org/install.ps1))) -Online -Version "{{xu_version}}"',
        }
        for lang in ('en', 'zh'):
            with self.subTest(lang=lang):
                home = source(lang, 'home.html')
                hero = home.split('<section', 1)[0]
                self.assertEqual(home.count('class="hero-install"'), 1)
                self.assertIn('class="hero-install"', hero)
                self.assertIn('class="hero-install-tabs" role="tablist"', hero)
                tabs = re.findall(r'<button\b([^>]*\bclass="hero-install-tab\b[^>]*)>(.*?)</button>', hero, re.S)
                self.assertEqual(len(tabs), 2)
                for (attrs, label), platform in zip(tabs, commands):
                    self.assertIn(f'data-tab="{platform}"', attrs)
                    self.assertIn('role="tab"', attrs)
                    self.assertIn('type="button"', attrs)
                    active = platform == 'unix'
                    self.assertIn(f'aria-selected="{str(active).lower()}"', attrs)
                    self.assertEqual('is-active' in attrs, active)
                    self.assertIn('macOS / Linux' if active else 'Windows (PowerShell)', label)
                panes = re.findall(r'<div class="hero-install-pane([^\"]*)" data-pane="([^"]+)">\s*<pre><code[^>]*>(.*?)</code></pre>\s*</div>', hero, re.S)
                self.assertEqual(len(panes), 2)
                for (classes, platform, command), expected in zip(panes, commands):
                    self.assertEqual(platform, expected)
                    self.assertEqual('is-active' in classes, platform == 'unix')
                    self.assertEqual(unescape(command), commands[platform])
                meta = re.search(r'<div class="hero-install-meta">(.*?)</div>', hero, re.S)
                self.assertIsNotNone(meta)
                self.assertEqual(meta[1].count('<span>'), 3)
                self.assertIn('PATH', meta[1])
                self.assertIn('SDK', meta[1])

    def test_home_embedded_playground_has_controls_and_options(self):
        for lang in ('en', 'zh'):
            with self.subTest(lang=lang):
                home = source(lang, 'home.html')
                self.assertIn('class="xu-play code-block-wrapper"', home)
                self.assertIn('id="xu-play-src"', home)
                self.assertIn('id="xu-play-run"', home)
                self.assertIn('id="xu-play-out"', home)
                self.assertIn('id="xu-play-ex"', home)
                self.assertIn('id="xu-play-ui"', home)
                self.assertIn('id="xu-play-canvas"', home)
                self.assertIn('id="xu-play-ui-status"', home)
                for option in ('hello', 'bindings', 'control', 'ints', 'coroutine', 'ui-counter', 'ui-widgets', 'ui-text-selection'):
                    self.assertIn(f'value="{option}"', home)
                self.assert_links_resolve(home, lang)

    def test_matrix_covers_all_integrations_and_transport_with_explicit_unknowns(self):
        expected = {p.stem for p in (ROOT / 'content/en/api/packages').glob('*.html')}
        unknowns = {}
        for lang in ('en', 'zh'):
            page = source(lang, 'docs/packages.html')
            table = re.search(r'<table id="integration-matrix".*?</table>', page, re.S)[0]
            self.assertEqual(table.count('<th>'), 9)
            rows = re.findall(r'<tr data-package="([^"]+)">(.*?)</tr>', table, re.S)
            self.assertEqual(len(rows), len(expected))
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
