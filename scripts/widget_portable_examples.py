"""Focused experiences for the extended, unchanged desktop widget families."""

CASES = {
    'stepper': ('stepper(&identity,1,&bounds,0.0,100.0,5.0,40.0)', '"Value: " + str(int(control.value()))', 'Value: 40', 'basic-label'),
    'select': ('select_box(&identity,1,&bounds,3,0)', '"Selected: " + str(control.selected())', 'Selected: 0', 'basic-options'),
    'radio-group': ('radio_group(&context,&identity,1,&bounds,&options,0)', '"Selected: " + str(control.selected())', 'Selected: 0', 'styled'),
    'pagination': ('pagination(&context,&identity,1,&bounds,4,0)', '"Page: " + str(control.selected() + 1)', 'Page: 1', 'styled'),
    'breadcrumbs': ('breadcrumbs(&context,&identity,1,&bounds,&options)', '"Activated: " + str(last)', 'Activated: 0', 'styled'),
    'range-slider': ('range_slider(&context,&identity,1,&bounds,0.0,100.0,20.0,80.0)', '"Range: " + str(int(control.values().lower)) + " - " + str(int(control.values().upper))', 'Range: 20 - 80', 'styled'),
    'split-view': ('split_view(&identity,1,&bounds,0.4)', '"Ratio: " + str(int(control.value() * 100.0))', 'Ratio: 40', 'styled'),
    'button-group': ('button_group(&context,&identity,1,&bounds,&items,widgets.BUTTON_GROUP_SINGLE)', '"Selected: " + str(control.active_key())', 'Selected: 1', 'styled'),
    'table': ('table(&context,&identity,1,&bounds,&headers,3,0)', '"Selected: " + str(control.selected())', 'Selected: 0', 'styled'),
    'menu': ('menu(&context,&identity,1,&bounds,"Actions",&items,widgets.MENU_DROPDOWN,0)', '"Command: " + str(last)', 'Command: 0', 'styled'),
    'context-menu': ('menu(&context,&identity,1,&bounds,"Right-click here / 在此右键",&items,widgets.MENU_CONTEXT,0)', '"Command: " + str(last)', 'Command: 0', 'styled'),
    'split-button': ('menu(&context,&identity,1,&bounds,"Save",&items,widgets.MENU_SPLIT,1)', '"Command: " + str(last)', 'Command: 0', 'styled'),
    'multi-select': ('multi_select(&context,&identity,1,&bounds,&options)', '"Selected count: " + str(control.values().len)', 'Selected count: 0', 'styled'),
    'color-picker': ('color_picker(&context,&identity,1,&bounds,draw.rgb(180,69,50))', '"Color: " + control.hex()', 'Color: #B44532FF', 'styled'),
    'chart': ('chart(&context,&identity,1,&bounds)', '"Selected point: " + str(control.selection().point_id)', 'Selected point: 0', 'styled'),
}


def source(name, slug):
    constructor, summary, initial, paint = CASES[slug]
    tall = slug in ('radio-group', 'split-view', 'table', 'chart', 'color-picker', 'context-menu')
    height = 200 if tall else 44
    code = '''@main
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
    theme := playground.dark_theme()
    styles := playground.dark_styles()
    options := ["Design","Develop","Review"]
    headers := ["Workspace","Members"]
'''
    code += f'    bounds := box(32.0,86.0,550.0,{height}.0)\n'
    if slug == 'button-group':
        code += '    items := [widgets.button_group_item(1,"Design"),widgets.button_group_item(2,"Develop"),widgets.button_group_item(3,"Review")]\n'
    elif slug in ('menu', 'context-menu', 'split-button'):
        code += '    items := [widgets.menu_item(1,"Save"),widgets.menu_item(2,"Export"),widgets.menu_item(3,"Duplicate")]\n'
    code += '    $control := widgets.' + constructor + ' or >>\n    $last := 0\n'
    if slug in ('menu', 'context-menu', 'split-button'):
        code += '    control.set_viewport(&box(0.0,0.0,640.0,360.0)) or >>\n'
    if slug == 'table':
        code += '''    for i in 0:3 { value := options[i]
        control.set_cell(i,0,&value) or >>
        number := str(12 - i * 3)
        control.set_cell(i,1,&number) or >> }
    control.set_sort_kind(1,widgets.TABLE_SORT_NUMBER) or >>
    control.set_local_sort(true) or >>
'''
    if slug == 'chart':
        code += '''    $series := widgets.chart_series(1,"Workspace",widgets.CHART_BAR)
    series.points = [widgets.chart_point(1,1.0,12.0),widgets.chart_point(2,2.0,8.0),widgets.chart_point(3,3.0,5.0)]
    control.set_series(&[series]) or >>
    _ := control.tick(&styles,time.instant_from_ns(1) or >>,true) or >>
'''
    styled = paint == 'styled'
    # These two controls calculate geometry during construction/painting.
    apply = styled and slug not in ('radio-group',)
    if apply:
        code += '    control.apply_styles(&styles) or >>\n'
    code += '''    $focus := widgets.focus_group(&identity,[1]) or >>
    while true {
        event := playground.next_input()
        if event.kind == 0 { <- }
        navigation := focus.input(&event)
        control.set_focus(focus.current() == 1)
        if navigation.consumed { -> }
        action := control.input(&event) or >>
        if action.request_focus { focus.focus(1) or >> }
        if action.kind == widgets.ACTION_ACTIVATE { last = int(action.value) }
'''
    if slug in ('menu', 'context-menu', 'split-button'):
        code += '        _ := control.tick(&styles,time.instant_from_ns(event.time_ns) or >>,true) or >>\n'
    code += '''    }
    $frame := context.new_frame(8192)
    frame.begin() or >>
    frame.clear(draw.rgb(16,24,39)) or >>
'''
    code += f'    draw.text(32,24,24,"#f8fafc","{name}")\n'
    if paint == 'basic-label':
        code += '    value := str(int(control.value()))\n    label := context.layout_text(&value,&draw.text_options(16.0)) or >>\n    control.paint($&frame,&label,&theme) or >>\n'
    elif paint == 'basic-options':
        code += '    $labels := []draw.TextLayout{}\n    for value in options { label := context.layout_text(&value,&draw.text_options(16.0)) or >>\n        labels.push(label) }\n    control.paint($&frame,&labels,&theme) or >>\n'
    else:
        code += '    control.paint_styled($&frame,&styles) or >>\n'
    if slug in ('menu', 'context-menu', 'split-button'):
        code += '    control.paint_popup_styled($&frame,&styles) or >>\n'
    if slug == 'split-view':
        code += '''    panes := control.layout()
    frame.fill_rect(panes.first.x,panes.first.y,panes.first.width,panes.first.height,draw.rgb(39,60,85)) or >>
    frame.fill_rect(panes.second.x,panes.second.y,panes.second.width,panes.second.height,draw.rgb(62,45,74)) or >>
'''
    code += f'    message := {summary}\n    draw.text(32,320,16,"#e2e8f0",message + "")\n    println(message)\n'
    code += '''    frame.present() or >>
    << 0
}
fn main() int {
    << demo() or (err) { eprintln(err.msg())
        << 1 }
}
'''
    return code, initial + '\n'
