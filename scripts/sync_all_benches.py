#!/usr/bin/env python3
"""Sync all 47 official cross-language benchmark workloads and sources into the website dataset."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH_REPO = ROOT.parent / "bench"
BENCH_TESTS_DIR = BENCH_REPO / "tests/bench"
CROSS_DIR = BENCH_TESTS_DIR / "cross"
SUMMARY_PATH = BENCH_REPO / "reports/crosslang_2026-10-14/summary.json"

DATA_FILE = ROOT / "www/benchmarks.json"
SOURCES_FILE = ROOT / "www/bench_sources.json"

BENCH_DESCRIPTIONS = {
    # 1. 控制流与语言底层机制 (control, 9项)
    'startup': {'cat': 'control', 'zh': '全进程冷启动基线开销（无 stdout）', 'en': 'Whole-process launch baseline (no stdout)'},
    'loop_sum': {'cat': 'control', 'zh': '紧凑整数加法循环（5000万次累加）', 'en': 'Tight integer loop (50M iterations)'},
    'fib': {'cat': 'control', 'zh': '深度递归计算与调用栈开销（fib 34）', 'en': 'Deep recursion & call stack (fib 34)'},
    'nested_loop': {'cat': 'control', 'zh': '8000×8000 双重嵌套循环乘法与掩码', 'en': 'Nested loops: 8000×8000 integer mul + mask'},
    'method_sum': {'cat': 'control', 'zh': '结构体可变方法调用（800万次方法派发）', 'en': 'Struct mutating method calls (8M iterations)'},
    'f64_sum': {'cat': 'control', 'zh': '双精度浮点 ALU 密集计算（2000万次）', 'en': 'f64 ALU: 20M exact integer float additions'},
    'iface_sum': {'cat': 'control', 'zh': '多态接口虚方法动态分发开销', 'en': 'Polymorphic interface dynamic dispatch'},
    'match_sum': {'cat': 'control', 'zh': '枚举分支模式匹配与解构开销', 'en': 'Enum variant pattern matching & destructuring'},
    'fn_val_sum': {'cat': 'control', 'zh': '函数闭包与一等函数指针间接调用', 'en': 'Function value closure & first-class dispatch'},

    # 2. 数值算法与密集计算 (algo, 7项)
    'matmul': {'cat': 'algo', 'zh': '250×250 行优先大矩阵乘法（1560万次乘累加）', 'en': 'Naive 250×250 integer matrix multiplication'},
    'quicksort_hoare': {'cat': 'algo', 'zh': '经典霍尔双向分区就地快速排序', 'en': 'Hoare in-place bidirectional quicksort'},
    'sort_lcg': {'cat': 'algo', 'zh': '线性同余发生器伪随机序列排序', 'en': 'LCG pseudorandom generation & sorting'},
    'sieve_primes': {'cat': 'algo', 'zh': '埃拉托斯特尼筛法求区间质数', 'en': 'Sieve of Eratosthenes prime computation'},
    'math_bits': {'cat': 'algo', 'zh': '底层位操作与二进制位统计（popcount/clz）', 'en': 'Low-level bit manipulation & popcount'},
    'crc32_iso': {'cat': 'algo', 'zh': 'ISO-3309 标准 CRC-32 循环冗余校验和', 'en': 'ISO-3309 CRC-32 checksum computation'},
    'algorithm_search': {'cat': 'algo', 'zh': '大型有序序列二分查找与区间扫描', 'en': 'Binary search & sequence interval probing'},

    # 3. 核心数据结构与内存管理 (data, 11项)
    'sroa_vec3': {'cat': 'data', 'zh': '结构体聚合字段与标量替换（4万次聚合归约）', 'en': 'AoS f64 fields: SROA & aggregate reductions'},
    'copy_bytes': {'cat': 'data', 'zh': '100万元素块连续内存跨段拷贝（80轮）', 'en': 'Bulk indexed copy of 1Mi elements (80 passes)'},
    'map_ops': {'cat': 'data', 'zh': '哈希表高频键值插入、命中与动态扩容', 'en': 'Hash map insert, query & dynamic rehash'},
    'array_ops': {'cat': 'data', 'zh': '动态数组自动扩容、切片索引与末尾追加', 'en': 'Dynamic array growth, slicing & push ops'},
    'ring_buffer': {'cat': 'data', 'zh': '环形定长缓冲区高频读写吞吐', 'en': 'Bounded ring buffer push/pop throughput'},
    'heap_priority': {'cat': 'data', 'zh': '二叉小顶堆优先队列批量插入与弹出', 'en': 'Binary min-heap priority queue operations'},
    'lru_cache': {'cat': 'data', 'zh': 'LRU 最近最少使用缓存哈希链表淘汰算法', 'en': 'LRU eviction cache with doubly-linked list'},
    'bloom_filter': {'cat': 'data', 'zh': '布隆过滤器多散列碰撞探测与成员过滤', 'en': 'Bloom filter multi-hash membership probing'},
    'chase_index': {'cat': 'data', 'zh': '指针/索引链式追踪（探测 CPU 缓存行命中）', 'en': 'Pointer chasing & L1/L2 cache line traversal'},
    'scan_dep': {'cat': 'data', 'zh': '循环数据流水线依赖与向量化边界探测', 'en': 'Loop-carried dependency & pipeline hazard probe'},
    'byte_view': {'cat': 'data', 'zh': '零拷贝连续字节切片窗口视图', 'en': 'Zero-copy byte view & sliding window access'},

    # 4. 文本处理、编解码与 I/O (string, 8项)
    'string_build': {'cat': 'string', 'zh': '字符串高频追加构建与动态扩容（至1MB）', 'en': 'String buffer dynamic growth (up to 1MB)'},
    'string_repeat': {'cat': 'string', 'zh': '模式文本高频重复组装与缓冲区预分配', 'en': 'Pattern string repeat & pre-allocated expansion'},
    'string_count': {'cat': 'string', 'zh': '大规模文本模式子串高效扫描与频次统计', 'en': 'Substring occurrence scanning & counting'},
    'strings_io': {'cat': 'string', 'zh': '字符串按行分割、字符过滤与格式化 I/O', 'en': 'String line split, character filter & I/O'},
    'hex_codec': {'cat': 'string', 'zh': '十六进制字节编码与解码（10万次编解码）', 'en': 'Hexadecimal fast encoding & decoding'},
    'base64_codec': {'cat': 'string', 'zh': '工业级 Base64 编码、解码与填充对齐', 'en': 'Base64 standard encoding & decoding'},
    'file_roundtrip': {'cat': 'string', 'zh': '磁盘文件批量写入与重新读取往返校验', 'en': 'Disk file batch write & read roundtrip'},
    'builder': {'cat': 'string', 'zh': '可复用通用内存构建器与多段组装', 'en': 'Reusable memory builder & multi-part assembly'},

    # 5. 现代密码学与散列摘要 (crypto, 11项)
    'sha256_chain': {'cat': 'crypto', 'zh': 'SHA-256 密码学哈希链（58KB 载荷 4 轮迭代）', 'en': 'Chained SHA-256 over 58KB body (4 rounds)'},
    'md5_chain': {'cat': 'crypto', 'zh': 'MD5 散列算法高频哈希链多轮计算', 'en': 'MD5 hash chain iteration & digest computation'},
    'aes128_encrypt': {'cat': 'crypto', 'zh': 'AES-128 对称加密标准分组迭代运算（10万次）', 'en': 'AES-128 block cipher encryption (100k rounds)'},
    'aes128_decrypt': {'cat': 'crypto', 'zh': 'AES-128 对称解密标准分组迭代运算（10万次）', 'en': 'AES-128 block cipher decryption (100k rounds)'},
    'aes128_key_setup': {'cat': 'crypto', 'zh': 'AES-128 密钥编排与轮密钥生成（Key Schedule）', 'en': 'AES-128 key expansion & schedule generation'},
    'aes192_encrypt': {'cat': 'crypto', 'zh': 'AES-192 对称加密运算（10万次分组）', 'en': 'AES-192 block encryption (100k rounds)'},
    'aes192_decrypt': {'cat': 'crypto', 'zh': 'AES-192 对称解密运算（10万次分组）', 'en': 'AES-192 block decryption (100k rounds)'},
    'aes192_key_setup': {'cat': 'crypto', 'zh': 'AES-192 扩展密钥编排与轮密钥生成', 'en': 'AES-192 key expansion & schedule generation'},
    'aes256_encrypt': {'cat': 'crypto', 'zh': 'AES-256 最高强度工业加密运算（10万次分组）', 'en': 'AES-256 military-grade encryption (100k rounds)'},
    'aes256_decrypt': {'cat': 'crypto', 'zh': 'AES-256 最高强度工业解密运算（10万次分组）', 'en': 'AES-256 military-grade decryption (100k rounds)'},
    'aes256_key_setup': {'cat': 'crypto', 'zh': 'AES-256 扩展密钥编排与轮密钥生成', 'en': 'AES-256 key expansion & schedule generation'},

    # 6. 高性能并发与协程通信 (concurrency, 1项)
    'chan_ping': {'cat': 'concurrency', 'zh': 'CSP 协程有界管道双向乒乓通信（50万次调度）', 'en': 'CSP coroutine channel throughput (500k messages)'},
}


def sync_sources():
    sources = {}
    for b_name in BENCH_DESCRIPTIONS.keys():
        srcs = {}
        xu_path = BENCH_TESTS_DIR / f"{b_name}.xu"
        if xu_path.exists():
            srcs["xu"] = xu_path.read_text(encoding="utf-8")

        for lang, ext in [('c', '.c'), ('rust', '.rs'), ('go', '.go'), ('swift', '.swift')]:
            c_path = CROSS_DIR / f"{b_name}{ext}"
            if c_path.exists():
                srcs[lang] = c_path.read_text(encoding="utf-8")
            else:
                alt_path = BENCH_TESTS_DIR / f"{b_name}{ext}"
                if alt_path.exists():
                    srcs[lang] = alt_path.read_text(encoding="utf-8")
        sources[b_name] = srcs

    SOURCES_FILE.write_text(json.dumps(sources, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"✓ Synchronized {len(sources)} benchmark source codes to {SOURCES_FILE}")


def sync_data():
    if not SUMMARY_PATH.exists():
        print(f"Warning: {SUMMARY_PATH} not found")
        return

    summary_raw = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    runtime = summary_raw.get("runtime", {})

    existing_data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    platforms = existing_data["platforms"]

    # 构造标准 benchmark 对象字典
    def build_bench_item(b_name, impls_map):
        meta_info = BENCH_DESCRIPTIONS.get(b_name, {'cat': 'algo', 'zh': b_name, 'en': b_name})
        xu_impl = impls_map.get("Xu", {})
        xu_wall = xu_impl.get("wall_ms")

        choices_c = [(k, impls_map[k]["wall_ms"]) for k in ("clang -O3", "clang -O2", "clang -O1") if k in impls_map and impls_map[k].get("wall_ms", 0) > 0]
        chosen_c = min(choices_c, key=lambda x: x[1]) if choices_c else (None, None)

        choices_rust = [(k, impls_map[k]["wall_ms"]) for k in ("rustc -O3", "rustc -O2", "rustc -O1") if k in impls_map and impls_map[k].get("wall_ms", 0) > 0]
        chosen_rust = min(choices_rust, key=lambda x: x[1]) if choices_rust else (None, None)

        go_wall = impls_map.get("go build", {}).get("wall_ms")
        swift_wall = impls_map.get("swiftc -O", {}).get("wall_ms")

        item = {
            "name": b_name,
            "desc_zh": meta_info["zh"],
            "desc_en": meta_info["en"],
            "category": meta_info["cat"],
            "xu_wall_ms": xu_wall,
            "xu_best_ms": xu_impl.get("best_ms"),
            "xu_rss_mib": xu_impl.get("rss_mib"),
            "xu_bytes": xu_impl.get("bytes"),
            "c_wall_ms": chosen_c[1],
            "c_implementation": chosen_c[0],
            "rust_wall_ms": chosen_rust[1],
            "rust_implementation": chosen_rust[0],
            "go_wall_ms": go_wall,
            "swift_wall_ms": swift_wall,
            "ratio_vs_c": (xu_wall / chosen_c[1]) if (xu_wall and chosen_c[1]) else None,
            "ratio_vs_rust": (xu_wall / chosen_rust[1]) if (xu_wall and chosen_rust[1]) else None,
            "ratio_vs_go": (xu_wall / go_wall) if (xu_wall and go_wall) else None,
            "ratio_vs_swift": (xu_wall / swift_wall) if (xu_wall and swift_wall) else None,
            "implementations": impls_map,
        }
        return item

    # 1. 对 macos-arm64（或默认平台），注入全量 47 项数据
    for pid, pdata in platforms.items():
        curr_benches = {b["name"]: b for b in pdata.get("benches", [])}
        new_bench_list = []
        for b_name in BENCH_DESCRIPTIONS.keys():
            if b_name in curr_benches:
                item = curr_benches[b_name]
                meta_info = BENCH_DESCRIPTIONS[b_name]
                item["desc_zh"] = meta_info["zh"]
                item["desc_en"] = meta_info["en"]
                item["category"] = meta_info["cat"]
                new_bench_list.append(item)
            elif b_name in runtime:
                impls = runtime[b_name]
                item = build_bench_item(b_name, impls)
                new_bench_list.append(item)
        pdata["benches"] = new_bench_list

    existing_data["benches"] = platforms["macos-arm64"]["benches"]
    existing_data["metadata"]["total_benches"] = len(existing_data["benches"])

    DATA_FILE.write_text(json.dumps(existing_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"✓ Synchronized {len(existing_data['benches'])} benchmark items to {DATA_FILE}")


if __name__ == "__main__":
    sync_sources()
    sync_data()
