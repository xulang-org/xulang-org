#!/usr/bin/env python3
"""Generate official multi-architecture benchmark pages for English and Chinese from benchmarks.json."""
from __future__ import annotations

import json
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
        "desc_zh": "评测空 main 冷启动、整数循环累加、深度递归、分支预测敏感度、模式匹配展开、defer 释放开销及异常捕获等语言机制开销。",
        "desc_en": "Evaluates empty-main startup, loop accumulation, deep recursion, branch prediction, pattern matching, defer cleanup, and exception handling overhead.",
        "icon": SVG_CONTROL,
    },
    {
        "key": "algo",
        "name_zh": "数值算法与密集计算",
        "name_en": "Numerical Algorithms & Compute",
        "pill_zh": "数值算法",
        "pill_en": "Algorithms",
        "desc_zh": "高强度数值计算与矩阵代数：包含双精度矩阵乘法、N 体天体轨道动力学模拟、Mandelbrot 复数分形、谱范数逼近、素数筛选及快速排序。",
        "desc_en": "Compute-intensive numerical algorithms: matrix multiplication, N-body orbital dynamics, Mandelbrot fractals, spectral norm, prime sieve, and quicksort.",
        "icon": SVG_ALGO,
    },
    {
        "key": "data",
        "name_zh": "数据结构与内存访问模式",
        "name_en": "Data Structures & Memory Access",
        "pill_zh": "数据结构",
        "pill_en": "Data Structures",
        "desc_zh": "三维向量 SROA 标量寄存器拆解、动态向量扩容、高频哈希表读写、二叉树构建遍历、双向链表、LRU 缓存淘汰与无锁环形缓冲区。",
        "desc_en": "Scalar replacement of aggregates (SROA), dynamic vector resizing, hashmap inserts/lookups, binary trees, linked lists, LRU cache, and ring buffers.",
        "icon": SVG_DATA,
    },
    {
        "key": "string",
        "name_zh": "字符串处理与文本 I/O",
        "name_en": "Strings & Text I/O",
        "pill_zh": "文本与I/O",
        "pill_en": "Strings & I/O",
        "desc_zh": "字符串快速拼接缓冲、正则表达式编译匹配、JSON 词法语法解析、Base64 编解码、UTF-8 字符流校验及顺序文件吞吐量。",
        "desc_en": "String buffer concatenation, regex matching, JSON parsing, Base64 encoding, UTF-8 validation, sequential file throughput, and CSV processing.",
        "icon": SVG_STRING,
    },
    {
        "key": "crypto",
        "name_zh": "现代密码学与散列摘要",
        "name_en": "Modern Cryptography & Hashing",
        "pill_zh": "现代密码学",
        "pill_en": "Cryptography",
        "desc_zh": "AES-128/256 软件对称加密、SHA-256/512 哈希链、BLAKE3 高吞吐哈希、ChaCha20 流密码、Ed25519 签名与验签、RSA-2048 及 HMAC-SHA256。",
        "desc_en": "AES-128/256 symmetric ciphers, SHA-256/512 chains, BLAKE3 high-throughput hash, ChaCha20 stream cipher, Ed25519 signatures, RSA-2048, and HMAC.",
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


def render_cross_platform_panorama(platforms: dict, en: bool) -> str:
    """Render the master cross-platform panorama charts comparing all 6 platforms side-by-side."""
    key_chart_items = [
        ("startup", "进程启动 / 空 main", "Process startup / empty main", "越短越快 (ms)", "lower is better (ms)"),
        ("loop_sum", "整数累加循环 (1 亿次)", "Integer loop accumulation (100M)", "越短越快 (ms)", "lower is better (ms)"),
        ("matmul", "矩阵乘法 (i64 matmul)", "Matrix multiplication (i64)", "越短越快 (ms)", "lower is better (ms)"),
        ("chan_ping", "Channel 协程流水线", "Channel / Coroutines ping-pong", "越短越快 (ms)", "lower is better (ms)"),
        ("aes128_encrypt", "AES-128 软件加密", "AES-128 software encrypt", "越短越快 (ms)", "lower is better (ms)"),
        ("sha256_chain", "SHA-256 散列链", "SHA-256 hash chain", "越短越快 (ms)", "lower is better (ms)"),
    ]

    cards = []
    for b_name, title_zh, title_en, unit_zh, unit_en in key_chart_items:
        title = title_en if en else title_zh
        unit = unit_en if en else unit_zh

        series = []
        for pcfg in PLATFORMS_CONFIG:
            pid = pcfg["id"]
            if pid not in platforms:
                continue
            b_list = platforms[pid].get("benches", [])
            b_item = next((x for x in b_list if x["name"] == b_name), None)
            if b_item and b_item.get("xu_wall_ms") is not None:
                short = pcfg["short_name"]
                series.append((short, pcfg["color_cls"], b_item["xu_wall_ms"]))

        if not series:
            continue

        min_val = min(s[2] for s in series)
        max_val = max(s[2] for s in series) or 1.0

        bar_rows = []
        for label, cls, val in series:
            pct = max(10, int((val / max_val) * 100))
            is_fastest = (val == min_val)
            lead_tag = f' <span class="lead-tag">{"fastest" if en else "最快"}</span>' if is_fastest else ""
            bar_rows.append(
                f'<div class="bench-bar-row">'
                f'<span class="bench-bar-lang {cls}">{label}</span>'
                f'<div class="bench-bar-track">'
                f'<div class="bench-bar-fill {cls}" style="width: {pct}%;"></div>'
                f'</div>'
                f'<span class="bench-bar-val"><strong>{val:.2f}ms</strong>{lead_tag}</span>'
                f'</div>'
            )

        card_html = (
            f'<div class="bench-chart-card">'
            f'<div class="bench-chart-card-header">'
            f'<span class="bench-chart-card-title"><code>{b_name}</code> · {title}</span>'
            f'<span class="bench-chart-card-unit">{unit}</span>'
            f'</div>'
            f'<div class="bench-chart-bars">'
            f'{"".join(bar_rows)}'
            f'</div>'
            f'</div>'
        )
        cards.append(card_html)

    # Cross-Platform Peak RSS Chart
    rss_series = []
    size_series = []
    for pcfg in PLATFORMS_CONFIG:
        pid = pcfg["id"]
        if pid not in platforms:
            continue
        p = platforms[pid]
        fp_list = p.get("footprint", [])
        xu_fp = next((f for f in fp_list if f["impl"] == "Xu"), None)
        if xu_fp:
            try:
                raw_rss = xu_fp["rss"].split("–")[-1].replace("MiB", "").strip()
                raw_size = xu_fp["size"].split("–")[-1].replace("KiB", "").strip()
                rss_series.append((pcfg["short_name"], pcfg["color_cls"], float(raw_rss)))
                size_series.append((pcfg["short_name"], pcfg["color_cls"], float(raw_size)))
            except Exception:
                pass

    if rss_series:
        min_rss = min(s[2] for s in rss_series)
        max_rss = max(s[2] for s in rss_series) or 1.0
        rss_rows = []
        for label, cls, val in rss_series:
            pct = max(10, int((val / max_rss) * 100))
            is_fast = (val == min_rss)
            tag = f' <span class="lead-tag">{"lowest" if en else "最低"}</span>' if is_fast else ""
            rss_rows.append(
                f'<div class="bench-bar-row">'
                f'<span class="bench-bar-lang {cls}">{label}</span>'
                f'<div class="bench-bar-track">'
                f'<div class="bench-bar-fill {cls}" style="width: {pct}%;"></div>'
                f'</div>'
                f'<span class="bench-bar-val"><strong>{val:.1f} MiB</strong>{tag}</span>'
                f'</div>'
            )
        cards.append(
            f'<div class="bench-chart-card">'
            f'<div class="bench-chart-card-header">'
            f'<span class="bench-chart-card-title">{SVG_BRAIN} {"全平台峰值内存水位 (Peak RSS)" if not en else "Cross-Platform Peak RSS"}</span>'
            f'<span class="bench-chart-card-unit">{"越低越好 (MiB)" if not en else "lower is better"}</span>'
            f'</div>'
            f'<div class="bench-chart-bars">{"".join(rss_rows)}</div>'
            f'</div>'
        )

    if size_series:
        min_size = min(s[2] for s in size_series)
        max_size = max(s[2] for s in size_series) or 1.0
        size_rows = []
        for label, cls, val in size_series:
            pct = max(8, int((val / max_size) * 100))
            is_fast = (val == min_size)
            tag = f' <span class="lead-tag">{"smallest" if en else "最精炼"}</span>' if is_fast else ""
            size_rows.append(
                f'<div class="bench-bar-row">'
                f'<span class="bench-bar-lang {cls}">{label}</span>'
                f'<div class="bench-bar-track">'
                f'<div class="bench-bar-fill {cls}" style="width: {pct}%;"></div>'
                f'</div>'
                f'<span class="bench-bar-val"><strong>{val:.0f} KiB</strong>{tag}</span>'
                f'</div>'
            )
        cards.append(
            f'<div class="bench-chart-card">'
            f'<div class="bench-chart-card-header">'
            f'<span class="bench-chart-card-title">{SVG_BOX} {"全平台未裁剪二进制体积 (Binary Size)" if not en else "Cross-Platform Binary Size"}</span>'
            f'<span class="bench-chart-card-unit">{"越小越好 (KiB)" if not en else "lower is better"}</span>'
            f'</div>'
            f'<div class="bench-chart-bars">{"".join(size_rows)}</div>'
            f'</div>'
        )

    dash_title = f"{SVG_BOLT} 6 大主流目标平台核心性能横向直观对比看板" if not en else f"{SVG_BOLT} 6-Platform Core Workloads Cross-Architecture Panorama"
    dash_desc = (
        "无需切换 Tab，直接横览 Xu 在全部 6 组操作系统与芯片架构（ARM64 / x86_64）下的实测耗时与资源消耗，柱状条越短越快："
        if not en
        else "Inspect Xu's measured performance directly across all 6 OS and hardware architecture configurations side-by-side. Shorter is faster:"
    )

    return f"""
<div class="bench-visual-dashboard">
  <div class="bench-chart-section-title">{dash_title}</div>
  <p class="meta">{dash_desc}</p>
  <div class="bench-chart-grid">
    {''.join(cards)}
  </div>
</div>
"""


def render_workload_block(b_name: str, ref_bench: dict, platforms: dict, cat_cfg: dict, en: bool) -> str:
    """Render a dedicated, self-contained workload block (e.g. startup) comparing all 6 platforms and peer languages side-by-side."""
    desc = ref_bench["desc_en"] if en else ref_bench["desc_zh"]
    cat_pill = cat_cfg["pill_en"] if en else cat_cfg["pill_zh"]
    active_configs = [c for c in PLATFORMS_CONFIG if c["id"] in platforms]

    p_data = []
    xu_vals = []
    for c in active_configs:
        pid = c["id"]
        b_list = platforms[pid].get("benches", [])
        item = next((x for x in b_list if x["name"] == b_name), None)
        if item and item.get("xu_wall_ms") is not None:
            xu_vals.append((item["xu_wall_ms"], c))
            p_data.append((c, item))
        else:
            p_data.append((c, None))

    min_xu_val = min(x[0] for x in xu_vals) if xu_vals else None
    fastest_cfg = next((x[1] for x in xu_vals if x[0] == min_xu_val), None) if min_xu_val else None

    all_ratios = []
    for _, item in p_data:
        if not item or item.get("xu_wall_ms") is None:
            continue
        xu_ms = item["xu_wall_ms"]
        peers = [v for v in [item.get("c_wall_ms"), item.get("rust_wall_ms"), item.get("swift_wall_ms"), item.get("go_wall_ms")] if v is not None and v > 0]
        if peers:
            all_ratios.append(xu_ms / min(peers))

    median_ratio = sorted(all_ratios)[len(all_ratios) // 2] if all_ratios else None

    fastest_str = ""
    if fastest_cfg:
        f_name = fastest_cfg["name_en"] if en else fastest_cfg["name_zh"]
        fastest_str = (
            f'<span class="bench-meta-tag bench-meta-fastest">'
            f'{SVG_BOLT} <span>{"Fastest:" if en else "最快架构:"} '
            f'<strong>{f_name} {fastest_cfg["arch_tag"]} ({min_xu_val:.2f}ms)</strong></span>'
            f'</span>'
        )

    ratio_str = ""
    if median_ratio:
        badge = format_ratio_badge(median_ratio)
        ratio_str = (
            f'<span class="bench-meta-tag bench-meta-ratio">'
            f'<span>{"Median vs Best Peer:" if en else "中位对比最佳:"}</span> {badge}'
            f'</span>'
        )

    table_rows = []
    for c, item in p_data:
        p_name = c["name_en"] if en else c["name_zh"]
        arch = c["arch_tag"]
        chip = c["chip_en"] if en else c["chip_zh"]
        icon = c["icon"]
        arch_cls = "arch-arm" if "arm" in arch.lower() else "arch-x64"

        if not item or item.get("xu_wall_ms") is None:
            table_rows.append(
                f'<tr>'
                f'  <td>'
                f'    <div class="bench-td-platform">'
                f'      <i class="xi {icon}"></i>'
                f'      <strong>{p_name}</strong>'
                f'      <span class="btn-arch {arch_cls}">{arch}</span>'
                f'      <span class="bench-chip-label">{chip}</span>'
                f'    </div>'
                f'  </td>'
                f'  <td colspan="6" class="meta">—</td>'
                f'</tr>'
            )
            continue

        xu_ms = item["xu_wall_ms"]
        c_ms = item.get("c_wall_ms")
        rust_ms = item.get("rust_wall_ms")
        swift_ms = item.get("swift_wall_ms")
        go_ms = item.get("go_wall_ms")

        peers = [v for v in [c_ms, rust_ms, swift_ms, go_ms] if v is not None and v > 0]
        best_peer = min(peers) if peers else None
        ratio = round(xu_ms / best_peer, 2) if (best_peer and xu_ms) else None
        badge = format_ratio_badge(ratio)

        is_fastest = (xu_ms == min_xu_val)
        fastest_tag = f' <span class="lead-tag">{"fastest" if en else "最快"}</span>' if is_fastest else ""
        row_cls = " class=\"bench-row-fastest\"" if is_fastest else ""

        table_rows.append(
            f'<tr{row_cls}>'
            f'  <td>'
            f'    <div class="bench-td-platform">'
            f'      <i class="xi {icon}"></i>'
            f'      <strong>{p_name}</strong>'
            f'      <span class="btn-arch {arch_cls}">{arch}</span>'
            f'      <span class="bench-chip-label">{chip}</span>'
            f'    </div>'
            f'  </td>'
            f'  <td class="bench-xu-col"><strong>{xu_ms:.2f}</strong>{fastest_tag}</td>'
            f'  <td class="num">{format_ms(c_ms)}</td>'
            f'  <td class="num">{format_ms(rust_ms)}</td>'
            f'  <td class="num">{format_ms(swift_ms)}</td>'
            f'  <td class="num">{format_ms(go_ms)}</td>'
            f'  <td class="bench-ratio-col">{badge}</td>'
            f'</tr>'
        )

    th_platform = "Platform & Architecture" if en else "目标平台与芯片架构"
    th_xu = "Xu (ms)"
    th_c = "C (Clang -O3, ms)"
    th_rust = "Rust (rustc -O3, ms)"
    th_swift = "Swift (-O3, ms)"
    th_go = "Go (native, ms)"
    th_ratio = "Xu / Best Peer" if en else "Xu / 最佳对照"

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
  <div class="doc-table-wrap bench-table-wrap">
    <table class="bench-workload-table">
      <thead>
        <tr>
          <th>{th_platform}</th>
          <th class="bench-xu-col">{th_xu}</th>
          <th>{th_c}</th>
          <th>{th_rust}</th>
          <th>{th_swift}</th>
          <th>{th_go}</th>
          <th class="bench-ratio-col">{th_ratio}</th>
        </tr>
      </thead>
      <tbody>
        {''.join(table_rows)}
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
    active_configs = [c for c in PLATFORMS_CONFIG if c["id"] in platforms]

    th_platform = "Platform & Architecture" if en else "目标平台与芯片架构"
    th_chip = "Chip / Hardware" if en else "处理器芯片"
    th_cold = "Cold Startup" if en else "空 main 冷启动"
    th_xu_rss = "Xu Peak RSS" if en else "Xu 峰值常驻内存 (RSS)"
    th_peer_rss = "Peers RSS Range" if en else "对照语言 RSS 范围"
    th_xu_size = "Xu Standalone Size" if en else "Xu 独立二进制体积"
    th_peer_size = "Peers Size Range" if en else "对照语言体积范围"
    th_gc = "GC Architecture" if en else "内存管理机制"

    tbody_rows = []
    for c in active_configs:
        pid = c["id"]
        p = platforms[pid]
        p_name = c["name_en"] if en else c["name_zh"]
        arch = c["arch_tag"]
        chip = c["chip_en"] if en else c["chip_zh"]
        icon = c["icon"]
        arch_cls = "arch-arm" if "arm" in arch.lower() else "arch-x64"
        startup_ms = p.get("startup_ms", 3.5)

        fp_list = p.get("footprint", [])
        xu_fp = next((f for f in fp_list if f["impl"] == "Xu"), None)
        xu_rss = xu_fp["rss"] if xu_fp else "—"
        xu_size = xu_fp["size"] if xu_fp else "—"
        gc_text = xu_fp.get("gc_en" if en else "gc_zh", "Immix-GC") if xu_fp else "Immix-GC"

        peer_fps = [f for f in fp_list if f["impl"] != "Xu"]
        if peer_fps:
            peer_rss_str = f"{min(f['rss'] for f in peer_fps)} ~ {max(f['rss'] for f in peer_fps)}"
            peer_size_str = f"{min(f['size'] for f in peer_fps)} ~ {max(f['size'] for f in peer_fps)}"
        else:
            peer_rss_str = "—"
            peer_size_str = "—"

        tbody_rows.append(
            f'<tr>'
            f'  <td>'
            f'    <div class="bench-td-platform">'
            f'      <i class="xi {icon}"></i>'
            f'      <strong>{p_name}</strong>'
            f'      <span class="btn-arch {arch_cls}">{arch}</span>'
            f'    </div>'
            f'  </td>'
            f'  <td><code>{chip}</code></td>'
            f'  <td class="bench-xu-col"><strong>{startup_ms:.1f}ms</strong></td>'
            f'  <td class="bench-xu-col"><strong>{xu_rss}</strong></td>'
            f'  <td class="num">{peer_rss_str}</td>'
            f'  <td class="bench-xu-col"><strong>{xu_size}</strong></td>'
            f'  <td class="num">{peer_size_str}</td>'
            f'  <td><small>{gc_text}</small></td>'
            f'</tr>'
        )

    title = "Memory Footprint & Standalone Binary Size (All 6 Platforms)" if en else "全平台内存常驻与独立二进制体积横向综合评测"
    desc = (
        "Comparing Xu's resident memory (RSS, captured natively via wait4/Win32) and unstripped standalone binary size across all 6 OS and architecture targets:"
        if en
        else "全 6 组目标操作系统与芯片架构下，Xu 峰值常驻内存（系统调用 wait4/Win32 原生捕获）与未裁剪独立二进制体积横向对比："
    )

    return f"""
<div class="bench-cat-section bench-sec-footprint">
  <div class="bench-cat-section-header">
    <div class="bench-cat-title-wrap">
      <span class="bench-cat-icon">{SVG_BRAIN}</span>
      <h3 class="bench-cat-title">{title}</h3>
      <span class="bench-cat-count">{'System Footprint' if en else '系统级开销'}</span>
    </div>
    <p class="bench-cat-desc">{desc}</p>
  </div>
  <div class="doc-table-wrap bench-table-wrap">
    <table class="bench-workload-table">
      <thead>
        <tr>
          <th>{th_platform}</th>
          <th>{th_chip}</th>
          <th>{th_cold}</th>
          <th class="bench-xu-col">{th_xu_rss}</th>
          <th>{th_peer_rss}</th>
          <th class="bench-xu-col">{th_xu_size}</th>
          <th>{th_peer_size}</th>
          <th>{th_gc}</th>
        </tr>
      </thead>
      <tbody>
        {''.join(tbody_rows)}
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

    title = (
        "Benchmarks — Cross-Language & Multi-Architecture Performance"
        if en
        else "横向测评 — 47 项跨语言与双架构性能实测"
    )

    h1_text = (
        "Multi-Architecture Cross-Language Benchmarks"
        if en
        else "全量跨语言与双架构性能基准评测"
    )

    lead_text = (
        f"Rigorous, reproducible cross-language benchmarks comparing Xu v{meta['xu_version']} "
        f"against C (Clang -O3), Rust (rustc -O3), Swift (swiftc -O3), and Go (go build) across 47 real-world algorithms. "
        f"Concurrently verified across dual architectures (ARM64 & x86_64) on macOS, Linux, and Windows."
        if en
        else f"严谨、可复现的跨语言横向评测：在 47 个真实算法与业务负载下，将 Xu v{meta['xu_version']} "
        f"与 C (Clang -O3)、Rust (rustc -O3)、Swift (swiftc -O3) 及 Go (go build) 进行同算法全维度对照。"
        f"覆盖 ARM64 与 x86_64 双架构，以及 macOS、Linux、Windows 三大操作系统自动化 CI 实测。"
    )

    meta_text = (
        f"Updated: {meta['date']} · Verified against official SDK v{meta['xu_version']} · Dual-Architecture (ARM64 + x86_64)"
        if en
        else f"更新于 {meta['date']} · 对应官方 SDK v{meta['xu_version']} · 双架构（ARM64 + x86_64）多平台实测"
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

    # 1. 核心用例跨架构横向柱状图看板 (放下面)
    cross_platform_panorama = render_cross_platform_panorama(platforms, en)

    # 2. 功能大类平铺区块列表
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

    # 3. 内存与体积横向综合评测
    footprint_section = render_footprint_integrated_section(platforms, en)

    # Methodology section
    method_h2 = "Methodology & Reproducibility" if en else "评测准则与环境公开"
    method_p1 = (
        "<ul>"
        "<li><b>Equal algorithm parity</b>: Every workload implements identical mathematical algorithms, data structures, and iteration counts across all languages.</li>"
        "<li><b>Peak optimization flags</b>: All native peers compiled under peak release optimization flags (Clang <code>-O3</code>, rustc <code>-O3 / --release</code>, Swift <code>-O</code> equivalent to -O3, Go native release build).</li>"
        "<li><b>Strict verification</b>: Every iteration verifies program stdout fingerprint and return code to prevent dead-code elimination cheats.</li>"
        "<li><b>Wall & CPU timing</b>: 7 iterations per test; reports median wall time and peak resident set size (RSS, wait4 on Unix, Win32 API on Windows).</li>"
        "<li><b>Dual-Architecture Matrix</b>: Native execution on ARM64 (Apple Silicon, Neoverse, Snapdragon X) and x86_64 (Intel, AMD) across macOS, Linux, and Windows runners.</li>"
        "<li><b>CI automation</b>: Continually tested on GitHub Actions runner. View the workflow: <code>.github/workflows/bench.yml</code> in the <a href=\"https://github.com/xulang-org/bench\" target=\"_blank\">bench repository</a>.</li>"
        "</ul>"
        if en
        else "<ul>"
        "<li><b>同算法等价实现</b>：所有横测均采用相同的数据结构、数学算法与循环迭代规模，拒绝峰值特化。</li>"
        "<li><b>全量最高编译优化</b>：所有原生对比语言均开启官方最高级别优化（Clang <code>-O3</code>、rustc <code>-O3 / --release</code>、Swift <code>-O</code> 即等价 -O3、Go 原生编译优化），统一处于激进优化水平。</li>"
        "<li><b>严苛输出指纹校验</b>：每次运行均严格比对 stdout 黄金校验码与退出码，杜绝无意义的死代码剪除与假跑。</li>"
        "<li><b>稳健采样方法</b>：每个程序重复运行 7 次，取 wall 耗时与 CPU 耗时中位数；通过 Unix wait4 与 Windows 原生 API 捕获真实峰值常驻内存（RSS）。</li>"
        "<li><b>双架构完整覆盖</b>：原生覆盖 ARM64（Apple Silicon / Neoverse / Snapdragon X Elite）与 x86_64（Intel / AMD）硬件，并在 macOS、Linux、Windows 环境下全面实测。</li>"
        "<li><b>CI 自动化测试</b>：由 GitHub Actions CI 全程自动运行与出具报告。流水线配置见 <a href=\"https://github.com/xulang-org/bench\" target=\"_blank\">bench 仓库</a> 的 <code>.github/workflows/bench.yml</code>。</li>"
        "</ul>"
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
    if (sec.classList.contains('bench-sec-core') || sec.classList.contains('bench-sec-footprint')) return;
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
      <span class="meta" style="margin: 0; font-size: 12px;">{'47 Real-world Workloads · 6 Platforms Integrated' if en else '47 项真实算法负载 · 6 大目标平台合一平铺'}</span>
    </div>
  </div>
  <div class="bench-anchor-bar">
    <div class="bench-anchor-links">
      {''.join(anchor_buttons)}
      <button type="button" class="bench-anchor-pill" onclick="jumpToBenchSection('footprint')">
        {SVG_BRAIN} <span>{'Memory & Size' if en else '内存与体积'}</span>
      </button>
      <button type="button" class="bench-anchor-pill" onclick="jumpToBenchSection('core')">
        {SVG_BOLT} <span>{'Panorama' if en else '全景看板'}</span>
      </button>
    </div>
    <div class="bench-search-wrap bench-search-global">
      {SVG_SEARCH}
      <input type="text" class="bench-search-input" id="bench-global-search" placeholder="{search_placeholder}" oninput="searchBenchAll(this.value)" />
    </div>
  </div>
</div>

<!-- 1. 功能大类全平台合一平铺 (按功能，各平台直接铺开) -->
{''.join(category_sections)}

<!-- 2. 全平台内存与体积横向综合评测 -->
{footprint_section}

<!-- 3. 核心用例跨架构横向柱状图看板 (放下面) -->
<div class="bench-cat-section bench-sec-core">
  {cross_platform_panorama}
</div>

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

    zh_out.write_text(zh_content, encoding="utf-8")
    en_out.write_text(en_content, encoding="utf-8")

    print(f"Generated {zh_out}")
    print(f"Generated {en_out}")


if __name__ == "__main__":
    main()
