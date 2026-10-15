"""Shared navigation and page shell for the static official site."""

from html import escape
from pathlib import Path
from string import Template

DOC_GROUPS = [
    ('xi-bookmark', '起步', 'Start', [
        ('start', '起步', 'Get started'), ('install', '安装', 'Install'), ('hello', 'Hello', 'Hello'),
        ('modules', '模块与依赖', 'Modules and dependencies'), ('packages', '扩展包', 'External packages'),
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
    ('xi-shield-check', '密码与国密', 'Crypto', 'crypto/sm2 crypto/sm3 crypto/sm4 crypto/sm9 crypto/zuc crypto/gmtls crypto/tls crypto/rand crypto/x509/pkix crypto/sha256'.split()),
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


def sidebar(route: str, en: bool) -> str:
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
            (prefix + '/blog/xu-0-8-4', 'Xu 0.8.x · 0.8.4'),
            (prefix + '/blog/packages-0-1-1', 'packages 0.1.1'),
            (prefix + '/blog/xu-0-1-0', 'Xu 0.1.0'),
        ]))
    if not groups:
        return ''
    sections = []
    for icon, label, links in groups:
        sections.append(f'<p class="side-h"><i class="xi {icon}"></i> <span>{escape(label)}</span></p><ul>'
                        + ''.join(side_link(href, text, route) for href, text in links) + '</ul>')
    return '<aside class="side">' + ''.join(sections) + '</aside>'


def render(root: Path, title: str, route: str, body: str, xu_version: str) -> str:
    en = not (route == '/zh' or route.startswith('/zh/'))
    prefix = '' if en else '/zh'
    home = prefix or '/'
    nav = []
    for href, icon, zh, english in [
        ('', 'home', '首页', 'Home'), ('/playground', 'play', '演练场', 'Playground'),
        ('/download', 'download', '下载', 'Download'),
        ('/docs/start', 'book', '文档', 'Docs'), ('/api', 'api', 'API', 'API'),
        ('/blog', 'chat', '博客', 'Blog'),
        ('/benchmarks', 'benchmark', '横测', 'Benchmarks'),
        ('/docs/status', 'shield-check', '现状', 'Status'),
    ]:
        target = prefix + href or '/'
        section = '/docs' if href == '/docs/start' else href
        active = route == target or (bool(section) and route.startswith(prefix + section + '/'))
        # Status has its own tab even though it is a documentation page.
        if href == '/docs/start' and route == prefix + '/docs/status':
            active = False
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
        main = '<div class="page">' + sidebar(route, en) + f'<main class="{cls}">' + body + '</main></div>'
    other = ('/zh' if route == '/' else '/zh' + route) if en else (route[3:] or '/')
    if route == '/404':
        other = '/zh'
    template = Template((root / 'templates/page.html').read_text(encoding='utf-8'))
    return template.substitute(
        lang='en' if en else 'zh-CN', title=escape(title), home=home,
        xu_version=escape(xu_version), nav=''.join(nav), main=main,
        other_lang=other, other_lang_code='zh-CN' if en else 'en',
        lang_title='中文' if en else 'English', lang_label='中文' if en else 'EN',
        theme_label='Switch theme' if en else '切换主题', ui_href=prefix + '/docs/ui',
        footer_text='MIT License · Zero GC · Supersonic AOT' if en else 'MIT 开源协议 · 坚若磐石 · 零 GC 内存安全 · 超音速 AOT',
        header_social=social_links(en, compact=True), footer_social=social_links(en),
        social_label='Official accounts' if en else '官方帐号',
    )
