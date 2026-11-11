#!/usr/bin/env python3
"""Compile the site's Xu evaluator using the product compiler's wasm32 target."""
import json
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import re
import gzip


OPTIMIZER_VERSION = '132.0.0'
OPTIMIZER_FLAGS = ['-O1', '--shrink-level=1', '--strip-debug', '--enable-bulk-memory',
                   '--enable-bulk-memory-opt', '--enable-nontrapping-float-to-int']


def optimize(root: Path, wasm: Path):
    package = root / 'node_modules/binaryen'
    metadata = package / 'package.json'
    node = shutil.which('node')
    if not node or not metadata.is_file():
        raise RuntimeError('WASM optimization requires Node.js 22+ and npm ci')
    if json.loads(metadata.read_text(encoding='utf-8'))['version'] != OPTIMIZER_VERSION:
        raise RuntimeError('WASM optimizer version does not match package-lock.json; run npm ci')
    command = [node, str(package / 'bin/wasm-opt')]
    before = wasm.stat().st_size
    output = wasm.with_suffix('.optimized.wasm')
    # Avoid oversubscribing low-memory developer machines with optimizer
    # workers. This changes build resource usage, not the optimization passes.
    optimizer_env = os.environ.copy()
    optimizer_env['BINARYEN_CORES'] = '1'
    subprocess.run([*command, str(wasm),
                    *OPTIMIZER_FLAGS, '-o', str(output)], env=optimizer_env, check=True)
    output.replace(wasm)
    print(f'WASM optimized: {before} -> {wasm.stat().st_size} bytes (Binaryen {OPTIMIZER_VERSION} -O1 -s1)')
    return before


def xu_literal(value):
    # JSON escaping covers quotes/backslashes/control characters. Xu also
    # interpolates '$', including inside embedded upstream Unicode tables.
    return json.dumps(value, ensure_ascii=False).replace('$', '\\$')

def build(root: Path, xu: Path, compiler: Path):
    version = (xu / 'VERSION').read_text(encoding='utf-8').strip()
    expected = os.environ.get('XU_RELEASE_VERSION', version)
    site_version = (root / 'VERSION').read_text(encoding='utf-8').strip()
    allow_dev = os.environ.get('XU_ALLOW_DEV') == '1'
    version_pattern = r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)'
    if allow_dev:
        prerelease = r'(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)'
        version_pattern += rf'(?:-{prerelease}(?:\.{prerelease})*)?'
    banner = subprocess.check_output([str(compiler), '--version'], cwd=xu, text=True)
    identity = re.search(r'Xu Compiler Toolchain v([0-9A-Za-z.-]+)(?:\s|$)', banner)
    if (version != expected or (not allow_dev and site_version != version) or
            not re.fullmatch(version_pattern, version) or
            not identity or identity[1] != version):
        raise RuntimeError('Xu compiler, SDK sources and selected final release versions must match')
    if allow_dev:
        print('WARNING: XU_ALLOW_DEV=1: this is a dev build, not for release.', file=sys.stderr)
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
    manifest.write_text(re.sub(r'(?m)^xu:.*$', 'xu: !ver ' + version, manifest.read_text(encoding='utf-8')), encoding='utf-8')
    embedded = '@main\n#xu/ast\n#xu/parser\n\n'
    for name, source in [('runtime', 'src/runtime/str_algo.xu'), ('errors', 'src/errors/mod.xu')]:
        embedded += f'fn playground_std_{name}() string {{\n    << ' + xu_literal((xu / source).read_text(encoding='utf-8')) + '\n}\n\n'
    embedded += 'fn playground_std_maps() string {\n    << ' + xu_literal((xu / 'src/runtime/map_algo.xu').read_text(encoding='utf-8')) + '\n}\n\n'
    for name in ('draw', 'browser', 'design', 'frame', 'text_input', 'clock', 'desktop_draw_types', 'desktop_ui', 'desktop_math', 'desktop_time', 'desktop_layout', 'desktop_utf8', 'desktop_codec', 'desktop_widgets'):
        source = root / 'playground/stdlib' / (name + '.xu')
        embedded += f'fn playground_std_{name}() string {{\n    << ' + xu_literal(source.read_text(encoding='utf-8')) + '\n}\n\n'
    selection = json.loads((root / 'playground/stdlib/desktop-sources.json').read_text(encoding='utf-8'))
    base_body = re.sub(r'(?m)^[@#][^\n]*\n', '', (root / 'playground/stdlib/desktop_widgets.xu').read_text(encoding='utf-8'))
    embedded += 'fn playground_std_widgets_base_body() string {\n    << ' + xu_literal(base_body) + '\n}\n\n'
    families = selection.get('families', {})
    chunks = selection.get('extension_chunks', [])
    for chunk in chunks:
        name = chunk['name']
        source = root / 'playground/stdlib' / ('desktop_' + name + '.xu')
        content = re.sub(r'(?m)^[@#][^\n]*\n', '', source.read_text(encoding='utf-8'))
        embedded += f'fn playground_std_{name}() string {{\n    << ' + xu_literal(content) + '\n}\n\n'
    embedded += 'fn playground_widget_flags(tokens &[]ast.Token) []bool {\n    $flags := []bool{}\n'
    for family, names in families.items():
        condition = ' || '.join('token.sval == ' + json.dumps(name) for name in names)
        embedded += f'    $want_{family} := false\n    for token in tokens {{ if token.kind == ast.TOK_IDENT && ({condition}) {{ want_{family} = true }} }}\n    flags.push(want_{family})\n'
    embedded += '    $native_maps := false\n    for token in tokens { if token.kind == ast.TOK_MAP { native_maps = true } }\n    flags.push(native_maps)\n    << flags\n}\nfn playground_merge_widget_extensions(p $&parser.Parser, flags &[]bool) {\n    $needed := false\n    for flag in flags { if flag { needed = true } }\n    if !needed { playground_merge(p,playground_std_desktop_widgets(),"ui/widgets.xu")\n        << }\n    playground_merge(p,playground_std_maps(),"runtime/map_algo.xu")\n'
    indexes = {family:i for i,family in enumerate(families)}
    def condition(names):
        return ' || '.join('flags[' + str(indexes[name]) + ']' for name in families if name in names) or 'false'
    modules = sorted({chunk['module'] for chunk in chunks} - {'ui/widgets'})
    for module in modules + ['ui/widgets']:
        parts = [chunk for chunk in chunks if chunk['module'] == module]
        name = 'source_' + module.replace('/','_')
        header = '@' + module + '\n' + '\n'.join('#' + p for p in ('ui','ui/draw','ui/layout','errors','math','time','unicode/utf8','ui/internal/codec') if p != module) + '\n'
        embedded += '    $' + name + ' := ' + xu_literal(header) + '\n'
        for external in ('strings','strconv','unicode'):
            if external == module: continue
            required = {family for chunk in chunks if chunk['module'] == external for family in chunk['families']}
            embedded += f'    if {condition(required)} {{ {name} = {name} + "#{external}\\n" }}\n'
        if module == 'ui/widgets': embedded += f'    {name} = {name} + playground_std_widgets_base_body()\n'
        for part in parts:
            embedded += f'    if {condition(part["families"])} {{ {name} = {name} + playground_std_{part["name"]}() }}\n'
        required = {family for part in parts for family in part['families']}
        if module == 'ui/widgets': embedded += f'    playground_merge(p,{name},"{module}.xu")\n'
        else: embedded += f'    if {condition(required)} {{ playground_merge(p,{name},"{module}.xu") }}\n'
    embedded += '}\n'
    (runtime / 'stdlib.xu').write_text(embedded, encoding='utf-8')
    wasm = root / 'build/playground/xu-play.wasm'
    with tempfile.TemporaryDirectory(prefix='xu-play-build-') as temporary:
        env = os.environ.copy()
        env.update(XU_ROOT=str(xu), XU_STDLIB_ROOT=str(xu / 'src'), XUPATH='', XU_CACHE=temporary)
        for name in ('XUOS', 'XUARCH', 'XU_BOOT_EXTRA', 'XU_SEED', 'XU_ALLOW_ORACLE_SEED'):
            env.pop(name, None)
        subprocess.run([str(compiler), 'build', str(runtime), '--target', 'wasm32', '-o', str(wasm)], cwd=xu, env=env, check=True)
    subprocess.run([sys.executable, str(root / 'scripts/link-playground-float.py'), str(wasm)], check=True)
    unoptimized_bytes = optimize(root, wasm)
    if (xu / 'VERSION').read_text(encoding='utf-8').strip() != version:
        raise RuntimeError('Xu SDK version changed during the build; rebuild from a fixed SDK')
    (wasm.parent / 'build.json').write_text(json.dumps({
        'initial_memory_bytes': 32 * 1024 * 1024,
        'memory_limit_bytes': 256 * 1024 * 1024,
        'compiler_optimization': 'default',
        'optimizer': {'name': 'binaryen', 'version': OPTIMIZER_VERSION, 'flags': OPTIMIZER_FLAGS},
        'unoptimized_bytes': unoptimized_bytes,
        'wasm_bytes': wasm.stat().st_size,
        'gzip_bytes': len(gzip.compress(wasm.read_bytes(), compresslevel=9, mtime=0)),
        'widget_sources_sha256': hashlib.sha256((root / 'playground/stdlib/desktop-sources.json').read_bytes()).hexdigest(),
        'xu_version': version, 'wasm_sha256': hashlib.sha256(wasm.read_bytes()).hexdigest(),
        **({'dev_build': True} if allow_dev else {}),
    }, indent=2) + '\n', encoding='utf-8')
    print(f'Xu playground built (with scalar WASM helpers): {wasm}')


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    xu = Path(os.environ.get('XU_ROOT', root.parent / 'xu')).resolve()
    compiler = Path(os.environ.get('XU_BIN', xu / 'bin/xu')).resolve()
    build(root, xu, compiler)
