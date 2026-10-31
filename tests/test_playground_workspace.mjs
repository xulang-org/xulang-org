// Exercise file state and execution inputs without relying on editor markup.
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createRuntime} from '../www/xu-play-runtime.mjs';

class Element {
  constructor(tag = 'div') {
    this.tag = tag; this.children = []; this.attributes = {}; this.listeners = {};
    this.value = ''; this.style = {}; this.selectionStart = this.selectionEnd = 0;
    this.scrollTop = this.scrollLeft = 0; this.classList = {add() {}};
  }
  set textContent(value) { this.content = value; this.children = []; }
  get textContent() { return (this.content || '') + this.children.map(child => child.textContent).join(''); }
  appendChild(child) { this.children.push(child); child.parentNode = this; return child; }
  setAttribute(key, value) { this.attributes[key] = value; }
  getAttribute(key) { return this.attributes[key]; }
  addEventListener(name, handler) { (this.listeners[name] ||= []).push(handler); }
  dispatchEvent(event) { event.currentTarget = this; for (const handler of this.listeners[event.type] || []) handler(event); }
  click() { if (!this.disabled) this.dispatchEvent({type: 'click'}); }
  focus() { this.focused = true; }
  setSelectionRange(start, end) { this.selectionStart = start; this.selectionEnd = end; }
  querySelector() { return null; }
}

function mount(storage = new Map()) {
  const elements = Object.create(null);
  const get = id => elements[id] ||= new Element();
  get('xu-play-workspace').setAttribute('data-xu-version', '0.10.3');
  get('xu-play-src').value = '@main\nfn main() int { println("first")\n << 0 }\n';
  const context = {
    document: {documentElement: {lang: 'en'}, getElementById: get,
      createElement: tag => new Element(tag), createTextNode: value => { const el = new Element(); el.textContent = value; return el; }},
    window: {addEventListener() {}}, sessionStorage: {
      getItem: key => storage.get(key) || null, setItem: (key, value) => storage.set(key, value)
    }, setTimeout() { return 1; }, clearTimeout() {}
  };
  vm.runInNewContext(readFileSync(new URL('../www/xu-play-workspace.js', import.meta.url), 'utf8'), context);
  function edit(value) { get('xu-play-src').value = value; get('xu-play-src').dispatchEvent({type: 'input'}); }
  function add(path) {
    get('xu-play-file-path').value = path;
    get('xu-play-new-file').dispatchEvent({type: 'submit', preventDefault() {}});
  }
  function open(path) { get('xu-play-file-tabs').children.find(tab => tab.title === path).click(); }
  return {get, edit, add, open, workspace: context.window.XuPlayWorkspace, storage};
}

test('edits survive file switches, example switches and session reloads', () => {
  const page = mount();
  page.edit('@main\nfn main() int { << 7 }');
  page.open('xu.xun');
  assert.equal(page.get('xu-play-src').readOnly, true);
  assert.match(page.workspace.getSource(), /<< 7/);
  page.workspace.setExample('bindings', '@main\nfn main() int { << 2 }');
  page.edit('@main\nfn main() int { << 9 }');
  page.workspace.setExample('hello', 'original hello');
  assert.match(page.workspace.getSource(), /<< 7/);
  page.workspace.setExample('bindings', 'original bindings');
  assert.match(page.workspace.getSource(), /<< 9/);
  assert.match(mount(page.storage).workspace.getSource(), /<< 9/);
});

test('a source beyond the execution limit still survives draft restoration', () => {
  const page = mount();
  const source = '@main\n//' + 'x'.repeat(128 * 1024);
  page.edit(source);
  page.workspace.getSource();
  const restored = mount(page.storage);
  assert.equal(restored.get('xu-play-src').value, source);
});

test('root source files execute together on the real Xu runtime', async () => {
  const page = mount();
  page.edit('@main\nfn main() int { println(answer())\n << 0 }');
  page.add('helpers.xu');
  page.edit('@main\nfn answer() int { << 42 }');
  const runtime = await createRuntime(readFileSync(new URL('../build/playground/xu-play.wasm', import.meta.url)));
  const result = runtime.run(page.workspace.getSource());
  assert.equal(result.exit, 0, result.stderr);
  assert.equal(result.stdout, '42\n');
});

test('project templates load every file and keep per-project edits on return', async () => {
  const page = mount();
  const catalog = JSON.parse(readFileSync(new URL('../www/xu-play-examples.json', import.meta.url), 'utf8'));
  page.workspace.setExample('checkout', catalog.projects.checkout);
  page.open('notes/README.md');
  assert.match(page.get('xu-play-src').value, /Checkout project/);
  page.open('main.xu');
  page.edit(page.get('xu-play-src').value.replace('50, 4', '50, 5'));
  page.workspace.setExample('blank', catalog.projects.blank);
  page.workspace.setExample('checkout', catalog.projects.checkout);
  assert.match(page.workspace.getSource(), /50, 5/);
  const runtime = await createRuntime(readFileSync(new URL('../build/playground/xu-play.wasm', import.meta.url)));
  assert.equal(runtime.run(page.workspace.getSource()).stdout, '230\n');
  assert.match(page.workspace.getSavedProjects().checkout['notes/README.md'], /pricing.xu/);
});

test('the first catalog replaces a pristine placeholder but preserves early edits', () => {
  const template = {files: {'main.xu': '@main\nfn main() int { << 3 }', 'helper.xu': '@main\nfn helper() {}'}};
  const pristine = mount();
  pristine.workspace.setExample('hello', template);
  assert.match(pristine.workspace.getSource(), /<< 3/);
  assert.match(pristine.workspace.getSource(), /fn helper/);
  const edited = mount();
  edited.edit('@main\nfn main() int { << 8 }');
  edited.workspace.setExample('hello', template);
  assert.match(edited.workspace.getSource(), /<< 8/);
  assert.doesNotMatch(edited.workspace.getSource(), /fn helper/);
});

test('legacy custom projects remain reachable after reloading another project', () => {
  const page = mount();
  page.workspace.setSource('@main\nfn main() int { << 17 }');
  page.workspace.setExample('hello', 'hello');
  const restored = mount(page.storage);
  assert.ok(restored.get('xu-play-ex').children.some(option => option.value === 'custom'));
  assert.match(restored.workspace.getSavedProjects().custom['main.xu'], /<< 17/);
  restored.workspace.setExample('custom', 'unused');
  assert.match(restored.workspace.getSource(), /<< 17/);
});

test('nested assets remain editable; nested Xu packages fail explicitly', () => {
  const page = mount();
  page.add('assets/theme.css'); page.edit('body { color: red; }');
  assert.doesNotMatch(page.workspace.getSource(), /color: red/);
  page.add('ui/view.xu'); page.edit('@main\nfn view() {}');
  assert.throws(() => page.workspace.getSource(), /subdirectories/);
  page.get('xu-play-remove').click();
  assert.match(page.workspace.getSource(), /first/);
  page.get('xu-play-undo-remove').click();
  assert.throws(() => page.workspace.getSource(), /subdirectories/);
  page.open('assets/theme.css');
  assert.equal(page.get('xu-play-src').value, 'body { color: red; }');
});

test('invalid and conflicting paths cannot overwrite files', () => {
  const page = mount();
  page.add('notes/guide.md');
  const original = page.workspace.getSource();
  for (const path of ['../outside.xu', '/absolute.xu', 'a//b.xu', '<script>.xu', 'main.xu', 'main.xu/child.xu', 'notes']) {
    page.add(path);
    assert.ok(page.get('xu-play-file-error').textContent, path);
    assert.equal(page.workspace.getSource(), original);
  }
});

test('removal and undo keep the main entry intact', () => {
  const page = mount();
  page.add('helper.xu'); page.edit('@main\nfn helper() {}');
  page.get('xu-play-remove').click();
  assert.doesNotMatch(page.workspace.getSource(), /fn helper/);
  page.get('xu-play-undo-remove').click();
  assert.match(page.workspace.getSource(), /fn helper/);
  page.open('main.xu');
  assert.equal(page.get('xu-play-remove').disabled, true);
});

test('preview tabs are keyboard navigable and execution returns to console', () => {
  const page = mount();
  // The production tab container is retained when the selected tab changes.
  const parent = new Element();
  parent.appendChild(page.get('xu-play-console-tab')); parent.appendChild(page.get('xu-play-preview-tab'));
  page.get('xu-play-console-tab').dispatchEvent({type: 'keydown', key: 'ArrowRight', preventDefault() {}});
  assert.equal(page.get('xu-play-console-panel').hidden, true);
  assert.equal(page.get('xu-play-preview-panel').hidden, false);
  assert.equal(page.get('xu-play-preview-tab').focused, true);
  page.workspace.showConsole();
  assert.equal(page.get('xu-play-console-panel').hidden, false);
  assert.equal(page.get('xu-play-preview-panel').hidden, true);
});

test('documentation snippets replace the custom entry without losing other examples', () => {
  const page = mount();
  page.workspace.setSource('@main\nfn main() int { << 4 }');
  page.workspace.setSource('@main\nfn main() int { << 5 }');
  assert.match(page.workspace.getSource(), /<< 5/);
  page.workspace.setExample('hello', 'original');
  assert.match(page.workspace.getSource(), /first/);
});
test('reset restores default template code after edits', () => {
  const page = mount();
  page.workspace.setExample('arithmetic', {source: '@main\nfn main() int { println(1 + 2)\n << 0 }'});
  page.edit('@main\nfn main() int { println(999)\n << 0 }');
  assert.match(page.workspace.getSource(), /999/);
  page.get('xu-play-reset').click();
  assert.match(page.workspace.getSource(), /1 \+ 2/);
});
