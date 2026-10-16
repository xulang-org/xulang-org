#!/usr/bin/env python3
"""Generate official multi-architecture benchmark pages for English and Chinese from benchmarks.json."""
from __future__ import annotations

import json
import html
import statistics
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "www/benchmarks.json"

SVG_BOLT = '<svg class="bench-icon bench-icon-bolt" viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>'
SVG_BRAIN = '<svg class="bench-icon bench-icon-brain" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/><path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"/><path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4"/><path d="M12 18v4"/><path d="M12 5V2"/></svg>'
SVG_BOX = '<svg class="bench-icon bench-icon-box" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/></svg>'
SVG_SEARCH = '<svg class="bench-search-icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>'
SVG_CONTROL = '<svg class="bench-icon bench-cat-svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="16 3 21 3 21 8"/><line x1="4" y1="20" x2="21" y2="3"/><polyline points="21 16 21 21 16 21"/><line x1="15" y1="15" x2="21" y2="21"/><line x1="4" y1="4" x2="9" y2="9"/></svg>'
SVG_ALGO = '<svg class="bench-icon bench-cat-svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="2" width="16" height="20" rx="2"/><line x1="8" y1="6" x2="16" y2="6"/><line x1="16" y1="14" x2="16" y2="18"/><path d="M16 10h.01"/><path d="M12 10h.01"/><path d="M8 10h.01"/><path d="M12 14h.01"/><path d="M8 14h.01"/><path d="M12 18h.01"/><path d="M8 18h.01"/></svg>'
SVG_DATA = '<svg class="bench-icon bench-cat-svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>'
SVG_STRING = '<svg class="bench-icon bench-cat-svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>'
SVG_CRYPTO = '<svg class="bench-icon bench-cat-svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>'
SVG_CONCURRENCY = '<svg class="bench-icon bench-cat-svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>'

CATEGORIES_CONFIG = [
    {
        "key": "control",
        "name_zh": "控制流与语言底层机制",
        "name_en": "Control Flow & Language Primitives",
        "pill_zh": "控制流机制",
        "pill_en": "Control & Primitives",
        "desc_zh": "实测进程启动、整数与浮点循环、递归、嵌套循环和结构体方法调用。",
        "desc_en": "Measured process startup, integer and floating-point loops, recursion, nested loops and struct method calls.",
        "icon": SVG_CONTROL,
    },
    {
        "key": "algo",
        "name_zh": "数值算法与密集计算",
        "name_en": "Numerical Algorithms & Compute",
        "pill_zh": "数值算法",
        "pill_en": "Algorithms",
        "desc_zh": "本轮实测数值计算负载；具体算法与规模以各项源码为准。",
        "desc_en": "Measured numerical workloads in this run; see each workload source for the algorithm and input size.",
        "icon": SVG_ALGO,
    },
    {
        "key": "data",
        "name_zh": "数据结构与内存访问模式",
        "name_en": "Data Structures & Memory Access",
        "pill_zh": "数据结构",
        "pill_en": "Data Structures",
        "desc_zh": "本轮实测数据结构字段访问及块内存拷贝。",
        "desc_en": "Measured aggregate field access and block memory copying.",
        "icon": SVG_DATA,
    },
    {
        "key": "string",
        "name_zh": "字符串处理与文本 I/O",
        "name_en": "Strings & Text I/O",
        "pill_zh": "文本与I/O",
        "pill_en": "Strings & I/O",
        "desc_zh": "字符串扩容与构建。",
        "desc_en": "String buffer growth and construction.",
        "icon": SVG_STRING,
    },
    {
        "key": "crypto",
        "name_zh": "现代密码学与散列摘要",
        "name_en": "Modern Cryptography & Hashing",
        "pill_zh": "现代密码学",
        "pill_en": "Cryptography",
        "desc_zh": "本轮实测 SHA-256 哈希链与 AES-128 加密；硬件与软件执行路径可能不同。",
        "desc_en": "Measured SHA-256 hash chains and AES-128 encryption; hardware and software execution paths may differ.",
        "icon": SVG_CRYPTO,
    },
    {
        "key": "concurrency",
        "name_zh": "高性能并发与协程通信",
        "name_en": "Concurrency & Coroutines",
        "pill_zh": "并发通信",
        "pill_en": "Concurrency",
        "desc_zh": "基于 CSP 通信顺序进程模型的轻量级协程调度延迟与有界/无界 Channel 管道跨协程高频乒乓（Ping-Pong）通信开销。",
        "desc_en": "CSP-model lightweight coroutine scheduling latency and high-frequency ping-pong channel communications.",
        "icon": SVG_CONCURRENCY,
    },
]

PLATFORMS_CONFIG = [
    {
        "id": "macos-arm64",
        "name_zh": "macOS",
        "name_en": "macOS",
        "arch_tag": "ARM64",
        "chip_zh": "Apple Silicon (M系列)",
        "chip_en": "Apple Silicon (M-Series)",
        "short_name": "Apple M-Series",
        "icon": "xi-apple",
        "color_cls": "p-macos-arm64",
    },
    {
        "id": "linux-arm64",
        "name_zh": "Linux",
        "name_en": "Linux",
        "arch_tag": "ARM64",
        "chip_zh": "ARM Neoverse-N2",
        "chip_en": "ARM Neoverse-N2",
        "short_name": "Linux Neoverse",
        "icon": "xi-linux",
        "color_cls": "p-linux-arm64",
    },
    {
        "id": "windows-arm64",
        "name_zh": "Windows",
        "name_en": "Windows",
        "arch_tag": "ARM64",
        "chip_zh": "Snapdragon X / WoA",
        "chip_en": "Snapdragon X / WoA",
        "short_name": "Snapdragon WoA",
        "icon": "xi-windows",
        "color_cls": "p-windows-arm64",
    },
    {
        "id": "macos-x64",
        "name_zh": "macOS",
        "name_en": "macOS",
        "arch_tag": "x86_64",
        "chip_zh": "Intel Core x86_64",
        "chip_en": "Intel Core (x86_64)",
        "short_name": "macOS Intel",
        "icon": "xi-apple",
        "color_cls": "p-macos-x64",
    },
    {
        "id": "linux-x64",
        "name_zh": "Linux",
        "name_en": "Linux",
        "arch_tag": "x86_64",
        "chip_zh": "AMD / Intel x86_64",
        "chip_en": "AMD / Intel (x86_64)",
        "short_name": "Linux x86_64",
        "icon": "xi-linux",
        "color_cls": "p-linux-x64",
    },
    {
        "id": "windows-x64",
        "name_zh": "Windows",
        "name_en": "Windows",
        "arch_tag": "x86_64",
        "chip_zh": "Windows Server x86_64",
        "chip_en": "Windows Server (x86_64)",
        "short_name": "Windows x86_64",
        "icon": "xi-windows",
        "color_cls": "p-windows-x64",
    },
]


def format_ms(val: float | None) -> str:
    if val is None:
        return "—"
    return f"{val:.2f}"


def format_ratio_badge(ratio: float | None) -> str:
    if ratio is None:
        return "—"
    if ratio <= 1.05:
        cls = "bench-badge-fast"
    elif ratio <= 1.5:
        cls = "bench-badge-close"
    elif ratio <= 2.2:
        cls = "bench-badge-mid"
    else:
        cls = "bench-badge-slow"
    return f'<span class="bench-badge {cls}">{ratio:.2f}×</span>'


def parse_fp_min(val_str: str | None) -> float | None:
    """Parse the lower bound number from a footprint range string, e.g. '1.45 – 17.45' -> 1.45."""
    if not val_str:
        return None
    try:
        parts = str(val_str).replace("~", "–").split("–")
        return float(parts[0].strip())
    except Exception:
        return None


def render_workload_block(b_name: str, ref_bench: dict, platforms: dict, cat_cfg: dict, en: bool) -> str:
    """Render a self-contained workload block (e.g. startup) with platforms as columns (horizontal) and languages as rows (vertical). Highlights per-platform best cells."""
    desc = ref_bench["desc_en"] if en else ref_bench["desc_zh"]
    cat_pill = cat_cfg["pill_en"] if en else cat_cfg["pill_zh"]
    active_configs = [c for c in PLATFORMS_CONFIG if c["id"] in platforms]

    # 收集 6 个平台的原始数据
    p_map = {}
    xu_vals = []
    for c in active_configs:
        pid = c["id"]
        b_list = platforms[pid].get("benches", [])
        item = next((x for x in b_list if x["name"] == b_name), None)
        p_map[pid] = item
        if item and item.get("xu_wall_ms") is not None and item["xu_wall_ms"] > 0:
            xu_vals.append((item["xu_wall_ms"], c))

    min_xu_val = min(x[0] for x in xu_vals) if xu_vals else None
    fastest_cfg = next((x[1] for x in xu_vals if x[0] == min_xu_val), None) if min_xu_val else None

    # 计算每一个平台的跨语言最优（绝对最小值）
    p_best_map = {}
    for c in active_configs:
        pid = c["id"]
        item = p_map.get(pid)
        if not item:
            continue
        vals = [
            v for v in [
                item.get("xu_wall_ms"),
                item.get("c_wall_ms"),
                item.get("rust_wall_ms"),
                item.get("swift_wall_ms"),
                item.get("go_wall_ms"),
            ]
            if v is not None and v > 0
        ]
        if vals:
            p_best_map[pid] = min(vals)

    all_ratios = []
    for pid, item in p_map.items():
        if not item or item.get("xu_wall_ms") is None or item["xu_wall_ms"] <= 0:
            continue
        xu_ms = item["xu_wall_ms"]
        peers = [v for v in [item.get("c_wall_ms"), item.get("rust_wall_ms")] if v is not None and v > 0]
        if peers:
            all_ratios.append(xu_ms / min(peers))

    median_ratio = statistics.median(all_ratios) if all_ratios else None

    fastest_str = ""
    if fastest_cfg:
        f_name = fastest_cfg["name_en"] if en else fastest_cfg["name_zh"]
        fastest_str = (
            f'<span class="bench-meta-tag bench-meta-fastest">'
            f'{SVG_BOLT} <span>{"Lowest observed wall time:" if en else "本轮最低 wall 耗时:"} '
            f'<strong>{f_name} {fastest_cfg["arch_tag"]} ({min_xu_val:.2f}ms)</strong></span>'
            f'</span>'
        )

    ratio_str = ""
    if median_ratio:
        badge = format_ratio_badge(median_ratio)
        ratio_str = (
            f'<span class="bench-meta-tag bench-meta-ratio">'
            f'<span>{"Median Xu / best C/Rust:" if en else "Xu / 最佳 C、Rust 中位数:"}</span> {badge}'
            f'</span>'
        )

    # 1. 横向表头：6 个目标平台
    th_cols = [f'<th class="bench-td-lang-cell" style="width: 16%;">{"Language" if en else "实现语言"}</th>']
    for c in active_configs:
        p_name = c["name_en"] if en else c["name_zh"]
        arch = c["arch_tag"]
        icon = c["icon"]
        arch_cls = "arch-arm" if "arm" in arch.lower() else "arch-x64"
        th_cols.append(
            f'<th class="bench-th-platform" style="width: 14%;">'
            f'  <div class="bench-th-pname"><i class="xi {icon}"></i> <span>{p_name}</span> <span class="btn-arch {arch_cls}">{arch}</span></div>'
            f'</th>'
        )

    # 2. 纵向各行：各个对比语言 (Xu, C, Rust, Swift, Go)
    # 行 1: Xu (重点高亮行)
    xu_cells = []
    for c in active_configs:
        pid = c["id"]
        item = p_map.get(pid)
        if not item or item.get("xu_wall_ms") is None or item["xu_wall_ms"] <= 0:
            xu_cells.append('<td class="meta">—</td>')
            continue
        xu_ms = item["xu_wall_ms"]
        peers = [v for v in [item.get("c_wall_ms"), item.get("rust_wall_ms")] if v is not None and v > 0]
        best_peer = min(peers) if peers else None
        ratio = round(xu_ms / best_peer, 2) if (best_peer and xu_ms) else None
        badge = format_ratio_badge(ratio)

        # 单平台最佳判定
        p_best = p_best_map.get(pid)
        is_best = (p_best is not None and abs(xu_ms - p_best) < 1e-4)
        best_cls = " bench-cell-best" if is_best else ""
        best_pill = f' <span class="bench-best-badge">{"Best" if en else "最优"}</span>' if is_best else ""
        val_cls = "bench-xu-val bench-val-best" if is_best else "bench-xu-val"

        xu_cells.append(
            f'<td class="bench-xu-col{best_cls}">'
            f'  <div class="bench-cell-wrap">'
            f'    <div class="bench-val-row">'
            f'      <span class="{val_cls}">{xu_ms:.2f}ms</span>{best_pill}'
            f'    </div>'
            f'    <div class="bench-ratio-sub">{badge}</div>'
            f'  </div>'
            f'</td>'
        )

    # 其余语言行
    peer_rows_def = [
        ("c", "C <small>best O1–O3</small>", "c_wall_ms"),
        ("rs", "Rust <small>best O1–O3</small>", "rust_wall_ms"),
        ("swift", "Swift <small>-O</small>", "swift_wall_ms"),
        ("go", "Go <small>native</small>", "go_wall_ms"),
    ]

    other_rows_html = []
    for cls_key, lang_label, key in peer_rows_def:
        cells = [f'<td class="bench-td-lang-cell"><span class="bench-bar-lang {cls_key}">{lang_label}</span></td>']
        for c in active_configs:
            pid = c["id"]
            item = p_map.get(pid)
            val = item.get(key) if item else None
            if val is not None and val > 0:
                p_best = p_best_map.get(pid)
                is_best = (p_best is not None and abs(val - p_best) < 1e-4)
                if is_best:
                    best_pill = f' <span class="bench-best-badge">{"Best" if en else "最优"}</span>'
                    cells.append(
                        f'<td class="num bench-cell-best">'
                        f'  <div class="bench-cell-wrap">'
                        f'    <div class="bench-val-row">'
                        f'      <strong class="bench-val-best">{val:.2f}ms</strong>{best_pill}'
                        f'    </div>'
                        f'  </div>'
                        f'</td>'
                    )
                else:
                    cells.append(f'<td class="num">{val:.2f}ms</td>')
            else:
                cells.append('<td class="meta">—</td>')
        other_rows_html.append(f'<tr>{"".join(cells)}</tr>')

    xu_row_html = (
        f'<tr class="bench-row-xu">'
        f'  <td class="bench-td-lang-cell"><strong class="bench-bar-lang xu">Xu</strong></td>'
        f'  {"".join(xu_cells)}'
        f'</tr>'
    )

    return f"""
<div class="bench-workload-block" id="workload-{b_name}" data-name="{b_name.lower()}" data-desc="{desc.lower()}">
  <div class="bench-workload-header">
    <div class="bench-workload-title-group">
      <code class="bench-workload-code">{b_name}</code>
      <span class="bench-workload-title">{desc}</span>
      <span class="bench-workload-cat-pill">{cat_pill}</span>
    </div>
    <div class="bench-workload-meta">
      {fastest_str}
      {ratio_str}
    </div>
  </div>
  <div class="bench-workload-table-wrap">
    <table class="bench-workload-table">
      <thead>
        <tr>
          {''.join(th_cols)}
        </tr>
      </thead>
      <tbody>
        {xu_row_html}
        {''.join(other_rows_html)}
      </tbody>
    </table>
  </div>
</div>
"""


def render_category_integrated_section(cat_cfg: dict, platforms: dict, en: bool) -> str:
    ck = cat_cfg["key"]
    cat_title = cat_cfg["name_en"] if en else cat_cfg["name_zh"]
    cat_desc = cat_cfg["desc_en"] if en else cat_cfg["desc_zh"]

    ref_benches = []
    for pid in [c["id"] for c in PLATFORMS_CONFIG]:
        if pid in platforms:
            ref_benches = [b for b in platforms[pid].get("benches", []) if b.get("category") == ck]
            if ref_benches:
                break

    if not ref_benches:
        return ""

    blocks = []
    for b in ref_benches:
        blocks.append(render_workload_block(b["name"], b, platforms, cat_cfg, en))

    cat_count_text = f"{len(ref_benches)} {'workloads' if en else '项算法评测'}"

    return f"""
<div class="bench-cat-section bench-sec-{ck}">
  <div class="bench-cat-section-header">
    <div class="bench-cat-title-wrap">
      <span class="bench-cat-icon">{cat_cfg["icon"]}</span>
      <h3 class="bench-cat-title">{cat_title}</h3>
      <span class="bench-cat-count">{cat_count_text}</span>
    </div>
    <p class="bench-cat-desc">{cat_desc}</p>
  </div>
  <div class="bench-workload-list">
    {''.join(blocks)}
  </div>
</div>
"""


def render_footprint_integrated_section(platforms: dict, en: bool) -> str:
    """Render memory footprint and binary size: platforms as columns (horizontal), languages as rows (vertical). Highlights per-platform best cells."""
    active_configs = [c for c in PLATFORMS_CONFIG if c["id"] in platforms]

    # 计算各平台 RSS 和 Size 的单平台最小值
    platform_min_rss = {}
    platform_min_size = {}

    for c in active_configs:
        pid = c["id"]
        p = platforms[pid]
        fp_list = p.get("footprint", [])
        rss_cands = []
        size_cands = []
        for f in fp_list:
            r = parse_fp_min(f.get("rss"))
            if r is not None and r > 0:
                rss_cands.append(r)
            s = parse_fp_min(f.get("size"))
            if s is not None and s > 0:
                size_cands.append(s)
        if rss_cands:
            platform_min_rss[pid] = min(rss_cands)
        if size_cands:
            platform_min_size[pid] = min(size_cands)

    # 横向表头：6 个目标平台
    th_cols_rss = [f'<th class="bench-td-lang-cell" style="width: 13%;">{"Language" if en else "实现语言"}</th>']
    th_cols_size = [f'<th class="bench-td-lang-cell" style="width: 16%;">{"Language" if en else "实现语言"}</th>']
    for c in active_configs:
        p_name = c["name_en"] if en else c["name_zh"]
        arch = c["arch_tag"]
        icon = c["icon"]
        arch_cls = "arch-arm" if "arm" in arch.lower() else "arch-x64"
        col_html_rss = (
            f'<th class="bench-th-platform" style="width: 11.5%;">'
            f'  <div class="bench-th-pname"><i class="xi {icon}"></i> <span>{p_name}</span> <span class="btn-arch {arch_cls}">{arch}</span></div>'
            f'</th>'
        )
        col_html_size = (
            f'<th class="bench-th-platform" style="width: 14%;">'
            f'  <div class="bench-th-pname"><i class="xi {icon}"></i> <span>{p_name}</span> <span class="btn-arch {arch_cls}">{arch}</span></div>'
            f'</th>'
        )
        th_cols_rss.append(col_html_rss)
        th_cols_size.append(col_html_size)

    th_cols_rss.append(f'<th style="width: 18%; text-align: left; padding-left: 14px;">{"GC Architecture" if en else "内存管理机制"}</th>')

    # 各语言配置定义
    langs_def = [
        ("xu", "Xu", "Xu", "零 GC · 编译期借用与 RAII 确定性析构", "Zero GC / RAII Scope Drop", True),
        ("c", "C <small>-O3</small>", "Clang", "手动 free / 无运行时开销", "Manual free / Zero runtime", False),
        ("rs", "Rust <small>-O3</small>", "rustc", "零 GC · 所有权生命周期与 Drop", "Zero GC / Ownership Drop", False),
        ("swift", "Swift <small>-O</small>", "Swift", "ARC 自动引用计数运行时", "ARC (Automatic Reference Counting)", False),
        ("go", "Go <small>native</small>", "Go", "并发三色标记清除 GC 运行时", "Concurrent Tracing GC Runtime", False),
    ]

    rss_rows = []
    size_rows = []

    for cls_key, label, match_prefix, gc_zh, gc_en, is_xu in langs_def:
        rss_cells = [f'<td class="bench-td-lang-cell"><strong class="bench-bar-lang {cls_key}">{label}</strong></td>' if is_xu else f'<td class="bench-td-lang-cell"><span class="bench-bar-lang {cls_key}">{label}</span></td>']
        size_cells = [f'<td class="bench-td-lang-cell"><strong class="bench-bar-lang {cls_key}">{label}</strong></td>' if is_xu else f'<td class="bench-td-lang-cell"><span class="bench-bar-lang {cls_key}">{label}</span></td>']

        for c in active_configs:
            pid = c["id"]
            p = platforms[pid]
            fp_list = p.get("footprint", [])
            fp = next((f for f in fp_list if match_prefix.lower() in f["impl"].lower()), None)
            
            if fp and fp.get("rss"):
                val_rss = f"{fp['rss']} MiB"
                num_rss = parse_fp_min(fp["rss"])
                p_min = platform_min_rss.get(pid)
                is_best = (num_rss is not None and p_min is not None and abs(num_rss - p_min) < 1e-4)

                if is_best:
                    best_pill = f' <span class="bench-best-badge">{"Best" if en else "最优"}</span>'
                    rss_cells.append(
                        f'<td class="bench-cell-best">'
                        f'  <div class="bench-cell-wrap">'
                        f'    <div class="bench-val-row">'
                        f'      <strong class="bench-val-best">{val_rss}</strong>{best_pill}'
                        f'    </div>'
                        f'  </div>'
                        f'</td>'
                    )
                elif is_xu:
                    rss_cells.append(f'<td class="bench-xu-col"><strong>{val_rss}</strong></td>')
                else:
                    rss_cells.append(f'<td class="num">{val_rss}</td>')
            else:
                rss_cells.append('<td class="meta">—</td>')

            if fp and fp.get("size"):
                val_size = f"{fp['size']} KiB"
                num_size = parse_fp_min(fp["size"])
                p_min = platform_min_size.get(pid)
                is_best = (num_size is not None and p_min is not None and abs(num_size - p_min) < 1e-4)

                if is_best:
                    best_pill = f' <span class="bench-best-badge">{"Best" if en else "最优"}</span>'
                    size_cells.append(
                        f'<td class="bench-cell-best">'
                        f'  <div class="bench-cell-wrap">'
                        f'    <div class="bench-val-row">'
                        f'      <strong class="bench-val-best">{val_size}</strong>{best_pill}'
                        f'    </div>'
                        f'  </div>'
                        f'</td>'
                    )
                elif is_xu:
                    size_cells.append(f'<td class="bench-xu-col"><strong>{val_size}</strong></td>')
                else:
                    size_cells.append(f'<td class="num">{val_size}</td>')
            else:
                size_cells.append('<td class="meta">—</td>')

        # 内存管理机制说明单元格
        gc_text = gc_en if en else gc_zh
        rss_cells.append(f'<td style="text-align: left; padding-left: 14px;"><small>{gc_text}</small></td>')

        row_cls = ' class="bench-row-xu"' if is_xu else ''
        rss_rows.append(f'<tr{row_cls}>{"".join(rss_cells)}</tr>')
        size_rows.append(f'<tr{row_cls}>{"".join(size_cells)}</tr>')

    sec_title = "Memory Footprint & Binary Size (All Platforms & Languages)" if en else "全平台内存常驻与独立二进制体积横向综合评测"
    sec_desc = (
        "Accurately comparing Xu against C, Rust, Swift, and Go across all 6 OS and architecture platforms (wait4/Win32 native capture):"
        if en
        else "在全 6 组操作系统与芯片架构下，横向对照各平台、纵向对照各语言的峰值常驻内存（wait4/Win32 原生捕获）与未裁剪独立体积："
    )

    h3_rss = "1. Peak Resident Memory across Platforms & Languages (RSS, lower is better)" if en else "1. 各语言在全平台的峰值常驻内存横向对照 (Peak RSS，越低越好)"
    h3_size = "2. Standalone Binary Size across Platforms & Languages (Unstripped on-disk size, smaller is better)" if en else "2. 各语言在全平台的未裁剪独立二进制体积横向对照 (Binary Size，越小越好)"

    return f"""
<div class="bench-cat-section bench-sec-footprint">
  <div class="bench-cat-section-header">
    <div class="bench-cat-title-wrap">
      <span class="bench-cat-icon">{SVG_BRAIN}</span>
      <h3 class="bench-cat-title">{sec_title}</h3>
      <span class="bench-cat-count">{'All Peers Compared' if en else '5 语言全平台横测'}</span>
    </div>
    <p class="bench-cat-desc">{sec_desc}</p>
  </div>

  <!-- 1. RSS 对比表：横向各平台，纵向各语言 -->
  <div class="bench-subtable-title"><strong>{h3_rss}</strong></div>
  <div class="bench-workload-table-wrap" style="margin-bottom: 24px;">
    <table class="bench-workload-table">
      <thead>
        <tr>
          {''.join(th_cols_rss)}
        </tr>
      </thead>
      <tbody>
        {''.join(rss_rows)}
      </tbody>
    </table>
  </div>

  <!-- 2. Binary Size 对比表：横向各平台，纵向各语言 -->
  <div class="bench-subtable-title"><strong>{h3_size}</strong></div>
  <div class="bench-workload-table-wrap">
    <table class="bench-workload-table">
      <thead>
        <tr>
          {''.join(th_cols_size)}
        </tr>
      </thead>
      <tbody>
        {''.join(size_rows)}
      </tbody>
    </table>
  </div>
</div>
"""


def render_page(data: dict, lang: str) -> str:
    en = lang == "en"
    meta = data["metadata"]
    version = meta.get("xu_version", "")
    if not re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", version):
        raise ValueError(f"Official benchmark requires an official release (x.y.z), got: {version}")
    platforms = data.get("platforms", {})
    categories = data["categories"]
    workload_count = meta["total_benches"]

    title = (
        "Benchmarks — Cross-Language & Multi-Architecture Performance"
        if en
        else f"横向测评 — {workload_count} 项跨语言与双架构性能实测"
    )

    h1_text = (
        "Multi-Architecture Cross-Language Benchmarks"
        if en
        else "全量跨语言与双架构性能基准评测"
    )

    lead_text = (
        f"Rigorous, reproducible cross-language benchmarks comparing Xu v{meta['xu_version']} "
        f"against C (best Clang O1–O3), Rust (best rustc O1–O3), Swift (swiftc -O), and Go (go build) across {workload_count} measured workloads. "
        f"Concurrently verified across dual architectures (ARM64 & x86_64) on macOS, Linux, and Windows."
        if en
        else f"严谨、可复现的跨语言横向评测：在 {workload_count} 个实测负载下，将 Xu v{meta['xu_version']} "
        f"与 C（Clang O1–O3 最佳）、Rust（rustc O1–O3 最佳）、Swift（swiftc -O） 及 Go (go build) 进行同算法全维度对照。"
        f"覆盖 ARM64 与 x86_64 双架构，以及 macOS、Linux、Windows 三大操作系统自动化 CI 实测。"
    )

    meta_text = (
        f"Updated: {meta['date']} · Measured Xu v{meta['xu_version']} · Dual-Architecture (ARM64 + x86_64)"
        if en
        else f"更新于 {meta['date']} · 实测 Xu v{meta['xu_version']} · 双架构（ARM64 + x86_64）多平台实测"
    )

    banner_text = (
        'Continuous benchmarks run automatically in GitHub Actions CI across macOS, Linux, and Windows (ARM64 + x86_64). '
        'Suite source code and test harness are fully open-source in the '
        '<a href="https://github.com/xulang-org/bench" target="_blank" rel="noopener noreferrer">bench repository</a>. '
        'Raw dataset: <a href="/benchmarks.json">benchmarks.json</a>.'
        if en
        else '横向基准测试由 GitHub Actions CI 自动化流水线在 macOS、Linux、Windows 双架构（ARM64 + x86_64）环境下并行运行。'
        '全量评测源码与测量方法完全开源于 '
        '<a href="https://github.com/xulang-org/bench" target="_blank" rel="noopener noreferrer">bench 仓库</a>。'
        '原始结构化数据集：<a href="/benchmarks.json">benchmarks.json</a>。'
    )

    run_url = html.escape(meta.get("run_url", "https://github.com/xulang-org/bench"), quote=True)
    commit = html.escape(meta.get("xu_commit", "unrecorded"))
    banner_text += (
        f' <a href="{run_url}">Source Actions run</a> · Xu <code>{commit}</code>. '
        'Ratios use the lowest same-platform C/Rust O1–O3 median. A dash means no measurement. '
        'Different runner timings are not speedup evidence. SHA-256 uses hardware instructions when '
        'available on ARM64; x64 currently uses software. Cryptographic library paths may differ.'
        if en else
        f' <a href="{run_url}">来源 Actions 运行</a> · Xu <code>{commit}</code>。'
        '倍数使用同平台 C、Rust O1–O3 中位数的最小值；横线表示没有实测数据。'
        '不同机器的绝对耗时不能作为加速证据。SHA-256 在支持的 ARM64 上使用硬件指令，'
        'x64 当前使用软件路径；各语言密码库采用的路径可能不同。'
    )

    # 1. 功能大类平铺区块列表
    category_sections = []
    anchor_buttons = []
    any_p = next(iter(platforms.values()), {})

    for cat_cfg in CATEGORIES_CONFIG:
        ck = cat_cfg["key"]
        sec_html = render_category_integrated_section(cat_cfg, platforms, en)
        if sec_html:
            category_sections.append(sec_html)
            pill_name = cat_cfg["pill_en"] if en else cat_cfg["pill_zh"]
            icon = cat_cfg["icon"]
            count = len([b for b in any_p.get("benches", []) if b.get("category") == ck])
            count_tag = f'<span class="badge">{count}</span>' if count else ""
            anchor_buttons.append(
                f'<button type="button" class="bench-anchor-pill" onclick="jumpToBenchSection(\'{ck}\')">'
                f'{icon} <span>{pill_name}</span> {count_tag}'
                f'</button>'
            )

    # 2. 内存与体积横向综合评测
    footprint_section = render_footprint_integrated_section(platforms, en)

    # Methodology section
    method_h2 = "Methodology & Reproducibility" if en else "评测准则与环境公开"
    method_p1 = (
        "<ul><li>Seven whole-program samples per implementation; wall time is the median, including process startup.</li>"
        "<li>C and Rust rows select the lowest measured median among O1/O2/O3 for that workload and platform. Go and Swift show only measured implementations.</li>"
        "<li>Every Xu workload output and exit status passed the benchmark harness. All six compiler identities match the recorded commit, version, source closure and Gen2=Gen3.</li>"
        "<li>RSS and binary-size ranges are derived from the measured workloads. O3 builds are used for the C/Rust footprint rows.</li>"
        "<li>Runner hardware, libraries, startup costs and hardware acceleration differ. Compare ratios within one platform; do not interpret cross-machine timing changes as optimization speedups.</li></ul>"
        if en else
        "<ul><li>每项实现运行七次，展示整进程 wall 耗时中位数，包含进程启动。</li>"
        "<li>C、Rust 行分别取该负载同平台 O1/O2/O3 中位数最小值；Go、Swift 仅展示实测实现。</li>"
        "<li>全部 Xu 负载的输出与退出状态通过校验；六份编译器身份的提交、版本、源闭包和 Gen2=Gen3 已核验。</li>"
        "<li>RSS 与体积范围来自本轮实测负载；C、Rust 的资源表使用 O3 构建。</li>"
        "<li>机器、库实现、启动成本和硬件加速路径不同，应在同一平台内比较倍数，不能把跨机器耗时变化当作优化收益。</li></ul>"
    )

    search_placeholder = "Search workload or algorithm across all sections..." if en else "全局搜索算法用例或说明 (如 startup, matmul, aes)..."

    bench_script = """
<script>
function jumpToBenchSection(secKey) {
  var target = document.querySelector('.bench-sec-' + secKey);
  if (target) {
    var nav = document.querySelector('.bench-tabs-wrapper');
    var navHeight = nav ? nav.offsetHeight : 80;
    var targetTop = target.getBoundingClientRect().top + window.pageYOffset - navHeight - 16;
    window.scrollTo({ top: targetTop, behavior: 'smooth' });
  }
}

function searchBenchAll(query) {
  var q = (query || '').toLowerCase().trim();
  var blocks = document.querySelectorAll('.bench-workload-block');
  var secCounts = {};

  blocks.forEach(function(block) {
    var name = block.getAttribute('data-name') || '';
    var desc = block.getAttribute('data-desc') || '';
    var sec = block.closest('.bench-cat-section');
    var secClass = sec ? sec.className : '';

    if (!q || name.indexOf(q) !== -1 || desc.indexOf(q) !== -1) {
      block.style.display = '';
      if (secClass) secCounts[secClass] = (secCounts[secClass] || 0) + 1;
    } else {
      block.style.display = 'none';
    }
  });

  document.querySelectorAll('.bench-cat-section').forEach(function(sec) {
    if (sec.classList.contains('bench-sec-footprint')) return;
    var count = secCounts[sec.className] || 0;
    if (q && count === 0) {
      sec.style.display = 'none';
    } else {
      sec.style.display = '';
    }
  });
}
</script>
"""

    return f"""<!--title: {title}-->
<div class="hero bench-hero">
  <div>
    <p class="banner"><i class="xi xi-benchmark xi-brand"></i> {meta_text}</p>
    <h1>{h1_text}</h1>
    <p class="lead">{lead_text}</p>
  </div>
</div>

<p class="banner">{banner_text}</p>

<div class="bench-tabs-wrapper">
  <div class="bench-sticky-topline">
    <div style="display: flex; align-items: center; gap: 8px;">
      <h2 style="margin: 0; font-size: 17px; font-weight: 700;">{'Cross-Architecture Benchmark Suite' if en else '全量架构性能评测工作集'}</h2>
      <span class="meta" style="margin: 0; font-size: 12px;">{f'{workload_count} Measured Workloads · 6 Platforms' if en else f'{workload_count} 项实测负载 · 6 个平台'}</span>
    </div>
  </div>
  <div class="bench-anchor-bar">
    <div class="bench-anchor-links">
      <button type="button" class="bench-anchor-pill" onclick="jumpToBenchSection('footprint')">
        {SVG_BRAIN} <span>{'Memory & Size' if en else '内存与体积'}</span>
      </button>
      {''.join(anchor_buttons)}
    </div>
    <div class="bench-search-wrap bench-search-global">
      {SVG_SEARCH}
      <input type="text" class="bench-search-input" id="bench-global-search" placeholder="{search_placeholder}" oninput="searchBenchAll(this.value)" />
    </div>
  </div>
</div>

<!-- 1. 全平台内存与体积横向综合评测 (位于 Control Flow 之上) -->
{footprint_section}

<!-- 2. 功能大类全平台合一平铺 (按功能，各平台直接铺开) -->
{''.join(category_sections)}

<h2>{method_h2}</h2>
{method_p1}

<p class="meta">
  <a href="/docs/status">{'View Limitations & Status' if en else '查看语言规范与现状限制'}</a> · 
  <a href="/download">{'Download Compiler' if en else '下载 Xu 编译器'}</a> · 
  <a href="https://github.com/xulang-org/bench" target="_blank" rel="noopener noreferrer">{'Benchmark Suite on GitHub' if en else 'GitHub 基准测试套件源码'}</a>
</p>
{bench_script}
"""


def main():
    if not DATA_FILE.is_file():
        raise SystemExit(f"Data file missing: {DATA_FILE}")

    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))

    zh_content = render_page(data, "zh")
    en_content = render_page(data, "en")

    zh_out = ROOT / "content/zh/benchmarks.html"
    en_out = ROOT / "content/en/benchmarks.html"

    zh_out.write_text("\n".join(line.rstrip() for line in zh_content.splitlines()) + "\n", encoding="utf-8")
    en_out.write_text("\n".join(line.rstrip() for line in en_content.splitlines()) + "\n", encoding="utf-8")

    print(f"Generated {zh_out}")
    print(f"Generated {en_out}")


if __name__ == "__main__":
    main()
