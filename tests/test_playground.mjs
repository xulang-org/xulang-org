// Execute the production runtime with the real compiled Xu WASM and UI examples.
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createRuntime} from '../www/xu-play-runtime.mjs';

const bytes = readFileSync(new URL('../build/playground/xu-play.wasm', import.meta.url));
const examples = JSON.parse(readFileSync(new URL('../www/xu-play-examples.json', import.meta.url), 'utf8'));
const expected = {
  hello: 'Hello from XU Programming Language!\n',
  bindings: 'Xu\n21\n100\n',
  arithmetic: '22\n12\n85\n3\n2\ntrue\nfalse\n',
  strings: 'Hello, Xu\n你好，Xu\nanswer = 42\n',
  conditions: 'passed\n',
  matching: 'teen\n',
  loops: '15\n3\n2\n1\n',
  loop_control: '1\n3\n5\n',
  recursion: '720\n',
  arrays: '3\n4\n12\n',
  enums: 'red\ngreen\n1\n2\n3\n',
  structs: '10\n11\n',
  assertions: 'check passed\n',
  control: 'minor\nteen\n3\n2\n1\n0\n1\n2\n3\n4\n',
  ints: '42\n7\n',
  'chan-buffered': '42\n',
  'chan-workers': '60\n',
  'chan-pipeline': '1\n4\n9\n16\n25\n'
};

for (const [name, example] of Object.entries(examples)) {
  test('homepage example: ' + name, async () => {
    const runtime = await createRuntime(bytes);
    const result = runtime.run(example.source);
    if (name === 'borrow') {
      assert.notEqual(result.exit, 0);
      assert.match(result.stderr, /cannot assign.*borrowed/);
      assert.equal(result.stdout, '');
      return;
    }
    assert.equal(result.exit, 0, result.stderr);
    assert.equal(result.stdout, expected[name]);
    if (name === 'recursion') assert.match(result.stderr, /warning: recursive call cycle/);
    else assert.equal(result.stderr, '');
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
  assert.equal(runtime.run(examples.hello.source).stdout, expected.hello);
});

test('embedded errors import runs; unsupported imports report a real error', async () => {
  const runtime = await createRuntime(bytes);
  const supported = runtime.run(examples.hello.source.replace('@main', '@main\n#errors'));
  assert.equal(supported.exit, 0, supported.stderr);
  const unsupported = runtime.run('@main\n#os\nfn main() int { << 0 }');
  assert.notEqual(unsupported.exit, 0);
  assert.match(unsupported.stderr, /module.*os.*not found/);
});

test('empty source and oversized source are bounded', async () => {
  const runtime = await createRuntime(bytes);
  assert.notEqual(runtime.run('').exit, 0);
  assert.throws(() => runtime.run('x'.repeat(128 * 1024 + 1)), /128 KiB/);
});


test('WASM is built from Xu and has no host evaluator imports', async () => {
  const module = await WebAssembly.compile(bytes);
  assert.deepEqual(WebAssembly.Module.imports(module), []);
  assert.ok(WebAssembly.Module.customSections(module, 'xu.source').length);
  assert.ok(WebAssembly.Module.exports(module).some(item => item.name === 'xu_eval_frame'));
});

test('unbuffered chan rendezvous and repeated evaluation', async () => {
  const runtime = await createRuntime(bytes);
  const result = runtime.run(`@main
fn send(ch chan int) { ch <- 42 }
fn main() int {
 ch := chan int{cap: 0}
 xu send(ch)
 println(<-ch)
 << 0
}`);
  assert.equal(result.exit, 0, result.stderr);
  assert.equal(result.stdout, '42\n');
  assert.equal(runtime.run(examples.hello.source).stdout, expected.hello);
});

test('chan deadlock reports a diagnostic and permits a fresh run', async () => {
  const runtime = await createRuntime(bytes);
  const result = runtime.run(`@main
fn main() int {
 ch := chan int{cap: 1}
 println(<-ch)
 << 0
}`);
  assert.notEqual(result.exit, 0);
  assert.match(result.stderr, /channel deadlock/);
  assert.equal(runtime.run(examples['chan-workers'].source).stdout, '60\n');
});

test('by-value strings and multi-slot structs follow the Xu ABI', async () => {
  const runtime = await createRuntime(bytes);
  const result = runtime.run(`@main
struct Pair { a int
 b int }
fn sum(p Pair, s string) int { println(s)
 << p.a + p.b }
fn main() int { println(sum(Pair{a: 17, b: 25}, "参数传递"))
 << 0 }
`);
  assert.equal(result.exit, 0, result.stderr);
  assert.equal(result.stdout, '参数传递\n42\n');
});


test('unsupported floating-point execution fails explicitly', async () => {
  const runtime = await createRuntime(bytes);
  const result = runtime.run('@main\nfn main() int { println(1.5)\n << 0 }');
  assert.notEqual(result.exit, 0);
  assert.match(result.stderr, /floating-point.*not supported/);
  const comparison = runtime.run('@main\nfn main() int { println(1.5 < 2.0)\n << 0 }');
  assert.notEqual(comparison.exit, 0);
  assert.match(comparison.stderr, /floating-point.*not supported/);
});
