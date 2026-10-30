// Run the production browser worker in a fresh thread with file-backed fetch.
// The shim supplies browser plumbing only; compilation and execution use WASM.
import {readFileSync} from 'node:fs';
import {Worker} from 'node:worker_threads';
import {once} from 'node:events';
import {test} from 'node:test';
import assert from 'node:assert/strict';

test('cold worker initializes silently and executes the requested component', {timeout: 90000}, async () => {
  const workerURL = new URL('../www/xu-play-worker.js', import.meta.url).href;
  const wasmURL = new URL('../build/playground/xu-play.wasm', import.meta.url).href;
  const bootstrap = `
    import {parentPort} from 'node:worker_threads';
    import {readFile} from 'node:fs/promises';
    globalThis.self = {location: new URL(${JSON.stringify(workerURL)}),
      postMessage: value => parentPort.postMessage(value)};
    globalThis.fetch = async () => new Response(await readFile(new URL(${JSON.stringify(wasmURL)})),
      {headers: {'Content-Type': 'application/wasm'}});
    await import(${JSON.stringify(workerURL)});
    parentPort.on('message', data => self.onmessage({data}));
    parentPort.postMessage({type: 'booted'});
  `;
  const worker = new Worker(new URL('data:text/javascript,' + encodeURIComponent(bootstrap)));
  try {
    assert.deepEqual((await once(worker, 'message'))[0], {type: 'booted'});
    const ready = once(worker, 'message');
    worker.postMessage({type: 'init'});
    assert.deepEqual((await ready)[0], {type: 'ready'});
    const result = once(worker, 'message');
    worker.postMessage({type: 'run', source: readFileSync(new URL('../playground/examples/widget-button.xu', import.meta.url), 'utf8'),
      events: [{kind: 72, x: 100, y: 124, button: 1}, {kind: 73, x: 100, y: 124, button: 1}]});
    const value = (await result)[0];
    assert.equal(value.type, 'result', value.message);
    assert.equal(value.exit, 0, value.stderr);
    assert.equal(value.stdout, 'Count: 1\n');
    assert.ok(value.ui.commands.length);
  } finally { await worker.terminate(); }
});
