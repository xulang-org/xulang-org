import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {test} from 'node:test';
import assert from 'node:assert/strict';

test('Canvas keeps logical geometry when high-density drawing resets its transform', () => {
  const host = {};
  vm.runInNewContext(readFileSync(new URL('../www/xu-play-canvas.js', import.meta.url), 'utf8'), host);
  const transforms = [];
  const context = new Proxy({}, {get: (_, method) => (...args) => {
    if (method === 'setTransform') transforms.push(args);
  }});
  let staging;
  const canvas = {ownerDocument: {
    defaultView: {devicePixelRatio: 2},
    createElement: () => (staging = {getContext: () => context}),
  }, getContext: () => context};
  assert.equal(host.XuPlayCanvas.render(canvas,
    'begin\ntranslate\t12\t24\norigin\nbgcolor\t#100e12\npresent\n'), true);
  assert.equal(canvas.width, 1280);
  assert.equal(canvas.height, 720);
  assert.equal(staging.width, canvas.width);
  assert.deepEqual(transforms, Array(3).fill([2, 0, 0, 2, 0, 0]));
  assert.equal(host.XuPlayCanvas.width, 640);
  assert.equal(host.XuPlayCanvas.height, 360);
  canvas.ownerDocument.defaultView.devicePixelRatio = 99;
  host.XuPlayCanvas.render(canvas, 'begin\npresent\n');
  assert.equal(canvas.width, 1920);
});
