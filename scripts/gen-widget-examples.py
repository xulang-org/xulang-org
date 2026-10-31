#!/usr/bin/env python3
"""Publish focused, editable Xu experiences using the browser's shared widgets."""
import argparse
import json
from pathlib import Path
from widget_portable_examples import CASES, source as portable_source

ROOT = Path(__file__).resolve().parents[1]

WIDGET_ZH_NAMES = {
    'button': '按钮',
    'checkbox': '复选框',
    'switch': '开关',
    'radio': '单选框',
    'slider': '滑块',
    'tabs': '标签页',
    'segmented': '分段控制',
    'list-box': '列表框',
    'progress': '进度条',
    'divider': '分割线',
    'badge': '徽标',
    'card': '卡片',
    'scroll': '滚动容器',
    'radio-group': '单选组',
    'stepper': '步进器',
    'select': '下拉选择',
    'multi-select': '多项选择',
    'color-picker': '取色器',
    'table': '数据表格',
    'pagination': '分页器',
    'breadcrumbs': '面包屑导航',
    'button-group': '按钮组',
    'chart': '图表',
    'range-slider': '双向范围滑块',
    'split-view': '分栏视图',
    'menu': '下拉菜单',
    'context-menu': '右键菜单',
    'split-button': '拆分按钮',
    'styled-label': '样式文本',
}

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
    theme := playground.dark_theme()
    styles := playground.dark_styles()
'''
SUFFIX = '''    frame.present() or >>
    << 0
}
fn main() int {
    << demo() or (err) { eprintln(err.msg())
        << 1 }
}
'''


def source(name, slug, description=''):
    constructor, initial, kind = CONTROLS[slug]
    static = kind in ('styled-label', 'card', 'divider')
    interactive = kind in ('button', 'label', 'slider', 'tabs', 'list', 'scroll')
    bounds = 'box(48.0,104.0,240.0,44.0)'
    if slug in ('checkbox', 'switch', 'radio'):
        bounds = 'box(48.0,104.0,260.0,44.0)'
    elif slug == 'slider':
        bounds = 'box(48.0,104.0,360.0,44.0)'
    elif slug in ('tabs', 'segmented'):
        bounds = 'box(48.0,104.0,480.0,44.0)'
    elif kind in ('list', 'scroll', 'card'):
        bounds = 'box(48.0,96.0,544.0,180.0)'
    elif kind == 'progress':
        bounds = 'box(48.0,116.0,400.0,22.0)'
    elif kind == 'badge':
        bounds = 'box(48.0,116.0,100.0,36.0)'
    elif kind == 'styled-label':
        bounds = 'box(48.0,104.0,544.0,44.0)'
    elif kind == 'divider':
        bounds = 'box(48.0,120.0,544.0,20.0)'

    code = PREFIX + f'    bounds := {bounds}\n    $control := widgets.{constructor}' + ('' if kind == 'styled-label' else ' or >>') + '\n'
    if not static:
        labels = {'button': 'Count +1 / 计数 +1', 'checkbox': 'Receive updates / 接收更新',
                  'switch': 'Live preview / 实时预览', 'radio': 'Stable / 稳定版',
                  'progress': 'Advance / 增加进度', 'badge': 'Add count / 增加计数'}
        code += '    $count := ' + ('4' if kind == 'progress' else '0') + '\n'
    if kind in ('button', 'label'):
        code += '    $styled := widgets.styled_label(&context,&"' + labels[slug] + '")\n'
    if kind in ('tabs', 'list', 'scroll'):
        code += '    $labels := []draw.TextLayout{}\n    for value in ["Overview","Activity","Settings"] { shaped := context.layout_text(&value,&draw.text_options(16.0)) or >>\n        labels.push(shaped) }\n'
    if not interactive and not static:
        code += '    $trigger := widgets.button(&identity,2,&box(48.0,260.0,240.0,40.0)) or >>\n'
        code += '    $trigger_label := widgets.styled_label(&context,&"' + labels[slug] + '")\n'
    focus_id = 1 if interactive else 2
    event_code = f'    $focus := widgets.focus_group(&identity,[{focus_id}]) or >>\n'
    event_code += '''    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        navigation := focus.input(&event)
'''
    focus_control = 'control' if interactive else 'trigger'
    event_code += f'        {focus_control}.set_focus(focus.current() == {focus_id})\n        if navigation.consumed {{ -> }}\n'
    event_code += f'        action := {focus_control}.input(&event)' + (' or >>' if kind in ('list', 'scroll') else '') + '\n'
    event_code += f'        if action.request_focus {{ focus.focus({focus_id}) or >> }}\n'
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
    code += '    $frame := context.new_frame(8192)\n    frame.begin() or >>\n    frame.clear(styles.background) or >>\n'
    code += '    frame.fill_rect(28.0,70.0,584.0,240.0,draw.rgb(25,22,28)) or >>\n'
    code += '    frame.stroke_rect(28.0,70.0,584.0,240.0,draw.rgb(62,54,69),1.0) or >>\n'
    code += f'    draw.text(32,22,20,"#f5f0ed","XUUI  /  {name}")\n'
    code += f'    draw.text(32,48,12,"#b3aab6","{description}")\n'
    if kind == 'badge':
        code += '    badge_label := context.layout_text(&str(count),&draw.text_options(16.0)) or >>\n    control.paint($&frame,&badge_label,&theme) or >>\n'
    elif kind in ('button', 'label'):
        code += '    control.paint_styled($&frame,$&styled,&styles) or >>\n'
    elif kind in ('slider', 'progress'):
        code += '    control.paint_styled($&frame,&styles) or >>\n'
    elif kind in ('tabs', 'list'):
        code += '    control.paint($&frame,&labels,&theme) or >>\n'
    elif kind == 'scroll':
        code += '''    control.begin($&frame) or >>
    for i in 0:9 { text := labels[i % 3]
        frame.text_layout(&text,12.0,12.0 + f64(i) * 42.0,theme.foreground) or >> }
    control.end($&frame) or >>
'''
    elif kind == 'styled-label':
        code += '    control.paint_text_styled($&frame,&bounds,&styles,&styles.button,0) or >>\n'
    else:
        code += '    control.paint($&frame,&theme) or >>\n'
    if kind == 'card':
        code += '    draw.text(64,124,18,"#f5f0ed","Workspace configuration")\n    draw.text(64,158,13,"#b3aab6","Header, body and footer keep distinct spacing.")\n'
    if not interactive and not static:
        code += '    trigger.paint_styled($&frame,$&trigger_label,&styles) or >>\n'
    code += '    draw.text(32,326,13,"#b3aab6",' + message + ')\n    println(' + message + ')\n'
    return code + SUFFIX, initial + '\n'


def generate(root=ROOT, check=False):
    path = root / 'www/xu-play-examples.json'
    catalog = json.loads(path.read_text(encoding='utf-8'))
    widgets = json.loads((root / 'templates/widgets.json').read_text(encoding='utf-8'))
    outputs = {}
    has_widgets = any(g['id'] == 'widgets' for g in catalog['groups'])
    if not has_widgets:
        catalog['groups'].append({
            'id': 'widgets',
            'title': {'zh': '组件库 · 29 个标准控件', 'en': 'Component catalog (29 widgets)'},
            'description': {
                'zh': '涵盖全部 29 种 XUUI 标准控件：按钮、表单输入、选择、数据表格、图表、菜单与分栏视图。',
                'en': 'All 29 XUUI standard interactive controls: buttons, inputs, tables, charts, menus, and split views.'
            }
        })
    for c in widgets['components']:
        if c['slug'] not in CONTROLS and c['slug'] not in CASES:
            continue
        desc = c['description'].get('zh', '')
        code, expected = (source if c['slug'] in CONTROLS else portable_source)(c['name'], c['slug'], desc)
        key = 'widget-' + c['slug']
        zh_title = f"{WIDGET_ZH_NAMES.get(c['slug'], c['name'])} · {c['name']}"
        catalog['projects'][key] = dict(group='widgets', component=c['slug'], title={'zh': zh_title, 'en': c['name']},
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
