#!/usr/bin/env python3
"""Install a released SDK with the website's Unix script and check its tools."""
from __future__ import annotations

import argparse
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import tempfile
from threading import Thread


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def run(args: list[str], cwd: Path, env: dict[str, str], script: str | None = None) -> str:
    result = subprocess.run(args, cwd=cwd, env=env, input=script,
                            capture_output=True, text=True, timeout=180)
    if result.returncode:
        raise RuntimeError(f"{args}: exit {result.returncode}\n{result.stdout}\n{result.stderr}")
    return result.stdout


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk-root", type=Path, required=True)
    parser.add_argument("--installer", type=Path, default=ROOT / "www/install.sh")
    parser.add_argument("--archive", type=Path, help="SDK archive (default: beside the extracted SDK)")
    args = parser.parse_args()
    sdk = args.sdk_root.resolve()
    manifest = json.loads((sdk / "bundle.json").read_text())
    name = f"xu-v{manifest['version']}-{manifest['target']}.tar.gz"
    archive = args.archive.resolve() if args.archive else sdk.parent / name
    assert archive.is_file(), archive
    downloads: list[str] = []

    class Mirror(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path != f"/v{manifest['version']}/{name}":
                self.send_error(404)
                return
            downloads.append(self.path)
            self.send_response(200)
            self.send_header("Content-Length", str(archive.stat().st_size))
            self.end_headers()
            with archive.open("rb") as source:
                while chunk := source.read(65536):
                    self.wfile.write(chunk)

        def log_message(self, *args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Mirror)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    script = args.installer.read_text()
    try:
        with tempfile.TemporaryDirectory(prefix="xu-website-installer-") as directory:
            work = Path(directory)
            prefix = work / "installed SDK with spaces"
            env = dict(os.environ)
            for key in ("XU_ROOT", "XU_STDLIB_ROOT", "XUPATH", "XU_PACKAGES_ROOT",
                        "XU_EXAMPLES_ROOT", "XU_VSCODE_ROOT", "XU_VERSION", "XUOS", "XUARCH",
                        "XU_INSTALL_DIR"):
                env.pop(key, None)
            env.update(HOME=str(work), TMPDIR=str(work), XU_SKIP_EDITOR_INSTALL="1",
                       XU_DOWNLOAD_URL=f"http://127.0.0.1:{server.server_port}")
            # Match curl | bash, including a caller located inside an existing
            # SDK. Do not pass --online: legacy commands must also download.
            command = ["bash", "-s", "--", "--version", manifest["version"],
                       "--no-modify-path", "--yes"]
            run(command + ["--prefix", str(prefix)], sdk, env, script)
            assert len(downloads) == 1, "streamed installer reused the caller's SDK"
            # Repair the same SDK through PATH selection, including read-only
            # managed files; the website command must not create a second SDK.
            if manifest.get("files"):
                (prefix / "src/website-stale.xu").write_text("stale")
                (prefix / "src/os/mod.xu").write_text("damaged")
                (prefix / "src").chmod(0o555)
                selected = env | {"PATH": str(prefix / "bin") + os.pathsep + env.get("PATH", "")}
                selected.pop("XU_INSTALL_DIR", None)
                run(command, prefix, selected, script)
                assert len(downloads) == 2, "reinstall did not download a fresh SDK"
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
                  f"streamed download/reinstall, PATH repair, {len(manifest['binaries'])} tool hashes, "
                  "VSIX, examples and updater")
    finally:
        server.shutdown()
        server.server_close()
        worker.join()


if __name__ == "__main__":
    main()
