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
  test('ButtonGroup pointer and keyboard focus use cinnabar with contrasting selected focus: ' + theme, async () => {
    const runtime = await createRuntime(module);
    const source = projects['widget-button-group'].files['main.xu']
      .replace('playground.light_styles()', 'playground.' + theme + '_styles()')
      .replace('playground.light_theme()', 'playground.' + theme + '_theme()');
    for (const events of [click(280,108), [...key(257),...key(262),...key(262),...key(258)]]) {
      const result = runtime.run(source,{events});
      assert.equal(result.exit,0,result.stderr);
      assert.equal(result.stdout,'Selected: 3\n');
      assert.doesNotMatch(result.ui.commands, /#005f9e|#a8d9ff/i);
      const strokes = host.XuPlayCanvas.frame(result.ui.commands).filter(c=>c.op==='path_stroke');
      assert.ok(strokes.some(c=>c.args[0]===brand),'focus boundary uses the brand color');
      assert.ok(strokes.some(c=>c.args[0]===ink && c.args[1]===2),'selected focus stays visible against the brand fill');
    }
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
