"""Select portable desktop component declarations and their shared dependencies.

All emitted bodies are exact upstream slices. Families load on demand in the
browser; unused components do not add parser/checker work to existing programs.
"""
import re
from collections import defaultdict

FAMILIES = {
    'basic_styles': ('paint_styled paint_position_styled', ['styled_controls.xu', 'controls_basic.xu'], ('Button', 'Checkbox', 'Switch', 'Slider', 'Radio')),
    'select': ('Select select_box', ['controls_nav.xu', 'select_options.xu'], ('Select',)),
    'stepper': ('Stepper stepper', ['controls_data.xu'], ('Stepper',)),
    'radio_group': ('RadioGroup radio_group', ['radio_group.xu'], ()),
    'pagination': ('Pagination pagination', ['pagination.xu', 'pagination_motion.xu', 'pagination_data.xu'], ()),
    'breadcrumbs': ('Breadcrumbs breadcrumbs', ['breadcrumbs.xu', 'breadcrumb_overflow.xu'], ()),
    'range_slider': ('RangeSlider range_slider', ['range_slider.xu', 'range_slider_input.xu', 'range_slider_paint.xu'], ()),
    'split_view': ('SplitView split_view', ['split_view.xu', 'split_view_input.xu', 'split_view_paint.xu'], ()),
    'button_group': ('ButtonGroup button_group button_group_item', ['button_group.xu', 'button_group_paint.xu'], ()),
    'table': ('Table table', ['table.xu', 'table_appearance.xu', 'table_sort.xu', 'table_minima.xu'], ()),
    'menu': ('Menu menu menu_item MENU_CONTEXT MENU_SPLIT', ['menu.xu', 'menu_input.xu', 'menu_geometry.xu', 'menu_paint.xu'], ()),
    'multi_select': ('MultiSelect multi_select', ['multi_select.xu', 'choice_highlight.xu'], ()),
    'color_picker': ('ColorPicker color_picker', ['color_picker.xu', 'color_precision.xu'], ()),
    'chart': ('Chart chart chart_point chart_series chart_domain CHART_BAR', ['chart.xu', 'chart_data.xu', 'chart_input.xu', 'chart_paint.xu'], ()),
}


def lexical(text):
    return re.sub(r'"(?:\\.|[^"\\])*"|//[^\n]*', ' ', text)


def identity(sig):
    match = re.match(r'(?:pub )?(struct|const) (\w+)', sig)
    if match:
        return match[1], '', match[2]
    match = re.match(r'(?:pub )?fn (?:\(\w+ (?:\$&|&(?:mut )?)?(\w+)\) )?(\w+)\(', sig)
    return ('fn', match[1] or '', match[2]) if match else ('', '', '')


def portable(sig):
    if sig.startswith('fn screen_controls_pop('): return True
    return not any(x in sig for x in ('Screen', 'Host)', 'NativeView', ') event(', 'screen_', 'ui.Event'))


def extensions(xu, base, declarations):
    # Only widgets are selected by structural closure. External leaf helpers
    # are selected by their qualified calls, never by copying native hosts.
    pool, functions, symbols, methods = {}, defaultdict(list), {}, defaultdict(list)
    paths = sorted((xu / 'src/ui/widgets').glob('*.xu'))
    external = {'strings': ['mod.xu', 'view.xu', 'storage.xu'], 'strconv': ['mod.xu', 'format_float.xu', 'parse_float.xu', 'bignum.xu'],
                'math': ['mod.xu'], 'time': ['mod.xu', 'typed.xu', 'constants.xu'],
                'unicode/utf8': ['mod.xu'], 'unicode': ['mod.xu', 'tables.xu', 'case_tables.xu'],
                'ui/layout': ['mod.xu'], 'ui/internal/codec': ['mod.xu']}
    paths += [xu / 'src' / module / filename for module, names in external.items() for filename in names]
    for path in paths:
        module = path.parent.relative_to(xu / 'src').as_posix()
        for sig, chunk in declarations(path.read_text(encoding='utf-8')):
            kind, receiver, name = identity(sig)
            if not kind or module == 'ui/widgets' and (not portable(sig) or receiver in ('Editor', 'Field')):
                continue
            key = (module, sig)
            pool[key] = (path.relative_to(xu / 'src').as_posix(), chunk, kind, receiver, name)
            if kind != 'fn': symbols[(module, name)] = key
            elif receiver: methods[(module, name)].append(key)
            else: functions[(module, name)].append(key)
    base_keys = {(module, sig) for module, sig in base}
    fields = {}
    for key, (_, body, kind, _, name) in pool.items():
        if kind == 'struct':
            for field, target in re.findall(r'^\s*(?:pub )?(\w+)\s+(?:\[\])?([\w.]+)', body, re.M):
                fields[(key[0], name, field)] = target
    def type_of(name, module):
        if '.' in name:
            alias, name = name.split('.', 1)
            return ({'draw':'ui/draw', 'layout':'ui/layout', 'ui':'ui', 'time':'time'}.get(alias, alias), name)
        for owner in (module, 'ui/widgets', 'time'):
            if (owner, name) in symbols and pool[symbols[(owner,name)]][2] == 'struct': return owner, name
        return ('', name)
    result = {}
    for family, (_, filenames, receivers) in FAMILIES.items():
        chosen = set()
        for key, (path, chunk, kind, receiver, name) in pool.items():
            if key[0] != 'ui/widgets' or path.split('/')[-1] not in filenames or key in base_keys:
                continue
            if receivers and not (receiver in receivers or name in ('Stepper', 'stepper', 'Select', 'select_box')):
                continue
            roots = set(FAMILIES[family][0].split()) | {'input','paint','paint_styled','apply_styles','set_focus','selected','value','values','active_key','layout','selection','set_cell','set_local_sort','set_sort_kind','set_series','open','close','is_open','hex'}
            if family in ('menu','chart'): roots.add('tick')
            if family == 'menu': roots.update(('paint_popup_styled','set_viewport'))
            if kind != 'fn' or name not in roots: continue
            chosen.add(key)
        while True:
            before = len(chosen)
            # Types used by selected declarations bound method lookup. Native
            # Editor and Screen are intentionally never candidates.
            bodies = {key: lexical(pool[key][1]) for key in chosen}
            types = defaultdict(set)
            for key, body in bodies.items():
                for word in set(re.findall(r'\b[A-Z]\w*\b', body)):
                    for module in (key[0], 'ui/widgets', 'time'):
                        symbol = symbols.get((module, word))
                        if symbol and pool[symbol][2] == 'struct': types[module].add(word)
            for key, body in bodies.items():
                module = key[0]
                variables = {var:type_of(ty,module) for var,ty in re.findall(r'(\w+)\s+(?:\$&|&(?:mut )?)?(?:\[\])?([\w.]+)', key[1])}
                def resolve(expression):
                    parts = expression.split('.')
                    current = variables.get(parts[0])
                    if not current: return None
                    for part in parts[1:]:
                        target = fields.get((*current, part))
                        if not target: return None
                        current = type_of(target, current[0])
                    return current
                for _ in range(3):
                    for var,expression,call in re.findall(r'\b(\w+)\s*:=\s*(?:\$&|\$|mut &|mut |&)?([\w.]+)\s*([({]?)', body):
                        inferred = resolve(expression)
                        if not inferred and call:
                            if call == '{': inferred = type_of(expression,module)
                            else:
                                owner,_,name = expression.rpartition('.')
                                candidates = []
                                if owner:
                                    recv = resolve(owner)
                                    if recv: candidates = [k for k in methods.get((recv[0],name),[]) if pool[k][3] == recv[1]]
                                    elif owner in external: candidates = functions.get((owner,name),[])
                                else: candidates = functions.get((module,expression),[])
                                if candidates:
                                    ret = candidates[0][1].rsplit(')',1)[-1].strip()
                                    if ret: inferred = type_of(ret,candidates[0][0])
                        if inferred: variables[var] = inferred
                for word in set(re.findall(r'\b\w+\b', body)):
                    symbol = symbols.get((module, word))
                    if symbol and symbol not in base_keys: chosen.add(symbol)
                for name in set(re.findall(r'(?<![.\w])([a-z_]\w*)\s*\(', body)):
                    chosen.update(k for k in functions.get((module, name), []) if k not in base_keys)
                for alias, name in re.findall(r'\b(\w+)\.(\w+)', body):
                    dependency = {'utf8': 'unicode/utf8', 'layout':'ui/layout', 'codec':'ui/internal/codec'}.get(alias, alias)
                    if dependency in external:
                        symbol = symbols.get((dependency,name))
                        if symbol and symbol not in base_keys: chosen.add(symbol)
                for alias, name in re.findall(r'\b([\w.]+)\.(\w+)\s*\(', body):
                    dependency = {'utf8': 'unicode/utf8', 'layout':'ui/layout', 'codec':'ui/internal/codec'}.get(alias, alias)
                    if dependency in external:
                        chosen.update(k for k in functions.get((dependency, name), []) if k not in base_keys)
                        continue
                    receiver = resolve(alias)
                    if receiver:
                        chosen.update(k for k in methods.get((receiver[0],name),[]) if pool[k][3] == receiver[1] and k not in base_keys)
                    else:
                        for owner in (module, 'ui/widgets', 'time'):
                            chosen.update(k for k in methods.get((owner, name), []) if pool[k][3] in types[owner] and k not in base_keys)
            if len(chosen) == before: break
        result[family] = chosen
    return pool, result
