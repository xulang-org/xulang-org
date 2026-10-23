"""Compile and execute the public chan examples with the hosted Xu compiler."""

import argparse
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--xu-root', type=Path, default=ROOT.parent / 'xu')
args = parser.parse_args()
xu_root = args.xu_root.resolve()
compiler = xu_root / 'bin/xu'
wrapper = xu_root / 'scripts/run_product_compiler.sh'
output = ROOT / 'build/chan-examples'
output.mkdir(parents=True, exist_ok=True)
environment = dict(os.environ, XU_ROOT=str(xu_root), XU_STDLIB_ROOT=str(xu_root / 'src'),
                   XUPATH='', XU_CACHE=str(output / 'cache'))
for key in ('XUOS', 'XUARCH', 'XU_BOOT_EXTRA'):
    environment.pop(key, None)

for name, expected in {
    'chan-buffered': '42\n',
    'chan-workers': '60\n',
    'chan-pipeline': '1\n4\n9\n16\n25\n',
}.items():
    source = ROOT / 'www/examples' / name / 'main.xu'
    binary = output / name
    command = [str(compiler), 'build', str(source), '-o', str(binary)]
    if wrapper.is_file():
        command = [str(wrapper), '--cwd', str(xu_root), *command]
    subprocess.run(command, cwd=xu_root, env=environment, check=True, timeout=60)
    result = subprocess.run([str(binary)], capture_output=True, text=True, check=True, timeout=15)
    if result.stdout != expected or result.stderr:
        raise AssertionError(f'{name}: expected {expected!r}, got {result.stdout!r}, stderr {result.stderr!r}')
    print(f'{name}: native compilation and output OK')
