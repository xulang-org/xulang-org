// Xu's actual WASM ABI; shared by the browser worker and execution tests.
export async function createRuntime(bytes) {
  const module = await WebAssembly.compile(bytes);
  if (WebAssembly.Module.imports(module).length) {
    throw new Error('Xu playground unexpectedly requires host imports');
  }
  const instance = await WebAssembly.instantiate(module, {});
  const exp = instance.exports;
  for (const name of ['xu_alloc', 'xu_free', 'xu_eval', 'xu_stdout_ptr',
    'xu_stdout_len', 'xu_stderr_ptr', 'xu_stderr_len']) {
    if (typeof exp[name] !== 'function') throw new Error('Missing Xu export: ' + name);
  }
  if (!(exp.memory instanceof WebAssembly.Memory)) throw new Error('Missing Xu memory');
  const decoder = new TextDecoder('utf-8');

  function decode(ptr, length) {
    ptr >>>= 0;
    length >>>= 0;
    if (!length) return {text: '', truncated: false};
    if (length === 0xffffffff || !ptr || ptr + length > exp.memory.buffer.byteLength) {
      throw new Error('Invalid Xu output buffer');
    }
    const shown = Math.min(length, 256 * 1024);
    return {text: decoder.decode(new Uint8Array(exp.memory.buffer, ptr, shown)), truncated: shown < length};
  }

  return {
    run(source) {
      const input = new TextEncoder().encode(source);
      if (input.length > 128 * 1024) throw new Error('Source exceeds 128 KiB');
      const ptr = exp.xu_alloc(input.length) >>> 0;
      if (input.length && !ptr) throw new Error('Could not allocate Xu source buffer');
      try {
        new Uint8Array(exp.memory.buffer, ptr, input.length).set(input);
        const exit = exp.xu_eval(ptr, input.length);
        const out = decode(exp.xu_stdout_ptr(), exp.xu_stdout_len());
        const err = decode(exp.xu_stderr_ptr(), exp.xu_stderr_len());
        return {exit, stdout: out.text, stderr: err.text, truncated: out.truncated || err.truncated};
      } finally {
        exp.xu_free(ptr, input.length);
      }
    }
  };
}
