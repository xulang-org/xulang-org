// Execute the production runtime with the real compiled Xu WASM and UI examples.
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createRuntime} from '../www/xu-play-runtime.mjs';

const bytes = readFileSync(new URL('../www/xu-play.wasm', import.meta.url));
const examples = JSON.parse(readFileSync(new URL('../www/xu-play-examples.json', import.meta.url), 'utf8'));
const expected = {
  hello: 'Hello from XU Programming Language!\n',
  bindings: 'Xu\n21\n100\n',
  control: 'minor\nteen\n3\n2\n1\n0\n1\n2\n3\n4\n',
  ints: '42\n10\n11\n'
};

for (const [name, source] of Object.entries(examples)) {
  test('homepage example: ' + name, async () => {
    const runtime = await createRuntime(bytes);
    const result = runtime.run(source);
    assert.equal(result.exit, 0, result.stderr);
    assert.equal(result.stdout, expected[name]);
    assert.equal(result.stderr, '');
  });
}

test('user edits execute as Xu and compiler diagnostics recover', async () => {
  const runtime = await createRuntime(bytes);
  const edited = runtime.run('@main\nfn main() int {\n println("你好 Xu")\n << 7\n }');
  assert.equal(edited.exit, 7);
  assert.equal(edited.stdout, '你好 Xu\n');
  const broken = runtime.run('fn main() int { println(\n');
  assert.notEqual(broken.exit, 0);
  assert.match(broken.stderr, /error:/);
  assert.equal(broken.stdout, '');
  assert.equal(runtime.run(examples.hello).stdout, expected.hello);
});

test('embedded errors import runs; unsupported imports report a real error', async () => {
  const runtime = await createRuntime(bytes);
  const supported = runtime.run(examples.hello.replace('@main', '@main\n#errors'));
  assert.equal(supported.exit, 0, supported.stderr);
  const unsupported = runtime.run('@main\n#os\nfn main() int { << 0 }');
  assert.notEqual(unsupported.exit, 0);
  assert.match(unsupported.stderr, /import.*os|module not found/);
});

test('empty source and oversized source are bounded', async () => {
  const runtime = await createRuntime(bytes);
  assert.notEqual(runtime.run('').exit, 0);
  assert.throws(() => runtime.run('x'.repeat(128 * 1024 + 1)), /128 KiB/);
});
