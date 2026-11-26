"""Interactive browser compositions with explicit desktop capability boundaries."""

PREFIX = '''@main
#ui
#ui/draw
#ui/layout
#ui/widgets
#playground
#time

fn box(x f64,y f64,w f64,h f64) layout.Rect {
    << layout.Rect{x:x,y:y,width:w,height:h}
}
fn demo() int {
    identity := playground.canvas_identity()
    context := draw.default_context()
    styles := playground.light_styles()
'''


def experience(name, description, setup, events, paint, message, ids='[1]', navigation='', helpers=''):
    prefix = PREFIX.replace('fn demo() int {\n', helpers + 'fn demo() int {\n') if helpers else PREFIX
    return prefix + setup + f'''    $focus := widgets.focus_group(&identity,{ids}) >>>
    while true {{
        event := playground.next_input()
        if event.kind == 0 {{ <- }}
        if event.kind == ui.EV_POINTER_CANCEL {{ focus.clear() }}
        nav := focus.input(&event)
        btn.set_focus(focus.current() == 1)
''' + navigation + '''        if nav.consumed { -> }
        act := btn.input(&event)
        if act.request_focus { focus.focus(1) >>> }
''' + events + f'''    }}
    $frame := context.new_frame(16384)
    frame.begin() >>>
    frame.clear(styles.background) >>>
    frame.fill_rect(28.0,70.0,584.0,240.0,styles.input.palette.normal) >>>
    frame.stroke_rect(28.0,70.0,584.0,240.0,styles.button.palette.border,1.0) >>>
    draw.text(32,22,20,"#282329","XUUI  /  {name}")
    draw.text(32,48,12,"#6d626e","{description}")
''' + paint + '    message := ' + message + '''
    draw.text(32,326,13,"#6d626e",message+"")
    println(message)
    frame.present() >>>
    << 0
}
fn main() int { << demo() >>> (err) { eprintln(err.msg())
    << 1 } }
'''


TREE = '''@main
#ui
#ui/draw
#ui/layout
#ui/widgets
#playground

fn box(x f64,y f64,w f64,h f64) layout.Rect {
    << layout.Rect{x: x,y: y,width: w,height: h}
}

fn demo() int {
    identity := playground.canvas_identity()
    context := draw.default_context()
    styles := playground.light_styles()
    bounds := box(32.0,80.0,550.0,220.0)
    $control := widgets.tree_view(&context,&identity,1,&bounds) >>>
    root := control.add(-1,&"src/widgets") >>>
    control.add(root,&"tree_view.xu") >>>
    control.add(root,&"task_button.xu") >>>
    control.add(root,&"field.xu") >>>
    control.set_expanded(root,true) >>>
    control.set_selected(root) >>>
    control.apply_styles(&styles) >>>
    $focus := widgets.focus_group(&identity,[1]) >>>
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        if event.kind == ui.EV_POINTER_CANCEL { focus.clear() }
        nav := focus.input(&event)
        control.set_focus(focus.current() == 1)
        if nav.consumed { -> }
        act := control.input(&event)
        if act.request_focus { focus.focus(1) >>> }
    }
    $frame := context.new_frame(16384)
    frame.begin() >>>
    frame.clear(styles.background) >>>
    frame.fill_rect(28.0,70.0,584.0,240.0,styles.input.palette.normal) >>>
    frame.stroke_rect(28.0,70.0,584.0,240.0,styles.button.palette.border,1.0) >>>
    draw.text(32,22,20,"#282329","XUUI  /  TreeView")
    draw.text(32,48,12,"#6d626e","展开、折叠与节点选择")
    control.paint_styled($&frame,&styles) >>>
    sel := control.selected()
    name := control.text(sel)
    exp := control.is_expanded(sel)
    message := "Selected node: " + name + " | Expanded: " + str(exp)
    draw.text(32,326,13,"#6d626e",message+"")
    println(message)
    frame.present() >>>
    << 0
}

fn main() int {
    << demo() >>> (err) { eprintln(err.msg())
        << 1 }
}
'''


DATE_SETUP = '''    $btn := widgets.date_picker(&context,&identity,1,&box(48.0,88.0,220.0,44.0),time.date(2026,10,31,0,0,0,0)) >>>
    btn.set_clearable(true)
    btn.apply_styles(&styles) >>>
    $reset := widgets.button(&identity,2,&box(288.0,88.0,120.0,44.0)) >>>
    $clear := widgets.button(&identity,3,&box(424.0,88.0,120.0,44.0)) >>>
    $opened := false
'''
DATE_EVENTS = '''        if act.kind == widgets.ACTION_ACTIVATE {
            opened = !opened
            btn.set_open(opened)
        }
        if act.kind == widgets.ACTION_CHANGE {
            opened = btn.is_open()
        }
        reset_action := reset.input(&event)
        clear_action := clear.input(&event)
        if reset_action.request_focus { focus.focus(2) >>> }
        if clear_action.request_focus { focus.focus(3) >>> }
        if reset_action.kind == widgets.ACTION_ACTIVATE {
            btn.set_value(time.date(2026,10,31,0,0,0,0)) >>>
        }
        if clear_action.kind == widgets.ACTION_ACTIVATE {
            btn.clear() >>>
        }
        if opened && event.kind == ui.EV_KEY_DOWN && event.key == ui.KEY_ESCAPE {
            opened = false
            btn.set_open(false)
            focus.focus(1) >>>
        }
'''
DATE_PAINT = '''    $value := "Choose date 选择日期"
    if btn.has_value() { value = btn.display_text() >>> }
    btn.paint_styled($&frame,&styles) >>>
    $reset_label := widgets.styled_label(&context,&"Reset 重置")
    $clear_label := widgets.styled_label(&context,&"Clear 清空")
    reset.paint_styled($&frame,$&reset_label,&styles) >>>
    clear.paint_styled($&frame,$&clear_label,&styles) >>>
    draw.text(48,150,14,"#282329","选择日期：点击展开日历网格 · 支持月份切换与日期点选")
    draw.text(48,172,12,"#6d626e","顶部操作：Reset 恢复 2026-10-31 · Clear 清空选择 · Escape 关闭")
    if opened {
        btn.paint_popup_styled($&frame,&styles) >>>
    }
'''
DATE = experience('DatePicker', '标准日期拾取组件：支持日期展示、弹出日历网格选择与清空重置。', DATE_SETUP, DATE_EVENTS, DATE_PAINT,
                  '"Date: "+value', '[1,2,3]', '''        reset.set_focus(focus.current() == 2)
        clear.set_focus(focus.current() == 3)
''')


TIME_SETUP = '''    $btn := widgets.time_picker(&context,&identity,1,&box(48.0,110.0,260.0,44.0),time.date(2026,10,25,14,30,0,0)) >>>
    btn.set_show_seconds(true)
    btn.apply_styles(&styles) >>>
    $mode := widgets.button(&identity,2,&box(320.0,110.0,120.0,44.0)) >>>
    $twelve := false
'''
TIME_EVENTS = '''        mode_action := mode.input(&event)
        if mode_action.request_focus { focus.focus(2) >>> }
        if mode_action.kind == widgets.ACTION_ACTIVATE {
            twelve = !twelve
            btn.set_12_hour(twelve)
        }
'''
TIME_PAINT = '''    t := btn.value()
    h := t.hour()
    m := t.minute()
    s := t.second()
    $mm := str(m)
    if m < 10 { mm = "0"+mm }
    $hh := str(h)
    if h < 10 { hh = "0"+hh }
    $ss := str(s)
    if s < 10 { ss = "0"+ss }
    stored := hh+":"+mm+":"+ss
    $display := stored+""
    $mode_text := "24-Hour"
    if twelve {
        $h12 := h%12
        if h12 == 0 { h12 = 12 }
        $suffix := " AM"
        if h >= 12 { suffix = " PM" }
        display = str(h12)+":"+mm+":"+ss+suffix
        mode_text = "12-Hour"
    }
    $mode_label := widgets.styled_label(&context,&mode_text)
    btn.paint_styled($&frame,&styles) >>>
    mode.paint_styled($&frame,$&mode_label,&styles) >>>
    draw.text(48,180,14,"#282329",display)
    draw.text(48,202,12,"#6d626e","点击分段聚焦 · ↑ / ↓ 或右侧箭头调整 · 键盘直接输入数字")
'''
TIME = experience('TimePicker', '标准时间拾取组件：支持分秒滚轮调整、12/24小时制切换。', TIME_SETUP, TIME_EVENTS, TIME_PAINT,
                  '"Time: "+stored', '[1,2]', '        mode.set_focus(focus.current() == 2)\n')


TOOLTIP = experience('Tooltip', '点击或键盘聚焦显示提示；Escape 关闭。', '''    anchor := box(48.0,132.0,260.0,44.0)
    $btn := widgets.button(&identity,1,&anchor) >>>
    tip_size := layout.Size{width: 320.0, height: 32.0}
    viewport := box(0.0,0.0,640.0,360.0)
    $tip := widgets.tooltip(&identity,2,&anchor,&tip_size,&viewport) >>>
    $tip_label := widgets.styled_label(&context,&"Focus help · Escape closes this tooltip.")
    $shown := false
''', '''        if act.request_focus || act.kind == widgets.ACTION_ACTIVATE {
            shown = true
            tip.set_focus(true, time.zero_instant()) >>>
        }
        if event.kind == ui.EV_KEY_DOWN && event.key == ui.KEY_ESCAPE {
            shown = false
            tip.dismiss(time.zero_instant(), true) >>>
        }
        if event.kind == ui.EV_POINTER_DOWN && !box(48.0,132.0,260.0,44.0).contains(event.x,event.y) {
            shown = false
            tip.dismiss(time.zero_instant(), true) >>>
        }
        if event.kind == ui.EV_POINTER_CANCEL {
            shown = false
            tip.dismiss(time.zero_instant(), true) >>>
        }
''', '''    $label := widgets.styled_label(&context,&"Show help 查看提示")
    btn.paint_styled($&frame,$&label,&styles) >>>
    if shown {
        tip.paint_styled($&frame,$&tip_label,&styles) >>>
    }
    draw.text(48,196,12,"#6d626e","标准气泡提示组件 · 遵循 xu-ui-design")
    $state := "hidden"
    if shown { state = "visible" }
''', '"Tooltip: "+state', navigation='''        if nav.consumed {
            shown = focus.current() == 1
            if shown { tip.set_focus(true, time.zero_instant()) >>> }
            else { tip.dismiss(time.zero_instant(), true) >>> }
        }
''')


TOAST_HELPERS = '''fn remove_toast(host &widgets.ToastHost, index int) widgets.ToastHost {
    $next_host := widgets.toast_host()
    next_host.set_capacity(3) >>>
    count := host.pending_count()
    for j in 0:count {
        if j != index {
            rec := host.record_at(j)
            n := widgets.notice(&rec.text)
            next_host.enqueue(&n) >>>
        }
    }
    << next_host
}
'''

TOAST_SETUP = '''    $btn := widgets.button(&identity,1,&box(48.0,96.0,200.0,44.0)) >>>
    $clear := widgets.button(&identity,2,&box(48.0,152.0,200.0,44.0)) >>>
    $t0 := widgets.toast(&identity, 10, &box(280.0, 96.0, 300.0, 44.0)) >>>
    $t1 := widgets.toast(&identity, 11, &box(280.0, 152.0, 300.0, 44.0)) >>>
    $t2 := widgets.toast(&identity, 12, &box(280.0, 208.0, 300.0, 44.0)) >>>
    t0.show(time.zero_instant(), time.duration(0), true) >>>
    t1.show(time.zero_instant(), time.duration(0), true) >>>
    t2.show(time.zero_instant(), time.duration(0), true) >>>
    $host := widgets.toast_host()
    host.set_capacity(3) >>>
    init1 := widgets.notice(&"Workspace saved 已保存")
    init2 := widgets.notice(&"Syncing changes 同步中")
    host.enqueue(&init1)
    host.enqueue(&init2)
    $serial := 0
'''

TOAST_EVENTS = '''        clear_action := clear.input(&event)
        if clear_action.request_focus { focus.focus(2) >>> }
        if clear_action.kind == widgets.ACTION_ACTIVATE {
            host = widgets.toast_host()
            host.set_capacity(3) >>>
        }
        if act.kind == widgets.ACTION_ACTIVATE {
            if host.pending_count() >= 3 {
                host = remove_toast(&host, 0)
            }
            serial += 1
            value := "Notification 通知 " + str(serial)
            n := widgets.notice(&value)
            host.enqueue(&n)
            t0.show(time.zero_instant(), time.duration(0), true) >>>
            t1.show(time.zero_instant(), time.duration(0), true) >>>
            t2.show(time.zero_instant(), time.duration(0), true) >>>
        }
        count := host.pending_count()
        if count > 0 {
            a0 := t0.input(&event)
            if a0.kind == widgets.ACTION_CHANGE {
                host = remove_toast(&host, 0)
                t0.show(time.zero_instant(), time.duration(0), true) >>>
                t1.show(time.zero_instant(), time.duration(0), true) >>>
                t2.show(time.zero_instant(), time.duration(0), true) >>>
            }
        }
        if count > 1 {
            a1 := t1.input(&event)
            if a1.kind == widgets.ACTION_CHANGE {
                host = remove_toast(&host, 1)
                t0.show(time.zero_instant(), time.duration(0), true) >>>
                t1.show(time.zero_instant(), time.duration(0), true) >>>
                t2.show(time.zero_instant(), time.duration(0), true) >>>
            }
        }
        if count > 2 {
            a2 := t2.input(&event)
            if a2.kind == widgets.ACTION_CHANGE {
                host = remove_toast(&host, 2)
                t0.show(time.zero_instant(), time.duration(0), true) >>>
                t1.show(time.zero_instant(), time.duration(0), true) >>>
                t2.show(time.zero_instant(), time.duration(0), true) >>>
            }
        }
'''

TOAST_PAINT = '''    $label := widgets.styled_label(&context,&"Enqueue notification")
    $clear_label := widgets.styled_label(&context,&"Clear all 清空")
    btn.paint_styled($&frame,$&label,&styles) >>>
    clear.paint_styled($&frame,$&clear_label,&styles) >>>
    count := host.pending_count()
    if count > 0 {
        r0 := host.record_at(0)
        $tl0 := widgets.styled_label(&context, &r0.text)
        t0.paint_styled($&frame, $&tl0, &styles) >>>
    }
    if count > 1 {
        r1 := host.record_at(1)
        $tl1 := widgets.styled_label(&context, &r1.text)
        t1.paint_styled($&frame, $&tl1, &styles) >>>
    }
    if count > 2 {
        r2 := host.record_at(2)
        $tl2 := widgets.styled_label(&context, &r2.text)
        t2.paint_styled($&frame, $&tl2, &styles) >>>
    }
    draw.text(48,276,12,"#6d626e","标准消息通知宿主 · 遵循 xu-ui-design")
'''

TOAST = experience('ToastHost', '新增通知与清空；最多显示三条，满时替换最早一条。',
                   TOAST_SETUP, TOAST_EVENTS, TOAST_PAINT,
                   '"Active toasts: "+str(host.pending_count())',
                   '[1,2]', '        clear.set_focus(focus.current() == 2)\n',
                   helpers=TOAST_HELPERS)


WEB = experience('WebView', '静态子视图示意；原生网页加载、导航请在桌面 SDK 运行。', '''    $btn := widgets.button(&identity,1,&box(424.0,88.0,156.0,44.0)) >>>
    $refreshes := 0
''', '''        if act.kind == widgets.ACTION_ACTIVATE { refreshes += 1 }
''', '''    draw.text(48,102,14,"#282329","xulang.org/docs/ · Preview")
    $label := widgets.styled_label(&context,&"Refresh preview")
    btn.paint_styled($&frame,$&label,&styles) >>>
    frame.stroke_rect(48.0,144.0,532.0,112.0,styles.button.palette.border,1.0) >>>
    draw.text(64,160,16,"#282329","WebView content preview")
    draw.text(64,192,13,"#6d626e","Native webpage embedding requires the desktop SDK.")
    draw.text(64,224,13,"#6d626e","Preview refreshes: "+str(refreshes))
''', '"WebView preview refreshes: "+str(refreshes)')


STATE_CASES = {
    'tree-view': ('Selected node: src/widgets | Expanded: true', TREE),
    'date-picker': ('Date: 2026-10-31', DATE),
    'time-picker': ('Time: 14:30:00', TIME),
    'tooltip': ('Tooltip: hidden', TOOLTIP),
    'toast-host': ('Active toasts: 2', TOAST),
    'web-view': ('WebView preview refreshes: 0', WEB),
}
