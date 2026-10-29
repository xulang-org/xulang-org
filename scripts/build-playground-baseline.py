#!/usr/bin/env python3
"""Build an old evaluator with timing entry points, without changing its VM.

Use the same SDK as the candidate to avoid compiler-version confounding:
  python3 scripts/build-playground-baseline.py --revision <pre-change-commit> \
    --xu-root /path/to/sdk --output /tmp/playground-baseline
  node scripts/bench-playground.mjs \
    --wasm=/tmp/playground-baseline/build/playground/xu-play.wasm \
    --cache=false --checkpoints=false --rounds=3
"""
import argparse
import io
import os
from pathlib import Path
import subprocess
import tarfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--xu-root', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    # Refuse to overwrite a checkout or a previous measurement.
    output.mkdir(parents=True, exist_ok=False)
    archive = subprocess.check_output(['git', 'archive', args.revision, 'playground',
        'scripts/build-xu-playground.py', 'scripts/link-playground-float.py', 'VERSION'], cwd=root)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(output, filter='data')
    source = output / 'playground/runtime/main.xu'
    text = source.read_text()
    signature = 'pub fn xu_eval(ptr int, length int) int {'
    tail = '    << vm_run(&m)'
    if text.count(signature) != 1 or text.count(tail) != 1 or 'xu_prepare' in text:
        raise RuntimeError('Expected the pre-split evaluator; choose a revision before this optimization')
    text = text.replace(tail, '    << m').replace(signature,
        signature + '\n    m := xu_prepare(ptr, length)\n    << vm_run(&m)\n}\n\n'
        'pub fn xu_prepare(ptr int, length int) types.Mir {')
    text += '\npub fn xu_execute(m &types.Mir) int { << vm_run(m) }\n'
    source.write_text(text)
    env = dict(os.environ, XU_ALLOW_DEV='1', XU_ROOT=str(args.xu_root.resolve()))
    subprocess.run(['python3', str(output / 'scripts/build-xu-playground.py')], cwd=output, env=env, check=True)


if __name__ == '__main__':
    main()
