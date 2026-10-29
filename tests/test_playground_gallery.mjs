import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createRuntime} from '../www/xu-play-runtime.mjs';
const bytes = readFileSync(new URL('../build/playground/xu-play.wasm', import.meta.url));
const runtime = await createRuntime(bytes);
const source = readFileSync(new URL('../playground/examples/ui-gallery.xu', import.meta.url), 'utf8');
const context = {};
vm.runInNewContext(readFileSync(new URL('../www/xu-play-canvas.js', import.meta.url), 'utf8'), context);
const host = context.XuPlayCanvas;
const click = (x,y) => [{kind:72,x,y,button:1}, {kind:73,x,y,button:1}];
const key = key => [{kind:78,key}, {kind:79,key}];
function run(events = [], code = source) {
  const result = runtime.run(code, {events});
  assert.equal(result.exit, 0, result.stderr);
  if (result.ui) host.frame(result.ui.commands);
  return result;
}
const data = click(320,62), display = click(520,62);

test('gallery entry source is the reviewable Xu example and paints valid resource text', () => {
  const examples = JSON.parse(readFileSync(new URL('../www/xu-play-examples.json', import.meta.url))).projects;
  assert.equal(examples['ui-gallery'].files['main.xu'], source);
  const commands = host.frame(run().ui.commands);
  const labels = commands.filter(c => c.op === 'layout_text');
  assert.deepEqual(Array.from(labels, c => c.args.at(-1)), ['Basics','Data / Scroll','Display','Button +1','Checkbox','Switch','Radio A','Radio B']);
  assert.ok(labels.every(c => c.args[2] === 15 && c.args[4] > 0));
});

test('same native/WASM contract covers selection, scrolling, focus, stale identity, and read-only', () => {
  assert.equal(run([], readFileSync(new URL('fixtures/playground_gallery.xu', import.meta.url), 'utf8')).stdout, 'gallery contract passed\n');
});

test('gallery pointer, keyboard tabs, page focus changes, and radio exclusivity run in Xu', () => {
  assert.match(run([...click(100,125), ...click(400,235), ...key(257), ...key(262)]).stdout,
    /Page: 1 \| Count: 1 .*Radio: 1/);
  assert.match(run([...key(257), ...key(262), ...key(257), ...key(266)]).stdout, /Page: 1 .*List: 7/);
  assert.match(run([...click(400,235), ...click(400,185)]).stdout, /Radio: 0/);
  assert.match(run([...click(80,125), ...data, ...key(258), ...click(80,62)]).stdout, /Page: 0 \| Count: 1/);
});

test('fractional wheel deltas reach ListBox and Scroll, with clipped translated content', () => {
  const result = run([...data, {kind:80,x:90,y:170,dy:40.5}, {kind:80,x:450,y:170,dy:84.5}]);
  assert.match(result.stdout, /Scroll: 84/);
  const commands = host.frame(result.ui.commands);
  assert.ok(commands.some(c => c.op === 'translate' && c.args[0] === 322 && c.args[1] === 29.5));
  assert.ok(commands.some(c => c.op === 'clip_rect' && c.args[0] === 322 && c.args[3] === 172));
  assert.ok(commands.some(c => c.op === 'layout_text' && c.args.at(-1) === 'Array' && c.args[1] < 120));
  assert.match(run([...data, ...click(450,160), ...key(268)]).stdout, /Scroll: 164/);
});

test('display page paints real StyledLabel, Card stroke, Badge, Progress and display-only Editor', () => {
  const result = run(display);
  const commands = host.frame(result.ui.commands);
  assert.ok(commands.some(c => c.op === 'path_stroke'));
  assert.ok(commands.some(c => c.op === 'layout_text' && c.args.at(-1) === 'Desktop control logic'));
  assert.ok(commands.some(c => c.op === 'layout_text' && c.args.at(-1) === 'Read-only Editor / Xu ownership'));
  assert.ok(commands.some(c => c.op === 'clip_rect' && c.args[0] === 52 && c.args[1] === 208 && c.args[2] === 65.6));
  for (const color of ['#e88471ff', '#fb7185ff', '#a6adb6ff']) assert.match(result.ui.commands, new RegExp(color));
  const unicode = run(display, source.replace('Read-only Editor / Xu ownership', '只读 Xu / 🙂'));
  assert.match(unicode.ui.commands, /只读 Xu \/ 🙂/);
  assert.match(run([...display, ...key(258), ...key(32)]).stdout, /Page: 2 \| Count: 0/);
  const unsupported = runtime.run(source.replace('editor.set_read_only(true)', 'editor.focus_session(true)'));
  assert.equal(unsupported.exit, 1);
  assert.match(unsupported.stderr, /native text input unavailable/);
});

test('full event history stays within the fixed WASM memory and rejects malformed scroll input', () => {
  const events = Array.from({length:32}, () => click(100,125)).flat();
  assert.match(run(events).stdout, /Count: 32/);
  const instance = new WebAssembly.Instance(new WebAssembly.Module(bytes), {});
  assert.equal(instance.exports.memory.buffer.byteLength, 128 * 1024 * 1024);
  assert.throws(() => instance.exports.memory.grow(1), RangeError);
  for (const event of [{kind:80,dy:NaN}, {kind:80,dx:Infinity}, {kind:80,dy:100001}])
    assert.throws(() => runtime.run(source, {events:[event]}), /Invalid UI scroll/);
});
