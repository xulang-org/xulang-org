"""Use measured line boxes in component examples, keeping raw draw API intact."""
import re

REMOVE = '''fn remove_last(value &string) string {
    if value.len == 0 { << "" }
    $end := value.len-1
    while end > 0 && (value[end] & 192) == 128 { end -= 1 }
    << value[0:end]
}
'''

COUNT = '''fn codepoints(value &string) int {
    $count := 0
    for i in 0:value.len { if (value[i] & 192) != 128 { count += 1 } }
    << count
}
'''

HELPERS = '''fn demo_text(frame $&draw.Frame,context &draw.Context,x int,y int,size int,ink draw.Color,text string) int {
    label := context.layout_text(&text,&draw.text_options(f64(size))) or >>
    << frame.text_layout(&label,f64(x),f64(y),ink) or >>
}
fn demo_center_text(frame $&draw.Frame,context &draw.Context,x int,top f64,height f64,size int,ink draw.Color,text string) int {
    label := context.layout_text(&text,&draw.text_options(f64(size))) or >>
    << frame.text_layout(&label,f64(x),top+(height-label.metrics.height)*0.5,ink) or >>
}
'''


def measured_text(code, slug):
    replacements = []
    for match in re.finditer(r'\bdraw\.text\(', code):
        start = match.end()
        depth, quoted, escaped, parts, field = 1, False, False, [], start
        for end in range(start, len(code)):
            ch = code[end]
            if quoted:
                if escaped:
                    escaped = False
                elif ch == '\\':
                    escaped = True
                elif ch == '"':
                    quoted = False
                continue
            if ch == '"':
                quoted = True
            elif ch in '([{':
                depth += 1
            elif ch in ')]}':
                depth -= 1
                if depth == 0:
                    parts.append(code[field:end].strip())
                    break
            elif ch == ',' and depth == 1:
                parts.append(code[field:end].strip())
                field = end + 1
        if len(parts) != 5:
            raise ValueError('Unexpected widget text call: ' + slug)
        x, y, size, color, value = parts
        literal = re.fullmatch(r'"#([0-9a-fA-F]{6}|[0-9a-fA-F]{8})"', color)
        if not literal:
            raise ValueError('Widget text color must be a pinned literal: ' + slug)
        hex_color = literal[1]
        channels = [str(int(hex_color[i:i+2], 16)) for i in range(0, len(hex_color), 2)]
        ink = ('draw.rgb(' if len(channels) == 3 else 'draw.rgba(') + ','.join(channels) + ')'
        inside_field = slug in ('input', 'field', 'password-input') and re.fullmatch(r'by\s*\+\s*\d+', y)
        floating_label = slug in ('field', 'field-area') and re.fullmatch(r'by\s*-\s*6', y)
        if inside_field and value == '"|"':
            call = f'frame.line(f64({x}),bounds.y+(bounds.height-{size}.0)*0.5,f64({x}),bounds.y+(bounds.height+{size}.0)*0.5,{ink},1.5)'
        elif inside_field:
            call = f'demo_center_text($&frame,&context,{x},bounds.y,bounds.height,{size},{ink},{value})'
        elif floating_label:
            call = f'demo_center_text($&frame,&context,{x},bounds.y-7.0,14.0,{size},{ink},{value})'
        elif slug == 'tooltip' and y == '97':
            call = f'demo_center_text($&frame,&context,{x},88.0,32.0,{size},{ink},{value})'
        elif slug == 'toast-host' and y in ('110', '162'):
            top = '96.0' if y == '110' else '148.0'
            call = f'demo_center_text($&frame,&context,{x},{top},44.0,{size},{ink},{value})'
        elif slug == 'date-picker' and value == '"31"':
            call = f'demo_center_text($&frame,&context,{x},166.0,22.0,{size},{ink},{value})'
        else:
            call = f'demo_text($&frame,&context,{x},{y},{size},{ink},{value})'
        suffix = '' if code[end+1:].lstrip().startswith('or ') else ' or >>'
        replacements.append((match.start(), end+1, call + suffix))
    for start, end, value in reversed(replacements):
        code = code[:start] + value + code[end:]
    if replacements:
        position = code.index('fn ')
        code = code[:position] + (REMOVE if 'remove_last(' in code and 'fn remove_last(' not in code else '') + (COUNT if 'codepoints(' in code else '') + HELPERS + '\n' + code[position:]
    return code
