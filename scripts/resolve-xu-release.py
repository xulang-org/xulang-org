#!/usr/bin/env python3
"""Resolve a published SDK whose version matches an immutable Xu main commit."""
import argparse
import base64
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


def resolve():
    commit = api('commits/main')['sha']
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('Invalid Xu main commit')
    content = api(f'contents/VERSION?ref={commit}')
    version = base64.b64decode(content['content']).decode().strip()
    if not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?', version):
        raise ValueError('Invalid Xu main VERSION')
    tag = 'v' + version
    release = api(f'releases/tags/{tag}')
    if release['tag_name'] != tag or release['draft'] or not release['published_at']:
        raise ValueError(f'Xu main {version} does not have a matching release')
    name = f'xu-{tag}-linux-arm64.tar.gz'
    asset = next((item for item in release['assets'] if item['name'] == name), None)
    if not asset or not re.fullmatch(r'sha256:[0-9a-f]{64}', asset.get('digest') or ''):
        raise ValueError(f'Matching Xu SDK with a SHA-256 digest is unavailable: {name}')
    return {'version': version, 'tag': tag, 'commit': commit,
            'archive': name, 'sha256': asset['digest'][7:]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--github-env', type=Path)
    args = parser.parse_args()
    try:
        release = resolve()
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
