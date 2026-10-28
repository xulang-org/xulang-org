"""Development SDKs require explicit opt-in and retain compiler identity checks."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build_gate', ROOT / 'scripts/build-xu-playground.py')
play = importlib.util.module_from_spec(spec)
spec.loader.exec_module(play)


class BuildGateTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        base = Path(temporary.name)
        self.root, self.xu = base / 'site', base / 'sdk'
        for directory in (self.root, self.xu):
            directory.mkdir()
        (self.root / 'VERSION').write_text('0.10.10\n')
        (self.xu / 'VERSION').write_text('0.10.10-dev.1\n')
        self.env = patch.dict(os.environ, {}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def build(self):
        play.build(self.root, self.xu, self.xu / 'bin/xu')

    def prepare_sources(self):
        runtime = self.root / 'playground/runtime'
        runtime.mkdir(parents=True)
        (runtime / 'xu.xun').write_text('xu: !ver 0.10.10\n')
        stdlib = self.root / 'playground/stdlib'
        stdlib.mkdir()
        for source in (ROOT / 'playground/stdlib').glob('*.xu'):
            (stdlib / source.name).write_text('')
        (stdlib / 'desktop-sources.json').write_text('{}')
        for relative in ('src/runtime/str_algo.xu', 'src/errors/mod.xu'):
            source = self.xu / relative
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text('')

    def mock_run(self, command, **kwargs):
        if '-o' in command:
            Path(command[command.index('-o') + 1]).write_bytes(b'mocked wasm')

    def test_strict_rejects_dev_version(self):
        for value in (None, '0', 'true'):
            with self.subTest(allow_dev=value):
                if value is not None:
                    os.environ['XU_ALLOW_DEV'] = value
                with patch.object(play.subprocess, 'check_output', return_value=
                                  'Xu Compiler Toolchain v0.10.10-dev.1\n'), \
                        patch.object(play.subprocess, 'run') as run:
                    with self.assertRaisesRegex(RuntimeError, 'versions must match'):
                        self.build()
                    run.assert_not_called()

    def test_opt_in_accepts_dev_and_marks_metadata(self):
        os.environ.update(XU_ALLOW_DEV='1', XU_RELEASE_VERSION='0.10.10-dev.1')
        self.prepare_sources()
        stderr = io.StringIO()
        with patch.object(play.subprocess, 'check_output', side_effect=[
                'Xu Compiler Toolchain v0.10.10-dev.1 (self-hosted)\n', 'wasm32']), \
                patch.object(play.subprocess, 'run', side_effect=self.mock_run) as run, \
                contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(io.StringIO()):
            self.build()
        self.assertEqual(run.call_count, 2)
        self.assertIn('dev build, not for release', stderr.getvalue())
        metadata = json.loads((self.root / 'build/playground/build.json').read_text())
        self.assertEqual(metadata['xu_version'], '0.10.10-dev.1')
        self.assertIs(metadata['dev_build'], True)
        self.assertIn('xu: !ver 0.10.10-dev.1',
                      (self.root / 'build/playground/source/xu.xun').read_text())

    def test_opt_in_still_requires_matching_identity_and_override(self):
        os.environ['XU_ALLOW_DEV'] = '1'
        for banner, expected in [('0.10.10', '0.10.10-dev.1'),
                                 ('0.10.10-dev.1', '0.10.10')]:
            with self.subTest(banner=banner, expected=expected):
                os.environ['XU_RELEASE_VERSION'] = expected
                with patch.object(play.subprocess, 'check_output', return_value=
                                  f'Xu Compiler Toolchain v{banner}\n'):
                    with self.assertRaisesRegex(RuntimeError, 'versions must match'):
                        self.build()


if __name__ == '__main__':
    unittest.main()
