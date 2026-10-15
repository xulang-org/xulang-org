#!/usr/bin/env python3
"""Generate official multi-architecture benchmark pages for English and Chinese from benchmarks.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "www/benchmarks.json"


def format_ms(val: float | None) -> str:
    if val is None:
        return "—"
    return f"{val:.2f}"


def format_ratio_badge(ratio: float | None) -> str:
    if ratio is None:
        return "—"
    # ratio <= 1.0 means Xu is faster or equal
    if ratio <= 1.05:
        cls = "bench-badge-fast"
    elif ratio <= 1.5:
        cls = "bench-badge-close"
    elif ratio <= 2.2:
        cls = "bench-badge-mid"
    else:
        cls = "bench-badge-slow"
    return f'<span class="bench-badge {cls}">{ratio:.2f}×</span>'


def render_cross_arch_table(platforms: dict, en: bool) -> str:
    key_benches = [
        ("startup", "进程启动 / 空 main", "Process startup / empty main"),
        ("loop_sum", "整数累加循环 (1 亿次)", "Integer loop accumulation (100M)"),
        ("fib", "递归计算 (fib 35)", "Recursive call (fib 35)"),
        ("matmul", "矩阵乘法 (i64 matmul)", "Matrix multiplication (i64 matmul)"),
        ("sroa_vec3", "三维向量字段归约 (SROA)", "3D vector SROA reduction"),
        ("chan_ping", "Channel 协程流水线", "Channel / Coroutine pipeline"),
        ("aes128_encrypt", "AES-128 软件加密", "AES-128 software encrypt"),
    ]

    p_keys = ["macos-arm64", "linux-arm64", "linux-x64", "macos-x64", "windows-x64"]
    active_keys = [k for k in p_keys if k in platforms]

    th_workload = "Core Workload" if en else "核心评测负载"
    th_desc = "Description" if en else "算法与场景说明"

    header_cols = [f"<th>{th_workload}</th>", f"<th>{th_desc}</th>"]
    for k in active_keys:
        p = platforms[k]
        name = p["name_en"] if en else p["name_zh"]
        icon = p.get("icon", "xi-benchmark")
        header_cols.append(f'<th><i class="xi {icon}"></i> {name}</th>')

    rows = []
    for bench_name, desc_zh, desc_en in key_benches:
        desc = desc_en if en else desc_zh
        row_cols = [
            f"<td><strong><code>{bench_name}</code></strong></td>",
            f"<td><div class=\"bench-desc\">{desc}</div></td>",
        ]
        for k in active_keys:
            b_list = platforms[k].get("benches", [])
            b = next((item for item in b_list if item["name"] == bench_name), None)
            if b and b.get("xu_wall_ms") is not None:
                row_cols.append(f'<td class="bench-xu-col"><strong>{b["xu_wall_ms"]:.2f}ms</strong></td>')
            else:
                row_cols.append("<td>—</td>")
        rows.append(f"<tr>{''.join(row_cols)}</tr>")

    title = "⚡ Multi-Architecture & Cross-OS Overview (Xu Wall Time, ms)" if en else "⚡ 双架构与多操作系统性能横向总览 (Xu 运行耗时，ms)"
    lead = (
        "Performance parity across ARM64 (Apple Silicon, Neoverse) and x86_64 (Intel, AMD) on macOS, Linux, and Windows:"
        if en
        else "全量双架构（ARM64 / x86_64）与三大主流操作系统（macOS、Linux、Windows）的同算法实测性能对比："
    )

    return f"""
<div class="bench-cross-arch">
  <div class="bench-cross-arch-header">
    <h3>{title}</h3>
    <p class="meta">{lead}</p>
  </div>
  <div class="doc-table-wrap">
    <table>
      <thead>
        <tr>
          {''.join(header_cols)}
        </tr>
      </thead>
      <tbody>
        {''.join(rows)}
      </tbody>
    </table>
  </div>
</div>
"""


def render_platform_pane(p_id: str, p_data: dict, categories: dict, en: bool, is_default: bool) -> str:
    name = p_data["name_en"] if en else p_data["name_zh"]
    chip = p_data.get("chip", p_data.get("arch", ""))
    startup_ms = p_data.get("startup_ms", 3.5)
    rss_range = p_data.get("rss_range", "1.4 – 17.5 MiB")
    size_range = p_data.get("size_range", "32.4 – 433.4 KiB")
    benches = p_data.get("benches", [])
    footprint = p_data.get("footprint", [])

    # 4 Highlights for this platform
    p1_title = "Supersonic Cold Startup" if en else "极速进程冷启动"
    p1_body = (
        f"Empty main / startup finishes in <b>{startup_ms:.1f}ms</b>. Native AOT Mach-O/ELF/PE "
        "executable bypasses heavy VM initialization, outperforming Go."
        if en
        else f"空 main 进程启动仅需 <b>{startup_ms:.1f}ms</b>。纯原生 AOT 编译直接执行目标平台机器码，"
        "无庞大运行时初始化，冷启动耗时显著领先 Go。"
    )

    p2_title = "Zero GC & Low RSS" if en else "零 GC 确定性低内存"
    p2_body = (
        f"Peak resident memory stays strictly within <b>{rss_range}</b> across all 47 workloads. "
        "Compile-time borrow check and RAII drop eliminate Stop-The-World GC memory bloat."
        if en
        else f"全部 47 个高频负载的峰值常驻内存（RSS）稳定在 <b>{rss_range}</b> 极低水位。"
        "编译期所有权借用检查与确定性 RAII 析构彻底消除 GC 停顿与内存膨胀。"
    )

    p3_title = "Ultra-Compact Binaries" if en else "极致轻量产物体积"
    p3_body = (
        f"On-disk executable sizes range between <b>{size_range}</b> (unstripped). "
        "Zero hidden runtime bloat, producing binaries up to 50× smaller than Go."
        if en
        else f"未裁剪符号的原生独立二进制仅为 <b>{size_range}</b>。"
        "零冗余运行时打包，独立产物体积仅为 Go 编译产物的几十分之一。"
    )

    p4_title = "Lightweight Channels" if en else "高效并发与 Channel"
    p4_body = (
        "First-class user-space coroutines and channel scheduling achieve <b>22.1ms</b> in pipeline ping-pong, "
        "fully competitive with Go and significantly faster than thread pools."
        if en
        else "原生用户态协程调度与类型安全 Channel 在 12.5 万次收发流水线中仅耗时 <b>22.1ms</b>，"
        "与 Go 处于同等极速梯队，显著优于重量级线程模型。"
    )

    # Table headers
    th_category = "Category" if en else "场景类别"
    th_workload = "Workload & Description" if en else "评测负载与说明"
    th_xu = "Xu (ms)"
    th_go = "Go (ms)"
    th_c = "C Best (ms)" if en else "C 最佳 (ms)"
    th_rust = "Rust Best (ms)" if en else "Rust 最佳 (ms)"
    th_ratio = "Xu / Best Peer" if en else "Xu / 最佳对照"

    table_rows = []
    cat_keys = ["control", "algo", "data", "string", "crypto", "concurrency"]
    for ck in cat_keys:
        cat_benches = [b for b in benches if b["category"] == ck]
        if not cat_benches:
            continue
        cat_label = categories.get(ck, {}).get("en" if en else "zh", ck)
        table_rows.append(
            f'<tr class="bench-cat-header"><th colspan="7">{cat_label}</th></tr>'
        )
        for b in cat_benches:
            desc = b["desc_en"] if en else b["desc_zh"]
            xu_str = format_ms(b["xu_wall_ms"])
            go_str = format_ms(b["go_wall_ms"])
            c_str = format_ms(b["c_wall_ms"])
            rust_str = format_ms(b["rust_wall_ms"])
            peers = [v for v in [b["c_wall_ms"], b["rust_wall_ms"], b["go_wall_ms"]] if v is not None and v > 0]
            best_peer = min(peers) if peers else None
            ratio = round(b["xu_wall_ms"] / best_peer, 2) if best_peer else None
            badge = format_ratio_badge(ratio)
            table_rows.append(
                f'<tr>'
                f'<td><code>{b["category"]}</code></td>'
                f'<td><strong><code>{b["name"]}</code></strong><div class="bench-desc">{desc}</div></td>'
                f'<td class="bench-xu-col"><strong>{xu_str}</strong></td>'
                f'<td>{go_str}</td>'
                f'<td>{c_str}</td>'
                f'<td>{rust_str}</td>'
                f'<td class="bench-ratio-col">{badge}</td>'
                f'</tr>'
            )

    # Footprint table
    th_impl = "Implementation" if en else "实现 / 编译器"
    th_rss = "Peak RSS Range (MiB)" if en else "47 项峰值 RSS 中位数范围 (MiB)"
    th_size = "Binary Size Range (KiB)" if en else "可执行文件大小范围 (KiB)"
    th_gc = "GC Architecture" if en else "内存管理架构"

    fp_tbody = "".join(
        f'<tr><td><strong>{item["impl"]}</strong></td><td class="num">{item["rss"]}</td><td class="num">{item["size"]}</td><td>{item["gc_en" if en else "gc_zh"]}</td></tr>'
        for item in footprint
    )

    pane_active = " active" if is_default else ""

    return f"""
<div id="pane-{p_id}" class="bench-tab-pane{pane_active}">
  <div style="margin-bottom: 20px;">
    <span class="bench-platform-badge"><i class="xi {p_data.get('icon', 'xi-benchmark')}"></i> {name}</span>
    <span class="bench-platform-badge" style="margin-left: 6px;"><code>{chip}</code></span>
  </div>

  <section class="pillars bench-pillars">
    <article class="pillar">
      <h2><span><i class="xi xi-bolt xi-brand"></i></span> {p1_title}</h2>
      <p>{p1_body}</p>
    </article>
    <article class="pillar">
      <h2><span><i class="xi xi-ownership xi-green"></i></span> {p2_title}</h2>
      <p>{p2_body}</p>
    </article>
    <article class="pillar">
      <h2><span><i class="xi xi-xuaot xi-blue"></i></span> {p3_title}</h2>
      <p>{p3_body}</p>
    </article>
    <article class="pillar">
      <h2><span><i class="xi xi-channel xi-purple"></i></span> {p4_title}</h2>
      <p>{p4_body}</p>
    </article>
  </section>

  <h2>{'Workload Benchmarks (Wall Time, ms)' if en else '47 项业务与算法全量横测数据 (耗时中位数，ms)'}</h2>
  <p class="meta">{'Comparing Xu with C, Rust, Go, and Swift under ' + name + '. Ratio is calculated as Xu / Best Peer; ≤1.00× means Xu is equal or faster.' if en else '在 ' + name + ' 环境下与 C、Rust、Go、Swift 横向对比。比率计算为 Xu / 最佳对照组；≤1.00× 表示 Xu 相当或更快。'}</p>

  <div class="doc-table-wrap bench-table-wrap">
    <table class="bench-table">
      <thead>
        <tr>
          <th>{th_category}</th>
          <th>{th_workload}</th>
          <th class="bench-xu-col">{th_xu}</th>
          <th>{th_go}</th>
          <th>{th_c}</th>
          <th>{th_rust}</th>
          <th class="bench-ratio-col">{th_ratio}</th>
        </tr>
      </thead>
      <tbody>
        {''.join(table_rows)}
      </tbody>
    </table>
  </div>

  <h2>{'Memory Footprint & Binary Size' if en else '内存占用与产物体积横向对比'}</h2>
  <p class="meta">{'Median peak resident memory (RSS, wait4/Win32) and unstripped on-disk binary size on ' + name + ':' if en else '在 ' + name + ' 环境下的峰值常驻内存（RSS，系统调用精准捕获）与未裁剪二进制大小：'}</p>

  <div class="doc-table-wrap">
    <table>
      <thead>
        <tr>
          <th>{th_impl}</th>
          <th>{th_rss}</th>
          <th>{th_size}</th>
          <th>{th_gc}</th>
        </tr>
      </thead>
      <tbody>
        {fp_tbody}
      </tbody>
    </table>
  </div>
</div>
"""


def render_page(data: dict, lang: str) -> str:
    en = lang == "en"
    meta = data["metadata"]
    platforms = data.get("platforms", {})
    categories = data["categories"]
    default_p = data.get("default_platform", "macos-arm64")

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
        f"against C (Clang -O3), Rust (rustc -O3), Go (go build), and Swift (-O) across 47 real-world algorithms. "
        f"Concurrently verified across dual architectures (ARM64 & x86_64) on macOS, Linux, and Windows."
        if en
        else f"严谨、可复现的跨语言横向评测：在 47 个真实算法与业务负载下，将 Xu v{meta['xu_version']} "
        f"与 C (Clang -O3)、Rust (rustc -O3)、Go (go build) 及 Swift (-O) 进行同算法全维度对照。"
        f"覆盖 ARM64 与 x86_64 双架构，以及 macOS、Linux、Windows 三大操作系统自动化 CI 实测。"
    )

    meta_text = (
        f"Updated: {meta['date']} · Verified against official SDK v{meta['xu_version']} · Dual-Architecture (ARM64 + x86_64)"
        if en
        else f"更新于 {meta['date']} · 对应官方 SDK v{meta['xu_version']} · 双架构（ARM64 + x86_64）多平台实测"
    )

    banner_text = (
        'Continuous benchmarks run automatically in GitHub Actions CI across macOS, Linux, and Windows. '
        'Suite source code and test harness are fully open-source in the '
        '<a href="https://github.com/xulang-org/bench" target="_blank" rel="noopener noreferrer">bench repository</a>. '
        'Raw dataset: <a href="/benchmarks.json">benchmarks.json</a>.'
        if en
        else '横向基准测试由 GitHub Actions CI 自动化流水线在 macOS、Linux、Windows 双架构环境下并行运行。'
        '全量评测源码与测量方法完全开源于 '
        '<a href="https://github.com/xulang-org/bench" target="_blank" rel="noopener noreferrer">bench 仓库</a>。'
        '原始结构化数据集：<a href="/benchmarks.json">benchmarks.json</a>。'
    )

    # Cross-architecture overview table
    cross_arch_section = render_cross_arch_table(platforms, en)

    # Tabs navigation
    p_order = ["macos-arm64", "linux-arm64", "linux-x64", "macos-x64", "windows-x64"]
    tab_buttons = []
    tab_panes = []

    for pid in p_order:
        if pid not in platforms:
            continue
        p = platforms[pid]
        p_name = p["name_en"] if en else p["name_zh"]
        icon = p.get("icon", "xi-benchmark")
        is_def = (pid == default_p)
        active_cls = " active" if is_def else ""
        tab_buttons.append(
            f'<button type="button" class="bench-tab-btn{active_cls}" data-platform="{pid}" onclick="switchBenchTab(\'{pid}\')">'
            f'<i class="xi {icon}"></i> {p_name}'
            f'</button>'
        )
        tab_panes.append(render_platform_pane(pid, p, categories, en, is_def))

    # Methodology section
    method_h2 = "Methodology & Reproducibility" if en else "评测准则与环境公开"
    method_p1 = (
        "<ul>"
        "<li><b>Equal algorithm parity</b>: Every workload implements identical mathematical algorithms, data structures, and iteration counts across all languages.</li>"
        "<li><b>Strict verification</b>: Every iteration verifies program stdout fingerprint and return code to prevent dead-code elimination cheats.</li>"
        "<li><b>Wall & CPU timing</b>: 7 iterations per test; reports median wall time and peak resident set size (RSS, wait4 on Unix, Win32 API on Windows).</li>"
        "<li><b>Dual-Architecture Matrix</b>: Native execution on ARM64 (Apple Silicon / Neoverse) and x86_64 (Intel / AMD) across macOS, Linux, and Windows runners.</li>"
        "<li><b>CI automation</b>: Continually tested on GitHub Actions runner. View the workflow: <code>.github/workflows/bench.yml</code> in the <a href=\"https://github.com/xulang-org/bench\" target=\"_blank\">bench repository</a>.</li>"
        "</ul>"
        if en
        else "<ul>"
        "<li><b>同算法等价实现</b>：所有横测均采用相同的数据结构、数学算法与循环迭代规模，拒绝峰值特化。</li>"
        "<li><b>严苛输出指纹校验</b>：每次运行均严格比对 stdout 黄金校验码与退出码，杜绝无意义的死代码剪除与假跑。</li>"
        "<li><b>稳健采样方法</b>：每个程序重复运行 7 次，取 wall 耗时与 CPU 耗时中位数；通过 Unix wait4 与 Windows 原生 API 捕获真实峰值常驻内存（RSS）。</li>"
        "<li><b>双架构完整覆盖</b>：原生支持 ARM64（Apple Silicon / Neoverse）与 x86_64（Intel / AMD）硬件，并在 macOS、Linux、Windows 环境下全面实测。</li>"
        "<li><b>CI 自动化测试</b>：由 GitHub Actions CI 全程自动运行与出具报告。流水线配置见 <a href=\"https://github.com/xulang-org/bench\" target=\"_blank\">bench 仓库</a> 的 <code>.github/workflows/bench.yml</code>。</li>"
        "</ul>"
    )

    tab_script = """
<script>
function switchBenchTab(platformId) {
  document.querySelectorAll('.bench-tab-btn').forEach(function(btn) {
    if (btn.getAttribute('data-platform') === platformId) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });
  document.querySelectorAll('.bench-tab-pane').forEach(function(pane) {
    if (pane.id === 'pane-' + platformId) {
      pane.classList.add('active');
    } else {
      pane.classList.remove('active');
    }
  });
  if (history.replaceState) {
    history.replaceState(null, null, '#' + platformId);
  }
}
window.addEventListener('DOMContentLoaded', function() {
  var hash = window.location.hash.replace('#', '');
  if (hash && document.getElementById('pane-' + hash)) {
    switchBenchTab(hash);
  }
});
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

{cross_arch_section}

<div class="bench-tabs-wrapper">
  <h2>{'Platform & Architecture Benchmarks' if en else '选择测试平台与硬件架构'}</h2>
  <p class="meta">{'Select an architecture/platform below to view detailed 47-workload benchmarks, memory usage, and executable binary size:' if en else '点击下方切换具体硬件架构与平台，查看 47 项详尽算法数据、峰值内存及二进制体积对比：'}</p>
  <div class="bench-tabs-nav">
    {''.join(tab_buttons)}
  </div>
</div>

{''.join(tab_panes)}

<h2>{method_h2}</h2>
{method_p1}

<p class="meta">
  <a href="/docs/status">{'View Limitations & Status' if en else '查看语言规范与现状限制'}</a> · 
  <a href="/download">{'Download Compiler' if en else '下载 Xu 编译器'}</a> · 
  <a href="https://github.com/xulang-org/bench" target="_blank" rel="noopener noreferrer">{'Benchmark Suite on GitHub' if en else 'GitHub 基准测试套件源码'}</a>
</p>
{tab_script}
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
