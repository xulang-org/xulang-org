import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {test} from 'node:test';
import vm from 'node:vm';
import {createRuntime} from '../www/xu-play-runtime.mjs';

const bytes = readFileSync(new URL('../build/playground/xu-play.wasm', import.meta.url));
const module = await WebAssembly.compile(bytes);
const runtime = await createRuntime(module);
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

test('input checkpoints replay only the suffix and match complete replay', async () => {
  const source = sourceFor('ui-gallery');
  const fast = await createRuntime(module);
  const reference = await createRuntime(module, {checkpoints: false});
  const click = (x, y) => [{kind: 72, x, y, button: 1, buttons: 1}, {kind: 73, x, y, button: 1}];
  const first = click(100, 125);
  const second = [...first, ...click(260, 125)];
  const changed = [...first, ...click(520, 62)];
  const scroll = [...changed, ...click(320, 62), {kind: 80, x: 450, y: 170, dy: 42.5}];
  const long = Array.from({length: 32}, () => click(100, 125)).flat();
  for (const [events, resume, replayed] of [
    [[], false, 0], [first, true, 2], [second, true, 2], [changed, false, 4],
    [scroll, true, 3], [first, false, 2], [[], false, 0],
    [long, true, 64], [long, true, 0], [[...long, ...first], true, 2],
  ]) {
    const {timings, ...result} = fast.run(source, {events, profile: true});
    assert.equal(result.exit, 0, result.stderr);
    assert.deepEqual(result, reference.run(source, {events}));
    assert.equal(timings.resumeHit, resume);
    assert.equal(timings.replayedEvents, replayed);
    assert.ok(timings.checkpointBytes > 0 && timings.checkpointBytes <= 8 * 1024 * 1024);
  }
});

test('checkpoint previews retain prefix output and discard exhausted-read effects', async () => {
  const source = `@main
#playground
fn main() int {
    $count := 0
    println("start")
    while true {
        click := playground.next_click()
        if click.ok == 0 { <- }
        count += 1
        println(click.x)
    }
    println("end " + str(count))
    << 0
}`;
  const runtime = await createRuntime(module);
  assert.equal(runtime.run(source).stdout, 'start\nend 0\n');
  const clicked = runtime.run(source, {events: [{x: 14, y: 2}], profile: true});
  assert.equal(clicked.timings.resumeHit, true);
  assert.equal(clicked.stdout, 'start\n14\nend 1\n');
  const two = runtime.run(source, {events: [{x: 14, y: 2}, {x: 25, y: 2}], profile: true});
  assert.equal(two.timings.replayedEvents, 1);
  assert.equal(two.stdout, 'start\n14\n25\nend 2\n');
});

test('tasks and checkpoints larger than 8 MiB use full replay', async () => {
  const runtime = await createRuntime(module);
  const reference = await createRuntime(module, {checkpoints: false});
  const counter = sourceFor('ui-counter');
  const concurrent = counter.replace('fn main() int {', 'fn noop() {}\nfn main() int {\n    xu noop()');
  const large = counter.replace('fn main() int {', `fn main() int {
    $values := make_ints(1200000)
    for i in 0:140 { values[i * 8192] = i + 1 }
    assert(values[100 * 8192] == 101)`);
  const events = [{x: 300, y: 200}];
  for (const source of [concurrent, large]) {
    for (const history of [[], events]) {
      const {timings, ...result} = runtime.run(source, {events: history, profile: true});
      assert.equal(result.exit, 0, result.stderr);
      assert.equal(timings.resumeHit, false);
      assert.equal(timings.checkpointBytes, 0);
      assert.deepEqual(result, reference.run(source, {events: history}));
    }
  }
});

test('the console preserves the bounded output prefix and reports truncation', () => {
  const result = runtime.run(`@main
fn main() int {
    $text := "x"
    for i in 0:19 { text = text + text }
    println(text)
    << 0
}`);
  assert.equal(result.exit, 0, result.stderr);
  assert.equal(result.stdout, 'x'.repeat(256 * 1024));
  assert.equal(result.truncated, true);
});
