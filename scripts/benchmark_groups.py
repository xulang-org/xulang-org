"""Presentation families; canonical workloads and measurements stay independent."""

FAMILIES = (
    ('fibonacci', 'control', 'Fibonacci', '斐波那契递归', (
        ('fib', 'Recursive fib(34)', '递归 fib(34)'),
        ('osprey_fib', 'Osprey recursive fib(35)', 'Osprey 递归 fib(35)'),
    )),
    ('nested-loops', 'control', 'Nested loops', '嵌套循环', (
        ('nested_loop', '2D multiply / mask · 8,000 × 8,000', '二维乘法与掩码 · 8,000 × 8,000'),
        ('osprey_nestedloop', 'Osprey modular accumulation · 250³', 'Osprey 模运算累加 · 250³'),
    )),
    ('primes', 'algo', 'Prime numbers', '素数计算', (
        ('sieve_primes', 'Eratosthenes sieve · below 2,000,000', '埃氏筛法 · 小于 2,000,000'),
        ('osprey_primes', 'Osprey trial division · below 200,000', 'Osprey 试除法 · 小于 200,000'),
    )),
    ('sorting', 'algo', 'Sorting', '排序算法', (
        ('sort_lcg', 'Standard-library sort · 100,000 integers', '标准库排序 · 100,000 个整数'),
        ('quicksort_hoare', 'Hoare quicksort · 5 × 100,000 integers', 'Hoare 快排 · 5 × 100,000 个整数'),
        ('merge_sort', 'Osprey merge sort · 8 × 2,000 integers', 'Osprey 归并排序 · 8 × 2,000 个整数'),
        ('osprey_quicksort', 'Osprey functional quicksort · 8 × 2,000 integers', 'Osprey 函数式快排 · 8 × 2,000 个整数'),
    )),
    *((
        'aes-' + operation, 'crypto', en, zh,
        tuple((f'aes{bits}_{suffix}', f'AES-{bits}', f'AES-{bits}') for bits in (128, 192, 256))
    ) for operation, suffix, en, zh in (
        ('encrypt', 'encrypt', 'AES encryption', 'AES 加密'),
        ('decrypt', 'decrypt', 'AES decryption', 'AES 解密'),
        ('key-setup', 'key_setup', 'AES key expansion', 'AES 密钥扩展'),
    )),
)


def group_workloads(benches: list[dict]) -> list[dict]:
    """Group existing rows in first-occurrence order without modifying them."""
    by_name = {b['name']: b for b in benches}
    membership = {v[0]: family for family in FAMILIES for v in family[4]}
    groups, seen = [], set()
    for bench in benches:
        family = membership.get(bench['name'])
        if family:
            key, category, en, zh, variants = family
            members = [dict(bench=by_name[name], label_en=label_en, label_zh=label_zh)
                       for name, label_en, label_zh in variants if name in by_name]
        else:
            key, category = bench['name'], bench.get('category')
            en, zh = bench.get('desc_en', key), bench.get('desc_zh', key)
            members = [dict(bench=bench, label_en=en, label_zh=zh)]
        if key not in seen:
            groups.append(dict(id=key, category=category, title_en=en, title_zh=zh, variants=members))
            seen.add(key)
    return groups


def platform_groups(platforms: dict) -> list[dict]:
    rows = next((p['benches'] for p in platforms.values() if p.get('benches')), [])
    return group_workloads(rows)
