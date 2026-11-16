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
  function declarationKind(title) {
    if (/^const\s/.test(title)) return 'constant';
    if (/^(?:struct@?|enum)\s/.test(title)) return 'type';
    return /^\(/.test(title) ? 'method' : 'function';
  }
  if (typeof module === 'object' && module.exports) module.exports = {normalize: normalize, prepare: prepare, search: search, isSearchKey: isSearchKey, isCloseKey: isCloseKey, declarationKind: declarationKind};
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
  // Share one prepared index between the inline explorer and global search.
  function pageSymbols() {
    if (symbols) return symbols;
    symbols = prepare(articles.map(function (article) {
      var heading = article.querySelector('h2');
      var signature = article.querySelector('pre code');
      var purpose = article.querySelector('h3 + p');
      return {title: heading.textContent.trim(), kind: declarationKind(heading.textContent.trim()), detail: signature ? signature.textContent.trim().split('\n')[0] : '',
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

  // Inline discovery complements the global search. Native package links and
  // declaration anchors remain usable when scripts are unavailable.
  var catalog = main.querySelector('.api-catalog');
  if (catalog) {
    var catalogQuery = catalog.querySelector('#api-catalog-query');
    var catalogClear = catalog.querySelector('[data-api-catalog-clear]');
    var catalogStatus = catalog.querySelector('[data-api-catalog-status]');
    var catalogEmpty = catalog.querySelector('[data-api-catalog-empty]');
    var categoryLinks = Array.from(catalog.querySelectorAll('.api-section-nav a'));
    var category = 'all';
    var catalogSections = Array.from(catalog.querySelectorAll('.api-section')).map(function (section) {
      var topics = Array.from(section.querySelectorAll('.api-topic')).map(function (topic) {
        var label = topic.querySelector('summary').textContent;
        var rows = Array.from(topic.querySelectorAll('.api-package-list > li')).map(function (row) {
          return {node: row, search: normalize(row.querySelector('a').textContent + ' ' + label)};
        });
        var more = document.createElement('button');
        more.type = 'button';
        more.className = 'api-topic-more';
        var model = {node: topic, rows: rows, more: more, expanded: false, open: topic.open};
        more.addEventListener('click', function () { model.expanded = !model.expanded; renderCatalog(); });
        topic.appendChild(more);
        return model;
      });
      return {node: section, topics: topics};
    });
    var wasSearching = false;
    function renderCatalog() {
      var terms = normalize(catalogQuery.value).split(' ').filter(Boolean);
      var searching = !!terms.length;
      var total = 0;
      catalogSections.forEach(function (section) {
        var selected = category === 'all' || category === section.node.id;
        var sectionCount = 0;
        section.topics.forEach(function (topic) {
          if (searching && !wasSearching) topic.open = topic.node.open;
          if (searching) topic.node.open = true;
          else if (wasSearching) topic.node.open = topic.open;
          var count = 0;
          topic.rows.forEach(function (row) {
            var matches = terms.every(function (term) { return row.search.includes(term); });
            row.node.hidden = !matches || (!searching && !topic.expanded && count >= 4);
            if (matches) count++;
          });
          topic.node.hidden = !count;
          topic.more.hidden = searching || topic.rows.length <= 4;
          topic.more.textContent = topic.expanded ? (en ? 'Show fewer' : '收起列表') :
            (en ? 'View all ' + topic.rows.length + ' packages' : '查看全部 ' + topic.rows.length + ' 个包');
          topic.more.setAttribute('aria-expanded', String(topic.expanded));
          sectionCount += count;
        });
        section.node.hidden = !selected || !sectionCount;
        // Supporting UI imagery and widget links are not package search results.
        Array.from(section.node.children).forEach(function (child) {
          if (child.matches('h3, .api-widget-topics, .api-ui-capture')) child.hidden = searching;
        });
        if (selected) total += sectionCount;
      });
      categoryLinks.forEach(function (link) {
        var current = (link.hasAttribute('data-api-all') ? 'all' : link.hash.slice(1)) === category;
        if (current) link.setAttribute('aria-current', 'true');
        else link.removeAttribute('aria-current');
      });
      wasSearching = searching;
      catalogEmpty.hidden = total > 0;
      catalogClear.disabled = !catalogQuery.value;
      catalogStatus.textContent = en ? total + ' packages' + (searching ? ' found' : ' · Browse by topic below') :
        (searching ? '找到 ' + total + ' 个包' : total + ' 个包 · 按下方主题浏览');
    }
    categoryLinks.forEach(function (link) {
      link.addEventListener('click', function (event) {
        if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        category = link.hasAttribute('data-api-all') ? 'all' : link.hash.slice(1);
        history.replaceState(null, '', link.hash);
        renderCatalog();
      });
    });
    function catalogHash() {
      category = catalogSections.some(function (section) { return '#' + section.node.id === location.hash; }) ? location.hash.slice(1) : 'all';
      renderCatalog();
    }
    catalogQuery.addEventListener('input', function (event) { if (!event.isComposing) renderCatalog(); });
    catalogQuery.addEventListener('compositionend', renderCatalog);
    catalogClear.addEventListener('click', function () { catalogQuery.value = ''; renderCatalog(); catalogQuery.focus(); });
    window.addEventListener('hashchange', catalogHash);
    catalog.querySelector('[data-api-catalog-search]').hidden = false;
    catalogHash();
  }

  if (articles.length) {
    var overview = document.createElement('section');
    overview.className = 'api-overview';
    overview.id = 'api-overview';
    overview.setAttribute('aria-labelledby', 'api-overview-title');
    overview.innerHTML = '<div class="api-overview-heading"><div><h2 id="api-overview-title">' +
      (en ? 'Explore declarations' : '声明速览') + '</h2><p>' +
      (en ? 'Find a name, then open its signature, parameters and usage.' : '先找到名称，再查看签名、参数与用法。') +
      '</p></div><a class="api-overview-guide"></a></div>' +
      '<label class="api-overview-label" for="api-symbol-query">' + (en ? 'Filter declarations' : '筛选本包声明') + '</label>' +
      '<div class="api-catalog-input"><i class="xi xi-search" aria-hidden="true"></i>' +
      '<input id="api-symbol-query" type="search" autocomplete="off" spellcheck="false" placeholder="' +
      (en ? 'Name or purpose, e.g. split' : '输入名称或用途，例如 split') + '"><button type="button" data-symbol-clear>' +
      (en ? 'Clear' : '清空') + '</button></div><div class="api-kind-filters" role="group" aria-label="' +
      (en ? 'Declaration kind' : '声明类型') + '"></div><p class="api-symbol-count" role="status" aria-live="polite"></p>' +
      '<ul class="api-symbol-list" aria-label="' + (en ? 'Declarations' : '声明列表') + '"></ul>' +
      '<button type="button" class="api-symbol-more">' + (en ? 'Show more declarations' : '显示更多声明') + '</button>';
    var guide = overview.querySelector('.api-overview-guide');
    var guideTarget = main.querySelector('#quickstart, #examples');
    if (guideTarget) {
      guide.href = '#' + guideTarget.id;
      guide.textContent = en ? 'Usage examples →' : '用法示例 →';
    } else guide.remove();
    var meta = main.querySelectorAll(':scope > .meta');
    (meta.length ? meta[meta.length - 1] : main.querySelector('h1')).after(overview);
    var symbolQuery = overview.querySelector('input');
    var symbolClear = overview.querySelector('[data-symbol-clear]');
    var symbolList = overview.querySelector('ul');
    var symbolCount = overview.querySelector('[role="status"]');
    var symbolMore = overview.querySelector('.api-symbol-more');
    var kindFilters = overview.querySelector('.api-kind-filters');
    var selectedKind = 'all';
    var symbolLimit = 60;
    var kindLabels = en ? {all: 'All', function: 'Functions', method: 'Methods', type: 'Types', constant: 'Constants'} :
      {all: '全部', function: '函数', method: '方法', type: '类型', constant: '常量'};
    Object.keys(kindLabels).forEach(function (kind) {
      var count = pageSymbols().filter(function (entry) { return kind === 'all' || entry.kind === kind; }).length;
      if (!count) return;
      var button = document.createElement('button');
      button.type = 'button';
      button.dataset.kind = kind;
      button.textContent = kindLabels[kind] + ' ' + count;
      button.addEventListener('click', function () { selectedKind = kind; symbolLimit = 60; renderSymbols(); });
      kindFilters.appendChild(button);
    });
    function renderSymbols() {
      var entries = pageSymbols().filter(function (entry) { return selectedKind === 'all' || entry.kind === selectedKind; });
      var found = search(entries, symbolQuery.value, symbolLimit);
      symbolList.replaceChildren();
      found.items.forEach(function (entry) {
        var item = document.createElement('li');
        var link = document.createElement('a');
        link.href = entry.href;
        var badge = document.createElement('span');
        badge.className = 'api-kind';
        badge.dataset.kind = entry.kind;
        badge.textContent = kindLabels[entry.kind];
        var name = document.createElement('code');
        name.textContent = entry.title;
        var purpose = document.createElement('span');
        purpose.className = 'api-symbol-purpose';
        purpose.textContent = entry.context || entry.detail;
        link.append(badge, name, purpose);
        link.addEventListener('click', function () { entry.target.focus({preventScroll: true}); });
        item.appendChild(link);
        symbolList.appendChild(item);
      });
      kindFilters.querySelectorAll('button').forEach(function (button) {
        button.setAttribute('aria-pressed', String(button.dataset.kind === selectedKind));
      });
      symbolClear.disabled = !symbolQuery.value;
      symbolMore.hidden = found.total <= symbolLimit;
      symbolCount.textContent = found.total ? (en ? found.total + ' declarations' : found.total + ' 项声明') +
        (found.total > symbolLimit ? (en ? ' · Showing ' + symbolLimit : ' · 当前显示 ' + symbolLimit + ' 项') : '') :
        (en ? 'No matches. Try another keyword or select All.' : '没有匹配的声明。试试其他关键词，或选择「全部」。');
    }
    symbolQuery.addEventListener('input', function (event) { if (!event.isComposing) { symbolLimit = 60; renderSymbols(); } });
    symbolQuery.addEventListener('compositionend', function () { symbolLimit = 60; renderSymbols(); });
    symbolClear.addEventListener('click', function () { symbolQuery.value = ''; symbolLimit = 60; renderSymbols(); symbolQuery.focus(); });
    symbolMore.addEventListener('click', function () {
      var next = symbolLimit;
      symbolLimit += 60;
      renderSymbols();
      var nextLink = symbolList.children[next] && symbolList.children[next].querySelector('a');
      if (nextLink) nextLink.focus();
    });
    renderSymbols();
    main.querySelectorAll('.api-examples .api-example[open]').forEach(function (example) { example.open = false; });
    function revealExample() {
      var target;
      try { target = document.getElementById(decodeURIComponent(location.hash.slice(1))); } catch (error) { return; }
      if (!target) return;
      for (var parent = target; parent && parent !== main; parent = parent.parentElement) {
        if (parent.matches('details')) parent.open = true;
      }
    }
    revealExample();
    window.addEventListener('hashchange', revealExample);
  }

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
