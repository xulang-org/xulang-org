import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createRuntime} from '../www/xu-play-runtime.mjs';

const module = await WebAssembly.compile(readFileSync(new URL('../build/playground/xu-play.wasm', import.meta.url)));
const projects = JSON.parse(readFileSync(new URL('../www/xu-play-examples.json', import.meta.url), 'utf8')).projects;
const click = (x, y) => [{kind: 72, x, y, button: 1, buttons: 1}, {kind: 73, x, y, button: 1, buttons: 0}];
for (const [slug, events, output] of [
  ['button', click(100, 124), 'Count: 1\n'],
  ['checkbox', click(100, 124), 'Value: true\n'],
  ['switch', click(100, 124), 'Value: true\n'],
  ['radio', click(100, 124), 'Value: true\n'],
  ['tabs', click(280, 124), 'Selected: 1\n'],
  ['progress', click(100, 280), 'Progress: 50\n'],
  ['badge', click(100, 280), 'Count: 1\n'],
]) {
  test('component experience responds through Xu widget logic: ' + slug, async () => {
    const runtime = await createRuntime(module);
    const result = runtime.run(projects['widget-' + slug].files['main.xu'], {events});
    assert.equal(result.exit, 0, result.stderr);
    assert.equal(result.stdout, output);
    assert.ok(result.ui.commands.length);
  });
}
