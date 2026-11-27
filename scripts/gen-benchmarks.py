#!/usr/bin/env python3
"""Generate official multi-architecture benchmark pages for English and Chinese from benchmarks.json."""
from __future__ import annotations

import json
import html
import math
import statistics
from pathlib import Path
import re
from benchmark_groups import platform_groups
from benchmark_results import FAILURES

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "www/benchmarks.json"
SOURCES_FILE = ROOT / "www/bench_sources.json"

SVG_BOLT = '<svg class="bench-icon bench-icon-bolt" viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>'
SVG_BRAIN = '<svg class="bench-icon bench-icon-brain" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/><path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"/><path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4"/><path d="M12 18v4"/><path d="M12 5V2"/></svg>'
SVG_BOX = '<svg class="bench-icon bench-icon-box" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/></svg>'
SVG_CLOCK = '<svg class="bench-icon bench-icon-clock" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>'
SVG_TRENDS = '<svg class="bench-icon bench-icon-trends" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>'
SVG_RADAR = '<svg class="bench-icon bench-icon-radar" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"/><line x1="12" y1="22" x2="12" y2="15.5"/><polyline points="22 8.5 12 15.5 2 8.5"/><polyline points="2 15.5 12 8.5 22 15.5"/><line x1="12" y1="2" x2="12" y2="8.5"/></svg>'
SVG_SEARCH = '<svg class="bench-search-icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>'
SVG_CONTROL = '<svg class="bench-icon bench-cat-svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="16 3 21 3 21 8"/><line x1="4" y1="20" x2="21" y2="3"/><polyline points="21 16 21 21 16 21"/><line x1="15" y1="15" x2="21" y2="21"/><line x1="4" y1="4" x2="9" y2="9"/></svg>'
SVG_ALGO = '<svg class="bench-icon bench-cat-svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="2" width="16" height="20" rx="2"/><line x1="8" y1="6" x2="16" y2="6"/><line x1="16" y1="14" x2="16" y2="18"/><path d="M16 10h.01"/><path d="M12 10h.01"/><path d="M8 10h.01"/><path d="M12 14h.01"/><path d="M8 14h.01"/><path d="M12 18h.01"/><path d="M8 18h.01"/></svg>'
SVG_DATA = '<svg class="bench-icon bench-cat-svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>'
SVG_STRING = '<svg class="bench-icon bench-cat-svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>'
SVG_CRYPTO = '<svg class="bench-icon bench-cat-svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>'
SVG_CONCURRENCY = '<svg class="bench-icon bench-cat-svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>'
SVG_WEB = '<svg class="bench-icon bench-cat-svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>'
SVG_STORAGE = '<svg class="bench-icon bench-cat-svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>'
SVG_SYSTEMS = '<svg class="bench-icon bench-cat-svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg>'
SVG_GRAPHICS = '<svg class="bench-icon bench-cat-svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>'
SVG_AI = '<svg class="bench-icon bench-cat-svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2v4"/><path d="M12 18v4"/><path d="m4.93 4.93 2.83 2.83"/><path d="m16.24 16.24 2.83 2.83"/><path d="M2 12h4"/><path d="M18 12h4"/><path d="m4.93 19.07 2.83-2.83"/><path d="m16.24 7.76 2.83-2.83"/></svg>'

CATEGORIES_CONFIG = [
    {
        "key": "control",
        "name_zh": "控制流与语言底层机制",
        "name_en": "Control Flow & Language Primitives",
        "pill_zh": "控制流机制",
        "pill_en": "Control & Primitives",
        "desc_zh": "实测进程启动、整数与浮点循环、递归、嵌套循环、结构体方法及动态派发（接口、match/switch、函数值）。",
        "desc_en": "Measured process startup, integer/f64 loops, recursion, nested loops, struct methods, and dynamic dispatch (interfaces, match/switch, function values).",
        "icon": SVG_CONTROL,
    },
    {
        "key": "algo",
        "name_zh": "数值算法与密集计算",
        "name_en": "Numerical Algorithms & Compute",
        "pill_zh": "数值算法",
        "pill_en": "Algorithms",
        "desc_zh": "实测矩阵乘法、排序与二分查找、硬件位运算、素数筛法、SROA/前缀扫描及 Osprey 算法题；具体规模以各项源码为准。",
        "desc_en": "Measured matrix multiplication, sorting and binary search, hardware bit ops, prime sieves, SROA/prefix scans, and Osprey algorithmic workloads; see each source for input sizes.",
        "icon": SVG_ALGO,
    },
    {
        "key": "data",
        "name_zh": "数据结构与内存访问模式",
        "name_en": "Data Structures & Memory Access",
        "pill_zh": "数据结构",
        "pill_en": "Data Structures",
        "desc_zh": "实测动态数组、哈希表、二叉堆优先队列、环形缓冲区、LRU 缓存、布隆过滤器、块内存拷贝、下标追逐与拥有型二叉树。",
        "desc_en": "Measured dynamic arrays, hash maps, priority heaps, ring buffers, LRU cache, Bloom filters, block copy, pointer chasing, and owning binary trees.",
        "icon": SVG_DATA,
    },
    {
        "key": "string",
        "name_zh": "字符串处理与文本 I/O",
        "name_en": "Strings & Text I/O",
        "pill_zh": "文本与I/O",
        "pill_en": "Strings & I/O",
        "desc_zh": "实测字符串构建与切片视图、字节计数、文件读写往返、Hex/Base64 编解码及分词与词频统计。",
        "desc_en": "Measured string building, byte views, substring counting, file roundtrip I/O, hex/Base64 codecs, and token/word-frequency text scans.",
        "icon": SVG_STRING,
    },
    {
        "key": "web",
        "name_zh": "Web 后端、网络协议与序列化",
        "name_en": "Web, Protocols & Serialization",
        "pill_zh": "Web 与协议",
        "pill_en": "Web & Protocols",
        "desc_zh": "实测 HTTP/1.1 请求解析与 Trie 动态路由、RFC 6455 WebSocket 帧掩码编解码、Protobuf Varint/ZigZag 嵌套编解码、TOML 配置解析及 HTML 模板 XSS 转义渲染。",
        "desc_en": "Measured HTTP/1.1 parsing and trie routing, RFC 6455 WebSocket framing, Protobuf Varint/ZigZag nested RPC codecs, TOML config lexing, and HTML template compilation with XSS escaping.",
        "icon": SVG_WEB,
    },
    {
        "key": "storage",
        "name_zh": "数据库内核、存储与全文检索",
        "name_en": "Storage, Databases & Search",
        "pill_zh": "存储与检索",
        "pill_en": "Storage & Search",
        "desc_zh": "实测 B+ 树索引分裂与范围扫描、LSM-Tree 多路归并压实、BM25 全文倒排检索、列存 SQL 过滤聚合、一致性哈希环与 WAL 崩溃恢复。",
        "desc_en": "Measured B+ tree split/range scan, LSM-Tree multi-way compaction, BM25 inverted-index search, columnar SQL execution, consistent hashing, and WAL recovery.",
        "icon": SVG_STORAGE,
    },
    {
        "key": "systems",
        "name_zh": "系统编程、编译工具链与压缩",
        "name_en": "Systems, Tooling & Compression",
        "pill_zh": "系统与工具链",
        "pill_en": "Systems & Tooling",
        "desc_zh": "实测表达式前端编译与字节码 VM、Myers 最短编辑距离 Diff、分级 Slab 内存分配与页回收、分层时间轮调度、LZ4 块压缩及 UTF-8 校验解码与文本规范化。",
        "desc_en": "Measured bytecode VM compilation, Myers text diff, segregated slab allocator with page reclaim, hierarchical timing wheels, LZ4 block compression, and UTF-8 validation/normalization.",
        "icon": SVG_SYSTEMS,
    },
    {
        "key": "graphics",
        "name_zh": "图形渲染、图像处理与物理仿真",
        "name_en": "Graphics, Imaging & Physics",
        "pill_zh": "图形与物理",
        "pill_en": "Graphics & Physics",
        "desc_zh": "实测 3D 球面光线追踪反射阴影、二维高斯模糊与 Sobel 边缘卷积流水线、及基于空间网格的多体弹性碰撞物理仿真。",
        "desc_en": "Measured 3D sphere ray tracing, 2D Gaussian blur + Sobel edge convolution pipelines, and spatial-hash 2D rigid-body collision physics.",
        "icon": SVG_GRAPHICS,
    },
    {
        "key": "ai",
        "name_zh": "AI 推理、机器学习与量化金融",
        "name_en": "AI Inference, ML & Quant",
        "pill_zh": "AI 与金融",
        "pill_en": "AI & Quant",
        "desc_zh": "实测三层稠密 MLP 神经网络前向推理（ReLU / Argmax）、8 维 Lloyd K-Means 迭代聚类，及价格-时间优先限价订单簿高频撮合引擎。",
        "desc_en": "Measured 3-layer dense MLP forward inference (ReLU/argmax), 8D Lloyd K-Means clustering, and price-time priority limit order book matching.",
        "icon": SVG_AI,
    },
    {
        "key": "crypto",
        "name_zh": "现代密码学与安全",
        "name_en": "Modern Cryptography & Security",
        "pill_zh": "现代密码学",
        "pill_en": "Cryptography",
        "desc_zh": "实测 SHA-256 / MD5 哈希链、CRC32 流校验与软件 AES-128/192/256（加解密及密钥扩展）；硬件与软件执行路径可能不同。",
        "desc_en": "Measured SHA-256 and MD5 hash chains, CRC32 stream checksums, and software AES-128/192/256 (encrypt, decrypt, key setup); hardware and software execution paths may differ.",
        "icon": SVG_CRYPTO,
    },
    {
        "key": "concurrency",
        "name_zh": "高性能并发与多核并行",
        "name_en": "Concurrency & Parallelism",
        "pill_zh": "并发与并行",
        "pill_en": "Concurrency",
        "desc_zh": "实测基于 CSP 模型的轻量级协程调度、Channel 高频乒乓通信延迟及并发自环回 HTTP 吞吐。",
        "desc_en": "Measured CSP-model lightweight coroutine scheduling, channel ping-pong latency, and concurrent loopback HTTP throughput.",
        "icon": SVG_CONCURRENCY,
    },
]

CATEGORY_EXTENSIONS = {
    "control": (
        {"awfy_richards", "brainfuck_vm"},
        " Also includes AWFY OS task scheduler simulation (Richards) and Brainfuck bytecode VM execution.",
        "同时涵盖 AWFY 操作系统任务调度模拟（Richards）与 Brainfuck 字节码虚拟机执行。",
    ),
    "algo": (
        {
            "plb2_nqueen", "plb2_sudoku", "scimark_montecarlo", "scimark_sor",
            "scimark_lu", "scimark_sparse", "scimark_fft", "huffman_coding", "astar_maze",
        },
        " Also includes PLB2 backtracking (15-Queens, kudoku), NIST SciMark2 numerical kernels (Monte Carlo, SOR, LU, CSR sparse, FFT), Huffman coding, and A* maze shortest-path search.",
        "同时涵盖 PLB2 组合回溯（15 皇后、kudoku）、NIST SciMark2 数值计算核（蒙特卡洛、SOR、LU、CSR 稀疏矩阵、FFT）、Huffman 编解码与 A* 迷宫最短路搜索。",
    ),
    "data": (
        {"avl_tree", "treap_ops", "plb2_bedcov"},
        " Also includes balanced trees (AVL, split/merge Treap) and PLB2 implicit interval tree overlap queries (bedcov).",
        "同时涵盖平衡搜索树（AVL、无旋转分裂合并 Treap）与 PLB2 隐式区间树重叠查询（bedcov）。",
    ),
    "string": (
        {"json_tokenizer", "awfy_json_parser", "lzw_codec", "regex_nfa", "levenshtein_dp", "csv_aggregate"},
        " Also includes LZW compression, JSON lexing and AWFY recursive-descent AST parsing, Thompson NFA regex matching, Levenshtein edit-distance DP, and fixed-point CSV aggregation.",
        "同时涵盖 LZW 压缩解压、JSON 词法扫描与 AWFY 递归下降 AST 解析、Thompson NFA 正则匹配、Levenshtein 编辑距离滚动 DP 及定点 CSV 聚合。",
    ),
    "crypto": (
        {"chacha20_stream"},
        " Also includes ChaCha20 stream cipher block generation.",
        "同时涵盖 ChaCha20 流密码块生成。",
    ),
    "concurrency": (
        {"thread_ring", "skynet"},
        " Also includes 503-node token ring scheduling (thread_ring) and 10-ary coroutine fan-out/fan-in (skynet).",
        "同时涵盖 503 节点令牌环调度（thread_ring）与 10 叉树协程扇出汇总（skynet）。",
    ),
}


def render_category_desc(cat_cfg: dict, present_names: set[str], en: bool) -> str:
    """Build category description matching workloads actually present in the dataset."""
    base = cat_cfg["desc_en"] if en else cat_cfg["desc_zh"]
    ext = CATEGORY_EXTENSIONS.get(cat_cfg["key"])
    if ext is not None and (present_names & ext[0]):
        base = base + (ext[1] if en else ext[2])
    if cat_cfg["key"] == "crypto":
        has_hmac = "hmac_pbkdf2" in present_names
        has_x25519 = "x25519_dh" in present_names
        if has_hmac and has_x25519:
            base += (
                " Also covers HMAC-SHA256 authentication, PBKDF2 key derivation, and Curve25519 / X25519 DH."
                if en else
                " 另涵盖 HMAC-SHA256 签名认证、PBKDF2 密钥派生与 Curve25519 / X25519 密钥交换。"
            )
        elif has_hmac:
            base += (
                " Also covers HMAC-SHA256 authentication and PBKDF2 key derivation."
                if en else
                " 另涵盖 HMAC-SHA256 签名认证与 PBKDF2 密钥派生。"
            )
        elif has_x25519:
            base += (
                " Also covers Curve25519 / X25519 Diffie-Hellman key exchange."
                if en else
                " 另涵盖 Curve25519 / X25519 密钥交换。"
            )
    if cat_cfg["key"] == "concurrency" and "parallel_mapreduce" in present_names:
        base += (
            " Also includes 8-worker parallel MapReduce channel pipeline (parallel_mapreduce)."
            if en else
            " 另涵盖 8 Worker 并发 MapReduce 通道扇出归约流水线（parallel_mapreduce）。"
        )
    return base

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


BENCH_LANGS_CONFIG = [
    {
        "key": "Xu",
        "name": "Xu",
        "cls": "fill-xu",
        "row_cls": "row-xu",
        "color": "var(--bench-xu)",
        "is_main": True,
    },
    {
        "key": "c",
        "name": "C (best O1–O3)",
        "cls": "fill-c",
        "row_cls": "row-c",
        "color": "#0ea5e9",
        "is_main": False,
    },
    {
        "key": "rust",
        "name": "Rust (best O1–O3)",
        "cls": "fill-rust",
        "row_cls": "row-rust",
        "color": "#f97316",
        "is_main": False,
    },
    {
        "key": "swift",
        "name": "Swift (-O)",
        "cls": "fill-swift",
        "row_cls": "row-swift",
        "color": "#ec4899",
        "is_main": False,
    },
    {
        "key": "go",
        "name": "Go",
        "cls": "fill-go",
        "row_cls": "row-go",
        "color": "#10b981",
        "is_main": False,
    },
]

BENCH_METRICS_CONFIG = [
    {
        "key": "wall_ms",
        "unit": "ms",
        "title_zh": "运行耗时 (Wall Time)",
        "title_en": "Wall Time",
        "badge_zh": "ms · 越低越好",
        "badge_en": "ms · Lower is better",
        "icon": SVG_BOLT,
    },
    {
        "key": "rss_mib",
        "unit": "MiB",
        "title_zh": "常驻物理内存 (Peak RSS)",
        "title_en": "Peak RSS Memory",
        "badge_zh": "MiB · 越低越好",
        "badge_en": "MiB · Lower is better",
        "icon": SVG_BRAIN,
    },
    {
        "key": "bytes",
        "unit": "KiB",
        "title_zh": "独立产物体积 (Binary Size)",
        "title_en": "Binary Size",
        "badge_zh": "KiB · 越小越好",
        "badge_en": "KiB · Smaller is better",
        "icon": SVG_BOX,
    },
    {
        "key": "cpu_ms",
        "unit": "ms",
        "title_zh": "CPU 计算耗时 (CPU Time)",
        "title_en": "CPU Time",
        "badge_zh": "ms · 越低越好",
        "badge_en": "ms · Lower is better",
        "icon": SVG_CLOCK,
    },
]


def comparable_metric(value: float | None) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value > 0)


def get_bench_impl_metric(b: dict | None, lang_key: str, metric_key: str) -> float | None:
    if not b:
        return None
    impls = b.get("implementations", {})
    target = None
    if lang_key == "Xu":
        target = impls.get("Xu")
    elif lang_key in ("c", "rust"):
        prefix = "clang" if lang_key == "c" else "rustc"
        choices = [impls[f"{prefix} -O{i}"] for i in (1, 2, 3)
                   if comparable_metric(impls.get(f"{prefix} -O{i}", {}).get("wall_ms"))]
        # Keep RSS, CPU and size attached to the same fastest-wall-time
        # artifact selected by the importer, rather than mixing opt levels.
        target = min(choices, key=lambda impl: impl["wall_ms"]) if choices else None
    elif lang_key == "swift":
        target = impls.get("swiftc -O")
    elif lang_key == "go":
        target = impls.get("go build")

    if not target or target.get('status', 'ok') != 'ok':
        return None
    val = target.get(metric_key)
    if (not isinstance(val, (int, float)) or isinstance(val, bool)
            or not math.isfinite(val) or val < 0):
        return None
    if val == 0 and metric_key not in ("wall_ms", "cpu_ms"):
        return None
    if metric_key == "bytes":
        return val / 1024.0  # KiB
    return float(val)


def workload_metric_values(b_name: str, platforms: dict, metric_key: str) -> dict:
    """Both chart and table use the same fixed six-platform cohort."""
    values = {lang["key"]: {} for lang in BENCH_LANGS_CONFIG}
    for cfg in PLATFORMS_CONFIG:
        pid = cfg["id"]
        platform = platforms.get(pid, {})
        bench = next((b for b in platform.get("benches", []) if b["name"] == b_name), None)
        for lang in values:
            value = get_bench_impl_metric(bench, lang, metric_key)
            if metric_key == "rss_mib" and platform.get("rss_validated") is False:
                value = None
            values[lang][pid] = value
    return values


def cross_platform_metric(values: dict) -> tuple[float | None, int, int]:
    samples = [values.get(cfg["id"]) for cfg in PLATFORMS_CONFIG]
    valid = [value for value in samples if comparable_metric(value)]
    return (statistics.median(valid) if valid else None, len(valid), len(samples))


def incomplete_metric_text(covered: int, total: int, en: bool) -> str:
    label = "comparable" if en else "可比数据"
    title = ("No comparable measurements available on target platforms."
             if en else "未获取到目标平台有效可比实测数据。")
    return f'— <small title="{title}">{label} {covered}/{total}</small>'


def zero_timing_text(unit: str, en: bool) -> str:
    title = ("Below timer resolution; excluded from ratios and ranking."
             if en else "计时精度不足，不参与倍率与排名。")
    return f'<span title="{title}">0.00 {unit}*</span>'


def render_workload_metric_table(b_name: str, platforms: dict, m_cfg: dict, en: bool) -> str:
    """Render a comprehensive multi-platform table for a single metric (wall_ms, rss_mib, bytes, cpu_ms).
    Includes all 6 target platforms as columns plus a cross-platform median column.
    """
    mk = m_cfg["key"]
    unit = m_cfg["unit"]
    active_configs = [c for c in PLATFORMS_CONFIG if c["id"] in platforms]

    langs_def = [
        ("xu", "Xu", "Xu", True),
        ("c", "C <small>best O1–O3</small>", "c", False),
        ("rs", "Rust <small>best O1–O3</small>", "rust", False),
        ("swift", "Swift <small>-O</small>", "swift", False),
        ("go", "Go <small>native</small>", "go", False),
    ]

    table_data = workload_metric_values(b_name, platforms, mk)

    p_best_map = {}
    for c in active_configs:
        pid = c["id"]
        col_vals = [table_data[lk][pid] for _, _, lk, _ in langs_def if table_data[lk].get(pid) is not None and table_data[lk][pid] > 0]
        if len(col_vals) >= 2:
            p_best_map[pid] = min(col_vals)

    summaries = {lk: cross_platform_metric(values) for lk, values in table_data.items()}
    lang_meds = {lk: summary[0] for lk, summary in summaries.items()}

    all_meds = [m for m in lang_meds.values() if m is not None and m > 0]
    complete_meds = [m for lk, m in lang_meds.items()
                     if m is not None and m > 0 and summaries[lk][1] == summaries[lk][2]]
    best_med = min(complete_meds) if len(complete_meds) >= 2 else (min(all_meds) if len(all_meds) >= 2 else None)

    th_cols = [f'<th class="bench-td-lang-cell" style="width: 14%;">{"Language" if en else "实现语言"}</th>']
    for c in active_configs:
        p_name = c["name_en"] if en else c["name_zh"]
        arch = c["arch_tag"]
        icon = c["icon"]
        arch_cls = "arch-arm" if "arm" in arch.lower() else "arch-x64"
        th_cols.append(
            f'<th class="bench-th-platform" style="width: 12.2%;">'
            f'  <div class="bench-th-pname"><i class="xi {icon}"></i> <span>{p_name}</span> <span class="btn-arch {arch_cls}">{arch}</span></div>'
            f'</th>'
        )

    med_hdr_title = "Cross-Platform" if en else "全平台中位数"
    med_hdr_sub = "6/6 for Best" if en else "6/6 参评最优"
    th_cols.append(
        f'<th class="bench-th-platform bench-th-median" style="width: 12.8%;">'
        f'  <div class="bench-th-pname"><i class="xi xi-chart-bar" style="color:var(--xu-brand);"></i> <span>{med_hdr_title}</span> <span class="bench-med-badge">{med_hdr_sub}</span></div>'
        f'</th>'
    )

    def format_metric_val(val: float | None) -> str:
        if val is None or val <= 0:
            return "—"
        if mk == "bytes":
            return f"{val:,.0f} KiB" if val >= 1000 else f"{val:.1f} KiB"
        elif mk == "rss_mib":
            return f"{val:.2f} MiB"
        else:
            return f"{val:.2f}ms"

    rows_html = []
    for cls_key, label, lk, is_xu in langs_def:
        cells = [
            f'<td class="bench-td-lang-cell"><strong class="bench-bar-lang {cls_key}">{label}</strong></td>' if is_xu
            else f'<td class="bench-td-lang-cell"><span class="bench-bar-lang {cls_key}">{label}</span></td>'
        ]

        for c in active_configs:
            pid = c["id"]
            val = table_data[lk].get(pid)
            bench = next((b for b in platforms[pid].get('benches', []) if b['name'] == b_name), {})
            failed = bench.get('xu_status') if is_xu else None
            if failed in FAILURES:
                label = FAILURES[failed][0 if en else 1]
                error = html.escape(bench.get('xu_error', ''), quote=True)
                cells.append(f'<td class="bench-result-failed" title="{error}">{label}</td>')
                continue
            if val is not None and val > 0:
                p_best = p_best_map.get(pid)
                is_best = (p_best is not None and abs(val - p_best) < 1e-4)
                best_pill = f' <span class="bench-best-badge">{"Best" if en else "最优"}</span>' if is_best else ""
                val_text = format_metric_val(val)

                ratio_badge_html = ""
                if is_xu:
                    peers = [table_data[other_lk].get(pid) for other_lk in ["c", "rust"] if table_data[other_lk].get(pid) is not None and table_data[other_lk][pid] > 0]
                    if peers:
                        best_peer = min(peers)
                        ratio = round(val / best_peer, 2)
                        ratio_badge_html = f'<div class="bench-ratio-sub">{format_ratio_badge(ratio)}</div>'

                if is_best:
                    best_cls = " bench-cell-best"
                    if is_xu:
                        cells.append(
                            f'<td class="bench-xu-col{best_cls}">'
                            f'  <div class="bench-cell-wrap">'
                            f'    <div class="bench-val-row">'
                            f'      <span class="bench-xu-val bench-val-best">{val_text}</span>{best_pill}'
                            f'    </div>'
                            f'    {ratio_badge_html}'
                            f'  </div>'
                            f'</td>'
                        )
                    else:
                        cells.append(
                            f'<td class="num bench-cell-best">'
                            f'  <div class="bench-cell-wrap">'
                            f'    <div class="bench-val-row">'
                            f'      <strong class="bench-val-best">{val_text}</strong>{best_pill}'
                            f'    </div>'
                            f'  </div>'
                            f'</td>'
                        )
                else:
                    if is_xu:
                        cells.append(
                            f'<td class="bench-xu-col">'
                            f'  <div class="bench-cell-wrap">'
                            f'    <div class="bench-val-row">'
                            f'      <span class="bench-xu-val">{val_text}</span>'
                            f'    </div>'
                            f'    {ratio_badge_html}'
                            f'  </div>'
                            f'</td>'
                        )
                    else:
                        cells.append(f'<td class="num">{val_text}</td>')
            elif val == 0:
                cells.append(f'<td class="meta">{zero_timing_text(unit, en)}</td>')
            else:
                cells.append('<td class="meta">—</td>')

        # 全平台中位数 / 实测均值
        m_val, covered, total = summaries[lk]
        if m_val is not None and m_val > 0:
            is_med_best = (covered == total and best_med is not None and abs(m_val - best_med) < 1e-4)
            best_pill = f' <span class="bench-best-badge">{"Best" if en else "最优"}</span>' if is_med_best else ""
            m_text = format_metric_val(m_val)
            sub_cov = f' <small title="{"Average across " + str(covered) + " passed platforms" if en else "已通过 " + str(covered) + " 个平台中位数"}" style="opacity:0.75; font-size:11px;">({covered}/{total})</small>' if covered < total else ''
            if is_med_best:
                cells.append(
                    f'<td class="num bench-cell-median bench-cell-best">'
                    f'  <div class="bench-cell-wrap">'
                    f'    <div class="bench-val-row">'
                    f'      <strong class="bench-val-best">{m_text}</strong>{best_pill}'
                    f'    </div>'
                    f'  </div>'
                    f'</td>'
                )
            else:
                cells.append(f'<td class="num bench-cell-median"><strong>{m_text}</strong>{sub_cov}</td>')
        else:
            cells.append(f'<td class="meta bench-cell-median">{incomplete_metric_text(covered, total, en)}</td>')

        row_cls = ' class="bench-row-xu"' if is_xu else ''
        rows_html.append(f'<tr{row_cls}>{"".join(cells)}</tr>')

    return f"""
    <table class="bench-workload-table">
      <thead>
        <tr>
          {''.join(th_cols)}
        </tr>
      </thead>
      <tbody>
        {''.join(rows_html)}
      </tbody>
    </table>
"""


def render_workload_block(b_name: str, ref_bench: dict, platforms: dict, cat_cfg: dict, en: bool, label: str | None = None) -> str:
    """Render a self-contained workload block (e.g. startup) with platforms as columns (horizontal) and languages as rows (vertical). Highlights per-platform best cells."""
    desc = label or (ref_bench["desc_en"] if en else ref_bench["desc_zh"])
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
        lbl_fast = "Fastest:" if en else "最优耗时:"
        fastest_str = (
            f'<span class="bench-meta-tag bench-meta-fastest">'
            f'{SVG_BOLT} <span>{lbl_fast} '
            f'<strong>{f_name} {fastest_cfg["arch_tag"]} ({min_xu_val:.2f}ms)</strong></span>'
            f'</span>'
        )

    ratio_str = ""
    if median_ratio:
        badge = format_ratio_badge(median_ratio)
        lbl_ratio = "vs C/Rust:" if en else "对 C/Rust:"
        ratio_str = (
            f'<span class="bench-meta-tag bench-meta-ratio">'
            f'<span>{lbl_ratio}</span> {badge}'
            f'</span>'
        )

    bars_matrix_html = render_workload_bars_matrix(b_name, platforms, en)

    btn_text = "View Source" if en else "查看源码"

    table_panes = []
    for idx, m_cfg in enumerate(BENCH_METRICS_CONFIG):
        mk = m_cfg["key"]
        t_html = render_workload_metric_table(b_name, platforms, m_cfg, en)
        is_active = (idx == 0)
        disp_style = "" if is_active else ' style="display: none;"'
        active_cls = " active" if is_active else ""
        table_panes.append(
            f'<div class="bench-table-pane{active_cls}" data-metric="{mk}"{disp_style}>\n{t_html}\n</div>'
        )

    tab_btns = []
    for idx, m_cfg in enumerate(BENCH_METRICS_CONFIG):
        mk = m_cfg["key"]
        icon = m_cfg["icon"]
        metric_values = workload_metric_values(b_name, platforms, mk)
        summaries = {lk: cross_platform_metric(values) for lk, values in metric_values.items()}
        title = m_cfg["title_en"] if en else m_cfg["title_zh"]
        is_active = (idx == 0)
        active_cls = " active" if is_active else ""
        tab_btns.append(
            f'<button type="button" class="bench-table-tab{active_cls}" data-metric="{mk}" onclick="switchWorkloadTableMetric(\'{b_name}\', \'{mk}\')">'
            f'{icon} <span>{title}</span>'
            f'</button>'
        )

    table_heading = "6-Platform Audited Data Matrix & Median" if en else "6 大目标平台审计实测数据表与中位数"
    failure_rows = []
    for c in active_configs:
        item = p_map.get(c['id'])
        if item and item.get('xu_status') in FAILURES:
            status = FAILURES[item['xu_status']][0 if en else 1]
            error = html.escape(item.get('xu_error', ''))
            failure_rows.append(f"<li><strong>{c['name_en']} {c['arch_tag']}: {status}</strong><pre>{error}</pre></li>")
    failures = ('<details class="bench-failure-detail"><summary>Xu: '
                + (f'{len(failure_rows)} platform failures' if en else f'{len(failure_rows)} 个平台失败')
                + '</summary><ul>' + ''.join(failure_rows) + '</ul></details>') if failure_rows else ''

    return f"""
<div class="bench-workload-block" id="workload-{b_name}" data-name="{b_name.lower()}" data-desc="{desc.lower()}" data-category="{cat_cfg['key']}">
  <div class="bench-workload-header">
    <div class="bench-workload-title-group">
      <code class="bench-workload-code">{b_name}</code>
      <span class="bench-workload-title">{desc}</span>
      <span class="bench-workload-cat-pill" data-cat-pill="{cat_cfg['key']}">{cat_pill}</span>
    </div>
    <div class="bench-workload-meta">
      {fastest_str}
      {ratio_str}
      <button type="button" class="bench-src-modal-btn" onclick="openBenchCodeModal('{b_name}', '{html.escape(desc, quote=True)}')">
        <i class="xi xi-code"></i> <span>{btn_text}</span>
      </button>
    </div>
  </div>
  {failures}
  {bars_matrix_html}
  <div class="bench-workload-table-toolbar">
    <div class="bench-workload-table-heading">
      <i class="xi xi-table xi-brand"></i>
      <span>{table_heading}</span>
    </div>
    <div class="bench-table-metric-tabs">
      {''.join(tab_btns)}
    </div>
  </div>
  <div class="bench-workload-table-wrap">
    {''.join(table_panes)}
  </div>
</div>
"""


def render_category_integrated_section(cat_cfg: dict, platforms: dict, en: bool) -> str:
    ck = cat_cfg["key"]
    cat_title = cat_cfg["name_en"] if en else cat_cfg["name_zh"]

    groups = [g for g in platform_groups(platforms) if g['category'] == ck]
    if not groups:
        return ""
    present_names = {v['bench']['name'] for g in groups for v in g['variants']}
    cat_desc = render_category_desc(cat_cfg, present_names, en)

    blocks = []
    for group in groups:
        variants = group['variants']
        body = ''.join(render_workload_block(v['bench']['name'], v['bench'], platforms, cat_cfg, en,
                                            v['label_en' if en else 'label_zh']) for v in variants)
        if len(variants) > 1:
            title = html.escape(group['title_en' if en else 'title_zh'])
            labels = html.escape(' · '.join(v['label_en' if en else 'label_zh'] for v in variants))
            count = f"{len(variants)} variants" if en else f"{len(variants)} 个变体"
            body = f'''<details class="bench-workload-group" id="group-{group['id']}" data-group-title="{title.lower()}">
  <summary><span class="bench-group-title">{title}</span><span class="bench-cat-count">{count}</span>
    <span class="bench-group-variants">{labels}</span></summary>
  <div class="bench-group-content">{body}</div>
</details>'''
        blocks.append(body)

    variant_count = sum(len(g['variants']) for g in groups)
    cat_count_text = (f"{len(groups)} groups · {variant_count} variants" if en
                      else f"{len(groups)} 个项目组 · {variant_count} 个变体")

    return f"""
<div class="bench-cat-section bench-sec-{ck}" id="cat-{ck}" data-category="{ck}">
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


def render_category_directory(populated_cats: list[dict], groups: list[dict], en: bool) -> str:
    """Render a domain overview directory grid for one-click category filtering."""
    if not populated_cats:
        return ""
    dir_title = "Engineering Domains Directory" if en else "软件工程领域分类导航"
    dir_sub = (
        f"Click any domain card to filter the matrix below without pooling separate algorithms or input sizes."
        if en else
        f"点击任意工程领域卡片即可在下方精准筛选该分类实测（各算法与输入规模仍保持独立展示，不合并均值）。"
    )
    cards = []
    for cat_cfg in populated_cats:
        ck = cat_cfg["key"]
        cat_groups = [g for g in groups if g.get("category") == ck]
        variant_names = [v["bench"]["name"] for g in cat_groups for v in g["variants"]]
        present_names = set(variant_names)
        cat_desc = render_category_desc(cat_cfg, present_names, en)
        cat_name = cat_cfg["name_en"] if en else cat_cfg["name_zh"]
        count_text = (
            f"{len(cat_groups)} groups · {len(variant_names)} variants"
            if en else f"{len(cat_groups)} 组 · {len(variant_names)} 项"
        )
        preview = variant_names[:4]
        chips = "".join(f'<code>{html.escape(n)}</code>' for n in preview)
        if len(variant_names) > 4:
            chips += f'<span class="bench-domain-more">+{len(variant_names) - 4}</span>'
        cards.append(
            f'<button type="button" class="bench-domain-card" data-cat="{ck}" aria-pressed="false" onclick="selectBenchCategory(\'{ck}\', true)">'
            f'  <div class="bench-domain-card-top">'
            f'    <span class="bench-cat-icon">{cat_cfg["icon"]}</span>'
            f'    <span class="bench-domain-card-title">{cat_name}</span>'
            f'    <span class="bench-cat-count">{count_text}</span>'
            f'  </div>'
            f'  <p class="bench-domain-card-desc">{cat_desc}</p>'
            f'  <div class="bench-domain-chips">{chips}</div>'
            f'</button>'
        )
    return f"""
<section class="bench-domain-directory" id="bench-domain-directory">
  <div class="bench-domain-dir-header">
    <h3 class="bench-domain-dir-title">{dir_title}</h3>
    <p class="bench-domain-dir-sub">{dir_sub}</p>
  </div>
  <div class="bench-domain-grid">
    {''.join(cards)}
  </div>
</section>
"""


def render_workload_bars_matrix(b_name: str, platforms: dict, en: bool) -> str:
    active_configs = [c for c in PLATFORMS_CONFIG if c["id"] in platforms]
    p_keys = ["all"] + [c["id"] for c in active_configs]

    panels = []
    for m_cfg in BENCH_METRICS_CONFIG:
        mk = m_cfg["key"]
        unit = m_cfg["unit"]
        title = m_cfg["title_en"] if en else m_cfg["title_zh"]
        badge = m_cfg["badge_en"] if en else m_cfg["badge_zh"]
        icon = m_cfg["icon"]
        metric_values = workload_metric_values(b_name, platforms, mk)
        summaries = {lk: cross_platform_metric(values) for lk, values in metric_values.items()}

        # 计算每个平台的数据
        p_data = {}
        for pid in p_keys:
            lang_vals = []
            for lcfg in BENCH_LANGS_CONFIG:
                lk = lcfg["key"]
                if pid == "all":
                    val_final = summaries[lk][0]
                else:
                    val_final = metric_values[lk][pid]
                lang_vals.append((lk, val_final))

            valid_nums = [v for lk, v in lang_vals if v is not None and v > 0]
            max_v = max(valid_nums) if valid_nums else 1.0

            if pid == "all":
                complete_nums = [summaries[lcfg["key"]][0] for lcfg in BENCH_LANGS_CONFIG
                                 if summaries[lcfg["key"]][0] is not None
                                 and summaries[lcfg["key"]][0] > 0
                                 and summaries[lcfg["key"]][1] == summaries[lcfg["key"]][2]]
                min_v = min(complete_nums) if len(complete_nums) >= 2 else (min(valid_nums) if valid_nums else None)
            else:
                min_v = min(valid_nums) if len(valid_nums) >= 2 else None

            p_map = {}
            for lk, v in lang_vals:
                cov_info = summaries[lk] if pid == "all" else None
                is_partial = (cov_info is not None and cov_info[1] < cov_info[2])
                if v is None:
                    pct = 0.0
                    _, covered, total = summaries[lk]
                    txt = incomplete_metric_text(covered, total, en) if pid == "all" else "—"
                elif v == 0:
                    pct = 0.0
                    txt = zero_timing_text(unit, en)
                else:
                    pct = (v / max_v) * 100.0
                    ratio = round(v / min_v, 1) if min_v is not None else None
                    v_str = f"{v:.2f}" if v < 100 else f"{v:.1f}"
                    if unit == "KiB" and v >= 1000:
                        v_str = f"{v:,.0f}"

                    is_best = (min_v is not None and abs(v - min_v) < 1e-4 and not is_partial)
                    badge_best = f' <span class="bench-bar-badge-best">{"Best" if en else "最优"}</span>' if is_best else ""

                    if is_partial:
                        covered, total = cov_info[1], cov_info[2]
                        ratio_str = f" · {ratio:.1f}×" if (ratio is not None and abs(ratio - 1.0) >= 0.04) else ""
                        txt = f'{v_str} {unit} <small style="opacity:0.7">({covered}/{total}{ratio_str})</small>'
                    elif ratio is None or is_best or abs(ratio - 1.0) < 0.04:
                        txt = f"{v_str} {unit}{badge_best}"
                    else:
                        txt = f'{v_str} {unit} <small style="opacity:0.7">({ratio:.1f}×)</small>'
                p_map[lk] = {"pct": pct, "txt": txt}
            p_data[pid] = p_map

        bar_rows = []
        for lcfg in BENCH_LANGS_CONFIG:
            lk = lcfg["key"]
            name = lcfg["name"]
            fill_cls = lcfg["cls"]
            row_cls = lcfg["row_cls"]

            attrs = []
            for pid in p_keys:
                info = p_data[pid][lk]
                attrs.append(f'data-pct-{pid}="{info["pct"]:.1f}"')
                escaped_txt = html.escape(info["txt"], quote=True)
                attrs.append(f'data-txt-{pid}="{escaped_txt}"')

            def_info = p_data["all"][lk]
            def_pct = def_info["pct"]
            def_txt = def_info["txt"]

            bar_rows.append(
                f'<div class="bench-bar-row {row_cls}">'
                f'  <div class="bench-bar-label">{name}</div>'
                f'  <div class="bench-bar-track">'
                f'    <div class="bench-bar-fill {fill_cls}" style="width: {def_pct:.1f}%;" {" ".join(attrs)}></div>'
                f'  </div>'
                f'  <div class="bench-bar-val"><span>{def_txt}</span></div>'
                f'</div>'
            )

        card_title_hint = f'Click to inspect {title} multi-platform table' if en else f'点击联动在下方切换查看 {title} 详细数据表'
        panels.append(
            f'<div class="bench-bar-panel" onclick="switchWorkloadTableMetric(\'{b_name}\', \'{mk}\')" title="{card_title_hint}">'
            f'  <div class="bench-bar-panel-header">'
            f'    <div class="bench-bar-panel-title">{icon} <span>{title}</span></div>'
            f'    <span class="bench-bar-panel-unit">{badge}</span>'
            f'  </div>'
            f'  <div class="bench-bar-rows">'
            f'    {"".join(bar_rows)}'
            f'  </div>'
            f'</div>'
        )

    bars_title = "4-Dimension Real Measurements" if en else "4 核心维度横向条形对比 (各平台即时联动)"
    bars_hint = (
        "Cross-platform aggregate (6/6 required for Best) · * Below timer resolution"
        if en
        else "全架构按已通过平台实测综合 (未满6平台不参评最优) · * 计时精度不足"
    )

    return f"""
<div class="bench-workload-bars-wrap">
  <div class="bench-workload-bars-header">
    <div class="bench-workload-bars-title">
      <i class="xi xi-chart-bar xi-brand"></i>
      <span>{bars_title}</span>
    </div>
    <div class="bench-workload-bars-hint">
      {bars_hint}
    </div>
  </div>
  <div class="bench-workload-bars-grid">
    {''.join(panels)}
  </div>
</div>
"""


def render_coverage_overview_section(platforms: dict, en: bool) -> str:
    """Count real valid measurements; do not imply an aggregate speed score."""
    names = {b['name'] for p in platforms.values() for b in p.get('benches', [])}
    total = len(names) * len(PLATFORMS_CONFIG)
    headers = ''.join('<th>' + html.escape(m['title_en' if en else 'title_zh']) + '</th>'
                      for m in BENCH_METRICS_CONFIG)
    rows = []
    for language in BENCH_LANGS_CONFIG:
        cells = []
        for metric in BENCH_METRICS_CONFIG:
            count = 0
            for cfg in PLATFORMS_CONFIG:
                platform = platforms.get(cfg['id'], {})
                if metric['key'] == 'rss_mib' and platform.get('rss_validated') is False:
                    continue
                count += sum(comparable_metric(get_bench_impl_metric(b, language['key'], metric['key']))
                             for b in platform.get('benches', []))
            cells.append(f'<td class="num" data-language="{language["key"]}" data-metric="{metric["key"]}">{count}/{total}</td>')
        rows.append('<tr><th>' + html.escape(language['name']) + '</th>' + ''.join(cells) + '</tr>')
    title = 'Measurement coverage' if en else '实测覆盖情况'
    explanation = ('Valid results / scheduled platform-workload pairs. Failed, unavailable and below-resolution measurements are excluded. Each algorithm and input size keeps its own results below.'
                   if en else '有效结果数 / 计划的平台负载组合数。失败、缺测和低于计时精度的结果不计入有效覆盖；各算法和输入规模的结果在下方分别展示。')
    return f'''
<div class="bench-cat-section bench-sec-radar">
  <div class="bench-cat-section-header"><h3 class="bench-cat-title">{title}</h3>
    <p class="bench-cat-desc">{explanation}</p></div>
  <div class="bench-workload-table-wrap"><table class="bench-workload-table">
    <thead><tr><th>{'Language' if en else '语言'}</th>{headers}</tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table></div>
</div>
'''


def render_footprint_integrated_section(platforms: dict, en: bool) -> str:
    """Render memory footprint and binary size: platforms as columns (horizontal), languages as rows (vertical). Highlights per-platform best cells."""
    active_configs = [c for c in PLATFORMS_CONFIG if c["id"] in platforms]

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
            
            if p.get("rss_validated") is False:
                rss_cells.append(f'<td class="meta">{"Pending retest" if en else "待复测"}</td>')
            elif fp and fp.get("rss"):
                rss_cells.append(f'<td class="num">{fp["rss"]} MiB</td>')
            else:
                rss_cells.append('<td class="meta">—</td>')
            if fp and fp.get("size"):
                size_cells.append(f'<td class="num">{fp["size"]} KiB</td>')
            else:
                size_cells.append('<td class="meta">—</td>')

        # 内存管理机制说明单元格
        gc_text = gc_en if en else gc_zh
        rss_cells.append(f'<td style="text-align: left; padding-left: 14px;"><small>{gc_text}</small></td>')

        row_cls = ' class="bench-row-xu"' if is_xu else ''
        rss_rows.append(f'<tr{row_cls}>{"".join(rss_cells)}</tr>')
        size_rows.append(f'<tr{row_cls}>{"".join(size_cells)}</tr>')

    sec_title = "Memory Footprint & Binary Size (All Platforms & Languages)" if en else "全平台内存与独立二进制体积"
    sec_desc = (
        "Each cell spans different workloads, not a matched-workload memory ranking. "
        if en else "每格覆盖不同负载，不能用范围下限评整体最优。"
    )
    sec_desc += rss_method_note(platforms, en)

    h3_rss = "1. Range of per-workload median peak RSS (MiB; no overall ranking)" if en else "1. 各负载峰值 RSS 中位数范围（MiB，不作整体排名）"
    h3_size = "2. Binary-size range across workloads (unstripped KiB; no overall ranking)" if en else "2. 不同负载的未裁剪二进制体积范围（KiB，不作整体排名）"

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


def render_transparency_charter_section(meta: dict, en: bool) -> str:
    badge_text = "Openness & Transparency Charter" if en else "阳光公开与严谨复现承诺"
    title_text = "Unbiased, 100% Transparent Cross-Language Benchmarks" if en else "零偏向、全透明的工业级跨语言性能实测"
    desc_text = (
        "Every benchmark runs fully automated inside GitHub Actions cloud runners across physical and isolated OS environments. "
        "Test implementations, compilation flags, execution environments, and raw metrics are 100% open-source and publicly auditable. "
        "We eliminate cherry-picked data, artificial optimizations, and black-box measurements."
        if en else
        "所有基准测试均由 GitHub Actions CI 在多系统隔离云端环境下全自动化执行。"
        "全部 5 种语言测试源码、环境配置、编译指令与原始测量数据全部透明开放，"
        "接受全球开发者全流程审阅，杜绝任何人工精选数据、局部特化优化或黑盒测试。"
    )

    run_url = html.escape(meta.get("run_url", "https://github.com/xulang-org/bench"), quote=True)
    commit = html.escape(meta.get("xu_commit", "unrecorded"))

    pills = [
        f'<span class="bench-charter-pill"><i class="xi xi-server"></i> <span>{"Automated CI: GitHub Actions" if en else "全自动 CI: GitHub Actions 云端流水线"}</span></span>',
        f'<span class="bench-charter-pill"><i class="xi xi-check-circle"></i> <span>{"Compiler Bootstrap Verified: Gen2 = Gen3" if en else "编译器闭包核验: Gen2 = Gen3 自举一致"}</span></span>',
        f'<a class="bench-charter-pill pill-link" href="{run_url}" target="_blank" rel="noopener noreferrer"><i class="xi xi-external-link"></i> <span>{"Source Actions Run" if en else "来源 Actions 运行"} (<code>{commit}</code>)</span></a>',
        f'<a class="bench-charter-pill pill-link" href="https://github.com/xulang-org/bench" target="_blank" rel="noopener noreferrer"><i class="xi xi-github"></i> <span>{"github.com/xulang-org/bench" if en else "评测套件开源仓库"}</span></a>',
        f'<a class="bench-charter-pill pill-link" href="/benchmarks.json" target="_blank"><i class="xi xi-download"></i> <span>{"Raw Dataset: benchmarks.json" if en else "原始全量数据集: benchmarks.json"}</span></a>',
    ]

    p1_title = "100% Open-Source Implementations" if en else "100% 评测源码透明开放"
    workload_count = meta["total_benches"]
    p1_desc = (
        f"Implementations for all {workload_count} workloads are publicly accessible, with Xu, C, Rust, Go, and Swift references where available. Inspect algorithm structure with the in-page 'View Source' modal or browse on GitHub."
        if en else
        f"全部 {workload_count} 项负载的实现源码公开，按适用范围提供 Xu、C、Rust、Go、Swift 对照。可在页面卡片点击【查看源码】对比算法结构，或直接查看 GitHub 仓库。"
    )

    p2_title = "Strict Isomorphic Workloads & No Bias" if en else "严禁私利 · 同构算法公平对照"
    p2_desc = (
        "Workloads strictly share equivalent algorithmic logic and data structures. No hand-tuned assembly hacks or specialized compiler cheating. C and Rust automatically select the lowest measured median among O1–O3."
        if en else
        "各语言严格遵循相同的算法复杂度与内存布局，禁止为特定语言手写私有内联汇编；C 与 Rust 自动选取 O1~O3 最优实测中位数，Go 与 Swift 采用官方标准发行编译参数。"
    )

    p3_title = "Automated Dual-Arch 6-Platform CI" if en else "双架构 6 平台自动化 CI 并行"
    p3_desc = (
        "Concurrently measured across macOS, Linux, and Windows on both ARM64 and x86_64 architectures. Every data point is generated in cloud runners without manual local machine selection."
        if en else
        "涵盖 macOS、Linux、Windows 三大操作系统及 ARM64 与 x86_64 双架构。所有数据均由云端自动化流水线并行采集并实时出具，杜绝任何人工挑选的单机数据。"
    )

    p4_title = "7-Run Median & Open Dataset" if en else "7 次冷启动中位数与全量数据开放"
    p4_desc = (
        "Seven independent whole-program executions per implementation; wall time uses the median, accounting for cold launch overhead. Peak RSS and unstripped binary size are reported faithfully with full JSON datasets."
        if en else
        "每项负载独立运行 7 次整进程取中位数（计入进程冷启动开销）；真实展示峰值物理 RSS 与未裁剪二进制体积；提供全量原始结构化数据集供全球查验复现。"
    )

    return f"""
<div class="bench-charter-card">
  <div class="bench-charter-top">
    <div class="bench-charter-badge">
      <i class="xi xi-shield-check"></i>
      <span>{badge_text}</span>
    </div>
    <h2 class="bench-charter-title">
      <i class="xi xi-verified xi-brand" style="color: #10b981;"></i>
      <span>{title_text}</span>
    </h2>
    <p class="bench-charter-desc">{desc_text}</p>
    <div class="bench-charter-meta-row">
      {''.join(pills)}
    </div>
  </div>
  <div class="bench-charter-grid">
    <div class="bench-pillar-card">
      <div class="bench-pillar-header">
        <span class="bench-pillar-icon icon-green"><i class="xi xi-code"></i></span>
        <h4 class="bench-pillar-title">{p1_title}</h4>
      </div>
      <p class="bench-pillar-body">{p1_desc}</p>
    </div>
    <div class="bench-pillar-card">
      <div class="bench-pillar-header">
        <span class="bench-pillar-icon icon-blue"><i class="xi xi-check-circle"></i></span>
        <h4 class="bench-pillar-title">{p2_title}</h4>
      </div>
      <p class="bench-pillar-body">{p2_desc}</p>
    </div>
    <div class="bench-pillar-card">
      <div class="bench-pillar-header">
        <span class="bench-pillar-icon icon-purple"><i class="xi xi-server"></i></span>
        <h4 class="bench-pillar-title">{p3_title}</h4>
      </div>
      <p class="bench-pillar-body">{p3_desc}</p>
    </div>
    <div class="bench-pillar-card">
      <div class="bench-pillar-header">
        <span class="bench-pillar-icon icon-orange"><i class="xi xi-database"></i></span>
        <h4 class="bench-pillar-title">{p4_title}</h4>
      </div>
      <p class="bench-pillar-body">{p4_desc}</p>
    </div>
  </div>
</div>
"""


def render_methodology_audit_section(platforms: dict, meta: dict, en: bool) -> str:
    sec_title = "Benchmark Methodology & Execution Environment" if en else "评测方法与运行环境"
    rss_note = rss_method_note(platforms, en)
    fixed_point = {'gen2_gen3': 'Gen2 = Gen3', 'gen3_gen4': 'Gen3 = Gen4'}.get(meta.get('fixed_point_pair'))
    fixed_point_note = ''
    if fixed_point:
        fixed_point_note = (f' Bootstrap fixed point: {fixed_point}.' if en
                            else f'自举定点为 {fixed_point}。')
    desc = (
        f"Seven whole-program executions per implementation; reported wall time is the median including process launch. "
        f"The rankings use default Xu optimization. C and Rust select the lowest measured median among O1/O2/O3. {rss_note} "
        f"Only successful, output-verified runs carry metrics. Failures retain their status and diagnostics. Compiler identities and source closures were verified.{fixed_point_note}"
        f" The upstream xulang-org/bench repository also evolves with additional engineering-domain workloads (Web protocols & serialization, storage/databases, systems/tooling, graphics/AI, PLB2, SciMark2, AWFY, and concurrency); new domains and suites appear here automatically once measured across all six CI platforms."
        if en else
        f"每项实现独立运行七次整进程，展示包含进程冷启动的 Wall 耗时中位数。"
        f"排行使用 Xu 默认优化，C 与 Rust 取同平台 O1/O2/O3 中位数的最小值。{rss_note}"
        f"仅成功且通过输出校验的运行记录实测指标，失败项保留状态和诊断。已核验编译器身份与源码闭包。{fixed_point_note}"
        f" 上游 xulang-org/bench 仓库持续按软件工程全领域扩充跨语言负载（涵盖 Web 与协议序列化、数据库存储检索、系统工具链与压缩、图形与 AI、PLB2、SciMark2、AWFY 与并发套件等）；新增分类与套件在完成六平台统一 CI 实测并导入后即自动呈现在本看板。"
    )

    t1_title = "Audited Platform & Telemetry Matrix" if en else "6 大目标测试机环境与遥测机制"
    th_p = "Target Platform" if en else "测试目标平台"
    th_arch = "Architecture" if en else "芯片架构"
    th_telemetry = "Memory & Time Accounting" if en else "统计口径与遥测机制"

    platforms_rows = [
        ("macOS ARM64", "Apple Silicon (M-series)", "wait4 · 整进程峰值物理 RSS 与 CPU 耗时"),
        ("Linux ARM64", "ARM64 (Ubuntu Cloud)", "exec 后独立地址空间峰值 RSS (排除跟踪开销)"),
        ("Windows ARM64", "ARM64 (Windows)", "目标进程工作集峰值 (Peak Working Set)"),
        ("macOS x86_64", "Intel Core x86_64", "wait4 · 整进程峰值物理 RSS 与 CPU 耗时"),
        ("Linux x86_64", "AMD64 / x86_64 (Ubuntu Cloud)", "exec 后独立地址空间峰值 RSS (排除跟踪开销)"),
        ("Windows x86_64", "AMD64 / x86_64 (Windows)", "目标进程工作集峰值 (Peak Working Set)"),
    ] if not en else [
        ("macOS ARM64", "Apple Silicon (M-series)", "wait4: whole-process peak RSS & CPU time"),
        ("Linux ARM64", "ARM64 (Ubuntu Cloud)", "post-exec address space peak RSS (tracing excluded)"),
        ("Windows ARM64", "ARM64 (Windows)", "Target process peak working set"),
        ("macOS x86_64", "Intel Core x86_64", "wait4: whole-process peak RSS & CPU time"),
        ("Linux x86_64", "AMD64 / x86_64 (Ubuntu Cloud)", "post-exec address space peak RSS (tracing excluded)"),
        ("Windows x86_64", "AMD64 / x86_64 (Windows)", "Target process peak working set"),
    ]

    p_trs = []
    for pname, parch, ptelemetry in platforms_rows:
        p_trs.append(
            f'<tr><td><strong>{pname}</strong></td><td><code>{parch}</code></td><td><small>{ptelemetry}</small></td></tr>'
        )

    t2_title = "Compiler Toolchains & Optimization Flags" if en else "5 大语言体系编译器基准与参数"
    th_lang = "Language / Toolchain" if en else "语言体系 / 编译器"
    th_flag = "Build Flags" if en else "构建参数 / 优化级别"
    th_rt = "Runtime & Memory Model" if en else "运行时与内存机制"

    compilers_rows = [
        ("Xu", "xu build（版本默认优化参数）", "零 GC · 编译期借用生命周期与 RAII 确定性析构"),
        ("C (Clang)", "clang -O1 / -O2 / -O3 (取最优，Unix 附加 -lm)", "手动 free · 零运行时开销 (性能标尺)"),
        ("Rust (rustc)", "rustc -C opt-level=1 / 2 / 3 (取最优)", "零 GC · 所有权生命周期与 Scope Drop"),
        ("Swift", "swiftc -O", "ARC 自动引用计数运行时 (含 Swift 标准库)"),
        ("Go", "go build (native)", "并发三色标记清除 GC 运行时 (含并发调度器)"),
    ] if not en else [
        ("Xu", "xu build (versioned defaults)", "Zero GC / RAII Scope Drop / Native machine-code backend"),
        ("C (Clang)", "clang -O1 / -O2 / -O3 (lowest median, -lm on Unix)", "Manual memory management / Zero runtime"),
        ("Rust (rustc)", "rustc -C opt-level=1 / 2 / 3 (lowest median)", "Zero GC / Ownership Drop / LLVM Backend"),
        ("Swift", "swiftc -O", "ARC (Automatic Reference Counting) runtime"),
        ("Go", "go build (native)", "Concurrent Tracing GC runtime & Scheduler"),
    ]

    c_trs = []
    for clang, cflag, crt in compilers_rows:
        c_trs.append(
            f'<tr><td><strong>{clang}</strong></td><td><code>{cflag}</code></td><td><small>{crt}</small></td></tr>'
        )

    bench_commit = meta.get('bench_commit', '')
    checkout = f'git checkout {bench_commit} && ' if re.fullmatch(r'[0-9a-f]{40}', bench_commit) else ''
    repro_cmd = html.escape('git clone https://github.com/xulang-org/bench.git && cd bench && '
                           + checkout + f'XU_ROOT=/path/to/xu-source-{meta["xu_version"]} '
                           + 'python3 scripts/bench_crosslang.py '
                           + f'--xu /path/to/xu-sdk-{meta["xu_version"]}/bin/xu '
                           + '--iters 7 --out reports/crosslang.txt', quote=True)
    source_commit = html.escape(meta.get('xu_commit', 'unrecorded'))
    repro_note = (f'Replace both /path/to paths: XU_ROOT is the Xu source checkout at {source_commit}; --xu is the matching published SDK executable (xu.exe on Windows).'
                  if en else f'请替换两个 /path/to 路径：XU_ROOT 指向提交 {source_commit} 的 Xu 源码检出，--xu 指向对应正式 SDK 的可执行文件（Windows 为 xu.exe）。')
    copy_btn_txt = "Copy Command" if en else "复制复现指令"

    return f"""
<div class="bench-audit-box">
  <div class="bench-audit-header">
    <h3 class="bench-audit-title">
      <i class="xi xi-shield-check xi-brand"></i>
      <span>{sec_title}</span>
    </h3>
    <p class="bench-audit-desc">{desc}</p>
  </div>

  <div class="bench-audit-grid">
    <div class="bench-audit-card">
      <div class="bench-audit-card-title"><i class="xi xi-server"></i> <span>{t1_title}</span></div>
      <table class="bench-audit-table">
        <thead>
          <tr><th>{th_p}</th><th>{th_arch}</th><th>{th_telemetry}</th></tr>
        </thead>
        <tbody>
          {''.join(p_trs)}
        </tbody>
      </table>
    </div>

    <div class="bench-audit-card">
      <div class="bench-audit-card-title"><i class="xi xi-terminal"></i> <span>{t2_title}</span></div>
      <table class="bench-audit-table">
        <thead>
          <tr><th>{th_lang}</th><th>{th_flag}</th><th>{th_rt}</th></tr>
        </thead>
        <tbody>
          {''.join(c_trs)}
        </tbody>
      </table>
    </div>
  </div>

  <p class="meta">{repro_note}</p>
  <div class="bench-repro-console">
    <div><span style="opacity: 0.6; user-select: none;">$ </span><span>{repro_cmd}</span></div>
    <button type="button" class="bench-repro-btn" onclick="copyBenchReproCmd(this, '{repro_cmd}')">
      <i class="xi xi-copy"></i> <span>{copy_btn_txt}</span>
    </button>
  </div>
</div>
"""


def rss_method_note(platforms: dict, en: bool) -> str:
    if any(p.get("rss_validated") is False for p in platforms.values()):
        return (
            "Legacy Linux RSS includes launcher memory and is withheld pending a retest."
            if en else "旧 Linux 采样混入启动进程内存，RSS 暂不展示，等待复测。"
        )
    return (
        "Linux peak RSS is collected in a separate post-exec run; tracing is excluded from wall time. "
        "macOS uses wait4 and Windows uses peak working set; these OS accounting methods differ."
        if en else
        "Linux 另次运行读取 exec 后目标地址空间的峰值 RSS，跟踪开销不计入耗时。"
        "macOS 使用 wait4，Windows 使用峰值工作集；各系统的内存统计口径不同。"
    )


def render_toolchain_versions(platforms: dict, version: str, en: bool) -> str:
    title = "Toolchain versions from this run" if en else "本轮实测工具链版本"
    absent = "Unavailable" if en else "本轮未提供"
    rows = []
    for target, data in platforms.items():
        versions = data.get("toolchains", {})
        values = [target, "Xu " + version] + [versions.get(key) or absent
                  for key in ("clang", "rustc", "go", "swiftc")]
        rows.append("<tr>" + "".join("<td><code>" + html.escape(value) + "</code></td>" for value in values) + "</tr>")
    return (f'<h2>{title}</h2><div class="doc-table-wrap"><table class="bench-toolchains">'
            '<thead><tr><th>Platform</th><th>Xu</th><th>Clang</th><th>Rust</th><th>Go</th><th>Swift</th></tr></thead>'
            '<tbody>' + "".join(rows) + '</tbody></table></div>')


def render_pending_workloads(sources: dict, platforms: dict, en: bool) -> str:
    measured = {
        bench["name"]
        for platform in platforms.values()
        for bench in platform.get("benches", [])
        if bench.get("xu_wall_ms") is not None
    }
    if "http_concurrent" not in sources or "http_concurrent" in measured:
        return ""
    title = "Workloads awaiting measurement" if en else "等待统一测量的负载"
    description = (
        "HTTP concurrency: 16 workers × 200 loopback requests, with Xu, Go and Rust source. "
        "This workload is excluded from the official measured workload count and ratios until matching measurements are available."
        if en else
        "HTTP 并发：16 个 worker × 200 次自环回请求，提供 Xu、Go 和 Rust 源码。"
        "该负载等待统一测量，暂不计入正式实测负载数量与性能比值。"
    )
    button = "View HTTP workload source" if en else "查看 HTTP 负载源码"
    return f'''<section class="bench-section" id="pending-workloads">
  <h2>{title}</h2>
  <p>{description}</p>
  <button type="button" class="bench-src-modal-btn" onclick="openBenchCodeModal('http_concurrent', 'HTTP concurrency')">{button}</button>
</section>'''


def render_outcome_summary(platforms: dict, en: bool) -> str:
    rows = []
    total = failed = 0
    for cfg in PLATFORMS_CONFIG:
        benches = platforms.get(cfg['id'], {}).get('benches', [])
        failures = sum(b.get('xu_status', 'ok') != 'ok' for b in benches)
        total += len(benches)
        failed += failures
        rows.append(f"<li>{cfg['name_en']} {cfg['arch_tag']}: "
                    + (f'{len(benches) - failures} passed / {failures} failed' if en
                       else f'{len(benches) - failures} 项通过 / {failures} 项失败') + '</li>')
    if not failed:
        return ''
    title = (f'Xu: {total - failed}/{total} platform-workload checks passed; {failed} failed'
             if en else f'Xu：{total - failed}/{total} 次平台负载检查通过，{failed} 项失败')
    explanation = ('Failed workloads remain in the suite with diagnostics. They have no performance metrics or ranking.'
                   if en else '失败负载继续保留并显示诊断，不填写性能指标、不参与排名。')
    return (f'<aside class="bench-outcome-summary" data-failed-count="{failed}"><strong>{title}</strong>'
            f'<p>{explanation}</p><ul>{"".join(rows)}</ul></aside>')


def render_peer_failures(platforms: dict, en: bool) -> str:
    rows = []
    peers = set()
    for cfg in PLATFORMS_CONFIG:
        for bench in platforms.get(cfg['id'], {}).get('benches', []):
            for name, result in bench.get('implementations', {}).items():
                status = result.get('status', 'ok')
                if name == 'Xu' or status not in FAILURES:
                    continue
                peers.add(name)
                label = FAILURES[status][0 if en else 1]
                heading = f"{cfg['name_en']} {cfg['arch_tag']} · {bench['name']} · {name}: {label}"
                rows.append(f'<li><strong>{html.escape(heading)}</strong>'
                            f'<pre>{html.escape(result.get("error", ""))}</pre></li>')
    if not rows:
        return ''
    title = (f'Comparison measurements: {len(rows)} failed' if en
             else f'比较程序测量：{len(rows)} 项失败')
    title += ' (' + ', '.join(sorted(peers)) + ')'
    explanation = ('Failed comparison results have no metrics, ratios or ranking.' if en
                   else '失败的比较结果不填写性能指标，不计算倍率、不参与排名。')
    details = 'View failure diagnostics' if en else '查看失败诊断'
    return (f'<aside class="bench-outcome-summary" data-peer-failed-count="{len(rows)}">'
            f'<strong>{html.escape(title)}</strong><p>{explanation}</p><details><summary>{details}</summary>'
            f'<ul>{"".join(rows)}</ul></details></aside>')


def render_page(data: dict, lang: str) -> str:
    en = lang == "en"
    meta = data["metadata"]
    version = meta.get("xu_version", "")
    if not re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", version):
        raise ValueError(f"Official benchmark requires an official release (x.y.z), got: {version}")
    platforms = data.get("platforms", {})
    categories = data["categories"]
    workload_count = meta["total_benches"]
    group_count = len(platform_groups(platforms))

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
        f"against C (best Clang O1–O3), Rust (best rustc O1–O3), Swift (swiftc -O), and Go (go build) across {group_count} groups and {workload_count} measured workload variants. "
        f"Concurrently verified across dual architectures (ARM64 & x86_64) on macOS, Linux, and Windows."
        if en
        else f"严谨、可复现的跨语言横向评测：在 {group_count} 个项目组、{workload_count} 个实测负载变体下，将 Xu v{meta['xu_version']} "
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
    banner_text += (' Related workloads share a display group. Each algorithm, input size, source and result remains separate; variants are never pooled.'
                    if en else ' 同类负载合并展示；不同算法、输入规模、源码和测量结果分别保留，不合并计算。')

    # 1. 功能大类平铺区块列表 & 领域筛选条
    category_sections = []
    populated_cats = []
    groups = platform_groups(platforms)
    all_pill_label = "All Domains" if en else "全部分类"
    anchor_buttons = [
        f'<button type="button" class="bench-anchor-pill bench-cat-filter-pill active" data-cat="all" aria-pressed="true" onclick="selectBenchCategory(\'all\', false)">'
        f'<span>{all_pill_label}</span> <span class="badge">{group_count}</span>'
        f'</button>'
    ]

    for cat_cfg in CATEGORIES_CONFIG:
        ck = cat_cfg["key"]
        sec_html = render_category_integrated_section(cat_cfg, platforms, en)
        if sec_html:
            category_sections.append(sec_html)
            populated_cats.append(cat_cfg)
            pill_name = cat_cfg["pill_en"] if en else cat_cfg["pill_zh"]
            icon = cat_cfg["icon"]
            count = len([g for g in groups if g['category'] == ck])
            count_tag = f'<span class="badge">{count}</span>' if count else ""
            anchor_buttons.append(
                f'<button type="button" class="bench-anchor-pill bench-cat-filter-pill" data-cat="{ck}" aria-pressed="false" onclick="selectBenchCategory(\'{ck}\', true)">'
                f'{icon} <span>{pill_name}</span> {count_tag}'
                f'</button>'
            )

    domain_directory_html = render_category_directory(populated_cats, groups, en)

    # Summaries report measured coverage and observed ranges only.
    coverage_section = render_coverage_overview_section(platforms, en)
    footprint_section = render_footprint_integrated_section(platforms, en)

    # 阳光公开与严谨复现承诺 (Transparency Charter)
    charter_section = render_transparency_charter_section(meta, en)

    # 评测准则与环境审计公示 (Methodology Audit Box)
    method_audit_section = render_methodology_audit_section(platforms, meta, en)

    search_placeholder = "Search workload or algorithm across all sections..." if en else "全局搜索算法用例或说明 (如 startup, matmul, aes)..."

    sources_json_str = "{}"
    if SOURCES_FILE.is_file():
        sources_json_str = SOURCES_FILE.read_text(encoding="utf-8")
    pending_workloads = render_pending_workloads(json.loads(sources_json_str), platforms, en)

    modal_title = "Source Code" if en else "算法实现源码"
    modal_copy_text = "Copy Code" if en else "复制代码"
    modal_footer_desc = (
        "Workload implementations and available language ports"
        if en
        else "负载实现与可用的语言对照"
    )
    modal_repo_link_text = (
        "View Full Suite on GitHub" if en else "在 GitHub 仓库查看完整工程"
    )

    modal_html = f"""
<!-- 源码查看弹窗模态框 (Source Code Modal) -->
<div id="bench-src-modal" class="bench-modal-backdrop" style="display: none;" onclick="handleBenchBackdropClick(event)">
  <div class="bench-modal-dialog" role="dialog" aria-modal="true" aria-labelledby="bench-modal-title">
    <div class="bench-modal-header">
      <div class="bench-modal-title-group">
        <i class="xi xi-code xi-brand" style="font-size: 15px;"></i>
        <code id="bench-modal-wname" class="bench-workload-code" style="font-size: 13px;">startup</code>
        <span id="bench-modal-title" class="bench-modal-title">{modal_title}</span>
      </div>
      <div class="bench-modal-actions">
        <button type="button" class="bench-modal-btn-copy" id="bench-modal-copy-btn" onclick="copyBenchCode()">
          <i class="xi xi-copy"></i> <span id="bench-modal-copy-text">{modal_copy_text}</span>
        </button>
        <button type="button" class="bench-modal-btn-close" onclick="closeBenchCodeModal()" aria-label="Close">
          <i class="xi xi-close"></i>
        </button>
      </div>
    </div>
    <div class="bench-modal-lang-tabs" id="bench-modal-tabs"></div>
    <div class="bench-modal-body">
      <pre class="bench-modal-code-pre"><code id="bench-modal-code"></code></pre>
    </div>
    <div class="bench-modal-footer">
      <div class="bench-modal-footer-info">
        <i class="xi xi-info"></i>
        <span id="bench-modal-footer-desc">{modal_footer_desc}</span>
      </div>
      <a id="bench-modal-github-link" class="bench-modal-repo-link" href="https://github.com/xulang-org/bench" target="_blank" rel="noopener noreferrer">
        <span>{modal_repo_link_text}</span> <i class="xi xi-external-link"></i>
      </a>
    </div>
  </div>
</div>
"""

    copy_success_text = "✓ Copied" if en else "✓ 已复制"

    bench_script_template = """
<script>
window.BENCH_SOURCES = __SOURCES_JSON__;

var BENCH_MODAL_LANGS = [
  { key: 'xu', name: 'Xu', icon: '🟣' },
  { key: 'c', name: 'C (-O3)', icon: '🔵' },
  { key: 'rust', name: 'Rust (-O3)', icon: '🟠' },
  { key: 'swift', name: 'Swift (-O)', icon: '🌸' },
  { key: 'go', name: 'Go', icon: '🟢' }
];

var currentBenchWorkload = '';
var currentBenchLang = 'xu';

function openBenchCodeModal(wname, desc) {
  var sources = (window.BENCH_SOURCES && window.BENCH_SOURCES[wname]) || {};
  currentBenchWorkload = wname;

  var wnameEl = document.getElementById('bench-modal-wname');
  if (wnameEl) wnameEl.textContent = wname;

  var titleEl = document.getElementById('bench-modal-title');
  if (titleEl) titleEl.textContent = desc || wname;

  var tabsWrap = document.getElementById('bench-modal-tabs');
  if (tabsWrap) {
    tabsWrap.innerHTML = '';
    var firstLang = null;
    BENCH_MODAL_LANGS.forEach(function(lcfg) {
      if (sources[lcfg.key]) {
        if (!firstLang) firstLang = lcfg.key;
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'bench-modal-lang-tab' + (lcfg.key === currentBenchLang ? ' active' : '');
        btn.setAttribute('data-lang', lcfg.key);
        btn.innerHTML = '<span>' + lcfg.icon + '</span> <span>' + lcfg.name + '</span>';
        btn.onclick = function() { switchBenchModalLang(lcfg.key); };
        tabsWrap.appendChild(btn);
      }
    });

    if (!sources[currentBenchLang] && firstLang) {
      currentBenchLang = firstLang;
    }
    var activeBtn = tabsWrap.querySelector('[data-lang="' + currentBenchLang + '"]');
    if (activeBtn) activeBtn.classList.add('active');
  }

  updateBenchModalCodeDisplay();

  var ghLink = document.getElementById('bench-modal-github-link');
  if (ghLink) {
    ghLink.href = 'https://github.com/xulang-org/bench/tree/main/tests/bench/' + wname;
  }

  var modal = document.getElementById('bench-src-modal');
  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  }
}

function switchBenchModalLang(langKey) {
  currentBenchLang = langKey;
  document.querySelectorAll('.bench-modal-lang-tab').forEach(function(tab) {
    if (tab.getAttribute('data-lang') === langKey) {
      tab.classList.add('active');
    } else {
      tab.classList.remove('active');
    }
  });
  updateBenchModalCodeDisplay();
}

function updateBenchModalCodeDisplay() {
  var codeEl = document.getElementById('bench-modal-code');
  if (!codeEl) return;
  var sources = (window.BENCH_SOURCES && window.BENCH_SOURCES[currentBenchWorkload]) || {};
  var code = sources[currentBenchLang] || '// No implementation available for this language.';
  codeEl.textContent = code;
}

function closeBenchCodeModal() {
  var modal = document.getElementById('bench-src-modal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

function handleBenchBackdropClick(e) {
  if (e.target && e.target.id === 'bench-src-modal') {
    closeBenchCodeModal();
  }
}

document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape' || e.keyCode === 27) {
    closeBenchCodeModal();
  }
});

function copyBenchCode() {
  var codeEl = document.getElementById('bench-modal-code');
  if (!codeEl) return;
  var code = codeEl.textContent || '';
  navigator.clipboard.writeText(code).then(function() {
    var txtEl = document.getElementById('bench-modal-copy-text');
    if (txtEl) {
      var orig = txtEl.textContent;
      txtEl.textContent = '__COPY_SUCCESS__';
      setTimeout(function() { txtEl.textContent = orig; }, 1500);
    }
  });
}

function copyBenchReproCmd(btn, cmd) {
  navigator.clipboard.writeText(cmd).then(function() {
    var orig = btn.innerHTML;
    btn.innerHTML = '<i class="xi xi-check"></i> <span>__COPY_SUCCESS__</span>';
    setTimeout(function() { btn.innerHTML = orig; }, 1500);
  });
}

function switchWorkloadTableMetric(wname, metricKey) {
  var block = document.getElementById('workload-' + wname);
  if (!block) return;
  block.querySelectorAll('.bench-table-tab').forEach(function(tab) {
    if (tab.getAttribute('data-metric') === metricKey) {
      tab.classList.add('active');
    } else {
      tab.classList.remove('active');
    }
  });
  block.querySelectorAll('.bench-table-pane').forEach(function(pane) {
    if (pane.getAttribute('data-metric') === metricKey) {
      pane.style.display = 'block';
      pane.classList.add('active');
    } else {
      pane.style.display = 'none';
      pane.classList.remove('active');
    }
  });
}

function selectBenchPlatform(pid) {
  document.querySelectorAll('.bench-platform-pill').forEach(function(b) {
    if (b.getAttribute('data-pid') === pid) {
      b.classList.add('active');
    } else {
      b.classList.remove('active');
    }
  });
  document.querySelectorAll('.bench-bar-fill').forEach(function(el) {
    var p = el.getAttribute('data-pct-' + pid) || el.getAttribute('data-pct-all');
    if (p !== null) el.style.width = p + '%';
  });
  document.querySelectorAll('.bench-bar-row').forEach(function(row) {
    var fill = row.querySelector('.bench-bar-fill');
    var valWrap = row.querySelector('.bench-bar-val');
    if (fill && valWrap) {
      var t = fill.getAttribute('data-txt-' + pid) || fill.getAttribute('data-txt-all');
      if (t !== null) valWrap.innerHTML = t;
    }
  });
}

function jumpToBenchSection(secKey) {
  var catSec = document.querySelector('.bench-sec-' + secKey + '[data-category]');
  if (catSec && typeof selectBenchCategory === 'function') {
    selectBenchCategory(secKey, true);
    return;
  }
  var target = document.querySelector('.bench-sec-' + secKey);
  if (target) {
    var nav = document.querySelector('.bench-tabs-wrapper');
    var navHeight = nav ? nav.offsetHeight : 80;
    var targetTop = target.getBoundingClientRect().top + window.pageYOffset - navHeight - 16;
    window.scrollTo({ top: targetTop, behavior: 'smooth' });
  }
}

</script>
<script src="/bench-groups.js" defer></script>
"""
    bench_script = bench_script_template.replace("__SOURCES_JSON__", sources_json_str).replace("__COPY_SUCCESS__", copy_success_text)

    platform_pills = []
    pills_cfg = [
        ("all", "All Architectures" if en else "全架构综合", "xi-globe"),
        ("macos-arm64", "macOS ARM64", "xi-apple"),
        ("linux-arm64", "Linux ARM64", "xi-linux"),
        ("windows-arm64", "Win ARM64", "xi-windows"),
        ("macos-x64", "macOS x64", "xi-apple"),
        ("linux-x64", "Linux x64", "xi-linux"),
        ("windows-x64", "Win x64", "xi-windows"),
    ]
    for pid, plabel, picon in pills_cfg:
        active_cls = " active" if pid == "all" else ""
        platform_pills.append(
            f'<button type="button" class="bench-platform-pill{active_cls}" data-pid="{pid}" onclick="selectBenchPlatform(\'{pid}\')">'
            f'  <i class="xi {picon}"></i> <span>{plabel}</span>'
            f'</button>'
        )

    selector_label = "Target Platform Perspective:" if en else "目标实测架构视角:"

    return f"""<!--title: {title}-->
<div class="hero bench-hero">
  <div>
    <p class="banner"><i class="xi xi-benchmark xi-brand"></i> {meta_text}</p>
    <h1>{h1_text}</h1>
    <p class="lead">{lead_text}</p>
    <p class="meta">{'Expand related workloads to compare their separate algorithms and input sizes. Results are never pooled.' if en else '展开同类项目可查看不同算法和输入规模的独立结果；各变体不合并计算。'}</p>
    {render_outcome_summary(platforms, en)}
    {render_peer_failures(platforms, en)}
    {render_toolchain_versions(platforms, version, en)}
  </div>
</div>

<!-- 阳光公开与权威基准评测承诺书 -->
{charter_section}

<div class="bench-tabs-wrapper">
  <div class="bench-sticky-topline">
    <div class="bench-sticky-title-group">
      <h2 style="margin: 0; font-size: 16.5px; font-weight: 700;">{'Cross-Architecture Benchmark Suite' if en else '全量架构性能评测工作集'}</h2>
      <span class="meta" style="margin: 0; font-size: 12px;">{f'{len(populated_cats)} Domains · {group_count} Groups · {workload_count} Measured Variants · 6 Platforms' if en else f'{len(populated_cats)} 个领域 · {group_count} 个项目组 · {workload_count} 个实测变体 · 6 个平台'}</span>
    </div>
    <div class="bench-toolbar-actions">
      <button type="button" class="bench-anchor-pill" onclick="jumpToBenchSection('radar')">
        {SVG_RADAR} <span>{'Coverage' if en else '实测覆盖'}</span>
      </button>
      <button type="button" class="bench-anchor-pill" onclick="jumpToBenchSection('footprint')">
        {SVG_BRAIN} <span>{'Memory & Size' if en else '内存与体积'}</span>
      </button>
      <button type="button" class="bench-util-btn" id="bench-compact-btn" aria-pressed="false" data-label-full="{'Full View' if en else '完整图表'}" data-label-compact="{'Compact Tables' if en else '精简表格'}" onclick="toggleBenchCompactMode(this)">
        <span>{'Compact Tables' if en else '精简表格'}</span>
      </button>
      <button type="button" class="bench-util-btn" id="bench-groups-toggle-btn" data-expanded="false" data-label-expand="{'Expand Groups' if en else '展开分组'}" data-label-collapse="{'Collapse Groups' if en else '折叠分组'}" onclick="toggleAllBenchGroups(this)">
        <span>{'Expand Groups' if en else '展开分组'}</span>
      </button>
    </div>
  </div>
  <div class="bench-anchor-bar">
    <div class="bench-anchor-links" role="group" aria-label="{'Filter benchmarks by domain' if en else '按工程领域筛选负载'}">
      {''.join(anchor_buttons)}
    </div>
  </div>
  <!-- 多平台架构视角一键切换器 -->
  <div class="bench-platform-selector-bar">
    <div class="bench-platform-selector-label"><i class="xi xi-sliders xi-brand"></i> <span>{selector_label}</span></div>
    <div class="bench-platform-pills">
      {''.join(platform_pills)}
    </div>
  </div>
</div>

<div class="bench-search-toolbar">
  <label class="bench-search-label" for="bench-search">{SVG_SEARCH}<span>{'Search workloads' if en else '搜索负载'}</span>
    <input id="bench-search" type="search" oninput="searchBenchAll(this.value)" placeholder="{'Name, algorithm or input size' if en else '名称、算法或输入规模'}">
  </label>
  <div class="bench-filter-status" id="bench-filter-status" hidden data-tpl-shown="{'Showing {shown} of {total} workloads' if en else '当前显示 {shown} / {total} 项负载'}" data-label-reset="{'Reset Filters' if en else '重置筛选'}"></div>
</div>

<!-- Valid measurement coverage; workloads remain separate. -->
{coverage_section}
{footprint_section}
{domain_directory_html}

<!-- 2. 功能大类全平台合一平铺 (每个功能内部均包含 4 维度条形矩阵 + 6 平台详细数据表) -->
<div id="bench-workloads-root" class="bench-workloads-root">
  {''.join(category_sections)}
</div>
<div id="bench-empty-state" class="bench-empty-state" hidden>
  <p>{'No workloads match the current domain filter and search query.' if en else '当前领域筛选与搜索关键词下暂无匹配的基准负载。'}</p>
  <button type="button" class="bench-filter-reset-btn" onclick="resetBenchFilters()">{'Show All Workloads' if en else '查看全部负载'}</button>
</div>

{pending_workloads}

<!-- 评测准则与环境审计公示专区 -->
{method_audit_section}

<p class="meta">
  <a href="/docs/status">{'View Limitations & Status' if en else '查看语言规范与现状限制'}</a> · 
  <a href="/download">{'Download Compiler' if en else '下载 Xu 编译器'}</a> · 
  <a href="https://github.com/xulang-org/bench" target="_blank" rel="noopener noreferrer">{'Benchmark Suite on GitHub' if en else 'GitHub 基准测试套件源码'}</a>
</p>
{modal_html}
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

    i18n_headers = {
        "de": ("<!--title: Benchmarks — Reale Messwerte über Sprachen und Architekturen-->", "<h1>Sprachübergreifende Multi-Architektur-Benchmarks</h1>"),
        "es": ("<!--title: Pruebas de rendimiento — Mediciones reales entre lenguajes y arquitecturas-->", "<h1>Pruebas de rendimiento multiarquitectura entre lenguajes</h1>"),
        "fr": ("<!--title: Performances — Mesures comparatives multi-langages et multi-architectures-->", "<h1>Tests de performance multi-architectures entre langages</h1>"),
        "ja": ("<!--title: ベンチマーク — クロス言語・クロスアーキテクチャ実測-->", "<h1>マルチアーキテクチャ・クロス言語ベンチマーク</h1>"),
        "ko": ("<!--title: 벤치마크 — 다중 언어 및 아키텍처 실측 데이터-->", "<h1>다중 아키텍처 크로스 언어 벤치마크</h1>"),
        "pt-br": ("<!--title: Benchmarks — Medições reais entre linguagens e arquiteturas-->", "<h1>Benchmarks multiarquitetura entre linguagens</h1>"),
        "ru": ("<!--title: Бенчмарки — Кросс-языковые тесты производительности-->", "<h1>Кросс-языковые тесты производительности на различных архитектурах</h1>"),
    }

    for lang, (title, h1) in i18n_headers.items():
        content = en_content
        content = re.sub(r"<!--title: [^>]+-->", title, content, count=1)
        content = re.sub(r"<h1>[^<]+</h1>", h1, content, count=1)
        out_file = ROOT / f"content/{lang}/benchmarks.html"
        out_file.write_text("\n".join(line.rstrip() for line in content.splitlines()) + "\n", encoding="utf-8")
        print(f"Generated {out_file}")

    tw_out = ROOT / "content/zh-tw/benchmarks.html"
    try:
        import opencc
        cc = opencc.OpenCC("s2twp")
        tw_content = cc.convert(zh_content)
    except Exception:
        tw_content = zh_content

    total_benches = data["metadata"]["total_benches"]
    date_str = data["metadata"]["date"]
    version_str = data["metadata"]["xu_version"]
    tw_title = f"<!--title: 橫向測評 — {total_benches} 項跨語言與雙架構效能實測-->"
    tw_h1 = "<h1>全量跨語言與雙架構效能基準評測</h1>"
    tw_banner = f'    <p class="banner"><i class="xi xi-benchmark xi-brand"></i> Updated: {date_str} · Measured Xu v{version_str} · Dual-Architecture (ARM64 + x86_64)</p>'

    tw_content = re.sub(r"<!--title: [^>]+-->", tw_title, tw_content, count=1)
    tw_content = re.sub(r"<h1>[^<]+</h1>", tw_h1, tw_content, count=1)
    tw_content = re.sub(r'    <p class="banner"><i class="xi xi-benchmark xi-brand"></i> [^<]+</p>', tw_banner, tw_content, count=1)

    tw_out.write_text("\n".join(line.rstrip() for line in tw_content.splitlines()) + "\n", encoding="utf-8")
    print(f"Generated {tw_out}")


if __name__ == "__main__":
    main()
