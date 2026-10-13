#!/usr/bin/env python3
"""Generate xu-site stdlib API HTML from Xu src.

Reads packages with mod.xu under --src (default ../xu/src).
Writes content/{zh,en}/api/**.html under --site.
Does not touch the language repo. Skips src/cmd/** and test_*.xu.
"""
from __future__ import annotations

import argparse
import html
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

FOREIGN_RE = re.compile(
    r"\b[Gg]olang\b|\b[Gg]o(?:'s)?\b|\bRust\b|\brustc\b|\bVlang\b|"
    r"与 V 一致|像 V 一样|Go 源码树|Go stdlib|非 Go|"
    r"对齐 Go[A-Za-z0-9_./]*|同 Go[A-Za-z0-9_./]*|Go 的 |Go `[^`]*`"
)
INTERNAL_LINE_RE = re.compile(
    r"Gen1|Clang|SROA|always-inline|licm|SIGSEGV|bootstrap|"
    r"workaround|mis-pass|mispasses|cyclic borrow|borrow checker would|"
    r"isel|unroll|ror/eor|8KB\+|stack frame|"
    r"runtime\.xu|sys_\*|os_fd_|lang-dep|fd-level helpers|M2b-safe",
    re.I,
)
TICKET_RE = re.compile(r"\((?:M|B|G|D|L-?)[0-9]+[a-z]?\)|\b(?:M|B|G)\d+[a-z]?\b|\*\*G\d+(?:/G\d+)*\*\*")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def is_cjk(s: str) -> bool:
    return bool(CJK_RE.search(s or ""))


def scrub_foreign(s: str) -> str:
    if not s:
        return ""
    t = FOREIGN_RE.sub("", s)
    t = re.sub(r"Xu 附加，?\s*", "Xu 附加。", t)
    t = t.replace("**Xu 附加。**", "Xu 附加。")
    t = TICKET_RE.sub("", t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    t = re.sub(r" ?\([ ,;/]*\)", "", t)
    t = re.sub(r" ?（[ ,;/]*）", "", t)
    t = re.sub(r"\s+([，。；、])", r"\1", t)
    t = re.sub(r" +\.", ".", t)
    t = re.sub(r"\s{2,}", " ", t)
    return t.strip(" \t-—:;|/")


def clean_comment_lines(lines: list[str]) -> str:
    kept = []
    for raw in lines:
        line = raw.strip()
        if line.startswith("//"):
            line = line[2:].strip()
        elif line.startswith("/*") or line.startswith("*"):
            line = line.lstrip("/*").rstrip("*/").strip()
        if not line:
            continue
        if INTERNAL_LINE_RE.search(line):
            continue
        line = scrub_foreign(line)
        if not line:
            continue
        kept.append(line)
    # drop package-scope "Read-only helpers..." if it's the only line on a fn? keep it
    return " ".join(kept).strip()


def split_depth(s: str, comma: bool = True) -> list[str]:
    parts: list[str] = []
    cur: list[str] = []
    depth = 0
    i = 0
    while i < len(s):
        c = s[i]
        if c in "([{":
            depth += 1
            cur.append(c)
        elif c in ")]}":
            depth -= 1
            cur.append(c)
        elif comma and c == "," and depth == 0:
            parts.append("".join(cur).strip())
            cur = []
        else:
            cur.append(c)
        i += 1
    if cur:
        parts.append("".join(cur).strip())
    return [p for p in parts if p]


def parse_receiver(recv: str) -> tuple[str, str]:
    recv = recv.strip()
    # name type, type may be &mut T / &T / T
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s+(.+)$", recv)
    if m:
        return m.group(1), m.group(2).strip()
    return "self", recv


def placeholder_name(typ: str) -> str:
    t = typ.strip()
    t = re.sub(r"^&mut\s+", "", t)
    t = re.sub(r"^&\s*", "", t)
    t = re.sub(r"^\[\]", "", t)
    t = t.split(".")[-1]
    t = re.sub(r"[^A-Za-z0-9_].*", "", t)
    if not t:
        return "v"
    if t == "Self":
        return "other"
    return t[0].lower() + t[1:] if t[0].isupper() else t


def parse_param(p: str) -> tuple[str, str, bool]:
    p = p.strip()
    if not p:
        return ("v", "?", False)
    if "<->" in p:
        name, typ = p.split("<->", 1)
        name = name.strip()
        typ = "<-> " + typ.strip()
        return (name or "args", typ, True)
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s+(.+)$", p)
    if m:
        return m.group(1), m.group(2).strip(), False
    return placeholder_name(p), p, False


@dataclass
class Param:
    name: str
    typ: str
    variadic: bool = False
    is_recv: bool = False


@dataclass
class Field:
    name: str
    typ: str
    comment: str = ""


@dataclass
class Item:
    kind: str  # fn, method, struct, const, iface, iface_method
    name: str
    sig: str
    recv_name: str = ""
    recv_type: str = ""
    generic: str = ""
    params: list[Param] = field(default_factory=list)
    ret: str = ""
    fields: list[Field] = field(default_factory=list)
    methods: list["Item"] = field(default_factory=list)
    comment: str = ""
    body: str = ""
    value: str = ""
    file: str = ""


@dataclass
class Package:
    path: str  # fmt, path/filepath
    import_path: str
    items: list[Item] = field(default_factory=list)
    file_comment: str = ""
    n_fn: int = 0
    n_method: int = 0
    n_type: int = 0
    n_const: int = 0
    n_iface: int = 0


def strip_strings_and_comments_for_braces(line: str, st: dict) -> str:
    """Return a copy with strings/comments blanked, tracking block-comment/string state."""
    out = []
    i = 0
    n = len(line)
    while i < n:
        if st.get("block"):
            if i + 1 < n and line[i] == "*" and line[i + 1] == "/":
                st["block"] = False
                out.append("  ")
                i += 2
                continue
            out.append(" ")
            i += 1
            continue
        if st.get("str"):
            q = st["str"]
            if line[i] == "\\" and i + 1 < n:
                out.append("  ")
                i += 2
                continue
            if line[i] == q:
                st["str"] = None
                out.append(" ")
                i += 1
                continue
            out.append(" ")
            i += 1
            continue
        if i + 1 < n and line[i] == "/" and line[i + 1] == "*":
            st["block"] = True
            out.append("  ")
            i += 2
            continue
        if i + 1 < n and line[i] == "/" and line[i + 1] == "/":
            out.append(" " * (n - i))
            break
        if line[i] in ('"', "'", "`"):
            st["str"] = line[i]
            out.append(" ")
            i += 1
            continue
        out.append(line[i])
        i += 1
    return "".join(out)


def collect_leading_comments(lines: list[str], idx: int) -> list[str]:
    j = idx - 1
    block: list[str] = []
    while j >= 0:
        t = lines[j].strip()
        if t == "":
            if block:
                break
            j -= 1
            continue
        if t.startswith("//"):
            block.append(lines[j])
            j -= 1
            continue
        if t.endswith("*/"):
            acc = [lines[j]]
            while j >= 0 and "/*" not in lines[j]:
                j -= 1
                if j >= 0:
                    acc.append(lines[j])
            block.extend(acc)
            j -= 1
            continue
        break
    block.reverse()
    return block


def signature_until_brace(lines: list[str], start: int) -> tuple[str, int, bool]:
    """Return (signature text without '{', line index of '{', found_brace)."""
    buf = []
    i = start
    depth = 0
    st = {"block": False, "str": None}
    while i < len(lines):
        raw = lines[i]
        blanked = strip_strings_and_comments_for_braces(raw, st)
        # cut line comment already blanked
        buf.append(raw.split("//")[0].rstrip() if not st["str"] else raw.rstrip())
        for c in blanked:
            if c == "{":
                text = "\n".join(buf)
                # trim from last { at depth 0 of this join — simpler: strip after first { that's starter
                # reconstruct: take original joined, find first { not in sig generics... use blanked join
                joined_raw = " ".join(x.strip() for x in buf)
                # find matching first brace in joined_raw approximately
                cut = joined_raw.find("{")
                if cut >= 0:
                    joined_raw = joined_raw[:cut].strip()
                return joined_raw, i, True
            if c == ";" and depth == 0 and i > start:
                joined_raw = " ".join(x.strip() for x in buf)
                joined_raw = joined_raw.rstrip(";").strip()
                return joined_raw, i, False
        i += 1
        if i > start + 12:
            break
    joined_raw = " ".join(x.strip() for x in buf).strip()
    return joined_raw, start, False


BRACE_PAIR = {"{": "}", "(": ")", "[": "]"}


def capture_block(lines: list[str], brace_line: int) -> str:
    """Capture body from the line that contains '{', through matching '}'."""
    st = {"block": False, "str": None}
    depth = 0
    started = False
    body_lines = []
    for i in range(brace_line, len(lines)):
        raw = lines[i]
        blanked = strip_strings_and_comments_for_braces(raw, st)
        body_lines.append(raw)
        for c in blanked:
            if c == "{":
                depth += 1
                started = True
            elif c == "}":
                depth -= 1
                if started and depth <= 0:
                    return "\n".join(body_lines)
        if i > brace_line + 400:
            break
    return "\n".join(body_lines[:40])


def parse_fn_sig(sig: str) -> dict:
    s = re.sub(r"\s+", " ", sig.strip())
    s = re.sub(r"^pub\s+", "", s)
    out = {
        "recv_name": "",
        "recv_type": "",
        "name": "",
        "generic": "",
        "params": [],
        "ret": "",
        "kind": "fn",
    }
    if s.startswith("fn "):
        s = s[3:].strip()
    recv = ""
    if s.startswith("("):
        depth = 1
        i = 1
        while i < len(s) and depth:
            if s[i] == "(":
                depth += 1
            elif s[i] == ")":
                depth -= 1
            i += 1
        recv = s[1 : i - 1].strip()
        s = s[i:].strip()
        out["kind"] = "method"
        rn, rt = parse_receiver(recv)
        out["recv_name"] = rn
        out["recv_type"] = rt
    # name#generic(
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)(#([^(\s]+))?\s*\(", s)
    if not m:
        # iface: maybe already "name(...)"
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)(#([^(\s]+))?\s*\(", s)
    if not m:
        return out
    out["name"] = m.group(1)
    out["generic"] = (m.group(3) or "").strip()
    rest = s[m.end() - 1 :]  # starts with (
    if not rest.startswith("("):
        return out
    depth = 0
    endp = None
    for i, c in enumerate(rest):
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                endp = i
                break
    if endp is None:
        return out
    inner = rest[1:endp]
    after = rest[endp + 1 :].strip()
    after = after.split("{")[0].strip()
    out["ret"] = after
    for p in split_depth(inner):
        n, t, v = parse_param(p)
        out["params"].append(Param(n, t, v))
    return out


def parse_struct_fields(block: str) -> list[Field]:
    fields: list[Field] = []
    # inside braces
    inner = block
    if "{" in inner:
        inner = inner[inner.find("{") + 1 :]
        if inner.rstrip().endswith("}"):
            inner = inner.rstrip()[:-1]
    pending_cmt: list[str] = []
    for line in inner.splitlines():
        t = line.strip()
        if t.startswith("//"):
            pending_cmt.append(t)
            continue
        if not t or t.startswith("fn "):
            pending_cmt = []
            continue
        # pub name type  OR  name type
        pub = False
        if t.startswith("pub "):
            pub = True
            t = t[4:].strip()
        if t.startswith("mut "):
            t = t[4:].strip()
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s+(.+?)$", t.rstrip(","))
        if not m:
            pending_cmt = []
            continue
        if not pub:
            # unexported; skip from public docs
            pending_cmt = []
            continue
        fields.append(Field(m.group(1), m.group(2).strip().rstrip(","), clean_comment_lines(pending_cmt)))
        pending_cmt = []
    return fields


def parse_iface_methods(block: str, iface_name: str, comment: str, file: str) -> tuple[list[Field], list[Item]]:
    """struct@ methods: `fn name(args) ret` no body."""
    methods: list[Item] = []
    inner = block
    if "{" in inner:
        inner = inner[inner.find("{") + 1 :]
        if inner.rstrip().endswith("}"):
            inner = inner.rstrip()[:-1]
    pending: list[str] = []
    for line in inner.splitlines():
        t = line.strip()
        if t.startswith("//"):
            pending.append(t)
            continue
        if not t.startswith("fn "):
            pending = []
            continue
        sig = t
        parsed = parse_fn_sig(sig)
        params = list(parsed["params"])
        # implicit receiver
        recv_p = Param("self", "Self", is_recv=True)
        item = Item(
            kind="iface_method",
            name=parsed["name"] or t,
            sig=sig,
            recv_name="self",
            recv_type=iface_name,
            params=[recv_p] + params,
            ret=parsed["ret"],
            comment=clean_comment_lines(pending),
            file=file,
        )
        methods.append(item)
        pending = []
    return [], methods


def parse_xu_file(path: str) -> tuple[list[Item], str]:
    text = open(path, encoding="utf-8", errors="replace").read()
    lines = text.splitlines()
    items: list[Item] = []
    file_comment_lines: list[str] = []
    # top comment: after @mod and #imports
    i0 = 0
    while i0 < len(lines):
        t = lines[i0].strip()
        if t == "" or t.startswith("@") or t.startswith("#") or re.match(r"^[A-Za-z_][A-Za-z0-9_]*\s+#", t):
            i0 += 1
            continue
        if t.startswith("//") or t.startswith("/*"):
            file_comment_lines.append(lines[i0])
            i0 += 1
            continue
        break
    file_comment = clean_comment_lines(file_comment_lines)

    st = {"block": False, "str": None}
    depth = 0
    i = 0
    n = len(lines)
    while i < n:
        raw = lines[i]
        blanked = strip_strings_and_comments_for_braces(raw, st)
        stripped = raw.strip()
        # count braces for top-level
        is_top = depth == 0 and not st["block"] and not st.get("str")
        if is_top:
            lead = collect_leading_comments(lines, i)
            cmt = clean_comment_lines(lead)
            if stripped.startswith("pub fn ") or (
                stripped.startswith("fn ") and False
            ):
                name_guess = stripped
                if re.search(r"\bfn test_|\bfn bench_", stripped):
                    # still need to skip body
                    sig, bidx, has_b = signature_until_brace(lines, i)
                    if has_b:
                        body = capture_block(lines, bidx)
                        i = bidx + body.count("\n") + 1
                        # fix: capture_block starts at bidx, we should jump to end
                    else:
                        i += 1
                    continue
                sig, bidx, has_b = signature_until_brace(lines, i)
                body = capture_block(lines, bidx) if has_b else ""
                parsed = parse_fn_sig(sig)
                if parsed["name"] and not parsed["name"].startswith("test_") and not parsed["name"].startswith("bench_"):
                    params = list(parsed["params"])
                    if parsed["recv_name"]:
                        params = [Param(parsed["recv_name"], parsed["recv_type"], is_recv=True)] + params
                    items.append(
                        Item(
                            kind=parsed["kind"],
                            name=parsed["name"],
                            sig=sig if sig.startswith("pub ") else "pub " + sig,
                            recv_name=parsed["recv_name"],
                            recv_type=parsed["recv_type"],
                            generic=parsed["generic"],
                            params=params,
                            ret=parsed["ret"],
                            comment=cmt,
                            body=body,
                            file=path,
                        )
                    )
                if has_b:
                    # advance i to line after block
                    # recompute end line
                    end_line = bidx + capture_block(lines, bidx).count("\n")
                    i = end_line + 1
                    depth = 0
                    continue
                i += 1
                continue
            if stripped.startswith("pub struct ") or stripped.startswith("struct@ "):
                is_iface = stripped.startswith("struct@ ")
                sig, bidx, has_b = signature_until_brace(lines, i)
                block = capture_block(lines, bidx) if has_b else stripped
                if is_iface:
                    name = stripped.split("{")[0].replace("struct@", "").strip()
                    _f, meths = parse_iface_methods(block, name, cmt, path)
                    it = Item(
                        kind="iface",
                        name=name,
                        sig=re.sub(r"\s+", " ", sig) + " { … }" if has_b else sig,
                        comment=cmt,
                        file=path,
                        methods=meths,
                    )
                    # pretty sig: original header + methods
                    header = stripped.split("{")[0].strip()
                    meth_src = []
                    inner = block[block.find("{") + 1 :] if "{" in block else ""
                    for ml in inner.splitlines():
                        mt = ml.strip()
                        if mt.startswith("fn "):
                            meth_src.append("    " + mt)
                    it.sig = header + " {\n" + "\n".join(meth_src) + "\n}"
                    items.append(it)
                    items.extend(meths)
                else:
                    name = stripped.split("{")[0]
                    name = name.replace("pub struct", "").strip()
                    fields = parse_struct_fields(block)
                    header = stripped.split("{")[0].strip()
                    field_src = []
                    for f in fields:
                        field_src.append(f"    pub {f.name} {f.typ}")
                    sig_pretty = header + " {\n" + "\n".join(field_src) + "\n}"
                    items.append(
                        Item(
                            kind="struct",
                            name=name,
                            sig=sig_pretty,
                            fields=fields,
                            comment=cmt,
                            file=path,
                        )
                    )
                if has_b:
                    end_line = bidx + capture_block(lines, bidx).count("\n")
                    i = end_line + 1
                    depth = 0
                    continue
                i += 1
                continue
            if stripped.startswith("pub const "):
                line = stripped.split("//")[0].strip()
                rest = line[len("pub const ") :].strip()
                name = rest
                value = ""
                if "=" in rest:
                    name, value = rest.split("=", 1)
                    name = name.strip()
                    value = value.strip()
                else:
                    # pub const foo
                    name = rest.split()[0]
                items.append(
                    Item(
                        kind="const",
                        name=name,
                        sig=line,
                        value=value,
                        comment=cmt,
                        file=path,
                    )
                )
                i += 1
                continue
        # update depth from blanked (already consumed for skipped blocks)
        for c in blanked:
            if c == "{":
                depth += 1
            elif c == "}":
                depth = max(0, depth - 1)
        i += 1
    return items, file_comment


def list_packages(src_root: str) -> list[str]:
    pkgs = []
    for root, dirs, files in os.walk(src_root):
        dirs[:] = [d for d in dirs if d != "cmd"]
        rel = os.path.relpath(root, src_root)
        if rel == "cmd" or rel.startswith("cmd" + os.sep):
            continue
        if "mod.xu" in files:
            if rel == ".":
                continue
            pkgs.append(rel.replace(os.sep, "/"))
    pkgs.sort()
    return pkgs


def load_package(src_root: str, pkg: str) -> Package:
    folder = os.path.join(src_root, *pkg.split("/"))
    p = Package(path=pkg, import_path="#" + pkg)
    seen = set()
    files = []
    for fn in sorted(os.listdir(folder)):
        if not fn.endswith(".xu"):
            continue
        if fn.startswith("test_"):
            continue
        files.append(fn)
    # mod.xu first
    files.sort(key=lambda x: (x != "mod.xu", x))
    for fn in files:
        path = os.path.join(folder, fn)
        items, fcomment = parse_xu_file(path)
        if fn == "mod.xu" and fcomment and not p.file_comment:
            p.file_comment = fcomment
        for it in items:
            key = (it.kind, it.recv_type, it.name, it.sig)
            if key in seen:
                continue
            seen.add(key)
            p.items.append(it)
    for it in p.items:
        if it.kind == "fn":
            p.n_fn += 1
        elif it.kind == "method":
            p.n_method += 1
        elif it.kind == "struct":
            p.n_type += 1
        elif it.kind == "const":
            p.n_const += 1
        elif it.kind == "iface":
            p.n_iface += 1
        # iface_method not counted separately (matches extract)
    return p


# ---------------------------------------------------------------------------
# Documentation
# ---------------------------------------------------------------------------

# Hand-written docs: (pkg, name) or (pkg, recv_type, name)
# values: {zh: {purpose, params: {name: meaning}, returns}, en: {...}}

OVERRIDES: dict = {}


def _ov(pkg, name, zh_p, zh_params, zh_r, en_p, en_params, en_r, recv=""):
    key = (pkg, recv, name) if recv else (pkg, name)
    OVERRIDES[key] = {
        "zh": {"purpose": zh_p, "params": zh_params, "returns": zh_r},
        "en": {"purpose": en_p, "params": en_params, "returns": en_r},
    }


_ov(
    "fmt", "Arg",
    "格式化实参的装箱结构。kind 区分载荷：0 int、1 string、2 bool、3 f64、4 字节/字符。",
    {"kind": "载荷标签：0 int / 1 string / 2 bool / 3 f64 / 4 字符",
     "iv": "整数或字符码（kind 0 或 4）",
     "sv": "字符串载荷（kind 1）",
     "bv": "布尔载荷（kind 2）",
     "fv": "浮点载荷（kind 3）"},
    "",
    "Boxed formatting argument. kind selects the payload: 0 int, 1 string, 2 bool, 3 f64, 4 byte/char.",
    {"kind": "payload tag: 0 int / 1 string / 2 bool / 3 f64 / 4 char",
     "iv": "int or character code (kind 0 or 4)",
     "sv": "string payload (kind 1)",
     "bv": "bool payload (kind 2)",
     "fv": "f64 payload (kind 3)"},
    "",
)
_ov("fmt", "i",
    "把 int 装箱为 Arg（kind=0）。",
    {"x": "要装箱的整数"}, "装箱后的 Arg",
    "Box an int as Arg (kind=0).",
    {"x": "integer to box"}, "the boxed Arg")
_ov("fmt", "s",
    "把 string 装箱为 Arg（kind=1）。",
    {"x": "要装箱的字符串"}, "装箱后的 Arg",
    "Box a string as Arg (kind=1).",
    {"x": "string to box"}, "the boxed Arg")
_ov("fmt", "b",
    "把 bool 装箱为 Arg（kind=2）。",
    {"x": "要装箱的布尔值"}, "装箱后的 Arg",
    "Box a bool as Arg (kind=2).",
    {"x": "bool to box"}, "the boxed Arg")
_ov("fmt", "f",
    "把 f64 装箱为 Arg（kind=3）。",
    {"x": "要装箱的浮点数"}, "装箱后的 Arg",
    "Box an f64 as Arg (kind=3).",
    {"x": "float to box"}, "the boxed Arg")
_ov("fmt", "c",
    "把字符码（int 字节/rune）装箱为 Arg（kind=4）。",
    {"x": "字符码（int）"}, "装箱后的 Arg",
    "Box a character code (int byte/rune) as Arg (kind=4).",
    {"x": "character code (int)"}, "the boxed Arg")
_ov("fmt", "sprintf",
    "按格式串组装字符串。支持标志 - + # 0 与空格、宽度、精度（* 会再吃一个 int Arg）。动词含 %v %s %d %b %o %x %X %c %q %f %g 以及 %%。未写精度的 %f/%g/%v 用最短十进制。",
    {"f": "格式串（支持 %- + # 0 宽 精度，与本包实现一致）",
     "args": "可变 Arg（用 fmt.i/s/b/f/c 装箱）"},
    "格式化后的 string",
    "Build a string from a format string. Flags - + # 0 and space, width, and precision (* consumes an int Arg). Verbs include %v %s %d %b %o %x %X %c %q %f %g and %%. %f/%g/%v without precision use shortest decimal.",
    {"f": "format string (flags - + # 0, width, precision; as implemented in this package)",
     "args": "variadic Arg values (box with fmt.i/s/b/f/c)"},
    "the formatted string")
_ov("fmt", "sprintf_args",
    "与 sprintf 相同，但实参是 []Arg 切片而不是可变参。",
    {"f": "格式串（支持 %- + # 0 宽 精度，与本包实现一致）",
     "args": "已装箱的 Arg 切片"},
    "格式化后的 string",
    "Same as sprintf, but arguments are a []Arg slice instead of a variadic list.",
    {"f": "format string (flags - + # 0, width, precision; as implemented in this package)",
     "args": "slice of boxed Arg values"},
    "the formatted string")
_ov("fmt", "sprint",
    "把各 Arg 默认格式化后用空格拼接成字符串，末尾不加换行。",
    {"args": "可变 Arg（用 fmt.i/s/b/f/c 装箱）"},
    "拼接后的 string",
    "Format each Arg with the default verb and join with spaces. No trailing newline.",
    {"args": "variadic Arg values (box with fmt.i/s/b/f/c)"},
    "the joined string")
_ov("fmt", "sprintln",
    "与 sprint 相同，但结果末尾加一个换行。",
    {"args": "可变 Arg（用 fmt.i/s/b/f/c 装箱）"},
    "拼接后并带换行的 string",
    "Same as sprint, with a trailing newline.",
    {"args": "variadic Arg values (box with fmt.i/s/b/f/c)"},
    "the joined string plus a newline")
_ov("fmt", "sprint_args",
    "与 sprint 相同，但实参是 []Arg 切片。",
    {"args": "已装箱的 Arg 切片"},
    "拼接后的 string",
    "Same as sprint, but arguments are a []Arg slice.",
    {"args": "slice of boxed Arg values"},
    "the joined string")
_ov("fmt", "print",
    "把各 Arg 默认格式化后打印。经内建 println 输出，行尾带换行。",
    {"args": "可变 Arg（用 fmt.i/s/b/f/c 装箱）"},
    "",
    "Print each Arg with the default format. Goes through builtin println, so a trailing newline is written.",
    {"args": "variadic Arg values (box with fmt.i/s/b/f/c)"},
    "")
_ov("fmt", "println",
    "把各 Arg 默认格式化后打印。经内建 println 输出，行尾带换行。",
    {"args": "可变 Arg（用 fmt.i/s/b/f/c 装箱）"},
    "",
    "Print each Arg with the default format. Goes through builtin println, so a trailing newline is written.",
    {"args": "variadic Arg values (box with fmt.i/s/b/f/c)"},
    "")
_ov("fmt", "printf",
    "按格式串格式化后打印。经内建 println 输出，行尾带换行。格式错误时打印错误信息。",
    {"f": "格式串（支持 %- + # 0 宽 精度，与本包实现一致）",
     "args": "可变 Arg（用 fmt.i/s/b/f/c 装箱）"},
    "",
    "Format with a format string and print. Goes through builtin println (trailing newline). On format error, prints the error text.",
    {"f": "format string (flags - + # 0, width, precision; as implemented in this package)",
     "args": "variadic Arg values (box with fmt.i/s/b/f/c)"},
    "")
_ov("fmt", "errorf",
    "按格式串组装字符串，并包成 errors.StrErr。",
    {"f": "格式串（支持 %- + # 0 宽 精度，与本包实现一致）",
     "args": "可变 Arg（用 fmt.i/s/b/f/c 装箱）"},
    "errors.StrErr，message 为格式化结果",
    "Build a string from a format string and wrap it as errors.StrErr.",
    {"f": "format string (flags - + # 0, width, precision; as implemented in this package)",
     "args": "variadic Arg values (box with fmt.i/s/b/f/c)"},
    "errors.StrErr whose message is the formatted text")

_ov("strings", "contains",
    "判断 s 是否包含子串 sub。空 sub 视为包含（下标 0）。",
    {"s": "被查找的字符串（借用，调用方仍持有）",
     "sub": "要查找的子串"},
    "包含则为 true，否则 false",
    "Whether s contains substring sub. An empty sub is treated as contained (index 0).",
    {"s": "haystack (borrowed; caller keeps it)",
     "sub": "needle substring"},
    "true if found, else false")
_ov("strings", "index_of",
    "返回 sub 在 s 中首次出现的字节下标。空 sub 返回 0；未找到返回 -1。查找走 Horspool。",
    {"s": "被查找的字符串（借用，调用方仍持有）",
     "sub": "要查找的子串"},
    "首次出现的下标；未找到为 -1；空 sub 为 0",
    "Byte index of the first occurrence of sub in s. Empty sub returns 0; not found returns -1. Search uses Horspool.",
    {"s": "haystack (borrowed; caller keeps it)",
     "sub": "needle substring"},
    "first index, or -1 if missing; empty sub yields 0")
_ov("strings", "split",
    "按 sep 切开 s。空 sep 不按字符拆，而是返回仅含整个 s 的单元素切片。",
    {"s": "源字符串（借用，调用方仍持有）",
     "sep": "分隔符；空串则整段作为一项"},
    "切开后的 []string（含末尾空段）",
    "Split s on sep. An empty sep does not split into bytes; the result is a one-element slice holding all of s.",
    {"s": "source (borrowed; caller keeps it)",
     "sep": "separator; empty keeps the whole string as one part"},
    "[]string parts (including a trailing empty piece when s ends with sep)")
_ov("strings", "join",
    "用 sep 把 parts 拼成一个字符串。空切片得到空串。",
    {"parts": "要拼接的字符串切片",
     "sep": "插在元素之间的分隔符"},
    "拼接后的 string",
    "Join parts with sep. An empty slice yields the empty string.",
    {"parts": "strings to join",
     "sep": "separator inserted between elements"},
    "the joined string")
_ov("strings", "replace",
    "把 s 里的 old 换成 new。n==0 或 old 为空则原样返回；n<0 替换全部；n>0 最多替换 n 次。",
    {"s": "源字符串（借用）",
     "old": "被替换的子串；空串则不替换",
     "new": "替换成的子串",
     "n": "最大替换次数；0 不改；负值表示全部"},
    "替换后的新 string",
    "Replace old with new in s. n==0 or empty old returns s unchanged; n<0 replaces all; n>0 replaces at most n times.",
    {"s": "source (borrowed)",
     "old": "substring to replace; empty means no replacement",
     "new": "replacement",
     "n": "max replacements; 0 leaves s unchanged; negative means all"},
    "a new string")
_ov("strings", "has_prefix",
    "判断 s 是否以 pre 开头。",
    {"s": "源字符串（借用）", "pre": "前缀"},
    "是则 true",
    "Whether s starts with pre.",
    {"s": "source (borrowed)", "pre": "prefix"},
    "true if it does")
_ov("strings", "has_suffix",
    "判断 s 是否以 suf 结尾。",
    {"s": "源字符串（借用）", "suf": "后缀"},
    "是则 true",
    "Whether s ends with suf.",
    {"s": "source (borrowed)", "suf": "suffix"},
    "true if it does")
_ov("strings", "ends_with",
    "判断 s 是否以 suf 结尾（与 has_suffix 同类）。",
    {"s": "源字符串（借用）", "suf": "后缀"},
    "是则 true",
    "Whether s ends with suf (same idea as has_suffix).",
    {"s": "source (borrowed)", "suf": "suffix"},
    "true if it does")
_ov("strings", "count",
    "统计 sub 在 s 中非重叠出现次数。空 sub 返回 1+s.len。",
    {"s": "源字符串（借用）", "sub": "要计数的子串"},
    "出现次数（int）",
    "Non-overlapping count of sub in s. Empty sub returns 1+s.len.",
    {"s": "source (borrowed)", "sub": "substring to count"},
    "occurrence count")

# name-token purposes (longest match on full name first, then suffix)
NAME_HINTS = {
    "contains": ("判断是否包含给定片段。", "Report whether the input contains the given piece."),
    "contains_any": ("判断是否包含 cutset 中任一字节。", "Report whether any byte from the cutset occurs."),
    "contains_func": ("判断是否存在使回调为真的字节。", "Report whether any byte satisfies the callback."),
    "contains_rune": ("判断是否包含给定 rune。", "Report whether the rune occurs."),
    "index_of": ("返回首次出现的字节下标；未找到为 -1。", "Index of the first occurrence; -1 if missing."),
    "index": ("返回首次出现的下标；未找到为 -1。", "Index of the first occurrence; -1 if missing."),
    "index_byte": ("返回字节 c 首次出现的下标；未找到为 -1。", "Index of the first byte c; -1 if missing."),
    "index_any": ("返回 cutset 中任一字节首次出现的下标；未找到为 -1。", "Index of the first byte that appears in the cutset; -1 if missing."),
    "index_func": ("返回使回调为真的首个字节下标；未找到为 -1。", "Index of the first byte that satisfies the callback; -1 if missing."),
    "index_rune": ("返回 rune 首次出现的下标；未找到为 -1。", "Index of the first rune; -1 if missing."),
    "last_index": ("返回最后一次出现的下标；未找到为 -1。", "Index of the last occurrence; -1 if missing."),
    "last_index_byte": ("返回字节 c 最后一次出现的下标；未找到为 -1。", "Index of the last byte c; -1 if missing."),
    "last_index_any": ("返回 cutset 中字节最后一次出现的下标；未找到为 -1。", "Last index of any cutset byte; -1 if missing."),
    "last_index_func": ("返回使回调为真的最后字节下标；未找到为 -1。", "Last index where the callback is true; -1 if missing."),
    "has_prefix": ("判断是否具有给定前缀。", "Report whether the value has the given prefix."),
    "has_suffix": ("判断是否具有给定后缀。", "Report whether the value has the given suffix."),
    "ends_with": ("判断是否以给定后缀结尾。", "Report whether the value ends with the given suffix."),
    "starts_with": ("判断是否以给定前缀开头。", "Report whether the value starts with the given prefix."),
    "trim_space": ("去掉两端 ASCII 空白，返回新串。", "Strip leading and trailing ASCII whitespace."),
    "trim_left": ("去掉左端出现在 cutset 中的字节。", "Strip leading bytes that appear in the cutset."),
    "trim_right": ("去掉右端出现在 cutset 中的字节。", "Strip trailing bytes that appear in the cutset."),
    "trim": ("去掉两端出现在 cutset 中的字节。", "Strip leading and trailing bytes that appear in the cutset."),
    "trim_prefix": ("若有前缀则去掉该前缀，否则原样返回。", "Remove prefix if present; otherwise return the input."),
    "trim_suffix": ("若有后缀则去掉该后缀，否则原样返回。", "Remove suffix if present; otherwise return the input."),
    "trim_func": ("按回调去掉两端字节。", "Trim bytes on both ends using the callback."),
    "trim_left_func": ("按回调去掉左端字节。", "Trim leading bytes using the callback."),
    "trim_right_func": ("按回调去掉右端字节。", "Trim trailing bytes using the callback."),
    "split": ("按分隔符切开。", "Split on the separator."),
    "split_n": ("按分隔符切开，最多 n 段。", "Split on the separator, at most n parts."),
    "split_after": ("按分隔符切开，分隔符留在各段末尾。", "Split after the separator, keeping it on each piece."),
    "split_after_n": ("按分隔符切开并保留分隔符，最多 n 段。", "Split after the separator, at most n parts."),
    "fields": ("按空白段切开，丢掉空白本身。", "Split on whitespace runs and drop the whitespace."),
    "fields_func": ("按回调为真的字节切开。", "Split on bytes for which the callback is true."),
    "join": ("用分隔符拼接各段。", "Join pieces with a separator."),
    "repeat": ("把内容重复 n 次；n<=0 得空串。", "Repeat the content n times; n<=0 yields empty."),
    "replace": ("替换子串，次数由 n 限制。", "Replace a substring, limited by n."),
    "replace_all": ("替换全部出现的子串。", "Replace every occurrence of the substring."),
    "equal_fold": ("ASCII 大小写不敏感比较。", "ASCII case-insensitive equality."),
    "equal": ("判断两值是否相等。", "Report whether the two values are equal."),
    "compare": ("字典序比较：小于 -1、相等 0、大于 1。", "Lexicographic compare: -1, 0, or 1."),
    "clone": ("拷贝一份独立的 string。", "Copy into a new independent string."),
    "to_lower": ("ASCII 字母转小写。", "Map ASCII letters to lowercase."),
    "to_upper": ("ASCII 字母转大写。", "Map ASCII letters to uppercase."),
    "to_valid_utf8": ("把非法 UTF-8 序列换成 replacement。", "Replace invalid UTF-8 sequences with replacement."),
    "map_bytes": ("对每个字节调用 f，用返回值重建字符串。", "Map each byte through f and rebuild the string."),
    "count": ("统计非重叠出现次数。", "Count non-overlapping occurrences."),
    "cut": ("在首个 sep 处切成前后两段。", "Cut into before/after at the first sep."),
    "cut_prefix": ("若有前缀则切掉。", "Cut off a prefix when present."),
    "cut_suffix": ("若有后缀则切掉。", "Cut off a suffix when present."),
    "new": ("构造该类型的新值。", "Construct a new value of this type."),
    "reset": ("清空内部状态，可再写入或读取。", "Clear internal state so the value can be reused."),
    "close": ("关闭资源。", "Close the resource."),
    "len": ("返回长度。", "Return the length."),
    "length": ("返回当前长度。", "Return the current length."),
    "size": ("返回尺寸。", "Return the size."),
    "cap": ("返回容量。", "Return the capacity."),
    "grow": ("保证至少还能再写入 n 字节。", "Ensure room for at least n more bytes."),
    "write": ("写入数据，返回写入的字节数。", "Write data and return the byte count."),
    "write_string": ("写入字符串，返回写入的字节数。", "Write a string and return the byte count."),
    "write_byte": ("写入一个字节。", "Write one byte."),
    "write_rune": ("写入一个 rune 的 UTF-8 编码。", "Write a rune as UTF-8."),
    "write_str": ("写入字符串。", "Write a string."),
    "read": ("读出最多 max 字节。", "Read up to max bytes."),
    "read_n": ("最多读 n 字节；到末尾可返回更短或空串。", "Read at most n bytes; may return shorter or empty at end."),
    "read_byte": ("读一个字节；失败时 throw。", "Read one byte; throws on failure."),
    "unread_byte": ("把最近读出的一字节退回。", "Unread the last byte."),
    "read_rune": ("读一个 UTF-8 rune。", "Read one UTF-8 rune."),
    "unread_rune": ("把最近读出的 rune 退回。", "Unread the last rune."),
    "read_at": ("从偏移 off 起最多读 n 字节。", "Read at most n bytes starting at offset off."),
    "read_bytes": ("读到 delim（含 delim）。", "Read through delim (inclusive)."),
    "seek": ("按 whence 把读位置移到 offset。whence 0/1/2 分别为绝对、相对、从末尾。", "Move the read position. whence 0/1/2 = absolute / relative / from end."),
    "next": ("取出下一项；没有则按本类型约定结束。", "Take the next item, or end according to this type."),
    "lock": ("加锁，直到获得互斥。", "Acquire the lock."),
    "unlock": ("释放锁。", "Release the lock."),
    "read_lock": ("获取共享读锁。", "Acquire a shared read lock."),
    "read_unlock": ("释放读锁。", "Release a read lock."),
    "write_lock": ("获取独占写锁。", "Acquire an exclusive write lock."),
    "write_unlock": ("释放写锁。", "Release a write lock."),
    "msg": ("返回错误或对象的文本。", "Return the message text."),
    "cause": ("返回被包装的底层错误文本。", "Return the wrapped cause text."),
    "encode": ("编码。", "Encode."),
    "decode": ("解码。", "Decode."),
    "encode_to_string": ("编码为字符串。", "Encode to a string."),
    "decode_string": ("从字符串解码。", "Decode from a string."),
    "parse": ("解析输入。", "Parse the input."),
    "format": ("格式化为字符串。", "Format as a string."),
    "sum": ("计算摘要（多为小写 hex）。", "Compute a digest (often lowercase hex)."),
    "sum_bytes": ("计算原始字节摘要。", "Compute a raw-byte digest."),
    "encrypt": ("加密。", "Encrypt."),
    "decrypt": ("Decrypt.", "Decrypt."),
    "sign": ("签名。", "Sign."),
    "verify": ("验签。", "Verify."),
    "open": ("打开。", "Open."),
    "create": ("创建。", "Create."),
    "stat": ("读取元信息。", "Read metadata."),
    "mkdir": ("创建目录。", "Create a directory."),
    "remove": ("删除。", "Remove."),
    "rename": ("重命名。", "Rename."),
    "dial": ("发起连接。", "Dial a connection."),
    "listen": ("开始监听。", "Listen for connections."),
    "accept": ("接受一个连接。", "Accept one connection."),
    "sleep": ("阻塞等待一段时间。", "Block for a duration."),
    "now": ("当前时间。", "Current time."),
    "abs": ("绝对值。", "Absolute value."),
    "min": ("较小值。", "Minimum."),
    "max": ("较大值。", "Maximum."),
    "floor": ("向下取整。", "Floor."),
    "ceil": ("向上取整。", "Ceiling."),
    "sqrt": ("平方根。", "Square root."),
    "pow": ("幂。", "Power."),
    "sin": ("正弦。", "Sine."),
    "cos": ("余弦。", "Cosine."),
    "tan": ("正切。", "Tangent."),
    "exp": ("e 的幂。", "e to the power."),
    "log": ("自然对数。", "Natural logarithm."),
    "is_nan": ("是否为 NaN。", "Whether the value is NaN."),
    "is_inf": ("是否为无穷。", "Whether the value is infinity."),
    "is_dir": ("是否为目录。", "Whether it is a directory."),
    "valid": ("是否合法。", "Whether the value is valid."),
    "less": ("是否严格小于另一值。", "Whether this value is strictly less than the other."),
    "add": ("相加。", "Add."),
    "sub": ("相减。", "Subtract."),
    "mul": ("相乘。", "Multiply."),
    "div": ("相除。", "Divide."),
    "mod": ("取模。", "Modulo."),
    "and": ("按位与。", "Bitwise and."),
    "or": ("按位或。", "Bitwise or."),
    "xor": ("按位异或。", "Bitwise xor."),
    "not": ("按位取反。", "Bitwise not."),
    "flush": ("刷出缓冲。", "Flush buffered data."),
    "bytes": ("返回已缓冲的字节串。", "Return the buffered bytes."),
    "text": ("返回当前文本。", "Return the current text."),
    "to_string": ("转成 string。", "Convert to string."),
    "errorf": ("按格式串构造错误。", "Build an error from a format string."),
    "printf": ("按格式串打印。", "Print using a format string."),
    "println": ("打印并换行。", "Print with a newline."),
    "print": ("打印。", "Print."),
    "sprintf": ("按格式串组装字符串。", "Build a string from a format string."),
    "atoi": ("把十进制字符串解析为 int。", "Parse a decimal string as int."),
    "itoa": ("把 int 转成十进制字符串。", "Format an int as a decimal string."),
    "quote": ("加上引号并转义。", "Quote and escape."),
    "unquote": ("去掉引号并还原转义。", "Unquote and unescape."),
    "escape_string": ("转义特殊字符。", "Escape special characters."),
    "unescape_string": ("还原转义。", "Unescape."),
    "valid_path": ("检查路径是否为未加根、斜杠分隔的合法名；仅允许 “.” 作为根。", "Whether the name is an unrooted slash-separated path; only “.” is allowed as the root."),
    "ipv4": ("由四个 0..255 的字节构造 IPv4 地址（长度为 4 的 string）。", "Build an IPv4 address from four 0..255 octets (a 4-byte string)."),
    "ipv6": ("由 16 字节构造 IPv6 地址。", "Build an IPv6 address from 16 bytes."),
}


# decrypt was wrongly set - fix
NAME_HINTS["decrypt"] = ("解密。", "Decrypt.")
NAME_HINTS["encrypt"] = ("加密。", "Encrypt.")

PARAM_HINTS = {
    "s": ("源字符串", "source string"),
    "str": ("字符串", "string"),
    "src": ("源数据", "source"),
    "dst": ("目标", "destination"),
    "sub": ("子串", "substring"),
    "sep": ("分隔符", "separator"),
    "pre": ("前缀", "prefix"),
    "prefix": ("前缀", "prefix"),
    "suf": ("后缀", "suffix"),
    "suffix": ("后缀", "suffix"),
    "old": ("旧值 / 被替换片段", "old value / piece to replace"),
    "new": ("新值 / 替换成的片段", "new value / replacement"),
    "n": ("数量、长度或上限", "count, length, or limit"),
    "i": ("下标或整数", "index or integer"),
    "j": ("下标", "index"),
    "k": ("键或下标", "key or index"),
    "v": ("值", "value"),
    "x": ("值", "value"),
    "y": ("值", "value"),
    "c": ("字节或字符码", "byte or character code"),
    "r": ("rune（Unicode 码点）", "rune (Unicode code point)"),
    "ch": ("字符码", "character code"),
    "f": ("回调或格式串", "callback or format string"),
    "args": ("可变实参", "variadic arguments"),
    "path": ("文件系统路径", "filesystem path"),
    "name": ("名字", "name"),
    "key": ("键", "key"),
    "val": ("值", "value"),
    "data": ("数据", "data"),
    "buf": ("缓冲", "buffer"),
    "body": ("正文", "body"),
    "err": ("错误", "error"),
    "mode": ("模式", "mode"),
    "off": ("偏移", "offset"),
    "offset": ("偏移", "offset"),
    "whence": ("定位基准：0 起点 / 1 当前 / 2 末尾", "seek base: 0 start / 1 current / 2 end"),
    "max": ("上限", "maximum"),
    "min": ("下限", "minimum"),
    "wid": ("宽度", "width"),
    "prec": ("精度", "precision"),
    "base": ("进制", "numeric base"),
    "bit": ("比特数", "bit count"),
    "bits": ("比特数", "bit count"),
    "seed": ("随机种子", "random seed"),
    "delta": ("增量", "delta"),
    "timeout": ("超时", "timeout"),
    "timeout_ns": ("超时（纳秒）", "timeout in nanoseconds"),
    "dir": ("目录", "directory"),
    "pattern": ("匹配模式", "pattern"),
    "host": ("主机", "host"),
    "port": ("端口", "port"),
    "addr": ("地址", "address"),
    "fd": ("文件描述符", "file descriptor"),
    "msg": ("消息", "message"),
    "text": ("文本", "text"),
    "code": ("码", "code"),
    "usage": ("用法说明", "usage text"),
    "def": ("默认值", "default"),
    "cutset": ("要剥除的字节集合", "bytes to trim"),
    "chars": ("字节集合（cutset）", "byte cutset"),
    "replacement": ("非法序列的替换串", "replacement for invalid sequences"),
    "parts": ("各段", "parts"),
    "items": ("元素列表", "items"),
    "less": ("比较回调：true 表示左<右", "less callback: true means left < right"),
    "visit": ("访问回调", "visit callback"),
    "other": ("另一侧同类型值", "the other value of the same type"),
    "self": ("接收者", "receiver"),
    "w": ("写入侧 / 宽度", "writer or width"),
    "h": ("高度或句柄", "height or handle"),
    "iv": ("整数载荷或初始向量", "int payload or initialization vector"),
    "sv": ("字符串载荷", "string payload"),
    "bv": ("布尔载荷", "bool payload"),
    "fv": ("浮点载荷", "float payload"),
    "kind": ("类型标签", "kind tag"),
}



TOKEN_ZH = {
    "search": "二分查找", "reverse": "逆序", "resolve": "解析",
    "dial": "拨号", "listen": "监听", "accept": "接受",
    "split": "拆分", "join": "拼接", "close": "关闭",
    "read": "读取", "write": "写入", "open": "打开", "create": "创建",
    "conn": "连接", "tcp": "TCP", "udp": "UDP", "ip": "IP",
    "addr": "地址", "host": "主机", "port": "端口", "packet": "数据报",
    "timeout": "超时", "context": "上下文", "file": "文件",
    "listener": "监听器", "interface": "网卡", "interfaces": "网卡列表",
    "ipv4": "IPv4", "ipv6": "IPv6", "zero": "全零",
    "unspecified": "未指定", "loopback": "回环", "private": "私网",
    "pt": "点", "rect": "矩形", "ints": "int 切片", "f64s": "f64 切片",
    "strings": "string 切片", "slice": "切片", "func": "回调",
    "by": "按", "name": "名称", "index": "下标",
    "to": "到", "on": "于", "from": "从",
    "lookup": "查找", "walk": "遍历", "glob": "通配匹配",
    "clean": "规范化", "base": "末段名", "dir": "目录部分", "ext": "扩展名",
    "abs": "绝对路径", "rel": "相对路径", "volume": "盘符",
    "matches": "是否匹配", "has": "是否具有",
    "encode": "编码", "decode": "解码", "parse": "解析", "format": "格式化",
    "marshal": "编码写出", "unmarshal": "解码读入",
    "encrypt": "加密", "decrypt": "解密", "sign": "签名", "verify": "验签",
    "generate": "生成", "public": "公钥", "private": "私钥",
    "sum": "摘要", "hash": "哈希", "update": "更新", "reset": "重置",
    "compress": "压缩", "decompress": "解压",
    "copy": "拷贝", "clone": "拷贝", "move": "移动",
    "push": "压入", "pop": "弹出", "peek": "窥视",
    "front": "队头", "back": "队尾", "next": "下一项", "prev": "上一项",
    "lock": "加锁", "unlock": "解锁", "wait": "等待", "signal": "唤醒一个",
    "broadcast": "唤醒全部", "done": "完成一项", "add": "增加",
    "sub": "减去", "mul": "乘", "div": "除", "mod": "取模",
    "less": "小于", "equal": "相等", "compare": "比较",
    "min": "最小", "max": "最大", "sort": "排序",
    "insert": "插入", "delete": "删除", "compact": "去重相邻",
    "contains": "包含", "count": "计数",
    "trim": "修剪", "repeat": "重复", "replace": "替换",
    "fields": "按空白切分", "cut": "切开",
    "valid": "合法", "invalid": "非法",
    "size": "尺寸", "len": "长度", "cap": "容量", "length": "长度",
    "seek": "定位", "flush": "刷出", "sync": "同步",
    "stat": "元信息", "mkdir": "建目录", "remove": "删除", "rename": "重命名",
    "chmod": "改权限", "chdir": "改目录",
    "getenv": "读环境变量", "environ": "环境变量表",
    "argv": "命令行参数", "hostname": "主机名", "getwd": "工作目录",
    "home": "家目录", "user": "用户", "uid": "用户 id", "gid": "组 id",
    "pid": "进程 id", "pagesize": "页大小",
    "sleep": "睡眠", "now": "当前时间", "since": "以来", "until": "直到",
    "year": "年", "month": "月", "day": "日", "hour": "时", "minute": "分",
    "second": "秒", "weekday": "星期", "date": "日期",
    "truncate": "截断", "round": "舍入", "timer": "定时器", "ticker": "周期器",
    "unix": "Unix 时间", "utc": "UTC",
    "header": "头", "cookie": "Cookie", "body": "正文", "query": "查询串",
    "request": "请求", "response": "响应", "server": "服务端", "client": "客户端",
    "dialer": "拨号器", "config": "配置",
    "buffer": "缓冲", "cursor": "游标", "reader": "读取器", "writer": "写入器",
    "scanner": "扫描器", "builder": "构建器",
    "error": "错误", "wrap": "包装", "cause": "原因", "code": "码",
    "print": "打印", "fatal": "打印后退出",
    "test": "测试", "skip": "跳过", "fail": "失败", "log": "记录",
    "cleanup": "清理回调", "run": "运行",
    "background": "根上下文", "cancel": "取消", "deadline": "截止时间",
    "value": "值", "key": "键", "seed": "种子",
    "perm": "排列", "shuffle": "打乱",
    "leading": "前导", "trailing": "尾随", "ones": "一比特", "rotate": "旋转",
    "bytes": "字节", "rune": "rune", "string": "字符串",
    "hex": "十六进制", "dump": "转储",
    "quote": "加引号", "unquote": "去引号",
    "escape": "转义", "unescape": "反转义",
    "indent": "缩进", "compact": "压成一行",
    "html": "HTML", "json": "JSON", "xml": "XML", "csv": "CSV", "pem": "PEM",
    "asn1": "ASN.1", "der": "DER",
    "block": "块", "stream": "流", "nonce": "nonce", "tag": "标签",
    "seal": "封装", "open": "打开",
    "cbc": "CBC", "ctr": "CTR", "gcm": "GCM", "cfb": "CFB", "ofb": "OFB",
    "pkcs1": "PKCS#1", "pkcs7": "PKCS7", "pkcs8": "PKCS#8",
    "sm2": "SM2", "sm3": "SM3", "sm4": "SM4", "sm9": "SM9",
    "sha1": "SHA-1", "sha256": "SHA-256", "sha512": "SHA-512", "md5": "MD5",
    "hmac": "HMAC", "aes": "AES", "des": "DES", "rsa": "RSA",
    "ed25519": "Ed25519", "tls": "TLS", "x509": "X.509",
    "rand": "随机", "prime": "素数",
    "gcd": "最大公约数", "exp": "幂", "quo": "商", "rem": "余",
    "num": "分子", "denom": "分母", "sign": "符号",
    "floor": "向下取整", "ceil": "向上取整", "sqrt": "平方根",
    "sin": "正弦", "cos": "余弦", "tan": "正切", "atan": "反正切",
    "asin": "反正弦", "acos": "反余弦", "log": "对数", "exp": "指数",
    "pow": "幂", "hypot": "斜边", "modf": "拆成整数与小数",
    "nan": "NaN", "inf": "无穷", "copysign": "拷贝符号", "signbit": "符号位",
    "available": "剩余空间", "discard": "丢弃", "buffered": "已缓冲量",
    "unread": "退回", "peek": "预看",
    "grow": "扩容", "reserve": "预留", "truncate": "截断",
    "reset": "重置", "length": "长度", "text": "文本",
    "do": "执行一次", "first": "首次",
    "load": "读", "store": "写", "swap": "交换",
    "compare_and_swap": "比较并交换",
    "notify": "通知", "stop": "停止", "ignore": "忽略",
    "current": "当前", "lookup": "查找",
    "command": "命令", "output": "输出", "combined": "合并输出",
    "start": "启动", "wait": "等待",
    "cookiejar": "Cookie 罐", "jar": "罐",
    "recorder": "记录器", "result": "结果",
    "valid_path": "合法路径",
    "read_file": "读文件", "read_dir": "列目录",
    "dir_fs": "目录文件系统", "sub": "子树",
    "walk": "遍历", "visit": "访问",
    "binary_search": "二分查找",
    "sort_func": "按回调排序",
    "equal_fold": "忽略 ASCII 大小写比较",
    "to_slash": "换成 /", "from_slash": "换成本地分隔符",
    "volume_name": "盘符",
    "expand_env": "展开 $VAR",
    "mkdir_all": "递归建目录", "mkdir_temp": "建临时目录",
    "create_temp": "建临时文件", "remove_all": "递归删除",
    "is_abs": "是否绝对路径", "is_dir": "是否目录",
    "is_exist": "是否已存在类错误", "is_not_exist": "是否不存在类错误",
    "path_separator": "路径分隔符", "is_path_separator": "是否路径分隔符",
    "user_cache_dir": "用户缓存目录", "user_config_dir": "用户配置目录",
    "temp_dir": "临时目录", "home_dir": "家目录",
    "getpid": "进程 id", "getppid": "父进程 id",
    "getuid": "用户 id", "getgid": "组 id", "geteuid": "有效用户 id",
    "getegid": "有效组 id", "getpagesize": "页大小",
    "listdir": "列出目录（文本）", "entries": "列出目录项",
    "socket": "套接字", "bind4": "IPv4 bind", "connect4": "IPv4 connect",
    "sendto": "发送数据报", "recvfrom": "收数据报",
    "fd_read": "从 fd 读", "fd_write": "向 fd 写", "fd_close": "关 fd",
    "ipv4_zero": "IPv4 全零地址",
    "join_host_port": "拼 host:port", "split_host_port": "拆 host:port",
    "ip_is_unspecified": "是否未指定地址", "ip_is_loopback": "是否回环地址",
    "ip_is_private": "是否私网地址",
    "file_conn": "从文件描述符构造连接", "file_listener": "从文件描述符构造监听器",
    "conn_close": "关闭连接", "conn_read": "从连接读", "conn_write": "向连接写",
    "dial_tcp": "拨 TCP", "listen_tcp": "听 TCP",
    "dial_to": "拨到地址", "listen_on": "在地址上听",
    "dial_context": "带上下文拨号", "dial_timeout": "带超时拨号",
    "listen_packet": "听数据报",
    "interface_addrs": "网卡地址", "interface_by_name": "按名取网卡",
    "interface_by_index": "按下标取网卡",
    "resolve_tcp_addr": "解析 TCP 地址", "resolve_udp_addr": "解析 UDP 地址",
    "resolve_ip_addr": "解析 IP 地址", "resolve_unix_addr": "解析 Unix 地址",
}

TOKEN_EN = {
    "search": "binary search", "reverse": "reverse", "resolve": "resolve",
    "dial": "dial", "listen": "listen", "accept": "accept",
    "split": "split", "join": "join", "close": "close",
    "read": "read", "write": "write", "open": "open", "create": "create",
    "conn": "connection", "tcp": "TCP", "udp": "UDP", "ip": "IP",
    "addr": "address", "host": "host", "port": "port", "packet": "packet",
    "timeout": "timeout", "context": "context", "file": "file",
    "listener": "listener", "interface": "interface", "interfaces": "interfaces",
    "ipv4": "IPv4", "ipv6": "IPv6", "zero": "zero",
    "unspecified": "unspecified", "loopback": "loopback", "private": "private",
    "pt": "point", "rect": "rectangle", "ints": "int slice", "f64s": "f64 slice",
    "strings": "string slice", "slice": "slice", "func": "callback",
    "lookup": "lookup", "walk": "walk", "glob": "glob",
    "clean": "clean", "base": "base name", "dir": "directory", "ext": "extension",
    "encode": "encode", "decode": "decode", "parse": "parse", "format": "format",
    "encrypt": "encrypt", "decrypt": "decrypt", "sign": "sign", "verify": "verify",
    "sum": "digest", "sort": "sort", "shuffle": "shuffle", "perm": "permutation",
}


def hint_name(name: str, lang: str, pkg: str = "") -> str:
    zh = lang == "zh"
    if name in NAME_HINTS:
        return NAME_HINTS[name][0 if zh else 1]
    # package-tuned
    if pkg == "sort":
        if name in ("ints", "strings", "f64s"):
            return "原地升序排序。" if zh else "In-place ascending sort."
        if name == "slice":
            return "按 Ord.less 原地排序。" if zh else "In-place sort using Ord.less."
        if name == "slice_func":
            return "按 less 回调原地排序。" if zh else "In-place sort using the less callback."
        if name.startswith("reverse_"):
            return "原地降序排序（先升序再翻转）。" if zh else "In-place descending sort (sort ascending, then reverse)."
        if name.startswith("search_"):
            return "在已排序切片中二分查找。" if zh else "Binary search a sorted slice."
        if name.startswith("is_sorted"):
            return "是否已按升序排好。" if zh else "Whether the slice is sorted ascending."
    if pkg == "slices" and name.startswith("binary_search"):
        return "在已排序切片中二分查找，返回下标与是否命中。" if zh else "Binary search a sorted slice; returns index and whether it was found."
    if pkg == "image":
        if name == "pt":
            return "构造 Point。" if zh else "Construct a Point."
        if name == "rect":
            return "构造 Rectangle。" if zh else "Construct a Rectangle."
    table = TOKEN_ZH if zh else TOKEN_EN
    if name in table:
        w = table[name]
        return (w if w.endswith("。") else w + "。") if zh else (w if w.endswith(".") else w[0].upper() + w[1:] + ".")
    m = re.match(r"^(.+)_is_(.+)$", name)
    if m:
        a, b = m.group(1), m.group(2)
        return (f"判断 {a} 是否为 {b}。" if zh else f"Whether {a} is {b}.")
    if name.startswith("new_"):
        rest = name[4:].replace("_", " ")
        return (f"构造 {rest}。" if zh else f"Construct {rest}.")
    if name.startswith("parse_"):
        rest = name[6:].replace("_", " ")
        return (f"解析为 {rest}。" if zh else f"Parse as {rest}.")
    if name.startswith("format_"):
        rest = name[7:].replace("_", " ")
        return (f"格式化为 {rest}。" if zh else f"Format as {rest}.")
    if name.startswith("encode_"):
        return ("编码。" if zh else "Encode.")
    if name.startswith("decode_"):
        return ("解码。" if zh else "Decode.")
    if name.startswith("is_"):
        rest = name[3:].replace("_", " ")
        return (f"判断是否 {rest}。" if zh else f"Whether it is {rest}.")
    if name.startswith("has_"):
        rest = name[4:].replace("_", " ")
        return (f"判断是否具有 {rest}。" if zh else f"Whether it has {rest}.")
    if name.startswith("to_"):
        rest = name[3:].replace("_", " ")
        return (f"转换为 {rest}。" if zh else f"Convert to {rest}.")
    if name.startswith("from_"):
        rest = name[5:].replace("_", " ")
        return (f"从 {rest} 构造。" if zh else f"Build from {rest}.")
    if name.startswith("get_"):
        rest = name[4:].replace("_", " ")
        return (f"读取 {rest}。" if zh else f"Read {rest}.")
    if name.startswith("set_"):
        rest = name[4:].replace("_", " ")
        return (f"设置 {rest}。" if zh else f"Set {rest}.")
    if name.startswith("with_"):
        rest = name[5:].replace("_", " ")
        return (f"派生一个带 {rest} 的新值。" if zh else f"Derive a new value with {rest}.")
    if name.startswith("must_"):
        rest = name[5:].replace("_", " ")
        return (f"{rest}；失败则 throw。" if zh else f"{rest}; throws on failure.")
    # compose tokens left-to-right
    parts = name.split("_")
    if len(parts) >= 2:
        words = [table.get(x, x.replace("_", " ")) for x in parts]
        if zh:
            # prefer verb-last Chinese: conn_close -> 关闭连接 if last is verb-like
            last = parts[-1]
            if last in ("close", "read", "write", "open", "create", "search", "resolve", "dial", "listen"):
                head = "".join(table.get(x, x) for x in parts[:-1])
                return f"{table[last]}{head}。"
            return "".join(words) + "。"
        s = " ".join(words)
        return s[0].upper() + s[1:] + "."
    if name.endswith("_string"):
        return ("处理或返回字符串。" if zh else "Operate on or return a string.")
    if name.startswith("sum"):
        return NAME_HINTS["sum"][0 if zh else 1]
    return ""


def param_meaning(pkg, fn: str, p: Param, lang: str) -> str:
    pkg = pkg_id(pkg)
    zh = lang == "zh"
    if p.is_recv:
        if zh:
            mut = "可变借用" if p.typ.startswith("&mut") else ("借用" if p.typ.startswith("&") else "值接收者")
            return f"接收者 {p.typ}（{mut}）"
        mut = "exclusive borrow" if p.typ.startswith("&mut") else ("borrow" if p.typ.startswith("&") else "value receiver")
        return f"receiver {p.typ} ({mut})"
    if p.variadic or p.typ.startswith("<->"):
        inner = p.typ.replace("<->", "").strip()
        if pkg == "fmt" and inner.endswith("Arg"):
            return "可变 Arg（用 fmt.i/s/b/f/c 装箱）" if zh else "variadic Arg values (box with fmt.i/s/b/f/c)"
        return (f"可变参数，类型 {inner}，在函数体内是 []{inner}" if zh
                else f"variadic {inner} (seen inside the function as []{inner})")
    # fmt.f format vs callback vs float
    if p.name == "f":
        if "fn(" in p.typ.replace(" ", ""):
            return ("字节回调：参数为字节值 0..255，返回是否命中" if zh
                    else "byte callback: argument is 0..255, return whether it matches")
        if pkg == "fmt" or p.typ == "string":
            if pkg == "fmt":
                return ("格式串（支持 %- + # 0 宽 精度，与本包实现一致）" if zh
                        else "format string (flags - + # 0, width, precision; as implemented in this package)")
        if p.typ == "f64":
            return "浮点值" if zh else "floating-point value"
    if "[]" in p.typ and p.name in ("a", "b", "s", "xs", "arr"):
        extra = type_note(p.typ, zh)
        return ("要处理的切片" if zh else "slice to operate on") + extra
    if p.name in ("a", "b") and fn in (
        "less", "less_int", "less_string", "less_f64",
        "compare", "compare_int", "compare_string", "compare_f64",
        "add", "sub", "mul", "div", "min", "max", "hypot", "copysign",
    ):
        extra = type_note(p.typ, zh)
        lab = ("左操作数" if p.name == "a" else "右操作数") if zh else ("left operand" if p.name == "a" else "right operand")
        return lab + extra
    if fn == "ipv4" and p.name in "abcd" and p.typ == "int":
        idx = "abcd".index(p.name) + 1
        return (f"第 {idx} 个八位组，0..255" if zh else f"octet {idx}, 0..255")
    if p.name == "a" and "[]" not in p.typ:
        extra = type_note(p.typ, zh)
        return ("值" if zh else "value") + extra
    if p.name in PARAM_HINTS:
        h = PARAM_HINTS[p.name][0 if zh else 1]
        extra = type_note(p.typ, zh)
        return h + extra
    extra = type_note(p.typ, zh)
    return (p.name + extra) if extra else (p.name if not zh else p.name)


def type_note(typ: str, zh: bool) -> str:
    t = typ.strip()
    bits = []
    if t.startswith("&mut "):
        bits.append("独占借用" if zh else "exclusive borrow")
        t = t[5:]
    elif t.startswith("&"):
        bits.append("借用，调用方仍持有" if zh else "borrowed; caller keeps it")
        t = t[1:].lstrip()
    if t.startswith("<->"):
        bits.append("可变参" if zh else "variadic")
    if t.startswith("fn(") or t.startswith("fn ("):
        bits.append("函数值" if zh else "function value")
    if t.startswith("chan "):
        bits.append("通道" if zh else "channel")
    if not bits:
        return f"（{typ}）" if zh else f" ({typ})"
    return "（" + "；".join(bits) + f"；类型 {typ}）" if zh else " (" + "; ".join(bits) + f"; type {typ})"


def body_notes(item: Item, lang: str) -> list[str]:
    b = item.body or ""
    notes = []
    zh = lang == "zh"
    # strip comments in body for signals
    raw = re.sub(r"//.*?$", "", b, flags=re.M)
    throws = bool(re.search(r"\bor\s*>>", raw)) or bool(re.search(r"(^|[{;])\s*>>\s", raw, re.M)) or (">> errors." in raw)
    if throws:
        notes.append("失败时 throw。" if zh else "Throws on failure.")
    if re.search(r"<<\s*-1\b", raw) and ("index" in item.name or item.name.startswith("last_") or item.name in ("index_of", "index")):
        notes.append("未找到返回 -1。" if zh else "Returns -1 if not found.")
    if item.name in ("to_lower", "to_upper") and "65" in raw:
        notes.append("仅处理 ASCII 字母。" if zh else "ASCII letters only.")
    if item.name == "split" and "sep.len == 0" in raw:
        notes.append("空分隔符返回整段作为唯一元素。" if zh else "An empty separator yields the whole input as the only element.")
    return notes


def pkg_id(pkg) -> str:
    return pkg if isinstance(pkg, str) else pkg.path


def lookup_override(pkg, item: Item, lang: str):
    p = pkg_id(pkg)
    for key in ((p, item.recv_type, item.name), (p, item.name)):
        if key in OVERRIDES:
            return OVERRIDES[key][lang]
    return None


def comment_as_purpose(cmt: str, lang: str) -> str:
    c = scrub_foreign(cmt or "")
    if not c:
        return ""
    if INTERNAL_LINE_RE.search(c):
        return ""
    if lang == "zh":
        if is_cjk(c):
            return c
        return ""  # keep English comment for en page only
    if is_cjk(c):
        return ""
    return c


def purpose_for(pkg: str, item: Item, lang: str) -> str:
    ov = lookup_override(pkg, item, lang)
    if ov and ov.get("purpose"):
        return ov["purpose"]
    c = comment_as_purpose(item.comment, lang)
    hinted = hint_name(item.name, lang, pkg_id(pkg))
    notes = body_notes(item, lang)
    zh = lang == "zh"
    if item.kind == "const":
        base = c or (f"公开常量 `{item.name}`。" if zh else f"Public constant `{item.name}`.")
        if item.value:
            base += (" 值为 " if zh else " Value ") + f"`{item.value}`" + ("。" if zh and not base.endswith("。") else ("" if zh else "."))
        return base.strip()
    if item.kind == "struct":
        base = c or (f"公开结构体 `{item.name}`。" if zh else f"Public struct `{item.name}`.")
        return base
    if item.kind == "iface":
        base = c or (
            f"方法集约束 `{item.name}`。实现类型须提供下列方法。不是接口值。"
            if zh else
            f"Method-set constraint `{item.name}`. Implementing types must provide the methods below. Not an interface value."
        )
        return base
    parts = []
    if c:
        parts.append(c)
    elif hinted:
        if item.kind in ("method", "iface_method") and item.recv_type:
            recv = item.recv_type
            if zh:
                parts.append(f"`{item.recv_type}` 上的方法：{hinted}")
            else:
                parts.append(f"Method on `{item.recv_type}`: {hinted[0].lower() + hinted[1:] if hinted else hinted}")
        else:
            parts.append(hinted)
    else:
        if item.kind in ("method", "iface_method") and item.recv_type:
            parts.append(
                f"在 `{item.recv_type}` 上调用 `{item.name}`。"
                if zh else
                f"Call `{item.name}` on `{item.recv_type}`."
            )
        else:
            # last-resort: name + params/return, still a real sentence
            if zh:
                if item.ret:
                    parts.append(f"{item.name}，返回 {item.ret}。")
                else:
                    parts.append(f"{item.name}。")
            else:
                if item.ret:
                    parts.append(f"{item.name}; returns {item.ret}.")
                else:
                    parts.append(f"{item.name}.")
    for n in notes:
        if n not in "".join(parts):
            parts.append(n)
    text = " ".join(parts).strip()
    text = re.sub(r"。\s+", "。", text)
    text = re.sub(r"\.\s+", ". ", text)
    return text


def params_for(pkg: str, item: Item, lang: str) -> list[tuple[str, str, str]]:
    ov = lookup_override(pkg, item, lang)
    zh = lang == "zh"
    rows = []
    if item.kind == "struct":
        if not item.fields:
            return []
        for f in item.fields:
            meaning = ""
            if ov and ov.get("params") and f.name in ov["params"]:
                meaning = ov["params"][f.name]
            elif f.comment:
                meaning = f.comment if (is_cjk(f.comment) == zh or (zh and is_cjk(f.comment)) or (not zh and not is_cjk(f.comment))) else ""
            if not meaning and f.name in PARAM_HINTS:
                meaning = PARAM_HINTS[f.name][0 if zh else 1]
            if not meaning:
                meaning = ("字段" if zh else "field") + type_note(f.typ, zh)
            rows.append((f.name, f.typ, meaning))
        return rows
    if item.kind == "const":
        return []
    if item.kind == "iface":
        for m in item.methods:
            meaning = purpose_for(pkg, m, lang)
            rows.append((m.name, m.sig, meaning))
        return rows
    for p in item.params:
        meaning = ""
        if ov and ov.get("params") and p.name in ov["params"]:
            meaning = ov["params"][p.name]
        else:
            meaning = param_meaning(pkg, item.name, p, lang)
        rows.append((p.name, p.typ, meaning))
    return rows


def returns_for(pkg: str, item: Item, lang: str) -> str:
    ov = lookup_override(pkg, item, lang)
    if ov and ov.get("returns"):
        return ov["returns"]
    if item.kind in ("struct", "const", "iface"):
        return ""
    ret = (item.ret or "").strip()
    if not ret:
        return ""
    zh = lang == "zh"
    hinted = ""
    if ret == "bool":
        hinted = "是否成立" if zh else "true or false"
    elif ret == "int" and ("index" in item.name or item.name.startswith("last_")):
        hinted = "下标；未找到为 -1" if zh else "index; -1 if missing"
    elif ret == "int" and item.name.startswith("search_"):
        hinted = "已排序切片中的下标（未命中则为插入点）" if zh else "index in the sorted slice (insertion point if missing)"
    elif ret == "int" and item.name in ("compare", "compare_int", "compare_string", "compare_f64"):
        hinted = "小于 -1、相等 0、大于 1" if zh else "-1 if less, 0 if equal, 1 if greater"
    elif ret == "int" and item.name in ("write", "write_string", "write_byte", "write_rune"):
        hinted = "写入的字节数" if zh else "bytes written"
    elif ret == "string":
        hinted = "结果字符串" if zh else "result string"
    elif ret.startswith("[]"):
        hinted = "切片结果" if zh else "slice result"
    else:
        hinted = ("该类型的值" if zh else "a value of this type")
    return f"{ret} — {hinted}" if hinted else ret


# ---------------------------------------------------------------------------
# Package blurbs (LANGUAGE.md §9 + extras). User-facing: no Go/Rust/V.
# ---------------------------------------------------------------------------

LANG_MD_ZH: dict[str, str] = {}
LANG_MD_EN: dict[str, str] = {}

BLURB_ZH = {
    "fmt": "格式化：Arg 装箱（i/s/b/f/c），sprintf/sprint/print/printf/errorf。标志 -+#0、宽度、精度；无扫描、无反射动词。",
    "strings": "字符串工具。只读函数吃 &string，调用方仍持有源。查找走 Horspool。含 Builder / Reader / Replacer。",
    "bytes": "字节串工具，形状与 strings 对称。Buffer 可读写。查找同样走 Horspool。",
    "errors": "错误值：StrErr / CodeErr / WrapErr 与 struct@ Error。动态装箱是语言语法 errors.Error(x)，不是本包函数。",
    "strconv": "数字与引号：atoi/itoa、parse/format、quote/unquote，以及 append_*。",
    "path": "POSIX 斜杠路径：join/clean/split/base/dir/ext/matches。",
    "path/filepath": "本地路径（含盘符与斜杠转换）、glob、walk。",
    "os": "进程、文件、环境。hosted 下 File：open/create/read/write/close。getwd 失败返空串。",
    "io": "Buffer / Cursor 与 copy、read_all、EOF。另有 multi/tee/section/pipe。",
    "io/fs": "目录树视图。实现钉死 os.DirFS；包级函数吃 &os.DirFS。valid_path 检查未加根的斜杠路径。",
    "bufio": "绑 io.Buffer 的 Reader/Writer 与 Scanner（行/词/字节）。",
    "log": "owning Logger：print/printf/fatal；可带文件位置。",
    "log/slog": "结构化日志。无包级默认 logger。文本或 JSON 一行一条。",
    "flag": "FlagSet，无全局状态：define_* + parse + print_defaults。",
    "time": "Duration 为纳秒 int。now/sleep、Time、Timer/Ticker（xu+chan+sleep）。无 IANA 时区。",
    "sync": "Mutex / WaitGroup / Once / RWMutex / Cond 与原子 int。",
    "context": "Background / WithCancel / WithTimeout；Done 为 chan。无 WithValue。",
    "testing": "T：error/fatal/skip/run 与 *f 格式化。cleanup LIFO。非测试构建不能 import。",
    "runtime": "caller(skip) 仅允许常量 skip 0 或 1。",
    "cmp": "比较：struct@ Ord 与 less_*/compare_*。f64：NaN 小于非 NaN，NaN 等于 NaN。",
    "sort": "ints/f64s/strings introsort；slice / slice_func 按 Ord 或回调。",
    "slices": "int/string/f64 切片：contains/index/equal/reverse/clone/sort_func 等。",
    "maps": "库形 StrInt/StrStr。语言 map[K]V 是内建，不经本包。",
    "math": "常用实函数与 Pi/E。pow 为整指数；pow_f64 为浮点幂。",
    "math/bits": "位长、前导零、旋转、加减乘除进位。",
    "math/rand": "Source 实例。无全局源。xorshift64*，intn 拒绝采样。",
    "math/big": "大整数 Int 与有理数 Rat。无 Float。",
    "unicode": "码点类别与大小写（含部分空白）。",
    "unicode/utf8": "UTF-8 编解码与合法性。",
    "unicode/utf16": "UTF-16 代理项与编解码。",
    "regexp": "正则子集：compile/match/find/replace；有界回溯。",
    "html": "escape_string / unescape_string（五特殊字符与数字实体）。",
    "html/template": "模板插值默认转义。无分上下文（JS/CSS/URL）。",
    "text/template": "无反射模板：{{.}}、管道、if/with/range/define。",
    "text/scanner": "词法扫描：Ident/Int/Float/Char/String；源为 owning 字符串。",
    "text/tabwriter": "弹性制表：write + flush 返串。",
    "encoding/json": "严格 JSON；parse 得池化 Doc。valid/compact/indent/quote。",
    "encoding/xml": "文本转义与 Decoder.token。无反射 Unmarshal。",
    "encoding/csv": "RFC4180 Reader/Writer，源为 owning 字符串。",
    "encoding/hex": "十六进制编解码与 dump。",
    "encoding/base64": "Std 与 Raw/URL 变体。",
    "encoding/base32": "Std/Hex 与 Raw 变体。",
    "encoding/binary": "大小端整数与 uvarint/varint。",
    "encoding/ascii85": "Ascii85 编解码；z 表示四字节 0。",
    "encoding/pem": "PEM decode / encode_to_memory。",
    "encoding/asn1": "DER TLV 编解码；INTEGER 拟合 i64。",
    "encoding/xun": "XUN 文档。parse 得池化 Doc。",
    "compress/flate": "inflate + 字面量 Huffman deflate。",
    "compress/gzip": "gzip Reader/Writer，校验 CRC-32。",
    "compress/zlib": "zlib Reader/Writer，校验 Adler-32；拒字典。",
    "compress/lzw": "GIF LSB / PDF MSB LZW。",
    "compress/bzip2": "bzip2 解码（无 Writer）。",
    "archive/tar": "ustar 子集：Header + Reader/Writer。归档为 owning 字符串。",
    "archive/zip": "zip Reader/Writer（Store 与 deflate）。无 ZIP64。",
    "hash/crc32": "IEEE/Castagnoli/Koopman CRC-32。",
    "hash/crc64": "ISO/ECMA CRC-64。",
    "hash/adler32": "Adler-32。",
    "hash/fnv": "FNV-1 / FNV-1a 32/64。",
    "hash/maphash": "显式 seed 的可移植字节哈希（非硬件 AES 位型）。",
    "crypto/md5": "MD5 摘要与 Digest。",
    "crypto/sha1": "SHA-1 摘要与 Digest。",
    "crypto/sha256": "SHA-256：hex 与原始字节 + Digest。",
    "crypto/sha512": "SHA-512 摘要与 Digest。",
    "crypto/sha3": "SHA-3 / SHAKE。",
    "crypto/hmac": "HMAC-SHA-256 与 HMAC-SM3。",
    "crypto/aes": "AES-128/192/256 单块。CBC/CTR/GCM 见 crypto/cipher。",
    "crypto/cipher": "AES-CBC/CTR/GCM（绑 crypto.aes.Cipher）。",
    "crypto/des": "DES / 3DES-EDE 单块。",
    "crypto/rc4": "RC4 流密码。算法已破，仅协议互通。",
    "crypto/rsa": "PKCS#1 v1.5 加密与签名。无 OAEP/PSS。",
    "crypto/ed25519": "Ed25519 密钥、签名、验签。",
    "crypto/subtle": "常时比较外形的工具；后端不保证常时。",
    "crypto/rand": "读密码学随机字节。hosted Unix 走 /dev/urandom；其它目标后置。",
    "crypto/tls": "TLS 客户端子集。握手走宿主平台库（macOS SecureTransport；Linux/Windows 目前 throw）。",
    "crypto/x509": "解析证书与验签（Ed25519、RSA SHA-256、SM2-with-SM3）。无签发。",
    "crypto/x509/pkix": "证书 Distinguished Name（CN/O/C 等）。",
    "crypto/sm2": "SM2：密钥、签名、加密、密钥交换。零 C、非商密认证。",
    "crypto/sm3": "SM3 摘要。零 C、非商密认证。",
    "crypto/sm4": "SM4 单块与 CBC/CTR/CFB/OFB/GCM。零 C、非商密认证。",
    "crypto/sm9": "SM9 标识密码：签名/加密/密钥交换。零 C、非商密认证。",
    "crypto/zuc": "ZUC-128 与 128-EEA3/EIA3。零 C、非商密认证。",
    "crypto/gmtls": "GMTLS 1.1 子集（SM2 双证 + SM4）。进程内 net.pipe，无 Listen。零 C、非商密认证。",
    "net": "IP/端口解析与 TCP IPv4 Dial/Listen/Accept。Windows 上 TCP 返回错误占位。",
    "net/http": "HTTP/1.1 Client 与 Server、Header、Cookie。本包无 TLS。",
    "net/http/httptest": "进程内 ResponseRecorder 与测试用 Request。不做真实 listen。",
    "net/http/cookiejar": "内存 Cookie Jar。带 Domain 属性的 cookie 忽略（无公共后缀表）。",
    "net/url": "URL 与 query 编解码。",
    "net/mail": "邮箱地址解析。",
    "net/smtp": "SMTP 客户端：EHLO/MAIL/RCPT/DATA/QUIT。无 AUTH。",
    "net/textproto": "MIME 头规范化与解析。",
    "net/netip": "Addr / AddrPort / Prefix：4 或 16 字节 owning 地址。",
    "mime": "媒体类型解析与按扩展名猜类型。",
    "mime/multipart": "multipart Reader/Writer。EOF 为错误 EOF。",
    "mime/quotedprintable": "quoted-printable 编解码。",
    "image": "Point / Rectangle / RGBA 像素缓冲。",
    "image/color": "颜色类型与通道转换。",
    "image/draw": "RGBA 上的 SRC/OVER 绘制。",
    "image/png": "PNG 编解码（8 位、非隔行）。",
    "image/jpeg": "基线 JPEG 解码与 RGBA 编码。",
    "image/gif": "GIF 首帧解码与 RGBA 编码。",
    "container/list": "双向链表，值钉死 owning string。",
    "container/heap": "IntHeap / StrHeap 最小堆。",
    "container/ring": "环形链表，值钉死 owning string。",
    "index/suffixarray": "后缀数组 lookup / find_all_index。",
    "database/sql": "数据库用户面：open、Conn、事务、Rows。",
    "database/sql/driver": "驱动快照 RowsResult 与 Conn/Stmt/Tx/Driver。",
    "os/exec": "Command / Run / Output。v1 经宿主 os_system；无管道 Start/Wait。",
    "os/signal": "Unix 信号编号。notify 未接到内核，调用即 throw，避免静默丢信号。",
    "os/user": "当前用户（uid/gid + USER/HOME）。Lookup 只认当前用户。",
    "testing/iotest": "一次一字节 / 半量 Reader，以及每次都 throw 的 err_reader。",
    "testing/fstest": "内存 MapFS 与一致性检查。",
    "ui": "窗口/菜单/托盘。host 未接时 run 会报 host not available。",
    "ui/draw": "立即模式 2D 画布。",
    "ui/webview": "把 webview 挂到 ui.Window：load_html/url、eval、on/emit。",
}

BLURB_EN = {
    "fmt": "Formatting: Arg boxing (i/s/b/f/c), sprintf/sprint/print/printf/errorf. Flags -+#0, width, precision. No scanning; no reflection verbs.",
    "strings": "String helpers. Read-only functions take &string so the caller keeps the source. Search uses Horspool. Includes Builder / Reader / Replacer.",
    "bytes": "Byte-string helpers, parallel to strings. Buffer is readable and writable. Search uses Horspool.",
    "errors": "Error values: StrErr / CodeErr / WrapErr and struct@ Error. Dynamic boxing is language syntax errors.Error(x), not a function here.",
    "strconv": "Numbers and quoting: atoi/itoa, parse/format, quote/unquote, and append_*.",
    "path": "POSIX slash paths: join/clean/split/base/dir/ext/matches.",
    "path/filepath": "Host paths (volume, slash conversion), glob, and walk.",
    "os": "Process, files, environment. Hosted File: open/create/read/write/close. getwd returns empty on failure.",
    "io": "Buffer / Cursor plus copy, read_all, EOF. Also multi/tee/section/pipe.",
    "io/fs": "Directory-tree view. Implementation is concrete os.DirFS; package functions take &os.DirFS. valid_path checks unrooted slash paths.",
    "bufio": "Reader/Writer bound to io.Buffer, plus Scanner (lines/words/bytes).",
    "log": "Owning Logger: print/printf/fatal; optional file location.",
    "log/slog": "Structured logging. No package-level default logger. Text or one JSON object per line.",
    "flag": "FlagSet with no globals: define_* + parse + print_defaults.",
    "time": "Duration is int nanoseconds. now/sleep, Time, Timer/Ticker (xu+chan+sleep). No IANA zones.",
    "sync": "Mutex / WaitGroup / Once / RWMutex / Cond and atomic int.",
    "context": "Background / WithCancel / WithTimeout; Done is a chan. No WithValue.",
    "testing": "T: error/fatal/skip/run and *f formatters. LIFO cleanup. Cannot import outside test builds.",
    "runtime": "caller(skip) allows constant skip 0 or 1 only.",
    "cmp": "Comparison: struct@ Ord and less_*/compare_*. f64: NaN is less than non-NaN; NaN equals NaN.",
    "sort": "ints/f64s/strings introsort; slice / slice_func by Ord or callback.",
    "slices": "int/string/f64 slice helpers: contains/index/equal/reverse/clone/sort_func and more.",
    "maps": "Library StrInt/StrStr maps. Language map[K]V is builtin and does not go through this package.",
    "math": "Common real functions plus Pi/E. pow is integer exponent; pow_f64 is floating power.",
    "math/bits": "Bit length, leading zeros, rotate, add/sub/mul/div with carry.",
    "math/rand": "Source instances. No global source. xorshift64*; intn uses rejection sampling.",
    "math/big": "Big Int and rational Rat. No Float.",
    "unicode": "Code-point classes and case (including extra whitespace).",
    "unicode/utf8": "UTF-8 encode/decode and validation.",
    "unicode/utf16": "UTF-16 surrogates and encode/decode.",
    "regexp": "Regexp subset: compile/match/find/replace; bounded backtracking.",
    "html": "escape_string / unescape_string (five specials and numeric entities).",
    "html/template": "Templates with escaped interpolation. No JS/CSS/URL context switch.",
    "text/template": "Templates without reflection: {{.}}, pipelines, if/with/range/define.",
    "text/scanner": "Token scan: Ident/Int/Float/Char/String; source is an owning string.",
    "text/tabwriter": "Elastic tabstops: write + flush returns a string.",
    "encoding/json": "Strict JSON; parse yields a pooled Doc. valid/compact/indent/quote.",
    "encoding/xml": "Text escape and Decoder.token. No reflection unmarshal.",
    "encoding/csv": "RFC4180 Reader/Writer over owning strings.",
    "encoding/hex": "Hex encode/decode and dump.",
    "encoding/base64": "Std plus Raw/URL variants.",
    "encoding/base32": "Std/Hex plus Raw variants.",
    "encoding/binary": "Endian integers and uvarint/varint.",
    "encoding/ascii85": "Ascii85 encode/decode; z is four zero bytes.",
    "encoding/pem": "PEM decode / encode_to_memory.",
    "encoding/asn1": "DER TLV; INTEGER fits in i64.",
    "encoding/xun": "XUN documents. parse yields a pooled Doc.",
    "compress/flate": "inflate plus literal-only Huffman deflate.",
    "compress/gzip": "gzip Reader/Writer with CRC-32.",
    "compress/zlib": "zlib Reader/Writer with Adler-32; dictionaries rejected.",
    "compress/lzw": "GIF LSB / PDF MSB LZW.",
    "compress/bzip2": "bzip2 decode (no Writer).",
    "archive/tar": "ustar subset: Header + Reader/Writer. Archives are owning strings.",
    "archive/zip": "zip Reader/Writer (Store and deflate). No ZIP64.",
    "hash/crc32": "IEEE/Castagnoli/Koopman CRC-32.",
    "hash/crc64": "ISO/ECMA CRC-64.",
    "hash/adler32": "Adler-32.",
    "hash/fnv": "FNV-1 / FNV-1a 32/64.",
    "hash/maphash": "Portable byte hash with explicit seed (not hardware AES bits).",
    "crypto/md5": "MD5 digest and Digest.",
    "crypto/sha1": "SHA-1 digest and Digest.",
    "crypto/sha256": "SHA-256: hex and raw bytes + Digest.",
    "crypto/sha512": "SHA-512 digest and Digest.",
    "crypto/sha3": "SHA-3 / SHAKE.",
    "crypto/hmac": "HMAC-SHA-256 and HMAC-SM3.",
    "crypto/aes": "AES-128/192/256 single block. CBC/CTR/GCM live in crypto/cipher.",
    "crypto/cipher": "AES-CBC/CTR/GCM bound to crypto.aes.Cipher.",
    "crypto/des": "DES / 3DES-EDE single block.",
    "crypto/rc4": "RC4 stream cipher. Broken; kept for protocol interop only.",
    "crypto/rsa": "PKCS#1 v1.5 encrypt and sign. No OAEP/PSS.",
    "crypto/ed25519": "Ed25519 keys, sign, verify.",
    "crypto/subtle": "Constant-time-shaped helpers; the backend does not guarantee timing.",
    "crypto/rand": "Read cryptographic random bytes. Hosted Unix uses /dev/urandom; other targets come later.",
    "crypto/tls": "TLS client subset. Handshake uses the host library (SecureTransport on macOS; Linux/Windows currently throw).",
    "crypto/x509": "Parse certificates and verify (Ed25519, RSA SHA-256, SM2-with-SM3). No issuance.",
    "crypto/x509/pkix": "Certificate distinguished name (CN/O/C and related fields).",
    "crypto/sm2": "SM2 keys, sign, encrypt, key exchange. Pure Xu, not commercial-crypto certified.",
    "crypto/sm3": "SM3 digest. Pure Xu, not commercial-crypto certified.",
    "crypto/sm4": "SM4 block plus CBC/CTR/CFB/OFB/GCM. Pure Xu, not commercial-crypto certified.",
    "crypto/sm9": "SM9 identity-based sign/encrypt/exchange. Pure Xu, not commercial-crypto certified.",
    "crypto/zuc": "ZUC-128 and 128-EEA3/EIA3. Pure Xu, not commercial-crypto certified.",
    "crypto/gmtls": "GMTLS 1.1 subset (dual SM2 certs + SM4). In-process net.pipe; no Listen. Pure Xu, not commercial-crypto certified.",
    "net": "IP/port parsing and TCP IPv4 Dial/Listen/Accept. On Windows, TCP returns an error placeholder.",
    "net/http": "HTTP/1.1 Client and Server, Header, Cookie. No TLS in this package.",
    "net/http/httptest": "In-process ResponseRecorder and test Request. No real listen.",
    "net/http/cookiejar": "In-memory cookie Jar. Domain-attribute cookies are ignored (no public suffix list).",
    "net/url": "URL and query encode/decode.",
    "net/mail": "Mailbox address parsing.",
    "net/smtp": "SMTP client: EHLO/MAIL/RCPT/DATA/QUIT. No AUTH.",
    "net/textproto": "MIME header canonicalization and parse.",
    "net/netip": "Addr / AddrPort / Prefix: owning 4- or 16-byte addresses.",
    "mime": "Media-type parse and type-by-extension.",
    "mime/multipart": "multipart Reader/Writer. EOF is the error EOF.",
    "mime/quotedprintable": "quoted-printable encode/decode.",
    "image": "Point / Rectangle / RGBA pixel buffer.",
    "image/color": "Color types and channel conversion.",
    "image/draw": "SRC/OVER drawing on RGBA.",
    "image/png": "PNG encode/decode (8-bit, non-interlaced).",
    "image/jpeg": "Baseline JPEG decode and RGBA encode.",
    "image/gif": "GIF first-frame decode and RGBA encode.",
    "container/list": "Doubly linked list; values are owning strings.",
    "container/heap": "IntHeap / StrHeap min-heaps.",
    "container/ring": "Ring list; values are owning strings.",
    "index/suffixarray": "Suffix array lookup / find_all_index.",
    "database/sql": "Database user API: open, Conn, transactions, Rows.",
    "database/sql/driver": "Driver snapshot RowsResult plus Conn/Stmt/Tx/Driver.",
    "os/exec": "Command / Run / Output. v1 uses hosted os_system; no piped Start/Wait.",
    "os/signal": "Unix signal numbers. notify is not hooked to the kernel and throws so signals are not silently dropped.",
    "os/user": "Current user from uid/gid + USER/HOME. Lookup only succeeds for the current user.",
    "testing/iotest": "One-byte / half-size readers, plus err_reader that always throws.",
    "testing/fstest": "In-memory MapFS and a consistency check.",
    "ui": "Windows, menus, tray. run reports host not available when the host is not wired.",
    "ui/draw": "Immediate-mode 2D canvas.",
    "ui/webview": "Attach a webview to ui.Window: load_html/url, eval, on/emit.",
}


def package_blurb(pkg: Package, lang: str) -> str:
    table = BLURB_ZH if lang == "zh" else BLURB_EN
    if pkg.path in table:
        return table[pkg.path]
    c = scrub_foreign(pkg.file_comment)
    if c:
        if lang == "zh" and is_cjk(c):
            return c
        if lang == "en" and not is_cjk(c):
            return c
    if lang == "zh":
        return f"标准库包 `{pkg.import_path}`。"
    return f"Standard library package `{pkg.import_path}`."


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------

LABELS = {
    "zh": {
        "purpose": "用途",
        "params": "参数",
        "returns": "返回",
        "none": "无",
        "crumb": "API",
        "import": "import",
        "counts": "counts",
        "fn": "函数",
        "method": "方法",
        "type": "类型",
        "const": "常量",
        "iface": "方法集",
    },
    "en": {
        "purpose": "Purpose",
        "params": "Parameters",
        "returns": "Returns",
        "none": "none",
        "crumb": "API",
        "import": "import",
        "counts": "counts",
        "fn": "fns",
        "method": "methods",
        "type": "types",
        "const": "consts",
        "iface": "ifaces",
    },
}


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def highlight_xu(sig: str) -> str:
    s = html.escape(sig, quote=False)
    # 1. Comments
    s = re.sub(r"(//.*$)", r'<span class="syn-cmt">\1</span>', s, flags=re.MULTILINE)
    # 2. Strings
    s = re.sub(r'("([^"\\]|\\.)*")', r'<span class="syn-str">\1</span>', s)
    # 3. Imports: #name
    s = re.sub(r'#([A-Za-z0-9_/]+)', r'<span class="syn-import"><span class="hash">#</span>\1</span>', s)
    # 4. Keywords
    s = re.sub(r'\b(pub|fn|struct|mut|const|affine|defer|xu|if|else|match|return|interface|type|chan|or)\b', r'<span class="syn-kw">\1</span>', s)
    s = re.sub(r'struct@', r'<span class="syn-kw">struct@</span>', s)
    # 5. Flow controls & operators
    s = re.sub(r'(&gt;&gt;|&lt;&lt;|:=|&lt;-|-&gt;)', r'<span class="syn-flow">\1</span>', s)
    # 6. Borrowing: &mut / mut &
    s = re.sub(r'(mut\s*&amp;|&amp;\s*mut)', r'<span class="syn-borrow">\1</span>', s)
    # 7. Native types
    s = re.sub(r'\b(int|i8|i16|i32|i64|u8|u16|u32|u64|f32|f64|string|bool|char|void|any|error|byte|rune|Self)\b', r'<span class="syn-type">\1</span>', s)
    return s


def code_block(sig: str) -> str:
    return (
        '<div class="code-block-wrapper">'
        '<div class="code-block-header"><span>XU</span><span>v0.1.0</span></div>'
        f"<pre><code>{highlight_xu(sig)}</code></pre>"
        "</div>"
    )


def item_id(item: Item, used: dict) -> str:
    if item.kind == "method":
        base = f"{item.recv_type}-{item.name}"
    elif item.kind == "iface_method":
        base = f"{item.recv_type}-{item.name}"
    elif item.kind == "struct":
        base = f"struct-{item.name}"
    elif item.kind == "const":
        base = f"const-{item.name}"
    elif item.kind == "iface":
        base = f"iface-{item.name}"
    else:
        base = item.name
    base = re.sub(r"[^A-Za-z0-9_.-]", "-", base)
    n = used.get(base, 0)
    used[base] = n + 1
    return base if n == 0 else f"{base}-{n}"


def render_item(pkg: Package, item: Item, lang: str, used_ids: dict) -> str:
    L = LABELS[lang]
    iid = item_id(item, used_ids)
    purpose = purpose_for(pkg, item, lang)
    params = params_for(pkg, item, lang)
    ret = returns_for(pkg, item, lang)
    heading = item.name
    if item.kind == "method" and item.recv_type:
        heading = f"({item.recv_type}) {item.name}"
    elif item.kind == "iface_method" and item.recv_type:
        heading = f"({item.recv_type}) {item.name}"
    elif item.kind == "const":
        heading = f"const {item.name}"
    elif item.kind == "struct":
        heading = f"struct {item.name}"
    elif item.kind == "iface":
        heading = f"struct@ {item.name}"
    parts = [
        f'<article class="api-item" id="{esc(iid)}">',
        f"<h2><code>{esc(heading)}</code></h2>",
        code_block(item.sig),
        f"<h3>{L['purpose']}</h3>",
        f"<p>{esc(purpose)}</p>",
        f"<h3>{L['params']}</h3>",
    ]
    if not params:
        parts.append(f'<p class="api-none">{L["none"]}</p>')
    else:
        parts.append('<dl class="api-params">')
        for name, typ, meaning in params:
            parts.append(
                f"<dt><code>{esc(name)}</code> <span class=\"type\">{esc(typ)}</span></dt>"
                f"<dd>{esc(meaning)}</dd>"
            )
        parts.append("</dl>")
    if ret:
        parts.append(f"<h3>{L['returns']}</h3>")
        parts.append(f"<p>{esc(ret)}</p>")
    parts.append("</article>")
    return "\n".join(parts)


def render_page(pkg: Package, lang: str) -> str:
    L = LABELS[lang]
    blurb = package_blurb(pkg, lang)
    counts = (
        f"{pkg.n_fn} {L['fn']}, {pkg.n_method} {L['method']}, "
        f"{pkg.n_type} {L['type']}, {pkg.n_const} {L['const']}, {pkg.n_iface} {L['iface']}"
    )
    used: dict = {}
    body = [
        f"<!--title: #{pkg.path}-->",
        f'<p class="crumb">{L["crumb"]}</p>',
        f"<h1><code>#{esc(pkg.path)}</code></h1>",
        f'<p class="meta">{L["import"]}: <code>{esc(pkg.import_path)}</code></p>',
        f'<p class="meta">{L["counts"]}: {esc(counts)}</p>',
        f'<p class="lead">{esc(blurb)}</p>',
    ]
    # stable order: consts, ifaces, structs, fns, methods, iface methods
    # Keep source order — more honest than regrouping.
    for it in pkg.items:
        body.append(render_item(pkg, it, lang, used))
    body.append("")
    return "\n".join(body)


def write_packages(site: str, packages: list[Package]) -> None:
    for lang in ("zh", "en"):
        root = os.path.join(site, "content", lang, "api")
        os.makedirs(root, exist_ok=True)
        for pkg in packages:
            rel = pkg.path + ".html"
            dest = os.path.join(root, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            html_text = render_page(pkg, lang)
            with open(dest, "w", encoding="utf-8") as f:
                f.write(html_text)


CSS_BLOCK = """
/* —— stdlib API pages —— */
.api-item {
  margin: 1.1rem 0 0;
  padding: 0.9rem 0 1.1rem;
  border-bottom: 1px solid var(--xu-border-subtle);
}
.api-item:last-child { border-bottom: 0; }
.api-item h2 {
  font-size: 15px;
  font-weight: 700;
  margin: 0 0 0.55rem;
  border: 0;
  padding: 0;
  font-family: var(--xu-font-mono);
  letter-spacing: 0;
}
.api-item h2 code {
  background: transparent;
  border: 0;
  padding: 0;
  color: var(--xu-text-primary);
  font-size: 15px;
}
.api-item h3 {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--xu-text-muted);
  margin: 0.7rem 0 0.28rem;
  border: 0;
  padding: 0;
}
.api-item p {
  margin: 0.15rem 0 0;
  color: var(--xu-text-secondary);
  font-size: 14px;
  line-height: 1.55;
  max-width: 72ch;
}
.api-item .code-block-wrapper {
  margin: 0.45rem 0 0.35rem;
}
.api-item .code-block-wrapper pre {
  padding: 10px 14px;
  font-size: 12.5px;
  line-height: 1.5;
  margin: 0;
}
.api-item .code-block-header {
  padding: 6px 12px;
  font-size: 11px;
}
.api-params {
  display: grid;
  grid-template-columns: minmax(9rem, 18rem) 1fr;
  gap: 0.2rem 1rem;
  margin: 0.2rem 0 0;
  font-size: 13.5px;
  line-height: 1.45;
}
.api-params dt {
  font-family: var(--xu-font-mono);
  color: var(--xu-text-primary);
  margin: 0;
  padding: 0.12rem 0;
}
.api-params dd {
  margin: 0;
  color: var(--xu-text-secondary);
  padding: 0.12rem 0;
}
.api-params .type {
  color: var(--xu-syn-type);
  font-size: 12px;
  font-weight: 500;
  margin-left: 0.35rem;
  background: transparent;
  border: 0;
  padding: 0;
}
.api-none {
  color: var(--xu-text-muted);
  font-size: 13.5px;
  margin: 0.15rem 0 0;
}
main.doc .lead {
  color: var(--xu-text-secondary);
  font-size: 15px;
  max-width: 72ch;
}
@media (max-width: 700px) {
  .api-params { grid-template-columns: 1fr; }
  .api-params dd { padding-bottom: 0.45rem; }
}
"""


def ensure_css(site: str) -> None:
    path = os.path.join(site, "www", "site.css")
    if not os.path.isfile(path):
        print("warn: no www/site.css", file=sys.stderr)
        return
    text = open(path, encoding="utf-8").read()
    marker = "/* —— stdlib API pages —— */"
    if marker in text:
        pre = text[: text.find(marker)]
        text = pre.rstrip() + "\n" + CSS_BLOCK
    else:
        text = text.rstrip() + "\n" + CSS_BLOCK
    open(path, "w", encoding="utf-8").write(text)


def parse_extract_counts(extract_path: str) -> dict:
    out = {}
    if not os.path.isfile(extract_path):
        return out
    text = open(extract_path, encoding="utf-8").read()
    for m in re.finditer(
        r"### `([^`]+)`\n\nimport:.*\nmodule id:.*\ncounts: (\d+) fns, (\d+) methods, (\d+) types, (\d+) consts, (\d+) ifaces",
        text,
    ):
        out[m.group(1)] = tuple(int(m.group(i)) for i in range(2, 7))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate Xu stdlib API HTML")
    here = os.path.dirname(os.path.abspath(__file__))
    default_site = os.path.abspath(os.path.join(here, ".."))
    default_src = os.environ.get("XU_SRC") or os.path.abspath(os.path.join(default_site, "..", "xu", "src"))
    ap.add_argument("--src", default=default_src, help="Xu src root (packages with mod.xu)")
    ap.add_argument("--site", default=os.environ.get("XU_SITE_ROOT") or default_site, help="xu-site root")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    src = os.path.abspath(args.src)
    site = os.path.abspath(args.site)
    if not os.path.isdir(src):
        print(f"src not found: {src}", file=sys.stderr)
        return 1

    names = list_packages(src)
    packages = [load_package(src, n) for n in names]
    extract = parse_extract_counts(os.path.join(site, "xu-api-extract.md"))

    missing_docs = []
    mismatches = []
    for pkg in packages:
        got = (pkg.n_fn, pkg.n_method, pkg.n_type, pkg.n_const, pkg.n_iface)
        exp = extract.get(pkg.path)
        if exp and got != exp:
            mismatches.append((pkg.path, exp, got, len(pkg.items)))
        for it in pkg.items:
            if it.kind in ("fn", "method", "iface_method"):
                if not it.params and "()" not in it.sig.replace(" ", ""):
                    pass
            # every item gets purpose+params by construction
            pzh = purpose_for(pkg, it, "zh")
            pen = purpose_for(pkg, it, "en")
            if not pzh or not pen:
                missing_docs.append((pkg.path, it.kind, it.name, "purpose"))
            if is_cjk(pen):
                missing_docs.append((pkg.path, it.kind, it.name, "en-has-cjk"))

    print(f"gen-api: {len(packages)} packages from {src}")
    print(
        "  items: "
        f"{sum(p.n_fn for p in packages)} fns, "
        f"{sum(p.n_method for p in packages)} methods, "
        f"{sum(p.n_type for p in packages)} types, "
        f"{sum(p.n_const for p in packages)} consts, "
        f"{sum(p.n_iface for p in packages)} ifaces"
    )
    if mismatches:
        print(f"  count mismatches vs extract: {len(mismatches)}")
        for row in mismatches[:20]:
            print(f"    {row[0]} extract={row[1]} got={row[2]} items={row[3]}")
    if missing_docs:
        print(f"  doc gaps: {len(missing_docs)}")
        for row in missing_docs[:20]:
            print("   ", row)

    if args.dry_run:
        return 0

    write_packages(site, packages)
    ensure_css(site)
    print(f"  wrote content/{{zh,en}}/api for {len(packages)} packages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
