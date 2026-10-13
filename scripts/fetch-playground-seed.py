#!/usr/bin/env python3
"""Fetch a checksum-pinned, self-hosted Xu release for the WASM build."""
import argparse
import hashlib
from pathlib import Path
import tarfile
import urllib.request

VERSION = '0.8.3'
CHECKSUMS = {
    'linux-x64': 'f6b88273e299f56b2b48623572a53e5b7145d0821b8895ffde21733d27fac911',
    'macos-arm64': '93382db7600ce5d785487192e3b2209cca0e00b5bb98a42131f76c4204499ac2',
    'macos-x64': '15aa02317a03f9388c23c34c4f8009eecf73387a43757670d42fc7aa22bd4157',
    'linux-arm64': '55bd1ebf9c24268102e8b622312b80da428efa18a032cc01c75a2ece687932d8',
}


def fetch(target: str, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    name = f'xu-v{VERSION}-{target}.tar.gz'
    archive = directory / name
    digest = CHECKSUMS[target]
    if not archive.exists() or hashlib.sha256(archive.read_bytes()).hexdigest() != digest:
        url = f'https://github.com/xulang-org/xu/releases/download/v{VERSION}/{name}'
        with urllib.request.urlopen(url, timeout=120) as response:
            data = response.read(64 * 1024 * 1024)
        if hashlib.sha256(data).hexdigest() != digest:
            raise RuntimeError(f'Xu release checksum mismatch: {name}')
        archive.write_bytes(data)
    with tarfile.open(archive) as bundle:
        for member in bundle.getmembers():
            path = (directory / member.name).resolve()
            if not path.is_relative_to(directory.resolve()) or not (member.isfile() or member.isdir()):
                raise RuntimeError(f'Unexpected release member: {member.name}')
        bundle.extractall(directory)
    root = directory / f'xu-v{VERSION}'
    if (root / 'VERSION').read_text().strip() != VERSION:
        raise RuntimeError('Xu release version mismatch')
    return root.resolve()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', choices=CHECKSUMS, required=True)
    parser.add_argument('--directory', type=Path, default=Path(__file__).resolve().parents[1] / 'build/playground-seed')
    args = parser.parse_args()
    print(fetch(args.target, args.directory))
