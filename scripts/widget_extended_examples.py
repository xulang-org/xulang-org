"""Workshop-aligned experiences for all 17 extended components.

Modeled directly after component_workshop (view.xu, layout.xu, style.xu)
using canonical light tokens and interactive controls.
"""

from widget_state_examples import STATE_CASES
from widget_modal_example import EXPECTED as MODAL_EXPECTED, SOURCE as MODAL_SOURCE
from widget_combo_example import EXPECTED as COMBO_EXPECTED, SOURCE as COMBO_SOURCE
from widget_popover_example import EXPECTED as POPOVER_EXPECTED, SOURCE as POPOVER_SOURCE

EXTENDED_CASES = {
    **STATE_CASES,
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
fn char_from_key(key int, shift bool) string {
    if key == 32 { << " " }
    if key >= 65 && key <= 90 {
        lower := "abcdefghijklmnopqrstuvwxyz"
        upper := "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        idx := key - 65
        if !shift { << lower[idx:idx + 1] }
        << upper[idx:idx + 1]
    }
    if key >= 48 && key <= 57 {
        digits := "0123456789"
        symbols := ")!@#\\$%^&*("
        idx := key - 48
        if shift { << symbols[idx:idx + 1] }
        << digits[idx:idx + 1]
    }
    if key == 45 { if shift { << "_" } << "-" }
    if key == 61 { if shift { << "+" } << "=" }
    if key == 46 { if shift { << ">" } << "." }
    if key == 44 { if shift { << "<" } << "," }
    if key == 47 { if shift { << "?" } << "/" }
    if key == 58 || key == 59 { if shift { << ":" } << ";" }
    if key == 64 { << "@" }
    << ""
}
fn demo() int {
    context := draw.default_context()
    styles := playground.light_styles()
    bounds := box(48.0,110.0,440.0,48.0)
    clear_box := box(446.0,117.0,32.0,32.0)
    $text := "xulang-workspace"
    $focused := false
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        if event.kind == 77 { focused = false }
        if event.kind == 72 {
            px := event.x
            py := event.y
            if px >= clear_box.x && px <= clear_box.x + clear_box.width && py >= clear_box.y && py <= clear_box.y + clear_box.height {
                text = ""
                focused = true
            } else if px >= bounds.x && px <= bounds.x + bounds.width && py >= bounds.y && py <= bounds.y + bounds.height {
                focused = true
            } else {
                focused = false
            }
        }
        if event.kind == 78 {
            if event.key == 257 { focused = !focused }
            if focused {
                if event.key == 259 {
                    if text.len > 0 { text = remove_last(&text) }
                } else if event.key == 256 {
                    focused = false
                } else if text.len < 32 {
                    shift := (event.modifiers & 1) != 0
                    ch := char_from_key(event.key, shift)
                    if ch.len > 0 { text = text + ch }
                }
            }
        }
    }
    $caret := ""
    if focused { caret = "│" }
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.fill_rect(28.0,70.0,584.0,240.0,draw.rgb(255,253,251)) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,draw.rgb(217,208,217),1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  Field")
    draw.text(32,48,12,"#6d626e","单行字段预览：标签、清空和空值校验。")

    frame.fill_rect(bounds.x,bounds.y,bounds.width,bounds.height,draw.rgb(255,255,255)) or >>
    is_invalid := text.len == 0
    if is_invalid {
        frame.stroke_rect(bounds.x,bounds.y,bounds.width,bounds.height,draw.rgb(184,33,56),1.5) or >>
    } else if focused {
        frame.stroke_rect(bounds.x,bounds.y,bounds.width,bounds.height,styles.input.palette.focus,2.0) or >>
    } else {
        frame.stroke_rect(bounds.x,bounds.y,bounds.width,bounds.height,draw.rgb(133,121,135),1.0) or >>
    }

    bx := int(bounds.x)
    by := int(bounds.y)
    bw := int(bounds.width)
    bh := int(bounds.height)

    // Floating notch and label matching component_workshop
    frame.fill_rect(bounds.x + 12.0,bounds.y - 7.0,150.0,14.0,draw.rgb(255,253,251)) or >>
    if is_invalid {
        draw.text(bx + 16,by - 6,12,"#b82138","Project name 项目名称 *")
    } else if focused {
        draw.text(bx + 16,by - 6,12,"#282329","Project name 项目名称 *")
    } else {
        draw.text(bx + 16,by - 6,12,"#6d626e","Project name 项目名称 *")
    }

    // Inside box: prefix, value, caret, clear icon
    draw.text(bx + 16,by + 16,15,"#6d626e","xu / ")
    if text.len > 0 {
        draw.text(bx + 52,by + 16,15,"#282329",text + caret)
        cx := clear_box.x + 16.0
        cy := clear_box.y + 16.0
        frame.line(cx - 5.0,cy - 5.0,cx + 5.0,cy + 5.0,draw.rgb(133,121,135),1.5) or >>
        frame.line(cx + 5.0,cy - 5.0,cx - 5.0,cy + 5.0,draw.rgb(133,121,135),1.5) or >>
    } else {
        if focused { draw.text(bx + 52,by + 16,15,"#be123c",caret) }
        else { draw.text(bx + 52,by + 16,15,"#857987","输入项目名称...") }
    }

    // Helper text & counter below
    if is_invalid {
        draw.text(bx,by + bh + 8,12,"#b82138","名称不能为空。Please enter a project name.")
        draw.text(bx + bw - 50,by + bh + 8,12,"#b82138","0 / 32")
    } else {
        draw.text(bx,by + bh + 8,12,"#6d626e","Browser key input · Native IME requires the desktop SDK")
        draw.text(bx + bw - 50,by + bh + 8,12,"#6d626e",str(text.len) + " / 32")
    }

    $message := "Field: " + text
    if is_invalid { message = "Field: empty (invalid)" }
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
        'FieldArea: 30 characters',
        '''@main
#ui
#ui/draw
#ui/layout
#ui/widgets
#playground

fn box(x f64,y f64,w f64,h f64) layout.Rect {
    << layout.Rect{x: x,y: y,width: w,height: h}
}
fn char_from_key(key int, shift bool) string {
    if key == 32 { << " " }
    if key >= 65 && key <= 90 {
        lower := "abcdefghijklmnopqrstuvwxyz"
        upper := "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        idx := key - 65
        if !shift { << lower[idx:idx + 1] }
        << upper[idx:idx + 1]
    }
    if key >= 48 && key <= 57 {
        digits := "0123456789"
        symbols := ")!@#\\$%^&*("
        idx := key - 48
        if shift { << symbols[idx:idx + 1] }
        << digits[idx:idx + 1]
    }
    if key == 45 { if shift { << "_" } << "-" }
    if key == 61 { if shift { << "+" } << "=" }
    if key == 46 { if shift { << ">" } << "." }
    if key == 44 { if shift { << "<" } << "," }
    if key == 47 { if shift { << "?" } << "/" }
    if key == 58 || key == 59 { if shift { << ":" } << ";" }
    if key == 64 { << "@" }
    << ""
}
fn demo() int {
    context := draw.default_context()
    styles := playground.light_styles()
    bounds := box(48.0,110.0,500.0,92.0)
    $text := "Build notes 构建说明 · 中文与 emoji 🙂"
    $focused := false
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        if event.kind == 77 { focused = false }
        if event.kind == 72 {
            px := event.x
            py := event.y
            if px >= bounds.x && px <= bounds.x + bounds.width && py >= bounds.y && py <= bounds.y + bounds.height {
                focused = true
            } else {
                focused = false
            }
        }
        if event.kind == 78 {
            if event.key == 257 { focused = !focused }
            if focused {
                if event.key == 259 {
                    if text.len > 0 { text = remove_last(&text) }
                } else if event.key == 256 {
                    focused = false
                } else if codepoints(&text) < 120 {
                    shift := (event.modifiers & 1) != 0
                    ch := char_from_key(event.key, shift)
                    if ch.len > 0 { text = text + ch }
                }
            }
        }
    }
    $caret := ""
    if focused { caret = "│" }
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.fill_rect(28.0,70.0,584.0,240.0,draw.rgb(255,253,251)) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,draw.rgb(217,208,217),1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  FieldArea")
    draw.text(32,48,12,"#6d626e","浏览器字段预览：编辑首行末尾，计数与辅助区保持一致。")

    frame.fill_rect(bounds.x,bounds.y,bounds.width,bounds.height,draw.rgb(255,255,255)) or >>
    if focused {
        frame.stroke_rect(bounds.x,bounds.y,bounds.width,bounds.height,styles.input.palette.focus,2.0) or >>
    } else {
        frame.stroke_rect(bounds.x,bounds.y,bounds.width,bounds.height,draw.rgb(133,121,135),1.0) or >>
    }

    bx := int(bounds.x)
    by := int(bounds.y)
    bw := int(bounds.width)
    bh := int(bounds.height)

    // Floating notch and label
    frame.fill_rect(bounds.x + 12.0,bounds.y - 7.0,160.0,14.0,draw.rgb(255,253,251)) or >>
    if focused {
        draw.text(bx + 16,by - 6,12,"#282329","Build notes 构建说明 *")
    } else {
        draw.text(bx + 16,by - 6,12,"#6d626e","Build notes 构建说明 *")
    }

    draw.text(bx + 12,by + 14,15,"#282329",text + caret)
    draw.text(bx + 12,by + 40,14,"#6d626e","完整多行编辑请使用桌面 SDK。")

    draw.text(bx,by + bh + 8,12,"#6d626e","首行末尾输入 / 退格删除 · 按 Unicode 码点计数")
    draw.text(bx + bw - 60,by + bh + 8,12,"#6d626e",str(codepoints(&text)) + " / 120")

    chars := codepoints(&text)
    message := "FieldArea: " + str(chars) + " characters"
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
fn char_from_key(key int, shift bool) string {
    if key == 32 { << " " }
    if key >= 65 && key <= 90 {
        lower := "abcdefghijklmnopqrstuvwxyz"
        upper := "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        idx := key - 65
        if !shift { << lower[idx:idx + 1] }
        << upper[idx:idx + 1]
    }
    if key >= 48 && key <= 57 {
        digits := "0123456789"
        symbols := ")!@#\\$%^&*("
        idx := key - 48
        if shift { << symbols[idx:idx + 1] }
        << digits[idx:idx + 1]
    }
    if key == 45 { if shift { << "_" } << "-" }
    if key == 61 { if shift { << "+" } << "=" }
    if key == 46 { if shift { << ">" } << "." }
    if key == 44 { if shift { << "<" } << "," }
    if key == 47 { if shift { << "?" } << "/" }
    if key == 58 || key == 59 { if shift { << ":" } << ";" }
    if key == 64 { << "@" }
    << ""
}
fn demo() int {
    context := draw.default_context()
    styles := playground.light_styles()
    bounds := box(48.0,114.0,500.0,44.0)
    $text := "developer@xulang.org"
    $focused := false
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        if event.kind == 77 { focused = false }
        if event.kind == 72 {
            px := event.x
            py := event.y
            if px >= bounds.x && px <= bounds.x + bounds.width && py >= bounds.y && py <= bounds.y + bounds.height {
                focused = true
            } else {
                focused = false
            }
        }
        if event.kind == 78 {
            if event.key == 257 { focused = !focused }
            if focused {
                if event.key == 259 {
                    if text.len > 0 { text = remove_last(&text) }
                } else if event.key == 256 {
                    focused = false
                } else if text.len < 64 {
                    shift := (event.modifiers & 1) != 0
                    ch := char_from_key(event.key, shift)
                    if ch.len > 0 { text = text + ch }
                }
            }
        }
    }
    $caret := ""
    if focused { caret = "│" }
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.fill_rect(28.0,70.0,584.0,240.0,draw.rgb(255,253,251)) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,draw.rgb(217,208,217),1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  Input")
    draw.text(32,48,12,"#6d626e","浏览器输入预览：末尾输入、退格删除；Escape 离开。")

    bx := int(bounds.x)
    by := int(bounds.y)
    draw.text(bx,by - 24,14,"#282329","User email 用户邮箱 *")

    frame.fill_rect(bounds.x,bounds.y,bounds.width,bounds.height,draw.rgb(255,255,255)) or >>
    if focused {
        frame.stroke_rect(bounds.x,bounds.y,bounds.width,bounds.height,styles.input.palette.focus,2.0) or >>
    } else {
        frame.stroke_rect(bounds.x,bounds.y,bounds.width,bounds.height,draw.rgb(133,121,135),1.0) or >>
    }

    if text.len > 0 {
        draw.text(bx + 14,by + 13,15,"#282329",text + caret)
    } else {
        if focused { draw.text(bx + 14,by + 13,15,"#be123c",caret) }
        else { draw.text(bx + 14,by + 13,15,"#857987","you@domain.com") }
    }

    draw.text(bx,by + int(bounds.height) + 8,12,"#6d626e","Basic key input · Native IME requires the desktop SDK")
    message := "Value: " + text
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
        'Lines: 3 | Characters: 76',
        '''@main
#ui
#ui/draw
#ui/layout
#ui/widgets
#playground

fn box(x f64,y f64,w f64,h f64) layout.Rect {
    << layout.Rect{x: x,y: y,width: w,height: h}
}
fn char_from_key(key int, shift bool) string {
    if key == 32 { << " " }
    if key >= 65 && key <= 90 {
        lower := "abcdefghijklmnopqrstuvwxyz"
        upper := "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        idx := key - 65
        if !shift { << lower[idx:idx + 1] }
        << upper[idx:idx + 1]
    }
    if key >= 48 && key <= 57 {
        digits := "0123456789"
        symbols := ")!@#\\$%^&*("
        idx := key - 48
        if shift { << symbols[idx:idx + 1] }
        << digits[idx:idx + 1]
    }
    if key == 45 { if shift { << "_" } << "-" }
    if key == 61 { if shift { << "+" } << "=" }
    if key == 46 { if shift { << ">" } << "." }
    if key == 44 { if shift { << "<" } << "," }
    if key == 47 { if shift { << "?" } << "/" }
    if key == 58 || key == 59 { if shift { << ":" } << ";" }
    if key == 64 { << "@" }
    << ""
}
fn demo() int {
    context := draw.default_context()
    styles := playground.light_styles()
    bounds := box(48.0,96.0,500.0,110.0)
    $line1 := "Native text editing in Xu UI."
    $focused := false
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        if event.kind == 77 { focused = false }
        if event.kind == 72 {
            px := event.x
            py := event.y
            if px >= bounds.x && px <= bounds.x + bounds.width && py >= bounds.y && py <= bounds.y + bounds.height {
                focused = true
            } else {
                focused = false
            }
        }
        if event.kind == 78 {
            if event.key == 257 { focused = !focused }
            if focused {
                if event.key == 259 {
                    if line1.len > 0 { line1 = remove_last(&line1) }
                } else if event.key == 256 {
                    focused = false
                } else if line1.len < 100 {
                    shift := (event.modifiers & 1) != 0
                    ch := char_from_key(event.key, shift)
                    if ch.len > 0 { line1 = line1 + ch }
                }
            }
        }
    }
    $caret := ""
    if focused { caret = "│" }
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.fill_rect(28.0,70.0,584.0,240.0,draw.rgb(255,253,251)) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,draw.rgb(217,208,217),1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  TextArea")
    draw.text(32,48,12,"#6d626e","浏览器多行预览：编辑首行末尾；完整编辑请用桌面 SDK。")

    frame.fill_rect(bounds.x,bounds.y,bounds.width,bounds.height,draw.rgb(255,255,255)) or >>
    if focused {
        frame.stroke_rect(bounds.x,bounds.y,bounds.width,bounds.height,styles.input.palette.focus,2.0) or >>
    } else {
        frame.stroke_rect(bounds.x,bounds.y,bounds.width,bounds.height,draw.rgb(133,121,135),1.0) or >>
    }

    bx := int(bounds.x)
    by := int(bounds.y)
    bw := int(bounds.width)
    bh := int(bounds.height)

    draw.text(bx + 12,by + 14,15,"#282329",line1 + caret)
    draw.text(bx + 12,by + 38,15,"#282329","桌面 SDK 提供选区、剪贴板与输入法。")
    draw.text(bx + 12,by + 62,15,"#6d626e","👨‍👩‍👧‍👦 family · emoji 与多语言")

    total_chars := codepoints(&line1) + codepoints(&"桌面 SDK 提供选区、剪贴板与输入法。") + codepoints(&"👨‍👩‍👧‍👦 family · emoji 与多语言")
    draw.text(bx,by + bh + 8,12,"#6d626e","首行末尾输入 / 退格删除 · Escape 离开")
    draw.text(bx + bw - 60,by + bh + 8,12,"#6d626e",str(total_chars) + " / 500")

    message := "Lines: 3 | Characters: " + str(total_chars)
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
fn char_from_key(key int, shift bool) string {
    if key == 32 { << " " }
    if key >= 65 && key <= 90 {
        lower := "abcdefghijklmnopqrstuvwxyz"
        upper := "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        idx := key - 65
        if !shift { << lower[idx:idx + 1] }
        << upper[idx:idx + 1]
    }
    if key >= 48 && key <= 57 {
        digits := "0123456789"
        symbols := ")!@#\\$%^&*("
        idx := key - 48
        if shift { << symbols[idx:idx + 1] }
        << digits[idx:idx + 1]
    }
    if key == 45 { if shift { << "_" } << "-" }
    if key == 61 { if shift { << "+" } << "=" }
    if key == 46 { if shift { << ">" } << "." }
    if key == 44 { if shift { << "<" } << "," }
    if key == 47 { if shift { << "?" } << "/" }
    if key == 58 || key == 59 { if shift { << ":" } << ";" }
    if key == 64 { << "@" }
    << ""
}
fn demo() int {
    identity := playground.canvas_identity()
    context := draw.default_context()
    styles := playground.light_styles()
    bounds := box(48.0,114.0,360.0,42.0)
    $check := widgets.checkbox(&identity,2,&box(428.0,114.0,140.0,42.0),false) or >>
    $check_lbl := widgets.styled_label(&context,&"显示密码")
    $focus := widgets.focus_group(&identity,[1,2]) or >>
    $show_pwd := false
    $text := "Xu-Secret-2026!"
    $focused := false

    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        if event.kind == 77 { focused = false }
        if event.kind == 72 {
            px := event.x
            py := event.y
            if px >= bounds.x && px <= bounds.x + bounds.width && py >= bounds.y && py <= bounds.y + bounds.height {
                focused = true
                focus.focus(1) or >>
            } else {
                focused = false
            }
        }
        if event.kind == 78 {
            if focused {
                if event.key == 259 {
                    if text.len > 0 { text = remove_last(&text) }
                } else if event.key == 256 {
                    focused = false
                } else if text.len < 32 {
                    shift := (event.modifiers & 1) != 0
                    ch := char_from_key(event.key, shift)
                    if ch.len > 0 { text = text + ch }
                }
            }
        }
        if event.kind == 77 { focus.clear() }
        nav := focus.input(&event)
        focused = focus.current() == 1
        check.set_focus(focus.current() == 2)
        if nav.consumed { -> }
        act := check.input(&event)
        if act.request_focus { focus.focus(2) or >> }
        if act.kind == widgets.ACTION_CHANGE { show_pwd = check.value() }
    }

    $caret := ""
    if focused { caret = "│" }
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.fill_rect(28.0,70.0,584.0,240.0,draw.rgb(255,253,251)) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,draw.rgb(217,208,217),1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  PasswordInput")
    draw.text(32,48,12,"#6d626e","浏览器密码预览：基本键盘输入与显隐切换；完整编辑请用 SDK。")

    bx := int(bounds.x)
    by := int(bounds.y)
    draw.text(bx,by - 24,14,"#282329","Password 密码 *")

    frame.fill_rect(bounds.x,bounds.y,bounds.width,bounds.height,draw.rgb(255,255,255)) or >>
    if focused {
        frame.stroke_rect(bounds.x,bounds.y,bounds.width,bounds.height,styles.input.palette.focus,2.0) or >>
    } else {
        frame.stroke_rect(bounds.x,bounds.y,bounds.width,bounds.height,draw.rgb(133,121,135),1.0) or >>
    }

    if show_pwd {
        draw.text(bx + 12,by + 12,15,"#282329",text + caret)
    } else {
        $bullets := ""
        for i in 0:text.len { bullets = bullets + "•" }
        draw.text(bx + 12,by + 12,15,"#282329",bullets + caret)
    }

    check.paint_styled($&frame,$&check_lbl,&styles) or >>
    draw.text(bx,by + int(bounds.height) + 8,12,"#6d626e","显隐切换保留内容与光标 · 禁止复制剪切密码")
    $message := "Password: masked (" + str(text.len) + " chars)"
    if show_pwd {
        message = "Password: plain (" + str(text.len) + " chars)"
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
    draw.text(32,48,12,"#6d626e","独立点击目标与动作名称；点击或 Enter 切换收藏。")
    control.paint_styled($&frame,$&label,&styles) or >>
    $status_text := "Favorite 收藏项目"
    if favorited {
        status_text = "Favorited 已收藏"
    }
    draw.text(112,128,15,"#282329",status_text)
    draw.text(112,150,12,"#6d626e","IconButton · 48x48 触摸/点击目标")
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
    draw.text(32,48,12,"#6d626e","任务状态预览；点击切换空闲与运行状态。")
    control.paint_styled($&frame,$&label,&styles) or >>
    $sub_val := "点击预览运行状态，再次点击恢复空闲"
    if running {
        sub_val = "运行状态示意 · 桌面 SDK 提供异步任务"
    }
    draw.text(48,180,14,"#6d626e",sub_val)
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

    'combo-box': (COMBO_EXPECTED, COMBO_SOURCE),


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
    bounds := box(48.0,210.0,160.0,42.0)
    $btn := widgets.button(&identity,1,&bounds) or >>
    $lbl := widgets.styled_label(&context,&"Stop 停止")
    $focus := widgets.focus_group(&identity,[1]) or >>
    $running := true
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        nav := focus.input(&event)
        btn.set_focus(focus.current() == 1)
        if nav.consumed { -> }
        act := btn.input(&event)
        if act.request_focus { focus.focus(1) or >> }
        if act.kind == widgets.ACTION_ACTIVATE { running = !running }
    }
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.fill_rect(28.0,70.0,584.0,240.0,draw.rgb(255,253,251)) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,draw.rgb(217,208,217),1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  Spinner")
    draw.text(32,48,12,"#6d626e","浏览器减少动效预览；点击按钮停止或恢复反馈。")
    if running {
        frame.set_fill(draw.rgba(0,0,0,0)) or >>
        frame.set_stroke(draw.rgb(190,18,60),3.0) or >>
        frame.circle(70.0,122.0,18.0) or >>
    }
    if !running { lbl = widgets.styled_label(&context,&"Start 开始") }
    draw.text(104,114,16,"#282329","Loading assets… 正在加载")
    btn.paint_styled($&frame,$&lbl,&styles) or >>
    draw.text(48,172,12,"#6d626e","静态加载反馈 · 桌面 SDK 提供连续动画")
    $message := "Spinner: running (period: 900ms)"
    if !running { message = "Spinner: stopped" }
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
    'popover': (POPOVER_EXPECTED, POPOVER_SOURCE),


    'modal': (MODAL_EXPECTED, MODAL_SOURCE),

}
