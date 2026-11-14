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


def experience(name, description, setup, events, paint, message, ids='[1]', navigation=''):
    return PREFIX + setup + f'''    $focus := widgets.focus_group(&identity,{ids}) or >>
    while true {{
        event := playground.next_input()
        if event.kind == 0 {{ <- }}
        if event.kind == ui.EV_POINTER_CANCEL {{ focus.clear() }}
        nav := focus.input(&event)
        btn.set_focus(focus.current() == 1)
''' + navigation + '''        if nav.consumed { -> }
        act := btn.input(&event)
        if act.request_focus { focus.focus(1) or >> }
''' + events + f'''    }}
    $frame := context.new_frame(16384)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.fill_rect(28.0,70.0,584.0,240.0,styles.input.palette.normal) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,styles.button.palette.border,1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  {name}")
    draw.text(32,48,12,"#6d626e","{description}")
''' + paint + '    message := ' + message + '''
    draw.text(32,326,13,"#6d626e",message+"")
    println(message)
    frame.present() or >>
    << 0
}
fn main() int { << demo() or (err) { eprintln(err.msg())
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
    $control := widgets.tree_view(&context,&identity,1,&bounds) or >>
    root := control.add(-1,&"src/widgets") or >>
    control.add(root,&"tree_view.xu") or >>
    control.add(root,&"task_button.xu") or >>
    control.add(root,&"field.xu") or >>
    control.set_expanded(root,true) or >>
    control.set_selected(root) or >>
    control.apply_styles(&styles) or >>
    $focus := widgets.focus_group(&identity,[1]) or >>
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        if event.kind == ui.EV_POINTER_CANCEL { focus.clear() }
        nav := focus.input(&event)
        control.set_focus(focus.current() == 1)
        if nav.consumed { -> }
        act := control.input(&event)
        if act.request_focus { focus.focus(1) or >> }
    }
    $frame := context.new_frame(16384)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.fill_rect(28.0,70.0,584.0,240.0,styles.input.palette.normal) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,styles.button.palette.border,1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  TreeView")
    draw.text(32,48,12,"#6d626e","展开、折叠与节点选择")
    control.paint_styled($&frame,&styles) or >>
    sel := control.selected()
    name := control.text(sel)
    exp := control.is_expanded(sel)
    message := "Selected node: " + name + " | Expanded: " + str(exp)
    draw.text(32,326,13,"#6d626e",message+"")
    println(message)
    frame.present() or >>
    << 0
}

fn main() int {
    << demo() or (err) { eprintln(err.msg())
        << 1 }
}
'''


DATE_SETUP = '''    $btn := widgets.date_picker(&context,&identity,1,&box(48.0,88.0,220.0,44.0),time.date(2026,10,31,0,0,0,0)) or >>
    btn.set_clearable(true)
    btn.apply_styles(&styles) or >>
    $reset := widgets.button(&identity,9,&box(48.0,240.0,120.0,44.0)) or >>
    $clear := widgets.button(&identity,10,&box(180.0,240.0,120.0,44.0)) or >>
    $days := []widgets.Button{}
    for i in 0:7 { days.push(widgets.button(&identity,i+2,&box(48.0+f64(i)*56.0,180.0,48.0,44.0)) or >>) }
    $opened := false
    $day := 31
'''
DATE_EVENTS = '''        if act.kind == widgets.ACTION_ACTIVATE {
            opened = !opened
            btn.set_open(opened)
            if opened { focus = widgets.focus_group(&identity,[1,2,3,4,5,6,7,8,9,10]) or >> }
            else { focus = widgets.focus_group(&identity,[1,9,10]) or >> }
            focus.focus(1) or >>
        }
        reset_action := reset.input(&event)
        clear_action := clear.input(&event)
        if reset_action.request_focus { focus.focus(9) or >> }
        if clear_action.request_focus { focus.focus(10) or >> }
        if reset_action.kind == widgets.ACTION_ACTIVATE {
            day = 31
            btn.set_value(time.date(2026,10,31,0,0,0,0)) or >>
        }
        if clear_action.kind == widgets.ACTION_ACTIVATE {
            day = 0
            btn.clear() or >>
        }
        if opened {
            for i in 0:7 {
                item := $&days[i]
                item.set_focus(focus.current() == i+2)
                choice := item.input(&event)
                if choice.request_focus { focus.focus(i+2) or >> }
                if choice.kind == widgets.ACTION_ACTIVATE {
                    day = 25+i
                    btn.set_value(time.date(2026,10,day,0,0,0,0)) or >>
                }
            }
            if event.kind == ui.EV_KEY_DOWN && event.key == ui.KEY_ESCAPE {
                opened = false
                btn.set_open(false)
                focus = widgets.focus_group(&identity,[1,9,10]) or >>
                focus.focus(1) or >>
            }
        }
'''
DATE_PAINT = '''    $value := "Choose date 选择日期"
    if day > 0 { value = "2026-10-"+str(day) }
    btn.paint_styled($&frame,&styles) or >>
    if opened {
        btn.paint_popup_styled($&frame,&styles) or >>
        draw.text(48,148,14,"#6d626e","October 2026 · 25–31")
        for i in 0:7 {
            item := $&days[i]
            $label_day := widgets.styled_label(&context,&str(25+i))
            item.paint_styled($&frame,$&label_day,&styles) or >>
            if day == 25+i { frame.fill_rect(60.0+f64(i)*56.0,216.0,24.0,3.0,styles.button.palette.accent) or >> }
        }
    }
    $reset_label := widgets.styled_label(&context,&"Reset 重置")
    $clear_label := widgets.styled_label(&context,&"Clear 清空")
    reset.paint_styled($&frame,$&reset_label,&styles) or >>
    clear.paint_styled($&frame,$&clear_label,&styles) or >>
'''
DATE = experience('DatePicker', '标准日期拾取组件：支持日期展示、弹出日历网格选择与清空重置。', DATE_SETUP, DATE_EVENTS, DATE_PAINT,
                  '"Date: "+value', '[1,9,10]', '''        reset.set_focus(focus.current() == 9)
        clear.set_focus(focus.current() == 10)
        for i in 0:7 { item := $&days[i]
            item.set_focus(opened && focus.current() == i+2) }
''')


TIME = experience('TimePicker', '标准时间拾取组件：支持分秒滚轮调整、12/24小时制切换。', '''    $btn := widgets.time_picker(&context,&identity,1,&box(48.0,110.0,260.0,44.0),time.date(2026,10,25,14,30,0,0)) or >>
    btn.set_show_seconds(true)
    btn.apply_styles(&styles) or >>
    $mode := widgets.button(&identity,2,&box(320.0,110.0,120.0,44.0)) or >>
    $minutes := 870
    $twelve := false
''', '''        mode_action := mode.input(&event)
        if mode_action.request_focus { focus.focus(2) or >> }
        if mode_action.kind == widgets.ACTION_ACTIVATE {
            twelve = !twelve
            btn.set_12_hour(twelve)
        }
        if (event.kind == ui.EV_POINTER_DOWN && event.button == ui.BUTTON_LEFT && btn.bounds().contains(event.x,event.y)) || act.kind == widgets.ACTION_ACTIVATE {
            minutes = (minutes+1)%1440
            h := minutes/60
            m := minutes%60
            btn.set_value(time.date(2026,10,25,h,m,0,0)) or >>
        }
        if event.kind == ui.EV_KEY_DOWN && focus.current() == 1 {
            if event.key == ui.KEY_UP {
                minutes = (minutes+1)%1440
                h := minutes/60
                m := minutes%60
                btn.set_value(time.date(2026,10,25,h,m,0,0)) or >>
            }
            if event.key == ui.KEY_DOWN {
                minutes = (minutes+1439)%1440
                h := minutes/60
                m := minutes%60
                btn.set_value(time.date(2026,10,25,h,m,0,0)) or >>
            }
        }
''', '''    hour := minutes/60
    minute := minutes%60
    $mm := str(minute)
    if minute < 10 { mm = "0"+mm }
    $hh := str(hour)
    if hour < 10 { hh = "0"+hh }
    stored := hh+":"+mm+":00"
    $display := stored+""
    $mode_text := "24-Hour"
    if twelve { $h := hour%12
        if h == 0 { h = 12 }
        $suffix := " AM"
        if hour >= 12 { suffix = " PM" }
        display = str(h)+":"+mm+":00"+suffix
        mode_text = "12-Hour" }
    $mode_label := widgets.styled_label(&context,&mode_text)
    btn.paint_styled($&frame,&styles) or >>
    mode.paint_styled($&frame,$&mode_label,&styles) or >>
    draw.text(48,180,14,"#282329",display)
    draw.text(48,202,12,"#6d626e","点击 / Enter 增加一分钟 · ↑ / ↓ 调整 · 存储为 24 小时")
''', '"Time: "+stored', '[1,2]', '        mode.set_focus(focus.current() == 2)\n')


TOOLTIP = experience('Tooltip', '点击或键盘聚焦显示提示；Escape 关闭。', '''    anchor := box(48.0,132.0,260.0,44.0)
    $btn := widgets.button(&identity,1,&anchor) or >>
    tip_size := layout.Size{width: 320.0, height: 32.0}
    viewport := box(0.0,0.0,640.0,360.0)
    $tip := widgets.tooltip(&identity,2,&anchor,&tip_size,&viewport) or >>
    $tip_label := widgets.styled_label(&context,&"Focus help · Escape closes this tooltip.")
    $shown := false
''', '''        if act.request_focus || act.kind == widgets.ACTION_ACTIVATE {
            shown = true
            tip.set_focus(true, time.zero_instant()) or >>
        }
        if event.kind == ui.EV_KEY_DOWN && event.key == ui.KEY_ESCAPE {
            shown = false
            tip.dismiss(time.zero_instant(), true) or >>
        }
        if event.kind == ui.EV_POINTER_DOWN && !box(48.0,132.0,260.0,44.0).contains(event.x,event.y) {
            shown = false
            tip.dismiss(time.zero_instant(), true) or >>
        }
        if event.kind == ui.EV_POINTER_CANCEL {
            shown = false
            tip.dismiss(time.zero_instant(), true) or >>
        }
''', '''    $label := widgets.styled_label(&context,&"Show help 查看提示")
    btn.paint_styled($&frame,$&label,&styles) or >>
    if shown {
        tip.paint_styled($&frame,$&tip_label,&styles) or >>
    }
    draw.text(48,196,12,"#6d626e","标准气泡提示组件 · 遵循 xu-ui-design")
    $state := "hidden"
    if shown { state = "visible" }
''', '"Tooltip: "+state', navigation='''        if nav.consumed {
            shown = focus.current() == 1
            if shown { tip.set_focus(true, time.zero_instant()) or >> }
            else { tip.dismiss(time.zero_instant(), true) or >> }
        }
''')


TOAST = experience('ToastHost', '新增通知与清空；最多显示三条，满时替换最早一条。', '''    $btn := widgets.button(&identity,1,&box(48.0,96.0,200.0,44.0)) or >>
    $clear := widgets.button(&identity,2,&box(48.0,152.0,200.0,44.0)) or >>
    $host := widgets.toast_host()
    host.set_capacity(3) or >>
    init1 := widgets.notice(&"Workspace saved 已保存")
    init2 := widgets.notice(&"Syncing changes 同步中")
    host.enqueue(&init1)
    host.enqueue(&init2)
    $serial := 0
''', '''        clear_action := clear.input(&event)
        if clear_action.request_focus { focus.focus(2) or >> }
        if clear_action.kind == widgets.ACTION_ACTIVATE {
            host = widgets.toast_host()
            host.set_capacity(3) or >>
        }
        if act.kind == widgets.ACTION_ACTIVATE {
            serial += 1
            value := "Notification 通知 " + str(serial)
            n := widgets.notice(&value)
            host.enqueue(&n)
        }
''', '''    $label := widgets.styled_label(&context,&"Enqueue notification")
    $clear_label := widgets.styled_label(&context,&"Clear all 清空")
    btn.paint_styled($&frame,$&label,&styles) or >>
    clear.paint_styled($&frame,$&clear_label,&styles) or >>
    count := host.pending_count()
    for i in 0:count {
        y := 96.0 + f64(i) * 56.0
        rec := host.record_at(i)
        t_bounds := box(280.0, y, 300.0, 44.0)
        $t := widgets.toast(&identity, 10 + i, &t_bounds) or >>
        t.show(time.zero_instant(), time.duration(0), true) or >>
        $t_label := widgets.styled_label(&context, &rec.text)
        t.paint_styled($&frame, $&t_label, &styles) or >>
    }
    draw.text(48,276,12,"#6d626e","标准消息通知宿主 · 遵循 xu-ui-design")
''', '"Active toasts: "+str(host.pending_count())', '[1,2]', '        clear.set_focus(focus.current() == 2)\n')


WEB = experience('WebView', '静态子视图示意；原生网页加载、导航请在桌面 SDK 运行。', '''    $btn := widgets.button(&identity,1,&box(424.0,88.0,156.0,44.0)) or >>
    $refreshes := 0
''', '''        if act.kind == widgets.ACTION_ACTIVATE { refreshes += 1 }
''', '''    draw.text(48,102,14,"#282329","xulang.org/docs/ · Preview")
    $label := widgets.styled_label(&context,&"Refresh preview")
    btn.paint_styled($&frame,$&label,&styles) or >>
    frame.stroke_rect(48.0,144.0,532.0,112.0,styles.button.palette.border,1.0) or >>
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
