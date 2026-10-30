// Host bridge only: Xu source is parsed, checked and interpreted inside WASM.
export const MAX_UI_EVENTS = 64;
export async function createRuntime(bytesOrModule, {cache = true, checkpoints = true} = {}) {
  const module = (bytesOrModule instanceof WebAssembly.Module)
    ? bytesOrModule
    : await WebAssembly.compile(bytesOrModule);
  if (WebAssembly.Module.imports(module).length) {
    throw new Error('Xu playground unexpectedly requires host imports');
  }
  const exports = WebAssembly.Module.exports(module);
  if (!['xu_eval_frame', 'xu_prepare_frame', 'xu_execute_frame'].every(name =>
        exports.some(item => item.name === name && item.kind === 'function')) ||
      !exports.some(item => item.name === 'memory' && item.kind === 'memory')) {
    throw new Error('Missing Xu WASM exports');
  }
  if (!WebAssembly.Module.customSections(module, 'xu.source').length) {
    throw new Error('Missing Xu build provenance');
  }
  const decoder = new TextDecoder('utf-8');
  const encoder = new TextEncoder();
  // One checked program per worker. Everything allocated by interpreted user
  // code lives after arenaEnd and is rewound or restored before the next run.
  let prepared;

  return {
    run(source, {events = [], profile = false} = {}) {
      const started = profile ? performance.now() : 0;
      const timings = {};
      const cached = cache && prepared?.source === source ? prepared : null;
      const input = cached ? null : encoder.encode(source);
      if (input && input.length > 128 * 1024) throw new Error('Source exceeds 128 KiB');
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
      const instanceStart = profile ? performance.now() : 0;
      const exp = cached ? cached.exp : new WebAssembly.Instance(module, {}).exports;
      // Discard the old program before compiling changed source or after any
      // trap. Never reuse a wasm stack/arena interrupted by an exception.
      prepared = undefined;
      if (profile) {
        timings.cacheHit = !!cached;
        timings.instanceMs = cached ? 0 : performance.now() - instanceStart;
        timings.compileMs = 0;
        timings.executeMs = 0;
      }
      const memory = exp.memory.buffer;
      const view = new DataView(memory);
      if (input) {
        new Uint8Array(memory, 2048, input.length).set(input);
        view.setBigInt64(800, 2048n, true);
        view.setBigInt64(792, BigInt(input.length), true);
      }
      view.setBigInt64(1040, cached ? cached.arenaEnd : 16n * 1024n * 1024n, true);
      view.setBigInt64(1024, cached ? cached.stdoutLength : 0n, true);
      view.setBigInt64(1032, cached ? cached.stderrLength : 0n, true);
      for (const slot of [1048, 1056, 1072, 1080, 1088, 1112, 1120]) view.setBigInt64(slot, 0n, true);
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
        if (cached) prepared = cached;
        else {
          const compileStart = profile ? performance.now() : 0;
          exp.xu_prepare_frame(800, 140000);
          if (profile) timings.compileMs = performance.now() - compileStart;
          prepared = {source, exp, arenaEnd: view.getBigInt64(1040, true),
            stdoutLength: view.getBigInt64(1024, true), stderrLength: view.getBigInt64(1032, true)};
        }
        view.setBigInt64(800, 140000n, true);
        const executeStart = profile ? performance.now() : 0;
        if (checkpoints && exp.xu_start_frame && exp.xu_drive_frame) {
          const base = Number(prepared.arenaEnd);
          const cp = prepared.checkpoint;
          const resume = cp && events.length >= cp.eventCount &&
            JSON.stringify(events.slice(0, cp.eventCount)) === cp.key;
          if (profile) {
            timings.resumeHit = !!resume;
            timings.replayedEvents = events.length - (resume ? cp.eventCount : 0);
          }
          if (resume) {
            new Uint8Array(memory, base, cp.arena.length).set(cp.arena);
            // Eval has three slice descriptors and four scalars: 13 descending
            // i64 slots at 146000. Keep in sync with runtime/interpreter.xu.
            new Uint8Array(memory, 146000 - 96, 104).set(cp.state);
            view.setBigInt64(1040, BigInt(base + cp.arena.length), true);
            view.setBigInt64(1072, BigInt(cp.eventCount), true);
            for (const [slot, ptr, data] of cp.outputs) {
              new Uint8Array(memory, ptr, data.length).set(data);
              view.setBigInt64(slot, BigInt(data.length), true);
            }
          } else exp.xu_start_frame(800, 146000);
          view.setBigInt64(792, 146000n, true);
          exp.xu_drive_frame(800, 768);
          prepared.checkpoint = undefined;
          if (view.getBigInt64(1120, true) !== 0n) {
            const end = Number(view.getBigInt64(1040, true));
            // Bounded extra host memory. Larger programs retain full replay.
            if (end - base <= 8 * 1024 * 1024) {
              prepared.checkpoint = {
                eventCount: events.length, key: JSON.stringify(events),
                arena: new Uint8Array(memory, base, end - base).slice(),
                state: new Uint8Array(memory, 146000 - 96, 104).slice(),
                outputs: [[1024, 150000], [1032, 450000], [1056, 720000]].map(([slot, ptr]) =>
                  [slot, ptr, new Uint8Array(memory, ptr, Number(view.getBigInt64(slot, true))).slice()])
              };
            }
            // Deliver the exhaustion record on a temporary branch to run the
            // user's paint/print tail. Next input resumes before that branch.
            view.setBigInt64(1112, 1n, true);
            exp.xu_drive_frame(800, 768);
          }
        } else exp.xu_execute_frame(800, 768);
        if (profile) timings.executeMs = performance.now() - executeStart;
        exit = Number(view.getBigInt64(768, true));
        if (exit !== 0 && prepared) prepared.checkpoint = undefined;
        if (profile) timings.checkpointBytes = prepared?.checkpoint?.arena.length ?? 0;
      } catch (error) {
        prepared = undefined;
        if (!(error instanceof WebAssembly.RuntimeError)) throw error;
        trap = error;
        exit = 1;
      }
      const decode = (ptr, slot) => {
        const n = view.getBigInt64(slot, true);
        if (n < 0n || n > 262144n) throw new Error('Invalid Xu output buffer');
        return decoder.decode(new Uint8Array(memory, ptr, Number(n)));
      };
      const decodeStart = profile ? performance.now() : 0;
      const stdout = decode(150000, 1024);
      let stderr = decode(450000, 1032);
      if (trap) {
        stderr += view.getBigInt64(1048, true) > 0n
          ? 'Xu playground memory limit exceeded\n'
          : 'Xu WASM execution stopped: ' + trap.message + '\n';
      }
      const commands = decode(720000, 1056);
      if (profile) {
        timings.outputDecodeMs = performance.now() - decodeStart;
        timings.totalMs = performance.now() - started;
        timings.arenaEnd = Number(view.getBigInt64(1040, true));
      }
      return {exit, stdout, stderr, ui: exit === 0 && commands ? {
        commands, input: view.getBigInt64(1088, true) !== 0n, interactive: view.getBigInt64(1080, true) !== 0n
      } : null, truncated:
        view.getBigInt64(1024, true) === 262144n || view.getBigInt64(1032, true) === 262144n,
        ...(profile ? {timings} : {})};
    }
  };
}
