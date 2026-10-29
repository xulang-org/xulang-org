#!/usr/bin/env python3
"""Generate the component layer from curated metadata and released API articles."""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
START, END = '<!--widget-directory:start-->', '<!--widget-directory:end-->'


def native_source(c):
    """Small Screen setup fragments; complete lifecycle is in the linked workshop."""
    if c['slug'] == 'toast-host':
        return '#ui/widgets\n\nfn notifications() widgets.ToastHost {\n    mut host := widgets.toast_host()\n    value := widgets.notice(&"Workspace saved")\n    host.enqueue(&value) or >>\n    << host\n}'
    args = {
        'styled-label': '"Make room for ideas.",20.0,false', 'button': '"Save"',
        'icon-button': '"www/logo.png","Favorite"', 'input': '"Xu workspace"',
        'text-area': '"Project description"', 'field': '"",&decoration',
        'field-area': '"",&decoration', 'tree-view': '', 'task-button': '"Export"',
        'checkbox': '"Receive updates",false', 'switch': '"Live preview",true',
        'radio': '"Stable",1,true', 'radio-group': '&options,0',
        'slider': '0.0,100.0,40.0', 'stepper': '0.0,100.0,5.0,40.0',
        'select': '&options,0', 'combo-box': '&options,"Design"',
        'multi-select': '&options', 'date-picker': 'value', 'time-picker': 'value',
        'color-picker': 'draw.rgb(180,69,50)', 'tabs': '&options,0',
        'segmented': '&options,0', 'list-box': '&options,0',
        'table': '&options,3,0', 'pagination': '4,0', 'breadcrumbs': '&options',
        'progress': '0.4', 'spinner': '', 'divider': 'widgets.AXIS_HORIZONTAL',
        'badge': '"3"', 'card': '', 'scroll': 'widgets.AXIS_VERTICAL,600.0',
        'popover': 'anchor,"Preferences"', 'tooltip': 'anchor,"Project name"',
        'modal': '"Apply changes?","Review before confirming."', 'web-view': '',
        'button-group': '&items,widgets.BUTTON_GROUP_SINGLE', 'chart': '',
        'range-slider': '0.0,100.0,20.0,80.0', 'split-view': '0.4',
        'menu': '"Actions",&items,widgets.MENU_DROPDOWN,0',
        'context-menu': '"Actions",&items,widgets.MENU_CONTEXT,0',
        'split-button': '"Save",&items,widgets.MENU_SPLIT,1',
        'password-input': '"Xu-demo-123"',
    }
    slug = c['slug']
    imports, setup = ['#ui/widgets'], []
    if '&options' in args[slug]:
        setup.append('options := ["Design","Develop","Review"]')
    if slug in ('field', 'field-area'):
        setup.append('decoration := widgets.field_decoration(&"Project name")')
    if slug in ('date-picker', 'time-picker'):
        imports.append('#time')
        setup.append('value := time.date(2026,10,28,14,30,0,0)')
    if slug == 'color-picker':
        imports.append('#ui/draw')
    if slug in ('popover', 'tooltip'):
        setup += ['anchor := screen.button("Preferences") or >>',
                  'screen.place(anchor,24.0,24.0,180.0,40.0) or >>']
    if slug in ('menu', 'context-menu', 'split-button', 'button-group'):
        factory = 'button_group_item' if slug == 'button-group' else 'menu_item'
        setup.append(f'items := [widgets.{factory}(1,"Save"),widgets.{factory}(2,"Export")]')
    setup.append(f'id := screen.{c["factory"]}({args[slug]}) or >>')
    # Overlays are positioned by Screen relative to their anchor or window.
    if slug not in ('popover', 'tooltip', 'modal'):
        setup.append('screen.place(id,24.0,24.0,320.0,80.0) or >>')
    setup.append('<< id')
    return '\n'.join(imports) + '\n\nfn configure(screen &mut widgets.Screen) int {\n    ' + '\n    '.join(setup) + '\n}'


def generate(root: Path = ROOT, check: bool = False) -> list[Path]:
    catalog = json.loads((root / 'templates/widgets.json').read_text(encoding='utf-8'))
    components, groups = catalog['components'], catalog['groups']
    outputs = {}
    projects = json.loads((root / 'www/xu-play-examples.json').read_text(encoding='utf-8'))['projects']
    version = (root / 'VERSION').read_text(encoding='utf-8').strip()
    for component in components:
        key = 'widget-' + component['slug']
        component['project'] = key if key in projects else None
    outputs[root / 'www/widgets.json'] = json.dumps(catalog, ensure_ascii=False, indent=2) + '\n'
    for lang in ('en', 'zh'):
        zh = lang == 'zh'
        prefix = '/zh' if zh else ''
        base = prefix + '/api/ui/widgets'
        source = root / f'content/{lang}/api/ui/widgets.html'
        original = source.read_text(encoding='utf-8')
        original = re.sub('\n' + re.escape(START) + r'.*?' + re.escape(END) + '\n', '', original, flags=re.S)
        articles = dict(re.findall(r'(<article class="api-item" id="([^"]+)">.*?</article>)', original, re.S))
        # Keep exact released declarations, parameter documentation and anchors.
        articles = {anchor: article for article, anchor in articles.items()}
        cards = []
        for group, titles in groups.items():
            cards.append(f'<section id="components-{group}" class="widget-category"><h2>{html.escape(titles[zh == False])}</h2><div class="widget-grid">')
            for c in components:
                if c['group'] != group:
                    continue
                label = 'Xu/WASM' if c['project'] else ('交互预览' if zh else 'Interactive preview')
                cards.append(f'<a class="widget-card" href="{base}/{c["slug"]}"><span class="widget-card-name">{c["name"]}<span aria-hidden="true">↗</span></span><p>{html.escape(c["description"][lang])}</p><small>{label}</small></a>')
            cards.append('</div></section>')
        title = 'Widgets 组件目录' if zh else 'Widgets component directory'
        intro = ('按用途选择组件。每个组件都有独立的用法、API 和体验入口。' if zh else 'Choose a component by purpose. Each has its own guide, API and experience.')
        directory = START + f'\n<section class="widget-directory"><p class="widget-kicker">UI / WIDGETS · {len(components)}</p><h2>{title}</h2><p class="lead">{intro}</p><nav class="widget-category-links" aria-label="{"组件分类" if zh else "Component categories"}">' + ''.join(f'<a href="#components-{g}">{html.escape(v[not zh])}</a>' for g, v in groups.items()) + '</nav>' + ''.join(cards) + '</section>\n' + END + '\n'
        # Original fragment anchors stay valid for existing API links.
        marker = '<p class="meta">counts:'
        at = original.find('</p>', original.find(marker)) + 4
        outputs[source] = original[:at] + '\n' + directory + original[at:]
        for index, c in enumerate(components):
            factory = c['factory'] if c.get('factory_kind') == 'fn' else '-mut-Screen-' + c['factory']
            if factory not in articles:
                raise ValueError(f'{c["name"]}: missing released constructor {factory}')
            kind = re.compile(r'^(?:struct-' + re.escape(c['type']) + r'$|-?(?:mut-)?' + re.escape(c['type']) + r'-)')
            related = [anchor for anchor in articles if kind.match(anchor) or anchor == factory]
            label = '在演练场运行 Xu 示例' if zh else 'Run the Xu example'
            query = 'example=' + c['project'] if c['project'] else 'widget=' + c['slug']
            if not c['project']:
                label = '在演练场体验预览' if zh else 'Try the interactive preview'
            playground = prefix + '/playground?' + query + ('#xu-play-workspace' if c['project'] else '#widget-experience')
            crumb = f'<nav class="widget-crumb" aria-label="{"位置" if zh else "Breadcrumb"}"><a href="{prefix}/api">API</a><span>/</span><a href="{prefix}/api/ui">UI</a><span>/</span><a href="{base}">Widgets</a><span>/</span><span aria-current="page">{c["name"]}</span></nav>'
            note = ('演练场中的预览用于体验交互，不执行 Xu；原生行为以本页 API 和完整 Xu 示例为准。' if zh else 'The playground preview demonstrates interaction without executing Xu. Use this API and the complete Xu example for native behavior.') if not c['project'] else ('示例由浏览器中的 Xu/WASM 运行器执行。' if zh else 'The example executes in the browser using the Xu/WASM runtime.')
            sections = [f'<!--title: {c["name"]} · UI / Widgets-->', f'<!--xu-api-version: {version}-->', crumb,
                        f'<header class="widget-page-heading"><p class="widget-kicker">UI / WIDGETS / {html.escape(groups[c["group"]][not zh])}</p><h1>{c["name"]}</h1><p class="lead">{html.escape(c["description"][lang])}</p><a class="btn pri" href="{playground}">{label} <span aria-hidden="true">↗</span></a><p class="note">{note}</p></header>',
                        f'<h2 id="experience">{"体验什么" if zh else "What to try"}</h2><p>{html.escape(c["exercise"][lang])}。</p>' if zh else f'<h2 id="experience">What to try</h2><p>{html.escape(c["exercise"][lang])}.</p>',
                        '<h2 id="behavior">' + ('使用要点' if zh else 'Usage notes') + '</h2><p>' + html.escape(c['notes'][lang]) + '</p>',
                        '<h2 id="create">' + (('创建通知队列' if zh else 'Create the notification queue') if c['slug'] == 'toast-host' else ('通过 Screen 创建' if zh else 'Create through Screen')) + '</h2>',
                        '<p>' + (('ToastHost 是通知队列对象，由应用保存并驱动显示。' if c['slug'] == 'toast-host' else '下面的 Screen 构造方法返回节点 ID。将 ID 交给 Screen 的布局、状态与事件接口；它不是下方独立控件类型的实例。') if zh else ('ToastHost is a notification queue owned and presented by the application.' if c['slug'] == 'toast-host' else 'The Screen constructor returns a node ID. Pass that ID to Screen layout, state and event APIs. It is separate from the standalone control object documented below.')) + '</p>',
                        '<p class="note">' + ('原生 Xu 创建片段：在已有 Screen 的初始化阶段调用 configure；窗口创建、事件循环与资源释放参见完整原生示例。' if zh else 'Native Xu setup fragment: call configure during initialization of an existing Screen. See the complete example for window creation, event dispatch and cleanup.') + '</p>' if c['slug'] != 'toast-host' else '',
                        '<pre class="xu-local-only"><code class="language-xu">' + html.escape(native_source(c)) + '</code></pre>', articles[factory],
                        '<h2 id="lifecycle">' + ('放置、状态与事件' if zh else 'Placement, state and events') + '</h2>',
                        '<p>' + ('组件由应用拥有。Screen.place 放置节点，Screen.set_enabled 和 Screen.set_visible 管理可用性与显示。状态变化后重新呈现；创建和修改时处理 <code>or</code> 错误，不在绘制回调中修改拓扑。ToastHost 使用自己的队列接口。' if zh else 'The application owns the component. Screen.place positions nodes; Screen.set_enabled and Screen.set_visible control availability and visibility. Present again after state changes, handle <code>or</code> errors, and keep topology changes outside paint callbacks. ToastHost uses its own queue API.') + '</p>',
                        f'<p><a href="{base}#struct-Action">Action</a> · <a href="{base}#struct-Styles">Styles</a> · <a href="{prefix}/docs/ui">' + ('界面生命周期与样式指南' if zh else 'UI lifecycle and styling guide') + '</a></p>',
                        f'<p><a href="{base}#-mut-Screen-place">Screen.place</a> · <a href="{base}#-mut-Screen-set_enabled">Screen.set_enabled</a> · <a href="{base}#-mut-Screen-set_visible">Screen.set_visible</a></p>' if c['slug'] != 'toast-host' else '',
                        '<h2 id="api">' + ('独立控件对象 API' if zh else 'Standalone control object API') + '</h2>',
                        '<p>' + ('以下类型与方法用于自行管理控件、输入和绘制的进阶用法。接收者是控件对象，不是 Screen 返回的节点 ID；普通 Screen 用法请使用上面的创建接口及 Widgets 模块中的 Screen 方法。' if zh else 'These types and methods support applications that manage control objects, input and painting directly. Their receiver is a control object, not a Screen node ID. For Screen usage, use the constructor above and the Screen methods in the Widgets module.') + '</p>' if c['slug'] != 'toast-host' else '',
                        *[articles[a] for a in related if a != factory],
                        f'<h2 id="native-example">{"完整原生示例" if zh else "Complete native example"}</h2><p><a href="{base}#example-a2be48ce1c23">Component Workshop</a> · <a href="{base}">{"返回 Widgets 目录" if zh else "Back to Widgets"}</a></p>']
            # Reused declaration articles may link to module-level anchors.
            page = '\n'.join(sections) + '\n'
            own_ids = set(re.findall(r'\bid="([^"]+)"', page))
            page = re.sub(r'href="#([^"]+)"', lambda m: m[0] if m[1] in own_ids else f'href="{base}#{m[1]}"', page)
            outputs[root / f'content/{lang}/api/ui/widgets/{c["slug"]}.html'] = page
    changed = []
    for path, value in outputs.items():
        if path.exists() and path.read_text(encoding='utf-8') == value:
            continue
        changed.append(path)
        if not check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(value, encoding='utf-8')
    if check and changed:
        raise ValueError('Widget pages need generation: ' + ', '.join(str(p.relative_to(root)) for p in changed))
    return changed


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--site', type=Path, default=ROOT)
    args = parser.parse_args()
    print(f'Widgets: {len(generate(root=args.site, check=args.check))} files updated')
