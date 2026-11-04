(function () {
  'use strict';

  function normalize(value) {
    return String(value).normalize('NFKC').toLowerCase().replace(/[#$&/.():]+/g, ' ').replace(/\s+/g, ' ').trim();
  }

  function prepare(entries) {
    return entries.map(function (entry) {
      var name = normalize(entry.title);
      var namespace = normalize(entry.namespace || '');
      return Object.assign({}, entry, {name: name, keys: (name + ' ' + namespace).split(' '),
        search: normalize(entry.title + ' ' + (entry.detail || '') + ' ' + (entry.context || '') + ' ' + namespace)});
    });
  }

  function search(entries, query, limit) {
    var normalized = normalize(query);
    var terms = normalized.split(' ').filter(Boolean);
    var qualifiers = /[.:]/.test(query) ? terms.slice(0, -1) : [];
    var matches = entries.filter(function (entry) {
      return terms.every(function (term) { return entry.search.includes(term); }) &&
        qualifiers.every(function (term) { return entry.keys.includes(term); }) &&
        (!qualifiers.length || entry.name.includes(terms[terms.length - 1]));
    });
    function score(entry) {
      return entry.name === normalized ? 0 : entry.name.startsWith(normalized) ? 1 : entry.name.includes(normalized) ? 2 : 3;
    }
    if (normalized) matches.sort(function (a, b) { return score(a) - score(b); });
    return {total: matches.length, items: matches.slice(0, limit)};
  }

  function isSearchKey(event, editing, modalOpen) {
    return event.key === '/' && !event.defaultPrevented && !event.isComposing &&
      !event.ctrlKey && !event.metaKey && !event.altKey && !editing && !modalOpen;
  }
  function isCloseKey(event) {
    return event.key === 'Escape' && !event.isComposing && event.keyCode !== 229;
  }
  if (typeof module === 'object' && module.exports) module.exports = {normalize: normalize, prepare: prepare, search: search, isSearchKey: isSearchKey, isCloseKey: isCloseKey};
  if (typeof document === 'undefined') return;

  var opener = document.querySelector('[data-api-search]');
  var main = document.querySelector('main.api-page');
  if (!opener || !main) return;
  var en = document.documentElement.lang === 'en';
  var directory = document.getElementById('api-directory');
  if (directory && window.matchMedia) {
    var media = window.matchMedia('(max-width: 860px)');
    function resizeDirectory() {
      var active = document.activeElement;
      var inside = directory.contains(active);
      directory.open = !media.matches;
      if (inside && media.matches) opener.focus({preventScroll: true});
      else if (active === directory.querySelector('summary')) (directory.querySelector('[aria-current="page"]') || opener).focus({preventScroll: true});
    }
    resizeDirectory();
    media.addEventListener('change', resizeDirectory);
  }

  var packages = prepare(Array.from(document.querySelectorAll('.side-api-links a, .side-list a')).map(function (link) {
    var topic = link.closest('.side-api-topic, .side-group');
    var summary = topic && topic.querySelector('summary, .side-h-title');
    return {title: link.textContent.trim(), detail: summary ? summary.textContent.trim() : (en ? 'API directory' : 'API 目录'),
      namespace: new URL(link.href, window.location.href).pathname, href: link.href};
  }));
  var symbols;
  var articles = Array.from(main.querySelectorAll('.api-item[id]'));
  var packageName = main.querySelector('h1').textContent.trim();
  // Preparing the large declarations index is deferred until search is requested.
  function pageSymbols() {
    if (symbols) return symbols;
    symbols = prepare(articles.map(function (article) {
      var heading = article.querySelector('h2');
      var signature = article.querySelector('pre code');
      var purpose = article.querySelector('h3 + p');
      return {title: heading.textContent.trim(), detail: signature ? signature.textContent.trim().split('\n')[0] : '',
        namespace: packageName, context: purpose ? purpose.textContent : '', href: '#' + encodeURIComponent(article.id), target: article};
    }));
    return symbols;
  }

  // Heading links are native bookmarks; no declaration ID or source text changes.
  articles.forEach(function (article) {
    var heading = article.querySelector('h2');
    var link = document.createElement('a');
    link.className = 'api-permalink';
    link.href = '#' + encodeURIComponent(article.id);
    link.title = en ? 'Link to this declaration' : '直达此声明';
    while (heading.firstChild) link.appendChild(heading.firstChild);
    heading.appendChild(link);
    article.tabIndex = -1;
  });

  var dialog = document.createElement('dialog');
  dialog.className = 'api-search-dialog';
  dialog.setAttribute('aria-labelledby', 'api-search-title');
  dialog.innerHTML = '<div class="api-search-heading"><div><h2 id="api-search-title">' + (en ? 'Find an API' : '查找 API') + '</h2>' +
    '<p>' + (en ? 'Search packages or jump to a declaration on this page.' : '查找包，或直接跳转到本页声明。') + '</p></div>' +
    '<button type="button" data-close>' + (en ? 'Close' : '关闭') + '</button></div>' +
    '<div class="api-search-fields"><label>' + (en ? 'Search scope' : '搜索范围') + '<select id="api-search-scope">' +
    (articles.length ? '<option value="page">' + (en ? 'This page' : '本页声明') + ' · ' + articles.length + '</option>' : '') +
    '<option value="packages">' + (en ? 'All packages & components' : '全部包与组件') + '</option></select></label>' +
    '<div class="api-search-query"><label for="api-search-input">' + (en ? 'Name or description' : '名称或说明') + '</label>' +
    '<div class="api-search-input-row"><input type="search" id="api-search-input" autocomplete="off" spellcheck="false">' +
    '<button type="button" data-clear>' + (en ? 'Clear' : '清空') + '</button></div></div></div>' +
    '<p class="api-search-count" role="status" aria-live="polite"></p><ul class="api-search-results" aria-label="' +
    (en ? 'API search results' : 'API 搜索结果') + '"></ul>';
  document.body.appendChild(dialog);
  var input = dialog.querySelector('input');
  var scope = dialog.querySelector('select');
  var results = dialog.querySelector('ul');
  var status = dialog.querySelector('[role="status"]');
  var clear = dialog.querySelector('[data-clear]');
  var restoreFocus = null;
  var jumpTarget = null;
  input.placeholder = articles.length ? 'split · Button.input' : '#strings · ui/widgets · mysql';
  function renderResults() {
    clear.disabled = !input.value;
    var entries = scope.value === 'page' ? pageSymbols() : packages;
    var found = search(entries, input.value, 30);
    results.replaceChildren();
    found.items.forEach(function (entry) {
      var item = document.createElement('li');
      var link = document.createElement('a');
      link.href = entry.href;
      var name = document.createElement('strong');
      name.textContent = entry.title;
      var detail = document.createElement('span');
      detail.textContent = entry.detail;
      link.append(name, detail);
      link.addEventListener('click', function () { jumpTarget = entry.target || null; dialog.close(); });
      item.appendChild(link);
      results.appendChild(item);
    });
    status.textContent = found.total ? (en ? found.total + (found.total === 1 ? ' result' : ' results') : '找到 ' + found.total + ' 项') +
      (found.total > 30 ? (en ? ' · Showing the first 30; refine your search.' : ' · 显示前 30 项，请输入更多关键词。') : '') :
      (en ? 'No matches. Try another name or change the scope.' : '没有匹配项。试试其他名称，或切换搜索范围。');
    results.scrollTop = 0;
  }
  function openSearch(event) {
    if (dialog.open) { input.focus(); return; }
    restoreFocus = event && event.currentTarget === opener ? opener : document.activeElement;
    jumpTarget = null;
    if (feedback) feedback.textContent = '';
    renderResults();
    dialog.showModal();
    input.focus();
  }
  opener.hidden = false;
  opener.addEventListener('click', openSearch);
  input.addEventListener('input', function (event) { if (!event.isComposing) renderResults(); });
  input.addEventListener('compositionend', renderResults);
  clear.addEventListener('click', function () { input.value = ''; renderResults(); input.focus(); });
  scope.addEventListener('change', function () { renderResults(); input.focus(); });
  input.addEventListener('keydown', function (event) {
    if (event.isComposing || event.keyCode === 229) return;
    var first = results.querySelector('a');
    if (event.key === 'ArrowDown' && first) { event.preventDefault(); first.focus(); }
    if (event.key === 'Enter' && first) { event.preventDefault(); first.click(); }
  });
  results.addEventListener('keydown', function (event) {
    var links = Array.from(results.querySelectorAll('a'));
    var index = links.indexOf(document.activeElement);
    if (index < 0) return;
    if (event.key === 'ArrowDown') { event.preventDefault(); links[Math.min(index + 1, links.length - 1)].focus(); }
    if (event.key === 'ArrowUp') { event.preventDefault(); if (index) links[index - 1].focus(); else input.focus(); }
  });
  dialog.querySelector('[data-close]').addEventListener('click', function () { dialog.close(); });
  dialog.addEventListener('keydown', function (event) {
    if (isCloseKey(event)) { event.preventDefault(); event.stopPropagation(); dialog.close(); }
  });
  dialog.addEventListener('click', function (event) {
    var rect = dialog.getBoundingClientRect();
    if (event.target === dialog && (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom)) dialog.close();
  });
  dialog.addEventListener('close', function () {
    if (jumpTarget) jumpTarget.focus({preventScroll: true});
    else if (restoreFocus && restoreFocus.isConnected) restoreFocus.focus({preventScroll: true});
  });
  document.addEventListener('keydown', function (event) {
    if (!isSearchKey(event, event.target.isContentEditable || !!event.target.closest('input, textarea, select'), !!document.querySelector('dialog[open]'))) return;
    event.preventDefault();
    openSearch();
  });

  var copy = document.querySelector('[data-api-copy]');
  var feedback = document.querySelector('[data-api-feedback]');
  window.addEventListener('hashchange', function () { feedback.textContent = ''; });
  copy.hidden = false;
  copy.addEventListener('click', async function () {
    try {
      await navigator.clipboard.writeText(window.location.href);
      feedback.textContent = en ? 'Link copied' : '链接已复制';
    } catch (error) {
      feedback.textContent = en ? 'Unable to copy. Copy the URL from the address bar.' : '无法复制，请从地址栏复制链接。';
    }
  });
})();
