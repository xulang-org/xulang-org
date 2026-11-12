import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {test} from 'node:test';
import vm from 'node:vm';
import {createTypedRuntime} from '../playground/typed/runtime.mjs';

const bytes = readFileSync(process.env.XU_TYPED_PLAYGROUND_WASM ??
  new URL('../build/playground-typed/xu-play.wasm', import.meta.url));
const module = await WebAssembly.compile(bytes);
const runtime = await createTypedRuntime(module);
const version = readFileSync(new URL('../VERSION', import.meta.url), 'utf8').trim();
const {projects} = JSON.parse(readFileSync(new URL('../www/xu-play-examples.json', import.meta.url), 'utf8'));
const canvas = {};
vm.runInNewContext(readFileSync(new URL('../www/xu-play-canvas.js', import.meta.url), 'utf8'), canvas);

function sourceFor(name) {
  return '@main\n' + Object.entries(projects[name].files)
    .filter(([path]) => !path.includes('/') && path.endsWith('.xu'))
    .map(([, source]) => source.replace(/^\s*@main\s*$/gm, ''))
    .join('\n\n');
}

test('the published SDK version and sandbox limit are recorded in the WASM', () => {
  const [identity] = WebAssembly.Module.customSections(module, 'xu.source');
  const build = JSON.parse(new TextDecoder().decode(identity));
  assert.equal(build.xu_version, version);
  assert.equal(build.target, 'wasm32-wasi');
  assert.match(build.sources_sha256, /^[0-9a-f]{64}$/);
  assert.ok(WebAssembly.Module.imports(module).every(({module}) => module === 'wasi_snapshot_preview1'));
  const imports = Object.fromEntries(WebAssembly.Module.imports(module).map(({name}) => [name, () => 52]));
  const {memory} = new WebAssembly.Instance(module, {wasi_snapshot_preview1: imports}).exports;
  assert.throws(() => memory.grow(4097 - memory.buffer.byteLength / 65536), RangeError);
});

for (const [name, project] of Object.entries(projects)) {
  test('catalog: ' + name, () => {
    const result = runtime.run(sourceFor(name));
    if (name === 'borrow') {
      assert.notEqual(result.exit, 0);
      assert.match(result.stderr, /cannot assign.*borrowed/);
      assert.equal(result.stdout, '');
      return;
    }
    assert.equal(result.exit, 0, result.stderr);
    assert.equal(result.stdout, project.expected.value);
    if (name.startsWith('ui-') || project.component) {
      assert.ok(result.ui?.commands);
      assert.ok(canvas.XuPlayCanvas.frame(result.ui.commands));
    }
  });
}

test('unbuffered channel rendezvous runs on the cooperative Xu runtime', () => {
  const result = runtime.run(`@main
fn send(ch chan int) { ch <- 42 }
fn main() int {
    ch := chan int{cap: 0}
    xu send(ch)
    println(<-ch)
    << 0
}`);
  assert.equal(result.exit, 0, result.stderr);
  assert.equal(result.stdout, '42\n');
  const blocked = runtime.run(`@main
fn main() int {
    ch := chan int{cap: 1}
    println(<-ch)
    << 0
}`);
  assert.notEqual(blocked.exit, 0);
  assert.match(blocked.stderr, /all tasks are asleep - deadlock/);
});

test('floating-point operands and conversions use IEEE binary64', () => {
  const result = runtime.run(`@main
fn main() int {
    $x := 1.5
    x += 2.25
    assert(x == 3.75 && -x < 0.0)
    assert(3.0 * 2.5 == 7.5 && 3.0 / 2.0 == 1.5)
    assert(f64(7) == 7.0 && int(-3.9) == -3)
    $values := [1.25, 2.5]
    values[0] += 0.75
    assert(values[0] == 2.0)
    println(x)
    << 0
}`);
  assert.equal(result.exit, 0, result.stderr);
  assert.equal(result.stdout, '3.75\n');
});

test('Canvas receives replayed click, keyboard, pointer, and scroll input', () => {
  const counter = runtime.run(sourceFor('ui-counter'), {events: [{x: 300, y: 200}]});
  assert.equal(counter.exit, 0, counter.stderr);
  assert.equal(counter.stdout, 'Count: 1\n');
  assert.equal(counter.ui.input, false);
  assert.equal(counter.ui.interactive, true);

  const click = (x, y) => [{kind: 72, x, y, button: 1}, {kind: 73, x, y, button: 1}];
  const key = code => [{kind: 78, key: code}, {kind: 79, key: code}];
  const widget = runtime.run(sourceFor('ui-widgets'), {events: [
    ...click(80, 120), ...key(258), ...click(60, 185), ...key(32),
    ...click(60, 240), ...click(470, 190), ...key(262),
  ]});
  assert.equal(widget.exit, 0, widget.stderr);
  assert.equal(widget.stdout, 'Count: 2 | Checkbox: false | Switch: true | Slider: 55\n');
  assert.equal(widget.ui.input, true);
  assert.ok(canvas.XuPlayCanvas.frame(widget.ui.commands));

  const scroll = runtime.run(`@main
#playground
fn main() int {
    event := playground.next_input()
    assert(event.kind == 76 && event.dx == -2.25 && event.dy == 12.5)
    << 0
}`, {events: [{kind: 76, dx: -2.25, dy: 12.5}]});
  assert.equal(scroll.exit, 0, scroll.stderr);
});

test('the standalone draw module masks Unicode text and preserves caret metrics', () => {
  const result = runtime.run(`@main
#ui/draw
fn main() int {
    context := draw.default_context()
    value := "a中🙂"
    options := draw.text_options(10.0)
    masked := context.layout_masked_text(&value,&options) or (err) { << 1 }
    hit := masked.caret(4,false) or (err) { << 2 }
    assert(int(masked.metrics.width) == 18 && int(hit.x) == 12 && hit.index == 4)
    $frame := context.new_frame(16)
    frame.begin() or (err) { << 3 }
    frame.text_layout(&masked,0.0,0.0,draw.rgb(255,255,255)) or (err) { << 4 }
    frame.present() or (err) { << 5 }
    << 0
}`);
  assert.equal(result.exit, 0, result.stderr);
  const labels = canvas.XuPlayCanvas.frame(result.ui.commands).filter(command => command.op === 'layout_text');
  assert.equal(labels.length, 1);
  assert.equal(labels[0].args.at(-1), '***');
});

test('typed MIR uses the released SDK semantics for owned map values', () => {
  const result = runtime.run(`@main
fn main() int {
    $values := map[int]string{}
    values[1] = "owner"
    println(values[1])
    << 0
}`);
  assert.equal(result.exit, 0, result.stderr);
  assert.equal(result.stdout, 'owner\n');
});

test('checked MIR is reused while each run replays from clean user state', async () => {
  const source = sourceFor('ui-counter');
  const cache = await createTypedRuntime(module);
  const first = cache.run(source, {profile: true});
  assert.equal(first.exit, 0, first.stderr);
  assert.equal(first.timings.cacheHit, false);
  const events = Array(32).fill({x: 300, y: 200});
  const {timings, ...clicked} = cache.run(source, {events, profile: true});
  assert.equal(clicked.exit, 0, clicked.stderr);
  assert.equal(clicked.stdout, 'Count: 32\n');
  assert.equal(timings.cacheHit, true);
  assert.equal(timings.compileMs, 0);
  const reference = await createTypedRuntime(module, {cache: false});
  assert.deepEqual(clicked, reference.run(source, {events}));
  for (let i = 0; i < 12; i++) {
    const replay = cache.run(source, {profile: true});
    assert.equal(replay.exit, 0, replay.stderr);
    assert.equal(replay.stdout, first.stdout);
    assert.equal(replay.ui.commands, first.ui.commands);
  }
  const edited = cache.run(source.replace('count += 1', 'count += 7'), {events: events.slice(0, 1), profile: true});
  assert.equal(edited.timings.cacheHit, false);
  assert.equal(edited.stdout, 'Count: 7\n');
});

test('rejected inputs and compile errors permit a fresh run', () => {
  const broken = runtime.run('fn main() int { println(\n');
  assert.notEqual(broken.exit, 0);
  assert.match(broken.stderr, /error:/);
  const unsupported = runtime.run('@main\n#os\nfn main() int { << 0 }');
  assert.notEqual(unsupported.exit, 0);
  assert.match(unsupported.stderr, /error:/);
  assert.throws(() => runtime.run('x'.repeat(128 * 1024 + 1)), /128 KiB/);
  assert.throws(() => runtime.run(sourceFor('ui-counter'), {events: [{x: 10, y: Infinity}]}), /Invalid UI/);
  const fresh = runtime.run(sourceFor('strings'));
  assert.equal(fresh.exit, 0, fresh.stderr);
  assert.equal(fresh.stdout, projects.strings.expected.value);
});
