"""Link a fixed set of scalar WASM instructions into the site's MIR VM.

The development wasm32 backend supports typed f64 arithmetic; the site's
selected 0.10.12 SDK predates it. The MIR interpreter,
however, stores all VM values as integer bit patterns: vm_fp_* in runtime/float.xu
are still trap stubs, not typed f64 functions. Numeric int/f64 casts would convert
these values rather than reinterpret their bits, so they cannot replace this
bridge. These helpers reinterpret the slots and perform scalar operations only;
they never interpret source or draw controls. All functions retain the product's
(args i32, result i32) -> void frame ABI.
"""
from pathlib import Path


def uleb(n):
    out = bytearray()
    while n >= 128:
        out.append((n & 127) | 128)
        n >>= 7
    out.append(n)
    return bytes(out)


def read_u(data, pos):
    value = shift = 0
    while True:
        n = data[pos]
        pos += 1
        value |= (n & 127) << shift
        if n < 128:
            return value, pos
        shift += 7


def sections(data):
    pos = 8
    while pos < len(data):
        tag = data[pos]
        size, start = read_u(data, pos + 1)
        yield tag, data[start:start + size]
        pos = start + size


def read_name(data, pos):
    size, pos = read_u(data, pos)
    return data[pos:pos + size].decode(), pos + size


def helper_bodies():
    # local.get 0 points to descending i64 argument slots.
    x = bytes.fromhex('20 00 29 03 00')
    y = bytes.fromhex('20 00 41 08 6b 29 03 00')
    fp_x, fp_y = x + b'\xbf', y + b'\xbf'  # f64.reinterpret_i64
    instructions = {}
    for name, op in [('add', 0xa0), ('sub', 0xa1), ('mul', 0xa2), ('div', 0xa3)]:
        instructions[name] = fp_x + fp_y + bytes([op, 0xbd])
    for name, op in [('eq', 0x61), ('ne', 0x62), ('lt', 0x63), ('gt', 0x64), ('le', 0x65), ('ge', 0x66)]:
        instructions[name] = fp_x + fp_y + bytes([op, 0xad]) # i64.extend_i32_u
    instructions['neg'] = fp_x + bytes([0x9a, 0xbd])
    instructions['from_int'] = x + bytes([0xb9, 0xbd])
    # Saturating conversion is explicit: NaN -> 0, overflow -> i64 bounds.
    instructions['to_int'] = fp_x + bytes([0xfc, 6])
    return {'_xu_main_vm_fp_' + name: b'\x00\x20\x01' + code + bytes.fromhex('37 03 00 0b')
            for name, code in instructions.items()}


# The disposable arena starts at 16 MiB and retains parser/checker/MIR/UI
# allocations until evaluation ends. Styled table/chart programs add compiler
# and paint work beyond the original gallery's roughly 107 MiB peak.
# Keep this in sync with wasm_support.xu, build metadata and the gallery test.
MEMORY_PAGES = 4096  # fixed 256 MiB initial and maximum memory


def link(path):
    data = path.read_bytes()
    if data[:8] != b'\x00asm\x01\x00\x00\x00':
        raise ValueError('expected WASM v1')
    parts = list(sections(data))
    names = {}
    for tag, payload in parts:
        if tag != 0:
            continue
        name, pos = read_name(payload, 0)
        if name != 'name':
            continue
        while pos < len(payload):
            sub = payload[pos]
            size, start = read_u(payload, pos + 1)
            if sub == 1:
                count, cursor = read_u(payload, start)
                for _ in range(count):
                    index, cursor = read_u(payload, cursor)
                    label, cursor = read_name(payload, cursor)
                    names[label] = index
            pos = start + size
    helpers = helper_bodies()
    if not helpers.keys() <= names.keys():
        raise ValueError('missing scalar VM helper labels')
    replacements = {names[label]: body for label, body in helpers.items()}
    out = bytearray(data[:8])
    for tag, payload in parts:
        if tag == 5:
            # The SDK emits one fixed 64 MiB memory. Expand both limits for the
            # checker/MIR/UI arena above; stack/data addresses stay intact.
            if payload != b'\x01\x01' + uleb(1024) + uleb(1024):
                raise ValueError('unexpected SDK memory limits')
            payload = b'\x01\x01' + uleb(MEMORY_PAGES) + uleb(MEMORY_PAGES)
        if tag == 10:
            count, pos = read_u(payload, 0)
            code = bytearray(uleb(count))
            for index in range(count):
                size, pos = read_u(payload, pos)
                body = replacements.get(index, payload[pos:pos + size])
                code += uleb(len(body)) + body
                pos += size
            payload = bytes(code)
        out += bytes([tag]) + uleb(len(payload)) + payload
    name = b'xu.playground.float'
    provenance = uleb(len(name)) + name + b'Frame ABI v1; fixed IEEE f64 scalar helpers; bounded memory 256 MiB; scripts/link-playground-float.py'
    out += b'\x00' + uleb(len(provenance)) + provenance
    path.write_bytes(out)


if __name__ == '__main__':
    import sys
    link(Path(sys.argv[1]))
