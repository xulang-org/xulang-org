#!/usr/bin/env python3
"""Build the official website using Python's standard library only."""

from __future__ import annotations

import argparse
import json
import hashlib
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path
import re
import shutil
from urllib.parse import unquote, urlsplit

from site_layout import render

ROOT = Path(__file__).resolve().parents[1]
RELEASES_URL = 'https://github.com/xulang-org/xu/releases'
URL_ATTR = re.compile(r'''(\s(?:href|src|action|poster)\s*=\s*)(["'])(.*?)\2''', re.IGNORECASE | re.DOTALL)
TITLE = re.compile(r'\A<!--title:\s*(.*?)-->\s*', re.DOTALL)


def playground_options(root: Path, body: str, lang: str) -> str:
    if 'id="xu-play-ex"' not in body:
        return body
    examples = json.loads((root / 'www/xu-play-examples.json').read_text(encoding='utf-8'))
    groups = {
        'basics': ('起步与基本类型', 'Getting started'),
        'flow': ('控制流', 'Control flow'),
        'data': ('函数与数据结构', 'Functions & data'),
        'checks': ('断言与编译诊断', 'Assertions & diagnostics'),
        'concurrency': ('协程与 chan', 'Coroutines & chan'),
        'combined': ('综合示例', 'Combined example'),
    }
    options = []
    for group, titles in groups.items():
        options.append('<optgroup label="' + escape(titles[lang == 'en']) + '">')
        for key, example in examples.items():
            if example['group'] == group:
                selected = ' selected' if key == 'hello' else ''
                options.append(f'<option value="{escape(key)}"{selected}>{escape(example["title"][lang])}</option>')
        options.append('</optgroup>')
    return re.sub(r'(<select id="xu-play-ex">).*?(</select>)',
                  lambda match: match[1] + ''.join(options) + match[2], body, flags=re.DOTALL)


def normalize_base(value: str) -> str:
    if value in ('', '/'):
        return ''
    if not re.fullmatch(r'/?[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*/?', value):
        raise ValueError('base path must be a URL path such as /xulang-org')
    return '/' + value.strip('/')


def content_route(relative: Path, lang: str) -> str:
    name = relative.with_suffix('').as_posix()
    if name == 'home':
        name = ''
    elif name.endswith('/index'):
        name = name[:-6]
    prefix = '' if lang == 'en' else '/zh'
    return prefix + ('/' + name if name else '') or '/'


class RewriteHTML(HTMLParser):
    """Rewrite real URL attributes without altering examples or inline scripts."""

    def __init__(self, base: str, routes: set[str], playground: bool, asset_key: str = "", content_lang: str = ""):
        super().__init__(convert_charrefs=False)
        self.base, self.routes, self.playground = base, routes, playground
        self.asset_key = asset_key
        self.content_lang = content_lang
        self.parts: list[str] = []

    def rewrite_url(self, raw: str, localized: bool = True) -> str:
        value = unescape(raw)
        if not value.startswith('/') or value.startswith('//'):
            return raw
        url = urlsplit(value)
        if url.path.startswith('/releases/'):
            return RELEASES_URL
        path = url.path
        # Older English fragments use /en; Chinese fragments use bare routes.
        # Keep shared assets at the root, and respect explicit hreflang links.
        if path == '/en' or path.startswith('/en/'):
            path = path[3:] or '/'
        elif localized and self.content_lang == 'zh':
            chinese = '/zh' + path.rstrip('/')
            if chinese in self.routes:
                path = chinese
        if path.rstrip('/') in self.routes or path == '/':
            path = path.rstrip('/') + '/'
        result = self.base + path
        if url.query:
            result += '?' + url.query
        if url.fragment:
            result += '#' + url.fragment
        return escape(result, quote=True)

    def start_tag(self, tag: str, attrs, closed: bool = False) -> None:
        raw = self.get_starttag_text()
        localized = not any(name == 'hreflang' for name, _ in attrs)
        raw = URL_ATTR.sub(lambda m: m[1] + m[2] + self.rewrite_url(m[3], localized) + m[2], raw)
        if tag == 'script' and re.search(r'''src\s*=\s*["'][^"']*/xu-play\.js["']''', raw):
            if self.asset_key:
                raw = raw.replace("xu-play.js", "xu-play.js?v=" + self.asset_key)
            end = '/>' if closed else '>'
            raw = raw[:-len(end)] + f' data-wasm-available="{str(self.playground).lower()}"' + end
        self.parts.append(raw)

    def handle_starttag(self, tag, attrs):
        self.start_tag(tag, attrs)

    def handle_startendtag(self, tag, attrs):
        self.start_tag(tag, attrs, True)

    def handle_endtag(self, tag):
        self.parts.append(f'</{tag}>')

    def handle_data(self, data):
        self.parts.append(data)

    def handle_entityref(self, name):
        self.parts.append('&' + name + ';')

    def handle_charref(self, name):
        self.parts.append('&#' + name + ';')

    def handle_comment(self, data):
        self.parts.append('<!--' + data + '-->')

    def handle_decl(self, decl):
        self.parts.append('<!' + decl + '>')


class LocalLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        self.links.extend(value for name, value in attrs if name in ('href', 'src', 'poster') and value)


def check_links(output: Path, base: str) -> None:
    errors = []
    for page in sorted(output.rglob('*.html')):
        parser = LocalLinks()
        parser.feed(page.read_text(encoding='utf-8'))
        for value in parser.links:
            url = urlsplit(value)
            if url.scheme or url.netloc or not url.path:
                continue
            path = unquote(url.path)
            if path.startswith('/'):
                if base and not path.startswith(base + '/'):
                    errors.append(f'{page.relative_to(output)}: URL escapes base path: {value}')
                    continue
                target = output / path[len(base):].lstrip('/')
            else:
                target = page.parent / path
            if target.is_dir():
                target = target / 'index.html'
            if not target.is_file() or not target.resolve().is_relative_to(output.resolve()):
                errors.append(f'{page.relative_to(output)}: missing {value}')
    if errors:
        raise ValueError('Broken local links:\n' + '\n'.join(sorted(set(errors))))


def build(root: Path, output: Path, base: str = '', require_playground: bool = False, xu_version: str | None = None) -> int:
    base = normalize_base(base)
    if output.is_symlink():
        raise ValueError('output must not be a symbolic link')
    root, output = root.resolve(), output.resolve()
    # Only the dedicated build directory may be replaced; never delete source.
    if output == root or root.is_relative_to(output) or (output.is_relative_to(root) and output != root / 'dist'):
        raise ValueError('output must be dist/ or a directory outside the source tree')
    if output.exists() and any(output.iterdir()) and not (output / '.xu-static-build').is_file():
        raise ValueError('refusing to replace a nonempty directory without a .xu-static-build marker')
    wasm = root / 'build/playground/xu-play.wasm'
    if require_playground and not wasm.is_file():
        raise ValueError('Xu playground WASM is required; run make wasm before publishing')
    if wasm.is_file() and wasm.read_bytes()[:8] != b'\x00asm\x01\x00\x00\x00':
        raise ValueError('invalid Xu playground WASM file')
    pages = {}
    for lang in ('zh', 'en'):
        directory = root / 'content' / lang
        for source in sorted(directory.rglob('*.html')):
            route = content_route(source.relative_to(directory), lang)
            if route in pages:
                raise ValueError(f'duplicate route: {route}')
            pages[route] = source
    if '/' not in pages or '/zh' not in pages:
        raise ValueError('both Chinese and English home pages are required')
    match = re.search(r'^xu:\s*!ver\s+(\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)\s*$', (root / 'xu.xun').read_text(), re.MULTILINE)
    if not match:
        raise ValueError('missing Xu version in xu.xun')
    xu_version = xu_version or match[1]
    if not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?', xu_version):
        raise ValueError('invalid Xu release version')
    if wasm.is_file():
        record = wasm.parent / 'build.json'
        if not record.is_file():
            raise ValueError('WASM build version is missing; run make wasm')
        built = json.loads(record.read_text())
        if built.get('xu_version') != xu_version:
            raise ValueError(f'WASM version does not match Xu {xu_version}; run make wasm with the matching SDK')
        if built.get('wasm_sha256') != hashlib.sha256(wasm.read_bytes()).hexdigest():
            raise ValueError('WASM build checksum does not match; run make wasm')
    for source in pages.values():
        if 'api' in source.relative_to(root / 'content').parts:
            recorded = re.search(r'<!--xu-api-version:\s*(.*?)-->', source.read_text())
            if not recorded or recorded[1].strip() != xu_version:
                raise ValueError(f'API version does not match Xu {xu_version}; regenerate API from the matching SDK')
    digest = hashlib.sha256()
    for name in ('xu-play.js', 'xu-play-worker.js', 'xu-play-runtime.mjs', 'xu-play-examples.json', 'xu-play.wasm'):
        asset = wasm if name == 'xu-play.wasm' else root / 'www' / name
        if asset.exists():
            digest.update(name.encode())
            digest.update(asset.read_bytes())
    asset_key = digest.hexdigest()[:16]
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    (output / '.xu-static-build').touch()
    for source in sorted((root / 'www').rglob('*')):
        relative = source.relative_to(root / 'www')
        if not source.is_file() or 'releases' in relative.parts or source.name.startswith('.') or source.name == 'xu-play.wasm':
            continue
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    if wasm.is_file():
        shutil.copyfile(wasm, output / 'xu-play.wasm')
    playground = (output / 'xu-play.wasm').is_file()
    for route, source in pages.items():
        lang = source.relative_to(root / 'content').parts[0]
        raw = source.read_text(encoding='utf-8').replace('{{xu_version}}', xu_version)
        title = TITLE.match(raw)
        body = raw[title.end():] if title else raw
        body = playground_options(root, body, lang)
        html = render(root, title[1].strip() if title else 'Xu', route, body, xu_version)
        parser = RewriteHTML(base, set(pages), playground, asset_key, lang)
        parser.feed(html)
        target = output / route.strip('/') / 'index.html'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(''.join(parser.parts), encoding='utf-8')
        if lang == 'en':
            # Preserve bookmarks to the former English prefix, including hashes
            # and query strings when JavaScript is enabled.
            destination = base + route.rstrip('/') + '/'
            alias = output / 'en' / route.strip('/') / 'index.html'
            alias.parent.mkdir(parents=True, exist_ok=True)
            href = escape(destination, quote=True)
            alias.write_text(
                '<!doctype html><html lang="en"><head><meta charset="utf-8">'
                f'<meta http-equiv="refresh" content="0;url={href}">'
                f'<link rel="canonical" href="{href}">'
                '<meta name="robots" content="noindex"><title>Page moved · Xu</title>'
                f'<script>location.replace({json.dumps(destination)} + location.search + location.hash);</script>'
                f'</head><body><a href="{href}">Continue to the English page</a></body></html>',
                encoding='utf-8',
            )
    body = '<h1>Page not found / 没有这一页</h1><p><a href="/">Home</a> · <a href="/zh">中文首页</a></p>'
    parser = RewriteHTML(base, set(pages), playground, asset_key)
    parser.feed(render(root, '404 · Xu', '/404', body, xu_version))
    (output / '404.html').write_text(''.join(parser.parts), encoding='utf-8')
    (output / '.nojekyll').touch()
    check_links(output, base)
    return len(pages)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist')
    parser.add_argument('--base-path', default='')
    parser.add_argument('--require-playground', action='store_true', help='fail rather than publish a disabled playground')
    parser.add_argument('--xu-version', help='version from the final SDK matching Xu main (default: xu.xun)')
    args = parser.parse_args()
    try:
        count = build(ROOT, args.output, args.base_path, args.require_playground, args.xu_version)
    except (OSError, ValueError) as error:
        parser.exit(1, f'{error}\n')
    print(f'Built {count} pages → {args.output} (base path: {normalize_base(args.base_path) or "/"})')


if __name__ == '__main__':
    main()
