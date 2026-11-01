#!/usr/bin/env node
// Reproducible production-worker benchmark. No browser or npm dependencies.
// Build first; see playground/README.md. Timings are milliseconds, mock Canvas
// measures host work/call counts, not GPU rasterization or browser presentation.
import {readFileSync} from 'node:fs';
import {Worker, isMainThread, parentPort, workerData} from 'node:worker_threads';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';

const now = () => performance.timeOrigin + performance.now();
if (!isMainThread) {
  let receivedAt;
  globalThis.self = {
    location: {href: new URL('../www/xu-play-worker.js', import.meta.url).href, search: ''},
    postMessage(message) {
      const sendAt = now();
      parentPort.postMessage({...message, receivedAt, sendAt});
      if (message.type === 'result') parentPort.postMessage({type: 'posted', serializeMs: now() - sendAt});
    }
  };
  globalThis.fetch = async () => new Response(readFileSync(workerData.wasm), {headers: {'Content-Type': 'application/wasm'}});
  await import('../www/xu-play-worker.js');
  parentPort.on('message', data => {
    receivedAt = now();
    self.onmessage({data});
  });
} else {
  const options = Object.fromEntries(process.argv.slice(2).map(arg => {
    const [key, ...value] = arg.replace(/^--/, '').split('=');
    return [key, value.join('=')];
  }));
  const wasm = fileURLToPath(new URL(options.wasm || '../build/playground/xu-play.wasm', import.meta.url));
  const example = options.example || 'ui-gallery';
  const rounds = Number(options.rounds || 3), clicks = Number(options.clicks || 3);
  assert.ok(rounds > 0 && Number.isInteger(rounds) && clicks > 0 && clicks <= 31 && Number.isInteger(clicks));
  const project = JSON.parse(readFileSync(new URL('../www/xu-play-examples.json', import.meta.url))).projects[example];
  const source = project?.files[project.entry];
  assert.ok(['ui-gallery', 'ui-counter', 'widget-color-picker'].includes(example) && source,
    'Use ui-gallery, ui-counter or widget-color-picker');
  const context = {};
  vm.runInNewContext(readFileSync(new URL('../www/xu-play-canvas.js', import.meta.url), 'utf8'), context);
  const host = context.XuPlayCanvas;
  let calls = {};
  const ctx = new Proxy({}, {get(_, key) { return (...args) => {
    calls[key] = (calls[key] || 0) + 1;
    if (key === 'measureText') return {width: [...args[0]].length * 9.6};
  }; }, set() { return true; }});
  const canvas = {getContext: () => ctx, ownerDocument: {createElement: () => ({getContext: () => ctx})}};
  const worker = new Worker(new URL(import.meta.url), {workerData: {wasm}});
  let resolveMessage, rejectMessage;
  worker.on('error', error => rejectMessage?.(error));
  worker.on('message', message => resolveMessage?.({...message, arrivedAt: now()}));
  const receive = () => new Promise((resolve, reject) => { resolveMessage = resolve; rejectMessage = reject; });
  async function request(message) {
    const waiting = receive();
    const sentAt = now();
    worker.postMessage(message);
    const inputSerializeMs = now() - sentAt;
    const result = await waiting;
    if (result.type === 'error') throw Error(result.message);
    return {result, sentAt, inputSerializeMs};
  }
  const samples = [];
  try {
    const init = {type: 'init', cache: options.cache !== 'false', checkpoints: options.checkpoints !== 'false'};
    const loading = await request(init);
    const loadMs = loading.result.arrivedAt - loading.sentAt;
    for (let round = 0; round < rounds; round++) {
      // Each round starts a new source session, including one cold compile.
      if (round) await request(init);
      const events = [];
      const stages = [{stage: 'initial', events: []}];
      if (example === 'widget-color-picker') {
        events.push({kind:72,x:280,y:182,button:1,buttons:1});
        stages.push({stage:'drag-down',events:events.slice()});
        for (let move=1;move<=clicks;move++) {
          events.push({kind:74,x:280+move*120/clicks,y:182,buttons:1});
          stages.push({stage:'drag-'+move,events:events.slice()});
        }
        events.push({kind:73,x:400,y:182,button:1});
        stages.push({stage:'drag-up',events:events.slice()});
      } else {
      for (let click = 1; click <= clicks; click++) {
        if (example === 'ui-gallery') {
          events.push({kind: 72, x: 100, y: 125, button: 1, buttons: 1});
          stages.push({stage: 'down-' + click, events: events.slice()});
          events.push({kind: 73, x: 100, y: 125, button: 1});
        } else events.push({x: 320, y: 200});
        stages.push({stage: 'click-' + click, events: events.slice()});
      }
      // The jump to 63 records measures a large burst. 63 -> 64 measures a
      // single new input at the session limit, separately from that burst.
      for (const n of [16, 63, 64]) stages.push({stage: 'history-' + n, events: Array.from({length: n}, (_, i) =>
        example === 'ui-gallery' ? (i % 2 ? {kind:73,x:100,y:125,button:1} :
          {kind:72,x:100,y:125,button:1,buttons:1}) : {x: 320, y: 200})});
      }
      for (const {stage, events} of stages) {
        const {result, sentAt, inputSerializeMs} = await request({type: 'run', source, events, profile: true});
        const posted = receive(); // second worker message carries measured postMessage time
        assert.equal(result.exit, 0, result.stderr);
        const expected = example === 'ui-gallery' ? Math.floor(events.length / 2) : events.length;
        if (example === 'widget-color-picker') assert.match(result.stdout,/^Color: #[0-9A-F]{8}\n$/);
        else assert.match(result.stdout, new RegExp('Count: ' + expected + '(?:\\n| \\|)'));
        assert.ok(result.ui?.commands);
        calls = {};
        let t = performance.now();
        const display = host.frame(result.ui.commands);
        const commandDecodeMs = performance.now() - t;
        t = performance.now();
        host.draw(canvas, display);
        const canvasMs = performance.now() - t;
        const paintDoneAt = now();
        const {serializeMs} = await posted;
        samples.push({round, stage, events: events.length, ...result.timings,
          inputSerializeMs, inputTransitMs: result.receivedAt - sentAt,
          outputSerializeMs: serializeMs, outputTransitMs: result.arrivedAt - result.sendAt,
          commandDecodeMs, canvasMs, interactionMs: paintDoneAt - sentAt,
          commandBytes: Buffer.byteLength(result.ui.commands),
          commandLines: result.ui.commands.trimEnd().split('\n').length,
          frameCommands: display.length, canvasCalls: Object.values(calls).reduce((a,b) => a+b, 0), calls});
      }
    }
    const median = values => { const a = values.slice().sort((a,b) => a-b); return a[Math.floor(a.length/2)]; };
    const summary = [...new Set(samples.map(s => s.stage))].map(stage => {
      const rows = samples.filter(s => s.stage === stage);
      return Object.fromEntries(Object.keys(rows[0]).filter(k => k !== 'calls' && k !== 'round').map(k =>
        [k, typeof rows[0][k] === 'number' ? median(rows.map(s => s[k])) : rows[0][k]]));
    });
    console.log(JSON.stringify({node: process.version, platform: process.platform, arch: process.arch,
      wasm, example, rounds, clicks, cache: init.cache, checkpoints: init.checkpoints,
      wasmSha256: createHash('sha256').update(readFileSync(wasm)).digest('hex'),
      sourceSha256: createHash('sha256').update(source).digest('hex'),
      xuVersion: readFileSync(new URL('../VERSION',import.meta.url),'utf8').trim(),
      loadMs, summary, samples}, null, 2));
  } finally { await worker.terminate(); }
}
