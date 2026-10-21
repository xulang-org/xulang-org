"""Shared navigation and page shell for the static official site."""

from html import escape
import json
from pathlib import Path
from string import Template

DOC_GROUPS = [
    ('xi-bookmark', '起步', 'Start', [
        ('start', '起步', 'Get started'), ('install', '安装', 'Install'),
        ('faq', '常见问题', 'FAQ'),
        ('modules', '模块与依赖', 'Modules and dependencies'), ('packages', '扩展包', 'External packages'),
        ('native', '原生模块与 .xulib', 'Native modules & .xulib'),
    ]),
    ('xi-code', '教程', 'Tutorial', [
        (f'tutorial/{i:02}', f'{i:02} {label}', f'{i:02} {label}')
        for i, label in enumerate('hello bindings control functions errors ownership arrays enum generics concurrency http fileserver context tcp udp ui'.split(), 1)
    ]),
    ('xi-ownership', '语言', 'Language', [
        ('lang/goals', '设计目标', 'Goals'), ('lang/syntax', '语法定稿', 'Syntax freeze'),
        ('lang/lexical', '词法', 'Lexical'), ('lang/structure', '程序结构', 'Structure'),
        ('lang/types', '类型', 'Types'), ('lang/functions', '函数与表达式', 'Functions'),
        ('lang/memory', '内存模型', 'Memory'), ('lang/concurrency', '并发', 'Concurrency'),
        ('lang/ebnf', 'EBNF', 'EBNF'), ('lang/stdlib', '标准库边界', 'Stdlib boundary'),
        ('lang/toolchain', '工具链', 'Toolchain'), ('lang/status', '规范快照', 'Spec snapshot'),
    ]),
    ('xi-terminal', '工具', 'Tools', [
        ('cli', '命令行', 'CLI'), ('ui', 'UI / WebView', 'UI / WebView'),
        ('vscode', 'VS Code', 'VS Code'), ('status', '限制与现状', 'Limitations'),
    ]),
]
API_GROUPS = [
    ('xi-api', 'API', 'API', ['']),
    ('xi-cpu', '核心', 'Core', 'errors fmt flag cmp context sync time runtime maps slices sort testing testing/fstest'.split()),
    ('xi-file', '文本', 'Text', 'strings bytes strconv unicode regexp html'.split()),
    ('xi-terminal', 'IO / OS', 'IO / OS', 'io io/fs os os/exec os/signal os/user bufio path log'.split()),
    ('xi-globe', '网络', 'Net', 'net net/http net/http/cookiejar net/http/httptest net/netip net/url'.split()),
    ('xi-binary', '编码', 'Encoding', 'encoding/json encoding/hex encoding/base64'.split()),
    ('xi-shield-check', '密码与国密', 'Crypto', 'crypto/aes crypto/cipher crypto/sm2 crypto/sm3 crypto/sm4 crypto/sm9 crypto/zuc crypto/gmtls crypto/tls crypto/rand crypto/rsa crypto/sha256 crypto/sha512 crypto/sha1 crypto/sha3 crypto/md5 crypto/hmac crypto/x509 crypto/x509/pkix crypto/ecdsa crypto/ed25519 crypto/des crypto/rc4 crypto/subtle crypto/password crypto/jwt'.split()),
    ('xi-package', '压缩 / 图像 / 数学', 'Compress / image / math', 'compress/gzip image math'.split()),
    ('xi-database', '数据库', 'Database', 'database/sql database/sql/driver'.split()),
    ('xi-package', '扩展包', 'External packages', ['packages/' + name for name in
        'cassandra chroma clickhouse consul dns elasticsearch etcd grpc influxdb kafka meilisearch memcached milvus mongodb mqtt mysql nacos nats neo4j postgres prometheus qdrant rabbitmq redis s3 smtp sqlite websocket zookeeper'.split()]),
    ('xi-xuui', 'UI', 'UI', 'ui ui/webview ui/draw'.split()),
]

SOCIAL_PROFILES = [
    ('GitHub', 'xulang-org', 'https://github.com/xulang-org', 'github'),
    ('X', 'xulang_org', 'https://x.com/xulang_org', 'x'),
]
SOCIAL_ICONS = {
    'github': '<path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38l-.01-1.49c-2.23.48-2.7-1.08-2.7-1.08-.36-.92-.89-1.17-.89-1.17-.73-.5.06-.49.06-.49.8.06 1.22.82 1.22.82.71 1.22 1.87.87 2.33.67.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.96 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.65 7.65 0 0 1 4 0c1.53-1.03 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.28.82 2.15 0 3.08-1.87 3.75-3.65 3.95.29.25.54.74.54 1.48l-.01 2.34c0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z"/>',
    'x': '<path d="M12.6 1h2.3L9.9 6.7 15.8 15h-4.6L7.6 10 3.2 15H.9l5.6-6.4L.8 1h4.7l3.3 4.6L12.6 1ZM11.8 13.5h1.3L4.8 2.4H3.4l8.4 11.1Z"/>',
}


def social_links(en: bool, compact: bool = False) -> str:
    links = []
    new_tab = 'opens in a new tab' if en else '在新标签页打开'
    for platform, handle, href, icon in SOCIAL_PROFILES:
        label = f'{platform} · @{handle} · {new_tab}'
        svg = ('<svg class="social-icon" viewBox="0 0 16 16" width="18" height="18" '
               'fill="currentColor" aria-hidden="true" focusable="false">' + SOCIAL_ICONS[icon] + '</svg>')
        text = '' if compact else f'<span>{platform} <span class="social-handle">@{handle}</span></span>'
        links.append(f'<a class="social-link" href="{href}" target="_blank" rel="me noopener noreferrer" '
                     f'aria-label="{escape(label)}" title="{escape(label)}">{svg}{text}</a>')
    return ''.join(links)


def side_link(href: str, label: str, route: str) -> str:
    active = ' class="on" aria-current="page"' if route == href else ''
    return f'<li><a{active} href="{href}">{escape(label)}</a></li>'


def sidebar(route: str, en: bool, xu_version: str = '') -> str:
    prefix = '' if en else '/zh'
    rest = route if en else route.removeprefix('/zh')
    groups = []
    if rest.startswith('/docs/'):
        for icon, zh, english, links in DOC_GROUPS:
            groups.append((icon, english if en else zh, [
                (prefix + '/docs/' + href, english_label if en else zh_label)
                for href, zh_label, english_label in links
            ]))
    elif rest == '/api' or rest.startswith('/api/'):
        for icon, zh, english, packages in API_GROUPS:
            groups.append((icon, english if en else zh, [
                (prefix + '/api' + ('/' + package if package else ''),
                 '#' + package.removeprefix('packages/') if package else 'Index')
                for package in packages
            ]))
    elif rest == '/blog' or rest.startswith('/blog/'):
        groups.append(('xi-chat', 'Blog', [
            (prefix + '/blog', 'Index' if en else '博客索引'),
            (prefix + '/blog/xu-lsp-and-vscode', 'Xu LSP & vscode-xu' if en else 'Xu LSP 与 vscode-xu'),
            (prefix + '/blog/xu-0-8-13', 'Xu 0.8.13'),
            (prefix + '/blog/xu-0-8-12', 'Xu 0.8.12'),
            (prefix + '/blog/xu-0-8-11', 'Xu 0.8.11'),
            (prefix + '/blog/xu-0-8-8', 'Xu 0.8.8'),
            (prefix + '/blog/xu-0-8-4', 'Xu 0.8.x · 0.8.4'),
            (prefix + '/blog/packages-0-1-1', 'packages 0.1.1'),
            (prefix + '/blog/xu-0-1-0', 'Xu 0.1.0'),
        ]))
    if not groups:
        return ''

    # 判断是否有任何一个组命中当前路由
    matched_idx = -1
    for idx, (_, _, links) in enumerate(groups):
        if any(href == route for href, _ in links):
            matched_idx = idx
            break

    sections = []
    for idx, (icon, label, links) in enumerate(groups):
        # 激活规则：
        # 1. 命中当前路由的组必定展开；
        # 2. 如果未命中任何具体组：
        #    - 在 docs 下：默认展开前两组（起步与教程）；
        #    - 在 api 下：默认展开前两组（Index与核心）；
        #    - 在 blog 下：默认展开；
        if matched_idx >= 0:
            is_open = (idx == matched_idx)
        else:
            is_open = (idx < 2) if (rest.startswith('/docs/') or rest.startswith('/api')) else True

        open_cls = ' is-open' if is_open else ''
        expanded_attr = 'true' if is_open else 'false'
        count = len(links)
        count_tag = f'<span class="side-badge">{count}</span>' if count > 1 else ''

        links_html = ''.join(side_link(href, text, route) for href, text in links)

        sections.append(
            f'<div class="side-group{open_cls}" data-group-index="{idx}">'
            f'  <button type="button" class="side-h" aria-expanded="{expanded_attr}" onclick="toggleSideGroup(this)">'
            f'    <div class="side-h-title"><i class="xi {icon}"></i> <span>{escape(label)}</span></div>'
            f'    <div class="side-h-meta">{count_tag}<i class="xi xi-chevron-down side-chevron"></i></div>'
            f'  </button>'
            f'  <ul class="side-list">'
            f'    {links_html}'
            f'  </ul>'
            f'</div>'
        )

    toggle_all_title = "Toggle all sections" if en else "折叠/展开全部菜单"
    scroll_top_title = "Back to top of menu" if en else "回到目录顶部"

    side_header = (
        f'<div class="side-header">'
        f'  <span class="side-header-title">{"Sections" if en else "目录导航"}</span>'
        f'  <button type="button" class="side-toggle-all-btn" onclick="toggleAllSideGroups(this)" title="{toggle_all_title}" aria-label="{toggle_all_title}">'
        f'    <i class="xi xi-sliders"></i>'
        f'  </button>'
        f'</div>'
    )

    ver_display = f'v{escape(xu_version)}' if xu_version else 'SDK'
    side_footer = (
        f'<div class="side-footer">'
        f'  <div class="side-footer-meta"><i class="xi xi-tag xi-brand"></i> <span>XU {ver_display}</span></div>'
        f'  <div class="side-footer-actions">'
        f'    <button type="button" class="side-footer-btn" onclick="scrollSideToTop(this)" title="{scroll_top_title}" aria-label="{scroll_top_title}">'
        f'      <i class="xi xi-arrow-up"></i>'
        f'    </button>'
        f'    <button type="button" class="side-footer-btn" onclick="toggleAllSideGroups(this)" title="{toggle_all_title}" aria-label="{toggle_all_title}">'
        f'      <i class="xi xi-sliders"></i>'
        f'    </button>'
        f'  </div>'
        f'</div>'
    )

    return (
        f'<aside class="side">'
        f'  {side_header}'
        f'  <div class="side-content">{"".join(sections)}</div>'
        f'  {side_footer}'
        f'</aside>'
    )


def get_seo_meta(route: str, title: str, en: bool, xu_version: str) -> dict[str, str]:
    origin = "https://xulang.org"
    if route in ('/', '/zh'):
        url_en = f"{origin}/"
        url_zh = f"{origin}/zh/"
        canonical_url = url_en if en else url_zh
    elif route == '/404':
        url_en = f"{origin}/"
        url_zh = f"{origin}/zh/"
        canonical_url = f"{origin}/404.html"
    else:
        bare_route = route if en else (route[3:] or '/')
        url_en = f"{origin}{bare_route.rstrip('/')}/"
        url_zh = f"{origin}/zh{bare_route.rstrip('/')}/"
        canonical_url = url_en if en else url_zh

    bare_path = route if en else (route[3:] or '/')
    bare_path = bare_path.strip('/')

    if not bare_path:
        if en:
            desc = f"Official portal for Xu v{xu_version} — rock-solid memory safety with zero runtime GC overhead, supersonic native AOT & WebAssembly compilation, user-space coroutines, and typed channels."
        else:
            desc = f"Xu 编程语言官方网站 (v{xu_version}) — 坚若磐石、零 GC 运行时开销、超音速原生 AOT 与 WebAssembly 编译的系统级编程语言，具备确定性 RAII 所有权、轻量协程与类型安全通道。"
    elif bare_path == 'benchmarks':
        if en:
            desc = "Cross-language runtime, CPU time, peak memory and binary-size measurements across Linux, macOS and Windows on ARM64 and x86-64. See the measured Xu version and source CI records."
        else:
            desc = "Xu 跨语言运行耗时、CPU 时间、峰值内存与二进制体积实测，覆盖 Linux、macOS、Windows 的 ARM64 与 x86-64 平台，标注实际测量版本并提供来源 CI 记录。"
    elif bare_path == 'playground':
        if en:
            desc = f"Interactive in-browser WebAssembly playground for Xu v{xu_version}. Compile, borrow-check, and execute Xu code client-side with zero installation."
        else:
            desc = f"Xu 编程语言 (v{xu_version}) 在线 WebAssembly 演练场。纯浏览器端客户端沙盒，即时编译、借用检查与执行 Xu 代码，免本地安装。"
    elif bare_path == 'download':
        if en:
            desc = f"Download official Xu v{xu_version} compiler SDK and toolchain for macOS, Linux, and Windows. One-line automated install scripts and release packages."
        else:
            desc = f"下载官方 Xu (v{xu_version}) 编译器 SDK 与工具链（macOS、Linux、Windows）。支持一键自动化安装脚本与原生二进制发行包。"
    elif bare_path.startswith('docs/faq'):
        if en:
            desc = f"Frequently Asked Questions (FAQ) for Xu v{xu_version} — Custom native backend, zero-GC memory safety, LSP editor support, xu get vs xu install, native C modules, and WebAssembly."
        else:
            desc = f"Xu 编程语言 (v{xu_version}) 常见问题解答 (FAQ) — 自研原生后端、零 GC 内存安全、LSP 编辑器支持、xu get 与 xu install 依赖管理、xu native 原生 C 模块及 WebAssembly。"
    elif bare_path.startswith('docs/tutorial'):
        if en:
            desc = f"{title} — Hands-on step-by-step tutorial for the Xu programming language, covering syntax, ownership, concurrency, and real-world networking."
        else:
            desc = f"{title} — Xu 编程语言实战系列教程，系统讲解语法结构、所有权机制、高并发通道与系统级网络编程。"
    elif bare_path.startswith('docs/lang'):
        if en:
            desc = f"{title} — Official language specification, memory model, concurrency architecture, and formal grammar for Xu."
        else:
            desc = f"{title} — Xu 编程语言官方规范：语法定义、内存模型与所有权语义、并发调度架构与 EBNF 文法。"
    elif bare_path.startswith('api'):
        if en:
            desc = f"Official API reference for {title} in the Xu v{xu_version} standard library and extended package ecosystem."
        else:
            desc = f"Xu 编程语言 (v{xu_version}) 标准库与扩展包官方 API 参考文档：{title}。"
    elif bare_path.startswith('blog'):
        if en:
            desc = f"{title} — Engineering blog post and release updates from the Xu programming language team."
        else:
            desc = f"{title} — Xu 编程语言团队官方技术博客与版本发布动态。"
    else:
        if en:
            desc = f"{title} — Documentation, guides, and tools for the Xu systems programming language."
        else:
            desc = f"{title} — Xu 系统级编程语言官方文档、工具与开发者指南。"

    keywords = (
        "Xu, Xu programming language, xulang, systems programming, AOT compiler, zero GC, memory safety, RAII, coroutines, channels, WebAssembly, WASM, performance benchmarks, LLVM alternative"
        if en else
        "Xu, Xu语言, 系统级编程语言, AOT编译器, 零GC, 内存安全, 所有权模型, 协程, 信道, WebAssembly, 性能评测, LLVM"
    )

    og_type = "website" if bare_path in ('', 'playground', 'benchmarks', 'download', '404') else "article"
    og_locale = "en_US" if en else "zh_CN"

    faq_entities = [
        {
            "@type": "Question",
            "name": "Does the Xu compiler use LLVM? Why a custom native backend?" if en else "Xu 编译器是否使用了 LLVM？为什么采用自研后端？",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": "No, Xu does not use LLVM. The compiler utilizes a completely self-hosted, custom MIR (Mid-level Intermediate Representation), register allocators, and direct machine code emitters that output native Mach-O, ELF, PE, and WASM binaries. LLVM's massive pass pipeline causes slow C++/Rust compile cycles; Xu targets Go-like sub-second compilation speeds, produces a compact single-binary compiler (~15MB), and requires zero external C++ runtime libraries." if en else "没有使用 LLVM。Xu 编译器采用完全自主研发的轻量 MIR（中间表示）、寄存器分配器与直接原生机器码发射器，直出 Mach-O、ELF、PE 与 WASM 二进制。LLVM pass 链庞大沉重，是 C++/Rust 编译龟速的根源；Xu 追求类似 Go 的亚秒级极致编译速度，且编译器本身为单文件极简二进制（约 15MB），零外置 C++ 动态库依赖，真正开箱即用。"
            }
        },
        {
            "@type": "Question",
            "name": "Does Xu use a garbage collector (GC)?" if en else "Xu 语言是否有垃圾回收（GC）？",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": "No. Xu has zero runtime GC overhead and no Stop-The-World (STW) pauses. Memory is managed deterministically through compile-time single-ownership tracking and RAII scoping drop, complemented by static shared (&T) and exclusive (&mut T) borrow checking." if en else "没有。Xu 完全不依赖任何运行时垃圾回收器（Zero GC），没有 Stop-The-World (STW) 暂停。内存由编译期唯一所有权跟踪与 RAII 作用域析构确定性释放，并通过 &T 共享借用与 &mut T 独占借用在编译阶段彻底消除悬垂指针、内存泄漏与多线程数据竞争。"
            }
        },
        {
            "@type": "Question",
            "name": "How does Xu compare to Rust and Go?" if en else "Xu 相比 Rust 与 Go 有哪些区别？",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": "Compared to Rust, Xu delivers memory safety and zero runtime overhead without complex lifetime annotations (<'a>), offering first-class language-level coroutines and channels without bulky async runtimes. Compared to Go, Xu compiles to true zero-GC native machine code without runtime STW latency, baseline memory bloat, or background GC threads." if en else "相比 Rust，Xu 在提供同等确定性零成本内存安全的同时，去除了复杂的显式生命周期标注（如 <'a>），并将轻量协程与通信通道作为语言一等公民内置，无需引入笨重的外部异步运行时；相比 Go，Xu 保持了轻快直观的并发体验，但编译为零 GC 原生机器码，完全没有并发三色标记清除 GC 的内存常驻底线与停顿延迟。"
            }
        },
        {
            "@type": "Question",
            "name": "How fast are Xu's compilation speed and runtime throughput?" if en else "Xu 的编译速度与实际执行性能如何？",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": "Compare Xu with C, Rust, Go and Swift across 47 workloads on six ARM64 and x86-64 platforms. The benchmark dashboard reports per-platform runtime, CPU time, peak memory and binary size; C and Rust use the lowest measured O1–O3 median for each workload. Compilation timings are available in the source CI reports." if en else "47 项负载覆盖 ARM64、x86-64 六个平台，对照 Xu、C、Rust、Go 和 Swift。横测看板展示各平台的运行耗时、CPU 时间、峰值内存与二进制体积；C、Rust 按负载选取同平台 O1–O3 的最小实测中位数。编译耗时记录在来源 CI 的原始报告中。"
            }
        },
        {
            "@type": "Question",
            "name": "Which editors support Xu, and how do I enable LSP?" if en else "Xu 支持哪些编辑器？如何启用 LSP？",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": "The official vscode-xu extension supports VS Code and Cursor. It runs xu lsp to launch the SDK's xu-lsp server for diagnostics, completion, go-to-definition, hover, symbols, references, rename, and formatting. Other LSP-compatible editors can launch xu lsp over stdin/stdout using JSON-RPC 2.0. Run xu lsp --help for help." if en else "官方 vscode-xu 扩展支持 VS Code 与 Cursor，通过 xu lsp 启动 SDK 中的 xu-lsp 语言服务器，提供诊断、补全、跳转定义、悬停、符号大纲、查找引用、重命名与格式化。其他支持 LSP 的编辑器也可配置 xu lsp，通过 stdin/stdout 交换 JSON-RPC 2.0 消息。可用 xu lsp --help 查看帮助。"
            }
        },
        {
            "@type": "Question",
            "name": "What is the difference between xu get and xu install?" if en else "xu get 与 xu install 有什么区别？",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": "In a project containing xu.xun, xu get github.com/xulang-org/packages@v0.1.1 adds or updates a pinned dependency, edits require:, installs sources into vendor/, and updates xu.lock. An explicit exact version is required; @latest is not accepted. xu install installs already-declared dependencies. Both support --offline; use xu build . --frozen for strict lockfile builds. The official packages repository provides 29 extension packages." if en else "在已有 xu.xun 的项目中，xu get github.com/xulang-org/packages@v0.1.1 添加或更新指定依赖，修改 require:、安装源码到 vendor/ 并更新 xu.lock。必须显式指定精确版本，不接受 @latest。xu install 安装清单中已经声明的依赖。两者均支持 --offline；严格按现有锁文件构建使用 xu build . --frozen。官方 packages 仓库提供 29 个扩展包。"
            }
        },
        {
            "@type": "Question",
            "name": "Does Xu support WebAssembly (WASM) out of the box?" if en else "Xu 是否原生支持 WebAssembly (WASM)？",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": "Yes, first-class native support. The compiler directly emits wasm32 binary modules (xu build --target wasm32) without Emscripten or external dependencies. The interactive in-browser Playground on xulang.org compiles the Xu compiler itself directly to WebAssembly to run client-side." if en else "原生一等公民支持。编译器内建 wasm32 直接后端（xu build --target wasm32），无需 Emscripten 或外置工具。官网上的在线演练场（Playground）正是将 Xu 编译器源码直接编译为 WASM，纯浏览器前端运行，免安装即可体验实时语法编译与借用检查。"
            }
        },
        {
            "@type": "Question",
            "name": "How do I use xu native to integrate C code?" if en else "如何用 xu native 集成 C 代码？",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": "xu native compile compiles C sources with interface metadata into .a; xu native archive wraps existing object files with metadata; xu native pack bundles target slices into .xulib; xu native inspect and xu native extract inspect and extract slices. Use .a for a single target and .xulib for distribution with interface contracts and multiple target slices. Build with xu build main.xu native/mylib.xulib -o app. Compiling C requires the corresponding C toolchain; run xu native compile --help for options." if en else "xu native compile 将 C 源码与接口元数据编译为 .a；xu native archive 为已有目标文件封装元数据；xu native pack 将目标切片打包为 .xulib；xu native inspect 与 xu native extract 用于检查和提取切片。.a 用于单目标，.xulib 用于携带接口契约与多个目标切片的分发。构建示例：xu build main.xu native/mylib.xulib -o app。编译 C 需相应的 C 工具链；参数见 xu native compile --help。"
            }
        },
        {
            "@type": "Question",
            "name": "What operating systems and CPU architectures are supported?" if en else "Xu 目前支持哪些操作系统与 CPU 芯片架构？",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": "Native multi-platform matrix: operating systems include macOS (Darwin), Linux, Windows (PE AOT), and WebAssembly; hardware architectures include ARM64 (Apple Silicon / AWS Graviton), x86-64 (Intel / AMD), LoongArch64, RISC-V 64/32, and Linux ARM32." if en else "原生支持主流跨端全矩阵：操作系统覆盖 macOS、Linux、Windows (PE AOT) 及 WebAssembly；CPU 架构支持 ARM64 (Apple Silicon / AWS Graviton)、x86-64 (Intel / AMD)、LoongArch64 (龙芯)、RISC-V 64/32 及 Linux ARM32。"
            }
        }
    ]

    if not bare_path:
        schema = {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "WebSite",
                    "@id": f"{origin}/#website",
                    "url": f"{origin}/",
                    "name": "Xu Programming Language",
                    "description": desc,
                    "inLanguage": ["en", "zh-CN"]
                },
                {
                    "@type": "Organization",
                    "@id": f"{origin}/#organization",
                    "name": "Xu Programming Language Organization",
                    "url": f"{origin}/",
                    "logo": f"{origin}/xu_classic.svg",
                    "sameAs": [
                        "https://github.com/xulang-org",
                        "https://x.com/xulang_org"
                    ]
                },
                {
                    "@type": "SoftwareApplication",
                    "@id": f"{origin}/#software",
                    "name": "Xu",
                    "operatingSystem": "macOS, Linux, Windows, WebAssembly",
                    "applicationCategory": "DeveloperApplication",
                    "softwareVersion": xu_version,
                    "license": "https://opensource.org/licenses/MIT",
                    "offers": {
                        "@type": "Offer",
                        "price": "0",
                        "priceCurrency": "USD"
                    }
                },
                {
                    "@type": "FAQPage",
                    "@id": f"{origin}/#faq",
                    "name": "Xu Frequently Asked Questions" if en else "Xu 编程语言常见问题解答",
                    "mainEntity": faq_entities
                }
            ]
        }
    elif bare_path == 'docs/faq':
        schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "headline": title,
            "description": desc,
            "url": canonical_url,
            "inLanguage": "en" if en else "zh-CN",
            "mainEntity": faq_entities,
            "publisher": {
                "@type": "Organization",
                "name": "Xu Programming Language",
                "url": f"{origin}/",
                "logo": f"{origin}/xu_classic.svg"
            }
        }
    else:
        schema = {
            "@context": "https://schema.org",
            "@type": "TechArticle" if bare_path.startswith(('docs', 'api')) else "Article",
            "headline": title,
            "description": desc,
            "url": canonical_url,
            "inLanguage": "en" if en else "zh-CN",
            "publisher": {
                "@type": "Organization",
                "name": "Xu Programming Language",
                "url": f"{origin}/",
                "logo": f"{origin}/xu_classic.svg"
            }
        }

    schema_json_ld = f'<script type="application/ld+json">\n{json.dumps(schema, ensure_ascii=False, indent=2)}\n  </script>'

    return {
        'meta_description': escape(desc, quote=True),
        'meta_keywords': escape(keywords, quote=True),
        'canonical_url': canonical_url,
        'url_en': url_en,
        'url_zh': url_zh,
        'og_type': og_type,
        'og_locale': og_locale,
        'schema_json_ld': schema_json_ld,
    }


def render(root: Path, title: str, route: str, body: str, xu_version: str) -> str:
    en = not (route == '/zh' or route.startswith('/zh/'))
    prefix = '' if en else '/zh'
    home = prefix or '/'
    nav = []
    for href, icon, zh, english in [
        ('/docs/start', 'book', '文档', 'Docs'),
        ('/api', 'api', 'API', 'API'),
        ('/playground', 'play', '演练场', 'Playground'),
        ('/benchmarks', 'benchmark', '横测', 'Benchmarks'),
        ('/download', 'download', '下载', 'Download'),
        ('/blog', 'chat', '博客', 'Blog'),
    ]:
        target = prefix + href
        if href == '/docs/start':
            active = route == target or route.startswith(prefix + '/docs/')
        elif href == '/api':
            active = route == target or route.startswith(prefix + '/api/')
        elif href == '/blog':
            active = route == target or route.startswith(prefix + '/blog/')
        else:
            active = route == target
        cls = 'nav-tab-btn active' if active else 'nav-tab-btn'
        current = ' aria-current="page"' if active else ''
        nav.append(f'<a class="{cls}"{current} href="{target}"><i class="xi xi-{icon}"></i> {english if en else zh}</a>')
    if route in ('/', '/zh'):
        main = '<main class="home">' + body + '</main>'
    elif route in ('/playground', '/zh/playground'):
        main = '<main class="home playground-page">' + body + '</main>'
    elif route in ('/benchmarks', '/zh/benchmarks'):
        main = '<main class="home bench-page">' + body + '</main>'
    else:
        cls = 'doc download' if route == prefix + '/download' else 'doc'
        main = '<div class="page page-with-side">' + sidebar(route, en, xu_version) + f'<main class="{cls}">' + body + '</main></div>'
    other = ('/zh' if route == '/' else '/zh' + route) if en else (route[3:] or '/')
    if route == '/404':
        other = '/zh'
    meta = get_seo_meta(route, title, en, xu_version)
    template = Template((root / 'templates/page.html').read_text(encoding='utf-8'))
    return template.substitute(
        lang='en' if en else 'zh-CN', title=escape(title), home=home,
        home_title='Xu Home' if en else 'Xu 官网首页',
        xu_version=escape(xu_version), nav=''.join(nav), main=main,
        other_lang=other, other_lang_code='zh-CN' if en else 'en',
        lang_title='中文' if en else 'English', lang_label='中文' if en else 'EN',
        theme_label='Switch theme' if en else '切换主题', ui_href=prefix + '/docs/ui',
        footer_text=('<a href="/LICENSE">MIT License</a> · Zero GC · Supersonic AOT' if en
                     else '<a href="/LICENSE">MIT 开源协议</a> · 坚若磐石 · 零 GC 内存安全 · 超音速 AOT'),
        header_social=social_links(en, compact=True), footer_social=social_links(en),
        social_label='Official accounts' if en else '官方帐号',
        menu_label='Navigation menu' if en else '导航菜单',
        nav_label='Main navigation' if en else '主导航',
        **meta,
    )
