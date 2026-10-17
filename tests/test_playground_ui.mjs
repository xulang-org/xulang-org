// Drive the production UI controller against a worker that never finishes.
// Fake time makes cancellation deterministic; real Xu execution is tested separately.
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {test} from 'node:test';
import assert from 'node:assert/strict';

class Element {
  constructor(tag) {
    this.tag = tag;
    this.children = [];
    this.listeners = {};
    this.attributes = {};
    this.className = '';
    this.classList = {
      contains: name => this.className.split(' ').includes(name),
      add: name => { if (!this.classList.contains(name)) this.className += ' ' + name; },
      remove: name => { this.className = this.className.split(' ').filter(value => value !== name).join(' '); }
    };
  }
  appendChild(child) {
    if (child.parentNode) child.parentNode.children.splice(child.parentNode.children.indexOf(child), 1);
    this.children.push(child);
    child.parentNode = this;
  }
  insertBefore(child, next) {
    this.children.splice(this.children.indexOf(next), 0, child);
    child.parentNode = this;
  }
  matches(selector) { return selector.startsWith('.') ? this.classList.contains(selector.slice(1)) : this.tag === selector; }
  querySelector(selector) {
    for (const child of this.children) {
      if (child.matches(selector)) return child;
      const found = child.querySelector(selector);
      if (found) return found;
    }
    return null;
  }
  closest(selector) { return this.matches(selector) ? this : this.parentNode?.closest(selector); }
  setAttribute(name, value) { this.attributes[name] = value; }
  focus() { this.focused = true; }
  addEventListener(name, handler) { this.listeners[name] = handler; }
  click() { if (!this.disabled) this.listeners.click(); }
}

async function mount({blocks, en = false, available = true, supported = true} = {}) {
  const elements = {};
  for (const id of blocks ? [] : ['src', 'ex', 'run', 'out', 'meta']) {
    elements['xu-play-' + id] = {
      listeners: {}, value: '', disabled: false,
      addEventListener(name, handler) { this.listeners[name] = handler; },
      click() { if (!this.disabled) this.listeners.click(); }
    };
  }
  const timers = new Map();
  const workers = [];
  const fetches = [];
  const copied = [];
  const pageEvents = {};
  const pres = [];
  if (blocks) {
    const main = new Element('main');
    for (const {source, api} of blocks) {
      const pre = new Element('pre');
      const code = new Element('code');
      code.textContent = source;
      pre.appendChild(code);
      pres.push(pre);
      // API pages already have wrappers; docs can contain plain pre elements.
      if (api) {
        const wrapper = new Element('div');
        wrapper.className = 'code-block-wrapper';
        const header = new Element('div');
        header.className = 'code-block-header';
        wrapper.appendChild(header);
        wrapper.appendChild(pre);
        main.appendChild(wrapper);
      } else main.appendChild(pre);
    }
  }
  let nextTimer = 0;
  class Worker {
    constructor(url, options) {
      assert.equal(String(url), 'https://example.org/repo/xu-play-worker.js?v=fixture');
      assert.equal(options.type, 'module');
      this.messages = [];
      workers.push(this);
    }
    postMessage(message) {
      this.messages.push(message);
      if (message.type === 'init') queueMicrotask(() => this.respond({type: 'ready'}));
    }
    respond(data) { this.onmessage({data}); }
    terminate() { this.terminated = true; }
  }
  const context = {
    document: {
      currentScript: {src: 'https://example.org/repo/xu-play.js?v=fixture', getAttribute: () => String(available)},
      documentElement: {lang: en ? 'en' : 'zh-CN', setAttribute() {}}, readyState: 'loading',
      getElementById: id => elements[id],
      createElement: tag => new Element(tag),
      querySelectorAll: () => pres,
      addEventListener(name, handler) { (pageEvents[name] ||= []).push(handler); }
    },
    window: {Worker: supported ? Worker : null, WebAssembly, location: Object.freeze({href: 'https://example.org/repo/zh/docs/tutorial/01/'}), addEventListener() {}}, Worker, URL,
    navigator: {clipboard: {writeText: async value => { copied.push(value); }}},
    fetch: async url => {
      fetches.push(String(url));
      assert.equal(String(url), 'https://example.org/repo/xu-play-examples.json?v=fixture');
      return {ok: true, json: async () => ({hello: {source: '@main', description: {zh: 'Hello', en: 'Hello'}}})};
    },
    setTimeout(handler, delay) { const id = ++nextTimer; timers.set(id, {handler, delay}); return id; },
    clearTimeout(id) { timers.delete(id); }
  };
  if (blocks) vm.runInNewContext(readFileSync(new URL('../www/theme.js', import.meta.url), 'utf8'), context);
  vm.runInNewContext(readFileSync(new URL('../www/xu-play.js?v=fixture', import.meta.url), 'utf8'), context);
  for (const handler of pageEvents.DOMContentLoaded) handler();
  await new Promise(setImmediate);
  return {elements, workers, timers, fetches, pres, context, copied};
}

test('Stop terminates the busy worker, preserves code, and permits another run', async () => {
  const {elements, workers} = await mount();
  const button = elements['xu-play-run'];
  elements['xu-play-src'].value = 'user program';
  button.click();
  assert.match(button.innerHTML, /停止运行/);
  assert.equal(workers[0].messages.at(-1).source, 'user program');
  button.click();
  await new Promise(setImmediate);
  assert.equal(workers[0].terminated, true);
  assert.equal(elements['xu-play-src'].value, 'user program');
  assert.match(elements['xu-play-out'].textContent, /运行已停止/);
  button.click();
  workers[1].respond({type: 'result', exit: 0, stdout: '42\n', stderr: ''});
  assert.equal(elements['xu-play-out'].textContent, '42\n');
  assert.equal(elements['xu-play-meta'].textContent, 'exit 0');
});

test('Timeout terminates execution and late results cannot overwrite the next run', async () => {
  const {elements, workers, timers} = await mount();
  const button = elements['xu-play-run'];
  button.click();
  const timeout = [...timers.values()].find(timer => timer.delay === 10000);
  assert.ok(timeout, 'execution must have a deadline');
  timeout.handler();
  await new Promise(setImmediate);
  assert.equal(workers[0].terminated, true);
  assert.match(elements['xu-play-out'].textContent, /运行超过 10 秒/);
  button.click();
  workers[1].respond({type: 'result', exit: 0, stdout: 'fresh result\n', stderr: ''});
  workers[0].respond({type: 'result', exit: 0, stdout: 'stale result\n', stderr: ''});
  assert.equal(elements['xu-play-out'].textContent, 'fresh result\n');
});

for (const en of [false, true]) {
  test(`Docs and API buttons render independent inline results (${en ? 'en' : 'zh'})`, async () => {
    const {pres, workers, fetches, context} = await mount({en, blocks: [
      {source: 'println("inline")'},
      {source: 'fn main() int { << 3 }', api: true}
    ]});
    assert.equal(workers.length, 0, 'reading a page must not load WASM');
    const wrappers = pres.map(pre => pre.closest('.code-block-wrapper'));
    const buttons = wrappers.map(wrapper => wrapper.querySelector('.code-run-btn'));
    buttons[0].click();
    await new Promise(setImmediate);
    assert.match(workers[0].messages.at(-1).source, /^@main\n\nfn main\(\) int \{/);
    assert.match(workers[0].messages.at(-1).source, /println\("inline"\)/);
    buttons[1].click();
    await new Promise(setImmediate);
    assert.equal(workers[1].messages.at(-1).source, '@main\n\nfn main() int { << 3 }');
    workers[1].respond({type: 'result', exit: 3, stdout: '', stderr: 'error: invalid code\n'});
    workers[0].respond({type: 'result', exit: 0, stdout: '<script>output is text</script>\n', stderr: ''});
    assert.equal(wrappers[0].querySelector('.xu-play-out').textContent, '<script>output is text</script>\n');
    assert.equal(wrappers[0].querySelector('.xu-play-meta').textContent, 'exit 0');
    assert.match(wrappers[1].querySelector('.xu-play-out').className, /is-err/);
    assert.equal(wrappers[1].querySelector('.xu-play-out').textContent, 'error: invalid code\n');
    assert.equal(wrappers[1].querySelector('.xu-play-meta').textContent, 'exit 3');
    assert.equal(buttons[0].attributes['aria-expanded'], 'true');
    assert.notEqual(buttons[0].attributes['aria-controls'], buttons[1].attributes['aria-controls']);
    assert.equal(workers[0].terminated, true, 'completed inline workers must release their memory');
    assert.equal(workers[1].terminated, true);
    assert.deepEqual(fetches, [], 'inline runs do not need playground examples');
    assert.equal(context.window.location.href, 'https://example.org/repo/zh/docs/tutorial/01/');
    buttons[0].click();
    await new Promise(setImmediate);
    workers[2].respond({type: 'result', exit: 0, stdout: '', stderr: '', truncated: true});
    assert.match(wrappers[0].querySelector('.xu-play-out').textContent, en ? /Output truncated/ : /输出过长/);
    assert.equal(wrappers[0].children.filter(child => child.className === 'code-run-result').length, 1);
  });
}

test('Inline stop, timeout, and retry ignore late results', async () => {
  const {pres, workers, timers} = await mount({blocks: [{source: '@main\nfn main() int { for {} }'}]});
  const wrapper = pres[0].closest('.code-block-wrapper');
  const button = wrapper.querySelector('.code-run-btn');
  const output = () => wrapper.querySelector('.xu-play-out');
  button.click();
  await new Promise(setImmediate);
  button.click();
  assert.equal(workers[0].terminated, true);
  assert.match(output().textContent, /运行已停止/);
  button.click();
  await new Promise(setImmediate);
  [...timers.values()].find(timer => timer.delay === 10000).handler();
  assert.equal(workers[1].terminated, true);
  assert.match(output().textContent, /运行超过 10 秒/);
  button.click();
  await new Promise(setImmediate);
  workers[2].respond({type: 'error', message: 'Failed to fetch WASM'});
  assert.equal(button.textContent, '重试');
  assert.equal(workers[2].terminated, true);
  button.click();
  await new Promise(setImmediate);
  workers[3].respond({type: 'result', exit: 0, stdout: 'recovered\n', stderr: ''});
  workers[0].respond({type: 'result', exit: 0, stdout: 'stale\n', stderr: ''});
  assert.equal(output().textContent, 'recovered\n');
});

test('Unavailable WASM and unsupported browsers show inline feedback without starting workers', async () => {
  for (const options of [{available: false}, {supported: false}]) {
    const {pres, workers} = await mount({...options, blocks: [{source: 'println(1)'}]});
    const wrapper = pres[0].closest('.code-block-wrapper');
    wrapper.querySelector('.code-run-btn').click();
    assert.match(wrapper.querySelector('.xu-play-out').textContent, options.available === false ? /暂未启用/ : /此浏览器不支持/);
    assert.equal(workers.length, 0);
  }
});

test('Shell commands retain Copy without a Run action', async () => {
  const {pres} = await mount({blocks: [{source: 'xu run main.xu'}]});
  const wrapper = pres[0].closest('.code-block-wrapper');
  assert.ok(wrapper.querySelector('.code-copy-btn'));
  assert.equal(wrapper.querySelector('.code-run-btn'), null);
  assert.equal(wrapper.querySelector('.code-edit-btn'), null);
});

for (const en of [false, true]) {
  test(`Editing docs and API code updates every run and copy (${en ? 'en' : 'zh'})`, async () => {
    const {pres, workers, copied} = await mount({en, blocks: [
      {source: 'println("original docs")'},
      {source: 'pub fn example(x int) int', api: true}
    ]});
    const wrappers = pres.map(pre => pre.closest('.code-block-wrapper'));
    const edit = wrappers[0].querySelector('.code-edit-btn');
    const run = wrappers[0].querySelector('.code-run-btn');
    assert.equal(wrappers[0].querySelector('.code-block-editor'), null);
    run.click();
    await new Promise(setImmediate);
    workers[0].respond({type: 'result', exit: 0, stdout: 'original docs\n', stderr: ''});
    edit.click();
    const editor = wrappers[0].querySelector('.code-block-editor');
    assert.equal(editor.focused, true);
    assert.equal(editor.hidden, false);
    assert.equal(pres[0].hidden, true);
    assert.equal(editor.value, 'println("original docs")');
    assert.equal(edit.attributes['aria-pressed'], 'true');
    assert.match(edit.innerHTML, en ? /Done/ : /完成/);
    editor.value = 'println("first edit")';
    run.click();
    editor.value = 'println("second edit")';
    await new Promise(setImmediate);
    assert.match(workers[1].messages.at(-1).source, /first edit/);
    assert.doesNotMatch(workers[1].messages.at(-1).source, /second edit/);
    workers[1].respond({type: 'result', exit: 0, stdout: 'first edit\n', stderr: ''});
    let prevented = false;
    editor.listeners.keydown({key: 'Enter', metaKey: true, preventDefault() { prevented = true; }});
    await new Promise(setImmediate);
    assert.equal(prevented, true);
    assert.match(workers[2].messages.at(-1).source, /second edit/);
    workers[2].respond({type: 'result', exit: 0, stdout: 'second edit\n', stderr: ''});
    wrappers[0].querySelector('.code-copy-btn').click();
    await new Promise(setImmediate);
    assert.deepEqual(copied, ['println("second edit")']);
    edit.click();
    assert.equal(editor.hidden, true);
    assert.equal(pres[0].hidden, false);
    assert.equal(pres[0].querySelector('code').textContent, editor.value);
    assert.equal(edit.attributes['aria-pressed'], 'false');
    edit.click();
    assert.equal(editor.value, 'println("second edit")', 'reopening must preserve changes');
    assert.equal(wrappers[0].children.filter(child => child.className === 'code-block-editor').length, 1);

    wrappers[1].querySelector('.code-edit-btn').click();
    const apiEditor = wrappers[1].querySelector('.code-block-editor');
    assert.equal(apiEditor.value, 'pub fn example(x int) int');
    assert.notEqual(editor.id, apiEditor.id);
    apiEditor.value = '@main\nfn main() int {\n    println("edited API")\n    << 0\n}';
    wrappers[1].querySelector('.code-run-btn').click();
    await new Promise(setImmediate);
    assert.equal(workers[3].messages.at(-1).source, apiEditor.value);
    assert.equal(editor.value, 'println("second edit")', 'editing API code must not change another block');
  });
}

test('Import snippets can be edited and keep imports outside the generated main function', async () => {
  const {pres, workers} = await mount({blocks: [{source: '#errors\nprintln("imported")'}]});
  const wrapper = pres[0].closest('.code-block-wrapper');
  assert.ok(wrapper.querySelector('.code-edit-btn'));
  wrapper.querySelector('.code-run-btn').click();
  await new Promise(setImmediate);
  assert.equal(workers[0].messages.at(-1).source,
    '@main\n\n#errors\n\nfn main() int {\n    println("imported")\n    << 0\n}\n');
});
