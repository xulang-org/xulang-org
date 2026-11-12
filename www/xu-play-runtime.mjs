// The guest reads two virtual files and writes to bounded streams.
const encoder = new TextEncoder();
const decoder = new TextDecoder();
const INPUT = 'program.xu';
const EVENTS = 'events.bin';
const ROOT_FD = 3;
const INPUT_FD = 4;
const EVENTS_FD = 7;
const MAX_SOURCE = 128 * 1024;
const MAX_OUTPUT = 256 * 1024;
export const MAX_UI_EVENTS = 100000;
const EVENT_BYTES = 80;
const MAX_CACHED_GROWTH = 32 * 1024 * 1024;
// The SDK's wasm32-wasi backend reserves the space between its globals at
// 4096 and static data at 131072. Linked entry points share the MIR
// descriptor and suspended interpreter state in this reserved space.
const MIR_ADDRESS = 65536n;
const STATE_ADDRESS = 65792n;
const OUTPUT_FDS = [1, 2, 5, 6];
const BAD_FD = 8;
const INVALID = 28;
const NOT_FOUND = 44;
const NO_SPACE = 51;
const NOT_SUPPORTED = 52;

class GuestExit {
  constructor(status) { this.status = status; }
}

function joinText(parts) {
  const bytes = new Uint8Array(parts.reduce((length, part) => length + part.length, 0));
  let offset = 0;
  for (const part of parts) {
    bytes.set(part, offset);
    offset += part.length;
  }
  return decoder.decode(bytes);
}

export async function createRuntime(bytesOrModule, {cache = true, checkpoints = true} = {}) {
  const module = bytesOrModule instanceof WebAssembly.Module
    ? bytesOrModule
    : await WebAssembly.compile(bytesOrModule);
  const imports = WebAssembly.Module.imports(module);
  if (imports.some(({module, kind}) => module !== 'wasi_snapshot_preview1' || kind !== 'function')) {
    throw new Error('Unexpected typed playground host imports');
  }
  const exports = WebAssembly.Module.exports(module);
  if (!['playground_prepare', 'playground_execute', 'playground_drive', 'playground_checkpoint', 'playground_preview'].every(entry =>
        exports.some(({name, kind}) => name === entry && kind === 'function')) ||
      !exports.some(({name, kind}) => name === 'memory' && kind === 'memory') ||
      WebAssembly.Module.customSections(module, 'xu.source').length !== 1) {
    throw new Error('Missing typed playground exports or build provenance');
  }
  let prepared;

  return {
    run(source, {events = [], profile = false} = {}) {
      const started = performance.now();
      const cached = cache && prepared?.source === source ? prepared : undefined;
      const input = encoder.encode(source);
      if (input.length > MAX_SOURCE) throw new Error('Source exceeds 128 KiB');
      if (!Array.isArray(events) || events.length > MAX_UI_EVENTS) throw new Error('UI event limit exceeded');
      const eventBytes = new Uint8Array(events.length * EVENT_BYTES);
      const eventView = new DataView(eventBytes.buffer);
      events.forEach((event, index) => {
        if (!event || !Number.isInteger(event.x ?? 0) || !Number.isInteger(event.y ?? 0) ||
            Math.abs(event.x ?? 0) > 100000 || Math.abs(event.y ?? 0) > 100000 ||
            (event.kind === undefined && (!Number.isInteger(event.x) || !Number.isInteger(event.y) ||
              event.x < 0 || event.x >= 640 || event.y < 0 || event.y >= 360))) {
          throw new Error('Invalid UI click coordinates');
        }
        if (event.kind !== undefined && (!Number.isInteger(event.kind) || event.kind < 72 || event.kind > 80)) {
          throw new Error('Invalid UI event kind');
        }
        for (const field of ['dx', 'dy']) {
          if (!Number.isFinite(event[field] ?? 0) || Math.abs(event[field] ?? 0) > 100000) {
            throw new Error('Invalid UI scroll delta');
          }
        }
        for (const field of ['key', 'modifiers', 'repeat', 'button', 'buttons']) {
          if (!Number.isInteger(event[field] ?? 0) || (event[field] ?? 0) < 0 || (event[field] ?? 0) > 65535) {
            throw new Error('Invalid UI event field');
          }
        }
        const offset = index * EVENT_BYTES;
        const words = [event.kind, event.x, event.y, event.key, event.modifiers, event.repeat, event.button, event.buttons];
        words.forEach((value, slot) => eventView.setBigInt64(offset + slot * 8, BigInt(value ?? 0), true));
        eventView.setFloat64(offset + 64, event.dx ?? 0, true);
        eventView.setFloat64(offset + 72, event.dy ?? 0, true);
      });
      const checkpoint = checkpoints ? cached?.checkpoint : undefined;
      const resume = checkpoint && checkpoint.events.length <= eventBytes.length &&
        checkpoint.events.every((byte, index) => byte === eventBytes[index]);
      const replayed = resume ? eventBytes.subarray(checkpoint.events.length) : eventBytes;
      const argv = ['xu-playground', '/' + INPUT, '/' + EVENTS].map(value => encoder.encode(value + '\0'));
      const env = [encoder.encode('PWD=/\0')];
      const streams = OUTPUT_FDS.map(() => []);
      const streamSizes = OUTPUT_FDS.map(() => 0);
      const files = new Map([
        [INPUT_FD, {name: INPUT, data: input, position: 0, open: false}],
        [EVENTS_FD, {name: EVENTS, data: replayed, position: 0, open: false}],
      ]);
      const descriptors = new Map([...files].map(([fd, file]) => [file.name, fd]));
      let instance;
      const view = () => new DataView(instance.exports.memory.buffer);
      const bytes = (ptr, size) => new Uint8Array(instance.exports.memory.buffer, ptr >>> 0, size >>> 0);
      const u32 = (ptr, value) => view().setUint32(ptr >>> 0, value, true);
      const u64 = (ptr, value) => view().setBigUint64(ptr >>> 0, BigInt(value), true);
      const fileName = (ptr, size) => decoder.decode(bytes(ptr, size));
      const vectorSizes = (items, countPtr, bytesPtr) => {
        u32(countPtr, items.length);
        u32(bytesPtr, items.reduce((size, item) => size + item.length, 0));
        return 0;
      };
      const writeVector = (items, pointers, payload) => {
        for (const item of items) {
          u32(pointers, payload);
          bytes(payload, item.length).set(item);
          pointers += 4;
          payload += item.length;
        }
        return 0;
      };
      const fileStat = (type, size, out) => {
        bytes(out, 64).fill(0);
        view().setUint8(out + 16, type);
        u64(out + 24, 1);
        u64(out + 32, size);
        return 0;
      };

      const wasi = {
        args_sizes_get: (count, size) => vectorSizes(argv, count, size),
        args_get: (pointers, payload) => writeVector(argv, pointers, payload),
        environ_sizes_get: (count, size) => vectorSizes(env, count, size),
        environ_get: (pointers, payload) => writeVector(env, pointers, payload),
        proc_exit: status => { throw new GuestExit(status); },
        fd_prestat_get(fd, out) {
          if (fd !== ROOT_FD) return BAD_FD;
          u32(out, 0);
          u32(out + 4, 1);
          return 0;
        },
        fd_prestat_dir_name(fd, out, size) {
          if (fd !== ROOT_FD || size < 1) return BAD_FD;
          bytes(out, 1)[0] = 47;
          return 0;
        },
        path_filestat_get(fd, _flags, path, size, out) {
          if (fd !== ROOT_FD) return BAD_FD;
          const name = fileName(path, size);
          if (name === '.') return fileStat(3, 0, out);
          const file = files.get(descriptors.get(name));
          return file ? fileStat(4, file.data.length, out) : NOT_FOUND;
        },
        path_open(fd, _lookup, path, size, oflags, _base, _inherited, fdflags, out) {
          if (fd !== ROOT_FD) return BAD_FD;
          const fileFd = descriptors.get(fileName(path, size));
          if (fileFd === undefined) return NOT_FOUND;
          if (oflags || fdflags) return INVALID;
          const file = files.get(fileFd);
          file.position = 0;
          file.open = true;
          u32(out, fileFd);
          return 0;
        },
        fd_filestat_get(fd, out) {
          if (fd === ROOT_FD) return fileStat(3, 0, out);
          const file = files.get(fd);
          return file?.open ? fileStat(4, file.data.length, out) : BAD_FD;
        },
        fd_fdstat_get(fd, out) {
          const type = fd === ROOT_FD ? 3 : files.get(fd)?.open ? 4 : OUTPUT_FDS.includes(fd) ? 2 : 0;
          if (!type) return BAD_FD;
          bytes(out, 24).fill(0);
          view().setUint8(out, type);
          return 0;
        },
        fd_close(fd) {
          const file = files.get(fd);
          if (!file?.open) return BAD_FD;
          file.open = false;
          return 0;
        },
        fd_seek(fd, offset, whence, out) {
          const file = files.get(fd);
          if (!file?.open) return BAD_FD;
          const position = whence === 0 ? 0 : whence === 1 ? file.position : whence === 2 ? file.data.length : -1;
          const next = BigInt(position) + offset;
          if (position < 0 || next < 0n || next > BigInt(file.data.length)) return INVALID;
          file.position = Number(next);
          u64(out, next);
          return 0;
        },
        fd_read(fd, iovs, count, out) {
          const file = files.get(fd);
          if (!file?.open) return BAD_FD;
          let total = 0;
          for (let i = 0; i < count; i++) {
            const pointer = view().getUint32(iovs + i * 8, true);
            const size = Math.min(view().getUint32(iovs + i * 8 + 4, true), file.data.length - file.position);
            bytes(pointer, size).set(file.data.subarray(file.position, file.position + size));
            total += size;
            file.position += size;
            if (file.position === file.data.length) break;
          }
          u32(out, total);
          return 0;
        },
        fd_write(fd, iovs, count, out) {
          const stream = OUTPUT_FDS.indexOf(fd);
          if (stream < 0) return BAD_FD;
          let total = 0;
          for (let i = 0; i < count; i++) {
            const pointer = view().getUint32(iovs + i * 8, true);
            const size = view().getUint32(iovs + i * 8 + 4, true);
            const written = Math.min(size, MAX_OUTPUT - streamSizes[stream]);
            if (stream >= 2 && written < size) {
              u32(out, total);
              return total ? 0 : NO_SPACE;
            }
            if (written > 0) streams[stream].push(bytes(pointer, written).slice());
            streamSizes[stream] += written;
            total += size;
          }
          u32(out, total);
          return 0;
        },
        clock_time_get(id, _precision, out) {
          const time = id === 0 ? Date.now() : performance.now();
          u64(out, BigInt(Math.floor(time * 1e6)));
          return 0;
        },
      };
      const timings = {cacheHit: !!cached, compileMs: 0, resumeHit: !!resume,
        replayedEvents: replayed.length / EVENT_BYTES, checkpointBytes: 0};
      const instanceStart = performance.now();
      const instanceHost = cached?.host ?? {wasi};
      if (cached) instance = cached.instance;
      else {
        const host = Object.fromEntries(imports.map(({name}) => [name,
          (...args) => instanceHost.wasi[name]?.(...args) ?? NOT_SUPPORTED]));
        instance = new WebAssembly.Instance(module, {wasi_snapshot_preview1: host});
      }
      instanceHost.wasi = wasi;
      const exp = instance.exports;
      const memory = exp.memory;
      const prepareStart = performance.now();
      let exit = 0;
      let guestExit = false;
      let diagnostic = '';
      try {
        prepared = cached;
        if (cached) {
          const prefix = resume ? checkpoint : cached;
          for (let stream = 0; stream < prefix.output.length; stream++) {
            for (const part of prefix.output[stream]) streams[stream].push(part);
            streamSizes[stream] = prefix.sizes[stream];
          }
        } else {
          exit = Number(exp.playground_prepare(MIR_ADDRESS));
          timings.compileMs = performance.now() - prepareStart;
          if (cache && exit === 0) {
            prepared = {
              source, instance, host: instanceHost, bytes: memory.buffer.byteLength,
              output: streams.slice(0, 2).map(parts => parts.slice()),
              sizes: streamSizes.slice(0, 2),
            };
          }
        }
        const executeStart = performance.now();
        if (exit === 0 && prepared && checkpoints) {
          prepared.checkpoint = undefined;
          exit = Number(exp.playground_drive(MIR_ADDRESS, STATE_ADDRESS, resume ? 1n : 0n));
          const size = exit === 0 ? Number(exp.playground_checkpoint(STATE_ADDRESS)) : 0;
          if (size > 0) {
            // A preview may print, paint, or mutate the running program.
            // Retain only the streams and state from before the empty read.
            prepared.checkpoint = {
              events: eventBytes, output: streams.map(parts => parts.slice()), sizes: streamSizes.slice(),
            };
            timings.checkpointBytes = size;
            exit = Number(exp.playground_preview(MIR_ADDRESS, STATE_ADDRESS));
          }
        } else if (exit === 0) {
          exit = Number(exp.playground_execute(MIR_ADDRESS));
        }
        timings.executeMs = performance.now() - executeStart;
        if (prepared && exit !== 0) prepared.checkpoint = undefined;
        if (prepared && memory.buffer.byteLength > prepared.bytes + MAX_CACHED_GROWTH) prepared = undefined;
      } catch (error) {
        prepared = undefined;
        if (error instanceof GuestExit) {
          exit = error.status;
          guestExit = true;
        }
        else if (error instanceof WebAssembly.RuntimeError || error instanceof RangeError) {
          exit = 1;
          diagnostic = 'error: typed playground runtime trapped\n';
        } else throw error;
      }
      instanceHost.wasi = {};
      timings.instanceMs = cached ? 0 : prepareStart - instanceStart;
      timings.arenaEnd = memory.buffer.byteLength;
      timings.memoryBytes = memory.buffer.byteLength;
      timings.preparedBytes = prepared?.bytes ?? 0;
      if (!prepared?.checkpoint) timings.checkpointBytes = 0;
      const decodeStart = performance.now();
      const stdout = joinText(streams[0]);
      let stderr = joinText(streams[1]) + diagnostic;
      const commands = joinText(streams[2]);
      const modes = joinText(streams[3]);
      if (guestExit && exit === 2 && stderr.includes('fatal error: out of memory')) {
        exit = 1;
        stderr += 'Xu playground memory limit exceeded\n';
      }
      timings.outputDecodeMs = performance.now() - decodeStart;
      timings.totalMs = performance.now() - started;
      return {exit, stdout, stderr,
        ui: exit === 0 && commands ? {commands, interactive: !!modes, input: modes.includes('input\n')} : null,
        truncated: streamSizes[0] === MAX_OUTPUT || streamSizes[1] === MAX_OUTPUT,
        ...(profile ? {timings} : {})};
    },
  };
}
