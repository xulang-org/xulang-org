"""Publication must follow Xu main's final release without older-SDK fallback."""
import base64
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('release', ROOT / 'scripts/resolve-xu-release.py')
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseAlignmentTests(unittest.TestCase):
    def setUp(self):
        self.sha = 'a' * 40
        self.published = {
            'tag_name': 'v0.8.7', 'draft': False, 'prerelease': False,
            'published_at': '2026-10-13T00:00:00Z',
            'assets': [{'name': 'xu-v0.8.7-linux-arm64.tar.gz', 'digest': 'sha256:' + 'b' * 64}],
        }

    def api(self, path):
        if path == 'commits/main':
            return {'sha': self.sha}
        if path == f'contents/VERSION?ref={self.sha}':
            return {'content': base64.b64encode(b'0.8.7\n').decode()}
        if path == 'releases/tags/v0.8.7':
            return copy.deepcopy(self.published)
        self.fail('VERSION and release must use the selected main snapshot: ' + path)

    def test_matching_final_release_uses_main_version_and_exact_sdk(self):
        with patch.object(release, 'api', side_effect=self.api):
            result = release.resolve()
        self.assertEqual(result['version'], '0.8.7')
        self.assertEqual(result['commit'], self.sha)
        self.assertEqual(result['archive'], 'xu-v0.8.7-linux-arm64.tar.gz')
        self.assertEqual(result['sha256'], 'b' * 64)

    def test_unpublished_or_mismatched_release_cannot_deploy(self):
        for key, value in [('tag_name', 'v0.8.6'), ('draft', True),
                           ('prerelease', True), ('published_at', None)]:
            with self.subTest(key=key):
                original = self.published[key]
                self.published[key] = value
                with patch.object(release, 'api', side_effect=self.api), self.assertRaises(ValueError):
                    release.resolve()
                self.published[key] = original

    def test_sdk_must_match_the_main_version_and_have_a_digest(self):
        for assets in [[], [{'name': 'xu-v0.8.6-linux-arm64.tar.gz', 'digest': 'sha256:' + 'b' * 64}],
                       [{'name': 'xu-v0.8.7-linux-arm64.tar.gz', 'digest': None}]]:
            with self.subTest(assets=assets):
                self.published['assets'] = assets
                with patch.object(release, 'api', side_effect=self.api), self.assertRaises(ValueError):
                    release.resolve()

    def test_missing_exact_release_does_not_fall_back_to_latest(self):
        def missing(path):
            if path.startswith('releases/'):
                raise RuntimeError('matching release not published')
            return self.api(path)
        with patch.object(release, 'api', side_effect=missing), self.assertRaises(RuntimeError):
            release.resolve()


if __name__ == '__main__':
    unittest.main()
