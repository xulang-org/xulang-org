import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {test} from 'node:test';
import assert from 'node:assert/strict';

const source = readFileSync(new URL('../www/theme.js', import.meta.url), 'utf8');
function visit({path = '/', locale = 'zh-CN', saved = {}, cookies = {}, storageBlocked = false, cookiesBlocked = false, base = '', choice = 'en'} = {}) {
  const events = {};
  const link = {href: `https://example.org${base}${choice === 'en' ? '/' : '/zh/'}`,
    getAttribute() { return choice === 'en' ? 'en' : 'zh-CN'; },
    addEventListener(name, handler) { events[name] = handler; }};
  const document = {
    currentScript: {src: `https://example.org${base}/theme.js`},
    documentElement: {lang: 'en', setAttribute() {}},
    getElementById(id) { return id === 'language-switch' ? link : null; },
    querySelectorAll() { return []; },
    addEventListener(name, handler) { events[name] = handler; },
    get cookie() { if (cookiesBlocked) throw Error('blocked'); return Object.entries(cookies).map(([k,v]) => `${k}=${v}`).join('; '); },
    set cookie(value) { if (cookiesBlocked) throw Error('blocked'); const [k,v] = value.split(';')[0].split('='); cookies[k] = v; }
  };
  const redirects = [];
  const window = {location: {href: `https://example.org${path}`, replace: p => redirects.push(p)}, addEventListener() {}};
  const localStorage = {
    getItem(k) { if (storageBlocked) throw Error('blocked'); return saved[k]; },
    setItem(k,v) { if (storageBlocked) throw Error('blocked'); saved[k] = v; }
  };
  vm.runInNewContext(source, {document, window, localStorage, navigator: {language: locale}, URL});
  events.DOMContentLoaded();
  return {redirects, link, click: () => events.click(), saved, cookies};
}

test('Chinese browser automatically chooses ZH only on the bare home, preserving query and fragment', () => {
  assert.deepEqual(visit({path: '/?example=hello#intro'}).redirects, ['/zh/?example=hello#intro']);
  for (const path of ['/docs/start/', '/zh/', '/api/', '/playground/']) assert.deepEqual(visit({path}).redirects, []);
  for (const locale of ['en-US', 'zh-TW', 'zh-Hant']) assert.deepEqual(visit({locale}).redirects, []);
});
test('manual EN click persists and overrides Chinese locale on a subsequent visit', () => {
  const state = visit({path: '/zh/'});
  state.click();
  assert.equal(state.saved['xu-lang'], 'en');
  assert.equal(state.cookies['xu-lang'], 'en');
  assert.deepEqual(visit({saved: state.saved, cookies: state.cookies}).redirects, []);
  assert.deepEqual(visit({path: new URL(state.link.href).pathname + new URL(state.link.href).search}).redirects, []);
});
test('cookie keeps EN when localStorage is blocked; all storage blocked still honors the explicit link', () => {
  const state = visit({path: '/zh/', storageBlocked: true}); state.click();
  assert.deepEqual(visit({storageBlocked: true, cookies: state.cookies}).redirects, []);
  const blocked = visit({path: '/zh/', storageBlocked: true, cookiesBlocked: true}); blocked.click();
  assert.match(blocked.link.href, /\?lang=en$/);
  assert.deepEqual(visit({path: '/?lang=en', storageBlocked: true, cookiesBlocked: true}).redirects, []);
});
test('manual ZH selection overrides an English locale; explicit query supersedes an older preference', () => {
  const state = visit({locale: 'en-US', choice: 'zh'}); state.click();
  assert.equal(state.saved['xu-lang'], 'zh');
  assert.deepEqual(visit({saved: state.saved, locale: 'en-US'}).redirects, ['/zh/']);
  assert.deepEqual(visit({path: '/?lang=en', saved: {'xu-lang': 'zh'}}).redirects, []);
});
test('root and project-prefix deployment redirects stay inside their base', () => {
  assert.deepEqual(visit({path: '/project/', base: '/project'}).redirects, ['/project/zh/']);
  const state = visit({path: '/project/zh/', base: '/project'}); state.click();
  assert.equal(state.link.href, 'https://example.org/project/?lang=en');
  assert.deepEqual(visit({path: '/project/?lang=en', base: '/project'}).redirects, []);
});
test('invalid stored values do not suppress locale detection; theme stays independent', () => {
  assert.deepEqual(visit({saved: {'xu-lang': 'bad', 'xu-theme': 'dark'}}).redirects, ['/zh/']);
  const state = visit({saved: {'xu-theme': 'dark'}, path: '/zh/'}); state.click();
  assert.equal(state.saved['xu-theme'], 'dark');
});
