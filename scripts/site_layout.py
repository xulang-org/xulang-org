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


def side_link(href: str, label: str, route: str) -> str:
    active = ' class="on" aria-current="page"' if route == href else ''
    return f'<li><a{active} href="{href}">{escape(label)}</a></li>'


def sidebar(route: str, en: bool) -> str:
    prefix = '/en' if en else ''
    rest = route.removeprefix('/en') if en else route
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
    en = route == '/en' or route.startswith('/en/')
    prefix = '/en' if en else ''
    home = prefix or '/'
    nav = []
    for href, icon, zh, english in [
        ('', 'home', '首页', 'Home'), ('/download', 'download', '下载', 'Download'),
        ('/docs/start', 'book', '文档', 'Docs'), ('/api', 'api', 'API', 'API'),
        ('/blog', 'chat', '博客', 'Blog'), ('/docs/status', 'benchmark', '现状', 'Status'),
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
    if route in ('/', '/en'):
        main = '<main class="home">' + body + '</main>'
    else:
        cls = 'doc download' if route == prefix + '/download' else 'doc'
        main = '<div class="page">' + sidebar(route, en) + f'<main class="{cls}">' + body + '</main></div>'
    other = (route[3:] or '/') if en else ('/en' if route == '/' else '/en' + route)
    if route == '/404':
        other = '/en'
    template = Template((root / 'templates/page.html').read_text(encoding='utf-8'))
    return template.substitute(
        lang='en' if en else 'zh-CN', title=escape(title), home=home,
        xu_version=escape(xu_version), nav=''.join(nav), main=main,
        other_lang=other, lang_title='中文' if en else 'English', lang_label='中' if en else 'EN',
        theme_label='Switch theme' if en else '切换主题', ui_href=prefix + '/docs/ui',
        footer_text='MIT License · Zero GC · Supersonic AOT' if en else 'MIT 开源协议 · 坚若磐石 · 零 GC 内存安全 · 超音速 AOT',
    )
