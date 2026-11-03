"""A native Modal with real child controls, focus trapping, and restoration."""

EXPECTED = 'Modal: closed\nResult: none\nFocus: 0'
SOURCE = '''@main
#ui
#ui/draw
#ui/layout
#ui/widgets
#playground
#time

fn box(x f64,y f64,w f64,h f64) layout.Rect {
    << layout.Rect{x: x,y: y,width: w,height: h}
}
fn caption(frame $&draw.Frame,context &draw.Context,text string,x f64,y f64,size f64,ink draw.Color) int {
    label := context.layout_text(&text,&draw.text_options(size)) or >>
    << frame.text_layout(&label,x,y,ink) or >>
}
fn demo() int {
    identity := playground.canvas_identity()
    context := draw.default_context()
    styles := playground.light_styles()
    $primary := styles.clone()
    primary.button.palette.normal = styles.button.palette.accent
    primary.button.palette.hovered = styles.button.palette.accent
    primary.button.palette.pressed = styles.button.palette.accent
    primary.button.palette.foreground = styles.button.palette.on_accent
    primary.button.palette.border = styles.button.palette.accent
    primary.button.palette.focus = styles.button.palette.on_accent
    primary.button.states = []widgets.StatePaint{}
    $trigger := widgets.button(&identity,1,&box(48.0,114.0,200.0,42.0)) or >>
    $trigger_label := widgets.styled_label(&context,&"Open confirmation")
    viewport := box(28.0,70.0,584.0,240.0)
    $dialog := widgets.modal(&identity,10,&box(148.0,96.0,344.0,188.0),&viewport) or >>
    dialog.set_focus_order(&[2,3]) or >>
    bounds := dialog.bounds()
    $cancel := widgets.button(&identity,2,&box(bounds.x+bounds.width-264.0,bounds.y+bounds.height-56.0,120.0,40.0)) or >>
    $apply := widgets.button(&identity,3,&box(bounds.x+bounds.width-136.0,bounds.y+bounds.height-56.0,96.0,40.0)) or >>
    $cancel_label := widgets.styled_label(&context,&"Cancel 取消")
    $apply_label := widgets.styled_label(&context,&"Apply 应用")
    $focus := widgets.focus_group(&identity,[1]) or >>
    $result := "none"
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        now := time.instant_from_ns(event.time_ns) or >>
        if dialog.blocks_input() {
            dispatch := dialog.input(&event) or >>
            cancel.set_focus(dialog.focused_id() == 2)
            apply.set_focus(dialog.focused_id() == 3)
            if !dispatch.consumed && dialog.allows_content(&event) {
                cancelled := cancel.input(&event)
                accepted := apply.input(&event)
                if cancelled.request_focus { dialog.set_content_focus(2) or >> }
                if accepted.request_focus { dialog.set_content_focus(3) or >> }
                if cancelled.kind == widgets.ACTION_ACTIVATE {
                    result = "cancelled"
                    dialog.close(now,true) or >>
                } else if accepted.kind == widgets.ACTION_ACTIVATE {
                    result = "applied"
                    dialog.close(now,true) or >>
                }
            }
            if !dialog.is_open() && result == "pending" { result = "cancelled" }
            restored := dialog.take_restore_focus()
            if restored > 0 { focus.focus(restored) or >> }
        } else {
            navigation := focus.input(&event)
            trigger.set_focus(focus.current() == 1)
            if !navigation.consumed {
                action := trigger.input(&event)
                if action.request_focus { focus.focus(1) or >> }
                if action.kind == widgets.ACTION_ACTIVATE {
                    dialog.open(now,true,1) or >>
                    result = "pending"
                }
            }
        }
        trigger.set_focus(!dialog.blocks_input() && focus.current() == 1)
        cancel.set_focus(dialog.is_open() && dialog.focused_id() == 2)
        apply.set_focus(dialog.is_open() && dialog.focused_id() == 3)
    }
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.fill_rect(viewport.x,viewport.y,viewport.width,viewport.height,styles.input.palette.normal) or >>
    frame.stroke_rect(viewport.x,viewport.y,viewport.width,viewport.height,styles.button.palette.border,1.0) or >>
    caption($&frame,&context,"XUUI  /  Modal",32.0,22.0,20.0,styles.button.palette.foreground) or >>
    caption($&frame,&context,"打开确认框；Tab 循环焦点，Escape 或取消返回。",32.0,48.0,12.0,styles.button.palette.muted) or >>
    trigger.paint_styled($&frame,$&trigger_label,&styles) or >>
    dialog.paint_styled($&frame,&styles) or >>
    if dialog.is_visible() {
        caption($&frame,&context,"Apply configuration?",bounds.x+16.0,bounds.y+20.0,16.0,styles.button.palette.foreground) or >>
        caption($&frame,&context,"焦点留在对话框内。",bounds.x+16.0,bounds.y+58.0,14.0,styles.button.palette.muted) or >>
        caption($&frame,&context,"取消或 Escape 保留当前设置。",bounds.x+16.0,bounds.y+82.0,13.0,styles.button.palette.muted) or >>
        cancel.paint_styled($&frame,$&cancel_label,&styles) or >>
        apply.paint_styled($&frame,$&apply_label,&primary) or >>
    }
    $state := "closed"
    if dialog.is_open() { state = "open" }
    $focused := focus.current()
    if dialog.is_open() { focused = dialog.focused_id() }
    message := "Modal: " + state
    caption($&frame,&context,message+" / "+result,32.0,326.0,13.0,styles.button.palette.muted) or >>
    println(message)
    println("Result: " + result)
    println("Focus: " + str(focused))
    frame.present() or >>
    << 0
}
fn main() int { << demo() or (err) { eprintln(err.msg())
    << 1 } }
'''
