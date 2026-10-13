#!/usr/bin/env python3
"""Build the official website using Python's standard library only."""

from __future__ import annotations

import argparse
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
    prefix = '/en' if lang == 'en' else ''
    return prefix + ('/' + name if name else '') or '/'


class RewriteHTML(HTMLParser):
    """Rewrite real URL attributes without altering examples or inline scripts."""

    def __init__(self, base: str, routes: set[str], playground: bool):
        super().__init__(convert_charrefs=False)
        self.base, self.routes, self.playground = base, routes, playground
        self.parts: list[str] = []

    def rewrite_url(self, raw: str) -> str:
        value = unescape(raw)
        if not value.startswith('/') or value.startswith('//'):
            return raw
        url = urlsplit(value)
        if url.path.startswith('/releases/'):
            return RELEASES_URL
        path = url.path
        if path.rstrip('/') in self.routes or path == '/':
            path = path.rstrip('/') + '/'
        result = self.base + path
        if url.query:
            result += '?' + url.query
        if url.fragment:
            result += '#' + url.fragment
        return escape(result, quote=True)

    def start_tag(self, tag: str, closed: bool = False) -> None:
        raw = self.get_starttag_text()
        raw = URL_ATTR.sub(lambda m: m[1] + m[2] + self.rewrite_url(m[3]) + m[2], raw)
        if tag == 'script' and re.search(r'''src\s*=\s*["'][^"']*/xu-play\.js["']''', raw):
            end = '/>' if closed else '>'
            raw = raw[:-len(end)] + f' data-wasm-available="{str(self.playground).lower()}"' + end
        self.parts.append(raw)

    def handle_starttag(self, tag, attrs):
        self.start_tag(tag)

    def handle_startendtag(self, tag, attrs):
        self.start_tag(tag, True)

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


def build(root: Path, output: Path, base: str = '') -> int:
    base = normalize_base(base)
    if output.is_symlink():
        raise ValueError('output must not be a symbolic link')
    root, output = root.resolve(), output.resolve()
    # Only the dedicated build directory may be replaced; never delete source.
    if output == root or root.is_relative_to(output) or (output.is_relative_to(root) and output != root / 'dist'):
        raise ValueError('output must be dist/ or a directory outside the source tree')
    if output.exists() and any(output.iterdir()) and not (output / '.xu-static-build').is_file():
        raise ValueError('refusing to replace a nonempty directory without a .xu-static-build marker')
    pages = {}
    for lang in ('zh', 'en'):
        directory = root / 'content' / lang
        for source in sorted(directory.rglob('*.html')):
            route = content_route(source.relative_to(directory), lang)
            if route in pages:
                raise ValueError(f'duplicate route: {route}')
            pages[route] = source
    if '/' not in pages or '/en' not in pages:
        raise ValueError('both Chinese and English home pages are required')
    match = re.search(r'^xu:\s*!ver\s+(\d+\.\d+\.\d+)\s*$', (root / 'xu.xun').read_text(), re.MULTILINE)
    if not match:
        raise ValueError('missing Xu version in xu.xun')
    xu_version = match[1]
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    (output / '.xu-static-build').touch()
    for source in sorted((root / 'www').rglob('*')):
        relative = source.relative_to(root / 'www')
        if not source.is_file() or 'releases' in relative.parts or source.name.startswith('.'):
            continue
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    playground = (output / 'xu-play.wasm').is_file()
    for route, source in pages.items():
        raw = source.read_text(encoding='utf-8')
        title = TITLE.match(raw)
        html = render(root, title[1].strip() if title else 'Xu', route, raw[title.end():] if title else raw, xu_version)
        parser = RewriteHTML(base, set(pages), playground)
        parser.feed(html)
        target = output / route.strip('/') / 'index.html'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(''.join(parser.parts), encoding='utf-8')
    body = '<h1>没有这一页 / Page not found</h1><p><a href="/">回首页</a> · <a href="/en">Home</a></p>'
    parser = RewriteHTML(base, set(pages), playground)
    parser.feed(render(root, '404 · Xu', '/404', body, xu_version))
    (output / '404.html').write_text(''.join(parser.parts), encoding='utf-8')
    (output / '.nojekyll').touch()
    check_links(output, base)
    return len(pages)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist')
    parser.add_argument('--base-path', default='')
    args = parser.parse_args()
    try:
        count = build(ROOT, args.output, args.base_path)
    except (OSError, ValueError) as error:
        parser.exit(1, f'{error}\n')
    print(f'Built {count} pages → {args.output} (base path: {normalize_base(args.base_path) or "/"})')


if __name__ == '__main__':
    main()
