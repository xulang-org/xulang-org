import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {createRuntime} from '../www/xu-play-runtime.mjs';

const module = await WebAssembly.compile(readFileSync(new URL('../build/playground/xu-play.wasm', import.meta.url)));
const projects = JSON.parse(readFileSync(new URL('../www/xu-play-examples.json', import.meta.url), 'utf8')).projects;
const canvas = {};
vm.runInNewContext(readFileSync(new URL('../www/xu-play-canvas.js', import.meta.url), 'utf8'), canvas);
const click = (x, y) => [{kind: 72, x, y, button: 1, buttons: 1}, {kind: 73, x, y, button: 1, buttons: 0}];
const key = key => [{kind:78,key},{kind:79,key}];
for (const [slug, events, output] of [
  ['button', click(100, 124), 'Count: 1\n'],
  ['checkbox', click(100, 124), 'Value: true\n'],
  ['switch', click(100, 124), 'Value: true\n'],
  ['radio', click(100, 124), 'Value: true\n'],
  ['tabs', click(280, 124), 'Selected: 1\n'],
  ['slider', [...key(257),...key(262)], 'Value: 45\n'],
  ['segmented', [...key(257),...key(262)], 'Selected: 1\n'],
  ['list-box', [...key(257),...key(264)], 'Selected: 1\n'],
  ['scroll', [...key(257),...key(264)], 'Offset: 40\n'],
  ['progress', click(100, 280), 'Progress: 50\n'],
  ['badge', click(100, 280), 'Count: 1\n'],
  ['stepper', click(560,108), 'Value: 45\n'],
  ['select', [...key(257),...key(264)], 'Selected: 1\n'],
  ['radio-group', [...key(257),...key(264)], 'Selected: 1\n'],
  ['pagination', [...key(257),...key(262)], 'Page: 2\n'],
  ['breadcrumbs', click(150,108), 'Activated: 1\n'],
  ['range-slider', [...key(257),...key(262)], 'Range: 21 - 80\n'],
  ['split-view', [...key(257),...key(262)], 'Ratio: 41\n'],
  ['button-group', [...key(257),...key(262),...key(258)], 'Selected: 2\n'],
  ['multi-select', [...click(100,108),...click(100,150)], 'Selected count: 1\n'],
  ['color-picker', [...key(257),...key(262)], 'Color: #B54532FF\n'],
  ['table', [...key(257),...key(264)], 'Selected: 1\n'],
  ['menu', [...key(257),...key(258),...key(264),...key(258)], 'Command: 2\n'],
  ['context-menu', [{kind:72,x:100,y:108,button:2,buttons:2},{kind:73,x:100,y:108,button:2,buttons:0},...key(264),...key(258)], 'Command: 2\n'],
  ['split-button', click(100,108), 'Command: 1\n'],
  ['chart', click(300,220), 'Selected point: 2\n'],
  ['field', click(460,130), 'Field: empty (invalid)\n'],
  ['tree-view', click(100,110), 'Selected node: src/widgets | Expanded: false\n'],
  ['date-picker', [...click(100,110),...click(70,200)], 'Date: 2026-10-25\n'],
  ['time-picker', click(100,132), 'Time: 14:31:00\n'],
  ['tooltip', [...key(257),...key(256)], 'Tooltip: hidden\n'],
  ['toast-host', click(100,118), 'Active toasts: 3\n'],
  ['web-view', click(500,110), 'WebView preview refreshes: 1\n'],
  ['field-area', [...click(100,132),...key(259)], 'FieldArea: 29 characters\n'],
]) {
  test('component experience responds through Xu widget logic: ' + slug, async () => {
    const runtime = await createRuntime(module);
    const result = runtime.run(projects['widget-' + slug].files['main.xu'], {events});
    assert.equal(result.exit, 0, result.stderr);
    assert.equal(result.stdout, output);
    assert.ok(result.ui.commands.length);
    assert.ok(canvas.XuPlayCanvas.frame(result.ui.commands));
  });
}

const components = Object.entries(projects).filter(([id]) => id.startsWith('widget-'));
assert.equal(components.length, 46);
for (const [id, project] of components) {
  test('component starts with its declared output and a valid complete frame: '+id, async () => {
    const runtime = await createRuntime(module);
    const result = runtime.run(project.files['main.xu']);
    assert.equal(result.exit, 0, id + ': ' + result.stderr);
    assert.equal(result.stderr, '', id);
    assert.equal(result.stdout, project.expected.value, id);
    assert.ok(canvas.XuPlayCanvas.frame(result.ui.commands), id);
  });
}

test('selected tab, segment, and list labels use the on-brand ink', async () => {
  const runtime = await createRuntime(module);
  for (const [theme, ink] of [['light','#fff8faff'],['dark','#190c12ff']]) {
   for (const slug of ['tabs','segmented','list-box']) {
    const source = projects['widget-'+slug].files['main.xu']
      .replace('playground.light_styles()', 'playground.'+theme+'_styles()')
      .replace('playground.light_theme()', 'playground.'+theme+'_theme()');
    const result = runtime.run(source);
    assert.equal(result.exit,0,result.stderr);
    const commands = Array.from(canvas.XuPlayCanvas.frame(result.ui.commands));
    const selected = commands.find(c => c.op === 'layout_text' && c.args.at(-1) === 'Overview');
    assert.equal(selected.args[3], ink, slug+' '+theme);
   }
  }
});

test('button group reports checked selection separately from keyboard focus', async () => {
  const runtime = await createRuntime(module);
  const source = projects['widget-button-group'].files['main.xu'];
  assert.equal(runtime.run(source,{events:[...key(257),...key(262)]}).stdout,'Selected: 1\n');
  assert.equal(runtime.run(source,{events:[...key(257),...key(262),...key(258)]}).stdout,'Selected: 2\n');
});

test('date clear/reset and time format switch change visible state', async () => {
  const runtime = await createRuntime(module);
  const date = projects['widget-date-picker'].files['main.xu'];
  assert.equal(runtime.run(date,{events:click(220,262)}).stdout,'Date: Choose date 选择日期\n');
  assert.equal(runtime.run(date,{events:[...click(220,262),...click(100,262)]}).stdout,'Date: 2026-10-31\n');
  const time = runtime.run(projects['widget-time-picker'].files['main.xu'],{events:click(370,132)});
  assert.equal(time.stdout,'Time: 14:30:00\n');
  const labels = Array.from(canvas.XuPlayCanvas.frame(time.ui.commands)).filter(c => c.op === 'layout_text').map(c => c.args.at(-1));
  assert.ok(labels.includes('2:30:00 PM'));
  assert.ok(labels.includes('12-Hour'));
});

test('opening a real Xu menu paints its popup items into the frame', async () => {
  const runtime = await createRuntime(module);
  const result = runtime.run(projects['widget-menu'].files['main.xu'], {events:click(100,108)});
  assert.equal(result.exit,0,result.stderr);
  const labels = Array.from(canvas.XuPlayCanvas.frame(result.ui.commands)).filter(c => c.op === 'layout_text').map(c => c.args.at(-1));
  for (const label of ['Save','Export','Duplicate']) assert.ok(labels.includes(label), label + ' is visible in the popup');
});

test('clicking the table header sorts the actual Xu rows numerically', async () => {
  const runtime = await createRuntime(module);
  const result = runtime.run(projects['widget-table'].files['main.xu'], {events:click(500,108)});
  assert.equal(result.exit,0,result.stderr);
  const labels = Array.from(canvas.XuPlayCanvas.frame(result.ui.commands)).filter(c => c.op === 'layout_text').map(c => c.args.at(-1));
  assert.deepEqual(labels.filter(label => ['Design','Develop','Review'].includes(label)), ['Review','Develop','Design']);
});
