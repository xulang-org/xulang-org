import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createRuntime} from '../www/xu-play-runtime.mjs';
const runtime = await createRuntime(readFileSync(new URL('../build/playground/xu-play.wasm',import.meta.url)));
test('native scalar map ABI preserves keys, updates, misses and deletes in WASM', () => {
  const result = runtime.run(`@main
fn main() int {
 $ints := map[int]int{}
 ints[7] = 3
 ints[7] = 9
 assert(ints[7] == 9)
 assert(ints.get_or(8,42) == 42)
 assert(ints.has(7))
 assert(!ints.has(8))
 assert(ints.len() == 1)
 ints.delete(7)
 assert(!ints.has(7))
 $names := map[string]bool{}
 names["你好"] = true
 names["Xu"] = false
 assert(names["你好"])
 assert(!names["Xu"])
 assert(names.has("Xu"))
 assert(names.get_or("missing",true))
 println("scalar maps passed")
 << 0
}`);
  assert.equal(result.exit,0,result.stderr);
  assert.equal(result.stdout,'scalar maps passed\n');
});
test('owned map values follow the released compiler semantics', () => {
  const result = runtime.run('@main\nfn main() int { $values := map[int]string{}\nvalues[1] = "owner"\nprintln(values[1])\n<< 0 }');
  assert.equal(result.exit,0,result.stderr);
  assert.equal(result.stdout,'owner\n');
  assert.equal(runtime.run('@main\nfn main() int { println(42)\n<< 0 }').stdout,'42\n');
});
