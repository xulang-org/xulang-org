#!/usr/bin/env python3
"""Sync registered cross-language benchmark workloads and sources into the website dataset."""
import json
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BENCH_REPO = ROOT.parent / "bench"
BENCH_TESTS_DIR = BENCH_REPO / "tests/bench"
CROSS_DIR = BENCH_TESTS_DIR / "cross"
SUMMARY_PATH = BENCH_REPO / "reports/crosslang_2026-10-14/summary.json"

DATA_FILE = ROOT / "www/benchmarks.json"
SOURCES_FILE = ROOT / "www/bench_sources.json"

# 纯粹微基准测试集合（24 项：重合项沿用现有基准，全新项使用标准算法命名，无任何 Osprey 标识）
BENCH_DESCRIPTIONS = {
    # 1. 控制流与递归机制 (control, 8项)
    'ackermann': {
        'cat': 'control',
        'zh': '阿克曼-彼得函数非尾深层递归（ack 3, 10）',
        'en': 'Ackermann-Peter deep non-tail recursion (ack 3, 10)'
    },
    'fib': {
        'cat': 'control',
        'zh': '深度递归计算与调用栈开销（fib 34/35）',
        'en': 'Deep recursion & call stack baseline'
    },
    'collatz': {
        'cat': 'control',
        'zh': '考拉兹 3n+1 猜想停止时间累加（10万区间整数递归）',
        'en': 'Sum of Collatz stopping times over 1..100,000'
    },
    'hanoi': {
        'cat': 'control',
        'zh': '经典汉诺塔双递归移动步数计数（n=25）',
        'en': 'Towers of Hanoi exponential double recursion (n=25)'
    },
    'pascal': {
        'cat': 'control',
        'zh': '二项式系数组合数无备忘展开递归（C 27, 13）',
        'en': 'Binomial coefficient recursion C(27, 13)'
    },
    'tak': {
        'cat': 'control',
        'zh': '竹内函数三元自递归与参数嵌套求值（tak 32, 16, 8）',
        'en': 'Takeuchi function ternary self-recursion (tak 32, 16, 8)'
    },
    'mutual_recursion': {
        'cat': 'control',
        'zh': '相互递归函数调用链奇偶性判定（13万次交替调用）',
        'en': 'Mutually recursive parity chain (130,000 iterations)'
    },
    'nested_loop': {
        'cat': 'control',
        'zh': '多层深层嵌套循环乘法与模乘累加',
        'en': 'Nested loops integer multiplication & modular accumulation'
    },

    # 2. 数值算法与离散数学 (algo, 9项)
    'digitsum': {
        'cat': 'algo',
        'zh': '200万连续整数各位十进制数字和累加',
        'en': 'Sum of decimal digit-sums over 1..2,000,000'
    },
    'factorial_mod': {
        'cat': 'algo',
        'zh': '千万级连续阶乘模乘折叠（mod 1000000007）',
        'en': 'Product 1..10,000,000 mod 1000000007 multiplication fold'
    },
    'gcd_sum': {
        'cat': 'algo',
        'zh': '欧几里得最大公约数递归累加求和（200万轮取模）',
        'en': 'Euclidean GCD recursion and modulo accumulation over 2M steps'
    },
    'isqrt': {
        'cat': 'algo',
        'zh': '百万整数牛顿迭代法求平方根与除法密集计算',
        'en': "Newton's method integer square roots over 1..1,000,000"
    },
    'powmod': {
        'cat': 'algo',
        'zh': '百万整数高阶模幂连续累加（20次模乘折叠）',
        'en': 'Sum of i^20 mod 1000000007 over 1..1,000,000'
    },
    'coprime': {
        'cat': 'algo',
        'zh': '2000×2000 网格互质数对统计（嵌套遍历与辗转相除）',
        'en': 'Count coprime pairs in a 2000x2000 grid via Euclidean GCD'
    },
    'sieve_primes': {
        'cat': 'algo',
        'zh': '连续质数筛法与区间素数统计',
        'en': 'Prime computation and sieve counting in hot loop'
    },
    'coins': {
        'cat': 'algo',
        'zh': 'SICP 硬币找零组合数穷举递归（总金额 600）',
        'en': 'Combinatorial coin change ways for amount 600 (SICP)'
    },
    'josephus': {
        'cat': 'algo',
        'zh': '千万级约瑟夫环幸存者索引迭代求解（n=10000000, k=7）',
        'en': 'Josephus survivor index computation (n=10M, k=7)'
    },

    # 3. 核心数据结构与向量 (data, 5项)
    'binarytrees': {
        'cat': 'data',
        'zh': '深度拥有型二叉树连续构建与校验',
        'en': 'Owning binary trees continuous build and check'
    },
    'expr_tree': {
        'cat': 'data',
        'zh': '深度 14 表达式树拥有型结构构建与递归求值',
        'en': 'Owning expression trees of depth 14 build and evaluate'
    },
    'merge_sort': {
        'cat': 'data',
        'zh': '交替划分递归归并排序与动态向量重构',
        'en': 'Alternating split recursive merge sort with dynamic vectors'
    },
    'quicksort_hoare': {
        'cat': 'data',
        'zh': '经典双向分区递归快速排序',
        'en': 'Bidirectional partition recursive quicksort'
    },
    'listops': {
        'cat': 'data',
        'zh': '动态扩容向量组构建与递归区间遍历统计',
        'en': 'Growable vectors recursive traversal and range predicate count'
    },

    # 4. 字符串与词元处理 (string, 2项)
    'textstats': {
        'cat': 'string',
        'zh': '20万词元文本流长度统计与前后缀模式扫描',
        'en': '200,000 tokens length, substring and prefix pattern scanning'
    },
    'word_frequency': {
        'cat': 'string',
        'zh': '20万词元字符串哈希频次映射与加权词频统计',
        'en': '200,000 tokens string-keyed frequency map and weighted counts'
    },
}

# 名字 fallback 映射（内部 bench 仓库文件名到对外名字）
FALLBACK_NAMES = {
    'coprime': ['coprime', 'osprey_coprime'],
    'listops': ['listops', 'osprey_listops'],
    'textstats': ['textstats', 'osprey_textstats'],
    'binarytrees': ['binarytrees', 'osprey_binarytrees', 'game/binarytrees'],
    'fib': ['fib', 'osprey_fib'],
    'nested_loop': ['nested_loop', 'osprey_nestedloop'],
    'quicksort_hoare': ['quicksort_hoare', 'osprey_quicksort'],
    'sieve_primes': ['sieve_primes', 'osprey_primes'],
}


def find_xu_file(b_name: str) -> Path | None:
    candidates = FALLBACK_NAMES.get(b_name, [b_name])
    for c in candidates:
        p = BENCH_TESTS_DIR / f"{c}.xu"
        if p.exists():
            return p
    return None


def find_cross_file(b_name: str, ext: str) -> Path | None:
    candidates = FALLBACK_NAMES.get(b_name, [b_name])
    for c in candidates:
        for parent_dir in (CROSS_DIR, BENCH_TESTS_DIR):
            p = parent_dir / f"{c}{ext}"
            if p.exists():
                return p
    return None


def clean_source(text: str) -> str:
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        if re.search(r'osprey', line, re.IGNORECASE):
            if re.search(r'//.*(?:Nimblesite|README\.md|benchmarks/cases)', line, re.IGNORECASE):
                continue
            sub = re.sub(r'//\s*Osprey(?:\s+[a-z_]+)?:\s*', '// ', line, flags=re.IGNORECASE)
            sub = re.sub(r';\s*see tests/bench/osprey/README\.md\.?', '.', sub, flags=re.IGNORECASE)
            sub = re.sub(r'\bOsprey\s*', '', sub, flags=re.IGNORECASE)
            if sub.strip() in ('//', ''):
                continue
            cleaned.append(sub)
        else:
            cleaned.append(line)
    result = '\n'.join(cleaned)
    result = re.sub(r'^\s*\n', '', result)
    return result.strip() + '\n'


def sync_sources():
    sources = {}
    for b_name in BENCH_DESCRIPTIONS.keys():
        srcs = {}
        xu_path = find_xu_file(b_name)
        if xu_path and xu_path.exists():
            srcs["xu"] = clean_source(xu_path.read_text(encoding="utf-8"))

        for lang, ext in [('c', '.c'), ('rust', '.rs'), ('go', '.go'), ('swift', '.swift')]:
            c_path = find_cross_file(b_name, ext)
            if c_path and c_path.exists():
                srcs[lang] = clean_source(c_path.read_text(encoding="utf-8"))
        sources[b_name] = srcs

    SOURCES_FILE.write_text(json.dumps(sources, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"✓ Synchronized {len(sources)} benchmark source codes to {SOURCES_FILE}")


def sync_data():
    existing_data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    platforms = existing_data["platforms"]

    # 构造标准 benchmark 对象字典
    def build_bench_item(b_name, impls_map):
        meta_info = BENCH_DESCRIPTIONS.get(b_name, {'cat': 'algo', 'zh': b_name, 'en': b_name})
        xu_impl = impls_map.get("Xu", {})
        xu_wall = xu_impl.get("wall_ms")

        choices_c = [(k, impls_map[k]["wall_ms"]) for k in ("clang -O3", "clang -O2", "clang -O1", "gcc -O3", "gcc -O2") if k in impls_map and impls_map[k].get("wall_ms", 0) > 0]
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

    # 对所有平台，筛选并仅保留这 24 项微基准
    for pid, pdata in platforms.items():
        curr_benches = {b["name"]: b for b in pdata.get("benches", [])}
        new_bench_list = []
        for b_name in BENCH_DESCRIPTIONS.keys():
            # 尝试直接按 b_name 查找，若找不到则尝试映射别名（例如 osprey_coprime）
            item = None
            for candidate in FALLBACK_NAMES.get(b_name, [b_name]):
                if candidate in curr_benches:
                    item = curr_benches[candidate].copy()
                    break
            if item:
                meta_info = BENCH_DESCRIPTIONS[b_name]
                item["name"] = b_name
                item["desc_zh"] = meta_info["zh"]
                item["desc_en"] = meta_info["en"]
                item["category"] = meta_info["cat"]
                new_bench_list.append(item)
            else:
                # 构造占位数据对象
                new_bench_list.append(build_bench_item(b_name, {}))
        pdata["benches"] = new_bench_list

    existing_data["benches"] = platforms.get("macos-arm64", {}).get("benches", [])
    existing_data["metadata"]["total_benches"] = len(BENCH_DESCRIPTIONS)

    DATA_FILE.write_text(json.dumps(existing_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"✓ Synchronized {len(existing_data['benches'])} benchmark items to {DATA_FILE}")


if __name__ == "__main__":
    sync_sources()
    sync_data()
