# Browser UI playground

Xu's scanner, parser, borrow checker, MIR interpreter, and cooperative scheduler
execute inside a disposable WASM instance. User source is never translated into
JavaScript. Canvas is the pixel host for both drawing and real widgets.

Open `/playground/?example=ui-gallery` (or `/zh/playground/?example=ui-gallery`)
for a three-page control gallery. `ui-widgets`, `ui-draw`, and `ui-counter`
remain available. Explicit example links load and run; ordinary selection waits
for Run Code. The reviewable source is `examples/ui-gallery.xu`; its JSON entry
is checked against that file.

The pages use shared desktop implementations:

- Basics: Button, Checkbox, Switch, Slider, and two Radio controls. The Xu
  caller applies Radio exclusivity; RadioGroup also has its own focused experience.
- Data: ListBox with selection and scrolling, plus a clipped/transformed Scroll
  container. Wheel deltas, keyboard navigation, and bounds run in the widgets.
- Display: StyledLabel text, Card, Badge, Progress with normal/invalid/disabled styled states linked to the slider, and
  `widgets.input()` Editor in display-only/read-only mode. The Editor owns no
  native text session; no editing, selection interaction, clipboard or IME is
  exposed. Native session requests return an explicit unsupported error.

Tabs and FocusGroup manage page selection and focus in Xu. Hidden controls lose
focus and armed state; their values survive page changes. Tab/Shift+Tab move
focus, arrows select a focused tab, and click switches pages. Scroll has basic
clipping/translation and keyboard/wheel input; its styled scrollbar is excluded.
ListBox keeps the desktop basic paint API, rather than its richer styled rows.

## Real desktop control logic

`stdlib/desktop_widgets.xu` contains complete, unchanged declarations selected
from `xu/src/ui/widgets`, including constructors, state/input methods, basic
paint, focus rings, rounded paths, theme primitives, StyledLabel text paint,
and the read-only Editor paint path. Divider and Segmented Tabs basic APIs are
also mirrored. This is a larger gallery subset, not the complete desktop suite.

`stdlib/desktop_*.xu` supplies necessary desktop layout, math, UTF-8 validation,
input, text/color/path types, style resolution, and motion initialization.
The focused component experiences additionally run Select, Stepper, RadioGroup,
Pagination, Breadcrumbs, RangeSlider, SplitView, ButtonGroup, MultiSelect,
ColorPicker, Table, Chart, and dropdown/context/split Menu modes. Their geometry,
state, input and paint methods are unchanged desktop Xu declarations. Canvas
forwards left/right/middle pointer buttons and supplies drawing resources.

Extension declarations are partitioned by their dependency owners in
`desktop-sources.json`. The runtime scans user identifier tokens, loads only the
requested families and shared declarations, and parses each package once.
Existing basic programs keep their original subset. Native event pumps, Screen,
WebView, editable input and the remaining component families are not exposed by
the WASM subset. Their separate playground interaction previews are clearly
marked as not executing Xu; they are not substitutes inside the WASM runtime.

The checked-in `stdlib/desktop-sources.json` records the upstream commit and a
SHA-256 for every declaration. To resync against a clean or dirty Xu checkout
without writing to that checkout:

```sh
python3 scripts/sync-playground-widgets.py --xu-root /path/to/xu
python3 scripts/sync-playground-widgets.py --xu-root /path/to/xu --check
```

The declaration hashes capture the actual input even when a source checkout is
dirty. Source selection lives in the sync script; do not hand-edit generated
files. `tests/test_playground_widget_sources.py` checks the vendored bodies
against the manifest. `tests/fixtures/playground_widgets.xu` runs unchanged in
the browser VM and with the native product compiler to check input semantics.

## Thin browser host

- `stdlib/draw.xu`: the existing integer `#ui/draw` command API.
- `stdlib/frame.xu`: browser implementations of `draw.Context`, `Frame`,
  `TextLayout`, and geometric `Path` recording. Text layouts use VM-owned scalar
  handles matching the copy semantics of desktop resources; string ownership
  is kept out of the resource struct. Widgets call the same basic
  desktop API signatures. These are host/resource adapters, not controls.
- `stdlib/text_input.xu`: explicit errors for unavailable native edit sessions.
- `stdlib/browser.xu`: `playground.canvas_identity()`, `next_click()` for the
  original counter, and `next_input() ui.InputEvent` for widgets. A zero kind
  means replay exhaustion. This driver replaces the native event pump.
- `runtime/ui.xu`: bounded command transport, scalar formatting, and input
  intrinsics. Strings follow Xu's indirect descriptor ABI.
- `www/xu-play-canvas.js`: validates complete display lists before drawing the
  final committed frame. It supports fractional geometry, cubic paths, and
  recorded text. Commands never contain HTML, executable JS, or widget IDs.
- `www/xu-play.js`: scales pointer positions, captures pointer drags, and maps
  native browser key down/up events to stable Xu key codes. Pending input is
  queued; motion is coalesced. Wheel events become bounded logical pixel deltas
  and enter real `ui.InputEvent.dx/dy`, including fractional values. Blur/capture cancellation reaches widgets too.

Button geometry is measured by the desktop `widgets.button_size()` using the
host TextLayout metrics. The browser text adapter currently implements a
single-line monospace grid (0.6 × font size per Unicode code point, height
1.25 × size). Canvas fits painted text to that same width. This is deterministic
basic text layout, not native shaping, wrapping, bidi, grapheme-cell measurement,
or IME. TextOptions fields other than size are outside this subset.
`layout_masked_text()` paints one mask character per code point on this grid
while caret and selection queries retain the original UTF-8 byte positions.
The original text is never included in the masked layout's Canvas paint command.

## Floating-point VM support

Widget geometry uses real IEEE binary64 values. The development wasm32 backend
supports typed f64 arithmetic; the selected 0.10.11 SDK predates that support.
The MIR interpreter represents VM values as
integer bit patterns. Its `vm_fp_*` functions are still trap stubs: numeric
`f64(int)` / `int(f64)` casts convert values and cannot reinterpret those bits.
The build therefore retains thirteen fixed scalar helpers linked by
`scripts/link-playground-float.py`. Each helper keeps the compiler's existing
`(args i32, result i32) -> void` frame ABI and performs only a native WASM
arithmetic, comparison, sign, or conversion instruction. No imports or JS
callbacks are added. Unlinked Xu helper stubs trap rather than silently compute
a wrong result. A `xu.playground.float` custom section identifies the link step.
This bridge needs no additional compiler changes.

The Xu interpreter handles typed float operations, including comparisons with
boolean destinations, casts, and field/index updates. Float-to-int conversion
uses explicit WASM saturation (NaN -> 0, out-of-range -> signed i64 bound).
Canvas decimal transport and float stdout currently use six fractional digits
and magnitudes at most 1e9; state calculations retain binary64 precision.
This does not claim general native floating-point formatting compatibility.

## Interaction and resource limits

Every input replays the program and its bounded history in a fresh WASM
instance. State, measurement, hit testing, focus, activation, and painting all
execute in Xu. Only the final committed frame is displayed. The gallery paints
once after consuming history, which bounds draw output independently of event
count. Run Code, source edits, and example changes reset the session.

- Fixed 640 × 360 logical canvas, responsive display and pointer coordinates.
- At most 64 records: a widget pointer/key down and up each use one record;
  legacy counter clicks use one record each. Drag motion also uses records.
- Tab / Shift+Tab cycle controls in the gallery. Enter/Space activate the
  focused Button/Checkbox/Switch. Arrows, Home/End, and PageUp/PageDown adjust
  Slider. Esc cancels and leaves the canvas. Click requests focus through the
  widgets API. Key events and an active drag’s motion/release are queued during replay; new pointer presses while busy are ignored. Stopping/editing discards pending input.
- 10-second worker timeout for ordinary programs; 30 seconds for programs importing `#ui/widgets`. The VM step limit and fixed 256 MiB initial/maximum memory still bound execution.

Worker initialization runs a silent minimal Xu program before reporting ready.
This warms the parser, checker and interpreter under the separate 30-second
loading deadline, keeping cold WASM tiering out of the first user execution's
execution budget. Initialization output is never shown as user output.
- Commands: 256 KiB / 4096 lines; transform stack: 32; text size: 1–256.
- No continuous animation, hover tracking while idle, native services/windows,
  WebView, full styled widgets, editable text input, or persistent external effects.
- The Canvas surface is keyboard operable, with state mirrored in stdout, but
  individual widgets do not yet expose a DOM accessibility tree.

## Build and preview

Use a complete SDK whose compiler banner and source VERSION match the site's
selected final VERSION. By default, the build rejects development/mismatched
SDKs; vendored widget source provenance is recorded independently of the
compiler version. No release version is relabeled.

For local development, set `XU_ALLOW_DEV=1` to accept a semver prerelease SDK
and a site VERSION mismatch. The compiler banner and `XU_RELEASE_VERSION` (if
set) must still match the SDK VERSION. This prints a dev-build warning and
marks `build/playground/build.json` with `dev_build: true`; these builds are
not for release.

```sh
XU_ROOT=/path/to/matching-sdk ./scripts/build-playground.sh
make check-playground
make check
python3 scripts/build-static.py --require-playground
python3 -m http.server 18110 --bind 127.0.0.1 --directory dist
```

The build invokes the scalar link step automatically, including adjustment of
the SDK memory section to a fixed 256 MiB limit. The disposable arena starts at
16 MiB and retains parser/checker/MIR/UI allocations until evaluation ends.
Styled tables and charts exceed the original 128 MiB budget even after loading
only their dependencies. The allocator, linker, build metadata and memory test
share the 256 MiB contract; programs cannot grow beyond it. The source size,
VM step count, input history and worker deadlines remain bounded.
Native SDK methods can emit conservative division warnings; warnings remain
visible, and a later WASM trap is appended rather than hidden by those warnings.
The VM supports the scalar maps needed by these controls (int/string keys,
int/bool values, at most 4096 entries); other map value/operation forms report an
explicit unsupported error. Input timestamps use a deterministic replay clock.
The build records the compiler
version, WASM digest, and widget-source manifest digest in
`build/playground/build.json`. Generated WASM and site output remain ignored.
For deployment below a prefix, pass `--base-path /xulang-org` and an optional
`--output` directory to the static builder. Canvas, Worker, examples, and WASM
participate in the same content-derived cache key and path rewriting.

The gallery contract is `tests/fixtures/playground_gallery.xu`; it runs the same
source natively and inside WASM. Browser tests also validate display-only Editor
painting and explicit rejection of native text-session requests.

Native contract check (uses the development product compiler without changing
its source tree):

```sh
XU_ROOT=/path/to/xu XU_STDLIB_ROOT=/path/to/xu/src \
  /path/to/xu/bin/xu build tests/fixtures/playground_widgets.xu \
  -o /tmp/xu-widget-contract
XU_UI_SIM=1 /tmp/xu-widget-contract
```

## Linear-memory ABI

Controls are little-endian i64. Existing source/stdout/stderr buffers and the
16 MiB arena start are unchanged. Input and draw buffers cannot overlap them.

| Address | Meaning |
| --- | --- |
| 1056 | Command byte length, at most 262144 |
| 1064 | Input record count, at most 64 |
| 1072 | Next input index |
| 1080 | An input driver was called (interactive) |
| 1088 | `next_input` was called (typed input mode) |
| 720000–982143 | UTF-8 newline-delimited drawing commands |
| 1000000–1005119 | 64 input records of 80 bytes each |

Each input record has eight i64 slots: kind, x, y, key, modifiers, repeat, button,
buttons, followed by two f64 slots for dx and dy. Pointer coordinates become f64 slots in `ui.InputEvent`; the browser
canvas identity is `(window_id:1, canvas_id:1, generation:1)`. Legacy
`next_click()` consumes x/y from the same record and returns `(x,y,ok)`.
Failures return no UI frame. ABI or intrinsic changes must be updated in both
the Xu interpreter and JS bridge and exercised with the actual built WASM.
