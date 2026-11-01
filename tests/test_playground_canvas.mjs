// Exercise the real Xu → WASM → display-list boundary, including replay state.
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createRuntime, MAX_UI_EVENTS} from '../www/xu-play-runtime.mjs';

const runtime = await createRuntime(readFileSync(new URL('../build/playground/xu-play.wasm', import.meta.url)));
const examples = JSON.parse(readFileSync(new URL('../www/xu-play-examples.json', import.meta.url))).projects;
const context = {};
vm.runInNewContext(readFileSync(new URL('../www/xu-play-canvas.js', import.meta.url), 'utf8'), context);
const host = context.XuPlayCanvas;

test('Canvas accepts native rounded stroke options and rejects invalid enums and widths', () => {
  const path = 'begin\npath_begin\npath_move\t0\t0\npath_line\t10\t10\n';
  assert.ok(host.frame(path + 'path_stroke\t#ffffff\t1.5\t1\t1\t10\npresent\n'));
  assert.throws(() => host.frame(path + 'path_stroke\t#ffffff\t1.5\t9\t1\t10\npresent\n'), /stroke options/);
  assert.throws(() => host.frame(path + 'path_stroke\t#ffffff\t0\t1\t1\t10\npresent\n'), /stroke width/);
});

test('Xu emits draw commands separately from stdout, including Unicode', () => {
  const result = runtime.run(examples['ui-draw'].files['main.xu']);
  assert.equal(result.exit, 0, result.stderr);
  assert.equal(result.stdout, 'Canvas frame presented.\n');
  assert.equal(result.ui.interactive, false);
  assert.match(result.ui.commands, /你好，Xu!/);
  const display = host.frame(result.ui.commands);
  assert.ok(display.some(item => item.op === 'circle'));
  assert.ok(display.some(item => item.op === 'text' && item.args[4] === '你好，Xu!'));
});

test('Xu owns counter state, hit testing, reset, and a fresh session', () => {
  const run = events => runtime.run(examples['ui-counter'].files['main.xu'], {events});
  const plus = {x: 320, y: 200}, reset = {x: 500, y: 200}, miss = {x: 20, y: 20};
  const result = run([plus, plus, miss]);
  assert.equal(result.exit, 0, result.stderr);
  assert.equal(result.stdout, 'Count: 2\n');
  assert.equal(result.ui.interactive, true);
  const display = host.frame(result.ui.commands);
  assert.ok(display.some(item => item.op === 'text' && item.args[4] === 'Count: 2'));
  assert.equal(run([plus, reset]).stdout, 'Count: 0\n');
  assert.equal(run([]).stdout, 'Count: 0\n');
  assert.equal(run(Array(64).fill(plus)).stdout, 'Count: 64\n');
  assert.equal(runtime.run(examples.hello.source).ui, null);
});

test('edited Xu code changes both state transitions and drawing', () => {
  const source = examples['ui-counter'].files['main.xu'].replace('count += 1', 'count += 7').replace('#e11d48', '#22c55e');
  const result = runtime.run(source, {events: [{x: 320, y: 200}]});
  assert.equal(result.exit, 0, result.stderr);
  assert.equal(result.stdout, 'Count: 7\n');
  assert.match(result.ui.commands, /#22c55e/);
  assert.ok(host.frame(result.ui.commands).some(item => item.args[4] === 'Count: 7'));
});

test('UI input and output limits reject overflow; a new run recovers', () => {
  assert.throws(() => runtime.run('', {events: Array(MAX_UI_EVENTS + 1).fill({x: 0, y: 0})}), /limit/);
  for (const event of [{x: -1, y: 0}, {x: 640, y: 0}, {x: 0, y: 360}, {x: 1.5, y: 0}, null]) {
    assert.throws(() => runtime.run('', {events: [event]}), /coordinates/);
  }
  const result = runtime.run(`@main
#ui/draw
fn main() int {
 draw.begin()
 for i in 0:70 { draw.fill_rect(0, 0, 1, 1, "${'#' + 'a'.repeat(4096)}") }
 draw.present()
 << 0
}`);
  assert.notEqual(result.exit, 0);
  assert.match(result.stderr, /UI command buffer limit/);
  assert.equal(result.ui, null);
  assert.equal(runtime.run(examples['ui-draw'].files['main.xu']).exit, 0);
});

test('Canvas transaction commits the last present and discards cancelled work', () => {
  const commands = 'begin\nfill_rect\t1\t2\t3\t4\t#ff0000\npresent\nbegin\nfill_rect\t5\t6\t7\t8\t#00ff00\ncancel\n';
  const display = host.frame(commands);
  assert.equal(display.length, 1);
  assert.equal(display[0].args[4], '#ff0000');
  assert.equal(host.frame('begin\ncancel\n'), null);
});

test('Canvas rejects unsupported or malformed commands, sizes, and stack abuse', () => {
  for (const commands of [
    'html\t<script>alert(1)</script>',
    'begin\ntext\t0\t0\t18\turl(x)\tunsafe\npresent',
    'begin\ncircle\t0\t0\t-1\npresent',
    'begin\npop\npresent',
    'begin\nline\t0\t0\t1\t1\t#ffffff\t0\npresent',
    'begin\n' + 'push\n'.repeat(33) + 'present',
    'begin\n' + 'rect\t0\t0\t1\t1\n'.repeat(4096) + 'present'
  ]) assert.throws(() => host.frame(commands));
});

test('Canvas preserves natural XUUI glyph proportions instead of squeezing estimated widths', () => {
  const operations = [];
  const fakeCtx = {
    setTransform: () => {},
    fillRect: () => {},
    save: () => {},
    restore: () => {},
    scale: () => assert.fail('layout_text must not deform glyphs to match grid metrics'),
    measureText: () => assert.fail('estimated advances must not drive font compression'),
    fillText: (...args) => operations.push({op: 'fillText', args}),
    drawImage: () => {}
  };
  let staging;
  const canvas = {
    ownerDocument: {
      defaultView: {devicePixelRatio: 1},
      createElement: () => (staging = {getContext: () => fakeCtx})
    },
    getContext: () => fakeCtx
  };
  const commands = 'begin\nlayout_text\t10\t20\t14\t#ffffff\t16.8\t保存\nlayout_text\t20\t40\t14\t#ffffff\t1\tWide text\npresent\n';
  assert.equal(host.render(canvas, commands), true);
  assert.deepEqual(operations, [
    {op:'fillText', args:['保存',10,20]},
    {op:'fillText', args:['Wide text',20,40]}
  ]);
  assert.equal(fakeCtx.textBaseline, 'top');
  assert.equal(fakeCtx.font, '14px ' + host.fontStack);
});

test('measureText helper reports font metrics with fontStack default', () => {
  assert.ok(host.fontStack);
  assert.equal(host.fontStack, JSON.parse(readFileSync(new URL('../playground/design/tokens.json', import.meta.url))).base['font-sans']);
  const metrics = host.measureText('Xu', 14);
  assert.ok(metrics && typeof metrics.width === 'number');
  assert.ok(metrics.width > 0);
});
