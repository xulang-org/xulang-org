"""Public API extraction and companion package generation."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('gen_api', ROOT / 'scripts/gen-api.py')
api = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = api
spec.loader.exec_module(api)


class APIGenerationTests(unittest.TestCase):
    def test_usage_links_and_downloads_include_examples_after_inline_limit(self):
        examples = [api.Example(f'examples/{i}/main.xu', '#ui/widgets\n', 'a' * 40,
                               {'ui/widgets': {'style_switcher'} if i == 3 else {'button'}})
                    for i in range(4)]
        package = api.Package('ui/widgets', '#ui/widgets', items=[
            api.Item('fn', 'style_switcher', 'pub fn style_switcher() StyleSwitcher')])
        for lang in ('en', 'zh'):
            page = api.render_page(package, lang, '0.10.2', examples=examples)
            related = examples[3]
            self.assertIn(f'id="{related.anchor}"', page)
            self.assertIn(f'href="#{related.anchor}"', page)
            self.assertIn(f'href="{related.asset_url}" download', page)

    def test_released_ui_examples_cover_every_public_package(self):
        names = ('ui', 'ui/draw', 'ui/layout', 'ui/widgets', 'ui/webview')
        packages = [api.Package(name, '#' + name) for name in names]
        examples = api.load_examples(str(ROOT), packages, (ROOT / 'VERSION').read_text().strip())
        for name in names:
            self.assertTrue(examples.get(name), name)
        collected = {ex.path for group in examples.values() for ex in group}
        for name in ('draw_gallery', 'widgets', 'text_input', 'desktop_services', 'multiwindow',
                     'workbench', 'editor_workbench', 'style_gallery', 'webview_requests', 'controls_gallery',
                     'component_workshop', 'component_catalog', 'interaction_gallery', 'webview_component', 'xacp_screen'):
            self.assertIn(f'examples/16_ui_webview/{name}/main.xu', collected)

    def test_multifile_examples_show_registration_sources_after_inline_limit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkout, site = root / 'examples', root / 'site'
            project = 'examples/16_ui_webview/component_workshop/'
            sources = {
                project + 'main.xu': '@main\n#ui/widgets\nfn main() { widgets.screen() }\n',
                project + 'events.xu': '@main\n#ui/widgets\nfn register() { d.on(1, widgets.ACTION_ACTIVATE, save) }\n',
                project + 'style.xu': '@main\n#ui/widgets\nfn appearance() { widgets.dark_styles() }\n',
            }
            for path, source in sources.items():
                target = checkout / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(source)
            (checkout / project / 'xu.xun').write_text('xu: !ver 0.10.13-dev.1\n')
            (site / 'templates').mkdir(parents=True)
            (site / 'templates/api-examples.json').write_text(json.dumps(list(sources)))
            api.refresh_examples(str(site), str(checkout), 'a' * 40, '0.10.12')
            package = api.Package('ui/widgets', '#ui/widgets')
            examples = api.load_examples(str(site), [package], '0.10.12')['ui/widgets']
            self.assertEqual(len(examples), 1)
            self.assertIn('ACTION_ACTIVATE', examples[0].uses['ui/widgets'])
            self.assertEqual(examples[0].required_sdk, '0.10.13-dev.1')
            plain = api.Example('examples/plain/main.xu', '#ui/widgets\n', 'a' * 40, {})
            for lang in ('en', 'zh'):
                for group in (examples, [plain] * 3 + examples):
                    page = api.render_examples(group, lang)
                    self.assertIn('0.10.13-dev.1', page)
                    self.assertIn('d.on(', page)
                    self.assertIn('events.xu', page)
                    self.assertIn('style.xu', page)
                    self.assertIn('Complete project' if lang == 'en' else '完整工程', page)
            asset = site / 'www/api-examples/sources' / (project + 'events.xu')
            asset.write_text('tampered companion')
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                api.load_examples(str(site), [package], '0.10.12')

    def test_working_tree_examples_label_sdk_and_link_companions(self):
        main = api.Example('examples/ui/main.xu', '#ui/widgets\n', 'b' * 40,
                           {'ui/widgets': {'action_dispatcher'}}, 'working-tree',
                           ('examples/ui/events.xu', 'examples/ui/style.xu'))
        committed = api.Example('examples/other/main.xu', '#ui/widgets\n', 'a' * 40,
                                {'ui/widgets': {'button'}})
        for lang in ('en', 'zh'):
            # Cover inline and overflow downloads without assuming snapshots stay uncommitted forever.
            for group in ([main], [committed] * 3 + [main]):
                page = api.render_examples(group, lang)
                self.assertIn('ActionDispatcher', page)
                self.assertNotIn(main.project_url, page)
                for companion in main.companions:
                    self.assertIn('href="/api-examples/sources/' + companion + '" download', page)

    def test_example_import_aliases_ignore_comments_and_strings(self):
        uses = api.example_uses('''@main
#io
db #github.com/xulang-org/packages/mysql
// #net
/*
#os
os.remove("ignored")
*/
fn main() {
    text := "io.fake() db.fake()"
    io.read(text)
    db.driver()
}
''')
        self.assertEqual(uses, {'io': {'read'}, 'github.com/xulang-org/packages/mysql': {'driver'}})

    def test_scoped_refresh_preserves_other_sources_and_immutable_refs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            site, checkout = root / 'site', root / 'checkout'
            paths = ['examples/one/main.xu', 'examples/two/main.xu']
            (site / 'templates').mkdir(parents=True)
            (site / 'templates/api-examples.json').write_text(json.dumps(paths))
            for path in paths:
                source = checkout / path
                source.parent.mkdir(parents=True, exist_ok=True)
                source.write_text('@main\n#io\nfn main() { io.read() }\n')
            api.refresh_examples(str(site), str(checkout), 'a' * 40, '0.10.12')
            (checkout / paths[0]).write_text('@main\n#io\nfn main() { io.write() }\n')
            # A scoped refresh must not read the other project from the checkout.
            (checkout / paths[1]).unlink()
            api.refresh_examples(str(site), str(checkout), 'b' * 40, '0.10.12', ['examples/one'])
            examples = api.load_examples(str(site), [api.Package('io', '#io')], '0.10.12')['io']
            by_path = {example.path: example for example in examples}
            self.assertEqual(by_path[paths[0]].ref, 'b' * 40)
            self.assertEqual(by_path[paths[1]].ref, 'a' * 40)
            self.assertIn('io.read()', by_path[paths[1]].source)
            with self.assertRaisesRegex(ValueError, 'unknown example project'):
                api.refresh_examples(str(site), str(checkout), 'b' * 40, '0.10.12', ['examples/missing'])
            with self.assertRaisesRegex(ValueError, 'selected SDK'):
                api.refresh_examples(str(site), str(checkout), 'b' * 40, '0.10.13', ['examples/one'])
            (site / 'www/api-examples/sources' / paths[1]).write_text('tampered')
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                api.refresh_examples(str(site), str(checkout), 'b' * 40, '0.10.12', ['examples/one'])

    def test_bundled_examples_preserve_code_and_survive_without_checkout(self):
        class Code(HTMLParser):
            def __init__(self, source):
                super().__init__()
                self.examples = []
                self.current = None
                self.feed(source)

            def handle_starttag(self, tag, attrs):
                if tag == 'code' and dict(attrs).get('class') == 'language-xu':
                    self.current = ''

            def handle_data(self, data):
                if self.current is not None:
                    self.current += data

            def handle_endtag(self, tag):
                if tag == 'code' and self.current is not None:
                    self.examples.append(self.current)
                    self.current = None

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            checkout = root / 'examples'
            relative = 'examples/01_io/main.xu'
            source = '@main\n#io\ndb #github.com/xulang-org/packages/mysql\n// "fn" and <html> remain comments\nfn main() {\n    io.read("http://localhost/<script> & string")\n    db.driver()\n}\n'
            original = checkout / relative
            original.parent.mkdir(parents=True)
            original.write_text(source)
            site = root / 'site'
            (site / 'templates').mkdir(parents=True)
            (site / 'templates/api-examples.json').write_text(json.dumps([relative]))
            guide = site / 'templates/api-guides/en/io.html'
            guide.parent.mkdir(parents=True)
            guide.write_text('<p>Curated guide stays.</p>')
            packages = [api.Package('io', '#io', items=[api.Item('fn', 'read', 'pub fn read(s string)')]),
                        api.Package('packages/mysql', 'db #github.com/xulang-org/packages/mysql', module='github.com/xulang-org/packages')]
            api.refresh_examples(str(site), str(checkout), 'a' * 40, '0.9.4')
            original.unlink()
            for _ in range(2):
                api.write_packages(str(site), packages, '0.9.4')
                for lang in ('en', 'zh'):
                    page = (site / f'content/{lang}/api/io.html').read_text()
                    self.assertEqual(Code(page).examples, [source.rstrip()])
                    self.assertNotIn('<script>', page)
                    self.assertIn('class="code-block-wrapper xu-local-only"', page)
                    self.assertIn('href="/api-examples/sources/' + relative + '" download', page)
                    self.assertIn('https://github.com/xulang-org/examples/tree/' + 'a' * 40, page)
                    self.assertIn('href="#example-', page)
                    if lang == 'en':
                        self.assertIn('Curated guide stays.', page)
                    external = (site / f'content/{lang}/api/packages/mysql.html').read_text()
                    self.assertEqual(Code(external).examples, [source.rstrip()])
                    index = (site / f'content/{lang}/api/index.html').read_text()
                    self.assertIn('/api/io#examples', index)
            asset = site / 'www/api-examples/sources' / relative
            asset.write_text('tampered')
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                api.write_packages(str(site), packages, '0.9.4')

    def test_example_snapshot_rejects_invalid_sources_and_stale_sdk(self):
        with tempfile.TemporaryDirectory() as temporary:
            site = Path(temporary)
            (site / 'templates').mkdir()
            (site / 'templates/api-examples.json').write_text('["examples/../../private.xu"]')
            with self.assertRaisesRegex(ValueError, 'invalid example source path'):
                api.refresh_examples(str(site), str(site), 'a' * 40, '0.9.4')
            self.assertFalse((site / 'www/api-examples').exists())
            (site / 'www/api-examples').mkdir(parents=True)
            (site / 'www/api-examples/index.json').write_text('{"xu_version": "0.9.3"}')
            with self.assertRaisesRegex(ValueError, 'checked and refreshed'):
                api.load_examples(str(site), [], '0.9.4')

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
pub fn read#T: Reader(src $&T) string {
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
                prefix = '' if lang == 'en' else '/zh'
                self.assertIn(f'href="{prefix}/docs/packages"', package)
                self.assertIn('mysql #github.com/xulang-org/packages/mysql', package)
                self.assertIn('0.1.1', package)
                self.assertIn('<!--xu-api-version: 0.8.4-->', package)
                self.assertIn('Xu {{xu_version}}', package)
                index = (site / f'content/{lang}/api/index.html').read_text()
                self.assertIn(f'href="{prefix}/api/packages/mysql"', index)
                self.assertNotIn('/api/internal', index)
            self.assertEqual(css.read_text(), styles)
            self.assertIn('version: !ver 0.8.4\nxu: !ver 0.8.4', (site / 'xu.xun').read_text())
            self.assertEqual((site / 'VERSION').read_text().strip(), '0.8.4')
            self.assertIn('version: !ver 0.1.1\nxu: !ver 0.8.4', runtime.read_text())
            parsed = api.load_package(str(source), 'io')
            self.assertEqual((parsed.n_fn, parsed.n_type, parsed.n_iface), (1, 2, 1))


if __name__ == '__main__':
    unittest.main()
