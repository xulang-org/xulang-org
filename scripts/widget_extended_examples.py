"""Workshop-aligned experiences for all 17 extended components.

Modeled directly after component_workshop (view.xu, layout.xu, style.xu)
using canonical light tokens and interactive controls.
"""

from widget_state_examples import STATE_CASES
from widget_modal_example import EXPECTED as MODAL_EXPECTED, SOURCE as MODAL_SOURCE
from widget_combo_example import EXPECTED as COMBO_EXPECTED, SOURCE as COMBO_SOURCE
from widget_popover_example import EXPECTED as POPOVER_EXPECTED, SOURCE as POPOVER_SOURCE

EXTENDED_HELPERS = r'''fn box(x f64,y f64,w f64,h f64) layout.Rect {
    << layout.Rect{x: x,y: y,width: w,height: h}
}
fn mono_options(size f64) draw.TextOptions {
    $opts := draw.text_options(size)
    opts.family = "mono"
    << opts
}
fn utf8_next(s &string,pos int) int {
    if pos >= s.len { << s.len }
    b := s[pos] & 255
    $w := 1
    if b >= 240 { w = 4 }
    else if b >= 224 { w = 3 }
    else if b >= 194 { w = 2 }
    if pos + w > s.len { << s.len }
    << pos + w
}
fn utf8_prev(s &string,pos int) int {
    if pos <= 0 { << 0 }
    $p := pos - 1
    while p > 0 && (s[p] & 192) == 128 { p -= 1 }
    << p
}
fn snap_pos(s &string,pos int) int {
    if pos <= 0 { << 0 }
    if pos >= s.len { << s.len }
    $p := pos
    while p > 0 && (s[p] & 192) == 128 { p -= 1 }
    << p
}
fn count_cps(s &string) int {
    $n := 0
    for i in 0:s.len { if (s[i] & 192) != 128 { n += 1 } }
    << n
}
fn is_word_byte(b int) bool {
    if b >= 48 && b <= 57 { << true }
    if b >= 65 && b <= 90 { << true }
    if b >= 97 && b <= 122 { << true }
    if b == 95 || b >= 128 { << true }
    << false
}
fn prev_word_start(text &string,pos int) int {
    if pos <= 0 { << 0 }
    $p := pos
    while p > 0 {
        prev := utf8_prev(text,p)
        if is_word_byte(text[prev] & 255) { <- }
        p = prev
    }
    while p > 0 {
        prev := utf8_prev(text,p)
        if !is_word_byte(text[prev] & 255) { <- }
        p = prev
    }
    << p
}
fn next_word_end(text &string,pos int) int {
    if pos >= text.len { << text.len }
    $p := pos
    while p < text.len && !is_word_byte(text[p] & 255) { p = utf8_next(text,p) }
    while p < text.len && is_word_byte(text[p] & 255) { p = utf8_next(text,p) }
    << p
}
fn select_word_at(text &string,pos int) []int {
    if text.len == 0 { << [0,0] }
    $idx := pos
    if idx >= text.len { idx = utf8_prev(text,text.len) }
    $lo := idx
    $hi := utf8_next(text,idx)
    target := is_word_byte(text[idx] & 255)
    while lo > 0 {
        prev := utf8_prev(text,lo)
        if is_word_byte(text[prev] & 255) != target { <- }
        lo = prev
    }
    while hi < text.len {
        if is_word_byte(text[hi] & 255) != target { <- }
        hi = utf8_next(text,hi)
    }
    << [lo,hi]
}
fn char_from_key(key int,mods int,shift bool) string {
    if (mods & 16) != 0 {
        if key < 32 || (key >= 0xD800 && key <= 0xDFFF) || key > 0x10FFFF { << "" }
        if key < 0x80 { << string_from_byte(key) }
        if key < 0x800 { << string_from_bytes([0xC0 | (key >> 6),0x80 | (key & 0x3F)]) }
        if key < 0x10000 { << string_from_bytes([0xE0 | (key >> 12),0x80 | ((key >> 6) & 0x3F),0x80 | (key & 0x3F)]) }
        << string_from_bytes([0xF0 | (key >> 18),0x80 | ((key >> 12) & 0x3F),0x80 | ((key >> 6) & 0x3F),0x80 | (key & 0x3F)])
    }
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
        symbols := ")!@#\$%^&*("
        idx := key - 48
        if shift { << symbols[idx:idx + 1] }
        << digits[idx:idx + 1]
    }
    if key == 39 { if shift { << "\"" } << "'" }
    if key == 44 { if shift { << "<" } << "," }
    if key == 45 { if shift { << "_" } << "-" }
    if key == 46 { if shift { << ">" } << "." }
    if key == 47 { if shift { << "?" } << "/" }
    if key == 59 { if shift { << ":" } << ";" }
    if key == 61 { if shift { << "+" } << "=" }
    if key == 91 { if shift { << "{" } << "[" }
    if key == 92 { if shift { << "|" } << "\\" }
    if key == 93 { if shift { << "}" } << "]" }
    if key == 96 { if shift { << "~" } << "`" }
    if key >= 33 && key <= 126 { << string_from_byte(key) }
    << ""
}
fn measure_prefix(context &draw.Context,options &draw.TextOptions,text &string,pos int) f64 {
    if pos <= 0 { << 0.0 }
    $n := pos
    if n > text.len { n = text.len }
    n = snap_pos(text,n)
    if n <= 0 { << 0.0 }
    sub := text[0:n]
    shaped := context.layout_text(&sub,options) or >>
    << shaped.metrics.width
}
fn hit_pos(context &draw.Context,options &draw.TextOptions,text &string,rel_x f64) int {
    if rel_x <= 0.0 || text.len == 0 { << 0 }
    $prev_pos := 0
    $prev_w := 0.0
    while prev_pos < text.len {
        next_pos := utf8_next(text,prev_pos)
        w := measure_prefix(context,options,text,next_pos) or >>
        if rel_x < (prev_w + w) * 0.5 { << prev_pos }
        prev_pos = next_pos
        prev_w = w
    }
    << text.len
}
fn compute_scroll(context &draw.Context,options &draw.TextOptions,text &string,head int,view_w f64,cur_scroll f64) f64 {
    caret_px := measure_prefix(context,options,text,head) or >>
    $sx := cur_scroll
    if caret_px - sx > view_w - 6.0 { sx = caret_px - (view_w - 6.0) }
    if caret_px - sx < 0.0 { sx = caret_px }
    if sx < 0.0 { sx = 0.0 }
    << sx
}
fn handle_edit_key(event &ui.InputEvent,text $&string,anchor $&int,head $&int,clipboard $&string,clip_seq $&int,just_copied $&bool,focused $&bool,max_bytes int,max_cps int,allow_copy bool) int {
    mod_cmd := (event.modifiers & (ui.MOD_CONTROL | ui.MOD_META)) != 0
    mod_word := (event.modifiers & (ui.MOD_CONTROL | ui.MOD_ALT)) != 0
    mod_line := (event.modifiers & ui.MOD_META) != 0
    mod_shift := (event.modifiers & ui.MOD_SHIFT) != 0
    mod_text := (event.modifiers & 16) != 0
    $lo := *anchor
    $hi := *head
    if lo > hi {
        tmp := lo
        lo = hi
        hi = tmp
    }
    *just_copied = false
    if !mod_text && mod_cmd && (event.key == 65 || event.key == 97) {
        *anchor = 0
        *head = text.len
    } else if !mod_text && allow_copy && mod_cmd && (event.key == 67 || event.key == 99) {
        if hi > lo {
            *clipboard = (*text)[lo:hi]
            *clip_seq += 1
            *just_copied = true
        }
    } else if !mod_text && allow_copy && mod_cmd && (event.key == 88 || event.key == 120) {
        if hi > lo {
            *clipboard = (*text)[lo:hi]
            *clip_seq += 1
            *just_copied = true
            *text = (*text)[0:lo] + (*text)[hi:text.len]
            *anchor = lo
            *head = lo
        }
    } else if !mod_text && event.key == ui.KEY_BACKSPACE {
        if hi > lo {
            *text = (*text)[0:lo] + (*text)[hi:text.len]
            *anchor = lo
            *head = lo
        } else if *head > 0 && text.len > 0 {
            $from := utf8_prev(text,*head)
            if mod_line { from = 0 }
            else if mod_word { from = prev_word_start(text,*head) }
            *text = (*text)[0:from] + (*text)[*head:text.len]
            *head = from
            *anchor = from
        }
    } else if !mod_text && event.key == ui.KEY_DELETE {
        if hi > lo {
            *text = (*text)[0:lo] + (*text)[hi:text.len]
            *anchor = lo
            *head = lo
        } else if *head < text.len {
            $to := utf8_next(text,*head)
            if mod_line { to = text.len }
            else if mod_word { to = next_word_end(text,*head) }
            *text = (*text)[0:*head] + (*text)[to:text.len]
            *anchor = *head
        }
    } else if !mod_text && event.key == ui.KEY_ESCAPE {
        *focused = false
        *anchor = *head
    } else if !mod_text && event.key == ui.KEY_LEFT {
        if !mod_shift && hi > lo {
            *head = lo
            *anchor = lo
        } else {
            if mod_line { *head = 0 }
            else if mod_word { *head = prev_word_start(text,*head) }
            else if *head > 0 { *head = utf8_prev(text,*head) }
            if !mod_shift { *anchor = *head }
        }
    } else if !mod_text && event.key == ui.KEY_RIGHT {
        if !mod_shift && hi > lo {
            *head = hi
            *anchor = hi
        } else {
            if mod_line { *head = text.len }
            else if mod_word { *head = next_word_end(text,*head) }
            else if *head < text.len { *head = utf8_next(text,*head) }
            if !mod_shift { *anchor = *head }
        }
    } else if !mod_text && event.key == ui.KEY_HOME {
        *head = 0
        if !mod_shift { *anchor = *head }
    } else if !mod_text && event.key == ui.KEY_END {
        *head = text.len
        if !mod_shift { *anchor = *head }
    } else if mod_text || !mod_cmd {
        ch := char_from_key(event.key,event.modifiers,mod_shift)
        if ch.len > 0 {
            replaced := (*text)[0:lo] + ch + (*text)[hi:text.len]
            $within := replaced.len <= max_bytes
            if within && max_cps > 0 { within = count_cps(&replaced) <= max_cps }
            if within {
                *text = replaced
                *anchor = lo + ch.len
                *head = lo + ch.len
            }
        }
    }
    << 0
}
fn paint_edit_line(frame $&draw.Frame,context &draw.Context,options &draw.TextOptions,text &string,text_x f64,top f64,line_h f64,clip_x f64,clip_y f64,clip_w f64,clip_h f64,scroll_x f64,anchor int,head int,focused bool,ink draw.Color) int {
    $lo := anchor
    $hi := head
    if lo > hi {
        tmp := lo
        lo = hi
        hi = tmp
    }
    $sel_pad := (line_h - 24.0) * 0.5
    if sel_pad < 2.0 { sel_pad = 2.0 }
    $caret_pad := (line_h - 20.0) * 0.5
    if caret_pad < 2.0 { caret_pad = 2.0 }
    frame.push() or >>
    frame.clip_rect(clip_x,clip_y,clip_w,clip_h) or >>
    if focused && hi > lo {
        x0 := text_x - scroll_x + (measure_prefix(context,options,text,lo) or >>)
        x1 := text_x - scroll_x + (measure_prefix(context,options,text,hi) or >>)
        frame.fill_rect(x0,top + sel_pad,x1 - x0,line_h - sel_pad * 2.0,draw.rgba(225,29,72,56)) or >>
    }
    if text.len > 0 {
        shaped := context.layout_text(text,options) or >>
        frame.text_layout(&shaped,text_x - scroll_x,top + (line_h - shaped.metrics.height) * 0.5,ink) or >>
    }
    if focused {
        cx := text_x - scroll_x + (measure_prefix(context,options,text,head) or >>)
        frame.line(cx,top + caret_pad,cx,top + line_h - caret_pad,draw.rgb(225,29,72),1.5) or >>
    }
    frame.pop() or >>
    << 0
}
'''

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

''' + EXTENDED_HELPERS + r'''fn demo() int {
    context := draw.default_context()
    styles := playground.light_styles()
    edit_opts := mono_options(15.0)
    bounds := box(48.0,110.0,440.0,48.0)
    clear_box := box(446.0,117.0,32.0,32.0)
    text_x := bounds.x + 52.0
    view_w := clear_box.x - text_x - 6.0
    $text := "xulang-workspace"
    $focused := false
    $anchor := 0
    $head := 0
    $dragging := false
    $clipboard := ""
    $clip_seq := 0
    $just_copied := false
    $scroll_x := 0.0
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        if event.kind == 77 {
            focused = false
            dragging = false
        }
        if event.kind == 72 {
            px := event.x
            py := event.y
            just_copied = false
            if px >= clear_box.x && px <= clear_box.x + clear_box.width && py >= clear_box.y && py <= clear_box.y + clear_box.height {
                text = ""
                anchor = 0
                head = 0
                scroll_x = 0.0
                focused = true
                dragging = false
            } else if px >= bounds.x && px <= bounds.x + bounds.width && py >= bounds.y && py <= bounds.y + bounds.height {
                focused = true
                pos := hit_pos(&context,&edit_opts,&text,px - text_x + scroll_x) or >>
                if event.repeat >= 3 {
                    anchor = 0
                    head = text.len
                    dragging = false
                } else if event.repeat == 2 {
                    span := select_word_at(&text,pos)
                    anchor = span[0]
                    head = span[1]
                    dragging = false
                } else {
                    dragging = true
                    if (event.modifiers & ui.MOD_SHIFT) != 0 {
                        head = pos
                    } else {
                        anchor = pos
                        head = pos
                    }
                }
                scroll_x = compute_scroll(&context,&edit_opts,&text,head,view_w,scroll_x) or >>
            } else {
                focused = false
                dragging = false
            }
        } else if event.kind == 74 && dragging {
            head = hit_pos(&context,&edit_opts,&text,event.x - text_x + scroll_x) or >>
            scroll_x = compute_scroll(&context,&edit_opts,&text,head,view_w,scroll_x) or >>
        } else if event.kind == 73 {
            dragging = false
        }
        if event.kind == 78 {
            if event.key == 257 {
                focused = !focused
                just_copied = false
                if focused {
                    anchor = 0
                    head = text.len
                    scroll_x = compute_scroll(&context,&edit_opts,&text,head,view_w,scroll_x) or >>
                }
            } else if focused {
                handle_edit_key(&event,$&text,$&anchor,$&head,$&clipboard,$&clip_seq,$&just_copied,$&focused,96,32,true) or >>
                scroll_x = compute_scroll(&context,&edit_opts,&text,head,view_w,scroll_x) or >>
            }
        }
    }
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    if text.len > 0 {
        frame.cursor_rect(bounds.x,bounds.y,clear_box.x - bounds.x,bounds.height,"text") or >>
        frame.cursor_rect(clear_box.x,clear_box.y,clear_box.width,clear_box.height,"pointer") or >>
    } else {
        frame.cursor_rect(bounds.x,bounds.y,bounds.width,bounds.height,"text") or >>
    }
    if clip_seq > 0 { frame.copy_text(clip_seq,&clipboard) or >> }
    frame.fill_rect(28.0,70.0,584.0,240.0,draw.rgb(255,253,251)) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,draw.rgb(217,208,217),1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  Field")
    draw.text(32,48,12,"#6d626e","单行字段预览：支持光标定位、选区复制粘贴、词级删除及空值校验。")

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

    // Floating notch and label sized dynamically to label text
    notch_text := "Project name 项目名称 *"
    notch_lbl := context.layout_text(&notch_text,&draw.text_options(12.0)) or >>
    frame.fill_rect(bounds.x + 12.0,bounds.y - 7.0,notch_lbl.metrics.width + 8.0,14.0,draw.rgb(255,253,251)) or >>
    if is_invalid {
        draw.text(bx + 16,by - 6,12,"#b82138","Project name 项目名称 *")
    } else if focused {
        draw.text(bx + 16,by - 6,12,"#282329","Project name 项目名称 *")
    } else {
        draw.text(bx + 16,by - 6,12,"#6d626e","Project name 项目名称 *")
    }

    // Inside box: prefix, value, selection, caret, clear icon
    draw.text(bx + 16,by + 16,15,"#6d626e","xu / ")
    if text.len > 0 || focused {
        paint_edit_line($&frame,&context,&edit_opts,&text,text_x,bounds.y,bounds.height,text_x - 2.0,bounds.y + 2.0,view_w + 8.0,bounds.height - 4.0,scroll_x,anchor,head,focused,draw.rgb(40,35,41)) or >>
    } else {
        draw.text(bx + 52,by + 16,15,"#857987","输入项目名称...")
    }
    if text.len > 0 {
        cx := clear_box.x + 16.0
        cy := clear_box.y + 16.0
        frame.line(cx - 5.0,cy - 5.0,cx + 5.0,cy + 5.0,draw.rgb(133,121,135),1.5) or >>
        frame.line(cx + 5.0,cy - 5.0,cx - 5.0,cy + 5.0,draw.rgb(133,121,135),1.5) or >>
    }

    // Helper text & counter below
    if is_invalid {
        draw.text(bx,by + bh + 8,12,"#b82138","名称不能为空。Please enter a project name.")
        draw.text(bx + bw - 50,by + bh + 8,12,"#b82138","0 / 32")
    } else if just_copied {
        draw.text(bx,by + bh + 8,12,"#146747","Copied to clipboard · 已复制到剪贴板")
        draw.text(bx + bw - 50,by + bh + 8,12,"#6d626e",str(count_cps(&text)) + " / 32")
    } else {
        draw.text(bx,by + bh + 8,12,"#6d626e","Browser key input · Native IME requires the desktop SDK")
        draw.text(bx + bw - 50,by + bh + 8,12,"#6d626e",str(count_cps(&text)) + " / 32")
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

''' + EXTENDED_HELPERS + r'''fn demo() int {
    context := draw.default_context()
    styles := playground.light_styles()
    edit_opts := mono_options(15.0)
    bounds := box(48.0,110.0,500.0,92.0)
    text_x := bounds.x + 12.0
    view_w := bounds.width - 24.0
    $text := "Build notes 构建说明 · 中文与 emoji 🙂"
    $focused := false
    $anchor := 0
    $head := 0
    $dragging := false
    $clipboard := ""
    $clip_seq := 0
    $just_copied := false
    $scroll_x := 0.0
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        if event.kind == 77 {
            focused = false
            dragging = false
        }
        if event.kind == 72 {
            px := event.x
            py := event.y
            just_copied = false
            if px >= bounds.x && px <= bounds.x + bounds.width && py >= bounds.y && py <= bounds.y + bounds.height {
                focused = true
                pos := hit_pos(&context,&edit_opts,&text,px - text_x + scroll_x) or >>
                if event.repeat >= 3 {
                    anchor = 0
                    head = text.len
                    dragging = false
                } else if event.repeat == 2 {
                    span := select_word_at(&text,pos)
                    anchor = span[0]
                    head = span[1]
                    dragging = false
                } else {
                    dragging = true
                    if (event.modifiers & ui.MOD_SHIFT) != 0 {
                        head = pos
                    } else {
                        anchor = pos
                        head = pos
                    }
                }
                scroll_x = compute_scroll(&context,&edit_opts,&text,head,view_w,scroll_x) or >>
            } else {
                focused = false
                dragging = false
            }
        } else if event.kind == 74 && dragging {
            head = hit_pos(&context,&edit_opts,&text,event.x - text_x + scroll_x) or >>
            scroll_x = compute_scroll(&context,&edit_opts,&text,head,view_w,scroll_x) or >>
        } else if event.kind == 73 {
            dragging = false
        }
        if event.kind == 78 {
            if event.key == 257 {
                focused = !focused
                just_copied = false
                if focused {
                    anchor = 0
                    head = text.len
                    scroll_x = compute_scroll(&context,&edit_opts,&text,head,view_w,scroll_x) or >>
                }
            } else if focused {
                handle_edit_key(&event,$&text,$&anchor,$&head,$&clipboard,$&clip_seq,$&just_copied,$&focused,256,120,true) or >>
                scroll_x = compute_scroll(&context,&edit_opts,&text,head,view_w,scroll_x) or >>
            }
        }
    }
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.cursor_rect(bounds.x,bounds.y,bounds.width,bounds.height,"text") or >>
    if clip_seq > 0 { frame.copy_text(clip_seq,&clipboard) or >> }
    frame.fill_rect(28.0,70.0,584.0,240.0,draw.rgb(255,253,251)) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,draw.rgb(217,208,217),1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  FieldArea")
    draw.text(32,48,12,"#6d626e","浏览器字段预览：支持选区拖拽、复制粘贴、词级删除及 Unicode 计数。")

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

    // Floating notch and label sized dynamically to label text
    notch_text := "Build notes 构建说明 *"
    notch_lbl := context.layout_text(&notch_text,&draw.text_options(12.0)) or >>
    frame.fill_rect(bounds.x + 12.0,bounds.y - 7.0,notch_lbl.metrics.width + 8.0,14.0,draw.rgb(255,253,251)) or >>
    if focused {
        draw.text(bx + 16,by - 6,12,"#282329","Build notes 构建说明 *")
    } else {
        draw.text(bx + 16,by - 6,12,"#6d626e","Build notes 构建说明 *")
    }

    paint_edit_line($&frame,&context,&edit_opts,&text,text_x,bounds.y + 12.0,24.0,bounds.x + 2.0,bounds.y + 8.0,bounds.width - 4.0,bounds.height - 12.0,scroll_x,anchor,head,focused,draw.rgb(40,35,41)) or >>
    draw.text(bx + 12,by + 42,14,"#6d626e","完整多行编辑请使用桌面 SDK。")

    if just_copied {
        draw.text(bx,by + bh + 8,12,"#146747","Copied to clipboard · 已复制到剪贴板")
    } else {
        draw.text(bx,by + bh + 8,12,"#6d626e","首行支持光标准确定位 / 退格删词 · 按 Unicode 码点计数")
    }
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

''' + EXTENDED_HELPERS + r'''fn demo() int {
    context := draw.default_context()
    styles := playground.light_styles()
    edit_opts := mono_options(15.0)
    bounds := box(48.0,114.0,500.0,44.0)
    text_x := bounds.x + 14.0
    view_w := bounds.width - 28.0
    $text := "developer@xulang.org"
    $focused := false
    $anchor := 0
    $head := 0
    $dragging := false
    $clipboard := ""
    $clip_seq := 0
    $just_copied := false
    $scroll_x := 0.0
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        if event.kind == 77 {
            focused = false
            dragging = false
        }
        if event.kind == 72 {
            px := event.x
            py := event.y
            just_copied = false
            if px >= bounds.x && px <= bounds.x + bounds.width && py >= bounds.y && py <= bounds.y + bounds.height {
                focused = true
                pos := hit_pos(&context,&edit_opts,&text,px - text_x + scroll_x) or >>
                if event.repeat >= 3 {
                    anchor = 0
                    head = text.len
                    dragging = false
                } else if event.repeat == 2 {
                    span := select_word_at(&text,pos)
                    anchor = span[0]
                    head = span[1]
                    dragging = false
                } else {
                    dragging = true
                    if (event.modifiers & ui.MOD_SHIFT) != 0 {
                        head = pos
                    } else {
                        anchor = pos
                        head = pos
                    }
                }
                scroll_x = compute_scroll(&context,&edit_opts,&text,head,view_w,scroll_x) or >>
            } else {
                focused = false
                dragging = false
            }
        } else if event.kind == 74 && dragging {
            head = hit_pos(&context,&edit_opts,&text,event.x - text_x + scroll_x) or >>
            scroll_x = compute_scroll(&context,&edit_opts,&text,head,view_w,scroll_x) or >>
        } else if event.kind == 73 {
            dragging = false
        }
        if event.kind == 78 {
            if event.key == 257 {
                focused = !focused
                just_copied = false
                if focused {
                    anchor = 0
                    head = text.len
                    scroll_x = compute_scroll(&context,&edit_opts,&text,head,view_w,scroll_x) or >>
                }
            } else if focused {
                handle_edit_key(&event,$&text,$&anchor,$&head,$&clipboard,$&clip_seq,$&just_copied,$&focused,96,0,true) or >>
                scroll_x = compute_scroll(&context,&edit_opts,&text,head,view_w,scroll_x) or >>
            }
        }
    }
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.cursor_rect(bounds.x,bounds.y,bounds.width,bounds.height,"text") or >>
    if clip_seq > 0 { frame.copy_text(clip_seq,&clipboard) or >> }
    frame.fill_rect(28.0,70.0,584.0,240.0,draw.rgb(255,253,251)) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,draw.rgb(217,208,217),1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  Input")
    draw.text(32,48,12,"#6d626e","浏览器输入预览：支持拖拽选中、双击选词、Ctrl/Cmd+A/C/X/V 及退格删词。")

    bx := int(bounds.x)
    by := int(bounds.y)
    draw.text(bx,by - 24,14,"#282329","User email 用户邮箱 *")

    frame.fill_rect(bounds.x,bounds.y,bounds.width,bounds.height,draw.rgb(255,255,255)) or >>
    if focused {
        frame.stroke_rect(bounds.x,bounds.y,bounds.width,bounds.height,styles.input.palette.focus,2.0) or >>
    } else {
        frame.stroke_rect(bounds.x,bounds.y,bounds.width,bounds.height,draw.rgb(133,121,135),1.0) or >>
    }

    if text.len > 0 || focused {
        paint_edit_line($&frame,&context,&edit_opts,&text,text_x,bounds.y,bounds.height,bounds.x + 2.0,bounds.y + 2.0,bounds.width - 4.0,bounds.height - 4.0,scroll_x,anchor,head,focused,draw.rgb(40,35,41)) or >>
    } else {
        draw.text(bx + 14,by + 13,15,"#857987","you@domain.com")
    }

    if just_copied {
        draw.text(bx,by + int(bounds.height) + 8,12,"#146747","Copied to clipboard · 已复制到剪贴板")
    } else {
        draw.text(bx,by + int(bounds.height) + 8,12,"#6d626e","Basic key input · Native IME requires the desktop SDK")
    }
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

''' + EXTENDED_HELPERS + r'''fn demo() int {
    context := draw.default_context()
    styles := playground.light_styles()
    edit_opts := mono_options(15.0)
    bounds := box(48.0,96.0,500.0,110.0)
    text_x := bounds.x + 12.0
    view_w := bounds.width - 24.0
    $line1 := "Native text editing in Xu UI."
    $focused := false
    $anchor := 0
    $head := 0
    $dragging := false
    $clipboard := ""
    $clip_seq := 0
    $just_copied := false
    $scroll_x := 0.0
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        if event.kind == 77 {
            focused = false
            dragging = false
        }
        if event.kind == 72 {
            px := event.x
            py := event.y
            just_copied = false
            if px >= bounds.x && px <= bounds.x + bounds.width && py >= bounds.y && py <= bounds.y + bounds.height {
                focused = true
                pos := hit_pos(&context,&edit_opts,&line1,px - text_x + scroll_x) or >>
                if event.repeat >= 3 {
                    anchor = 0
                    head = line1.len
                    dragging = false
                } else if event.repeat == 2 {
                    span := select_word_at(&line1,pos)
                    anchor = span[0]
                    head = span[1]
                    dragging = false
                } else {
                    dragging = true
                    if (event.modifiers & ui.MOD_SHIFT) != 0 {
                        head = pos
                    } else {
                        anchor = pos
                        head = pos
                    }
                }
                scroll_x = compute_scroll(&context,&edit_opts,&line1,head,view_w,scroll_x) or >>
            } else {
                focused = false
                dragging = false
            }
        } else if event.kind == 74 && dragging {
            head = hit_pos(&context,&edit_opts,&line1,event.x - text_x + scroll_x) or >>
            scroll_x = compute_scroll(&context,&edit_opts,&line1,head,view_w,scroll_x) or >>
        } else if event.kind == 73 {
            dragging = false
        }
        if event.kind == 78 {
            if event.key == 257 {
                focused = !focused
                just_copied = false
                if focused {
                    anchor = 0
                    head = line1.len
                    scroll_x = compute_scroll(&context,&edit_opts,&line1,head,view_w,scroll_x) or >>
                }
            } else if focused {
                handle_edit_key(&event,$&line1,$&anchor,$&head,$&clipboard,$&clip_seq,$&just_copied,$&focused,200,0,true) or >>
                scroll_x = compute_scroll(&context,&edit_opts,&line1,head,view_w,scroll_x) or >>
            }
        }
    }
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.cursor_rect(bounds.x,bounds.y,bounds.width,bounds.height,"text") or >>
    if clip_seq > 0 { frame.copy_text(clip_seq,&clipboard) or >> }
    frame.fill_rect(28.0,70.0,584.0,240.0,draw.rgb(255,253,251)) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,draw.rgb(217,208,217),1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  TextArea")
    draw.text(32,48,12,"#6d626e","浏览器多行预览：首行支持拖拽选中、复制粘贴与光标同步；完整编辑请用桌面 SDK。")

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

    paint_edit_line($&frame,&context,&edit_opts,&line1,text_x,bounds.y + 12.0,24.0,bounds.x + 2.0,bounds.y + 6.0,bounds.width - 4.0,28.0,scroll_x,anchor,head,focused,draw.rgb(40,35,41)) or >>
    draw.text(bx + 12,by + 40,15,"#282329","桌面 SDK 提供选区、剪贴板与输入法。")
    draw.text(bx + 12,by + 64,15,"#6d626e","👨‍👩‍👧‍👦 family · emoji 与多语言")

    total_chars := codepoints(&line1) + codepoints(&"桌面 SDK 提供选区、剪贴板与输入法。") + codepoints(&"👨‍👩‍👧‍👦 family · emoji 与多语言")
    if just_copied {
        draw.text(bx,by + bh + 8,12,"#146747","Copied to clipboard · 已复制到剪贴板")
    } else {
        draw.text(bx,by + bh + 8,12,"#6d626e","首行支持光标准确定位 / 退格删词 · Escape 离开")
    }
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

''' + EXTENDED_HELPERS + r'''fn mask_bullets(text &string) string {
    $out := ""
    n := count_cps(text)
    for i in 0:n { out = out + "•" }
    << out
}
fn byte_to_cp_index(text &string,bpos int) int {
    $n := 0
    $p := 0
    while p < bpos && p < text.len {
        p = utf8_next(text,p)
        n += 1
    }
    << n
}
fn cp_to_byte_index(text &string,cp_idx int) int {
    $n := 0
    $p := 0
    while n < cp_idx && p < text.len {
        p = utf8_next(text,p)
        n += 1
    }
    << p
}
fn demo() int {
    identity := playground.canvas_identity()
    context := draw.default_context()
    styles := playground.light_styles()
    edit_opts := mono_options(15.0)
    bounds := box(48.0,114.0,360.0,42.0)
    check_bounds := box(428.0,114.0,140.0,42.0)
    text_x := bounds.x + 12.0
    view_w := bounds.width - 24.0
    $check := widgets.checkbox(&identity,2,&check_bounds,false) or >>
    $check_lbl := widgets.styled_label(&context,&"显示密码")
    $focus := widgets.focus_group(&identity,[1,2]) or >>
    $show_pwd := false
    $text := "Xu-Secret-2026!"
    $focused := false
    $anchor := 0
    $head := 0
    $dragging := false
    $clipboard := ""
    $clip_seq := 0
    $just_copied := false
    $scroll_x := 0.0

    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        if event.kind == 77 {
            focused = false
            dragging = false
            focus.clear()
        }
        $display := text
        if !show_pwd { display = mask_bullets(&text) }
        if event.kind == 72 {
            px := event.x
            py := event.y
            if px >= bounds.x && px <= bounds.x + bounds.width && py >= bounds.y && py <= bounds.y + bounds.height {
                focused = true
                focus.focus(1) or >>
                dpos := hit_pos(&context,&edit_opts,&display,px - text_x + scroll_x) or >>
                $pos := dpos
                if !show_pwd { pos = cp_to_byte_index(&text,dpos / 3) }
                if event.repeat >= 3 || (!show_pwd && event.repeat == 2) {
                    anchor = 0
                    head = text.len
                    dragging = false
                } else if event.repeat == 2 {
                    span := select_word_at(&text,pos)
                    anchor = span[0]
                    head = span[1]
                    dragging = false
                } else {
                    dragging = true
                    if (event.modifiers & ui.MOD_SHIFT) != 0 {
                        head = pos
                    } else {
                        anchor = pos
                        head = pos
                    }
                }
            } else {
                dragging = false
                if px < check_bounds.x || px > check_bounds.x + check_bounds.width || py < check_bounds.y || py > check_bounds.y + check_bounds.height {
                    focused = false
                }
            }
        } else if event.kind == 74 && dragging {
            dpos := hit_pos(&context,&edit_opts,&display,event.x - text_x + scroll_x) or >>
            if show_pwd { head = dpos }
            else { head = cp_to_byte_index(&text,dpos / 3) }
        } else if event.kind == 73 {
            dragging = false
        }
        if event.kind == 78 && focused && event.key != 257 {
            handle_edit_key(&event,$&text,$&anchor,$&head,$&clipboard,$&clip_seq,$&just_copied,$&focused,48,0,false) or >>
            if !focused { focus.clear() }
        }
        nav := focus.input(&event)
        $was_focus := focused
        focused = focus.current() == 1
        if focused && !was_focus && event.kind == 78 && event.key == 257 {
            anchor = 0
            head = text.len
        }
        check.set_focus(focus.current() == 2)
        if !nav.consumed {
            act := check.input(&event)
            if act.request_focus { focus.focus(2) or >> }
            if act.kind == widgets.ACTION_CHANGE { show_pwd = check.value() }
        }
        $cur_display := text
        $dhead := head
        if !show_pwd {
            cur_display = mask_bullets(&text)
            dhead = byte_to_cp_index(&text,head) * 3
        }
        scroll_x = compute_scroll(&context,&edit_opts,&cur_display,dhead,view_w,scroll_x) or >>
    }

    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.cursor_rect(bounds.x,bounds.y,bounds.width,bounds.height,"text") or >>
    frame.cursor_rect(check_bounds.x,check_bounds.y,check_bounds.width,check_bounds.height,"pointer") or >>
    frame.fill_rect(28.0,70.0,584.0,240.0,draw.rgb(255,253,251)) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,draw.rgb(217,208,217),1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  PasswordInput")
    draw.text(32,48,12,"#6d626e","浏览器密码预览：支持光标定位、选区删词与显隐切换；完整编辑请用 SDK。")

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
        paint_edit_line($&frame,&context,&edit_opts,&text,text_x,bounds.y,bounds.height,bounds.x + 2.0,bounds.y + 2.0,bounds.width - 4.0,bounds.height - 4.0,scroll_x,anchor,head,focused,draw.rgb(40,35,41)) or >>
    } else {
        bullets := mask_bullets(&text)
        danchor := byte_to_cp_index(&text,anchor) * 3
        dhead := byte_to_cp_index(&text,head) * 3
        paint_edit_line($&frame,&context,&edit_opts,&bullets,text_x,bounds.y,bounds.height,bounds.x + 2.0,bounds.y + 2.0,bounds.width - 4.0,bounds.height - 4.0,scroll_x,danchor,dhead,focused,draw.rgb(40,35,41)) or >>
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
#time

fn box(x f64,y f64,w f64,h f64) layout.Rect {
    << layout.Rect{x: x,y: y,width: w,height: h}
}
fn demo() int {
    identity := playground.canvas_identity()
    context := draw.default_context()
    styles := playground.light_styles()
    bounds := box(48.0,114.0,220.0,44.0)
    label_text := "Build project 构建"
    $control := widgets.task_button(&context,&identity,1,&bounds,&label_text) or >>
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
        if act.kind == widgets.ACTION_ACTIVATE {
            running = !running
            if running {
                control.begin(1,time.zero_instant()) or >>
                control.set_progress(1,0.45)
            } else {
                control.reset() or >>
            }
        }
    }
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.fill_rect(28.0,70.0,584.0,240.0,draw.rgb(255,253,251)) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,draw.rgb(217,208,217),1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  TaskButton")
    draw.text(32,48,12,"#6d626e","任务按钮：支持空闲、运行中进度动画与完成反馈。")
    control.paint_styled($&frame,&styles) or >>
    $sub_val := "点击预览运行状态，再次点击恢复空闲"
    if running {
        sub_val = "任务执行中 (45%) · 桌面 SDK 提供异步任务调度"
    }
    draw.text(48,180,14,"#6d626e",sub_val)
    $message := "Task: idle"
    if control.is_running() {
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
#time

fn box(x f64,y f64,w f64,h f64) layout.Rect {
    << layout.Rect{x: x,y: y,width: w,height: h}
}
fn demo() int {
    identity := playground.canvas_identity()
    context := draw.default_context()
    styles := playground.light_styles()
    bounds := box(48.0,210.0,160.0,42.0)
    $btn := widgets.button(&identity,1,&bounds) or >>
    $lbl := widgets.styled_label(&context,&"Stop 停止")
    spinner_bounds := box(52.0,104.0,36.0,36.0)
    $spin := widgets.spinner(&spinner_bounds) or >>
    $focus := widgets.focus_group(&identity,[1]) or >>
    $running := true
    $ticks := 0
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        nav := focus.input(&event)
        btn.set_focus(focus.current() == 1)
        if nav.consumed { -> }
        act := btn.input(&event)
        if act.request_focus { focus.focus(1) or >> }
        if act.kind == widgets.ACTION_ACTIVATE {
            running = !running
            spin.set_running(running)
            ticks += 1
            if running {
                spin.tick(time.instant_from_ns(ticks * 112500000) or >>, false)
            }
        }
    }
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(styles.background) or >>
    frame.fill_rect(28.0,70.0,584.0,240.0,draw.rgb(255,253,251)) or >>
    frame.stroke_rect(28.0,70.0,584.0,240.0,draw.rgb(217,208,217),1.0) or >>
    draw.text(32,22,20,"#282329","XUUI  /  Spinner")
    draw.text(32,48,12,"#6d626e","加载指示器：展示任务进行中的旋转圆点动效。")
    spin.paint_styled($&frame,&styles) or >>
    if !running { lbl = widgets.styled_label(&context,&"Start 开始") }
    draw.text(104,114,16,"#282329","Loading assets… 正在加载")
    btn.paint_styled($&frame,$&lbl,&styles) or >>
    draw.text(48,172,12,"#6d626e","标准组件加载指示器 · 遵循 xu-ui-design")
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
