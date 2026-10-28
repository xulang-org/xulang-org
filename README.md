<p align="center">
  <a href="https://xulang.org">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/xulang-org/xulang-org/main/brand/xu-profile-dark.svg">
      <img src="https://raw.githubusercontent.com/xulang-org/xulang-org/main/brand/xu-profile-light.svg" alt="XU — Native code. Clear intent." width="100%">
    </picture>
  </a>
</p>

<h1 align="center">The XU programming language</h1>

<p align="center">
  A systems language with native compilation, ownership, and built-in concurrency.<br>
  <strong>Deterministic memory management. No garbage collector.</strong>
</p>

<p align="center">
  <a href="https://xulang.org/playground"><strong>Try in your browser</strong></a> &nbsp; · &nbsp;
  <a href="https://xulang.org/docs/start">Read the guide</a> &nbsp; · &nbsp;
  <a href="https://xulang.org/download">Download XU</a> &nbsp; · &nbsp;
  <a href="https://github.com/xulang-org/xu">Compiler source</a>
</p>

<p align="center">
  <strong>English</strong> / <a href="README.zh-CN.md">简体中文</a>
</p>

## A small language with a clear flow

XU brings compile-time ownership and borrowing together with lightweight coroutines and typed channels. It compiles ahead of time to native code or WebAssembly, with resource lifetimes managed deterministically.

| Language choice | What it gives you |
| :--- | :--- |
| **Ownership, without a GC** | Compile-time move and borrow checks, inferred lifetimes, and deterministic resource cleanup. |
| **Concurrency in the language** | Start a coroutine with `xu`; exchange values through typed `chan` channels. |
| **Visible control flow** | `<<` returns a value, `>>` raises an error, and `or (err) { … }` handles it at the call site. |
| **An integrated toolchain** | Build, run, check, test, format, generate docs, and use language services through `xu`. |

## Read a little XU

Two workers, one channel, and an explicit error path:

```xu
@main
#errors

fn score(name string) int {
    if name.len == 0 { >> errors.new("empty name") }
    << name.len * 10
}

fn worker(name string, results chan int) {
    value := score(name) or (err) {
        results <- 0
        <<
    }
    results <- value
}

fn main() int {
    results := chan int{cap: 2}
    xu worker("hello", results)
    xu worker("world", results)
    println(<-results + <-results)
    << 0
}
```

Save as `main.xu`, then run `xu run main.xu`. It prints `100`.

`#errors` imports a package. `xu worker(...)` starts a coroutine. The two receives collect the results; if `score` fails, `or (err) { … }` sends a fallback value of `0` and returns from that worker.

## Start here

Explore the [browser playground](https://xulang.org/playground) without installing anything, or [download the SDK](https://xulang.org/download) for local development. After installation:

```sh
xu --version
xu run main.xu
xu build main.xu -o hello
```

Continue with the [getting started guide](https://xulang.org/docs/start), [language reference](https://xulang.org/docs/lang/syntax), or [runnable examples](https://github.com/xulang-org/examples).

XU is actively evolving in the **0.x series**. See [Releases](https://github.com/xulang-org/xu/releases) for published SDKs and [status and limitations](https://xulang.org/docs/status) for platform and runtime coverage. The [benchmark dashboard](https://xulang.org/benchmarks) records measured workloads, compiler versions, and source provenance.

## Explore the ecosystem

| Project | Where to go |
| :--- | :--- |
| **Language & compiler** | [xu](https://github.com/xulang-org/xu) — self-hosted compiler, standard library, and CLI tools. |
| **Learn by running** | [examples](https://github.com/xulang-org/examples) — language basics, concurrency, networking, databases, and UI examples. |
| **Libraries & integrations** | [packages](https://github.com/xulang-org/packages) — database drivers, messaging, storage, and service integrations. |
| **Editor support** | [vscode-xu](https://github.com/xulang-org/vscode-xu) — syntax highlighting and XU language services for VS Code and Cursor. |
| **Performance** | [bench](https://github.com/xulang-org/bench) — cross-language workloads and reproducible benchmark sources. |
| **Website & documentation** | [xulang-org](https://github.com/xulang-org/xulang-org) — xulang.org, documentation, and the WebAssembly playground. |

## Build XU with us

Try an example, report a compiler issue, improve the docs, or contribute a library. Start with [compiler issues](https://github.com/xulang-org/xu/issues) or [website issues](https://github.com/xulang-org/xulang-org/issues).

Read the [contribution guide](CONTRIBUTING.md) and [shared repository rules](.github/REPOSITORY_RULES.md) before contributing. Maintainers can follow the [GitHub settings checklist](.github/GITHUB_SETTINGS.md).

[Website](https://xulang.org) · [GitHub](https://github.com/xulang-org) · [X / @xulang_org](https://x.com/xulang_org) · [MIT license](LICENSE)

---

<details>
<summary><strong>Working on xulang.org</strong> — website build, playground, and deployment</summary>

This profile repository also contains the source for the official website. The site selects the published **XU 0.10.2 SDK**; development builds remain separate.

### Local build

Requires **Python 3.10+**, using only the standard library. Static builds and checks run without XU, Node.js, or companion checkouts.

```sh
make build                       # Build dist/ and verify internal links and assets
make run                         # Preview at http://127.0.0.1:8080
make run PORT=18080               # Preview on a custom port
make check                       # Run the static site regression suite
make build BASE_PATH=/xulang-org  # Build for a project subpath
make clean                       # Remove dist/ and build/playground/
```

| Path | Purpose |
| :--- | :--- |
| `content/{en,zh}/` | Documentation, tutorials, blog posts, and API content. |
| `templates/` | Page templates, API guides, and example selections. |
| `www/` | Styles, scripts, fonts, icons, and static assets. |
| `playground/runtime/` | Browser WebAssembly runtime written in XU. |
| `scripts/` | Static builder, API generation, and release validation. |
| `tests/` | Static site, playground, and channel regression coverage. |
| `brand/` | Brand assets and visual identity guidelines. |

Generated output goes to the ignored `dist/` and `build/` directories. Content fragments declare titles with `<!--title: ...-->` and render into directory routes such as `docs/start/index.html`.

### API content and examples

Curated prose lives in `templates/api-guides/{en,zh}/`. API generation combines it with declarations from the selected SDK. Examples are imported from the official examples repository at an immutable commit; bundled snapshots in `www/api-examples/` preserve independent local and CI builds.

To refresh declarations and examples, select compatible sources in `templates/api-examples.json`, check them with the selected SDK, and supply the examples checkout and its full commit SHA:

```sh
make api XU_ROOT=/path/to/xu-v0.10.2 XU_PACKAGES_ROOT=/path/to/xu-v0.10.2/packages \
  XU_EXAMPLES_ROOT=../examples XU_EXAMPLES_REF=FULL_EXAMPLES_COMMIT_SHA
```

Selected files must match that commit. Without the two examples variables, `make api` reuses and verifies bundled snapshots. Native examples run locally with the SDK.

### WebAssembly playground

Use the matching SDK to compile the XU runtime to WebAssembly. Execution checks additionally require Node.js.

```sh
make wasm              # Compile build/playground/xu-play.wasm
make check-playground  # Check real WASM execution and examples in Node.js
make check-chan        # Check native channel examples with XU
make build             # Bundle the runtime into dist/
```

The playground runs client-side in the browser. Generated WASM stays in `build/playground/`; `www/` remains source-only.

### Benchmarks and deployment

To refresh benchmarks, download one complete six-platform Actions run, then run:

```sh
python3 scripts/import-benchmarks.py --artifacts DIR --commit FULL_SHA --run-id ID --date YYYY-MM-DD
python3 scripts/gen-benchmarks.py
```

Import verifies compiler identities, source closure, fixed point, workload completeness, and stdout. Unmeasured cells remain empty; C/Rust rows select the lowest O1/O2/O3 median.

`.github/workflows/pages.yml` checks release alignment, verifies published SDK SHA-256 digests, compiles the playground, builds the site, and deploys to GitHub Pages on pushes to `main`.

</details>

### UI API and examples

The [UI guide](content/en/docs/ui.html) and [Chinese guide](content/zh/docs/ui.html) document the official Xu 0.10.2 SDK. All five packages — `ui`, `ui/draw`, `ui/layout`, `ui/widgets` and `ui/webview` — appear in the released API navigation. Former UI preview URLs redirect to the corresponding released pages while preserving declaration anchors.

Handwritten release guides live in `templates/api-guides/{en,zh}/ui*`; semantic contracts and field descriptions live in `templates/api-contracts.json`. Run `make api` with the selected release SDK to regenerate declarations. The curated source catalog includes drawing, layout, editors, desktop services, windows, WebView requests, styles and the extended controls gallery. Each example links to its immutable complete project and a checksum-verified source download.

For a future unreleased API, the generator still supports an explicit development preview without changing the selected release:

```sh
python3 scripts/gen-api.py --src /path/to/development-sdk/src --preview --package ui
make build
make check
```

Preview guides and contracts use `templates/api-guides/{en,zh}/preview/ui*` and `templates/api-preview-contracts.json`. An explicitly generated preview carries its development SDK version and source SHA-256 and takes precedence over legacy redirects. Release builds continue to use the selected official SDK and bundled example snapshots.

The browser playground includes a [three-page control gallery](https://xulang.org/playground?example=ui-gallery):
shared desktop Xu logic covers basic controls, Radio, ListBox, Scroll, Tabs,
StyledLabel, Card, Badge, Progress and a display-only Editor in WASM. Canvas
renders their paint commands. Editable text and IME remain unavailable. The shapes and click-counter demos
remain available. See [the browser UI build guide](playground/README.md) for
source synchronization, supported APIs, keyboard controls, and replay limits.
