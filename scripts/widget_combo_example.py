"""Bounded browser text editing with a real native Menu for ComboBox choices."""

EXPECTED = 'Selected: Workspace 工作区'
SOURCE = '''@main
#ui
#ui/draw
#ui/layout
#ui/widgets
#playground
#time

fn box(x f64,y f64,w f64,h f64) layout.Rect {
    << layout.Rect{x:x,y:y,width:w,height:h}
}
fn letter(key int,shift bool) string {
    if key < 32 || key > 126 { << "" }
    if key >= 65 && key <= 90 && !shift { << string_from_byte(key+32) }
    << string_from_byte(key)
}
fn lower(value int) int {
    if value >= 65 && value <= 90 { << value+32 }
    << value
}
fn matches(value &string,query &string) bool {
    if query.len == 0 { << true }
    if query.len > value.len { << false }
    for start in 0:value.len-query.len+1 {
        $same := true
        for i in 0:query.len {
            if lower(value[start+i]) != lower(query[i]) { same = false }
        }
        if same { << true }
    }
    << false
}
fn choices(options &[]string,query &string,selected int) []widgets.MenuItem {
    $items := []widgets.MenuItem{}
    for i in 0:options.len {
        if matches(&options[i],query) {
            $item := widgets.menu_item(i+1,options[i])
            item.kind = widgets.MENU_RADIO
            item.radio_group = 1
            item.checked = i == selected
            items.push(item)
        }
    }
    if items.len == 0 {
        $empty := widgets.menu_item(99,"No matches 无匹配项")
        empty.enabled = false
        items.push(empty)
    }
    << items
}
fn remove_last(value &string) string {
    if value.len == 0 { << "" }
    $end := value.len-1
    while end > 0 && (value[end] & 192) == 128 { end = end-1 }
    << value[0:end]
}
fn demo() int {
    identity := playground.canvas_identity()
    context := draw.default_context()
    styles := playground.light_styles()
    bounds := box(48.0,110.0,400.0,42.0)
    options := ["Workspace 工作区","History 历史","Output 输出"]
    initial := choices(&options,&"",0)
    $menu := widgets.menu(&context,&identity,1,&bounds,"",&initial,widgets.MENU_DROPDOWN,0) or >>
    menu.set_style(&styles.input) or >>
    menu.set_viewport(&box(28.0,70.0,584.0,240.0)) or >>
    $focus := widgets.focus_group(&identity,[1]) or >>
    $text := "Workspace 工作区"
    $selected := 0
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        if event.kind == ui.EV_POINTER_CANCEL { focus.clear() }
        navigation := focus.input(&event)
        menu.set_focus(focus.current() == 1)
        if navigation.consumed { -> }
        $changed := false
        $editing := false
        if event.kind == ui.EV_KEY_DOWN && focus.current() == 1 {
            if event.key == ui.KEY_BACKSPACE { text = remove_last(&text)
                changed = true
                editing = true
            } else if (event.modifiers & (ui.MOD_CONTROL | ui.MOD_META)) == 0 {
                ch := letter(event.key,(event.modifiers & ui.MOD_SHIFT) != 0)
                if ch.len > 0 && text.len < 64 { text = text+ch
                    changed = true
                    editing = true }
            }
        }
        if changed {
            selected = -1
            filtered := choices(&options,&text,selected)
            menu.set_items(&filtered) or >>
            menu.open_at(bounds.x,bounds.y,false) or >>
        } else if !editing {
            was_open := menu.is_open()
            action := menu.input(&event) or >>
            if action.request_focus { focus.focus(1) or >> }
            if (action.kind == widgets.ACTION_ACTIVATE || action.kind == widgets.ACTION_CHANGE) && action.value >= 1.0 && action.value <= 3.0 {
                selected = int(action.value)-1
                text = options[selected]
                all := choices(&options,&"",selected)
                menu.set_items(&all) or >>
            } else if !was_open && menu.is_open() {
                all := choices(&options,&"",selected)
                menu.set_items(&all) or >>
                menu.open_at(bounds.x,bounds.y,false) or >>
            }
        }
        if event.kind == ui.EV_POINTER_DOWN && !bounds.contains(event.x,event.y) && !menu.is_open() { focus.clear() }
        menu.set_focus(focus.current() == 1)
        _ := menu.tick(&styles,time.instant_from_ns(event.time_ns) or >>,true) or >>
    }
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.fill_rect(28.0,70.0,584.0,240.0,styles.input.palette.normal) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,styles.button.palette.border,1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  ComboBox")
    draw.text(32,48,12,"#6d626e","展开候选项；方向键、Enter 选择，Escape 关闭。")
    draw.text(48,86,14,"#282329","Environment 环境选择")
    menu.paint_styled($&frame,&styles) or >>
    $display := text+""
    if focus.current() == 1 { display = display+"│" }
    $label := widgets.styled_label(&context,&display)
    $field := styles.input.clone()
    field.padding = layout.Insets{left:0.0,top:0.0,right:0.0,bottom:0.0}
    field.align_x = 0.0
    field.align_y = 0.5
    content := box(bounds.x+12.0,bounds.y,bounds.width-56.0,bounds.height)
    $state := 0
    if focus.current() == 1 { state = widgets.STATE_FOCUSED }
    label.paint_text_styled($&frame,&content,&styles,&field,state) or >>
    draw.text(48,174,12,"#6d626e","输入基本字符筛选；中文选项可直接选择。")
    menu.paint_popup_styled($&frame,&styles) or >>
    message := "Selected: "+text
    draw.text(32,326,13,"#6d626e",message+"")
    println(message)
    frame.present() or >>
    << 0
}
fn main() int { << demo() or (err) { eprintln(err.msg())
    << 1 } }
'''
