// Cache regressions: reuse compiler metadata while replaying user state from zero.
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createRuntime} from '../www/xu-play-runtime.mjs';

const bytes = readFileSync(new URL('../build/playground/xu-play.wasm', import.meta.url));
const examples = JSON.parse(readFileSync(new URL('../www/xu-play-examples.json', import.meta.url))).projects;
const source = examples['ui-counter'].files['main.xu'];

test('cached MIR replays from zero and recycles the execution arena across long sessions', async () => {
  const runtime = await createRuntime(bytes);
  const run = events => runtime.run(source, {events, profile: true});
  const first = run([]);
  assert.equal(first.exit, 0, first.stderr);
  assert.equal(first.timings.cacheHit, false);
  const history = Array(64).fill({x: 320, y: 200});
  const full = run(history);
  assert.equal(full.stdout, 'Count: 64\n');
  assert.equal(full.timings.cacheHit, true);
  assert.equal(full.timings.compileMs, 0);
  assert.equal(full.timings.instanceMs, 0);
  // Resolve every call site before comparing stable arena high-water marks.
  const warm = run([]);
  for (let i = 0; i < 20; i++) {
    const result = run([]);
    assert.equal(result.stdout, 'Count: 0\n');
    assert.equal(result.ui.commands, first.ui.commands);
    assert.equal(result.timings.arenaEnd, warm.timings.arenaEnd);
  }
  const again = run(history);
  assert.equal(again.stdout, full.stdout);
  assert.equal(again.ui.commands, full.ui.commands);
  assert.ok(again.timings.arenaEnd <= full.timings.arenaEnd);
  assert.equal(run(history).timings.arenaEnd, again.timings.arenaEnd);
  const edit = runtime.run(source.replace('count += 1', 'count += 7'), {events: [{x:320,y:200}], profile:true});
  assert.equal(edit.stdout, 'Count: 7\n');
  assert.equal(edit.timings.cacheHit, false);
});

test('compile diagnostics survive reuse; parser and execution traps discard the interrupted instance', async () => {
  const runtime = await createRuntime(bytes);
  const recursive = examples.recursion.source;
  const first = runtime.run(recursive, {profile:true});
  const again = runtime.run(recursive, {profile:true});
  assert.equal(again.stdout, first.stdout);
  assert.equal(again.stderr, first.stderr);
  assert.match(again.stderr, /warning: recursive call cycle/);
  assert.equal(again.timings.cacheHit, true);
  const broken = runtime.run('fn main() int { println(\n', {profile:true});
  assert.notEqual(broken.exit, 0);
  assert.match(broken.stderr, /error:/);
  // Exponential strings trap at the fixed arena limit, exercising an
  // interrupted wasm stack rather than an ordinary VM diagnostic.
  const bad = '@main\nfn main() int { $s := "x"\n for i in 0:32 { s = s + s }\n println(s)\n << 0 }';
  for (let i = 0; i < 2; i++) {
    const trapped = runtime.run(bad, {profile:true});
    assert.equal(trapped.exit, 1);
    assert.match(trapped.stderr, /memory limit exceeded/);
    assert.equal(trapped.timings.cacheHit, false);
  }
  const recovered = runtime.run(source, {profile:true});
  assert.equal(recovered.exit, 0, recovered.stderr);
  assert.equal(recovered.stdout, 'Count: 0\n');
  assert.equal(recovered.timings.cacheHit, false);
});

test('incremental input snapshots match full replay through clicks, history rewrites and page changes', async () => {
  const fast = await createRuntime(bytes);
  const reference = await createRuntime(bytes, {checkpoints:false});
  const gallery = examples['ui-gallery'].files['main.xu'];
  const click = (x,y) => [{kind:72,x,y,button:1,buttons:1}, {kind:73,x,y,button:1}];
  const histories = [[], click(100,125), [...click(100,125), ...click(260,125)],
    [...click(100,125), ...click(520,62)], // rewrite history: no snapshot reuse
    [...click(100,125), ...click(520,62), ...click(320,62)],
    [...click(100,125), ...click(520,62), ...click(320,62), {kind:80,x:450,y:170,dy:42.5}],
    [], Array.from({length:32}, () => click(100,125)).flat()];
  for (const events of histories) {
    const expected = reference.run(gallery, {events});
    const actual = fast.run(gallery, {events, profile:true});
    const {timings, ...result} = actual;
    assert.equal(actual.exit, 0, actual.stderr);
    assert.deepEqual(result, expected);
    assert.ok(timings.checkpointBytes <= 8 * 1024 * 1024);
  }
  // Same 64-event history now resumes the exhausted read, retaining state.
  const last = fast.run(gallery, {events:histories.at(-1), profile:true});
  assert.equal(last.timings.resumeHit, true);
  assert.equal(last.timings.replayedEvents, 0);
  assert.match(last.stdout, /Count: 32/);
});

test('programs with spawned tasks keep deterministic complete replay', async () => {
  const runtime = await createRuntime(bytes);
  const concurrent = source.replace('fn main() int {', 'fn noop() {}\nfn main() int {\n xu noop()');
  const events = [{x:320,y:200}];
  const first = runtime.run(concurrent, {events, profile:true});
  const again = runtime.run(concurrent, {events:[...events, ...events], profile:true});
  assert.equal(first.stdout, 'Count: 1\n');
  assert.equal(again.stdout, 'Count: 2\n');
  assert.equal(again.timings.resumeHit, false);
});
