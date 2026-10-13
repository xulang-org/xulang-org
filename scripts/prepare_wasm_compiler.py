#!/usr/bin/env python3
"""Build an isolated Xu driver with the site's experimental WASM backend.

The product checkout and its installed compiler are never modified. Both the
driver and backend are Xu sources, compiled by the hosted product compiler.
"""
import argparse
import shutil
from pathlib import Path


def prepare(root: Path, xu: Path) -> Path:
    out = root / "build/wasm-compiler-source"
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.xu"):
        old.unlink()
    source = xu / "src/cmd/compile"
    for path in source.glob("*.xu"):
        shutil.copyfile(path, out / path.name)
    (out / "xu.xun").write_text("module: xu/site/wasm-compiler\nversion: !ver 0.1.0\nxu: !ver " + (xu / "VERSION").read_text().strip() + "\n")
    target = out / "asm_arm64.xu"
    text = target.read_text()
    anchor = 'fn parse_target(s string) int {\n'
    if text.count(anchor) != 1:
        raise RuntimeError("Xu target parser changed; review WASM integration")
    target.write_text(text.replace(anchor, anchor + '    if s == "wasm32" { << 41 }\n'))
    driver = out / "driver_build.xu"
    text = driver.read_text()
    anchor = '    mut a := Assembler{\n'
    if text.count(anchor) != 1:
        raise RuntimeError("Xu build driver changed; review WASM integration")
    driver.write_text(text.replace(anchor, '    if target_code == 41 { << wasm_emit(&m, out_path) }\n' + anchor))
    for path in (root / "playground/compiler").glob("*.xu"):
        shutil.copyfile(path, out / path.name)
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--xu-root", type=Path, required=True)
    args = p.parse_args()
    print(prepare(Path(__file__).resolve().parents[1], args.xu_root.resolve()))
