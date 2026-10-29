## Additional syntax examples

Each block is a complete independent program from the site's playground examples or ownership tutorial. Save one at a time as `main.xu`.

### Bindings and mutability

{{example:bindings}}

### Structs and methods

{{example:structs}}

### Borrowing

`&T` denotes a shared borrow; `$&T` denotes an exclusive mutable borrow. Follow compiler diagnostics for inferred ownership and borrow lifetimes.

{{example:ownership}}

### Loops and control flow

`<-` breaks a loop and `->` continues it. `<<` returns from a function; `<<<` exits the process.

{{example:loop_control}}

## Project manifest and dependency workflow

Place the project beside the extracted SDK directory named `xu-v{{xu_version}}`, or adjust the local path below to the installed SDK's packages directory:

```xun
module: myapp
version: !ver 0.1.0
xu: !ver {{xu_version}}
require:
  "github.com/xulang-org/packages": file:../xu-v{{xu_version}}/packages
```

From the project root, run:

```sh
xu install
xu check main.xu --offline
xu build main.xu --frozen -o app
```

Commit the application manifest and lockfile for reproducibility. For fetching the SDK's exact source commit instead of using a local bundle, follow https://xulang.org/docs/packages/. Native bridge artifacts may require separate preparation; installing Xu source dependencies does not build those artifacts.

## Tests

Save this as `test.example.xu`:

```xu
@main

fn test_add() {
    assert(1 + 1 == 2)
}
```

Run `xu test test.example.xu -v`. Benchmark functions follow the same filename and signature restrictions, use the `bench_` prefix, and are selected with `-bench REGEXP`.

## Native container metadata

The product `xu native pack` writes top-level `abi`, `format`, `module`, and `slices` metadata. Export signatures are stored in each slice's XUOBJ metadata. The source-tree Python helper `scripts/xunative.py` also retains fields copied from its input manifest, including `exports`; consumers must not assume every product-generated container has top-level `exports`.

Packing multiple target slices and linking a native executable are separate capabilities. The one-step macOS link path needs the macOS C toolchain. For other targets, emit XUOBJ with `--emit-obj`, convert to a platform object, and use the target's external linker. See https://xulang.org/docs/native/ for platform scope.

## Standard library and integrations

The API catalog at https://xulang.org/api/ is generated from the selected released SDK. It covers formatting, errors, collections, text and encodings, files and processes, networking, cryptography, SQL, and the `ui`, `ui/draw`, `ui/layout`, `ui/widgets`, and `ui/webview` packages. Consult each package's documented target limits.

Official service integrations live in the independent https://github.com/xulang-org/packages repository. The website documents the SDK's pinned package snapshot, which can differ from that repository's current branch. Read the relevant API and example before assuming a protocol feature or native target is supported.
