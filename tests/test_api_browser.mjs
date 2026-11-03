import {createRequire} from 'node:module';
import {test} from 'node:test';
import assert from 'node:assert/strict';
const {normalize, prepare, search, isSearchKey, isCloseKey} = createRequire(import.meta.url)('../www/api-browser.js');

test('namespace punctuation and Unicode normalize without discarding identifiers', () => {
  assert.equal(normalize(' ＃UI/Widgets.Button::apply_styles() '), 'ui widgets button apply_styles');
  assert.equal(normalize('保留 历史'), '保留 历史');
});
test('qualified methods and package paths match regardless of case', () => {
  const entries = prepare([{title: '(Button) apply_styles', detail: 'pub fn apply_styles', namespace: '#ui/widgets'}]);
  assert.equal(search(entries, 'BUTTON.apply_styles', 30).total, 1);
  assert.equal(search(entries, '#ui/widgets apply_styles', 30).total, 1);
  assert.equal(search(entries, 'Slider.apply_styles', 30).total, 0);
});
test('qualified receivers do not confuse Button with ButtonGroup or prose', () => {
  const entries = prepare([
    {title: '($&ButtonGroup) input', detail: '', context: 'Input on a button group', namespace: '#ui/widgets'},
    {title: '($&Button) route', detail: 'pub fn route(input &Event)', namespace: '#ui/widgets'},
    {title: '($&Button) input', detail: '', namespace: '#ui/widgets'}]);
  assert.deepEqual(search(entries, 'Button.input', 30).items.map(e => e.title), ['($&Button) input']);
  assert.equal(search(entries, 'Button', 30).total, 3);
});
test('localized purposes can be found and query terms all apply', () => {
  const entries = prepare([{title: 'split', detail: 'pub fn split()', context: '#strings 将文本拆分为片段'}]);
  assert.equal(search(entries, '文本 拆分', 30).total, 1);
  assert.equal(search(entries, '拆分 不存在', 30).total, 0);
});
test('exact names precede prefixes and descriptive matches', () => {
  const entries = prepare([{title: 'join', detail: 'Pairs well with split'}, {title: 'split_lines', detail: ''}, {title: 'split', detail: ''}]);
  assert.deepEqual(search(entries, 'split', 30).items.map(e => e.title), ['split', 'split_lines', 'join']);
});
test('large declaration sets keep the correct total with bounded visible results', () => {
  const entries = prepare(Array.from({length: 2500}, (_, i) => ({title: '(View) operation_' + i, detail: 'UI declaration'})));
  const found = search(entries, 'View', 30);
  assert.equal(found.total, 2500);
  assert.equal(found.items.length, 30);
  assert.equal(entries.length, 2500);
});
test('empty queries keep source order and unknown queries have no fallback result', () => {
  const entries = prepare([{title: '#mysql'}, {title: '#strings'}]);
  assert.deepEqual(search(entries, '', 30).items.map(e => e.title), ['#mysql', '#strings']);
  assert.equal(search(entries, 'not-a-package', 30).total, 0);
  assert.equal(search(entries, 'undefined', 30).total, 0);
});
test('search shortcut keeps typing, IME composition and existing dialogs intact', () => {
  assert.equal(isSearchKey({key: '/'}, false, false), true);
  assert.equal(isSearchKey({key: '/'}, true, false), false);
  assert.equal(isSearchKey({key: '/', isComposing: true}, false, false), false);
  assert.equal(isSearchKey({key: '/'}, false, true), false);
});
test('search shortcut respects platform modifiers and handled keys', () => {
  for (const property of ['ctrlKey', 'metaKey', 'altKey', 'defaultPrevented'])
    assert.equal(isSearchKey({key: '/', [property]: true}, false, false), false);
  assert.equal(isSearchKey({key: 'k'}, false, false), false);
});
test('Escape closes search while allowing IME to cancel its own composition', () => {
  assert.equal(isCloseKey({key: 'Escape'}), true);
  assert.equal(isCloseKey({key: 'Escape', isComposing: true}), false);
  assert.equal(isCloseKey({key: 'Escape', keyCode: 229}), false);
  assert.equal(isCloseKey({key: 'Enter'}), false);
});
