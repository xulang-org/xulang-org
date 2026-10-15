<p align="center">
  <a href="https://xulang.org"><img src="www/xu_classic.svg" alt="Xu Logo" width="100" height="100"></a>
</p>

<h1 align="center">xulang.org Official Website & Interactive Portal</h1>

<p align="center">
  <b>Official Portal, WebAssembly Playground, and Cross-Language Benchmark Dashboard for the Xu Programming Language</b>
</p>

<p align="center">
  <b>English</b> | <a href="README.zh-CN.md">简体中文</a>
</p>

<p align="center">
  <a href="https://xulang.org"><img src="https://img.shields.io/badge/Site-xulang.org-rose" alt="Site"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License"></a>
  <a href="https://xulang.org/benchmarks"><img src="https://img.shields.io/badge/Benchmarks-47%20Tasks-amber" alt="Benchmarks"></a>
  <a href="https://github.com/xulang-org/xulang-org/actions/workflows/pages.yml"><img src="https://github.com/xulang-org/xulang-org/actions/workflows/pages.yml/badge.svg" alt="Pages CI"></a>
</p>

**xulang.org** is the source repository for the official website, interactive portal, and documentation hub of the [Xu Programming Language](https://github.com/xulang-org/xu), hosted on GitHub Pages at [xulang.org](https://xulang.org).

Key features hosted in this portal:
- 🌐 **Bilingual Official Docs & Tutorials**: Comprehensive guides, language specs, standard library, and API references with seamless language switching.
- ⚡ **Multi-Platform 47-Task Benchmark Dashboard**: Interactive cross-language performance and resource comparisons across ARM64, x86-64, and Windows ARM64.
- 🚀 **Client-Side WebAssembly Playground**: Xu compiled directly to a zero-server-load in-browser WASM sandbox for instant experimentation.
- 🎨 **Brand Identity Assets**: Official vector logos, typography, and badges.

Official account links:
- GitHub: [@xulang-org](https://github.com/xulang-org)
- X (Twitter): [@xulang_org](https://x.com/xulang_org)

## Directory Structure

| Directory / File | Description |
| --- | --- |
| `content/{zh,en}/` | Markdown/HTML sources for documentation, tutorials, blogs, and API references |
| `templates/` | Shell templates and page chrome |
| `www/` | CSS styles, JavaScript, vector webfonts, icons, and static assets |
| `playground/runtime/` | In-browser WebAssembly runtime sandbox written entirely in Xu |
| `scripts/` | Static site builder, WebAssembly compilation, API extraction, and release validator |
| `tests/` | Regression test suites for static builds, online playground, and channel concurrency |
| `brand/` | Official Xu logo assets, supergraphics, and brand design guidelines |

Build artifacts are generated into the untracked `dist/` and `build/` directories.

## Local Build & Preview

Requires Python 3.10 or newer (uses standard library only, zero external pip packages):

```sh
make build                      # Build into dist/, verify internal links and assets
make run                        # Start local live preview server at http://127.0.0.1:8080
make run PORT=18080             # Preview on a custom port
make check                      # Run full static site and playground test suites
make build BASE_PATH=/xulang-org # Build for a project subpath
make clean                      # Clean dist/ and build/playground/
```

Static compilation requires no compiler or external dependencies. Content fragments in `content/` declare titles via `<!--title: ...-->` and render into clean directory routes (e.g. `docs/start/index.html`).

## WebAssembly Playground

The interactive playground compiler is compiled from Xu sources into WebAssembly:

```sh
make wasm                           # Compile xu-play.wasm locally
make check-playground                # Test real WASM execution and examples in Node.js
make check-chan                      # Verify channel concurrency examples
make build                          # Bundle runtime into dist/
```

The playground runs client-side in the browser with zero backend dependencies, supporting coroutines, channels, ownership checks, and pattern matching.

## GitHub Pages Deployment

Automated deployment is configured in `.github/workflows/pages.yml`:
- Pushing to `main` automatically runs checks, validates SDK release alignment, compiles the WebAssembly playground, generates static pages, and deploys to GitHub Pages;
- The workflow strictly aligns with published releases of `xulang-org/xu` and verifies SHA-256 binary digests before publication.

## License

This repository is open-sourced under the [MIT License](LICENSE).
