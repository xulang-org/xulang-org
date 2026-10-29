#!/usr/bin/env python3
"""Publish focused, editable Xu experiences using the browser's shared widgets."""
import argparse
import json
from pathlib import Path
from widget_portable_examples import CASES, source as portable_source

ROOT = Path(__file__).resolve().parents[1]
CONTROLS = {
    'button': ('button(&identity,1,&bounds)', 'Count: 0', 'button'),
    'checkbox': ('checkbox(&identity,1,&bounds,false)', 'Value: false', 'label'),
    'switch': ('switch_control(&identity,1,&bounds,false)', 'Value: false', 'label'),
    'radio': ('radio(&identity,1,&bounds,0,false)', 'Value: false', 'label'),
    'slider': ('slider(&identity,1,&bounds,0.0,100.0,40.0)', 'Value: 40', 'slider'),
    'tabs': ('tabs(&identity,1,&bounds,3,0)', 'Selected: 0', 'tabs'),
    'segmented': ('segmented(&identity,1,&bounds,3,0)', 'Selected: 0', 'tabs'),
    'list-box': ('list_box(&identity,1,&bounds,3,0)', 'Selected: 0', 'list'),
    'scroll': ('scroll(&identity,1,&bounds,widgets.AXIS_VERTICAL,400.0)', 'Offset: 0', 'scroll'),
    'progress': ('progress(&bounds,0.4)', 'Progress: 40', 'progress'),
    'badge': ('badge(&bounds)', 'Count: 0', 'badge'),
    'card': ('card(&bounds)', 'Count: 0', 'card'),
    'divider': ('divider(&bounds,widgets.AXIS_HORIZONTAL)', 'Count: 0', 'divider'),
    'styled-label': ('styled_label(&context,&"Make room for ideas.")', 'Count: 0', 'styled-label'),
}
PREFIX = '''@main
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
    theme := widgets.default_theme()
    styles := widgets.dark_styles()
'''
SUFFIX = '''    frame.present() or >>
    << 0
}
fn main() int {
    << demo() or (err) { eprintln(err.msg())
        << 1 }
}
'''


def source(name, slug):
    constructor, initial, kind = CONTROLS[slug]
    static = kind in ('styled-label', 'card', 'divider')
    interactive = kind in ('button', 'label', 'slider', 'tabs', 'list', 'scroll')
    bounds = 'box(32.0,104.0,550.0,44.0)'
    if kind in ('list', 'scroll', 'card'):
        bounds = 'box(32.0,86.0,550.0,160.0)'
    if kind == 'progress':
        bounds = 'box(32.0,116.0,550.0,22.0)'
    code = PREFIX + f'    bounds := {bounds}\n    mut control := widgets.{constructor}' + ('' if kind == 'styled-label' else ' or >>') + '\n'
    if not static:
        labels = {'button': 'Count +1 / 计数 +1', 'checkbox': 'Receive updates / 接收更新',
                  'switch': 'Live preview / 实时预览', 'radio': 'Stable / 稳定版',
                  'progress': 'Advance / 增加进度', 'badge': '+1'}
        code += '    mut count := ' + ('4' if kind == 'progress' else '0') + '\n    label := context.layout_text(&"' + labels.get(slug, 'Value / 数值') + '",&draw.text_options(16.0)) or >>\n'
    if kind in ('tabs', 'list', 'scroll'):
        code += '    mut labels := []draw.TextLayout{}\n    for value in ["Overview","Activity","Settings"] { shaped := context.layout_text(&value,&draw.text_options(16.0)) or >>\n        labels.push(shaped) }\n'
    if not interactive and not static:
        code += '    mut trigger := widgets.button(&identity,2,&box(32.0,260.0,220.0,40.0)) or >>\n'
    event_code = f'    mut focus := widgets.focus_group(&identity,[{1 if interactive else 2}]) or >>\n'
    event_code += '''    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        navigation := focus.input(&event)
'''
    focus_control = 'control' if interactive else 'trigger'
    event_code += f'        {focus_control}.set_focus(focus.current() == {1 if interactive else 2})\n        if navigation.consumed {{ -> }}\n'
    event_code += f'        action := {focus_control}.input(&event)' + (' or >>' if kind in ('list', 'scroll') else '') + '\n'
    event_code += f'        if action.request_focus {{ focus.focus({1 if interactive else 2}) or >> }}\n'
    event_code += '        if action.kind == widgets.ACTION_ACTIVATE { count += 1 }\n'
    if kind == 'progress':
        event_code += '        if action.kind == widgets.ACTION_ACTIVATE { control.set_value(f64(count % 11) / 10.0) or >> }\n'
    if not static:
        code += event_code + '    }\n'
    if static:
        message = '"' + name + ' rendered."'
        initial = name + ' rendered.'
    elif kind in ('slider', 'progress'):
        message = '"' + ('Progress: ' if kind == 'progress' else 'Value: ') + '" + str(int(control.value()' + (' * 100.0' if kind == 'progress' else '') + '))'
    elif kind == 'label':
        message = '"Value: " + str(control.value())'
    elif kind in ('tabs', 'list'):
        message = '"Selected: " + str(control.selected())'
    elif kind == 'scroll':
        message = '"Offset: " + str(int(control.offset()))'
    else:
        message = '"Count: " + str(count)'
    code += '    mut frame := context.new_frame(8192)\n    frame.begin() or >>\n    frame.clear(draw.rgb(16,24,39)) or >>\n'
    code += f'    draw.text(32,24,24,"#f8fafc","{name}")\n'
    if kind == 'badge':
        code += '    badge_label := context.layout_text(&str(count),&draw.text_options(16.0)) or >>\n    control.paint(mut &frame,&badge_label,&theme) or >>\n'
    elif kind in ('button', 'label'):
        code += '    control.paint(mut &frame,&label,&theme) or >>\n'
    elif kind in ('tabs', 'list'):
        code += '    control.paint(mut &frame,&labels,&theme) or >>\n'
    elif kind == 'scroll':
        code += '''    control.begin(mut &frame) or >>
    for i in 0:9 { text := labels[i % 3]
        frame.text_layout(&text,12.0,12.0 + f64(i) * 42.0,theme.foreground) or >> }
    control.end(mut &frame) or >>
'''
    elif kind == 'styled-label':
        code += '    control.paint_text_styled(mut &frame,&bounds,&styles,&styles.button,0) or >>\n'
    else:
        code += '    control.paint(mut &frame,&theme) or >>\n'
    if kind == 'card':
        code += '    draw.text(48,110,20,"#f8fafc","Xu workspace")\n    draw.text(48,146,16,"#cbd5e1","A place for your next idea.")\n'
    if not interactive and not static:
        code += '    trigger.paint(mut &frame,&label,&theme) or >>\n'
    code += '    draw.text(32,320,16,"#e2e8f0",' + message + ')\n    println(' + message + ')\n'
    return code + SUFFIX, initial + '\n'


def generate(root=ROOT, check=False):
    path = root / 'www/xu-play-examples.json'
    catalog = json.loads(path.read_text(encoding='utf-8'))
    widgets = json.loads((root / 'templates/widgets.json').read_text(encoding='utf-8'))
    outputs = {}
    for c in widgets['components']:
        if c['slug'] not in CONTROLS and c['slug'] not in CASES:
            continue
        code, expected = (source if c['slug'] in CONTROLS else portable_source)(c['name'], c['slug'])
        key = 'widget-' + c['slug']
        catalog['projects'][key] = dict(group='ui', component=c['slug'], title={lang: c['name'] for lang in ('zh', 'en')},
            description=c['description'], exercise=c['exercise'], entry='main.xu', files={'main.xu': code}, expected={'kind': 'stdout', 'value': expected})
        outputs[root / f'playground/examples/{key}.xu'] = code
    outputs[path] = json.dumps(catalog, ensure_ascii=False, indent=2) + '\n'
    changed = [p for p, text in outputs.items() if not p.exists() or p.read_text(encoding='utf-8') != text]
    if check and changed:
        raise ValueError('Regenerate widget experiences: ' + ', '.join(str(p) for p in changed))
    if not check:
        for p in changed:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(outputs[p], encoding='utf-8', newline='\n')
    return changed


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    print(f'Widget examples: {len(generate(check=parser.parse_args().check))} files updated')
