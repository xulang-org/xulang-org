# Repository-local development rules

All agents must read ../xu/docs/DEVELOPMENT.md before editing. This is a local
companion checkout; set XU_ROOT if the compiler checkout is elsewhere.
Do not commit or push without the user's instruction. Stage explicit paths only.
Keep reports, notes, logs, caches, generated binaries and local docs untracked.
Module version: and xu: are independent. Bump changed modules once per batch;
align xu: with the selected Xu release. Compiler VERSION is owned by xu.

The official deployment is a static GitHub Pages site. Use `make build` and
`make check`; these must work without Xu, Node.js, or companion checkouts.
`make run` previews the static output. The old Xu HTTP service is optional and
is available through `make run-http`. Keep dist/ and generated WASM untracked.
