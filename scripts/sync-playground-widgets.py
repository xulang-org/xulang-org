#!/usr/bin/env python3
"""Vendor complete, unchanged desktop declarations for the browser UI subset.

No widget behavior is rewritten here. Unsupported native event loops and
control-specific styled methods are excluded at declaration boundaries. The manifest records every slice hash.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def declarations(text):
    matches = list(re.finditer(r'^(?:pub )?(?:fn|struct|const) [^\n{]+', text, re.M))
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunk = text[match.start():end].rstrip()
        # Comments between declarations belong to neither API implementation.
        chunk = re.sub(r'\n(?://[^\n]*\n?)+$', '', chunk).rstrip()
        yield match[0].strip(), chunk


def basic(sig):
    """Keep basic APIs; styled paint/layout and native event pumps are separate."""
    return not any(x in sig for x in ('styled(', 'style(', 'style_or(', 'has_style(',
        'visual_state(', ') event(', 'set_motion(', 'tick(', 'next_tick(', 'apply_styles(',
        'content_bounds(', 'item_bounds('))


def selected(path, sig):
    if path == 'ui/widgets/mod.xu':
        return (' Host' not in sig and 'attach(' not in sig and ') event(' not in sig)
    if path == 'ui/widgets/controls_basic.xu':
        return (sig.startswith(('pub struct Switch', 'pub fn switch_control', 'pub struct Slider', 'pub fn slider(', 'fn clamp_slider_value', 'pub struct Radio', 'pub fn radio(')) or
                (('&Switch)' in sig or '&mut Switch)' in sig or '&Slider)' in sig or '&mut Slider)' in sig or '&Radio)' in sig or '&mut Radio)' in sig) and
                not any(x in sig for x in ('_styled(', 'paint_position', 'style(', 'style_or(', 'has_style(', 'visual_state(', ') event(', 'set_motion(', 'tick(', 'next_tick(', 'apply_styles('))))
    if path == 'ui/widgets/editor.xu':
        return sig.startswith(('pub const ACTION_SUBMIT', 'const EDITOR_', 'pub const EDITOR_', 'pub struct Editor', 'fn new_editor(', 'pub fn input(',
            'fn (editor &Editor) is_multiline(', 'fn (editor &Editor) layout_value(',
            'pub fn (editor &Editor)', 'fn (editor &Editor) caret_rect(', 'fn (editor &mut Editor) read_state(',
            'fn (editor &mut Editor) drop_layout(', 'fn (editor &mut Editor) stash(', 'fn (editor &mut Editor) stop_session(',
            'pub fn (editor &mut Editor) focus_session(', 'pub fn (editor &mut Editor) paint(',
            'fn (editor &mut Editor) paint_editor(', 'fn (editor &mut Editor) bind_geometry('))
    if path == 'ui/widgets/editor_styles.xu':
        return sig.startswith(('fn (editor &Editor)', 'pub fn (editor &Editor) visual_state(',
            'pub fn (editor &Editor) is_read_only(', 'pub fn (editor &mut Editor) set_read_only('))
    if path == 'ui/widgets/editor_input.xu':
        return sig.startswith('fn (editor &mut Editor) cancel_clipboard(')
    if path == 'ui/widgets/editor_motion.xu':
        return sig.startswith('fn (editor &mut Editor) restart_caret(')
    if path == 'ui/widgets/screen.xu':
        return sig.startswith('fn screen_empty(')
    if path == 'ui/widgets/scroll.xu':
        return (sig.startswith('pub const AXIS_') or (basic(sig) and not any(x in sig for x in ('visible_items(', 'layout_items('))))
    if path == 'ui/widgets/scroll_styles.xu':
        return sig.startswith(('pub fn (scroll &Scroll) scrollbar_', 'fn (scroll &mut Scroll) bar_input('))
    if path == 'ui/widgets/controls_data.xu':
        return basic(sig) and ('ListBox)' in sig or sig.startswith(('pub struct ListBox', 'pub fn list_box(')))
    if path == 'ui/widgets/controls_nav.xu':
        return sig.startswith(('fn max_int(', 'fn min_int(')) or basic(sig) and ('Tabs)' in sig or sig.startswith(('pub struct Tabs', 'pub fn tabs(', 'pub fn segmented(')))
    if path == 'ui/widgets/controls_display.xu':
        return basic(sig)
    if path == 'ui/widgets/list_rows.xu':
        return sig.startswith(('pub struct ListAppearance', 'pub fn list_appearance('))
    if path == 'ui/widgets/data_scrollbar.xu':
        return 'ListBox)' in sig and 'paint_data_scrollbar' not in sig
    if path == 'ui/widgets/appearance.xu':
        return sig.startswith('pub const BADGE_')
    if path == 'ui/widgets/badge_attachment.xu':
        return sig.startswith('pub const BADGE_')
    if path == 'ui/widgets/styled_controls.xu':
        return (('progress &Progress)' in sig or 'progress &mut Progress)' in sig) and 'set_style(' not in sig) or sig.startswith(('pub fn (button &Button) is_', 'pub fn (button &mut Button) set_invalid(', 'pub fn (button &mut Button) set_read_only('))
    if path == 'ui/widgets/state_style.xu':
        return sig.startswith(('pub const PAINT_', 'pub struct StatePaint', 'pub struct ResolvedStyle', 'pub fn state_paint(', 'pub fn (c &ControlStyle) resolve(', 'fn validate_states(', 'fn copy_states(', 'fn states_equal(', 'fn read_style_color(', 'fn read_style_f64(', 'fn decode_control_style(', 'struct ScalarControlStyle', 'fn empty_scalar_style', 'fn unpack_scalar_style('))
    if path == 'ui/widgets/selection_motion.xu':
        return sig.startswith(('struct SelectionMotion', 'fn selection_motion'))
    if path == 'ui/widgets/motion.xu':
        return sig.startswith(('fn fade_color(', 'pub const EASE_', 'pub struct MotionSpec', 'pub fn motion_spec(', 'pub struct Tween', 'pub fn tween('))
    if path == 'ui/widgets/slider_appearance.xu':
        return sig.startswith(('pub struct SliderAppearance', 'pub fn slider_appearance('))
    if path == 'ui/widgets/style.xu':
        return not any(x in sig for x in ('set_style(',))
    if path == 'ui/layout/mod.xu':
        return (sig.startswith(('pub const MAX_EXTENT', 'pub struct Size', 'pub struct Rect', 'pub struct Insets', 'fn extent(', 'fn coordinate(', 'pub fn intersect(')) or ') contains(x f64' in sig)
    if path == 'ui/text_input.xu':
        return sig.startswith(('pub struct TextInput', 'pub fn text_input_options(', 'pub fn (state &TextInputState) display_'))
    if path == 'ui/text_input_geometry.xu':
        return sig.startswith(('pub struct TextInputTransform', 'pub fn text_input_translation('))
    if path == 'ui/requests.xu':
        return sig.startswith('pub struct Request') and not sig.startswith(('pub struct RequestOptions', 'pub struct RequestResult'))
    if path == 'ui/input.xu':
        return sig.startswith(('pub struct CanvasEvent', 'pub struct InputEvent')) or bool(re.match(r'pub const [A-Z][A-Z_0-9]* ', sig))
    if path == 'math/mod.xu':
        return sig.startswith(tuple('pub fn ' + n + '(' for n in ('abs', 'min', 'max', 'floor', 'ceil', 'is_nan', 'is_inf', 'round', 'ldexp'))) or sig.startswith(('fn math_hw_supported(', 'fn math_hw_floor(', 'fn math_hw_ceil('))
    if path == 'unicode/utf8/mod.xu':
        return sig.startswith(('fn is_cont(', 'pub fn rune_len(', 'pub fn decode(', 'pub fn decode_width(', 'pub fn valid('))
    if path == 'ui/internal/codec/mod.xu':
        return sig.startswith(('pub fn read_word32(', 'pub fn read_float64('))
    if path == 'time/constants.xu':
        return sig.startswith('const NS_PER_MILLISECOND')
    if path == 'time/typed.xu':
        return sig.startswith(('pub struct Duration', 'pub fn duration(', 'pub struct Instant', 'pub fn zero_instant('))
    if path == 'time/mod.xu':
        return sig.startswith(('pub fn millisecond(',))
    if path == 'ui/draw/frame.xu':
        return sig.startswith(('pub struct Color', 'fn color_byte(', 'pub fn rgba(', 'pub fn rgb(', 'pub fn (color &Color) value(', 'pub fn (color &Color) with_alpha('))
    if path in ('ui/draw/text.xu', 'ui/draw/path.xu'):
        return sig.startswith(('pub struct TextOptions', 'pub struct TextMetrics', 'pub struct TextLayout', 'pub struct TextHit', 'pub struct TextSelectionRect', 'pub struct StrokeOptions', 'pub fn stroke_options(', 'pub const CAP_', 'pub const JOIN_', 'pub fn text_options(', 'pub const TEXT_'))
    return False


SOURCES = {
    'utf8': ('unicode/utf8', '#errors', ['unicode/utf8/mod.xu']),
    'codec': ('ui/internal/codec', '#math\n#errors', ['ui/internal/codec/mod.xu']),
    'widgets': ('ui/widgets', '#ui\n#ui/draw\n#ui/layout\n#errors\n#math\n#time\n#unicode/utf8\n#ui/internal/codec', [
        'ui/widgets/mod.xu', 'ui/widgets/editor.xu', 'ui/widgets/editor_styles.xu', 'ui/widgets/editor_input.xu', 'ui/widgets/editor_motion.xu', 'ui/widgets/screen.xu', 'ui/widgets/scroll_styles.xu', 'ui/widgets/scroll.xu', 'ui/widgets/controls_basic.xu', 'ui/widgets/controls_data.xu', 'ui/widgets/controls_nav.xu', 'ui/widgets/controls_display.xu', 'ui/widgets/list_rows.xu', 'ui/widgets/data_scrollbar.xu', 'ui/widgets/appearance.xu', 'ui/widgets/badge_attachment.xu', 'ui/widgets/styled_controls.xu', 'ui/widgets/state_style.xu',
        'ui/widgets/selection_motion.xu', 'ui/widgets/motion.xu', 'ui/widgets/slider_appearance.xu', 'ui/widgets/style.xu']),
    'layout': ('ui/layout', '#errors\n#math', ['ui/layout/mod.xu']),
    'ui': ('ui', '', ['ui/input.xu', 'ui/text_input.xu', 'ui/text_input_geometry.xu', 'ui/requests.xu']),
    'math': ('math', '', ['math/mod.xu']),
    'time': ('time', '', ['time/typed.xu', 'time/mod.xu', 'time/constants.xu']),
    'draw_types': ('ui/draw', '', ['ui/draw/frame.xu', 'ui/draw/text.xu', 'ui/draw/path.xu'])}


def generate(xu):
    files, manifest = {}, {'upstream': 'xulang-org/xu', 'commit': '', 'declarations': []}
    import subprocess
    manifest['commit'] = subprocess.check_output(['git', '-C', str(xu), 'rev-parse', 'HEAD'], text=True).strip()
    for name, (module, imports, paths) in SOURCES.items():
        out = '@' + module + '\n\n// Generated by scripts/sync-playground-widgets.py; do not edit.\n' + imports + '\n\n'
        for path in paths:
            for sig, chunk in declarations((xu / 'src' / path).read_text()):
                if selected(path, sig):
                    out += '// Upstream: src/' + path + '\n' + chunk + '\n\n'
                    manifest['declarations'].append({'module': name, 'path': 'src/' + path, 'signature': sig,
                                                     'sha256': hashlib.sha256(chunk.encode()).hexdigest()})
        files['desktop_' + name + '.xu'] = out
    from widget_extensions import extensions, FAMILIES
    base = {(SOURCES[d['module']][0], d['signature']) for d in manifest['declarations']}
    pool, families = extensions(xu, base, declarations)
    owners = {}
    for family, keys in families.items():
        for key in keys: owners.setdefault(key, []).append(family)
    buckets = {}
    for key, names in owners.items():
        module = key[0]
        suffix = names[0] if len(names) == 1 else 'shared_' + hashlib.sha256(','.join(names).encode()).hexdigest()[:10]
        target = ('widgets_extra_' if module == 'ui/widgets' else 'extra_' + module.replace('/', '_') + '_') + suffix
        buckets.setdefault((module, target), []).append(key)
    manifest['families'] = {key: value[0].split() for key, value in FAMILIES.items()}
    manifest['extension_chunks'] = []
    for (module, name), keys in sorted(buckets.items()):
        manifest['extension_chunks'].append({'name':name,'module':module,'families':owners[keys[0]]})
        imports = '#ui\n#ui/draw\n#ui/layout\n#errors\n#math\n#time\n#strings\n#strconv\n#unicode/utf8\n#ui/internal/codec' if module == 'ui/widgets' else '\n'.join('#' + p for p in ('errors', 'math', 'time', 'strings', 'strconv', 'unicode', 'unicode/utf8') if p != module)
        out = '@' + module + '\n\n// Generated by scripts/sync-playground-widgets.py; do not edit.\n' + imports + '\n\n'
        for key in sorted(keys):
            path, chunk, *_ = pool[key]
            out += '// Upstream: src/' + path + '\n' + chunk + '\n\n'
            manifest['declarations'].append({'module': name, 'path': 'src/' + path, 'signature': key[1], 'sha256': hashlib.sha256(chunk.encode()).hexdigest()})
        files['desktop_' + name + '.xu'] = out
    files['desktop-sources.json'] = json.dumps(manifest, ensure_ascii=False, indent=2) + '\n'
    return files


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--xu-root', type=Path, default=Path('/workspace/xu'))
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    generated = generate(args.xu_root)
    for old in (ROOT / 'playground/stdlib').glob('desktop_*extra*.xu'):
        if old.name not in generated and 'Generated by scripts/sync-playground-widgets.py' in old.read_text():
            if args.check: raise SystemExit('obsolete desktop subset: ' + str(old))
            old.unlink()
    for name, text in generated.items():
        path = ROOT / 'playground/stdlib' / name
        if args.check:
            if path.read_text() != text:
                raise SystemExit('desktop subset drift: ' + str(path))
        else:
            path.write_text(text)
