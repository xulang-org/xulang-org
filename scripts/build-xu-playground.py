#!/usr/bin/env python3
"""Compile the Xu backend with Xu, then compile the Xu evaluator to WASM."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from prepare_wasm_compiler import prepare


def build(root: Path, seed: Path):
    driver = prepare(root, seed)
    runtime = root / 'build/runtime-source'
    runtime.mkdir(parents=True, exist_ok=True)
    for old in runtime.glob('*.xu'):
        old.unlink()
    for source in (root / 'playground/runtime').iterdir():
        if source.suffix in ('.xu', '.xun'):
            shutil.copyfile(source, runtime / source.name)
    embedded = '@main\n\n'
    for name, source in [('runtime', 'src/runtime/str_algo.xu'), ('errors', 'src/errors/mod.xu')]:
        embedded += f'fn playground_std_{name}() string {{\n    << ' + json.dumps((seed / source).read_text(), ensure_ascii=False) + '\n}\n\n'
    (runtime / 'stdlib.xu').write_text(embedded)
    compiler = root / 'build/xu-wasm'
    wasm = root / 'build/xu-play.wasm'
    with tempfile.TemporaryDirectory(prefix='xu-play-build-') as temporary:
        env = os.environ.copy()
        env.update(XU_STDLIB_ROOT=str(seed / 'src'), XUPATH='', XU_CACHE=temporary)
        for name in ('XUOS', 'XUARCH', 'XU_BOOT_EXTRA', 'XU_SEED', 'XU_ALLOW_ORACLE_SEED'):
            env.pop(name, None)
        subprocess.run([str(seed / 'bin/xu'), 'build', str(driver), '-o', str(compiler)], cwd=seed, env=env, check=True)
        subprocess.run([str(compiler), 'build', str(runtime), '--target', 'wasm32', '-O0', '-o', str(wasm)], cwd=seed, env=env, check=True)
    shutil.copyfile(wasm, root / 'www/xu-play.wasm')
    print(f'Pure Xu playground built: {root / "www/xu-play.wasm"}')


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    build(root, Path(os.environ['XU_PLAYGROUND_SEED']).resolve())
