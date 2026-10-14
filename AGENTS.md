# Repository-local development rules

All agents must read ../xu/docs/DEVELOPMENT.md before editing. This is a local
companion checkout; set XU_ROOT if the compiler checkout is elsewhere.
Do not commit or push without the user's instruction. Stage explicit paths only.
Keep reports, notes, logs, caches, generated binaries and local docs untracked.
User decision (2026-10-13): website VERSION, root xu.xun version: and xu: must
match the final SDK selected from Xu main. Do not independently bump the site's
release number. The playground runtime module retains its own version:; align
its xu: with the selected SDK. Compiler VERSION is owned by xu.

The official deployment is a static GitHub Pages site. Use `make build` and
`make check`; these must work without Xu, Node.js, or companion checkouts.
`make run` previews the static output. Xu owns the compiler and WASM backend;
this repository owns the playground runtime and browser bridge. Keep www/
source-only; generated WASM belongs in build/playground/ and is copied to dist/
by the static builder. Local archives belong in the ignored .local/ directory.
