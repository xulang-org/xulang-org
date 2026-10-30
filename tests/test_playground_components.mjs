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
  ['button-group', [...key(257),...key(262)], 'Selected: 2\n'],
  ['multi-select', [...click(100,108),...click(100,150)], 'Selected count: 1\n'],
  ['color-picker', [...key(257),...key(262)], 'Color: #B54532FF\n'],
  ['table', [...key(257),...key(264)], 'Selected: 1\n'],
  ['menu', [...key(257),...key(258),...key(264),...key(258)], 'Command: 2\n'],
  ['context-menu', [{kind:72,x:100,y:108,button:2,buttons:2},{kind:73,x:100,y:108,button:2,buttons:0},...key(264),...key(258)], 'Command: 2\n'],
  ['split-button', click(100,108), 'Command: 1\n'],
  ['chart', click(300,220), 'Selected point: 2\n'],
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
