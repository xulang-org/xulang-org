"""Keep downloadable installers compatible with legacy shell encodings."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class InstallerEncodingTests(unittest.TestCase):
    def test_installers_are_ascii(self):
        for name in ('install.sh', 'install.ps1'):
            with self.subTest(script=name):
                (ROOT / 'www' / name).read_bytes().decode('ascii')


if __name__ == '__main__':
    unittest.main()
