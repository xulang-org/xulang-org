"""Component coverage, released API links, and repeatable regeneration."""
import importlib.util
import html
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
CATALOG = json.loads((ROOT / 'templates/widgets.json').read_text(encoding='utf-8'))


def generator(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WidgetPages(unittest.TestCase):
    def test_visual_components_have_bilingual_detail_pages_and_experiences(self):
        components = CATALOG['components']
        self.assertEqual(len(components), 46)
        self.assertEqual(len({c['slug'] for c in components}), 46)
        published = json.loads((ROOT / 'www/widgets.json').read_text(encoding='utf-8'))
        projects = json.loads((ROOT / 'www/xu-play-examples.json').read_text(encoding='utf-8'))['projects']
        self.assertEqual([c['slug'] for c in published['components']], [c['slug'] for c in components])
        for lang in ('en', 'zh'):
            directory = (ROOT / f'content/{lang}/api/ui/widgets.html').read_text(encoding='utf-8')
            for c in published['components']:
                with self.subTest(lang=lang, component=c['name']):
                    page = (ROOT / f'content/{lang}/api/ui/widgets/{c["slug"]}.html').read_text(encoding='utf-8')
                    self.assertIn('/api/ui/widgets/' + c['slug'], directory)
                    self.assertIn('aria-current="page">' + c['name'], page)
                    self.assertIn('<!--xu-api-version: ' + (ROOT / 'VERSION').read_text().strip(), page)
                    self.assertIn(c['description'][lang], page)
                    self.assertIn(html.escape(generator('gen-widgets').native_source(c)), page)
                    factory = c['factory'] if c.get('factory_kind') == 'fn' else '--Screen-' + c['factory']
                    self.assertIn('id="' + factory + '"', page)
                    if c['project']:
                        self.assertIn('example=' + c['project'], page)
                        self.assertEqual(projects[c['project']]['component'], c['slug'])
                    else:
                        self.assertIn('widget=' + c['slug'], page)
                        self.assertIn('不执行 Xu' if lang == 'zh' else 'without executing Xu', page)

    def test_generators_are_idempotent(self):
        self.assertEqual(generator('gen-widget-examples').generate(check=True), [])
        self.assertEqual(generator('gen-widgets').generate(check=True), [])

    def test_experience_sources_are_the_actual_project_sources(self):
        projects = json.loads((ROOT / 'www/xu-play-examples.json').read_text(encoding='utf-8'))['projects']
        for key, project in projects.items():
            if project.get('component'):
                self.assertEqual((ROOT / f'playground/examples/{key}.xu').read_text(encoding='utf-8'), project['files']['main.xu'])

    def test_page_fragment_links_point_to_real_declarations(self):
        for lang in ('en', 'zh'):
            module = (ROOT / f'content/{lang}/api/ui/widgets.html').read_text(encoding='utf-8')
            ids = set(re.findall(r'\bid="([^"]+)"', module))
            for page in (ROOT / f'content/{lang}/api/ui/widgets').glob('*.html'):
                for anchor in re.findall(r'/api/ui/widgets#([^" ]+)', page.read_text(encoding='utf-8')):
                    self.assertIn(anchor, ids, (page, anchor))
