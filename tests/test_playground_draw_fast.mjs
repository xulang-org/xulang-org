import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createRuntime} from '../www/xu-play-runtime.mjs';
const module=await WebAssembly.compile(readFileSync(new URL('../build/playground/xu-play.wasm',import.meta.url)));

test('text option scaling, copying and cache invalidation match checked MIR',async()=>{
 const source=`@main
#playground
#ui/widgets
#ui/draw
fn probe() int {
    $styles := playground.light_styles()
    context := draw.default_context()
    $label := widgets.styled_label(&context,&"Aa 中文 g│")
    for scale in [0.5,1.0,2.0] {
        styles.text_scale = scale
        for inherited in [false,true] {
            $control := styles.button.clone()
            control.inherit_font = inherited
            control.font.family = "Custom 字体"
            control.font.size = 18.0
            control.font.weight = 700
            control.font.italic = true
            control.font.line_height = 24.0
            options := styles.text_options(&control)
            println(options.family)
            println(options.size)
            println(options.width)
            println(options.weight)
            println(options.italic)
            println(options.align)
            println(options.line_height)
            for i in 0:2 { size := label.measure_styled(&styles,&control) or >>
                println(size.width)
                println(size.height) }
        }
    }
    << 0
}
fn main() int { << probe() or (err) { eprintln(err.msg())
    << 1 } }
`;
 const fast=await createRuntime(module),reference=await createRuntime(module,{fastIntrinsics:false});
 const result=fast.run(source); assert.equal(result.exit,0,result.stderr); assert.deepEqual(result,reference.run(source));
});

test('AOT style clones own their strings and state arrays and resolve every state like MIR',async()=>{
 const source=`@main
#playground
#ui/widgets
#ui/draw
#ui/layout
fn mutate(value string) string {
    $text := value
    text[0] = 90
    << text
}
fn validate(styles &widgets.Styles) int {
    << styles.validate() or (err) { println(err.msg())
        << 0 }
}
fn probe() int {
    $styles := playground.light_styles()
    styles.font.family = "Root"
    styles.button.font.family = "Button"
    styles.button.states = []widgets.StatePaint{}
    for i in 0:9 {
        $rule := widgets.state_paint(widgets.STATE_SELECTED)
        rule.fields = widgets.PAINT_BACKGROUND | widgets.PAINT_ICON_OPACITY
        rule.background = draw.rgba(i,20,30,40)
        rule.icon_opacity = f64(i) * 0.1
        styles.button.states.push(rule)
    }
    $copied := styles.clone()
    copied.font.family = mutate(copied.font.family)
    copied.button.font.family = mutate(copied.button.font.family)
    $rule := copied.button.states[0]
    rule.background = draw.rgb(240,0,0)
    copied.button.states[0] = rule
    copied.button.states.push(widgets.state_paint(widgets.STATE_FOCUSED))
    assert(styles.font.family == "Root")
    assert(styles.button.font.family == "Button")
    assert(styles.button.states.len == 9)
    assert(copied.button.states.len == 10)
    assert(styles.button.states[0].background.value() == draw.rgba(0,20,30,40).value())
    validate(&styles) or >>
    $bad := styles.clone()
    bad.font.weight = 99
    validate(&bad) or >>
    bad = styles.clone()
    bad.font.family = string_from_bytes([0])
    validate(&bad) or >>
    bad = styles.clone()
    bad.button.align_y = 2.0
    validate(&bad) or >>
    bad = styles.clone()
    bad.button.icon_placement = 4
    validate(&bad) or >>
    bad = styles.clone()
    $invalid := widgets.state_paint(128)
    bad.button.states.push(invalid)
    validate(&bad) or >>
    bad = styles.clone()
    bad.density = 0.25
    validate(&bad) or >>
    bad = styles.clone()
    bad.font.size = 200.0
    bad.text_scale = 4.0
    validate(&bad) or >>
    context := draw.default_context()
    $frame := context.new_frame(8192)
    frame.begin() or >>
    for state in 0:128 {
        resolved := copied.button.resolve(state)
        println(resolved.background.value())
        println(resolved.foreground.value())
        println(resolved.border.value())
        println(resolved.focus.value())
        println(resolved.icon_opacity)
    }
    for radius in [0.0,1.5,8.0,80.0] {
        copied.button.radius = radius
        widgets.paint_box_styled($&frame,&layout.Rect{x:1.25,y:2.75,width:80.5,height:39.25},&copied,&copied.button,widgets.STATE_FOCUSED) or >>
    }
    frame.present() or >>
    << 0
}
fn main() int { << probe() or (err) { eprintln(err.msg())
    << 1 } }
`;
 const fast=await createRuntime(module),reference=await createRuntime(module,{fastIntrinsics:false});
 const result=fast.run(source);assert.equal(result.exit,0,result.stderr);assert.deepEqual(result,reference.run(source));
});

test('AOT drawing preserves paths, RGBA clamping, text masking and catchable frame errors',async()=>{
 const source=`@main
#ui/draw
#ui/layout
#playground
fn inactive(frame $&draw.Frame) int {
    << frame.fill_rect(0.0,0.0,5.0,5.0,draw.rgb(0,0,0)) or (err) { println(err.msg())
        << 0 }
}
fn probe() int {
    context := draw.default_context()
    $frame := context.new_frame(8192)
    inactive($&frame) or >>
    frame.begin() or >>
    frame.clip_rect(1.25,2.5,90.75,80.0) or >>
    frame.fill_rect(1.5,2.25,3.5,4.75,draw.rgba(300,0-5,128,64)) or >>
    frame.stroke_rect(1.5,2.25,3.5,4.75,draw.rgb(5,6,7),1.25) or >>
    frame.line(1.5,2.25,3.5,4.75,draw.rgba(8,9,10,11),2.5) or >>
    $path := draw.new_path(400)
    path.move_to(1.25,2.5) or >>
    path.line_to(30.5,40.75) or >>
    path.cubic_to(20.0,10.5,30.25,40.0,50.0,60.5) or >>
    path.close() or >>
    frame.fill_path(&path,draw.rgb(1,2,3),draw.FILL_NONZERO) or >>
    $stroke := draw.stroke_options(1.75)
    stroke.cap = 1
    stroke.join = 2
    stroke.miter_limit = 5.5
    frame.stroke_path(&path,draw.rgba(3,2,1,50),&stroke) or >>
    label := context.layout_text(&"Latin 中文 😀\\tline\\nnext",&draw.text_options(14.5)) or >>
    frame.text_layout(&label,12.25,13.5,draw.rgb(4,5,6)) or >>
    masked := context.layout_masked_text(&"secret 中文 😀",&draw.text_options(14.0)) or >>
    frame.text_layout(&masked,12.0,40.0,draw.rgb(4,5,6)) or >>
    frame.present() or >>
    << 0
}
fn main() int { << probe() or (err) { eprintln(err.msg())
    << 1 } }
`;
 const fast=await createRuntime(module),reference=await createRuntime(module,{fastIntrinsics:false});
 const result=fast.run(source);assert.equal(result.exit,0,result.stderr);assert.doesNotMatch(result.ui.commands,/secret/);assert.deepEqual(result,reference.run(source));
});
