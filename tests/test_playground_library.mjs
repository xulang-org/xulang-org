import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {test} from 'node:test';
import assert from 'node:assert/strict';

const catalog = JSON.parse(readFileSync(new URL('../www/xu-play-examples.json', import.meta.url), 'utf8'));

class Element {
  constructor() { this.children = []; this.listeners = {}; this.attributes = {}; this.value = ''; }
  set textContent(value) { this.content = value; this.children = []; }
  get textContent() { return (this.content || '') + this.children.map(child => child.textContent).join(''); }
  appendChild(child) { this.children.push(child); child.parentNode = this; }
  setAttribute(key, value) { this.attributes[key] = value; }
  getAttribute(key) { return this.attributes[key]; }
  addEventListener(type, handler) { (this.listeners[type] ||= []).push(handler); }
  dispatchEvent(event) { for (const handler of this.listeners[event.type] || []) handler(event); }
  click() { if (!this.disabled) this.dispatchEvent({type: 'click'}); }
  focus() { this.focused = true; }
  showModal() { this.open = true; }
  close() { this.open = false; }
}

function mount(saved = {}) {
  const elements = Object.create(null);
  const get = name => elements['xu-play-' + name] ||= new Element();
  const context = {
    document: {getElementById: id => get(id.replace('xu-play-', '')), createElement: () => new Element(), documentElement: {lang: 'en'}},
    window: {}, Event: class { constructor(type) { this.type = type; } }
  };
  vm.runInNewContext(readFileSync(new URL('../www/xu-play-library.js', import.meta.url), 'utf8'), context);
  context.window.XuPlayLibrary.load(catalog, () => saved);
  context.window.XuPlayLibrary.setActive('hello');
  get('browse').click();
  return {
    get,
    search(value) { get('library-search').value = value; get('library-search').dispatchEvent({type: 'input'}); },
    category(name) { get('library-groups').children.find(button => button.textContent === name).click(); }
  };
}

test('search finds a project by filename and previews its complete file set', () => {
  const page = mount();
  assert.equal(page.get('library-list').children.length, 21);
  page.search('pricing.xu');
  assert.equal(page.get('library-list').children.length, 1);
  const detail = page.get('library-detail').textContent;
  for (const value of ['main.xu', 'pricing.xu', 'notes/README.md', 'xu.xun', '180']) assert.ok(detail.includes(value), value);
});

test('diagnostics and UI categories make their expected behavior explicit', () => {
  const page = mount();
  page.category('Diagnostics');
  assert.equal(page.get('library-list').children.length, 2);
  page.get('library-list').children.find(button => button.textContent.includes('Borrow checking')).click();
  assert.match(page.get('library-detail').textContent, /compiler diagnostic/);
  page.category('UI & assets');
  assert.equal(page.get('library-ui').hidden, false);
  assert.equal(page.get('library-open').disabled, true);
});

test('a search with no result offers a working clear-filters action', () => {
  const page = mount();
  page.search('not-a-project-92816');
  assert.equal(page.get('library-empty').hidden, false);
  assert.equal(page.get('library-open').disabled, true);
  page.get('library-reset').click();
  assert.equal(page.get('library-list').children.length, 21);
  assert.equal(page.get('library-open').disabled, false);
});

test('custom and legacy drafts can be reopened with their actual files', () => {
  const page = mount({
    custom: {'main.xu': '@main', 'notes/draft.md': 'my notes', 'xu.xun': 'manifest'},
    coroutine: {'main.xu': '@main', 'legacy.xu': 'retained source'}
  });
  page.category('My drafts');
  assert.equal(page.get('library-list').children.length, 2);
  page.get('library-list').children.find(button => button.textContent.includes('Custom project')).click();
  assert.match(page.get('library-detail').textContent, /notes\/draft.md/);
  assert.doesNotMatch(page.get('library-detail').textContent, /Template output/);
  let changed = false;
  page.get('ex').addEventListener('change', () => { changed = true; });
  page.get('library-open').click();
  assert.equal(page.get('ex').value, 'custom');
  assert.equal(page.get('library').open, false);
  assert.equal(changed, true);
});

test('selecting a template does not load it before Open project is pressed', () => {
  const page = mount();
  let changed = false;
  page.get('ex').addEventListener('change', () => { changed = true; });
  page.search('checkout');
  assert.equal(changed, false);
  page.get('library-open').click();
  assert.equal(changed, true);
  assert.equal(page.get('ex').value, 'checkout');
});
