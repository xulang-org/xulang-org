#!/usr/bin/env python3
"""Build the browser playground with the site's released Xu SDK."""

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "playground" / "typed"
WASM_HEADER = b"\x00asm\x01\x00\x00\x00"
MAX_MEMORY_PAGES = 4096
PLAYGROUND_EXPORTS = (
    "playground_prepare", "playground_execute", "playground_drive",
    "playground_checkpoint", "playground_preview",
)
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


def finalize_module(module: bytes, version: str, sources: list[Path]) -> tuple[bytes, int]:
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
    minimum_pages = None
    for tag, payload in parts:
        if tag == 5:
            count, pos = read_u(payload, 0)
            flags, pos = read_u(payload, pos)
            minimum, pos = read_u(payload, pos)
            if count != 1 or flags != 0 or pos != len(payload) or minimum > MAX_MEMORY_PAGES:
                raise ValueError("Unexpected Xu WebAssembly memory declaration")
            payload = b"\x01\x01" + uleb(minimum) + uleb(MAX_MEMORY_PAGES)
            minimum_pages = minimum
        if tag == 7:
            count, pos = read_u(payload, 0)
            payload = uleb(count + len(exports)) + payload[pos:]
            for name in PLAYGROUND_EXPORTS:
                encoded = name.encode("utf-8")
                payload += uleb(len(encoded)) + encoded + b"\x00" + uleb(exports[name])
        output.extend(bytes([tag]) + uleb(len(payload)) + payload)
    if minimum_pages is None:
        raise ValueError("Missing Xu WebAssembly memory declaration")
    digest = hashlib.sha256()
    for source in sources:
        digest.update(hashlib.sha256(source.read_text(encoding="utf-8").encode("utf-8")).digest())
    identity = json.dumps({"xu_version": version, "target": "wasm32-wasi",
                           "sources_sha256": digest.hexdigest()}).encode("utf-8")
    name = b"xu.source"
    payload = uleb(len(name)) + name + identity
    output.extend(b"\x00" + uleb(len(payload)) + payload)
    return bytes(output), minimum_pages


def build(sdk: Path, output: Path, compiler: Path | None = None) -> None:
    sdk = sdk.resolve()
    output = output.resolve()
    src = sdk / "src"
    version = (sdk / "VERSION").read_text(encoding="utf-8").strip()
    allow_dev = os.environ.get("XU_ALLOW_DEV") == "1"
    version_pattern = r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    if allow_dev:
        expected = os.environ.get("XU_RELEASE_VERSION", version)
        prerelease = r"(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
        version_pattern += rf"(?:-{prerelease}(?:\.{prerelease})*)?"
    else:
        expected = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if version != expected or not re.fullmatch(version_pattern, version):
        raise ValueError(f"Expected Xu SDK {expected}, got {version}")
    compiler = compiler.resolve() if compiler else sdk / "bin" / ("xu.exe" if os.name == "nt" else "xu")
    banner = subprocess.check_output([str(compiler), "--version"], encoding="utf-8")
    identity = re.search(r"Xu Compiler Toolchain v(\S+)", banner)
    if not identity or identity[1] != version:
        raise ValueError(f"Compiler version must match the SDK version {version}")
    if allow_dev:
        print("WARNING: XU_ALLOW_DEV=1 creates a local development build.", file=sys.stderr)

    env = os.environ.copy()
    env.update(XU_ROOT=str(sdk), XU_STDLIB_ROOT=str(src), XUPATH="")
    for key in ("XUOS", "XUARCH", "XU_ALLOW_DEV", "XU_BOOT_EXTRA", "XU_SEED", "XU_ALLOW_ORACLE_SEED"):
        env.pop(key, None)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="xu-playground-typed-") as tmp:
        tmp = Path(tmp)
        embedded = tmp / "embedded_core.xu"
        embed_sources(src, embedded)
        stdlib = tmp / "embedded_ui.xu"
        tools = runpy.run_path(str(ROOT / "scripts/build-xu-playground.py"))
        stdlib.write_text(tools["embedded_stdlib"](ROOT, sdk, merge="add_source", include_maps=False),
                          encoding="utf-8")
        env["XU_CACHE"] = str(tmp / "cache")
        sources = [RUNTIME / "main.xu", RUNTIME / "machine.xu", RUNTIME / "floats.xu", embedded, stdlib]
        compiled = tmp / "xu-play.wasm"
        subprocess.run([str(compiler), "build", *map(str, sources), "--target", "wasm32-wasi",
                        "-o", str(compiled)], cwd=sdk, env=env, check=True)
        module, initial_pages = finalize_module(compiled.read_bytes(), version, sources)
        compiled.write_bytes(module)
        unoptimized_bytes = tools["optimize"](ROOT, compiled)
        if (sdk / "VERSION").read_text(encoding="utf-8").strip() != version:
            raise ValueError("Xu SDK version changed during the playground build")
        module = compiled.read_bytes()
        output.write_bytes(module)
        (output.parent / "build.json").write_text(json.dumps({
            "xu_version": version,
            "target": "wasm32-wasi",
            "initial_memory_bytes": initial_pages * 65536,
            "memory_limit_bytes": MAX_MEMORY_PAGES * 65536,
            "optimizer": {"name": "binaryen", "version": tools["OPTIMIZER_VERSION"],
                          "flags": tools["OPTIMIZER_FLAGS"]},
            "unoptimized_bytes": unoptimized_bytes,
            "wasm_bytes": len(module),
            "gzip_bytes": len(gzip.compress(module, compresslevel=9, mtime=0)),
            "wasm_sha256": hashlib.sha256(module).hexdigest(),
            "widget_sources_sha256": hashlib.sha256(
                (ROOT / "playground/stdlib/desktop-sources.json").read_bytes()
            ).hexdigest(),
            **({"dev_build": True} if allow_dev else {}),
        }, indent=2) + "\n", encoding="utf-8")
    print(f"Xu {version} playground built: {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk", type=Path, required=True)
    parser.add_argument("--compiler", type=Path)
    parser.add_argument("--out", type=Path, default=ROOT / "build/playground/xu-play.wasm")
    args = parser.parse_args()
    build(args.sdk, args.out, args.compiler)


if __name__ == "__main__":
    main()
