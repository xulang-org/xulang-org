"""A prerelease compiler cannot generate a runtime stamped as the final SDK."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('playground_build', ROOT / 'scripts/build-xu-playground.py')
play = importlib.util.module_from_spec(spec)
spec.loader.exec_module(play)


def write_runtime_pin(site, version):
    runtime = site / 'playground/runtime'
    runtime.mkdir(parents=True)
    (runtime / 'xu.xun').write_text(f'xu: !ver {version}\n')


class PlaygroundReleaseIdentityTests(unittest.TestCase):
    def test_optimizer_dependency_is_required_for_wasm_builds(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            with patch.object(play.shutil, 'which', return_value=None):
                with self.assertRaisesRegex(RuntimeError, 'Node.js 22.*npm ci'):
                    play.optimize(base, base / 'runtime.wasm')

    def test_prerelease_banner_cannot_match_final_version_prefix(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            for name in ('site', 'sdk'):
                (base / name).mkdir()
                (base / name / 'VERSION').write_text('0.8.13\n')
            write_runtime_pin(base / 'site', '0.8.13')
            with patch.object(play.subprocess, 'check_output', return_value='Xu Compiler Toolchain v0.8.13-dev.8 (self-hosted)\n'):
                with self.assertRaisesRegex(RuntimeError, 'versions must match'):
                    play.build(base / 'site', base / 'sdk', base / 'compiler')

    def test_browser_pin_and_sdk_must_agree(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            for name, version in [('site', '0.8.12'), ('sdk', '0.8.13')]:
                (base / name).mkdir()
                (base / name / 'VERSION').write_text(version+'\n')
            write_runtime_pin(base / 'site', '0.8.12')
            with patch.object(play.subprocess, 'check_output', return_value='Xu Compiler Toolchain v0.8.13 (self-hosted)\n'):
                with self.assertRaisesRegex(RuntimeError, 'versions must match'):
                    play.build(base / 'site', base / 'sdk', base / 'compiler')
