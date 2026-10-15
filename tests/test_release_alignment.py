"""Publication must follow Xu's latest official release without dev or draft fallbacks."""
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
            'tag_name': 'v0.8.8', 'draft': False, 'prerelease': False,
            'published_at': '2026-10-15T00:00:00Z',
            'target_commitish': self.sha,
            'assets': [{'name': 'xu-v0.8.8-linux-arm64.tar.gz', 'digest': 'sha256:' + 'b' * 64}],
        }

    def api(self, path):
        if path == 'releases/latest':
            return copy.deepcopy(self.published)
        if path == 'releases/tags/v0.8.8':
            return copy.deepcopy(self.published)
        if path == 'commits/v0.8.8':
            return {'sha': self.sha}
        self.fail('Unexpected API call: ' + path)

    def test_latest_official_release_resolved(self):
        with patch.object(release, 'api', side_effect=self.api):
            result = release.resolve()
        self.assertEqual(result['version'], '0.8.8')
        self.assertEqual(result['commit'], self.sha)
        self.assertEqual(result['archive'], 'xu-v0.8.8-linux-arm64.tar.gz')
        self.assertEqual(result['sha256'], 'b' * 64)

    def test_unpublished_or_draft_or_prerelease_cannot_deploy(self):
        for key, value in [('tag_name', 'v0.8.8-dev.1'), ('draft', True),
                           ('prerelease', True), ('published_at', None)]:
            with self.subTest(key=key):
                original = self.published[key]
                self.published[key] = value
                with patch.object(release, 'api', side_effect=self.api), self.assertRaises(ValueError):
                    release.resolve()
                self.published[key] = original

    def test_sdk_must_match_and_have_a_digest(self):
        for assets in [[], [{'name': 'xu-v0.8.7-linux-arm64.tar.gz', 'digest': 'sha256:' + 'b' * 64}],
                       [{'name': 'xu-v0.8.8-linux-arm64.tar.gz', 'digest': None}]]:
            with self.subTest(assets=assets):
                self.published['assets'] = assets
                with patch.object(release, 'api', side_effect=self.api), self.assertRaises(ValueError):
                    release.resolve()

    def test_target_version_override(self):
        with patch.object(release, 'api', side_effect=self.api):
            result = release.resolve('0.8.8')
        self.assertEqual(result['version'], '0.8.8')
        self.assertEqual(result['tag'], 'v0.8.8')

    def test_missing_latest_release_raises(self):
        def missing(path):
            raise RuntimeError('latest release not published')
        with patch.object(release, 'api', side_effect=missing), self.assertRaises(RuntimeError):
            release.resolve()


if __name__ == '__main__':
    unittest.main()

