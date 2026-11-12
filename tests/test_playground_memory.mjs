import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createRuntime} from '../www/xu-play-runtime.mjs';

const bytes = readFileSync(new URL('../build/playground/xu-play.wasm', import.meta.url));
const color = readFileSync(new URL('../playground/examples/widget-color-picker.xu', import.meta.url), 'utf8');
const build = JSON.parse(readFileSync(new URL('../build/playground/build.json', import.meta.url)));
const hello = '@main\nfn main() int { println("small")\n << 0 }';
const MiB = 1024 * 1024;

// Constrain the engine's maximum to exercise memory.grow failure, including
// failure after an earlier growth detached the host's original buffer.
function withMaximum(mebibytes) {
  const read = at => {
    let value = 0, shift = 0, byte;
    do { byte = bytes[at++]; value |= (byte & 127) << shift; shift += 7; } while (byte & 128);
    return [value, at];
  };
  const leb = value => {
    const out = [];
    do { const byte = value & 127; value >>>= 7; out.push(byte | (value ? 128 : 0)); } while (value);
    return Buffer.from(out);
  };
  const parts = [bytes.subarray(0, 8)];
  for (let at = 8; at < bytes.length;) {
    const start = at, tag = bytes[at++];
    const [size, body] = read(at);
    at = body + size;
    if (tag === 5) {
      const memory = Buffer.concat([Buffer.from([1, 1]), leb(build.initial_memory_bytes / 65536), leb(mebibytes * 16)]);
      parts.push(Buffer.from([tag]), leb(memory.length), memory);
    } else parts.push(bytes.subarray(start, at));
  }
  return Buffer.concat(parts);
}

test('small programs reuse the WASM instance after compiler memory growth', async () => {
  const module = await WebAssembly.compile(bytes);
  assert.equal(WebAssembly.Module.customSections(module, 'xu.source').length, 1);
  const runtime = await createRuntime(module);
  const result = runtime.run(hello, {profile: true});
  assert.equal(result.exit, 0, result.stderr);
  assert.equal(result.stdout, 'small\n');
  assert.ok(result.timings.memoryBytes >= build.initial_memory_bytes);
  assert.ok(result.timings.memoryBytes <= 64 * MiB);
  const again = runtime.run(hello, {profile: true});
  assert.equal(again.timings.cacheHit, true);
  assert.equal(again.timings.memoryBytes, result.timings.memoryBytes);
});

test('component preparation grows memory and cached input preserves views and checkpoints', async () => {
  const runtime = await createRuntime(bytes);
  const initial = runtime.run(color, {profile: true});
  assert.equal(initial.exit, 0, initial.stderr);
  assert.ok(initial.timings.memoryBytes > 32 * MiB);
  assert.ok(initial.timings.memoryBytes <= 256 * MiB);
  const selected = runtime.run(color, {profile: true, events: [
    {kind: 72, x: 250, y: 151, button: 1}, {kind: 73, x: 250, y: 151, button: 1}
  ]});
  assert.equal(selected.exit, 0, selected.stderr);
  assert.equal(selected.timings.cacheHit, true);
  assert.match(selected.stdout, /^Color: #[0-9A-F]{8}\n$/);
  assert.ok(selected.ui.commands.length);
  const edited = runtime.run(hello, {profile: true});
  assert.equal(edited.stdout, 'small\n');
  assert.ok(edited.timings.memoryBytes < initial.timings.memoryBytes);
});

test('execution growth works without checkpoint entry points', async () => {
  const runtime = await createRuntime(bytes, {checkpoints: false});
  const result = runtime.run('@main\nfn main() int { $s := "x"\n for i in 0:24 { s = s + s }\n println(s.len)\n << 0 }', {profile: true});
  assert.equal(result.exit, 0, result.stderr);
  assert.equal(result.stdout, '16777216\n');
  assert.ok(result.timings.memoryBytes > 32 * MiB);
});

test('large execution snapshots fall back to replay within the 8 MiB host budget', async () => {
  const runtime = await createRuntime(bytes);
  const source = '@main\n#playground\nfn main() int { $s := "x"\n for i in 0:22 { s = s + s }\n $count := 0\n while true { event := playground.next_input()\n if event.kind == 0 { <- }\n if event.kind == 73 { count += 1 } }\n println(s.len)\n println(count)\n << 0 }';
  const first = runtime.run(source, {profile: true});
  assert.equal(first.exit, 0, first.stderr);
  assert.equal(first.stdout, '4194304\n0\n');
  assert.equal(first.timings.checkpointBytes, 0);
  const next = runtime.run(source, {profile: true, events: [{kind: 73, button: 1}]});
  assert.equal(next.exit, 0, next.stderr);
  assert.equal(next.stdout, '4194304\n1\n');
  assert.equal(next.timings.resumeHit, false);
  assert.equal(next.timings.checkpointBytes, 0);
});

for (const maximum of [64, 96]) {
  test(`engine growth failure at ${maximum} MiB reports a limit and permits recovery`, async () => {
    const runtime = await createRuntime(withMaximum(maximum));
    const result = runtime.run(color, {profile: true});
    assert.equal(result.exit, 1);
    assert.match(result.stderr, /memory limit exceeded/);
    assert.ok(result.timings.memoryBytes > build.initial_memory_bytes);
    assert.ok(result.timings.memoryBytes <= maximum * MiB);
    const recovered = runtime.run(hello, {profile: true});
    assert.equal(recovered.exit, 0, recovered.stderr);
    assert.equal(recovered.stdout, 'small\n');
    assert.equal(recovered.timings.cacheHit, false);
  });
}
