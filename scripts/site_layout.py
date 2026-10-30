"""Shared navigation and page shell for the static official site."""

from html import escape
from html.parser import HTMLParser
from collections.abc import Iterable
import json
from pathlib import Path
import re
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
_CURATED_API_GROUPS = [
    ('xi-api', 'API', 'API', ['']),
    ('xi-cpu', '核心', 'Core', 'errors fmt flag cmp context sync time runtime maps slices sort testing testing/fstest xacp'.split()),
    ('xi-file', '文本', 'Text', 'strings bytes strconv unicode regexp html'.split()),
    ('xi-terminal', 'IO / OS', 'IO / OS', 'io io/fs os os/exec os/signal os/user bufio path log'.split()),
    ('xi-globe', '网络', 'Net', 'net net/http net/http/cookiejar net/http/httptest net/netip net/url'.split()),
    ('xi-binary', '编码', 'Encoding', 'encoding/json encoding/hex encoding/base64'.split()),
    ('xi-shield-check', '密码与国密', 'Crypto', 'crypto/aes crypto/cipher crypto/sm2 crypto/sm3 crypto/sm4 crypto/sm9 crypto/zuc crypto/gmtls crypto/tls crypto/rand crypto/rsa crypto/sha256 crypto/sha512 crypto/sha1 crypto/sha3 crypto/md5 crypto/hmac crypto/x509 crypto/x509/pkix crypto/ecdsa crypto/ed25519 crypto/des crypto/rc4 crypto/subtle crypto/password crypto/jwt'.split()),
    ('xi-package', '压缩 / 图像 / 数学', 'Compress / image / math', 'compress/gzip image math'.split()),
    ('xi-database', '数据库', 'Database', 'database/sql database/sql/driver'.split()),
    ('xi-package', '扩展包', 'Extensions', ['packages/' + name for name in
        'cassandra chroma clickhouse consul dns elasticsearch etcd grpc influxdb kafka meilisearch memcached milvus mongodb mqtt mysql nacos nats neo4j postgres prometheus qdrant rabbitmq redis s3 smtp sqlite websocket zookeeper'.split()]),
    ('xi-xuui', 'UI', 'UI', 'ui ui/draw ui/layout ui/widgets ui/webview'.split()),
]


def api_pages(root: Path | None = None) -> set[str]:
    """Discover released pages, including widget details but excluding previews."""
    api_root = (root or Path(__file__).resolve().parents[1]) / 'content/en/api'
    return {
        page.relative_to(api_root).with_suffix('').as_posix()
        for page in api_root.rglob('*.html')
        if page.name != 'index.html' and 'preview' not in page.relative_to(api_root).parts
    }


def group_api_packages(packages: Iterable[str]) -> list[tuple[str, str, str, list[str]]]:
    """Apply the same curated topic order to generated packages and disk pages."""
    on_disk = set(packages)
    groups = [
        (icon, zh, en, [package for package in packages if not package or package in on_disk])
        for icon, zh, en, packages in _CURATED_API_GROUPS
    ]
    namespaces = {
        package.partition('/')[0]: index
        for index, (_icon, _zh, _en, packages) in enumerate(_CURATED_API_GROUPS)
        for package in packages if package
    }
    listed = {package for _icon, _zh, _en, packages in groups for package in packages}
    other = []
    for package in sorted(on_disk - listed):
        index = namespaces.get(package.partition('/')[0])
        (groups[index][3] if index is not None else other).append(package)
    if other:
        groups.append(('xi-package', '其他', 'Other', other))
    return [group for group in groups if group[3]]


def api_groups(root: Path | None = None) -> list[tuple[str, str, str, list[str]]]:
    return group_api_packages(api_pages(root))


def widget_catalog(root: Path | None = None) -> dict:
    path = (root or Path(__file__).resolve().parents[1]) / 'templates/widgets.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}


def api_sections(packages: Iterable[str], root: Path | None = None) -> list[tuple]:
    """Three primary buckets shared by the API index and every released sidebar."""
    standard, ui, extensions = [], [], []
    for icon, zh, en, members in group_api_packages(packages):
        if en == 'API':
            continue
        if en == 'UI':
            modules = [p for p in members if not p.startswith('ui/widgets/')]
            widgets = set(members) - set(modules)
            if modules:
                ui.append((icon, '包', 'Packages', modules))
            catalog = widget_catalog(root)
            for category, labels in catalog.get('groups', {}).items():
                paths = ['ui/widgets/' + c['slug'] for c in catalog['components']
                         if c['group'] == category and 'ui/widgets/' + c['slug'] in widgets]
                if paths:
                    ui.append(('xi-package', labels[0], labels[1], paths))
                    widgets.difference_update(paths)
            if widgets:
                ui.append(('xi-package', '其他控件', 'Other widgets', sorted(widgets)))
        elif en == 'Extensions':
            extensions.append((icon, '集成', 'Integrations', members))
        else:
            standard.append((icon, zh, en, members))
    return [
        ('standard-library', 'xi-cpu', '标准库', 'Standard library', standard),
        ('ui', 'xi-xuui', 'UI', 'UI', ui),
        ('extensions', 'xi-package', '扩展包', 'Extensions', extensions),
    ]


API_GROUPS = api_groups()


class PackageInventory(HTMLParser):
    """The generated index lists packages; widget detail pages are not packages."""

    def __init__(self, source: str):
        super().__init__()
        self.packages = set()
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        href = dict(attrs).get('href', '')
        match = re.fullmatch(r'/(?:zh/)?api/([^#?]+)', href)
        if tag == 'a' and match and not match[1].startswith('preview/'):
            self.packages.add(match[1])


def shared_content(root: Path) -> dict[str, dict[str, str]]:
    """Expand bilingual pages from the generated inventory and release metadata."""
    inventories = {}
    for lang in ('en', 'zh'):
        inventory = PackageInventory((root / f'content/{lang}/api/index.html').read_text()).packages
        for package in inventory:
            if not (root / f'content/{lang}/api/{package}.html').is_file():
                raise ValueError(f'API inventory points to a missing package: {lang}/{package}')
        inventories[lang] = inventory
    if not inventories['en'] or inventories['en'] != inventories['zh']:
        raise ValueError('API package inventories must be nonempty and match in EN/ZH')
    external = sum(p.startswith('packages/') for p in inventories['en'])
    releases = release_entries(root)
    values = {}
    for lang in ('en', 'zh'):
        values[lang] = {
            'api_standard_count': str(len(inventories[lang]) - external),
            'api_external_count': str(external),
            'release_notes': '\n'.join(
                f'<h2 id="v{item["version"].replace(".", "-")}">{item["version"]} '
                + ('release' if lang == 'en' else '正式版') + '</h2>\n' + item['notes'][lang]
                for item in releases),
            'release_blog_entries': '\n'.join('<li>' + item['blog_entry'][lang] + '</li>' for item in releases),
        }
    return values


def release_entries(root: Path) -> list[dict]:
    return json.loads((root / 'templates/releases.json').read_text(encoding='utf-8'))

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


def api_sidebar_sections(route: str, en: bool, tree: list[tuple], root: Path | None = None) -> list[str]:
    prefix = '' if en else '/zh'
    index = prefix + '/api'
    widget_names = {'ui/widgets/' + c['slug']: c['name']
                    for c in widget_catalog(root).get('components', [])}
    sections = ['<ul class="side-api-index">' + side_link(index, 'API index' if en else 'API 索引', route) + '</ul>']
    for key, icon, zh, english, topics in tree:
        paths = [p for _icon, _zh, _en, members in topics for p in members]
        is_open = route in [index + '/' + p for p in paths] or (route == index and key == 'standard-library')
        opened = ' open' if is_open else ''
        sections.append(f'<details class="side-api-bucket" data-api-section="{key}"{opened}>'
                        f'<summary><i class="xi {icon}" aria-hidden="true"></i> '
                        f'<span>{escape(english if en else zh)}</span><span class="side-badge">{len(paths)}</span></summary>')
        for _icon, topic_zh, topic_en, members in topics:
            opened = ' open' if any(route == index + '/' + p for p in members) else ''
            sections.append(f'<details class="side-api-topic"{opened}><summary>'
                            f'<span>{escape(topic_en if en else topic_zh)}</span> <span class="side-badge">{len(members)}</span></summary>'
                            '<ul class="side-api-links">')
            for package in members:
                label = '#' + package.removeprefix('packages/')
                if package.startswith('ui/widgets/'):
                    label = widget_names.get(package, package.rsplit('/', 1)[1])
                sections.append(side_link(index + '/' + package, label, route))
            sections.append('</ul></details>')
        sections.append('</details>')
    return sections


def sidebar(route: str, en: bool, xu_version: str = '', root: Path | None = None) -> str:
    prefix = '' if en else '/zh'
    rest = route if en else route.removeprefix('/zh')
    groups = []
    api_tree = None
    if rest.startswith('/docs/'):
        for icon, zh, english, links in DOC_GROUPS:
            groups.append((icon, english if en else zh, [
                (prefix + '/docs/' + href, english_label if en else zh_label)
                for href, zh_label, english_label in links
            ]))
    elif rest == '/api/preview' or rest.startswith('/api/preview/'):
        groups.append(('xi-xuui', 'Development preview' if en else '开发预览', [
            (prefix + '/api/preview', 'Index' if en else '索引'),
            *[(prefix + '/api/preview/' + package, '#' + package)
              for package in ('ui', 'ui/draw', 'ui/layout', 'ui/widgets', 'ui/webview')],
            (prefix + '/api', 'Released SDK API' if en else '正式 SDK API'),
        ]))
    elif rest == '/api' or rest.startswith('/api/'):
        api_tree = api_sections(api_pages(root), root)
    elif rest == '/blog' or rest.startswith('/blog/'):
        groups.append(('xi-chat', 'Blog', [
            (prefix + '/blog', 'Index' if en else '博客索引'),
            *[(prefix + '/blog/xu-' + item['version'].replace('.', '-'), 'Xu ' + item['version'])
              for item in release_entries(root or Path(__file__).resolve().parents[1])],
            (prefix + '/blog/xu-lsp-and-vscode', 'Xu LSP & vscode-xu' if en else 'Xu LSP 与 vscode-xu'),
            (prefix + '/blog/xu-0-8-13', 'Xu 0.8.13'),
            (prefix + '/blog/xu-0-8-12', 'Xu 0.8.12'),
            (prefix + '/blog/xu-0-8-11', 'Xu 0.8.11'),
            (prefix + '/blog/xu-0-8-8', 'Xu 0.8.8'),
            (prefix + '/blog/xu-0-8-4', 'Xu 0.8.x · 0.8.4'),
            (prefix + '/blog/packages-0-1-1', 'packages 0.1.1'),
            (prefix + '/blog/xu-0-1-0', 'Xu 0.1.0'),
        ]))
    if not groups and api_tree is None:
        return ''

    # 判断是否有任何一个组命中当前路由
    matched_idx = -1
    for idx, (_, _, links) in enumerate(groups):
        if any(href == route for href, _ in links):
            matched_idx = idx
            break

    sections = api_sidebar_sections(route, en, api_tree, root) if api_tree is not None else []
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


class FAQParser(HTMLParser):
    """Keep FAQ structured data in sync with the questions shown on each page."""

    def __init__(self):
        super().__init__()
        self.entities = []
        self.active = False
        self.summary = False
        self.question = []
        self.answer = []

    def handle_starttag(self, tag, attrs):
        if tag == 'details' and 'faq-item' in dict(attrs).get('class', '').split():
            self.active = True
            self.question, self.answer = [], []
        elif self.active and tag == 'summary':
            self.summary = True
        elif self.active and tag in ('p', 'li', 'br'):
            self.answer.append(' ')

    def handle_data(self, data):
        if self.active:
            (self.question if self.summary else self.answer).append(data)

    def handle_endtag(self, tag):
        if tag == 'summary':
            self.summary = False
        elif self.active and tag == 'details':
            self.entities.append({
                '@type': 'Question',
                'name': ' '.join(''.join(self.question).split()),
                'acceptedAnswer': {
                    '@type': 'Answer',
                    'text': ' '.join(''.join(self.answer).split()),
                },
            })
            self.active = False


def get_seo_meta(route: str, title: str, en: bool, xu_version: str, body: str = '') -> dict[str, str]:
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
            desc = "Xu systems programming language: zero GC, inferred ownership, borrow checking, deterministic cleanup, built-in coroutines, and custom native/WebAssembly AOT backends."
        else:
            desc = "Xu 系统编程语言：零 GC、所有权推断、借用检查、确定性资源释放、内建协程及自研原生 / WebAssembly AOT 后端。"
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
            desc = "Xu FAQ: ownership and borrow checking, shared-state synchronization, native/FFI safety boundaries, code generation targets, SDK availability, and runtime verification."
        else:
            desc = "Xu 常见问题：所有权与借用检查、共享状态同步、原生 / FFI 安全边界、代码发射目标、SDK 可下载范围与运行实测。"
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
    elif bare_path == 'api/preview' or bare_path.startswith('api/preview/'):
        desc = (f'Unreleased Xu development API reference: {title}. Use the SDK version and source digest shown on the page.'
                if en else f'Xu 开发预览 API：{title}。尚未发布，请使用页面标明的 SDK 版本与源码摘要。')
    elif bare_path == 'api/xacp':
        if en:
            desc = f"Xu v{xu_version} SDK #xacp safety core: sessions, permissions, XUN checks, and frame limits. Native transport and UI integration remain unverified."
        else:
            desc = f"Xu v{xu_version} SDK 的 #xacp 安全核心：会话、权限、XUN 校验与帧上限。原生传输与 UI 集成仍待验。"
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

    faq_parser = FAQParser()
    faq_parser.feed(body)
    faq_entities = faq_parser.entities

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
        main = '<div class="page page-with-side">' + sidebar(route, en, xu_version, root) + f'<main class="{cls}">' + body + '</main></div>'
    other = ('/zh' if route == '/' else '/zh' + route) if en else (route[3:] or '/')
    if route == '/404':
        other = '/zh'
    meta = get_seo_meta(route, title, en, xu_version, body)
    template = Template((root / 'templates/page.html').read_text(encoding='utf-8'))
    playground_assets = '' if route in ('/', '/zh') else (
        '<link rel="preload" href="/xu-play.wasm" as="fetch" type="application/wasm" crossorigin>\n'
        '  <script src="/xu-play.js" defer></script>'
    )
    return template.substitute(
        lang='en' if en else 'zh-CN', title=escape(title), home=home,
        home_title='Xu Home' if en else 'Xu 官网首页',
        version_badge=('' if route in ('/', '/zh') else f'<span class="badge">v{escape(xu_version)}</span>'),
        footer_identity='XU' if route in ('/', '/zh') else 'XU v' + escape(xu_version),
        nav=''.join(nav), main=main,
        playground_assets=playground_assets,
        page_assets=('<link rel="stylesheet" href="/playground-design.css"><link rel="stylesheet" href="/widgets.css">'
                     if '/api/ui/widgets' in route else '') + ('<link rel="stylesheet" href="/playground.css">'
                     '<link rel="stylesheet" href="/playground-design.css">'
                     '<link rel="stylesheet" href="/widgets.css">'
                     '<script src="/xu-play-canvas.js" defer></script>'
                     '<script src="/xu-play-workspace.js" defer></script>'
                     '<script src="/xu-play-library.js" defer></script>'
                     '<script src="/widget-experience.js" defer></script>'
                     if route in ('/playground', '/zh/playground') else ''),
        other_lang=other, other_lang_code='zh-CN' if en else 'en',
        lang_title='中文' if en else 'English', lang_label='中文' if en else 'EN',
        theme_label='Switch theme' if en else '切换主题', ui_href=prefix + '/docs/ui',
        footer_text=('<a href="/LICENSE">MIT License</a> · Zero GC · Inferred Ownership · Custom AOT' if en
                     else '<a href="/LICENSE">MIT 开源协议</a> · 零 GC · 所有权推断 · 自研 AOT'),
        header_social=social_links(en, compact=True), footer_social=social_links(en),
        social_label='Official accounts' if en else '官方帐号',
        menu_label='Navigation menu' if en else '导航菜单',
        nav_label='Main navigation' if en else '主导航',
        **meta,
    )
