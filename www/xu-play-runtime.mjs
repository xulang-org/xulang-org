// Host bridge only: Xu source is parsed, checked and interpreted inside WASM.
export const MAX_UI_EVENTS = 64;
export async function createRuntime(bytesOrModule) {
  const module = (bytesOrModule instanceof WebAssembly.Module)
    ? bytesOrModule
    : await WebAssembly.compile(bytesOrModule);
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
    run(source, {events = []} = {}) {
      const input = new TextEncoder().encode(source);
      if (input.length > 128 * 1024) throw new Error('Source exceeds 128 KiB');
      if (!Array.isArray(events) || events.length > MAX_UI_EVENTS) throw new Error('UI event limit exceeded (64)');
      for (const event of events) {
        if (!event || !Number.isInteger(event.x ?? 0) || !Number.isInteger(event.y ?? 0) ||
            Math.abs(event.x ?? 0) > 100000 || Math.abs(event.y ?? 0) > 100000 ||
            (event.kind === undefined && (!Number.isInteger(event.x) || !Number.isInteger(event.y) ||
              event.x < 0 || event.x >= 640 || event.y < 0 || event.y >= 360))) {
          throw new Error('Invalid UI click coordinates');
        }
        if (event.kind !== undefined && ![72, 73, 74, 75, 76, 77, 78, 79, 80].includes(event.kind)) throw new Error('Invalid UI event kind');
        for (const field of ['dx', 'dy']) {
          if (!Number.isFinite(event[field] ?? 0) || Math.abs(event[field] ?? 0) > 100000) throw new Error('Invalid UI scroll delta');
        }
        for (const field of ['key', 'modifiers', 'repeat', 'button', 'buttons']) {
          if (!Number.isInteger(event[field] ?? 0) || (event[field] ?? 0) < 0 || (event[field] ?? 0) > 65535) throw new Error('Invalid UI event field');
        }
      }
      // A fresh arena for each evaluation also recovers from parser/checker traps.
      const exp = new WebAssembly.Instance(module, {}).exports;
      const memory = exp.memory.buffer;
      const view = new DataView(memory);
      new Uint8Array(memory, 2048, input.length).set(input);
      view.setBigInt64(800, 2048n, true);
      view.setBigInt64(792, BigInt(input.length), true);
      view.setBigInt64(1040, 16n * 1024n * 1024n, true);
      view.setBigInt64(1064, BigInt(events.length), true);
      events.forEach((event, index) => {
        const values = [event.kind ?? 0, event.x ?? 0, event.y ?? 0, event.key ?? 0,
          event.modifiers ?? 0, event.repeat ?? 0, event.button ?? 0, event.buttons ?? 0];
        view.setFloat64(1000000 + index * 80 + 64, event.dx ?? 0, true);
        view.setFloat64(1000000 + index * 80 + 72, event.dy ?? 0, true);
        values.forEach((value, slot) => view.setBigInt64(1000000 + index * 80 + slot * 8, BigInt(value), true));
      });
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
      if (trap) {
        stderr += view.getBigInt64(1048, true) > 0n
          ? 'Xu playground memory limit exceeded\n'
          : 'Xu WASM execution stopped: ' + trap.message + '\n';
      }
      const commands = decode(720000, 1056);
      return {exit, stdout, stderr, ui: exit === 0 && commands ? {
        commands, input: view.getBigInt64(1088, true) !== 0n, interactive: view.getBigInt64(1080, true) !== 0n
      } : null, truncated:
        view.getBigInt64(1024, true) === 262144n || view.getBigInt64(1032, true) === 262144n};
    }
  };
}
