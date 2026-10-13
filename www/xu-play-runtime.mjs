// Host bridge only: Xu source is parsed, checked and interpreted inside WASM.
export async function createRuntime(bytes) {
  const module = await WebAssembly.compile(bytes);
  if (WebAssembly.Module.imports(module).length) {
    throw new Error('Xu playground unexpectedly requires host imports');
  }
  const exports = WebAssembly.Module.exports(module);
  if (!exports.some(item => item.name === 'xu_eval_frame' && item.kind === 'function') ||
      !exports.some(item => item.name === 'memory' && item.kind === 'memory')) {
    throw new Error('Missing Xu WASM exports');
  }
  if (!WebAssembly.Module.customSections(module, 'xu.source').length) {
    throw new Error('Missing Xu build provenance');
  }
  const decoder = new TextDecoder('utf-8');

  return {
    run(source) {
      const input = new TextEncoder().encode(source);
      if (input.length > 128 * 1024) throw new Error('Source exceeds 128 KiB');
      // A fresh arena for each evaluation also recovers from parser/checker traps.
      const exp = new WebAssembly.Instance(module, {}).exports;
      const memory = exp.memory.buffer;
      const view = new DataView(memory);
      new Uint8Array(memory, 2048, input.length).set(input);
      view.setBigInt64(800, 2048n, true);
      view.setBigInt64(792, BigInt(input.length), true);
      view.setBigInt64(1040, 16n * 1024n * 1024n, true);
      let exit;
      let trap;
      try {
        exp.xu_eval_frame(800, 768);
        exit = Number(view.getBigInt64(768, true));
      } catch (error) {
        if (!(error instanceof WebAssembly.RuntimeError)) throw error;
        trap = error;
        exit = 1;
      }
      const decode = (ptr, slot) => {
        const n = view.getBigInt64(slot, true);
        if (n < 0n || n > 262144n) throw new Error('Invalid Xu output buffer');
        return decoder.decode(new Uint8Array(memory, ptr, Number(n)));
      };
      const stdout = decode(150000, 1024);
      let stderr = decode(450000, 1032);
      if (trap && !stderr) {
        stderr = view.getBigInt64(1048, true) > 0n
          ? 'Xu playground memory limit exceeded\n'
          : 'Xu WASM execution stopped: ' + trap.message + '\n';
      }
      return {exit, stdout, stderr, truncated:
        view.getBigInt64(1024, true) === 262144n || view.getBigInt64(1032, true) === 262144n};
    }
  };
}
