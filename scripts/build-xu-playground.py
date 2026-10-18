#!/usr/bin/env python3
"""Compile the site's Xu evaluator using the product compiler's wasm32 target."""
import json
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import re


def build(root: Path, xu: Path, compiler: Path):
    version = (xu / 'VERSION').read_text().strip()
    expected = os.environ.get('XU_RELEASE_VERSION', version)
    site_version = (root / 'VERSION').read_text().strip()
    banner = subprocess.check_output([str(compiler), '--version'], cwd=xu, text=True)
    identity = re.search(r'Xu Compiler Toolchain v([0-9A-Za-z.-]+)(?:\s|$)', banner)
    if (version != expected or site_version != version or
            not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', version) or
            not identity or identity[1] != version):
        raise RuntimeError('Xu compiler, SDK sources and selected final release versions must match')
    help_text = subprocess.check_output([str(compiler), '--help'], cwd=xu, text=True)
    if 'wasm32' not in help_text:
        raise RuntimeError('Xu compiler lacks wasm32 support; rebuild Xu or install a WASM-capable SDK')
    runtime = root / 'build/playground/source'
    runtime.mkdir(parents=True, exist_ok=True)
    for old in runtime.glob('*.xu'):
        old.unlink()
    for source in (root / 'playground/runtime').iterdir():
        if source.suffix in ('.xu', '.xun'):
            shutil.copyfile(source, runtime / source.name)
    manifest = runtime / 'xu.xun'
    manifest.write_text(re.sub(r'(?m)^xu:.*$', 'xu: !ver ' + version, manifest.read_text()))
    embedded = '@main\n\n'
    for name, source in [('runtime', 'src/runtime/str_algo.xu'), ('errors', 'src/errors/mod.xu')]:
        embedded += f'fn playground_std_{name}() string {{\n    << ' + json.dumps((xu / source).read_text(), ensure_ascii=False) + '\n}\n\n'
    (runtime / 'stdlib.xu').write_text(embedded)
    wasm = root / 'build/playground/xu-play.wasm'
    with tempfile.TemporaryDirectory(prefix='xu-play-build-') as temporary:
        env = os.environ.copy()
        env.update(XU_ROOT=str(xu), XU_STDLIB_ROOT=str(xu / 'src'), XUPATH='', XU_CACHE=temporary)
        for name in ('XUOS', 'XUARCH', 'XU_BOOT_EXTRA', 'XU_SEED', 'XU_ALLOW_ORACLE_SEED'):
            env.pop(name, None)
        subprocess.run([str(compiler), 'build', str(runtime), '--target', 'wasm32', '-O0', '-o', str(wasm)], cwd=xu, env=env, check=True)
    if (xu / 'VERSION').read_text().strip() != version:
        raise RuntimeError('Xu SDK version changed during the build; rebuild from a fixed SDK')
    (wasm.parent / 'build.json').write_text(json.dumps({
        'xu_version': version, 'wasm_sha256': hashlib.sha256(wasm.read_bytes()).hexdigest(),
    }, indent=2) + '\n')
    print(f'Pure Xu playground built: {wasm}')


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    xu = Path(os.environ.get('XU_ROOT', root.parent / 'xu')).resolve()
    compiler = Path(os.environ.get('XU_BIN', xu / 'bin/xu')).resolve()
    build(root, xu, compiler)
