import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {test} from 'node:test';
import assert from 'node:assert/strict';

const catalog = JSON.parse(readFileSync(new URL('../www/widgets.json', import.meta.url), 'utf8'));
const script = readFileSync(new URL('../www/widget-experience.js', import.meta.url), 'utf8');

// Browser plumbing only: exercise the production controller and real catalog.
async function mount(slug, language = 'en') {
  const timers = new Map();
  let nextTimer = 0;
  const document = {documentElement: {lang: language}, activeElement: null};
  class Element {
    constructor(tag) {
      this.tagName = tag; this.children = []; this.attributes = {}; this.dataset = {};
      this.listeners = {}; this.value = ''; this.hidden = false;
      this.classList = {add: () => {}};
    }
    set textContent(value) { this.text = value; this.children = []; }
    get textContent() { return (this.text || '') + this.children.map(c => c.textContent).join(''); }
    appendChild(child) { child.parentNode = this; this.children.push(child); return child; }
    setAttribute(key, value) { this.attributes[key] = String(value); }
    getAttribute(key) { return this.attributes[key] ?? null; }
    removeAttribute(key) { delete this.attributes[key]; }
    addEventListener(type, handler) { (this.listeners[type] ||= []).push(handler); }
    dispatchEvent(event) { for (const fn of this.listeners[event.type] || []) fn(event); }
    click() { if (!this.disabled) { this.focus(); this.dispatchEvent({type: 'click'}); } }
    focus() {
      if (document.activeElement === this) return;
      document.activeElement?.dispatchEvent({type: 'blur'});
      document.activeElement = this; this.dispatchEvent({type: 'focus'});
    }
    contains(el) { return el === this || this.children.some(c => c.contains(el)); }
    showModal() { this.open = true; descendants(this).find(c => c.tagName === 'button')?.focus(); }
    close() { this.open = false; }
    remove() { this.parentNode.children = this.parentNode.children.filter(c => c !== this); }
  }
  function descendants(el) { return el.children.flatMap(c => [c, ...descendants(c)]); }
  const root = new Element('section'), list = new Element('nav'), detail = new Element('section');
  const search = new Element('input'), category = new Element('select'), count = new Element('small');
  const workspace = new Element('section'), help = new Element('p');
  const controls = {'[data-widget-list]': list, '[data-widget-detail]': detail,
    'input[type="search"]': search, select: category, '[data-widget-count]': count};
  root.querySelector = selector => controls[selector];
  document.getElementById = id => ({'widget-experience': root,
    'xu-play-workspace': workspace, 'xu-play-help': help})[id];
  document.createElement = tag => new Element(tag);
  document.body = new Element('body'); document.currentScript = {src: 'https://example.org/repo/widget-experience.js'};
  const location = {href: 'https://example.org/repo/playground/?widget=' + slug, hash: ''};
  vm.runInNewContext(script, {document, location, URL, Event: class {constructor(type) {this.type = type;}},
    history: {replaceState: (_, __, url) => {location.href = String(url);}},
    fetch: async () => ({ok: true, json: async () => catalog}),
    window: {addEventListener() {}}, requestAnimationFrame: fn => fn(),
    setTimeout: (fn, delay) => {timers.set(++nextTimer, {fn, delay}); return nextTimer;},
    clearTimeout: id => timers.delete(id)});
  await new Promise(resolve => setImmediate(resolve));
  return {document, detail, workspace, help, timers,
    find: predicate => descendants(detail).find(predicate),
    button: text => descendants(detail).find(el => el.tagName === 'button' && el.textContent === text),
    choose: name => list.children.find(el => el.textContent === name).click(),
    flush: () => {const pending = [...timers.values()]; timers.clear(); pending.forEach(t => t.fn());}};
}

test('all component entries render and browsing hides the previous project', async () => {
  const page = await mount('button');
  for (const c of catalog.components) {
    page.choose(c.name);
    assert.equal(page.find(el => el.tagName === 'h3').textContent, c.name);
    assert.equal(page.document.activeElement.tagName, 'h3');
    assert.equal(page.workspace.hidden, true);
    assert.equal(page.help.hidden, true);
  }
});

for (const slug of ['input', 'text-area', 'field', 'field-area']) {
  test('input validation preserves errors, connects feedback and recovers: ' + slug, async () => {
    const page = await mount(slug);
    const field = page.find(el => ['input', 'textarea'].includes(el.tagName));
    const status = page.find(el => el.getAttribute('role') === 'status');
    assert.equal(field.getAttribute('aria-invalid'), null);
    field.value = '   '; page.button('Save').click();
    assert.equal(field.getAttribute('aria-invalid'), 'true');
    assert.equal(field.getAttribute('aria-describedby'), status.id);
    assert.equal(status.textContent, 'Enter a value');
    assert.equal(page.document.activeElement, field);
    field.dispatchEvent({type: 'input'});
    assert.equal(status.textContent, 'Enter a value');
    field.value = 'x'.repeat(field.maxLength + 1); page.button('Save').click();
    assert.equal(field.getAttribute('aria-invalid'), 'true');
    field.value = 'Xu workspace'; field.dispatchEvent({type: 'input'}); page.button('Save').click();
    assert.equal(field.getAttribute('aria-invalid'), 'false');
    assert.equal(status.textContent, 'Saved');
    assert.equal(field.value, 'Xu workspace');
  });
}

test('Escape cancels pending tooltip appearance; a focused click keeps help visible', async () => {
  const page = await mount('tooltip');
  const help = page.button('Project name ⓘ'), tip = page.find(el => el.getAttribute('role') === 'tooltip');
  help.dispatchEvent({type: 'mouseenter'});
  page.find(el => el.className === 'widget-demo-stage').dispatchEvent({type: 'keydown', key: 'Escape'});
  page.flush(); assert.equal(tip.hidden, true);
  help.click(); assert.equal(tip.hidden, false);
  help.dispatchEvent({type: 'mouseleave'}); page.flush(); assert.equal(tip.hidden, false);
});

test('password reveal reports its toggle state without changing the sample value', async () => {
  const page = await mount('password-input');
  const field = page.find(el => el.tagName === 'input'), reveal = page.button('Show password');
  assert.equal(reveal.getAttribute('aria-pressed'), 'false');
  reveal.click(); assert.equal(field.type, 'text'); assert.equal(reveal.getAttribute('aria-pressed'), 'true');
  reveal.click(); assert.equal(field.type, 'password'); assert.equal(reveal.getAttribute('aria-pressed'), 'false');
  assert.equal(field.value, 'Xu-demo-123');
});

test('toast dismissal restores focus to a visible trigger', async () => {
  const page = await mount('toast-host');
  const trigger = page.button('Show notification'); trigger.click(); page.button('Dismiss').click();
  assert.equal(page.document.activeElement, trigger);
  assert.equal(page.find(el => el.className === 'widget-demo-toast').hidden, true);
});

test('task previews expose busy state and pause cancels completion', async () => {
  for (const slug of ['task-button', 'spinner']) {
    const page = await mount(slug);
    const stage = page.find(el => el.className === 'widget-demo-stage');
    page.button('Start').click(); assert.equal(stage.getAttribute('aria-busy'), 'true');
    page.button('Pause').click(); page.flush();
    assert.equal(stage.getAttribute('aria-busy'), 'false');
    assert.equal(page.find(el => el.getAttribute('role') === 'status').textContent, 'Paused');
  }
});

test('modal names, cancellation and focus return work in both languages', async () => {
  for (const lang of ['en', 'zh-CN']) {
    const page = await mount('modal', lang);
    const trigger = page.button(lang === 'en' ? 'Open confirmation' : '打开确认框'); trigger.click();
    const dialog = page.document.body.children[0];
    assert.equal(dialog.getAttribute('aria-labelledby'), dialog.children[0].id);
    assert.equal(dialog.getAttribute('aria-describedby'), dialog.children[1].id);
    assert.equal(page.document.activeElement.textContent, lang === 'en' ? 'Cancel' : '取消');
    dialog.dispatchEvent({type: 'cancel', preventDefault() {}});
    assert.equal(page.document.activeElement, trigger);
    assert.equal(page.document.body.children.length, 0);
  }
});
