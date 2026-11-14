# Browser UI playground

Xu's scanner, parser, borrow checker, MIR interpreter, and cooperative scheduler
execute inside a worker-owned WASM instance. User source is never translated into
JavaScript. Canvas is the pixel host for both drawing and real widgets.

The gallery, `ui-widgets`, and focused component examples use the pinned
[xu-ui-design token adapter](design/README.md). This maps reference colors and
styled control dimensions into Xu; Button, Checkbox, Switch, Radio, Slider, and Stepper
also use desktop styled painting.
The browser text host and basic widget geometry retain the limitations below.

The desktop snapshot is pinned in `stdlib/desktop-sources.json`. The existing
Chart divisor guards from site commit `b847723de6e77ee19e665bde1fd9db493737147f`
are recorded in `stdlib/desktop-adaptations.json`, with the original and adapted
declaration hashes (UTF-8 with LF) and exact replacements. Regeneration applies them only to the
matching upstream bodies; source checks reverse and replay every adaptation.
Additional browser adaptations skip exponent scaling for canonical zero style
scalars and pass typed styles directly to ColorPicker's private channel sliders.
The parent validates the styles once; its private sliders reuse the same geometry
calculation without repeating the full Styles validation for every RGBA row.
The color values, slider input and painting still execute in Xu; the browser does
not approximate the controls or redraw their values independently.
Opaque ColorPicker swatches skip the fully covered transparency grid.
The browser focus adaptation treats a zero focus inset as one emphasized
boundary. Shared control boxes, Slider thumbs, joined ButtonGroup segments, and RangeSlider
thumbs replace their regular border instead of adding another outline. Styles
with a positive focus inset keep the upstream inset-ring behavior. Selection
and focus still belong to the Xu widgets.
When a program supplies widget input, Canvas leaves focus painting to those
controls; it does not add a second outline around the entire preview. Basic
Scroll paints its own viewport boundary. Tabs, Segmented and ListBox use the
pinned on-brand ink for selected labels; browser ListBox, choice menus and
pagination have 44 logical px hit areas at normal density. Fit scales the whole
fixed canvas for an overview; use 100% and the phone pan control for original-size
text and targets.
At intermediate widths the source pane has a bounded height and its editor
scrolls internally, so long programs do not push the preview thousands of pixels
down the page. Phone tabs retain their flexible panel height.
Menu and ButtonGroup navigation guard a local positive item count before modulo.

Open `/playground/?example=ui-gallery` (or `/zh/playground/?example=ui-gallery`)
for a three-page control gallery. `ui-widgets`, `ui-draw`, and `ui-counter`
remain available. Explicit example links load and run; ordinary selection waits
for Run Code. The reviewable source is `examples/ui-gallery.xu`; its JSON entry
is checked against that file.
The basic controls example is kept in `examples/ui-widgets.xu` and synchronized
into the catalog by `scripts/gen-widget-examples.py`. Its active and checked
fills use XUUI brand/on-brand colors rather than the SDK's default blue theme.

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

`stdlib/desktop_widgets.xu` contains complete declarations selected
from `xu/src/ui/widgets`, including constructors, state/input methods, basic
paint, focus rings, rounded paths, theme primitives, StyledLabel text paint,
and the read-only Editor paint path. Divider and Segmented Tabs basic APIs are
also mirrored, with the hashed browser adaptations described above. This is a
larger gallery subset, not the complete desktop suite.

`stdlib/desktop_*.xu` supplies necessary desktop layout, math, UTF-8 validation,
input, text/color/path types, style resolution, and motion initialization.
The focused component experiences additionally run Select, Stepper, RadioGroup,
Pagination, Breadcrumbs, RangeSlider, SplitView, ButtonGroup, MultiSelect,
ColorPicker, Table, Chart, Popover, Modal, and dropdown/context/split Menu modes. Their
geometry, state, and input use desktop Xu declarations; painting includes the
documented browser adaptations above. Canvas forwards left/right/middle pointer
buttons and supplies drawing resources.

The Popover experience uses the desktop anchored surface, real checkboxes and
buttons. It paints the floating surface after background guidance and clips
child content within its padding. Apply saves preferences; Cancel, Escape,
outside presses and pointer cancellation discard edits and restore trigger
focus. Reduced motion keeps the input-replay example deterministic. Placement
and edge flipping remain desktop logic; Screen and native event pumps are not
needed. The source is maintained in `scripts/widget_popover_example.py` and
published by `scripts/gen-widget-examples.py`.

MultiSelect and Select explicitly paint their popup surfaces and options after
the trigger. ComboBox combines bounded browser key editing with the desktop Menu
for visible candidates, filtering, selection and dismissal. Modal uses the desktop
dialog, real Cancel/Apply buttons, a trapped focus order and trigger restoration.
Its background remains blocked until the dialog closes.

The composed browser examples in `scripts/widget_state_examples.py` demonstrate
TreeView expansion and node selection, a selectable October 25–31 date strip with
Reset/Clear, minute adjustment and 12/24-hour formatting, focus/click tooltip
dismissal, three visible notifications with Clear, and a refreshable WebView
placeholder. They execute Xu and use native Button input; they do not implement
the desktop tree, full calendar, hover timing, notification scheduler or webpage
engine. Their captions describe that boundary. TaskButton also previews states
without starting a background task. Bounded Input/Field examples edit the end of
one line using basic keys; full selection, clipboard and IME require the SDK.
Their end caret shares the text layout so browser glyph advances determine its
position. Multiline counters consistently count Unicode code points.

Extension declarations are partitioned by their dependency owners in
`desktop-sources.json`. The runtime scans user identifier tokens, loads only the
requested families and shared declarations, and parses each package once.
Existing basic programs keep their original subset. Native event pumps, Screen,
WebView, editable input and the remaining complete component implementations are
not exposed by the WASM subset. Composed Xu examples describe their limited
behavior, while the separate JavaScript interaction previews are marked as not
executing Xu; neither replaces the desktop implementation.

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
  intrinsics. Strings follow Xu's indirect descriptor ABI. Pure codec operations,
  finite metric checks, UTF-8 validation, style cloning/resolution/validation,
  rounded geometry and drawing commands have equivalent AOT paths. Style clones
  retain independent strings and state arrays. Invalid validation inputs,
  inactive frames and unsupported strokes fall back to MIR so Xu error propagation is preserved.
  `createRuntime(..., {fastIntrinsics:false})` runs the original scalar MIR for
  equivalence testing. Decoded 56-byte instructions cache their intrinsic ID at
  offset 48, avoiding repeated function-name comparisons during interpretation.
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
1.25 × size). Canvas uses the XUUI sans-serif font stack at its natural glyph
proportions, without horizontally squeezing text to the estimated advance.
Canvas centers the visible glyph bounds vertically within the 1.25 × size line
box, using an alphabetic baseline. If glyph bounds are unavailable, it falls
back to font bounds and then an em-box estimate. The horizontal layout origin
and enclosing clips still come from Xu. This is deterministic
basic text layout, not native shaping, wrapping, bidi, grapheme-cell measurement,
or IME. TextOptions fields other than size are outside this subset.
Focused component examples use measured text layouts rather than raw top-aligned
text. Single-line fields, floating labels, ColorPicker channel labels and toast
messages center their line boxes within their actual control bounds. Raw
`draw.text` remains a top-origin drawing API for user programs.
`layout_masked_text()` paints one mask character per code point on this grid
while caret and selection queries retain the original UTF-8 byte positions.
The original text is never included in the masked layout's Canvas paint command.

UI Preview uses the pinned XUUI theme, spacing, 40 px controls (44 px for touch
and narrow viewports), and 14 px interface text. Fit shows the whole 640 × 360
canvas, centered in the available viewport; 100% preserves its logical size in a
keyboard-scrollable viewport. Overflow remains reachable from the top and left.
Expand temporarily gives the results the editor's space; Back to editor restores
the editor without resetting project edits or widget values. The console
remains available. These display controls do not recolor user drawing commands
or change Xu's hit-test coordinates. Native font measurement and per-widget
accessibility remain outside the Canvas host's current scope.

## Floating-point VM support

The interpreter stores IEEE binary64 values as integer bits and reinterprets
them before typed floating-point operations. WebAssembly executes the arithmetic,
comparisons, and conversions. Canvas coordinates are serialized to six decimal
places, while widget geometry and state retain binary64 precision.

## Interaction and resource limits

Identical source reuses checked MIR in one WASM instance. Single-task programs
pause before an exhausted input read. Appended input resumes the checkpoint,
and a copy of the paused state runs the exhaustion and painting tail. Changes
to previous input replay from zero. Programs that use tasks or channels, or
exceed the 8 MiB checkpoint budget, use full replay. Edits and traps discard
the cached instance. State, measurement, hit testing, focus, activation, and
painting execute in Xu. The browser displays the final committed frame. The gallery paints
once after consuming history, which bounds draw output independently of event
count. Run Code, source edits, and example changes reset the session.

- Fixed 640 × 360 logical canvas, responsive display and pointer coordinates.
- At most 100,000 input records. A widget press and release each use one
  record. Counter clicks and drag motion also use one record each.
- Tab / Shift+Tab cycle controls in the gallery. Enter/Space activate the
  focused Button/Checkbox/Switch. Arrows, Home/End, and PageUp/PageDown adjust
  Slider. Esc is handled by the focused Xu control, allowing dialogs to restore
  trigger focus. Click requests focus through the widgets API. Complete pointer
  gestures, keys and drag releases are queued during replay; consecutive pending
  motion is coalesced. Interactive updates preserve the previous output while
  the worker redraws. Stopping/editing discards pending input.
- The worker allows 10 seconds for ordinary programs and 30 seconds for widget programs. The VM step limit and 256 MiB maximum linear memory bound execution.

Reading a documentation page does not preload WASM. Running an example starts
the shared worker on demand; explicit playground example links still run when
opened. Initialization loads the module and performs a bounded empty-program
warmup before reporting ready. The page downloads the module only when requested
and uses asynchronous WebAssembly compilation, then shares the compiled Module
with the worker. This avoids stalled large binary downloads in worker contexts
without moving instantiation or Xu execution onto the main thread. Compilation
is cached per page; failed downloads can be retried, and stopped workers never
receive a late initialization. The checked-MIR cache compiles requested source
once and reuses it for subsequent interactions.
Programs without explicit module imports skip the UI declarations during
preparation. Native map literals still load their runtime algorithms. Imported
module examples retain the existing browser library subset.
- Commands: 256 KiB / 4096 lines; transform stack: 32; text size: 1–256.
- No continuous animation, hover tracking while idle, native services/windows,
  WebView, full styled widgets, editable text input, or persistent external effects.
- The Canvas surface is keyboard operable, with state mirrored in stdout, but
  individual widgets do not yet expose a DOM accessibility tree.

## Build and preview

Use a published SDK whose compiler banner and source VERSION match the site's
VERSION. The build records the provenance of the vendored widget sources separately.
Set `XU_ALLOW_DEV=1` for a local development build. The SDK and compiler banner
must agree, and the resulting metadata marks the build as development-only.

```sh
npm ci --ignore-scripts
XU_ROOT=/path/to/released-sdk ./scripts/build-playground.sh
make check-playground
make check
python3 scripts/build-static.py --require-playground
python3 -m http.server 18110 --bind 127.0.0.1 --directory dist
```

The SDK compiles the interpreter to `wasm32-wasi`. The link step exposes the
worker entry points, caps linear memory at 256 MiB, and adds Xu build provenance.
The build runs the lockfile-pinned Binaryen optimizer using Node.js 22+.
The browser's WASI adapter provides two read-only virtual files for source and
input events and bounded streams for console output and Canvas commands.
The SDK handles type checking, typed MIR lowering, and native map semantics.
Input timestamps use a deterministic replay clock.
The build records the compiler version, optimizer version/flags, initial and
maximum memory, pre/post-optimization size, gzip size, WASM digest and widget-source manifest digest in
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

## Performance reproduction

After building with a matching SDK, run the production worker in Node:

```sh
node scripts/bench-playground.mjs --rounds=3 > /tmp/playground-timing.json
node scripts/bench-playground.mjs --example=ui-counter --rounds=3
node scripts/bench-playground.mjs --example=widget-color-picker --rounds=3 --clicks=8
node scripts/bench-playground.mjs --clicks=31 --rounds=3
# Disable reuse to measure compiler cost on the same artifact:
node scripts/bench-playground.mjs --cache=false --checkpoints=false --rounds=3
```

`--wasm=/absolute/path/to/artifact.wasm` selects an artifact. Each round creates a
fresh runtime, then measures press/release redraws and histories of 16, 63 and 64
records. The 63-record batch and the final single record are reported separately.
JSON includes raw samples and stage medians for instance setup, source-to-MIR
compilation, execution (including bounded snapshot copies), UTF-8 output decoding,
worker input/output serialization and transit, command validation, Canvas calls,
and input-to-mock-paint latency. It also records frame commands, transport bytes,
Canvas method counts, cache/resume hits, replayed events and arena high-water marks.
Canvas uses a counting mock; GPU rasterization, browser event dispatch, downloading
over a real network, and screen presentation are outside this measurement.
`tests/test_playground_cache.mjs` compares snapshots against complete replay and
checks edits, history resets, compiler diagnostics, wasm traps and arena reuse.
Run older WebAssembly artifacts with the benchmark driver and worker from
a checkout that uses their ABI. `scripts/build-playground-baseline.py` adds
compile and execute timing entry points to pre-split legacy runtimes.

## Linear-memory ABI

The worker calls `playground_prepare` to compile source and
`playground_execute` for complete replay. `playground_drive` processes an input
batch and can pause before an exhausted read. `playground_checkpoint` reports
the size of that state, and `playground_preview` runs a copy to finish the frame.
The worker preserves output produced before the checkpoint.

Each input record has eight i64 slots: kind, x, y, key, modifiers, repeat, button,
buttons, followed by two f64 slots for dx and dy. Pointer coordinates become f64 slots in `ui.InputEvent`; the browser
canvas identity is `(window_id:1, canvas_id:1, generation:1)`. Legacy
`next_click()` consumes x/y from the same record and returns `(x,y,ok)`.
Failures return no UI frame. The worker and Xu interpreter share the input
record layout and use little-endian WebAssembly values.
