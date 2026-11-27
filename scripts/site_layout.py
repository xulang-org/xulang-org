"""Shared navigation and page shell for the static official site."""
from __future__ import annotations

from html import escape, unescape
from html.parser import HTMLParser
from collections.abc import Iterable
import hashlib
import json
from pathlib import Path
import re
from string import Template

ALL_LANGS = ['en', 'zh', 'zh-tw', 'ja', 'ko', 'es', 'fr', 'de', 'ru', 'pt-br']

RESEARCH_LABELS = {
    'en': ('Research', 'Operating systems', 'AI development'),
    'zh': ('研发方向', '操作系统研发', 'AI 研发'),
    'zh-tw': ('研發方向', '作業系統研發', 'AI 研發'),
    'ja': ('開発分野', 'OS 開発', 'AI 開発'),
    'ko': ('개발 분야', '운영체제 개발', 'AI 개발'),
    'es': ('Investigación', 'Sistemas operativos', 'Desarrollo de IA'),
    'fr': ('Recherche', 'Systèmes d’exploitation', 'Développement IA'),
    'de': ('Forschung', 'Betriebssysteme', 'KI-Entwicklung'),
    'ru': ('Исследования', 'Разработка ОС', 'Разработка ИИ'),
    'pt-br': ('Pesquisa', 'Sistemas operacionais', 'Desenvolvimento de IA'),
}

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
        ('phone', '移动应用', 'Mobile apps'),
        ('vscode', 'VS Code', 'VS Code'), ('status', '限制与现状', 'Limitations'),
    ]),
]

DOC_GROUPS_LANGS = {
    'zh': {'起步': '起步', '教程': '教程', '语言': '语言', '工具': '工具'},
    'en': {'起步': 'Start', '教程': 'Tutorial', '语言': 'Language', '工具': 'Tools'},
    'zh-tw': {'起步': '起步', '教程': '教程', '语言': '語言', '工具': '工具'},
    'ja': {'起步': 'スタート', '教程': 'チュートリアル', '语言': '言語仕様', '工具': 'ツール'},
    'ko': {'起步': '시작하기', '教程': '튜토리얼', '语言': '언어 사양', '工具': '도구'},
    'es': {'起步': 'Inicio', '教程': 'Tutorial', '语言': 'Lenguaje', '工具': 'Herramientas'},
    'fr': {'起步': 'Débuter', '教程': 'Tutoriel', '语言': 'Langage', '工具': 'Outils'},
    'de': {'起步': 'Start', '教程': 'Tutorial', '语言': 'Sprache', '工具': 'Werkzeuge'},
    'ru': {'起步': 'Начало работы', '教程': 'Учебник', '语言': 'Язык', '工具': 'Инструменты'},
    'pt-br': {'起步': 'Início', '教程': 'Tutorial', '语言': 'Linguagem', '工具': 'Ferramentas'},
}

DOC_LABELS_LANGS = {
    'zh-tw': {
        'start': '快速起步', 'install': '編譯器安裝', 'faq': '常見問題 (FAQ)',
        'modules': '模組與依賴', 'packages': '擴充套件生態', 'native': '原生模組與 .xulib',
        'lang/goals': '設計目標', 'lang/syntax': '語法定稿', 'lang/lexical': '詞法結構',
        'lang/structure': '程式結構', 'lang/types': '型別系統', 'lang/functions': '函式與運算式',
        'lang/memory': '記憶體模型', 'lang/concurrency': '並行規格', 'lang/ebnf': 'EBNF',
        'lang/stdlib': '標準庫邊界', 'lang/toolchain': '工具鏈', 'lang/status': '規範快照',
        'cli': 'CLI 命令行工具', 'ui': 'UI / WebView', 'phone': '行動應用開發',
        'vscode': 'VS Code', 'status': '限制與現狀',
    },
    'ja': {
        'start': 'クイックスタート', 'install': 'インストール', 'faq': 'よくある質問 (FAQ)',
        'modules': 'モジュールと依存関係', 'packages': '外部パッケージ', 'native': 'ネイティブモジュールと .xulib',
        'lang/goals': '設計目標', 'lang/syntax': '構文仕様確定', 'lang/lexical': '字句構造',
        'lang/structure': 'プログラム構造', 'lang/types': '型システム', 'lang/functions': '関数と式',
        'lang/memory': 'メモリモデル', 'lang/concurrency': '並行処理', 'lang/ebnf': 'EBNF',
        'lang/stdlib': '標準ライブラリ境界', 'lang/toolchain': 'ツールチェーン', 'lang/status': '仕様スナップショット',
        'cli': 'CLI コマンドライン', 'ui': 'UI / WebView', 'phone': 'モバイルアプリ',
        'vscode': 'VS Code', 'status': 'プロジェクト状況と制限',
    },
    'ko': {
        'start': '시작하기', 'install': '설치', 'faq': '자주 묻는 질문 (FAQ)',
        'modules': '모듈 및 종속성', 'packages': '외부 패키지', 'native': '네이티브 모듈 및 .xulib',
        'lang/goals': '설계 목표', 'lang/syntax': '구문 사양 확정', 'lang/lexical': '어휘 구조',
        'lang/structure': '프로그램 구조', 'lang/types': '타입 시스템', 'lang/functions': '함수 및 표현식',
        'lang/memory': '메모리 모델', 'lang/concurrency': '동시성', 'lang/ebnf': 'EBNF',
        'lang/stdlib': '표준 라이브러리 경계', 'lang/toolchain': '툴체인', 'lang/status': '사양 스냅샷',
        'cli': 'CLI 명령줄 도구', 'ui': 'UI / WebView', 'phone': '모바일 앱',
        'vscode': 'VS Code', 'status': '프로젝트 현황 및 제한',
    },
    'es': {
        'start': 'Primeros pasos', 'install': 'Instalación', 'faq': 'Preguntas frecuentes (FAQ)',
        'modules': 'Módulos y dependencias', 'packages': 'Paquetes externos', 'native': 'Módulos nativos y .xulib',
        'lang/goals': 'Objetivos de diseño', 'lang/syntax': 'Sintaxis', 'lang/lexical': 'Estructura léxica',
        'lang/structure': 'Estructura del programa', 'lang/types': 'Tipos', 'lang/functions': 'Funciones y expresiones',
        'lang/memory': 'Modelo de memoria', 'lang/concurrency': 'Concurrencia', 'lang/ebnf': 'EBNF',
        'lang/stdlib': 'Límites de la biblioteca', 'lang/toolchain': 'Herramientas', 'lang/status': 'Instantánea de especificación',
        'cli': 'Línea de comandos CLI', 'ui': 'UI / WebView', 'phone': 'Aplicaciones móviles',
        'vscode': 'VS Code', 'status': 'Estado y limitaciones',
    },
    'fr': {
        'start': 'Premiers pas', 'install': 'Installation', 'faq': 'Foire aux questions (FAQ)',
        'modules': 'Modules et dépendances', 'packages': 'Paquets externes', 'native': 'Modules natifs et .xulib',
        'lang/goals': 'Objectifs de conception', 'lang/syntax': 'Syntaxe', 'lang/lexical': 'Structure lexicale',
        'lang/structure': 'Structure du programme', 'lang/types': 'Types', 'lang/functions': 'Fonctions et expressions',
        'lang/memory': 'Modèle de mémoire', 'lang/concurrency': 'Concurrence', 'lang/ebnf': 'EBNF',
        'lang/stdlib': 'Périmètre bibliothèque standard', 'lang/toolchain': 'Chaîne d\'outils', 'lang/status': 'Instantané de spécification',
        'cli': 'Ligne de commande CLI', 'ui': 'UI / WebView', 'phone': 'Applications mobiles',
        'vscode': 'VS Code', 'status': 'État et limites',
    },
    'de': {
        'start': 'Erste Schritte', 'install': 'Installation', 'faq': 'Häufig gestellte Fragen (FAQ)',
        'modules': 'Module & Abhängigkeiten', 'packages': 'Externe Pakete', 'native': 'Native Module & .xulib',
        'lang/goals': 'Entwurfsziele', 'lang/syntax': 'Syntax', 'lang/lexical': 'Lexikalische Struktur',
        'lang/structure': 'Programmstruktur', 'lang/types': 'Typen', 'lang/functions': 'Funktionen & Ausdrücke',
        'lang/memory': 'Speichermodell', 'lang/concurrency': 'Nebenläufigkeit', 'lang/ebnf': 'EBNF',
        'lang/stdlib': 'Grenzen der Standardbibliothek', 'lang/toolchain': 'Toolchain', 'lang/status': 'Spezifikations-Snapshot',
        'cli': 'CLI-Befehlszeile', 'ui': 'UI / WebView', 'phone': 'Mobile Anwendungen',
        'vscode': 'VS Code', 'status': 'Status & Einschränkungen',
    },
    'ru': {
        'start': 'Начало работы', 'install': 'Установка', 'faq': 'Часто задаваемые вопросы (FAQ)',
        'modules': 'Модули и зависимости', 'packages': 'Внешние пакеты', 'native': 'Нативные модули и .xulib',
        'lang/goals': 'Цели проектирования', 'lang/syntax': 'Синтаксис', 'lang/lexical': 'Лексическая структура',
        'lang/structure': 'Структура программы', 'lang/types': 'Система типов', 'lang/functions': 'Функции и выражения',
        'lang/memory': 'Модель памяти', 'lang/concurrency': 'Конкурентность', 'lang/ebnf': 'EBNF',
        'lang/stdlib': 'Границы стандартной библиотеки', 'lang/toolchain': 'Инструментарий', 'lang/status': 'Снимок спецификации',
        'cli': 'Командная строка CLI', 'ui': 'UI / WebView', 'phone': 'Мобильные приложения',
        'vscode': 'VS Code', 'status': 'Статус и ограничения',
    },
    'pt-br': {
        'start': 'Primeiros passos', 'install': 'Instalação', 'faq': 'Perguntas frequentes (FAQ)',
        'modules': 'Módulos e dependências', 'packages': 'Pacotes externos', 'native': 'Módulos nativos e .xulib',
        'lang/goals': 'Objetivos de design', 'lang/syntax': 'Sintaxe', 'lang/lexical': 'Estrutura léxica',
        'lang/structure': 'Estrutura do programa', 'lang/types': 'Tipos', 'lang/functions': 'Funções e expressões',
        'lang/memory': 'Modelo de memória', 'lang/concurrency': 'Concorrência', 'lang/ebnf': 'EBNF',
        'lang/stdlib': 'Limites da biblioteca padrão', 'lang/toolchain': 'Cadeia de ferramentas', 'lang/status': 'Instantâneo de especificação',
        'cli': 'Linha de comando CLI', 'ui': 'UI / WebView', 'phone': 'Aplicativos móveis',
        'vscode': 'VS Code', 'status': 'Status e limitações',
    },
}

_CURATED_API_GROUPS = [
    ('xi-api', 'API', 'API', ['']),
    ('xi-cpu', '核心', 'Core', 'errors fmt flag cmp context sync time runtime maps slices sort testing testing/fstest xacp'.split()),
    ('xi-file', '文本', 'Text', 'strings bytes strconv unicode regexp html'.split()),
    ('xi-terminal', 'IO / OS', 'IO / OS', 'io io/fs os os/exec os/signal os/user bufio path log'.split()),
    ('xi-globe', '网络', 'Net', 'net net/http net/http/cookiejar net/http/httptest net/netip net/url'.split()),
    ('xi-binary', '编码', 'Encoding', 'encoding/json encoding/hex encoding/base64'.split()),
    ('xi-shield-check', '密码与国密', 'Crypto', 'crypto/aes crypto/cipher crypto/sm2 crypto/sm3 crypto/sm4 crypto/sm9 crypto/zuc crypto/gmtls crypto/tls crypto/rand crypto/rsa crypto/sha256 crypto/sha512 crypto/sha1 crypto/sha3 crypto/md5 crypto/hmac crypto/x509 crypto/x509/pkix crypto/ecdsa crypto/ed25519 crypto/des crypto/rc4 crypto/subtle crypto/password crypto/jwt'.split()),
    ('xi-package', '压缩 / 图像 / 数学 / 张量', 'Compress / image / math / tensor', 'compress/gzip image math tensor'.split()),
    ('xi-database', '数据库', 'Database', 'database/sql database/sql/driver'.split()),
    ('xi-package', '图形与窗口', 'Graphics & Window', 'gpu gpu/layout window window/events'.split()),
    ('xi-package', '扩展包', 'Extensions', ['packages/' + name for name in
        'a2a agent anthropic cassandra chroma clickhouse cohere consul dns elasticsearch etcd eval gateway gemini grpc guardrails influxdb kafka mcp meilisearch memcached metal milvus mongodb mqtt mysql nacos nats neo4j openai postgres prometheus prompt qdrant rabbitmq rag redis s3 smtp sqlite synth transport websocket zookeeper'.split()]),
    ('xi-xuui', 'UI', 'UI', 'ui ui/draw ui/layout ui/chart ui/phone ui/widgets ui/webview'.split()),
]


def api_pages(root: Path | None = None) -> set[str]:
    api_root = (root or Path(__file__).resolve().parents[1]) / 'content/en/api'
    return {
        page.relative_to(api_root).with_suffix('').as_posix()
        for page in api_root.rglob('*.html')
        if page.name != 'index.html' and 'preview' not in page.relative_to(api_root).parts
    }


def group_api_packages(packages: Iterable[str]) -> list[tuple[str, str, str, list[str]]]:
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
    inventories = {}
    for lang in ('en', 'zh'):
        inventory = PackageInventory((root / f'content/{lang}/api/index.html').read_text(encoding='utf-8')).packages
        for package in inventory:
            if not (root / f'content/{lang}/api/{package}.html').is_file():
                raise ValueError(f'API inventory points to a missing package: {lang}/{package}')
        inventories[lang] = inventory
    if not inventories['en'] or inventories['en'] != inventories['zh']:
        raise ValueError('API package inventories must be nonempty and match in EN/ZH')
    external = sum(p.startswith('packages/') for p in inventories['en'])
    releases = release_entries(root)
    values = {}
    
    release_label = {
        'en': 'release', 'zh': '正式版', 'zh-tw': '正式版',
        'ja': 'リリース', 'ko': '정식 릴리스', 'es': 'versión',
        'fr': 'version', 'de': 'Release', 'ru': 'релиз', 'pt-br': 'lançamento'
    }

    for l in ALL_LANGS:
        lbl = release_label.get(l, 'release')
        notes_list = []
        blog_list = []
        for item in releases:
            v_id = item["version"].replace(".", "-")
            note_content = item['notes'].get(l, item['notes']['en'])
            blog_content = item['blog_entry'].get(l, item['blog_entry']['en'])
            notes_list.append(f'<h2 id="v{v_id}">{item["version"]} {lbl}</h2>\n{note_content}')
            blog_list.append(f'<li>{blog_content}</li>')

        values[l] = {
            'api_standard_count': str(len(inventories['en']) - external),
            'api_external_count': str(external),
            'release_notes': '\n'.join(notes_list),
            'release_blog_entries': '\n'.join(blog_list),
        }
    return values


def release_entries(root: Path) -> list[dict]:
    return json.loads((root / 'templates/releases.json').read_text(encoding='utf-8'))

HEADER_SOCIAL_PROFILES = [
    ('GitHub', 'xulang-org/xu', 'https://github.com/xulang-org/xu', 'github'),
    ('X', 'xulang_org', 'https://x.com/xulang_org', 'x'),
]
FOOTER_SOCIAL_PROFILES = [
    ('GitHub', 'xulang-org', 'https://github.com/xulang-org/xu', 'github'),
    ('X', 'xulang_org', 'https://x.com/xulang_org', 'x'),
]
SOCIAL_PROFILES = FOOTER_SOCIAL_PROFILES
SOCIAL_ICONS = {
    'github': '<path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38l-.01-1.49c-2.23.48-2.7-1.08-2.7-1.08-.36-.92-.89-1.17-.89-1.17-.73-.5.06-.49.06-.49.8.06 1.22.82 1.22.82.71 1.22 1.87.87 2.33.67.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.96 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.65 7.65 0 0 1 4 0c1.53-1.03 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.28.82 2.15 0 3.08-1.87 3.75-3.65 3.95.29.25.54.74.54 1.48l-.01 2.34c0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z"/>',
    'x': '<path d="M12.6 1h2.3L9.9 6.7 15.8 15h-4.6L7.6 10 3.2 15H.9l5.6-6.4L.8 1h4.7l3.3 4.6L12.6 1ZM11.8 13.5h1.3L4.8 2.4H3.4l8.4 11.1Z"/>',
}


def social_links(en: bool | str, compact: bool = False, profiles: list[tuple] | None = None) -> str:
    links = []
    lang = en if isinstance(en, str) else ('en' if en else 'zh')
    new_tab = {
        'en': 'opens in a new tab', 'zh': '在新标签页打开', 'zh-tw': '在新分頁開啟',
        'ja': '新しいタブで開く', 'ko': '새 탭에서 열기', 'es': 'se abre en una nueva pestaña',
        'fr': 's\'ouvre dans un nouvel onglet', 'de': 'öffnet in neuem Tab',
        'ru': 'открывается в новой вкладке', 'pt-br': 'abre em uma nova aba'
    }.get(lang, 'opens in a new tab')
    selected = profiles if profiles is not None else (HEADER_SOCIAL_PROFILES if compact else FOOTER_SOCIAL_PROFILES)
    for platform, handle, href, icon in selected:
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


def detect_lang(route: str, en: bool | str | None = None) -> str:
    for l in ('zh-tw', 'pt-br', 'ja', 'ko', 'es', 'fr', 'de', 'ru', 'zh'):
        if route == f'/{l}' or route.startswith(f'/{l}/'):
            return l
    if isinstance(en, str) and en in ALL_LANGS:
        return en
    if isinstance(en, bool) and not en:
        return 'zh'
    return 'en'


def sidebar(route: str, en: bool | str | None = None, xu_version: str = '', root: Path | None = None) -> str:
    lang = detect_lang(route, en)
    prefix = f'/{lang}' if lang != 'en' else ''
    rest = route.removeprefix(prefix) if prefix else route
    groups = []
    api_tree = None

    group_labels = DOC_GROUPS_LANGS.get(lang, DOC_GROUPS_LANGS['en'])
    doc_labels = DOC_LABELS_LANGS.get(lang, {})

    if rest.startswith('/docs/'):
        research_label, os_label, ai_label = RESEARCH_LABELS[lang]
        research_prefix = '/zh' if lang in ('zh', 'zh-tw') else ''
        groups.append(('xi-flask', research_label, [
            (research_prefix + '/docs/os', os_label),
            (research_prefix + '/docs/ai', ai_label),
        ]))
        for icon, zh, english, links in DOC_GROUPS:
            group_title = group_labels.get(zh, english if lang == 'en' else zh)
            group_links = []
            for href, zh_label, english_label in links:
                if lang in ('zh', 'zh-tw'):
                    fallback = zh_label if lang == 'zh' else doc_labels.get(href, zh_label)
                elif lang == 'en':
                    fallback = english_label
                else:
                    fallback = english_label
                link_title = doc_labels.get(href, fallback)
                group_links.append((prefix + '/docs/' + href, link_title))
            groups.append((icon, group_title, group_links))
    elif rest == '/api/preview' or rest.startswith('/api/preview/'):
        preview_title = 'Development preview' if lang == 'en' else ('开发预览' if lang == 'zh' else 'Preview API')
        index_label = 'Index' if lang == 'en' else ('索引' if lang == 'zh' else 'Index')
        sdk_label = 'Released SDK API' if lang == 'en' else ('正式 SDK API' if lang == 'zh' else 'SDK API')
        groups.append(('xi-xuui', preview_title, [
            (prefix + '/api/preview', index_label),
            *[(prefix + '/api/preview/' + package, '#' + package)
              for package in ('ui', 'ui/draw', 'ui/layout', 'ui/chart', 'ui/widgets', 'ui/webview')],
            (prefix + '/api', sdk_label),
        ]))
    elif rest == '/api' or rest.startswith('/api/'):
        api_tree = api_sections(api_pages(root), root)
    elif rest == '/blog' or rest.startswith('/blog/'):
        blog_index = 'Index' if lang == 'en' else ('博客索引' if lang == 'zh' else 'Blog Index')
        lsp_label = 'Xu LSP & vscode-xu' if lang != 'zh' else 'Xu LSP 与 vscode-xu'
        groups.append(('xi-chat', 'Blog' if lang != 'zh' else '博客', [
            (prefix + '/blog', blog_index),
            *[(prefix + '/blog/xu-' + item['version'].replace('.', '-'), 'Xu ' + item['version'])
              for item in release_entries(root or Path(__file__).resolve().parents[1])],
            (prefix + '/blog/xu-lsp-and-vscode', lsp_label),
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

    matched_idx = -1
    for idx, (_, _, links) in enumerate(groups):
        if any(href == route for href, _ in links):
            matched_idx = idx
            break

    sections = api_sidebar_sections(route, lang == 'en', api_tree, root) if api_tree is not None else []
    for idx, (icon, label, links) in enumerate(groups):
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

    toggle_all_title = {
        'en': 'Toggle all sections', 'zh': '折叠/展开全部菜单', 'zh-tw': '折疊/展開全部選單',
        'ja': 'すべてのセクションを開閉', 'ko': '모든 섹션 접기/펼치기', 'es': 'Alternar todas las secciones',
        'fr': 'Basculer toutes les sections', 'de': 'Alle Abschnitte umschalten',
        'ru': 'Свернуть/развернуть все', 'pt-br': 'Alternar todas as seções'
    }.get(lang, 'Toggle all sections')
    scroll_top_title = {
        'en': 'Back to top of menu', 'zh': '回到目录顶部', 'zh-tw': '回到目錄頂部',
        'ja': 'メニューの一番上へ', 'ko': '메뉴 상단으로', 'es': 'Volver al principio del menú',
        'fr': 'Haut du menu', 'de': 'Zum Menüanfang',
        'ru': 'Вверх меню', 'pt-br': 'Voltar ao topo do menu'
    }.get(lang, 'Back to top of menu')
    sections_header = {
        'en': 'Sections', 'zh': '目录导航', 'zh-tw': '目錄導航',
        'ja': 'セクション', 'ko': '목차 탐색', 'es': 'Secciones',
        'fr': 'Sections', 'de': 'Abschnitte',
        'ru': 'Разделы', 'pt-br': 'Seções'
    }.get(lang, 'Sections')

    side_header = (
        f'<div class="side-header">'
        f'  <span class="side-header-title">{sections_header}</span>'
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

    contents = side_header + f'<div class="side-content">{"".join(sections)}</div>' + side_footer
    if rest == '/api' or rest.startswith('/api/'):
        browse_label = 'Browse API directory' if lang == 'en' else ('浏览 API 目录' if lang == 'zh' else 'Browse API')
        contents = ('<details class="api-directory" id="api-directory" open>'
                    f'<summary>{browse_label}<i class="xi xi-chevron-down" aria-hidden="true"></i></summary>'
                    '<div class="api-directory-body">' + contents + '</div></details>')
    return '<aside class="side">' + contents + '</aside>'


def api_tools(route: str, en: bool, root: Path) -> str:
    prefix = '' if en else '/zh'
    relative = route.removeprefix(prefix + '/api').strip('/')
    crumbs = [f'<a href="{prefix}/api">API</a>']
    pieces = relative.split('/') if relative else []
    for depth in range(1, len(pieces)):
        parent = '/'.join(pieces[:depth])
        label = escape(pieces[depth - 1])
        if parent != 'index' and (root / 'content' / ('en' if en else 'zh') / 'api' / (parent + '.html')).is_file():
            crumbs.append(f'<a href="{prefix}/api/{escape(parent, quote=True)}">{label}</a>')
        else:
            crumbs.append(f'<span>{label}</span>')
    if relative:
        crumbs.append(f'<span aria-current="page">{escape(pieces[-1])}</span>')
    return ('<div class="api-toolbar">'
            f'<nav class="api-breadcrumbs" aria-label="{"API location" if en else "API 位置"}">'
            + '<span aria-hidden="true">/</span>'.join(crumbs) + '</nav>'
            '<div class="api-toolbar-actions">'
            f'<button type="button" data-api-search hidden><i class="xi xi-search" aria-hidden="true"></i>'
            f'<span>{"Search API" if en else "搜索 API"}</span><kbd>/</kbd></button>'
            f'<button type="button" data-api-copy hidden>{"Copy link" if en else "复制链接"}</button>'
            '</div><span class="api-feedback" role="status" data-api-feedback></span></div>')


def api_index_presentation(body: str, en: bool) -> str:
    if 'class="api-section-nav"' not in body:
        return body
    descriptions = {
        '核心': ('错误处理、集合、时间与并发', 'Errors, collections, time and concurrency'),
        '文本': ('查找、拆分、转换与匹配文本', 'Find, split, convert and match text'),
        'IO / OS': ('读写文件、路径与系统进程', 'Files, paths and system processes'),
        '网络': ('HTTP 服务、连接与网络协议', 'HTTP services, connections and protocols'),
        '编码': ('JSON、二进制与数据格式转换', 'JSON, binary and data formats'),
        '密码与国密': ('加密、签名、摘要与安全连接', 'Encryption, signatures, hashes and TLS'),
        '压缩 / 图像 / 数学': ('压缩数据、处理图像与数值计算', 'Compression, images and numeric operations'),
        '数据库': ('数据库连接、查询与驱动接口', 'Database connections, queries and drivers'),
        '图形与窗口': ('GPU 渲染、窗口与输入事件', 'GPU rendering, windows and input events'),
        '其他': ('容器、嵌入式与更多工具', 'Containers, embedded systems and more'),
        '包': ('构建界面、布局、图表与 WebView', 'Interfaces, layouts, charts and WebView'),
        '集成': ('连接数据库、消息队列与外部服务', 'Connect databases, messaging and services'),
    }
    english = {zh: english for _icon, zh, english, _members in _CURATED_API_GROUPS}
    english.update({'其他': 'Other', '包': 'Packages', '集成': 'Integrations'})
    topic_descriptions = {english.get(key, key) if en else key: values[en] for key, values in descriptions.items()}

    def topic(match):
        label, count, packages = match.groups()
        text = topic_descriptions.get(unescape(label), '')
        description = f'<span class="api-topic-description">{escape(text)}</span>' if text else ''
        return ('<details class="api-topic" open><summary><span class="api-topic-title">'
                + label + f'<span class="api-topic-count">{count}</span></span>' + description
                + '</summary>' + packages + '</details>')

    body = re.sub(r'<details class="api-topic"[^>]*><summary>(.*?) <span class="api-topic-count">(\d+)</span></summary>\s*(<ul class="api-package-list">.*?</ul>)</details>',
                  topic, body, flags=re.DOTALL)
    quick = []
    for path, zh, english in [
        ('core/arch', '内核与硬件接口', 'Kernel and hardware APIs'),
        ('math', '数值计算', 'Numerical computing'),
        ('net/http', '构建 HTTP 服务', 'Build HTTP services'),
        ('ui/widgets', '构建用户界面', 'Build interfaces'),
    ]:
        link = re.search(r'href="([^"#]*/api/(?:preview/)?' + re.escape(path) + r')"', body)
        if link:
            quick.append(f'<a href="{link[1]}"><span>{english if en else zh}</span><code>#{path}</code>'
                         '<i class="xi xi-arrow-right" aria-hidden="true"></i></a>')
    quick_html = ('<nav class="api-quick-links" aria-label="' + ('Common tasks' if en else '常用任务')
                  + '">' + ''.join(quick) + '</nav>') if quick else ''
    controls = ('<div class="api-catalog-search" data-api-catalog-search hidden>'
                '<label for="api-catalog-query">' + ('Find a package' if en else '查找包') + '</label>'
                '<div class="api-catalog-input"><i class="xi xi-search" aria-hidden="true"></i>'
                '<input id="api-catalog-query" type="search" autocomplete="off" spellcheck="false" placeholder="'
                + ('Search names or topics, e.g. strings, HTTP, database' if en else '输入包名或用途，例如 strings、HTTP、数据库')
                + '"><button type="button" data-api-catalog-clear>' + ('Clear' if en else '清空') + '</button></div>'
                '<p data-api-catalog-status role="status" aria-live="polite"></p></div>')
    intro = ('Find the right package. Jump straight to its API.' if en else '按用途找到包，直达你需要的 API。')
    body = re.sub(r'(<h1>.*?</h1>)', '<p class="api-eyebrow">XU / API REFERENCE</p>\\1'
                  + f'<p class="api-intro">{intro}</p>', body, count=1)
    body = body.replace('<nav class="api-section-nav"', quick_html + controls + '<nav id="api-catalog" class="api-section-nav"', 1)
    body = body.replace('aria-label="API 分类">', 'aria-label="API 分类"><a href="#api-catalog" data-api-all>全部包</a>', 1) if not en else body.replace(
        'aria-label="API sections">', 'aria-label="API sections"><a href="#api-catalog" data-api-all>All packages</a>', 1)
    return '<div class="api-catalog">' + body + '<p class="api-empty" data-api-catalog-empty hidden>' + (
        'No matching packages. Try another keyword or select All packages.' if en else '没有找到匹配的包。试试其他关键词，或切换到「全部包」。') + '</p></div>'


class FAQParser(HTMLParser):
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


OG_LOCALES = {
    'en': 'en_US', 'zh': 'zh_CN', 'zh-tw': 'zh_TW',
    'ja': 'ja_JP', 'ko': 'ko_KR', 'es': 'es_ES',
    'fr': 'fr_FR', 'de': 'de_DE', 'ru': 'ru_RU', 'pt-br': 'pt_BR'
}

IN_LANGUAGES = {
    'en': 'en', 'zh': 'zh-CN', 'zh-tw': 'zh-TW',
    'ja': 'ja', 'ko': 'ko', 'es': 'es',
    'fr': 'fr', 'de': 'de', 'ru': 'ru', 'pt-br': 'pt-BR'
}


def get_seo_meta(route: str, title: str, en: bool | str, xu_version: str, body: str = '') -> dict[str, str]:
    origin = "https://xulang.org"
    lang = detect_lang(route, en)

    # Bare route extraction
    bare_route = route
    for l in ('zh-tw', 'pt-br', 'ja', 'ko', 'es', 'fr', 'de', 'ru', 'zh'):
        if bare_route == f'/{l}' or bare_route.startswith(f'/{l}/'):
            bare_route = bare_route[len(l) + 1:] or '/'
            break

    url_en = f"{origin}{bare_route.rstrip('/')}/" if bare_route != '/' else f"{origin}/"
    urls = {'url_en': url_en}
    for l in ('zh', 'zh-tw', 'ja', 'ko', 'es', 'fr', 'de', 'ru', 'pt-br'):
        key = f"url_{l.replace('-', '_')}"
        urls[key] = f"{origin}/{l}{bare_route.rstrip('/')}/" if bare_route != '/' else f"{origin}/{l}/"

    if route == '/404':
        canonical_url = f"{origin}/404.html"
    elif lang == 'en':
        canonical_url = url_en
    else:
        canonical_url = urls[f"url_{lang.replace('-', '_')}"]

    bare_path = bare_route.strip('/')

    if not bare_path:
        desc = {
            'en': 'Xu is a systems language for operating system and AI development. Build freestanding kernels and explore local CPU inference with native AOT and inferred ownership.',
            'zh': 'Xu 是面向操作系统与 AI 研发的系统编程语言。使用原生 AOT 与所有权推断构建裸机内核，探索本地 CPU 推理。',
            'zh-tw': 'Xu 是面向作業系統與 AI 研發的系統程式語言。使用原生 AOT 與所有權推斷建置裸機核心，探索本機 CPU 推論。',
            'ja': 'Xu は OS と AI 開発のためのシステム言語です。ネイティブ AOT と所有権推論でベアメタルカーネルを構築し、ローカル CPU 推論を試せます。',
            'ko': 'Xu는 운영체제와 AI 개발을 위한 시스템 언어입니다. 네이티브 AOT와 소유권 추론으로 베어메탈 커널을 빌드하고 로컬 CPU 추론을 살펴보세요.',
            'es': 'Xu es un lenguaje de sistemas para desarrollar sistemas operativos e IA. Explora núcleos autónomos e inferencia local en CPU con AOT nativo y propiedad inferida.',
            'fr': 'Xu est un langage système pour les systèmes d’exploitation et l’IA. Explorez les noyaux autonomes et l’inférence CPU locale avec AOT natif et inférence de propriété.',
            'de': 'Xu ist eine Systemsprache für Betriebssysteme und KI. Erkunde freistehende Kernel und lokale CPU-Inferenz mit nativem AOT und Eigentumsinferenz.',
            'ru': 'Xu — системный язык для разработки ОС и ИИ. Собирайте автономные ядра и изучайте локальный инференс на CPU с нативной AOT-компиляцией и выводом владения.',
            'pt-br': 'Xu é uma linguagem de sistemas para desenvolvimento de sistemas operacionais e IA. Explore núcleos independentes e inferência local em CPU com AOT nativo e propriedade inferida.',
        }[lang]
    elif bare_path == 'benchmarks':
        desc = (f"{title} — Cross-language runtime, CPU time, peak memory and binary-size measurements across Linux, macOS and Windows."
                if lang == 'en' else f"{title} — Xu 跨语言运行耗时、CPU 时间、峰值内存与二进制体积实测。")
    elif bare_path == 'playground':
        desc = (f"Interactive in-browser WebAssembly playground for Xu v{xu_version}. Compile, borrow-check, and execute Xu code client-side."
                if lang == 'en' else f"Xu 编程语言 (v{xu_version}) 在线 WebAssembly 演练场。")
    elif bare_path == 'download':
        desc = (f"Download official Xu v{xu_version} compiler SDK and toolchain for macOS, Linux, and Windows."
                if lang == 'en' else f"下载官方 Xu (v{xu_version}) 编译器 SDK 与工具链。")
    elif bare_path == 'docs/start':
        desc = (f"Get started with Xu v{xu_version}: language introduction, environment setup, writing and compiling your first zero-GC program."
                if lang == 'en' else f"Xu (v{xu_version}) 快速起步：语言介绍、环境配置与第一个零 GC 程序。")
    elif bare_path == 'docs/os':
        desc = ('Build a freestanding Xu kernel for x64, ARM64, or RISC-V 64. Explore ELF output, memory-mapped I/O, and core hardware APIs.'
                if lang == 'en' else '使用 Xu 构建 x64、ARM64 或 RISC-V 64 裸机内核，了解 ELF 产物、内存映射 I/O 与核心硬件 API。')
    elif bare_path == 'docs/ai':
        desc = ('Run local models with the Xu development CPU engine. Explore GGUF and Safetensors support, paged KV cache, and compiler tensor optimizations.'
                if lang == 'en' else '用 Xu 开发版 CPU 引擎运行本地模型，了解 GGUF、Safetensors、分页 KV 缓存与编译器张量优化。')
    elif bare_path.startswith('docs/faq'):
        desc = ("Xu FAQ: bare-metal OS & kernel development, ownership, borrow checking, shared-state synchronization, native/FFI safety boundaries, and toolchain features."
                if lang == 'en' else "Xu 常见问题：操作系统与裸机开发、所有权与借用检查、共享状态同步、原生 / FFI 安全边界与工具链特性。")
    elif bare_path.startswith('docs/tutorial'):
        desc = (f"{title} — Hands-on step-by-step tutorial for the Xu programming language, covering syntax, ownership, concurrency, and real-world networking."
                if lang == 'en' else f"{title} — Xu 编程语言实战系列教程，系统讲解语法结构、所有权机制、高并发通道与系统级网络编程。")
    elif bare_path.startswith('docs/lang'):
        desc = (f"{title} — Official language specification, memory model, concurrency architecture, and formal grammar for Xu."
                if lang == 'en' else f"{title} — Xu 编程语言官方规范：语法定义、内存模型与所有权语义、并发调度架构与 EBNF 文法。")
    elif bare_path == 'api/preview' or bare_path.startswith('api/preview/'):
        desc = (f'Unreleased Xu development API reference: {title}. Use the SDK version and source digest shown on the page.'
                if lang == 'en' else f'Xu 开发预览 API：{title}。尚未发布，请使用页面标明的 SDK 版本与源码摘要。')
    elif bare_path == 'api/xacp':
        if lang == 'en':
            desc = f"Xu v{xu_version} SDK #xacp safety core: sessions, permissions, XUN checks, and frame limits. Native transport and UI integration remain unverified."
        elif lang in ('zh', 'zh-tw'):
            desc = f"Xu v{xu_version} SDK 的 #xacp 安全核心：会话、权限、XUN 校验与帧上限。原生传输与 UI 集成仍待验。"
        else:
            desc = f"Xu v{xu_version} SDK #xacp safety core: sessions, permissions, XUN checks, and frame limits."
    elif bare_path.startswith('api'):
        desc = (f"Official API reference for {title} in the Xu v{xu_version} standard library and extended package ecosystem."
                if lang == 'en' else f"Xu 编程语言 (v{xu_version}) 标准库与扩展包官方 API 参考文档：{title}。")
    elif bare_path.startswith('blog'):
        desc = (f"{title} — Engineering blog post and release updates from the Xu programming language team."
                if lang == 'en' else f"{title} — Xu 编程语言团队官方技术博客与版本发布动态。")
    else:
        desc = f"{title} — Xu Programming Language documentation, guides, and tools."

    keywords = (
        "Xu, xulang, systems programming, operating system development, bare-metal kernels, AI inference, AOT compiler, zero GC, WebAssembly"
        if lang not in ('zh', 'zh-tw') else
        "Xu, Xu語言, 系統編程, 作業系統研發, 裸機內核, AI 推理, AOT 編譯器, 零 GC, WebAssembly"
    )

    og_type = "website" if bare_path in ('', 'playground', 'benchmarks', 'download', '404') else "article"
    og_locale = OG_LOCALES.get(lang, 'en_US')

    faq_parser = FAQParser()
    faq_parser.feed(body)
    faq_entities = faq_parser.entities

    def make_breadcrumbs_schema(origin_url: str, crumbs: list[tuple[str, str]]) -> dict:
        return {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": i + 1,
                    "name": name,
                    "item": f"{origin_url}{path.rstrip('/')}/" if path != '/' else f"{origin_url}/"
                }
                for i, (name, path) in enumerate(crumbs)
            ]
        }

    in_lang_code = IN_LANGUAGES.get(lang, 'en')

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
                    "inLanguage": ["en", "zh-CN", "zh-TW", "ja", "ko", "es", "fr", "de", "ru", "pt-BR"],
                    "potentialAction": {
                        "@type": "SearchAction",
                        "target": {
                            "@type": "EntryPoint",
                            "urlTemplate": f"{origin}/api/?q={{search_term_string}}"
                        },
                        "query-input": "required name=search_term_string"
                    }
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
                    "name": "Xu FAQ",
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
            "inLanguage": in_lang_code,
            "mainEntity": faq_entities,
            "publisher": {
                "@type": "Organization",
                "name": "Xu Programming Language",
                "url": f"{origin}/",
                "logo": f"{origin}/xu_classic.svg"
            }
        }
    elif bare_path.startswith('api'):
        home_lbl = 'Home' if lang == 'en' else ('首页' if lang == 'zh' else 'Home')
        home_target = f'/{lang}' if lang != 'en' else '/'
        api_target = f'/{lang}/api' if lang in ('en', 'zh') else '/api'
        api_crumbs = [(home_lbl, home_target), ('API', api_target)]
        if bare_path != 'api':
            api_crumbs.append((title, ((f'/{lang}/' if lang != 'en' else '/') + bare_path)))
        schema = {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": ["TechArticle", "APIReference"],
                    "headline": title,
                    "name": title,
                    "description": desc,
                    "url": canonical_url,
                    "inLanguage": in_lang_code,
                    "programmingLanguage": "Xu",
                    "softwareVersion": xu_version,
                    "targetPlatform": ["Linux", "macOS", "Windows", "WebAssembly"],
                    "publisher": {
                        "@type": "Organization",
                        "name": "Xu Programming Language",
                        "url": f"{origin}/",
                        "logo": f"{origin}/xu_classic.svg"
                    }
                },
                make_breadcrumbs_schema(origin, api_crumbs)
            ]
        }
    elif bare_path.startswith('docs'):
        home_lbl = 'Home' if lang == 'en' else ('首页' if lang == 'zh' else 'Home')
        docs_lbl = 'Docs' if lang == 'en' else ('文档' if lang == 'zh' else 'Docs')
        home_target = f'/{lang}' if lang != 'en' else '/'
        docs_target = f'/{lang}/docs/start' if lang != 'en' else '/docs/start'
        doc_crumbs = [(home_lbl, home_target), (docs_lbl, docs_target)]
        if bare_path != 'docs/start':
            doc_crumbs.append((title, ((f'/{lang}/' if lang != 'en' else '/') + bare_path)))
        schema = {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "TechArticle",
                    "headline": title,
                    "description": desc,
                    "url": canonical_url,
                    "inLanguage": in_lang_code,
                    "programmingLanguage": "Xu",
                    "softwareVersion": xu_version,
                    "publisher": {
                        "@type": "Organization",
                        "name": "Xu Programming Language",
                        "url": f"{origin}/",
                        "logo": f"{origin}/xu_classic.svg"
                    }
                },
                make_breadcrumbs_schema(origin, doc_crumbs)
            ]
        }
    else:
        schema = {
            "@context": "https://schema.org",
            "@type": "Article" if bare_path.startswith('blog') else "WebPage",
            "headline": title,
            "description": desc,
            "url": canonical_url,
            "inLanguage": in_lang_code,
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
        'og_type': og_type,
        'og_locale': og_locale,
        'schema_json_ld': schema_json_ld,
        **urls
    }


def doc_breadcrumbs(route: str, en: bool | str | None = None) -> str:
    lang = detect_lang(route, en)
    prefix = f'/{lang}' if lang != 'en' else ''
    rel = route.removeprefix(prefix + '/docs').strip('/')
    group_name = ''
    item_name = ''
    group_labels = DOC_GROUPS_LANGS.get(lang, DOC_GROUPS_LANGS['en'])
    doc_labels = DOC_LABELS_LANGS.get(lang, {})

    for _icon, zh_g, en_g, links in DOC_GROUPS:
        for href, zh, english in links:
            if href == rel:
                group_name = group_labels.get(zh_g, english if lang == 'en' else zh_g)
                item_name = doc_labels.get(href, english if lang == 'en' else zh)
                break
        if item_name:
            break
    if not item_name:
        return ''
    docs_title = "Docs" if lang in ('en', 'es', 'fr', 'de', 'pt-br') else ("文档" if lang == 'zh' else ("文件" if lang == 'zh-tw' else ("ドキュメント" if lang == 'ja' else ("문서" if lang == 'ko' else "Документация"))))
    aria_label = "Documentation hierarchy" if lang == 'en' else ("文档层级导航" if lang == 'zh' else "Hierarchy")
    return (
        f'<nav class="doc-breadcrumbs" aria-label="{aria_label}">'
        f'<a href="{prefix}/docs/start">{docs_title}</a>'
        f'<span class="sep" aria-hidden="true">/</span>'
        f'<span>{escape(group_name)}</span>'
        f'<span class="sep" aria-hidden="true">/</span>'
        f'<span aria-current="page">{escape(item_name)}</span>'
        f'</nav>'
    )


def doc_pagination(route: str, en: bool | str | None = None) -> str:
    lang = detect_lang(route, en)
    prefix = f'/{lang}' if lang != 'en' else ''
    rel = route.removeprefix(prefix + '/docs').strip('/')
    doc_labels = DOC_LABELS_LANGS.get(lang, {})

    prev_word = {'zh': '← 上一篇', 'zh-tw': '← 上一篇', 'ja': '← 前へ', 'ko': '← 이전', 'es': '← Anterior', 'fr': '← Précédent', 'de': '← Zurück', 'ru': '← Назад', 'pt-br': '← Anterior'}.get(lang, '← Previous')
    next_word = {'zh': '下一篇 →', 'zh-tw': '下一篇 →', 'ja': '次へ →', 'ko': '다음 →', 'es': 'Siguiente →', 'fr': 'Suivant →', 'de': 'Weiter →', 'ru': 'Далее →', 'pt-br': 'Próximo →'}.get(lang, 'Next →')

    for _icon, _zh_g, _en_g, links in DOC_GROUPS:
        for i, (href, zh, english) in enumerate(links):
            if href == rel:
                prev_link = links[i - 1] if i > 0 else None
                next_link = links[i + 1] if i + 1 < len(links) else None
                if not prev_link and not next_link:
                    return ''
                prev_html = ''
                if prev_link:
                    p_href, p_zh, p_en = prev_link
                    p_label = doc_labels.get(p_href, p_en if lang == 'en' else p_zh)
                    prev_html = (
                        f'<a class="doc-pagination-link prev" href="{prefix}/docs/{escape(p_href)}/">'
                        f'<span class="doc-pagination-sub">{prev_word}</span>'
                        f'<span class="doc-pagination-title">{escape(p_label)}</span>'
                        f'</a>'
                    )
                next_html = ''
                if next_link:
                    n_href, n_zh, n_en = next_link
                    n_label = doc_labels.get(n_href, n_en if lang == 'en' else n_zh)
                    next_html = (
                        f'<a class="doc-pagination-link next" href="{prefix}/docs/{escape(n_href)}/">'
                        f'<span class="doc-pagination-sub">{next_word}</span>'
                        f'<span class="doc-pagination-title">{escape(n_label)}</span>'
                        f'</a>'
                    )
                return f'<nav class="doc-pagination" aria-label="Pagination">{prev_html}{next_html}</nav>'
    return ''


NAV_TAB_LABELS = {
    'en': ('Docs', 'API', 'Playground', 'Benchmarks', 'Download', 'Blog'),
    'zh': ('文档', 'API', '演练场', '横测', '下载', '博客'),
    'zh-tw': ('文件', 'API', '演練場', '效能評測', '下載', '部落格'),
    'ja': ('ドキュメント', 'API', 'プレイグラウンド', 'ベンチマーク', 'ダウンロード', 'ブログ'),
    'ko': ('문서', 'API', '플레이그라운드', '벤치마크', '다운로드', '블로그'),
    'es': ('Docs', 'API', 'Playground', 'Benchmarks', 'Descargar', 'Blog'),
    'fr': ('Docs', 'API', 'Bac à sable', 'Performances', 'Télécharger', 'Blog'),
    'de': ('Docs', 'API', 'Playground', 'Benchmarks', 'Download', 'Blog'),
    'ru': ('Документация', 'API', 'Песочница', 'Бенчмарки', 'Скачать', 'Блог'),
    'pt-br': ('Docs', 'API', 'Playground', 'Benchmarks', 'Baixar', 'Blog'),
}


def render(root: Path, title: str, route: str, body: str, xu_version: str) -> str:
    lang = detect_lang(route)
    en = lang == 'en'
    prefix = f'/{lang}' if not en else ''
    home = prefix or '/'
    api_route = route == prefix + '/api' or route.startswith(prefix + '/api/')
    api_assets = ''
    rest = route.removeprefix(prefix) if prefix else route

    if rest.startswith('/docs/'):
        doc_crumb_html = doc_breadcrumbs(route, lang)
        if doc_crumb_html:
            if re.search(r'<p\s+class=[\'"]crumb[\'"]>.*?</p>\s*', body):
                body = re.sub(r'<p\s+class=[\'"]crumb[\'"]>.*?</p>\s*', doc_crumb_html, body, count=1)
            else:
                body = doc_crumb_html + body
        pagination = doc_pagination(route, lang)
        if pagination:
            body = body + pagination
    if api_route:
        digest = hashlib.sha256()
        for name in ('api-browser.css', 'api-browser.js'):
            digest.update((root / 'www' / name).read_bytes())
        version = digest.hexdigest()[:16]
        api_assets = (f'<link rel="stylesheet" href="/api-browser.css?v={version}">'
                      f'<script src="/api-browser.js?v={version}" defer></script>')
        body = re.sub(r'<p class="crumb">.*?</p>\s*', '', body, count=1, flags=re.DOTALL)
        body = re.sub(r'<nav class="widget-crumb"[^>]*>.*?</nav>\s*', '', body, count=1, flags=re.DOTALL)
        body = api_tools(route, en, root) + api_index_presentation(body, en)

    nav = []
    tabs = NAV_TAB_LABELS.get(lang, NAV_TAB_LABELS['en'])
    nav_items = [
        ('/docs/start', 'book', tabs[0]),
        ('/api', 'api', tabs[1]),
        ('/playground', 'play', tabs[2]),
        ('/benchmarks', 'benchmark', tabs[3]),
        ('/download', 'download', tabs[4]),
        ('/blog', 'chat', tabs[5]),
    ]
    for href, icon, tab_label in nav_items:
        if lang not in ('en', 'zh') and href in ('/api', '/blog'):
            target = href
        else:
            target = prefix + href
        if href == '/docs/start':
            active = route == target or route.startswith(prefix + '/docs/')
        elif href == '/api':
            active = route == target or route.startswith('/api/') or (prefix and route.startswith(prefix + '/api/'))
        elif href == '/blog':
            active = route == target or route.startswith('/blog/') or (prefix and route.startswith(prefix + '/blog/'))
        else:
            active = route == target
        cls = 'nav-tab-btn active' if active else 'nav-tab-btn'
        current = ' aria-current="page"' if active else ''
        nav.append(f'<a class="{cls}"{current} href="{target}"><i class="xi xi-{icon}"></i> {tab_label}</a>')

    is_home = route in ('/', '/zh', '/ru') or any(route == f'/{l}' for l in ALL_LANGS)
    is_play = any(route == f'/{l}/playground' for l in ALL_LANGS if l != 'en') or route == '/playground'
    is_bench = any(route == f'/{l}/benchmarks' for l in ALL_LANGS if l != 'en') or route == '/benchmarks'

    if is_home:
        main = '<main class="home">' + body + '</main>'
    elif is_play:
        main = '<main class="home playground-page">' + body + '</main>'
    elif is_bench:
        main = '<main class="home bench-page">' + body + '</main>'
    else:
        cls = 'doc download' if route == prefix + '/download' else ('doc api-page' if api_route else 'doc')
        main = '<div class="page page-with-side">' + sidebar(route, lang, xu_version, root) + f'<main class="{cls}">' + body + '</main></div>'

    # Relative paths for dropdown
    bare_route = rest.rstrip('/')
    dropdown_urls = {}
    active_flags = {}
    translated_languages = []

    for l in ALL_LANGS:
        key = f"url_{l.replace('-', '_')}_rel"
        act_key = f"active_{l.replace('-', '_')}"
        active_flags[act_key] = ' active' if lang == l else ''

        if route == '/404':
            dropdown_urls[key] = '/' if l == 'en' else f'/{l}/'
        else:
            t_file = bare_route.strip('/') + '.html' if bare_route else 'home.html'
            exists = (root / f'content/{l}' / t_file).is_file()
            if exists:
                translated_languages.append(l)
                dropdown_urls[key] = (bare_route or '') + '/' if l == 'en' else f'/{l}' + (bare_route or '') + '/'
            else:
                dropdown_urls[key] = '/' if l == 'en' else f'/{l}/'

    # For the language switch button (maintains test invariants):
    if lang == 'en':
        other = ('/zh' if route == '/' else '/zh' + route)
        other_code = 'zh-CN'
        lang_title = '中文'
        lang_label = '中文'
    else:
        other = (route.removeprefix(prefix) or '/')
        other_code = 'en'
        lang_title = 'English'
        lang_label = 'EN'
    if route == '/404':
        other = '/zh' if lang == 'en' else '/'

    meta = get_seo_meta(route, title, lang, xu_version, body)
    alternate_links = [
        f'<link rel="alternate" hreflang="{IN_LANGUAGES[l]}" href="{meta["url_" + l.replace("-", "_")]}">'
        for l in translated_languages
    ]
    if 'en' in translated_languages:
        alternate_links.append(f'<link rel="alternate" hreflang="x-default" href="{meta["url_en"]}">')
    template = Template((root / 'templates/page.html').read_text(encoding='utf-8'))
    playground_assets = '<script src="/xu-play.js" defer></script>'

    home_title = {
        'en': 'Xu Home', 'zh': 'Xu 官网首页', 'zh-tw': 'Xu 官網首頁',
        'ja': 'Xu 公式ホーム', 'ko': 'Xu 공식 홈', 'es': 'Xu Inicio',
        'fr': 'Xu Accueil', 'de': 'Xu Startseite',
        'ru': 'Xu Главная', 'pt-br': 'Xu Início'
    }.get(lang, 'Xu Home')
    search_label = {
        'en': 'Search', 'zh': '搜索', 'zh-tw': '搜尋',
        'ja': '検索', 'ko': '검색', 'es': 'Buscar',
        'fr': 'Rechercher', 'de': 'Suche',
        'ru': 'Поиск', 'pt-br': 'Buscar'
    }.get(lang, 'Search')
    theme_label = {
        'en': 'Switch theme', 'zh': '切换主题', 'zh-tw': '切換主題',
        'ja': 'テーマ切替', 'ko': '테마 전환', 'es': 'Cambiar tema',
        'fr': 'Changer de thème', 'de': 'Thema wechseln',
        'ru': 'Сменить тему', 'pt-br': 'Alternar tema'
    }.get(lang, 'Switch theme')
    social_label = 'Official accounts' if lang != 'zh' else '官方帐号'
    menu_label = 'Navigation menu' if lang != 'zh' else '导航菜单'
    nav_label = 'Main navigation' if lang != 'zh' else '主导航'
    footer_text = (
        '<a href="/LICENSE">MIT License</a> · Zero GC · Inferred Ownership · Custom AOT'
        if lang not in ('zh', 'zh-tw') else
        '<a href="/LICENSE">MIT 開源協議</a> · 零 GC · 所有權推斷 · 自研 AOT'
    )

    return template.substitute(
        lang=IN_LANGUAGES.get(lang, 'en'),
        title=escape(title), home=home,
        home_title=home_title,
        version_badge=('' if is_home else f'<span class="badge">v{escape(xu_version)}</span>'),
        footer_identity='XU' if is_home else 'XU v' + escape(xu_version),
        nav=''.join(nav), main=main,
        alternate_links='\n  '.join(alternate_links),
        search_label=search_label,
        playground_assets=playground_assets,
        page_assets=api_assets + ('<script src="/xu-play-canvas.js" defer></script>'
                     if is_home else '') + ('<link rel="stylesheet" href="/playground-design.css"><link rel="stylesheet" href="/widgets.css">'
                     if '/api/ui/widgets' in route else '') + ('<link rel="stylesheet" href="/playground.css">'
                     '<link rel="stylesheet" href="/playground-design.css">'
                     '<link rel="stylesheet" href="/widgets.css">'
                     '<script src="/xu-play-canvas.js" defer></script>'
                     '<script src="/xu-play-preview.js" defer></script>'
                     '<script src="/xu-play-workspace.js" defer></script>'
                     '<script src="/xu-play-library.js" defer></script>'
                     '<script src="/widget-experience.js" defer></script>'
                     if is_play else ''),
        other_lang=other, other_lang_code=other_code,
        lang_title=lang_title, lang_label=lang_label,
        theme_label=theme_label, ui_href=prefix + '/docs/ui',
        footer_text=footer_text,
        header_social=social_links(lang, compact=True), footer_social=social_links(lang),
        social_label=social_label,
        menu_label=menu_label,
        nav_label=nav_label,
        **dropdown_urls,
        **active_flags,
        **meta,
    )
