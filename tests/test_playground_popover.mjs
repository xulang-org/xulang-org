import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {createRuntime} from '../www/xu-play-runtime.mjs';

const module = await WebAssembly.compile(readFileSync(new URL('../build/playground/xu-play.wasm', import.meta.url)));
const source = JSON.parse(readFileSync(new URL('../www/xu-play-examples.json', import.meta.url))).projects['widget-popover'].files['main.xu'];
const canvas = {};
vm.runInNewContext(readFileSync(new URL('../www/xu-play-canvas.js', import.meta.url), 'utf8'), canvas);
const click = (x,y) => [{kind:72,x,y,button:1,buttons:1},{kind:73,x,y,button:1}];
const key = key => [{kind:78,key},{kind:79,key}];
const labels = result => Array.from(canvas.XuPlayCanvas.frame(result.ui.commands))
  .filter(c=>c.op==='text'||c.op==='layout_text').map(c=>c.args.at(-1));

test('popover dismisses on Escape, outside press and pointer cancellation, then reopens from its trigger', async () => {
  const runtime = await createRuntime(module);
  for (const events of [key(256),click(580,280),[{kind:77}]]) {
    const closed = runtime.run(source,{events});
    assert.equal(closed.exit,0,closed.stderr);
    assert.match(closed.stdout,/^Popover: closed\n/);
    assert.ok(!labels(closed).includes('Workspace preferences'));
    const reopened = runtime.run(source,{events:[...events,...key(258)]});
    assert.equal(reopened.exit,0,reopened.stderr);
    assert.match(reopened.stdout,/^Popover: open\n/);
    assert.ok(labels(reopened).includes('Workspace preferences'));
  }
});

test('popover checkboxes and Apply/Cancel operate real Xu controls and restore saved preferences', async () => {
  const runtime = await createRuntime(module);
  const toggled = runtime.run(source,{events:click(260,150)});
  assert.equal(toggled.exit,0,toggled.stderr);
  assert.match(toggled.stdout,/History: false \| Auto save: true/);
  assert.match(toggled.stdout,/Saved history: true/);
  const cancelled = runtime.run(source,{events:[...click(260,150),...click(380,260)]});
  assert.equal(cancelled.exit,0,cancelled.stderr);
  assert.match(cancelled.stdout,/^Popover: closed\nHistory: true/);
  const applied = runtime.run(source,{events:[...click(260,150),...click(480,260)]});
  assert.equal(applied.exit,0,applied.stderr);
  assert.match(applied.stdout,/^Popover: closed\nHistory: false/);
  assert.match(applied.stdout,/Saved history: false/);
  const keyboard = runtime.run(source,{events:[...key(32),...key(257),...key(257),...key(257),...key(258)]});
  assert.equal(keyboard.exit,0,keyboard.stderr);
  assert.match(keyboard.stdout,/^Popover: closed\nHistory: false/);
  assert.match(keyboard.stdout,/Saved history: false/);
});

test('popover content is clipped inside a rounded neutral surface painted above background guidance', async () => {
  const runtime = await createRuntime(module);
  const result = runtime.run(source);
  assert.equal(result.exit,0,result.stderr);
  const commands = Array.from(canvas.XuPlayCanvas.frame(result.ui.commands));
  for (const text of ['Workspace preferences','保留历史记录','自动保存','Cancel','Apply']) assert.ok(labels(result).includes(text),text);
  assert.doesNotMatch(result.ui.commands,/☑|\[ Apply|#005f9e|#a8d9ff/i);
  const title = commands.findIndex(c=>c.op==='layout_text'&&c.args.at(-1)==='Workspace preferences');
  const guidance = commands.findIndex(c=>(c.op==='layout_text'||c.op==='text')&&c.args.at(-1)==='点击外部或 Esc 关闭');
  const clip = commands.findIndex(c=>c.op==='clip_rect'&&c.args[0]===224&&c.args[1]===98);
  assert.ok(guidance>=0&&guidance<clip&&clip<title,'background precedes clipped overlay content');
  assert.ok(commands.slice(guidance,clip).some(c=>c.op==='path_cubic'),'surface uses rounded corners');
  assert.ok(commands.slice(guidance,clip).some(c=>c.op==='path_stroke'&&c.args[0]!=='#be123cff'),'surface border stays neutral');
});

test('desktop popover placement flips at right and bottom edges and clips oversized panels', async () => {
  const runtime = await createRuntime(module);
  const result = runtime.run(`@main
#ui/widgets
#ui/layout
#playground
fn probe() int {
    identity := playground.canvas_identity()
    viewport := layout.Rect{x: 0.0,y: 0.0,width: 640.0,height: 360.0}
    anchor := layout.Rect{x: 560.0,y: 112.0,width: 32.0,height: 40.0}
    size := layout.Size{width: 344.0,height: 216.0}
    $panel := widgets.popover(&identity,10,&anchor,&size,&viewport) or >>
    $placement := widgets.overlay_placement()
    placement.side = widgets.OVERLAY_RIGHT
    panel.set_placement(&placement) or >>
    right := panel.bounds()
    assert(right.x + right.width < anchor.x)
    assert(right.x >= viewport.x && right.y + right.height <= 360.0)
    bottom_anchor := layout.Rect{x: 100.0,y: 304.0,width: 120.0,height: 40.0}
    placement.side = widgets.OVERLAY_BOTTOM
    panel.set_placement(&placement) or >>
    panel.set_geometry(&bottom_anchor,&size,&viewport) or >>
    bottom := panel.bounds()
    assert(bottom.y + bottom.height < bottom_anchor.y)
    tiny_viewport := layout.Rect{x: 20.0,y: 20.0,width: 44.0,height: 44.0}
    panel.set_geometry(&anchor,&size,&tiny_viewport) or >>
    tiny := panel.bounds()
    assert(tiny.x == 20.0 && tiny.y == 20.0 && tiny.width == 44.0 && tiny.height == 44.0)
    println("popover placement passed")
    << 0
}
fn main() int { << probe() or (err) { eprintln(err.msg())
    << 1 } }
`);
  assert.equal(result.exit,0,result.stderr);
  assert.equal(result.stdout,'popover placement passed\n');
});
