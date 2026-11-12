#!/usr/bin/env python3
"""Build the typed-MIR playground prototype with the selected released SDK."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "playground" / "typed"
WASM_HEADER = b"\x00asm\x01\x00\x00\x00"
MAX_MEMORY_PAGES = 4096
PLAYGROUND_EXPORTS = ("playground_prepare", "playground_execute")
UI_SOURCES = (
    "draw", "browser", "desktop_ui", "design", "text_input", "frame",
    "desktop_draw_types", "desktop_math", "desktop_time", "clock",
    "desktop_layout", "desktop_utf8", "desktop_codec",
)


def embed_sources(src: Path, out: Path) -> None:
    files = [
        *(src / "runtime/core").glob("*.xu"),
        *(src / "internal/uiabi").glob("*.xu"),
        *(src / "errors").glob("*.xu"),
        src / "runtime/str_algo.xu",
        src / "runtime/map_algo.xu",
    ]
    lines = ["@main", "#xu/parser"]
    lines.append("fn add_core(p $&parser.Parser) {")
    for path in sorted(files):
        if path.name.startswith(("test.", "test_")):
            continue
        name = path.relative_to(src).as_posix()
        literal = json.dumps(path.read_text(encoding="utf-8"), ensure_ascii=False).replace("$", "\\$")
        lines.append(f'    add_source(p, {literal}, "{name}")')
    lines.append("}")
    lines.append("fn add_browser_ui(p $&parser.Parser, full bool) {")
    for name in UI_SOURCES[:3]:
        lines.append(f'    add_source(p, playground_std_{name}(), "{name}.xu")')
    lines.append("    if !full { << }")
    for name in UI_SOURCES[3:]:
        lines.append(f'    add_source(p, playground_std_{name}(), "{name}.xu")')
    lines.append("}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def finalize_module(module: bytes, version: str, sources: list[Path]) -> bytes:
    if not module.startswith(WASM_HEADER):
        raise ValueError("Invalid WebAssembly output")
    wasm = runpy.run_path(str(ROOT / "scripts/link-playground-float.py"))
    uleb, read_u, read_name, sections = (wasm[name] for name in ("uleb", "read_u", "read_name", "sections"))
    parts = list(sections(module))
    exports = {}
    for tag, payload in parts:
        if tag != 0:
            continue
        name, pos = read_name(payload, 0)
        if name != "name":
            continue
        while pos < len(payload):
            sub = payload[pos]
            size, start = read_u(payload, pos + 1)
            if sub == 1:
                count, cursor = read_u(payload, start)
                for _ in range(count):
                    index, cursor = read_u(payload, cursor)
                    label, cursor = read_name(payload, cursor)
                    if label.startswith("_xu_main_") and label[9:] in PLAYGROUND_EXPORTS:
                        exports[label[9:]] = index
            pos = start + size
    if exports.keys() != set(PLAYGROUND_EXPORTS):
        raise ValueError("Missing typed playground entry points")
    output = bytearray(WASM_HEADER)
    limited = False
    for tag, payload in parts:
        if tag == 5:
            count, pos = read_u(payload, 0)
            flags, pos = read_u(payload, pos)
            minimum, pos = read_u(payload, pos)
            if count != 1 or flags != 0 or pos != len(payload) or minimum > MAX_MEMORY_PAGES:
                raise ValueError("Unexpected Xu WebAssembly memory declaration")
            payload = b"\x01\x01" + uleb(minimum) + uleb(MAX_MEMORY_PAGES)
            limited = True
        if tag == 7:
            count, pos = read_u(payload, 0)
            payload = uleb(count + len(exports)) + payload[pos:]
            for name in PLAYGROUND_EXPORTS:
                encoded = name.encode("utf-8")
                payload += uleb(len(encoded)) + encoded + b"\x00" + uleb(exports[name])
        output.extend(bytes([tag]) + uleb(len(payload)) + payload)
    if not limited:
        raise ValueError("Missing Xu WebAssembly memory declaration")
    digest = hashlib.sha256()
    for source in sources:
        digest.update(hashlib.sha256(source.read_bytes()).digest())
    identity = json.dumps({"xu_version": version, "target": "wasm32-wasi",
                           "sources_sha256": digest.hexdigest()}).encode("utf-8")
    name = b"xu.source"
    payload = uleb(len(name)) + name + identity
    output.extend(b"\x00" + uleb(len(payload)) + payload)
    return bytes(output)


def build(sdk: Path, output: Path) -> None:
    sdk = sdk.resolve()
    output = output.resolve()
    src = sdk / "src"
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    sdk_version = (sdk / "VERSION").read_text(encoding="utf-8").strip()
    if sdk_version != version:
        raise ValueError(f"Expected published Xu {version}, got {sdk_version}")
    compiler = sdk / "bin" / ("xu.exe" if os.name == "nt" else "xu")
    banner = subprocess.check_output([str(compiler), "--version"], encoding="utf-8")
    identity = re.search(r"Xu Compiler Toolchain v(\S+)", banner)
    if not identity or identity[1] != version:
        raise ValueError(f"Compiler version must match the SDK version {version}")

    env = os.environ.copy()
    env.update(XU_ROOT=str(sdk), XU_STDLIB_ROOT=str(src), XUPATH="")
    for key in ("XUOS", "XUARCH", "XU_ALLOW_DEV", "XU_BOOT_EXTRA", "XU_SEED"):
        env.pop(key, None)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="xu-playground-typed-") as tmp:
        tmp = Path(tmp)
        embedded = tmp / "embedded_core.xu"
        embed_sources(src, embedded)
        stdlib = tmp / "embedded_ui.xu"
        generate = runpy.run_path(str(ROOT / "scripts/build-xu-playground.py"))["embedded_stdlib"]
        stdlib.write_text(generate(ROOT, sdk, merge="add_source", include_maps=False), encoding="utf-8")
        env["XU_CACHE"] = str(tmp / "cache")
        sources = [RUNTIME / "main.xu", RUNTIME / "machine.xu", RUNTIME / "floats.xu", embedded, stdlib]
        compiled = tmp / "xu-play.wasm"
        subprocess.run([str(compiler), "build", *map(str, sources), "--target", "wasm32-wasi",
                        "-o", str(compiled)], cwd=sdk, env=env, check=True)
        output.write_bytes(finalize_module(compiled.read_bytes(), version, sources))
    print(f"Xu {version} typed playground built: {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=ROOT / "build/playground-typed/xu-play.wasm")
    args = parser.parse_args()
    build(args.sdk, args.out)


if __name__ == "__main__":
    main()
