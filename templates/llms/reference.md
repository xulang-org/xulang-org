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

### Standard library package directory

- `#fmt`: Formatted I/O, string formatting, `println`, `sprint`
- `#strings`: UTF-8 string manipulation, splitting, trimming, and searching
- `#bytes`: Byte buffer operations, slice manipulations, and dynamic buffers
- `#strconv`: String conversion to int, float, bool, and numeric formatting
- `#unicode`: Unicode UTF-8 and UTF-16 character classifications and conversions
- `#regexp`: Regular expressions parsing and pattern matching
- `#net`: TCP, UDP, raw IP socket networking, `listen_on`, `dial`, `listen_packet`
- `#net/http`: High-concurrency multi-worker HTTP server and client, HTTP/2 HPACK decoding
- `#io`: Stream primitives, Reader/Writer interfaces, and filesystem abstractions
- `#os`: System calls, process spawning, signals, environment variables
- `#sync`: Mutex, WaitGroup, Once, and atomic primitives
- `#time`: Wall-clock time, monotonic duration, timers, tickers, and sleep
- `#runtime`: Compiler runtime statistics, allocator inspection, coroutine scheduling
- `#database/sql`: SQL driver interfaces and connection pooling
- `#crypto/sm4`, `#crypto/sm2`, `#crypto/sm3`, `#crypto/sm9`, `#crypto/zuc`: ShangMi national standard algorithms
- `#crypto/aes`, `#crypto/rsa`, `#crypto/sha256`, `#crypto/tls`: International cryptographic algorithms and TLS
- `#ui`, `#ui/widgets`, `#ui/draw`, `#ui/layout`, `#ui/webview`: Declarative retained-mode UI and GPU canvas

### Networking patterns (TCP / UDP)

```xu
@main
#net

fn run_tcp_server() {
    ln := net.listen_on("tcp", "127.0.0.1:8080") or (err) { << }
    c := ln.accept() or (err) { << }
    buf := c.read(4096) or (err) { << }
    c.write(&buf) or (err) { << }
}
```

Official service integrations live in the independent https://github.com/xulang-org/packages repository. The website documents the SDK's pinned package snapshot, which can differ from that repository's current branch. Read the relevant API and example before assuming a protocol feature or native target is supported.
