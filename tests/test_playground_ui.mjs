// Drive the production UI controller against a worker that never finishes.
// Fake time makes cancellation deterministic; real Xu execution is tested separately.
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {test} from 'node:test';
import assert from 'node:assert/strict';

async function mount() {
  const elements = {};
  for (const id of ['src', 'ex', 'run', 'out', 'meta']) {
    elements['xu-play-' + id] = {
      listeners: {}, value: '', disabled: false,
      addEventListener(name, handler) { this.listeners[name] = handler; },
      click() { if (!this.disabled) this.listeners.click(); }
    };
  }
  const timers = new Map();
  const workers = [];
  let nextTimer = 0;
  class Worker {
    constructor(url, options) {
      assert.equal(String(url), 'https://example.org/repo/xu-play-worker.js');
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
      currentScript: {src: 'https://example.org/repo/xu-play.js', getAttribute: () => 'true'},
      documentElement: {lang: 'zh-CN'}, readyState: 'complete',
      getElementById: id => elements[id]
    },
    window: {Worker, WebAssembly, addEventListener() {}}, Worker, URL,
    fetch: async url => {
      assert.equal(String(url), 'https://example.org/repo/xu-play-examples.json');
      return {ok: true, json: async () => ({hello: '@main'})};
    },
    setTimeout(handler, delay) { const id = ++nextTimer; timers.set(id, {handler, delay}); return id; },
    clearTimeout(id) { timers.delete(id); }
  };
  vm.runInNewContext(readFileSync(new URL('../www/xu-play.js', import.meta.url), 'utf8'), context);
  await new Promise(setImmediate);
  return {elements, workers, timers};
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
