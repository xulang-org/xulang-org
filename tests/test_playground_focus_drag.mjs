import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {createRuntime} from '../www/xu-play-runtime.mjs';

const module = await WebAssembly.compile(readFileSync(new URL('../build/playground/xu-play.wasm', import.meta.url)));
const projects = JSON.parse(readFileSync(new URL('../www/xu-play-examples.json', import.meta.url))).projects;
const host = {};
vm.runInNewContext(readFileSync(new URL('../www/xu-play-canvas.js', import.meta.url), 'utf8'), host);
const click = (x,y) => [{kind:72,x,y,button:1,buttons:1},{kind:73,x,y,button:1}];
const key = key => [{kind:78,key},{kind:79,key}];

for (const [theme,brand,ink] of [['light','#be123cff','#fff8faff'],['dark','#ff5274ff','#190c12ff']]) {
  test('ButtonGroup pointer and keyboard selection has one contrasting boundary: ' + theme, async () => {
    const runtime = await createRuntime(module);
    const source = projects['widget-button-group'].files['main.xu']
      .replace('playground.light_styles()', 'playground.' + theme + '_styles()')
      .replace('playground.light_theme()', 'playground.' + theme + '_theme()');
    for (const events of [click(280,108), [...key(257),...key(262),...key(262),...key(258)]]) {
      const result = runtime.run(source,{events});
      assert.equal(result.exit,0,result.stderr);
      assert.equal(result.stdout,'Selected: 3\n');
      assert.doesNotMatch(result.ui.commands, /#005f9e|#a8d9ff/i);
      const paint = host.XuPlayCanvas.frame(result.ui.commands);
      const strokes = paint.filter(c=>c.op==='path_stroke');
      assert.equal(strokes.length,3,'each joined segment has one boundary, including the focused selection');
      assert.ok(paint.some(c=>c.op==='path_fill' && c.args[0]===brand),'selection keeps its cinnabar fill');
      assert.ok(strokes.some(c=>c.args[0]===ink && c.args[1]===2),'selected focus stays visible against the brand fill');
    }
  });
  test('RangeSlider keyboard focus replaces the thumb boundary without adding a halo: '+theme,async()=>{
    const runtime=await createRuntime(module);
    const source=projects['widget-range-slider'].files['main.xu']
      .replace('playground.light_styles()','playground.'+theme+'_styles()');
    const result=runtime.run(source,{events:key(257)});
    assert.equal(result.exit,0,result.stderr);
    const strokes=host.XuPlayCanvas.frame(result.ui.commands).filter(c=>c.op==='path_stroke');
    assert.equal(strokes.length,3,'one track border and one border per thumb');
    assert.equal(strokes.filter(c=>c.args[1]===2 && c.args[0]===brand).length,1,'focused thumb has one visible 2 px boundary');
  });
  test('Slider keyboard focus paints its thumb boundary once: '+theme,async()=>{
    const runtime=await createRuntime(module);
    const source=projects['widget-slider'].files['main.xu'].replace('playground.light_styles()','playground.'+theme+'_styles()');
    const result=runtime.run(source,{events:key(257)});
    assert.equal(result.exit,0,result.stderr);
    const strokes=host.XuPlayCanvas.frame(result.ui.commands).filter(c=>c.op==='path_stroke');
    assert.equal(strokes.length,2,'one track boundary and one thumb boundary');
    assert.equal(strokes.filter(c=>c.args[0]===brand && c.args[1]===2).length,1);
  });
}

for (const [theme,brand,ink,danger,border] of [
  ['light','#be123cff','#fff8faff','#b82138ff','#857987ff'],
  ['dark','#ff5274ff','#190c12ff','#ff8e9dff','#8a7e90ff']
]) {
  test('all shared control styles paint one boundary across focus and selection states: '+theme,async()=>{
    const runtime=await createRuntime(module);
    const result=runtime.run(`@main
#playground
#ui/widgets
#ui/draw
#ui/layout
fn paint_demo() int {
    styles := playground.${theme}_styles()
    controls := [styles.button.clone(),styles.checkbox.clone(),styles.input.clone(),styles.text_area.clone(),styles.progress.clone(),styles.scroll.clone()]
    states := [0,widgets.STATE_FOCUSED,widgets.STATE_FOCUSED | widgets.STATE_SELECTED,
        widgets.STATE_FOCUSED | widgets.STATE_INVALID,widgets.STATE_FOCUSED | widgets.STATE_DISABLED,
        widgets.STATE_FOCUSED | widgets.STATE_PRESSED,widgets.STATE_FOCUSED | widgets.STATE_SELECTED | widgets.STATE_READ_ONLY]
    context := draw.default_context()
    $frame := context.new_frame(8192)
    frame.begin() or >>
    for row in 0:controls.len {
        for col in 0:states.len {
            bounds := layout.Rect{x: 8.0 + f64(col) * 88.0,y: 8.0 + f64(row) * 52.0,width: 80.0,height: 40.0}
            widgets.paint_box_styled($&frame,&bounds,&styles,&controls[row],states[col]) or >>
        }
    }
    $transparent_focus := styles.button.clone()
    transparent_focus.palette.focus = draw.rgba(0,0,0,0)
    transparent_focus.states = []widgets.StatePaint{}
    widgets.paint_box_styled($&frame,&layout.Rect{x: 8.0,y: 320.0,width: 80.0,height: 32.0},&styles,&transparent_focus,widgets.STATE_FOCUSED) or >>
    $inset_focus := styles.button.clone()
    inset_focus.focus_inset = 3.0
    widgets.paint_box_styled($&frame,&layout.Rect{x: 96.0,y: 320.0,width: 80.0,height: 32.0},&styles,&inset_focus,widgets.STATE_FOCUSED) or >>
    frame.present() or >>
    << 0
}
fn main() int {
    << paint_demo() or (err) { eprintln(err.msg())
        << 1 }
}
`);
    assert.equal(result.exit,0,result.stderr);
    const strokes=host.XuPlayCanvas.frame(result.ui.commands).filter(c=>c.op==='path_stroke');
    assert.equal(strokes.length,45,'42 shared states, one transparent-focus border, and two legacy inset strokes');
    const expected=[[border,1],[brand,2],[ink,2],[danger,2],[border,1],[brand,2],[brand,2]];
    for(let i=0;i<42;i++) assert.deepEqual(Array.from(strokes[i].args).slice(0,2),expected[i%7]);
    assert.deepEqual(Array.from(strokes.slice(42),c=>Array.from(c.args).slice(0,2)),[[border,1],[brand,1],[brand,2]]);
  });
}

test('ColorPicker drag and release match full replay through the optimized typed paint path', async () => {
  const fast = await createRuntime(module);
  const reference = await createRuntime(module,{checkpoints:false});
  const source = projects['widget-color-picker'].files['main.xu'];
  const events = [{kind:72,x:280,y:182,button:1,buttons:1}];
  for (const x of [310,340,370,400]) events.push({kind:74,x,y:182,buttons:1});
  events.push({kind:73,x:400,y:182,button:1});
  fast.run(source);
  for (const end of [1,4,events.length]) {
    const {timings,...result} = fast.run(source,{events:events.slice(0,end),profile:true});
    assert.equal(result.exit,0,result.stderr);
    assert.equal(timings.compileMs,0);
    assert.equal(timings.resumeHit,true);
    assert.deepEqual(result,reference.run(source,{events:events.slice(0,end)}));
    assert.doesNotMatch(result.ui.commands,/#005f9e|#a8d9ff/i);
  }
  assert.equal(fast.run(source,{events}).stdout,'Color: #B4B132FF\n');
});

test('scalar and UTF-8 intrinsics match MIR for zero, subnormal, finite and invalid values', async () => {
  const source = `@main
#ui/widgets
#ui/internal/codec
#unicode/utf8
fn codec_family(p &widgets.ColorPicker) bool { << p.is_enabled() }
fn probe() int {
    zero := string_from_bytes([0,0,0,0,0,0,0,0])
    minus_zero := string_from_bytes([0,0,0,0,0,0,0,128])
    for i in 0:128 {
        first := codec.read_float64(&zero,0) or >>
        second := codec.read_float64(&minus_zero,0) or >>
        assert(first == 0.0)
        assert(second == 0.0)
    }
    value := string_from_bytes([0,0,0,0,0,0,4,192])
    number := codec.read_float64(&value,0) or >>
    assert(number == 0.0 - 2.5)
    tiny := string_from_bytes([1,0,0,0,0,0,0,0])
    subnormal := codec.read_float64(&tiny,0) or >>
    assert(subnormal > 0.0)
    for value in [0.0,0.0 - 2.5,1.0,255.0,1000000000.0,1000000001.0,subnormal] {
        bits := codec.finite_f64_bits(value)
        println(bits)
    }
    for text in ["", "XUUI 中文 😀", string_from_bytes([194,128]), string_from_bytes([224,160,128]),
        string_from_bytes([244,143,191,191]), string_from_bytes([128]), string_from_bytes([192,128]),
        string_from_bytes([224,128,128]), string_from_bytes([237,160,128]), string_from_bytes([240,128,128,128]),
        string_from_bytes([244,144,128,128]), string_from_bytes([245,128,128,128]), string_from_bytes([226,130])] {
        println(utf8.valid(&text))
    }
    invalid := string_from_bytes([0,0,0,0,0,0,240,127])
    _ := codec.read_float64(&invalid,0) or (err) {
        assert(err.msg() == "ui: invalid native floating-point scalar")
        println("scalar decoding passed")
        << 0
    }
    << 1
}
fn main() int { << probe() or (err) { eprintln(err.msg())
    << 1 } }
`;
  const fast = await createRuntime(module);
  const reference = await createRuntime(module,{fastIntrinsics:false});
  const result = fast.run(source);
  assert.equal(result.exit,0,result.stderr);
  assert.match(result.stdout,/scalar decoding passed\n$/);
  assert.deepEqual(result,reference.run(source));
});
