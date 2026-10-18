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


class PlaygroundReleaseIdentityTests(unittest.TestCase):
    def test_prerelease_banner_cannot_match_final_version_prefix(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            for name in ('site', 'sdk'):
                (base / name).mkdir()
                (base / name / 'VERSION').write_text('0.8.13\n')
            with patch.object(play.subprocess, 'check_output', return_value='Xu Compiler Toolchain v0.8.13-dev.8 (self-hosted)\n'):
                with self.assertRaisesRegex(RuntimeError, 'versions must match'):
                    play.build(base / 'site', base / 'sdk', base / 'compiler')

    def test_site_and_sdk_must_agree(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            for name, version in [('site', '0.8.12'), ('sdk', '0.8.13')]:
                (base / name).mkdir()
                (base / name / 'VERSION').write_text(version+'\n')
            with patch.object(play.subprocess, 'check_output', return_value='Xu Compiler Toolchain v0.8.13 (self-hosted)\n'):
                with self.assertRaisesRegex(RuntimeError, 'versions must match'):
                    play.build(base / 'site', base / 'sdk', base / 'compiler')
