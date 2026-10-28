import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createRuntime} from '../www/xu-play-runtime.mjs';
const runtime = await createRuntime(readFileSync(new URL('../build/playground/xu-play.wasm', import.meta.url)));
const source = JSON.parse(readFileSync(new URL('../www/xu-play-examples.json', import.meta.url)))['ui-widgets'].source;
const context = {};
vm.runInNewContext(readFileSync(new URL('../www/xu-play-canvas.js', import.meta.url), 'utf8'), context);
const host = context.XuPlayCanvas;
const run = (events = [], code = source) => {
  const result = runtime.run(code, {events});
  assert.equal(result.exit, 0, result.stderr);
  return result;
};
const click = (x,y) => [{kind:72, x,y,button:1}, {kind:73, x,y,button:1}];
const key = code => [{kind:78,key:code}, {kind:79,key:code}];
const labels = result => host.frame(result.ui.commands).filter(c => c.op === 'layout_text');

test('desktop widget input contract runs unchanged inside the WASM interpreter', () => {
  const result = run([], readFileSync(new URL('fixtures/playground_widgets.xu', import.meta.url), 'utf8'));
  assert.equal(result.stdout, 'widgets contract passed\n');
});

test('gallery uses real measurements, press/release states, focus rings, and cubic paths', () => {
  const initial = run();
  assert.equal(initial.ui.input, true);
  assert.equal(initial.ui.interactive, true);
  assert.equal(labels(initial)[0].args[4], 112.2);
  const measured = host.frame(initial.ui.commands).find(c => c.op === 'clip_rect');
  assert.equal(measured.args[2], 160.2);
  assert.equal(measured.args[3], 45.25);
  assert.ok(host.frame(initial.ui.commands).some(c => c.op === 'path_cubic'));
  const pressed = run(click(80,120).slice(0,1));
  assert.match(pressed.stdout, /Count: 0/);
  assert.match(pressed.ui.commands, /#232d3cff/);
  assert.match(pressed.ui.commands, /stroke_rect\t34\t102\t156.2\t41.25\t#93c5fdff/);
  assert.match(run(click(80,120)).stdout, /Count: 1/);
  const edited = run([], source.replace('17.0', '22.0'));
  assert.notEqual(labels(edited)[0].args[4], labels(initial)[0].args[4]);
  assert.equal(host.frame(edited.ui.commands).find(c => c.op === 'clip_rect').args[2], 193.2);
});

test('mouse, key, slider dragging, Shift+Tab, and cancellation drive Xu control state', () => {
  const events = [...click(80,120), ...key(258), ...click(60,185), ...key(32), ...click(60,240),
    ...click(470,190), ...key(262)];
  assert.equal(run(events).stdout, 'Count: 2 | Checkbox: false | Switch: true | Slider: 55\n');
  assert.match(run([...key(257), ...key(258), ...key(257), ...key(32)]).stdout, /Count: 1 \| Checkbox: true/);
  assert.match(run([...key(257), {kind:78,key:257,modifiers:1}, ...key(266)]).stdout, /Slider: 100/);
  assert.match(run([{kind:72,x:80,y:120,button:1}, {kind:77}, {kind:73,x:80,y:120,button:1}]).stdout, /Count: 0/);
  assert.match(run([{kind:72,x:80,y:120,button:1}, {kind:73,x:210,y:120,button:1}]).stdout, /Count: 0/);
  assert.match(run([{kind:72,x:340,y:190,button:1}, {kind:74,x:700,y:190}, {kind:73,x:700,y:190,button:1}]).stdout, /Slider: 100/);
  assert.match(run(Array.from({length:32}, () => click(80,120)).flat()).stdout, /Count: 32/);
});

test('editable Xu code changes widget state and native theme painting', () => {
  const edited = source.replace('count += 1', 'count += 7').replace('theme := widgets.default_theme()',
    'mut theme := widgets.default_theme()\n    theme.hovered = draw.rgb(220,40,80)');
  const result = run(click(80,120), edited);
  assert.match(result.stdout, /Count: 7/);
  assert.match(result.ui.commands, /#dc2850ff/);
  assert.match(run(click(80,120), source.replace('mut count := 0', 'button.set_enabled(false)\n    mut count := 0')).stdout, /Count: 0/);
});

test('typed input rejects invalid records and Canvas validates fractional paths and text', () => {
  for (const event of [{kind:999}, {kind:78,key:NaN}, {kind:72,button:-1}, {kind:74,x:Infinity}])
    assert.throws(() => runtime.run(source, {events:[event]}), /Invalid UI/);
  assert.doesNotThrow(() => host.frame('begin\nfill_rect\t0.5\t1.25\t2.5\t3.5\t#ffffff\npresent'));
  for (const cmd of ['path_fill\t#ffffff', 'path_cubic\t0\t0\t0\t0\t0\t0',
    'layout_text\t0\t0\t16\t#ffffff\t-1\tbad', 'fill_rect\tNaN\t0\t2\t2\t#ffffff'])
    assert.throws(() => host.frame('begin\n' + cmd + '\npresent'));
});
