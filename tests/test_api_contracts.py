"""Contract resolution must fail closed before generation, including dry runs."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('contract_api', ROOT / 'scripts/gen-api.py')
api = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = api
spec.loader.exec_module(api)


def contract(package='sample', name='open', receiver='', params=None):
    return dict(package=package, name=name, receiver=receiver, **{
        lang: dict(purpose='Contract purpose.', params=params or {}, returns='')
        for lang in ('en', 'zh')
    })


class ContractValidationTests(unittest.TestCase):
    def generate(self, entries, source, *, preview=False, dry_run=False, extra_sources=None):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            src = root / 'sdk/src/sample'
            src.mkdir(parents=True)
            (src / 'mod.xu').write_text(source)
            for name, text in (extra_sources or {}).items():
                package = src.parent / name
                package.mkdir(parents=True)
                (package / 'mod.xu').write_text(text)
            (src.parents[1] / 'VERSION').write_text('0.10.13-dev.1' if preview else '0.10.12')
            site = root / 'site'
            (site / 'templates').mkdir(parents=True)
            (site / 'VERSION').write_text('selected release')
            template = 'api-preview-contracts.json' if preview else 'api-contracts.json'
            (site / 'templates' / template).write_text(json.dumps(entries))
            command = [sys.executable, str(ROOT / 'scripts/gen-api.py'),
                       '--src', str(src.parent), '--site', str(site)]
            if preview:
                command += ['--preview', '--package', 'sample']
            if dry_run:
                command += ['--dry-run']
            env = {k: v for k, v in os.environ.items() if k not in ('XU_PACKAGES_ROOT', 'XU_SRC', 'XU_SITE_ROOT')}
            result = subprocess.run(command, capture_output=True, text=True, env=env)
            if result.returncode:
                self.assertFalse((site / 'content').exists(), result.stderr)
                self.assertEqual((site / 'VERSION').read_text(), 'selected release')
            elif not dry_run:
                for lang in ('en', 'zh'):
                    page = (site / 'content' / lang / 'api' / ('preview' if preview else '') / 'sample.html').read_text()
                    for entry in entries:
                        if entry['package'] == 'sample':
                            self.assertIn(api.esc(entry[lang]['purpose']), page)
            return result

    def test_missing_ambiguous_and_duplicate_symbols_exit_nonzero(self):
        cases = [
            ([contract(name='missing')], 'pub fn open() {}', 'resolves to 0 declarations'),
            ([contract(package='missing')], 'pub fn open() {}', 'resolves to 0 declarations'),
            ([contract()], 'pub fn open(a int) {}\npub fn open(a string) {}', 'resolves to 2 declarations'),
            ([contract(), contract()], 'pub fn open() {}', 'duplicate contract'),
            ([contract(receiver='&mut Reader'), contract(receiver='$&Reader')],
             'pub fn (r $&Reader) open() {}', 'duplicate contract'),
            ([contract()], 'pub fn (r $&Reader) open() {}', 'resolves to 0 declarations'),
        ]
        for entries, source, diagnostic in cases:
            for preview in (False, True):
                for dry_run in (False, True):
                    with self.subTest(entries=entries, preview=preview, dry_run=dry_run):
                        result = self.generate(entries, source, preview=preview, dry_run=dry_run)
                        self.assertNotEqual(result.returncode, 0, result.stdout)
                        self.assertIn(diagnostic, result.stderr)

    def test_stale_parameter_and_field_keys_exit_nonzero(self):
        for name, source in [('open', 'pub fn open(d int) {}'),
                             ('Options', 'pub struct Options {\n    pub size int\n}')]:
            for lang in ('en', 'zh'):
                entry = contract(name=name)
                entry[lang]['params'] = {'stale': 'obsolete name'}
                with self.subTest(name=name, lang=lang):
                    result = self.generate([entry], source, dry_run=True)
                    self.assertNotEqual(result.returncode, 0, result.stdout)
                    self.assertIn('unknown parameter/field', result.stderr)
                    self.assertIn(lang, result.stderr)

    def test_valid_fields_and_normalized_receivers_generate(self):
        entries = [contract(name='Options', params={'size': 'capacity'}),
                   contract(receiver='&mut Reader', params={'n': 'count'})]
        source = ('pub struct Options {\n    pub size int\n}\n'
                  'pub fn (r $&Reader) open(n int) {}')
        for preview in (False, True):
            with self.subTest(preview=preview):
                result = self.generate(entries, source, preview=preview)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_scoped_preview_validates_unrendered_contracts(self):
        for name, expected in [('other', 0), ('missing', 1)]:
            with self.subTest(name=name):
                result = self.generate([contract(package=name)], 'pub fn example() {}', preview=True,
                                       extra_sources={'other': 'pub fn open() {}'})
                self.assertEqual(result.returncode, expected, result.stderr)


class UIReceiverRegressionTests(unittest.TestCase):
    def test_all_17_audited_receivers_in_release_and_preview(self):
        # Frozen identities from analysis-lang-api.zh.md E31, signatures
        # reverified against the v0.10.12 archive (no dev checkout required).
        rows = json.loads((ROOT / 'tests/fixtures/api_ui_receivers.json').read_text())
        self.assertEqual(len(rows), 17)
        identities = {(row['package'], row['receiver'], row['name']) for row in rows}
        for preview in (False, True):
            template = 'api-preview-contracts.json' if preview else 'api-contracts.json'
            entries = [entry for entry in json.loads((ROOT / 'templates' / template).read_text())
                       if (entry['package'], entry.get('receiver', ''), entry['name']) in identities]
            self.assertEqual(len(entries), 17)
            for spelling in ('$&', '&mut '):
                with self.subTest(preview=preview, spelling=spelling), tempfile.TemporaryDirectory() as temporary:
                    site = Path(temporary)
                    (site / 'templates').mkdir()
                    (site / 'templates' / template).write_text(json.dumps(entries))
                    packages = {}
                    for row in rows:
                        package = packages.setdefault(row['package'], api.Package(row['package'], '#' + row['package']))
                        sig = row['signature'].replace('$&', spelling)
                        parsed = api.parse_fn_sig(sig)
                        parsed['params'].insert(0, api.Param(parsed['recv_name'], parsed['recv_type'], is_recv=True))
                        package.items.append(api.Item(sig=sig, **parsed))
                    api.write_packages(str(site), list(packages.values()), '0.10.12', 'a' * 64 if preview else '')
                    for lang in ('en', 'zh'):
                        for package in packages.values():
                            page = (site / 'content' / lang / 'api' / ('preview' if preview else '') / (package.path + '.html')).read_text()
                            self.assertNotIn('value receiver', page)
                            for entry in entries:
                                if entry['package'] == package.path:
                                    self.assertIn(api.esc(entry[lang]['purpose']), page)
                            for item in package.items:
                                self.assertIn(api.highlight_xu(item.sig), page)
                                receiver = api.params_for(package, item, lang)[0][2]
                                self.assertIn('独占借用' if lang == 'zh' else 'exclusive borrow', receiver)
                                self.assertNotIn('value receiver', receiver)
                                self.assertIn('独占借用' if lang == 'zh' else 'exclusive borrow', api.type_note(item.recv_type, lang == 'zh'))

    def test_screen_factories_and_control_methods_use_same_normalization(self):
        for spelling in ('$&', '&mut '):
            factory = api.Item('method', 'input', '', recv_type=spelling + 'Screen', ret='int')
            control = api.Item('method', 'input', '', recv_type=spelling + 'Button', ret='Action')
            with self.subTest(spelling=spelling):
                self.assertTrue(api.widget_constructor(factory))
                self.assertEqual(api.widget_constructor(control), '')
                self.assertIn('node ID', api.returns_for('ui/widgets', factory, 'en'))
        for typ, expected in [('&View', 'borrow'), ('View', 'value receiver')]:
            self.assertIn(expected, api.param_meaning('ui/widgets', '', api.Param('view', typ, is_recv=True), 'en'))


if __name__ == '__main__':
    unittest.main()
