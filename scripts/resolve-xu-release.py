#!/usr/bin/env python3
"""Resolve a published SDK matching Xu's latest official release."""
import argparse
import json
from pathlib import Path
import re
import subprocess

REPO = 'xulang-org/xu'


def api(path):
    result = subprocess.run(['gh', 'api', f'repos/{REPO}/{path}'],
                            capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f'Cannot read Xu {path}: {result.stderr.strip()}')
    return json.loads(result.stdout)


def resolve(target_version=None):
    if target_version:
        tag = 'v' + target_version.lstrip('v')
        release = api(f'releases/tags/{tag}')
    else:
        release = api('releases/latest')

    if release.get('draft') or release.get('prerelease') or not release.get('published_at'):
        raise ValueError(f'Xu release is draft or prerelease: {release.get("tag_name")}')

    tag = release['tag_name']
    version = tag.lstrip('v')
    if not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', version):
        raise ValueError(f'Invalid official Xu release version: {version}')

    name = f'xu-{tag}-linux-arm64.tar.gz'
    asset = next((item for item in release.get('assets', []) if item['name'] == name), None)
    if not asset or not re.fullmatch(r'sha256:[0-9a-f]{64}', asset.get('digest') or ''):
        raise ValueError(f'Matching Xu SDK with a SHA-256 digest is unavailable: {name}')

    commit = release.get('target_commitish') or ''
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        try:
            commit = api(f'commits/{tag}')['sha']
        except Exception:
            commit = '0' * 40

    return {'version': version, 'tag': tag, 'commit': commit,
            'archive': name, 'sha256': asset['digest'][7:]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', type=str, help='Explicit release version to resolve')
    parser.add_argument('--github-env', type=Path)
    args = parser.parse_args()
    try:
        release = resolve(target_version=args.version)
    except (RuntimeError, ValueError, KeyError) as error:
        parser.exit(1, f'Xu release alignment failed: {error}\n')
    if args.github_env:
        with args.github_env.open('a') as stream:
            for name, key in [('XU_RELEASE_VERSION', 'version'), ('XU_MAIN_SHA', 'commit'),
                              ('XU_SDK_ARCHIVE', 'archive'), ('XU_SDK_SHA256', 'sha256')]:
                stream.write(f'{name}={release[key]}\n')
    print(json.dumps(release))


if __name__ == '__main__':
    main()
