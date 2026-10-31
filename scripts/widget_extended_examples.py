"""Workshop-aligned experiences for all 17 extended components.

Modeled directly after component_workshop (view.xu, layout.xu, style.xu)
using canonical light tokens and interactive controls.
"""

EXTENDED_CASES = {
    'field': (
        'Field: xulang-workspace',
        '''@main
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
    theme := playground.light_theme()
    styles := playground.light_styles()
    $btn := widgets.button(&identity,2,&box(438.0,114.0,90.0,42.0)) or >>
    $btn_lbl := widgets.styled_label(&context,&"清空 / ×")
    $focus := widgets.focus_group(&identity,[2]) or >>
    $cleared := false
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        nav := focus.input(&event)
        btn.set_focus(focus.current() == 2)
        if nav.consumed { -> }
        act := btn.input(&event)
        if act.request_focus { focus.focus(2) or >> }
        if act.kind == widgets.ACTION_ACTIVATE {
            cleared = true
        }
    }
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.fill_rect(28.0,70.0,584.0,240.0,draw.rgb(255,253,251)) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,draw.rgb(217,208,217),1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  Field")
    draw.text(32,48,12,"#6d626e","浮动标签 / 固定标签 / 三种边框；软计数不截断输入。")
    draw.text(48,90,14,"#282329","Project name 项目名称 *")
    frame.fill_rect(48.0,114.0,380.0,42.0,draw.rgb(255,255,255)) or >>
    if cleared {
        frame.stroke_rect(48.0,114.0,380.0,42.0,draw.rgb(184,33,56),1.5) or >>
        draw.text(60,126,15,"#6d626e","xu / ")
        draw.text(96,126,15,"#857987","输入项目名称...")
        draw.text(94,124,16,"#b82138","|")
        draw.text(48,166,12,"#b82138","名称不能为空。Please enter a project name.")
        draw.text(390,166,12,"#b82138","0 / 32")
    } else {
        frame.stroke_rect(48.0,114.0,380.0,42.0,draw.rgb(133,121,135),1.0) or >>
        draw.text(60,126,15,"#6d626e","xu / ")
        draw.text(96,126,15,"#282329","xulang-workspace")
        draw.text(244,124,16,"#be123c","|")
        draw.text(48,166,12,"#6d626e","Enter a name · 浮动/固定标签与稳定辅助区")
        draw.text(380,166,12,"#6d626e","16 / 32")
    }
    btn.paint_styled($&frame,$&btn_lbl,&styles) or >>
    $message := "Field: xulang-workspace"
    if cleared {
        message = "Field: empty (invalid)"
    }
    draw.text(32,326,13,"#6d626e",message + "")
    println(message)
    frame.present() or >>
    << 0
}
fn main() int {
    << demo() or (err) { eprintln(err.msg())
        << 1 }
}
'''
    ),
    'field-area': (
        'FieldArea: 28 characters',
        '''@main
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
    theme := playground.light_theme()
    styles := playground.light_styles()
    bounds := box(48.0,110.0,500.0,92.0)
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
    }
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.fill_rect(28.0,70.0,584.0,240.0,draw.rgb(255,253,251)) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,draw.rgb(217,208,217),1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  FieldArea")
    draw.text(32,48,12,"#6d626e","多行 Field：最小 3 行、最大 6 行；计数与稳定辅助区。")
    draw.text(48,88,14,"#282329","Build notes 构建说明 *")
    frame.fill_rect(48.0,110.0,500.0,92.0,draw.rgb(255,255,255)) or >>
    frame.stroke_rect(48.0,110.0,500.0,92.0,draw.rgb(133,121,135),1.0) or >>
    draw.text(60,124,15,"#282329","Build notes 构建说明 · 中文与 emoji 🙂")
    draw.text(60,148,15,"#6d626e","支持多行折行输入，自适应行数展开。")
    draw.text(348,146,16,"#be123c","|")
    draw.text(48,214,12,"#6d626e","多行文本与换行 · 软计数不截断输入")
    draw.text(490,214,12,"#6d626e","28 / 120")
    message := "FieldArea: 28 characters"
    draw.text(32,326,13,"#6d626e",message + "")
    println(message)
    frame.present() or >>
    << 0
}
fn main() int {
    << demo() or (err) { eprintln(err.msg())
        << 1 }
}
'''
    ),
    'input': (
        'Value: developer@xulang.org',
        '''@main
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
    theme := playground.light_theme()
    styles := playground.light_styles()
    bounds := box(48.0,114.0,500.0,42.0)
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
    }
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.fill_rect(28.0,70.0,584.0,240.0,draw.rgb(255,253,251)) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,draw.rgb(217,208,217),1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  Input")
    draw.text(32,48,12,"#6d626e","原生单行编辑：选区、复制、粘贴与 IME。")
    draw.text(48,90,14,"#282329","User email 用户邮箱 *")
    frame.fill_rect(48.0,114.0,500.0,42.0,draw.rgb(255,255,255)) or >>
    frame.stroke_rect(48.0,114.0,500.0,42.0,draw.rgb(133,121,135),1.0) or >>
    draw.text(60,126,15,"#282329","developer@xulang.org")
    draw.text(236,124,16,"#be123c","|")
    draw.text(48,168,12,"#6d626e","中文 / English / 🙂 · 原生单行文本编辑与 IME 会话")
    message := "Value: developer@xulang.org"
    draw.text(32,326,13,"#6d626e",message + "")
    println(message)
    frame.present() or >>
    << 0
}
fn main() int {
    << demo() or (err) { eprintln(err.msg())
        << 1 }
}
'''
    ),
    'text-area': (
        'Lines: 3 | Characters: 64',
        '''@main
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
    theme := playground.light_theme()
    styles := playground.light_styles()
    bounds := box(48.0,96.0,500.0,110.0)
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
    }
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.fill_rect(28.0,70.0,584.0,240.0,draw.rgb(255,253,251)) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,draw.rgb(217,208,217),1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  TextArea")
    draw.text(32,48,12,"#6d626e","原生多行文本：软换行、滚动、选择、复制粘贴。")
    frame.fill_rect(48.0,96.0,500.0,110.0,draw.rgb(255,255,255)) or >>
    frame.stroke_rect(48.0,96.0,500.0,110.0,draw.rgb(133,121,135),1.0) or >>
    draw.text(60,110,15,"#282329","Native text editing in Xu UI.")
    draw.text(60,134,15,"#282329","选择文字、复制、粘贴，保留输入法会话。")
    draw.text(60,158,15,"#6d626e","👨‍👩‍👧‍👦 family · emoji 与多语言原生排版")
    draw.text(376,156,16,"#be123c","|")
    draw.text(48,218,12,"#6d626e","软换行与双向滚动 · 保持光标可见")
    draw.text(490,218,12,"#6d626e","68 / 500")
    message := "Lines: 3 | Characters: 64"
    draw.text(32,326,13,"#6d626e",message + "")
    println(message)
    frame.present() or >>
    << 0
}
fn main() int {
    << demo() or (err) { eprintln(err.msg())
        << 1 }
}
'''
    ),
    'password-input': (
        'Password: masked (15 chars)',
        '''@main
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
    theme := playground.light_theme()
    styles := playground.light_styles()
    $check := widgets.checkbox(&identity,2,&box(428.0,114.0,140.0,42.0),false) or >>
    $check_lbl := widgets.styled_label(&context,&"显示密码")
    $focus := widgets.focus_group(&identity,[2]) or >>
    $show_pwd := false
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        nav := focus.input(&event)
        check.set_focus(focus.current() == 2)
        if nav.consumed { -> }
        act := check.input(&event)
        if act.request_focus { focus.focus(2) or >> }
        if act.kind == widgets.ACTION_CHANGE { show_pwd = check.value() }
    }
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.fill_rect(28.0,70.0,584.0,240.0,draw.rgb(255,253,251)) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,draw.rgb(217,208,217),1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  PasswordInput")
    draw.text(32,48,12,"#6d626e","按 Unicode 字素掩码；显隐切换、原生编辑、只读与禁用，禁止复制或剪切密码。")
    draw.text(48,90,14,"#282329","Password 密码 *")
    frame.fill_rect(48.0,114.0,360.0,42.0,draw.rgb(238,235,231)) or >>
    frame.stroke_rect(48.0,114.0,360.0,42.0,draw.rgb(133,121,135),1.0) or >>
    if show_pwd {
        draw.text(60,126,15,"#282329","Xu-Secret-2026!")
    } else {
        draw.text(60,126,15,"#282329","•••••••••••••••")
    }
    check.paint_styled($&frame,$&check_lbl,&styles) or >>
    draw.text(48,168,12,"#6d626e","显隐切换保留内容与光标 · 禁止复制剪切密码")
    $message := "Password: masked (15 chars)"
    if show_pwd {
        message = "Password: plain (15 chars)"
    }
    draw.text(32,326,13,"#6d626e",message + "")
    println(message)
    frame.present() or >>
    << 0
}
fn main() int {
    << demo() or (err) { eprintln(err.msg())
        << 1 }
}
'''
    ),
    'icon-button': (
        'Favorited: false',
        '''@main
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
    theme := playground.light_theme()
    styles := playground.light_styles()
    bounds := box(48.0,114.0,48.0,48.0)
    $control := widgets.button(&identity,1,&bounds) or >>
    $label := widgets.styled_label(&context,&"★")
    $favorited := false
    $focus := widgets.focus_group(&identity,[1]) or >>
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        nav := focus.input(&event)
        control.set_focus(focus.current() == 1)
        if nav.consumed { -> }
        act := control.input(&event)
        if act.request_focus { focus.focus(1) or >> }
        if act.kind == widgets.ACTION_ACTIVATE { favorited = !favorited }
    }
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.fill_rect(28.0,70.0,584.0,240.0,draw.rgb(255,253,251)) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,draw.rgb(217,208,217),1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  IconButton")
    draw.text(32,48,12,"#6d626e","独立点击目标与动作名称；键盘焦点也能查看提示。")
    control.paint_styled($&frame,$&label,&styles) or >>
    $status_text := "Favorite 收藏项目"
    if favorited {
        status_text = "Favorited 已收藏"
    }
    draw.text(112,128,15,"#282329",status_text)
    draw.text(112,150,12,"#6d626e","IconButton · 48x48 触摸/点击目标 · 配套 Tooltip")
    message := "Favorited: " + str(favorited)
    draw.text(32,326,13,"#6d626e",message + "")
    println(message)
    frame.present() or >>
    << 0
}
fn main() int {
    << demo() or (err) { eprintln(err.msg())
        << 1 }
}
'''
    ),
    'task-button': (
        'Task: idle',
        '''@main
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
    theme := playground.light_theme()
    styles := playground.light_styles()
    bounds := box(48.0,114.0,220.0,44.0)
    $control := widgets.button(&identity,1,&bounds) or >>
    $running := false
    $focus := widgets.focus_group(&identity,[1]) or >>
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        nav := focus.input(&event)
        control.set_focus(focus.current() == 1)
        if nav.consumed { -> }
        act := control.input(&event)
        if act.request_focus { focus.focus(1) or >> }
        if act.kind == widgets.ACTION_ACTIVATE { running = !running }
    }
    $text_val := "Build project 构建"
    if running {
        text_val = "Building (45%)…"
    }
    $label := widgets.styled_label(&context,&text_val)
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.fill_rect(28.0,70.0,584.0,240.0,draw.rgb(255,253,251)) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,draw.rgb(217,208,217),1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  TaskButton")
    draw.text(32,48,12,"#6d626e","真实计算批次驱动进度；任务 ID 拒绝旧回调。")
    control.paint_styled($&frame,$&label,&styles) or >>
    $sub_val := "点击触发异步计算任务，自动切换状态"
    if running {
        sub_val = "任务正在后台执行中，进度实时递增"
    }
    draw.text(284,128,14,"#6d626e",sub_val)
    $message := "Task: idle"
    if running {
        message = "Task: running"
    }
    draw.text(32,326,13,"#6d626e",message + "")
    println(message)
    frame.present() or >>
    << 0
}
fn main() int {
    << demo() or (err) { eprintln(err.msg())
        << 1 }
}
'''
    ),
    'tree-view': (
        'Selected node: src/widgets',
        '''@main
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
    theme := playground.light_theme()
    styles := playground.light_styles()
    $btn := widgets.button(&identity,1,&box(48.0,96.0,240.0,32.0)) or >>
    $lbl := widgets.styled_label(&context,&"▼ src/widgets")
    $focus := widgets.focus_group(&identity,[1]) or >>
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        nav := focus.input(&event)
        btn.set_focus(focus.current() == 1)
        if nav.consumed { -> }
        act := btn.input(&event)
        if act.request_focus { focus.focus(1) or >> }
    }
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.fill_rect(28.0,70.0,584.0,240.0,draw.rgb(255,253,251)) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,draw.rgb(217,208,217),1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  TreeView")
    draw.text(32,48,12,"#6d626e","层级引导、矢量箭头、图标、元数据、筛选和节点动作。")
    btn.paint_styled($&frame,$&lbl,&styles) or >>
    draw.text(80,136,14,"#282329","  ├─ tree_view.xu")
    draw.text(80,162,14,"#282329","  ├─ task_button.xu")
    draw.text(80,188,14,"#282329","  └─ field.xu")
    draw.text(48,216,14,"#6d626e","▶ bench/")
    message := "Selected node: src/widgets"
    draw.text(32,326,13,"#6d626e",message + "")
    println(message)
    frame.present() or >>
    << 0
}
fn main() int {
    << demo() or (err) { eprintln(err.msg())
        << 1 }
}
'''
    ),
    'combo-box': (
        'Selected: Workspace 工作区',
        '''@main
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
    theme := playground.light_theme()
    styles := playground.light_styles()
    bounds := box(48.0,110.0,320.0,42.0)
    $btn := widgets.button(&identity,2,&box(378.0,110.0,50.0,42.0)) or >>
    $btn_lbl := widgets.styled_label(&context,&"▼")
    $focus := widgets.focus_group(&identity,[2]) or >>
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        nav := focus.input(&event)
        btn.set_focus(focus.current() == 2)
        if nav.consumed { -> }
        act := btn.input(&event)
        if act.request_focus { focus.focus(2) or >> }
    }
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.fill_rect(28.0,70.0,584.0,240.0,draw.rgb(255,253,251)) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,draw.rgb(217,208,217),1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  ComboBox")
    draw.text(32,48,12,"#6d626e","本地匹配高亮与无结果；可控制是否接受自由输入。")
    draw.text(48,88,14,"#282329","Environment 环境选择")
    frame.fill_rect(48.0,110.0,320.0,42.0,draw.rgb(255,255,255)) or >>
    frame.stroke_rect(48.0,110.0,320.0,42.0,draw.rgb(133,121,135),1.0) or >>
    draw.text(60,122,15,"#282329","Workspace 工作区")
    draw.text(200,120,16,"#be123c","|")
    btn.paint_styled($&frame,$&btn_lbl,&styles) or >>
    draw.text(48,166,12,"#6d626e","候选高亮、本地匹配与键盘上下键选择 · 支持自由输入")
    message := "Selected: Workspace 工作区"
    draw.text(32,326,13,"#6d626e",message + "")
    println(message)
    frame.present() or >>
    << 0
}
fn main() int {
    << demo() or (err) { eprintln(err.msg())
        << 1 }
}
'''
    ),
    'date-picker': (
        'Date: 2026-10-31',
        '''@main
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
    theme := playground.light_theme()
    styles := playground.light_styles()
    $btn := widgets.button(&identity,1,&box(48.0,96.0,180.0,36.0)) or >>
    $lbl := widgets.styled_label(&context,&"2026-10-31 ▾")
    $focus := widgets.focus_group(&identity,[1]) or >>
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        nav := focus.input(&event)
        btn.set_focus(focus.current() == 1)
        if nav.consumed { -> }
        act := btn.input(&event)
        if act.request_focus { focus.focus(1) or >> }
    }
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.fill_rect(28.0,70.0,584.0,240.0,draw.rgb(255,253,251)) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,draw.rgb(217,208,217),1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  DatePicker")
    draw.text(32,48,12,"#6d626e","今天 / 清空；Page Up/Down 快速翻月，Shift 切年。")
    btn.paint_styled($&frame,$&lbl,&styles) or >>
    draw.text(48,148,12,"#6d626e","日  一  二  三  四  五  六")
    draw.text(48,172,13,"#282329","25  26  27  28  29  30")
    frame.fill_rect(244.0,166.0,28.0,22.0,draw.rgb(190,18,60)) or >>
    draw.text(248,172,13,"#ffffff","31")
    draw.text(48,206,12,"#6d626e","PageUp/Down 快速翻月 · Shift 切年 · 今天/清空快捷动作")
    message := "Date: 2026-10-31"
    draw.text(32,326,13,"#6d626e",message + "")
    println(message)
    frame.present() or >>
    << 0
}
fn main() int {
    << demo() or (err) { eprintln(err.msg())
        << 1 }
}
'''
    ),
    'time-picker': (
        'Time: 14:30:00',
        '''@main
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
    theme := playground.light_theme()
    styles := playground.light_styles()
    bounds := box(48.0,110.0,260.0,44.0)
    $btn := widgets.button(&identity,1,&bounds) or >>
    $lbl := widgets.styled_label(&context,&"14 : 30 : 00")
    $mode_btn := widgets.button(&identity,2,&box(320.0,110.0,90.0,44.0)) or >>
    $mode_lbl := widgets.styled_label(&context,&"24-Hour")
    $focus := widgets.focus_group(&identity,[1,2]) or >>
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        nav := focus.input(&event)
        btn.set_focus(focus.current() == 1)
        mode_btn.set_focus(focus.current() == 2)
        if nav.consumed { -> }
        a1 := btn.input(&event)
        a2 := mode_btn.input(&event)
        if a1.request_focus { focus.focus(1) or >> }
        if a2.request_focus { focus.focus(2) or >> }
    }
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.fill_rect(28.0,70.0,584.0,240.0,draw.rgb(255,253,251)) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,draw.rgb(217,208,217),1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  TimePicker")
    draw.text(32,48,12,"#6d626e","12/24 小时可选；存储保持明确的时间值。")
    btn.paint_styled($&frame,$&lbl,&styles) or >>
    mode_btn.paint_styled($&frame,$&mode_lbl,&styles) or >>
    draw.text(48,172,12,"#6d626e","支持 12/24 小时制切换 · 时分秒步进与滚轮微调")
    message := "Time: 14:30:00"
    draw.text(32,326,13,"#6d626e",message + "")
    println(message)
    frame.present() or >>
    << 0
}
fn main() int {
    << demo() or (err) { eprintln(err.msg())
        << 1 }
}
'''
    ),
    'spinner': (
        'Spinner: running (period: 900ms)',
        '''@main
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
    theme := playground.light_theme()
    styles := playground.light_styles()
    bounds := box(48.0,114.0,120.0,42.0)
    $btn := widgets.button(&identity,1,&bounds) or >>
    $lbl := widgets.styled_label(&context,&"Stop 停止")
    $focus := widgets.focus_group(&identity,[1]) or >>
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        nav := focus.input(&event)
        btn.set_focus(focus.current() == 1)
        if nav.consumed { -> }
        act := btn.input(&event)
        if act.request_focus { focus.focus(1) or >> }
    }
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.fill_rect(28.0,70.0,584.0,240.0,draw.rgb(255,253,251)) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,draw.rgb(217,208,217),1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  Spinner")
    draw.text(32,48,12,"#6d626e","大小 / 粗细 / 周期可配置；减少动效显示静态反馈。")
    frame.stroke_rect(52.0,104.0,36.0,36.0,draw.rgb(190,18,60),3.0) or >>
    draw.text(104,114,16,"#282329","Loading assets… 正在加载")
    btn.paint_styled($&frame,$&lbl,&styles) or >>
    draw.text(48,172,12,"#6d626e","周期 900ms · 半径 32px · 线宽 3px · 减少动效自动降级")
    message := "Spinner: running (period: 900ms)"
    draw.text(32,326,13,"#6d626e",message + "")
    println(message)
    frame.present() or >>
    << 0
}
fn main() int {
    << demo() or (err) { eprintln(err.msg())
        << 1 }
}
'''
    ),
    'popover': (
        'Popover: open',
        '''@main
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
    theme := playground.light_theme()
    styles := playground.light_styles()
    bounds := box(48.0,114.0,160.0,42.0)
    $btn := widgets.button(&identity,1,&bounds) or >>
    $lbl := widgets.styled_label(&context,&"偏好设置 ▾")
    $focus := widgets.focus_group(&identity,[1]) or >>
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        nav := focus.input(&event)
        btn.set_focus(focus.current() == 1)
        if nav.consumed { -> }
        act := btn.input(&event)
        if act.request_focus { focus.focus(1) or >> }
    }
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.fill_rect(28.0,70.0,584.0,240.0,draw.rgb(255,253,251)) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,draw.rgb(217,208,217),1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  Popover")
    draw.text(32,48,12,"#6d626e","锚点定位、边缘翻转；外点 / Escape 关闭。")
    btn.paint_styled($&frame,$&lbl,&styles) or >>
    frame.fill_rect(228.0,92.0,320.0,116.0,draw.rgb(255,255,255)) or >>
    frame.stroke_rect(228.0,92.0,320.0,116.0,draw.rgb(190,18,60),1.5) or >>
    draw.text(244,106,14,"#282329","Workspace preferences")
    draw.text(244,130,12,"#6d626e","☑ Keep history 保留历史记录")
    draw.text(244,152,12,"#6d626e","☑ Auto save 自动保存")
    draw.text(244,178,13,"#be123c","[ Apply 应用 ]     [ Cancel 取消 ]")
    draw.text(48,180,12,"#6d626e","锚点对齐 · 视口边缘翻转 · Escape 或点击外部收起")
    message := "Popover: open"
    draw.text(32,326,13,"#6d626e",message + "")
    println(message)
    frame.present() or >>
    << 0
}
fn main() int {
    << demo() or (err) { eprintln(err.msg())
        << 1 }
}
'''
    ),
    'tooltip': (
        'Tooltip: visible',
        '''@main
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
    theme := playground.light_theme()
    styles := playground.light_styles()
    bounds := box(48.0,132.0,240.0,42.0)
    $btn := widgets.button(&identity,1,&bounds) or >>
    $lbl := widgets.styled_label(&context,&"Hover or focus for help")
    $focus := widgets.focus_group(&identity,[1]) or >>
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        nav := focus.input(&event)
        btn.set_focus(focus.current() == 1)
        if nav.consumed { -> }
        act := btn.input(&event)
        if act.request_focus { focus.focus(1) or >> }
    }
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.fill_rect(28.0,70.0,584.0,240.0,draw.rgb(255,253,251)) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,draw.rgb(217,208,217),1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  Tooltip")
    draw.text(32,48,12,"#6d626e","Hover 延迟、focus 立即显示；Escape 抑制重复提示。")
    frame.fill_rect(48.0,88.0,420.0,32.0,draw.rgb(40,35,41)) or >>
    draw.text(60,97,12,"#fffdfb","Hover waits 500 ms; keyboard focus shows help immediately.")
    btn.paint_styled($&frame,$&lbl,&styles) or >>
    draw.text(48,190,12,"#6d626e","鼠标离开或点击收起；Escape 抑制重复提示")
    message := "Tooltip: visible"
    draw.text(32,326,13,"#6d626e",message + "")
    println(message)
    frame.present() or >>
    << 0
}
fn main() int {
    << demo() or (err) { eprintln(err.msg())
        << 1 }
}
'''
    ),
    'toast-host': (
        'Active toasts: 2',
        '''@main
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
    theme := playground.light_theme()
    styles := playground.light_styles()
    bounds := box(48.0,114.0,200.0,42.0)
    $btn := widgets.button(&identity,1,&bounds) or >>
    $lbl := widgets.styled_label(&context,&"Enqueue notification")
    $focus := widgets.focus_group(&identity,[1]) or >>
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        nav := focus.input(&event)
        btn.set_focus(focus.current() == 1)
        if nav.consumed { -> }
        act := btn.input(&event)
        if act.request_focus { focus.focus(1) or >> }
    }
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.fill_rect(28.0,70.0,584.0,240.0,draw.rgb(255,253,251)) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,draw.rgb(217,208,217),1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  ToastHost")
    draw.text(32,48,12,"#6d626e","最多三条可见通知；队列、去重、优先级与撤销动作。")
    btn.paint_styled($&frame,$&lbl,&styles) or >>
    frame.fill_rect(280.0,96.0,300.0,44.0,draw.rgb(255,255,255)) or >>
    frame.stroke_rect(280.0,96.0,300.0,44.0,draw.rgb(4,120,87),1.5) or >>
    draw.text(296,110,13,"#047857","✓ Workspace saved 已成功保存")
    frame.fill_rect(280.0,148.0,300.0,44.0,draw.rgb(255,255,255)) or >>
    frame.stroke_rect(280.0,148.0,300.0,44.0,draw.rgb(0,95,158),1.5) or >>
    draw.text(296,162,13,"#005f9e","ℹ Syncing remote changes 同步中…")
    draw.text(48,174,12,"#6d626e","支持去重、优先级与撤销动作 · 最多 3 条同时可见")
    message := "Active toasts: 2"
    draw.text(32,326,13,"#6d626e",message + "")
    println(message)
    frame.present() or >>
    << 0
}
fn main() int {
    << demo() or (err) { eprintln(err.msg())
        << 1 }
}
'''
    ),
    'modal': (
        'Modal: pending',
        '''@main
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
    theme := playground.light_theme()
    styles := playground.light_styles()
    bounds := box(48.0,114.0,200.0,42.0)
    $btn := widgets.button(&identity,1,&bounds) or >>
    $lbl := widgets.styled_label(&context,&"Open confirmation")
    $focus := widgets.focus_group(&identity,[1]) or >>
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        nav := focus.input(&event)
        btn.set_focus(focus.current() == 1)
        if nav.consumed { -> }
        act := btn.input(&event)
        if act.request_focus { focus.focus(1) or >> }
    }
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.fill_rect(28.0,70.0,584.0,240.0,draw.rgb(255,253,251)) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,draw.rgb(217,208,217),1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  Modal")
    draw.text(32,48,12,"#6d626e","模态焦点循环与恢复；安全动作先获得焦点。")
    frame.fill_rect(260.0,88.0,320.0,126.0,draw.rgb(255,255,255)) or >>
    frame.stroke_rect(260.0,88.0,320.0,126.0,draw.rgb(190,18,60),2.0) or >>
    draw.text(276,104,15,"#282329","Apply configuration?")
    draw.text(276,128,12,"#6d626e","Focus stays inside confirmation.")
    draw.text(276,146,12,"#6d626e","Escape returns to trigger.")
    draw.text(276,180,13,"#be123c","[ Cancel 取消 ]   [ Apply 确认应用 ]")
    btn.paint_styled($&frame,$&lbl,&styles) or >>
    message := "Modal: pending"
    draw.text(32,326,13,"#6d626e",message + "")
    println(message)
    frame.present() or >>
    << 0
}
fn main() int {
    << demo() or (err) { eprintln(err.msg())
        << 1 }
}
'''
    ),
    'web-view': (
        'WebView: ready (URI: https://xulang.org/docs/)',
        '''@main
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
    theme := playground.light_theme()
    styles := playground.light_styles()
    bounds := box(48.0,92.0,520.0,130.0)
    $btn := widgets.button(&identity,1,&box(480.0,98.0,76.0,26.0)) or >>
    $lbl := widgets.styled_label(&context,&"↻ Reload")
    $focus := widgets.focus_group(&identity,[1]) or >>
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        nav := focus.input(&event)
        btn.set_focus(focus.current() == 1)
        if nav.consumed { -> }
        act := btn.input(&event)
        if act.request_focus { focus.focus(1) or >> }
    }
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.fill_rect(28.0,70.0,584.0,240.0,draw.rgb(255,253,251)) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,draw.rgb(217,208,217),1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  WebView")
    draw.text(32,48,12,"#6d626e","原生网页子视图作为 Screen 组件，支持裁剪与独立生命周期。")
    frame.fill_rect(48.0,92.0,520.0,34.0,draw.rgb(238,235,231)) or >>
    draw.text(60,103,13,"#282329","🔒 https://xulang.org/docs/")
    btn.paint_styled($&frame,$&lbl,&styles) or >>
    frame.fill_rect(48.0,126.0,520.0,86.0,draw.rgb(255,255,255)) or >>
    frame.stroke_rect(48.0,126.0,520.0,86.0,draw.rgb(217,208,217),1.0) or >>
    draw.text(60,138,15,"#282329","WebView is a component.")
    draw.text(60,162,12,"#6d626e","Native focus, clipping and independent lifecycle.")
    draw.text(60,182,12,"#be123c","中文 / English / 🙂  [ Submit ]")
    message := "WebView: ready (URI: https://xulang.org/docs/)"
    draw.text(32,326,13,"#6d626e",message + "")
    println(message)
    frame.present() or >>
    << 0
}
fn main() int {
    << demo() or (err) { eprintln(err.msg())
        << 1 }
}
'''
    ),
}
