#!/usr/bin/env python3
"""Install a released SDK with the website's Unix script and check its tools."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def run(args: list[str], cwd: Path, env: dict[str, str]) -> str:
    result = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, timeout=180)
    if result.returncode:
        raise RuntimeError(f"{args}: exit {result.returncode}\n{result.stdout}\n{result.stderr}")
    return result.stdout


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk-root", type=Path, required=True)
    parser.add_argument("--installer", type=Path, default=ROOT / "www/install.sh")
    args = parser.parse_args()
    sdk = args.sdk_root.resolve()
    manifest = json.loads((sdk / "bundle.json").read_text())
    # Placing the website script beside the released SDK selects its real
    # offline payload. No second download or replacement of the bundled script.
    descriptor, name = tempfile.mkstemp(prefix=".website-installer-", suffix=".sh", dir=sdk)
    installer = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as target:
            target.write(args.installer.read_bytes())
        with tempfile.TemporaryDirectory(prefix="xu-website-installer-") as directory:
            work = Path(directory)
            prefix = work / "installed SDK with spaces"
            env = dict(os.environ)
            for key in ("XU_ROOT", "XU_STDLIB_ROOT", "XUPATH", "XU_PACKAGES_ROOT",
                        "XU_EXAMPLES_ROOT", "XU_VSCODE_ROOT", "XU_VERSION", "XUOS", "XUARCH"):
                env.pop(key, None)
            env.update(HOME=str(work), TMPDIR=str(work), XU_SKIP_EDITOR_INSTALL="1")
            run(["bash", str(installer), "--prefix", str(prefix), "--no-modify-path", "--yes"], work, env)
            # Repair the same SDK through PATH selection, including read-only
            # managed files; the website command must not create a second SDK.
            if manifest.get("files"):
                (prefix / "src/website-stale.xu").write_text("stale")
                (prefix / "src/os/mod.xu").write_text("damaged")
                (prefix / "src").chmod(0o555)
                selected = env | {"PATH": str(prefix / "bin") + os.pathsep + env.get("PATH", "")}
                selected.pop("XU_INSTALL_DIR", None)
                run(["bash", str(installer), "--no-modify-path", "--yes"], work, selected)
                assert not (prefix / "src/website-stale.xu").exists()
                for name, expected in manifest["files"].items():
                    assert sha256(prefix / name) == expected, name
            installed = json.loads((prefix / "bundle.json").read_text())
            assert installed["version"] == manifest["version"]
            for binary, expected in manifest["binaries"].items():
                assert sha256(prefix / "bin" / binary) == expected, binary
            extension = json.loads((sdk / "editors/vscode/package.json").read_text())
            vsix = f"editors/vscode/{extension['name']}-{extension['version']}.vsix"
            assert sha256(prefix / vsix) == sha256(sdk / vsix)
            example = "examples/16_ui_webview/shared/mod.xu"
            assert sha256(prefix / example) == sha256(sdk / example)
            output = run([str(prefix / "bin/xu"), "update", "--check", "--version", manifest["version"]], work, env)
            assert "already up to date" in output, output
            print(f"website-installer: PASS {manifest['target']} {manifest['version']}; "
                  f"{len(manifest['binaries'])} tool hashes, VSIX, examples and updater")
    finally:
        installer.unlink()


if __name__ == "__main__":
    main()
