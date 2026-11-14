# Playground typed MIR runtime

Build with the installed official SDK that matches the site's `VERSION`, then run the catalog and sandbox tests.

```sh
npm ci --ignore-scripts
make wasm XU_ROOT=/path/to/xu-sdk
make check-playground
```

The WASM module parses and checks source with the SDK and interprets typed MIR. It uses the Linux ARM64 runtime ABI for interpreted programs so the Xu channel scheduler can switch virtual call stacks. The host exposes two read-only virtual files for source and replayed UI events and bounded streams for console output and Canvas commands.

The worker retains one checked program. Eligible programs pause before an exhausted input read and use a copy of the checkpoint to finish painting. Appended input resumes the checkpoint and processes the suffix. Editing or shortening the history, using tasks or channels, or exceeding the 8 MiB checkpoint budget triggers complete replay.
