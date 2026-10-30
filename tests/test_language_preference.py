"""Run behavioral language-choice checks when Node is available locally."""
from pathlib import Path
import shutil
import subprocess
import unittest


class LanguagePreferenceTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node is optional for static builds')
    def test_language_preference_behavior(self):
        result = subprocess.run(['node', '--test', str(Path(__file__).with_suffix('.mjs'))],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
