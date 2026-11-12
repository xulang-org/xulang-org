# Playground typed MIR runtime

Build with the installed official SDK that matches the site's `VERSION`, then run the catalog and sandbox tests.

```sh
python3 scripts/build-typed-playground.py --sdk /path/to/xu-sdk
node --test tests/test_typed_playground.mjs
```

The WASM module parses and checks source with the SDK and interprets typed MIR. It uses the Linux ARM64 runtime ABI for interpreted programs so the Xu channel scheduler can switch virtual call stacks. The host exposes two read-only virtual files for source and replayed UI events and bounded streams for console output and Canvas commands.

The runtime retains one checked program and rebuilds interpreted state for each input history. It discards the checked program after a trap or 32 MiB of execution-side memory growth. The production worker still uses the previous runtime pending incremental input checkpoint parity.
