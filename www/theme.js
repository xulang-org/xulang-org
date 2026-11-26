(function () {
  // Language choice is independent of theme. Only an unprefixed home visit is automatic.
  var languageKey = 'xu-lang';
  var locationURL = new URL(window.location.href);
  var script = document.currentScript;
  var base = script ? new URL(script.src, window.location.href).pathname.replace(/\/theme\.js$/, '') : '';
  var supportedLangs = ['en', 'zh', 'zh-tw', 'ja', 'ko', 'es', 'fr', 'de', 'ru', 'pt-br'];
  function validLanguage(value) { return supportedLangs.indexOf(value) !== -1; }
  function saveLanguage(value) {
    try { localStorage.setItem(languageKey, value); } catch (e) {}
    try {
      document.cookie = languageKey + '=' + value + '; Max-Age=31536000; Path=' + (base || '/') + '; SameSite=Lax';
    } catch (e) {}
  }
  var preference = '';
  try { preference = localStorage.getItem(languageKey); } catch (e) {}
  if (!validLanguage(preference)) {
    var cookie;
    try { cookie = (document.cookie || '').match(/(?:^|;\s*)xu-lang=(en|zh|zh-tw|ja|ko|es|fr|de|ru|pt-br)(?:;|$)/); } catch (e) {}
    preference = cookie ? cookie[1] : '';
  }
  // Explicit links also work when both persistence mechanisms are blocked.
  var explicit = locationURL.searchParams.get('lang');
  if (validLanguage(explicit)) {
    preference = explicit;
    saveLanguage(explicit);
  }
  var homePath = locationURL.pathname.replace(/\/+$/, '') || '/';
  if (homePath === (base || '/') && preference !== 'en') {
    if (preference === 'zh' || (!preference && /^zh(?:-cn|-hans)?$/i.test(navigator.language || ''))) {
      window.location.replace(base + '/zh/' + locationURL.search + locationURL.hash);
    } else if (preference === 'ru' || (!preference && /^ru(?:-[a-z]+)?$/i.test(navigator.language || ''))) {
      window.location.replace(base + '/ru/' + locationURL.search + locationURL.hash);
    } else if (preference && preference !== 'en' && validLanguage(preference)) {
      window.location.replace(base + '/' + preference + '/' + locationURL.search + locationURL.hash);
    }
  }

  var key = 'xu-theme';
  try {
    var saved = localStorage.getItem(key);
    if (saved === 'light' || saved === 'dark') {
      document.documentElement.setAttribute('data-theme', saved);
    } else {
      document.documentElement.setAttribute('data-theme', 'light');
    }
  } catch (e) {}

  document.addEventListener('DOMContentLoaded', function () {
    var languageSwitch = document.getElementById('language-switch');
    if (languageSwitch) {
      languageSwitch.addEventListener('click', function () {
        var h = languageSwitch.getAttribute('hreflang');
        var choice = h === 'en' ? 'en' : (h === 'ru' ? 'ru' : 'zh');
        saveLanguage(choice);
      });
      var destination = new URL(languageSwitch.href, window.location.href);
      var h = languageSwitch.getAttribute('hreflang');
      destination.searchParams.set('lang', h === 'en' ? 'en' : (h === 'ru' ? 'ru' : 'zh'));
      languageSwitch.href = destination.href;
    }

    var langOpts = document.querySelectorAll('.lang-opt');
    langOpts.forEach(function (opt) {
      opt.addEventListener('click', function () {
        var h = opt.getAttribute('hreflang') || 'en';
        var lang = h === 'zh-CN' ? 'zh' : h.toLowerCase();
        saveLanguage(lang);
      });
    });

    // Theme toggle
    var themeBtn = document.getElementById('theme-toggle-btn');
    if (themeBtn) {
      function syncTheme() {
        var light = document.documentElement.getAttribute('data-theme') === 'light';
        themeBtn.innerHTML = light
          ? '<i class="xi xi-sun xi-gold"></i> <span>Light</span>'
          : '<i class="xi xi-moon"></i> <span>Dark</span>';
        themeBtn.setAttribute('aria-pressed', String(light));
      }
      themeBtn.addEventListener('click', function () {
        var current = document.documentElement.getAttribute('data-theme') || 'light';
        var next = current === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', next);
        try { localStorage.setItem(key, next); } catch (e) {}
        syncTheme();
      });
      syncTheme();
    }

    // Mobile navigation toggle
    var menuBtn = document.getElementById('mobile-menu-btn');
    var scrim = document.getElementById('mobile-nav-scrim');
    var siteNav = document.getElementById('site-nav');
    if (menuBtn && siteNav) {
      function setMenu(open) {
        var isOpen = typeof open === 'boolean' ? open : !document.body.classList.contains('mobile-nav-open');
        document.body.classList.toggle('mobile-nav-open', isOpen);
        menuBtn.setAttribute('aria-expanded', String(isOpen));
        menuBtn.innerHTML = isOpen
          ? '<i class="xi xi-close"></i>'
          : '<i class="xi xi-menu"></i>';
      }
      menuBtn.addEventListener('click', function () { setMenu(); });
      if (scrim) {
        scrim.addEventListener('click', function () { setMenu(false); });
      }
      siteNav.querySelectorAll('a').forEach(function (link) {
        link.addEventListener('click', function () { setMenu(false); });
      });
      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && document.body.classList.contains('mobile-nav-open')) {
          setMenu(false);
        }
      });
      window.addEventListener('resize', function () {
        if (window.innerWidth > 1100 && document.body.classList.contains('mobile-nav-open')) {
          setMenu(false);
        }
      });
    }

    // Initialize code block copy and run toolbars
    initCodeToolbars();

    // Fragment links reveal examples and FAQ answers, including bookmarks.
    function revealLinkedDetails() {
      var hash = window.location.hash || '';
      if (!hash) return;
      var target = document.getElementById(hash.slice(1));
      if (target && target.classList && (target.classList.contains('api-example') || target.classList.contains('faq-item'))) {
        target.open = true;
        if (target.classList.add) target.classList.add('is-target');
        if (typeof setTimeout === 'function') {
          setTimeout(function () {
            if (target.scrollIntoView) {
              try {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
              } catch (_) {
                target.scrollIntoView(true);
              }
            }
          }, 80);
          setTimeout(function () {
            if (target.classList.remove) target.classList.remove('is-target');
          }, 2500);
        }
      }
    }
    window.addEventListener('hashchange', revealLinkedDetails);
    revealLinkedDetails();

    // Initialize hero install tab switcher
    initHeroInstallTabs();

    // Initialize FAQ search and category filters
    initFaq();

    // Initialize global search command palette
    initGlobalSearch();
  });

  // 侧边栏菜单分组折叠/收起与滚动控制
  window.toggleSideGroup = function (btn) {
    var group = btn.closest('.side-group');
    if (!group) return;
    var isOpen = group.classList.toggle('is-open');
    btn.setAttribute('aria-expanded', String(isOpen));
  };

  window.toggleAllSideGroups = function (btn) {
    var side = btn.closest('.side');
    if (!side) return;
    var groups = side.querySelectorAll('.side-group');
    var apiGroups = side.querySelectorAll('.side-api-bucket, .side-api-topic');
    var allOpen = Array.from(groups).every(function (g) { return g.classList.contains('is-open'); }) &&
      Array.from(apiGroups).every(function (g) { return g.open; });
    var nextState = !allOpen;
    groups.forEach(function (g) {
      g.classList.toggle('is-open', nextState);
      var h = g.querySelector('button.side-h');
      if (h) h.setAttribute('aria-expanded', String(nextState));
    });
    apiGroups.forEach(function (g) { g.open = nextState; });
    side.querySelectorAll('.side-toggle-all-btn, .side-footer-btn').forEach(function (b) {
      if (b.querySelector('.xi-sliders')) b.setAttribute('data-expanded', String(nextState));
    });
  };

  window.scrollSideToTop = function (btn) {
    var side = btn.closest('.side');
    if (!side) return;
    var content = side.querySelector('.side-content') || side;
    content.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Code blocks share an editable source buffer for copying and running.
  function initCodeToolbars() {
    var isEn = document.documentElement.lang === 'en';
    var copyText = isEn ? 'Copy' : '复制';
    var copiedText = isEn ? '✓ Copied' : '✓ 已复制';
    var runText = isEn ? 'Run' : '运行';
    var runTitle = isEn ? 'Run in the browser WASM subset (MIR interpreter)' : '在浏览器 WASM 子集中运行（MIR 解释器）';
    var resultId = 0;
    var editorId = 0;

    function isCompleteProgram(value) {
      // Ignore comments and literals: mentioning an entry point is not defining it.
      var source = value.replace(/\/\/[^\n]*|\/\*[\s\S]*?\*\/|"(?:\\[\s\S]|[^"\\])*"|'(?:\\[\s\S]|[^'\\])*'|`[^`]*`/g, ' ');
      var entry = /(?:^|\n)\s*(?:pub\s+)?fn\s+main\s*\(\s*\)\s*(?:int\s*)?\{/.exec(source);
      if (!entry) return false;
      var mainBrace = entry.index + entry[0].length - 1;
      var depth = 0;
      for (var i = 0; i < source.length; i++) {
        if (i === mainBrace && depth !== 0) return false;
        if (source[i] === '{') depth++;
        if (source[i] === '}' && --depth < 0) return false;
      }
      return depth === 0;
    }

    function prepareCode(value) {
      return /(?:^|\n)\s*@main\b/.test(value) ? value : '@main\n\n' + value;
    }

    function detectBlockKind(pre, rawCode) {
      var code = pre.querySelector('code');
      var cls = ((code && code.className) || '') + ' ' + (pre.className || '');

      // Explicit class markers
      if (/\blang(?:uage)?-(?:sh|bash|shell|cmd)\b|\bblock-shell\b/.test(cls)) return 'shell';
      if (/\blang(?:uage)?-(?:c|cpp)\b|\bblock-c\b/.test(cls)) return 'c';
      if (/\blang(?:uage)?-json\b|\bblock-json\b/.test(cls)) return 'json';
      if (/\blang(?:uage)?-(?:xun|yaml)\b|\bblock-xun\b/.test(cls)) return 'xun';
      if (/\blang(?:uage)?-(?:diagram|ascii|tree)\b|\bblock-diagram\b/.test(cls)) return 'diagram';
      if (/\blang(?:uage)?-(?:output|console)\b|\bblock-output\b/.test(cls)) return 'output';
      if (/\bblock-api\b/.test(cls)) return 'api';
      if (/\blang(?:uage)?-xu\b|\bblock-xu\b/.test(cls)) return 'xu';

      if (pre.closest && pre.closest('.api-item')) return 'api';

      var lines = rawCode.split('\n');
      var firstLine = lines[0].trim();

      // Check for preceding output indicator in DOM if possible
      var parent = pre.parentNode;
      var prev = pre.previousElementSibling;
      if (!prev && parent && parent.children) {
        var children = Array.prototype.slice.call(parent.children);
        var idx = children.indexOf(pre);
        if (idx > 0) prev = children[idx - 1];
      }
      if (prev && prev.textContent) {
        var prevText = prev.textContent.trim().toLowerCase();
        if (/^(?:运行输出|输出|output|stdout|stderr)$/i.test(prevText)) {
          return 'output';
        }
      }

      // 0. Explicit or Heuristic CLI Help
      if (/\blang(?:uage)?-help\b|\bblock-help\b/.test(cls)) return 'help';
      if (/^(?:xu\s+help\b|xu\s+.*--help\b|usage:|用法:|subcommands:|options:)/i.test(firstLine)) {
        return 'help';
      }

      // Xu's standalone -> is continue, so recognize complete programs before
      // applying diagram heuristics. Explicit block markers still take priority.
      if (isCompleteProgram(rawCode)) return 'xu';

      // 1. ASCII Diagram / Layout / Flowchart / Tree / EBNF
      if (/^[+]{3,}|^[+]-+|^[|].*[|]$|^┌─|^└──|^├──/.test(firstLine)) {
        return 'diagram';
      }
      if (lines.filter(function (l) { return /^[+]-+[-+]+$/.test(l.trim()) || /^[|].*[|]$/.test(l.trim()); }).length >= 2) {
        return 'diagram';
      }
      if (lines.some(function (l) { return /^[ \t]*(?:↓|->|-->|=>|▼|▲)[ \t]*$/.test(l); })) {
        return 'diagram';
      }
      if (/^[A-Za-z0-9_.-]+\/(?:[ \t]*\n)?/.test(rawCode) && (rawCode.indexOf('├──') !== -1 || rawCode.indexOf('└──') !== -1)) {
        return 'diagram';
      }
      if (/^File\s*=\s*"@"/.test(rawCode) || (rawCode.indexOf('=') !== -1 && rawCode.indexOf('{') !== -1 && rawCode.indexOf('}') !== -1 && lines.some(function (l) { return /\.\s*$/.test(l.trim()); }))) {
        return 'diagram';
      }

      // 2. Command Output
      if (/^===\s*.*===\s*$/.test(firstLine) || /^(?:exit\s+\d+|output:\s*)/i.test(firstLine)) {
        return 'output';
      }
      if (/^[0-9\s]+$/.test(rawCode) && lines.length <= 6 && !lines.some(function (l) { return l.indexOf(';') !== -1 || l.indexOf('=') !== -1; })) {
        return 'output';
      }

      // 3. C / C++ Source Code
      if (/^#include\s+[<"]/.test(firstLine) || /\bXU_NATIVE_SYMBOL\b/.test(rawCode) || /\bxu_int\b/.test(rawCode)) {
        return 'c';
      }

      // 4. Shell / Terminal Commands
      // Note: Must match 'xu run main.xu'
      if (/^(?:xu\s+(?:run|build|test|fmt|check|doc|map|doctor|setup|install|get|init|up|update|env|--version|-v)|git\s+|curl\s+|irm\s+|wget\s+|python3?\s+|make\s+|cd\s+|mkdir\s+|clang\s+|gcc\s+|\$|npm\s+|brew\s+|cargo\s+|docker\s+|tar\s+|unzip\s+)/.test(firstLine) ||
          (lines.length === 1 && firstLine.startsWith('xu ')) ||
          /^XUPROXY=|^XU_|^export\s+/.test(firstLine)) {
        return 'shell';
      }
      if (/^#(?:\s+|$)/.test(firstLine) && lines.some(function (l) {
        return /^(?:xu\s+|python3?\s+|git\s+|curl\s+|make\s+|\$|cd\s+|clang\s+|gcc\s+)/.test(l.trim());
      })) {
        return 'shell';
      }

      // 5. JSON Manifest
      if ((firstLine === '{' || firstLine.startsWith('{')) && rawCode.endsWith('}') &&
          (rawCode.indexOf('"module"') !== -1 || rawCode.indexOf('"abi"') !== -1 || rawCode.indexOf('"slices"') !== -1)) {
        return 'json';
      }

      // 6. Xun Manifest (xu.xun)
      if (/^module:\s+/m.test(rawCode) && (rawCode.indexOf('native:') !== -1 || rawCode.indexOf('require:') !== -1 || rawCode.indexOf('version:') !== -1)) {
        return 'xun';
      }

      return 'xu';
    }

    var pres = document.querySelectorAll('main.doc pre, main.home pre, .api-item pre');
    pres.forEach(function (pre) {
      if (pre.closest('#bench-src-modal') || pre.classList.contains('xu-play-out') || pre.querySelector('.code-actions')) return;
      var code = pre.querySelector('code');
      if (!code) return;

      var rawCode = (code.textContent || '').trim();
      if (!rawCode) return;
      var editor = null;
      var editorHelp = null;
      function currentCode() { return editor ? editor.value : rawCode; }

      var kind = detectBlockKind(pre, rawCode);
      var isLocalOnly = kind === 'xu' && !!pre.closest('.xu-local-only');
      // Project previews need every file; their explicit catalog link opens the
      // complete workspace. Running just the entry file would lose its helpers.
      var isProjectPreview = !!pre.closest('.xu-project-example');
      var isRunnable = kind === 'xu' && !isLocalOnly && !isProjectPreview && isCompleteProgram(rawCode);

      var kindMeta = {
        xu: { icon: 'xi-code xi-brand', title: isEn ? 'Xu Source' : 'Xu 代码', badge: isRunnable ? '<span class="code-badge">' + (isEn ? 'WASM subset' : 'WASM 子集') + '</span>' : '' },
        api: { icon: 'xi-interface xi-brand', title: isEn ? 'API Signature' : 'API 声明', badge: '<span class="code-badge">Xu</span>' },
        shell: { icon: 'xi-terminal', title: isEn ? 'Terminal' : '终端命令', badge: '<span class="code-badge terminal-badge">SHELL</span>' },
        help: { icon: 'xi-help-circle', title: isEn ? 'Command Help & Options' : '命令帮助与参数说明', badge: '<span class="code-badge help-badge">' + (isEn ? 'HELP' : '帮助') + '</span>' },
        diagram: { icon: 'xi-flow', title: isEn ? 'Specification & Architecture' : '结构与说明图示', badge: '<span class="code-badge diagram-badge">SPEC</span>' },
        output: { icon: 'xi-terminal-box', title: isEn ? 'Output' : '运行输出', badge: '<span class="code-badge output-badge">OUTPUT</span>' },
        c: { icon: 'xi-code', title: isEn ? 'C / C++ Source' : '原生 C 源码', badge: '<span class="code-badge">C/C++</span>' },
        json: { icon: 'xi-file-code', title: isEn ? 'JSON Manifest' : 'JSON 契约清单', badge: '<span class="code-badge">JSON</span>' },
        xun: { icon: 'xi-file-code', title: isEn ? 'xu.xun Manifest' : 'xu.xun 工程清单', badge: '<span class="code-badge">Xun</span>' }
      }[kind] || { icon: 'xi-code xi-brand', title: isEn ? 'Xu Source' : 'Xu 代码', badge: '' };

      var dotsHtml = kind === 'shell'
        ? '<span class="terminal-dots" aria-hidden="true"><span class="terminal-dot dot-red"></span><span class="terminal-dot dot-yellow"></span><span class="terminal-dot dot-green"></span></span>'
        : '';

      var titleHtml = dotsHtml + '<i class="xi ' + kindMeta.icon + '"></i> <span>' + kindMeta.title + '</span>' + (kindMeta.badge ? ' ' + kindMeta.badge : '');

      var wrapper = pre.closest('.code-block-wrapper');
      var header = null;

      if (!wrapper) {
        wrapper = document.createElement('div');
        wrapper.className = 'code-block-wrapper block-kind-' + kind;
        pre.parentNode.insertBefore(wrapper, pre);

        header = document.createElement('div');
        header.className = 'code-block-header';

        var titleSpan = document.createElement('span');
        titleSpan.className = 'code-block-header-title';
        titleSpan.innerHTML = titleHtml;
        header.appendChild(titleSpan);

        wrapper.appendChild(header);
        wrapper.appendChild(pre);
      } else {
        wrapper.classList.add('block-kind-' + kind);
        header = wrapper.querySelector('.code-block-header');
        if (!header) {
          header = document.createElement('div');
          header.className = 'code-block-header';
          wrapper.insertBefore(header, wrapper.firstChild);
        }
        var titleSpan = header.querySelector('.code-block-header-title');
        if (!titleSpan) {
          titleSpan = document.createElement('span');
          titleSpan.className = 'code-block-header-title';
          titleSpan.innerHTML = titleHtml;
          header.insertBefore(titleSpan, header.firstChild);
        }
      }

      if (header.querySelector('.code-actions')) return;

      if (isLocalOnly) {
        var localHelp = document.createElement('div');
        localHelp.className = 'code-editor-help code-local-help';
        localHelp.innerHTML = isEn
          ? '<span>Use the local Xu SDK with the complete project and its dependencies. From the project directory, run <code>xu run main.xu</code> (replace main.xu with the entry file).</span>'
          : '<span>使用本地 Xu SDK，保留完整工程及其依赖。在工程目录运行 <code>xu run main.xu</code>（将 main.xu 替换为入口文件）。</span>';
        wrapper.insertBefore(localHelp, pre);
      }

      var actions = document.createElement('div');
      actions.className = 'code-actions';

      var copyLabel = copyText;
      if (kind === 'shell') copyLabel = isEn ? 'Copy' : '复制命令';
      else if (kind === 'help') copyLabel = isEn ? 'Copy' : '复制说明';

      // 复制按钮
      var copyBtn = document.createElement('button');
      copyBtn.type = 'button';
      copyBtn.className = 'code-action-btn code-copy-btn';
      copyBtn.innerHTML = '<i class="xi xi-copy"></i> <span>' + copyLabel + '</span>';
      copyBtn.title = kind === 'shell' ? (isEn ? 'Copy command' : '复制终端命令') : (isEn ? 'Copy code' : '复制代码');
      copyBtn.addEventListener('click', function () {
        navigator.clipboard.writeText(currentCode()).then(function () {
          copyBtn.classList.add('copied');
          copyBtn.innerHTML = '<i class="xi xi-check"></i> <span>' + copiedText + '</span>';
          setTimeout(function () {
            copyBtn.classList.remove('copied');
            copyBtn.innerHTML = '<i class="xi xi-copy"></i> <span>' + copyLabel + '</span>';
          }, 1500);
        });
      });
      actions.appendChild(copyBtn);

      // Only complete browser examples receive edit and run actions.
      if (isRunnable) {
        var editBtn = document.createElement('button');
        editBtn.type = 'button';
        editBtn.className = 'code-action-btn code-edit-btn';
        editBtn.innerHTML = '<i class="xi xi-edit"></i> <span>' + (isEn ? 'Edit' : '编辑') + '</span>';
        editBtn.title = isEn ? 'Edit code on this page' : '在当前页面编辑代码';
        editBtn.setAttribute('aria-pressed', 'false');
        editBtn.addEventListener('click', function () {
          if (!editor) {
            editor = document.createElement('textarea');
            editor.className = 'code-block-editor';
            editor.id = 'code-editor-' + (++editorId);
            editor.value = rawCode;
            editor.rows = Math.min(24, Math.max(6, rawCode.split('\n').length + 1));
            editor.spellcheck = false;
            editor.wrap = 'off';
            editor.hidden = true;
            editor.setAttribute('autocapitalize', 'off');
            editor.setAttribute('autocomplete', 'off');
            editor.setAttribute('aria-label', isEn ? 'Xu code editor' : 'Xu 代码编辑器');
            editorHelp = document.createElement('div');
            editorHelp.className = 'code-editor-help';
            editorHelp.id = editor.id + '-help';
            var isTouchScreen = typeof window !== 'undefined' && typeof window.innerWidth === 'number' && (window.innerWidth <= 640 || /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent || ''));
            editorHelp.innerHTML = '<i class="xi xi-info-circle"></i> <span>' +
              (isTouchScreen
                ? (isEn ? 'Run your changes with Run.' : '修改后点击「运行」。')
                : (isEn ? 'Run your changes with Run or Ctrl / Cmd + Enter.' : '修改后点击「运行」，或按 Ctrl / Cmd + Enter。')) +
              '</span>';
            editor.setAttribute('aria-describedby', editorHelp.id);
            editor.addEventListener('keydown', function (event) {
              if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
                event.preventDefault();
                if (!runBtn.disabled) runBtn.click();
              }
            });
            wrapper.insertBefore(editor, pre);
            wrapper.insertBefore(editorHelp, pre);
            editBtn.setAttribute('aria-controls', editor.id);
          }
          var editing = editor.hidden;
          editor.hidden = editorHelp.hidden = !editing;
          pre.hidden = editing;
          editBtn.setAttribute('aria-pressed', String(editing));
          editBtn.innerHTML = editing
            ? '<i class="xi xi-check"></i> <span>' + (isEn ? 'Done' : '完成') + '</span>'
            : '<i class="xi xi-edit"></i> <span>' + (isEn ? 'Edit' : '编辑') + '</span>';
          editBtn.title = editing ? (isEn ? 'Finish editing' : '完成编辑') : (isEn ? 'Edit code on this page' : '在当前页面编辑代码');
          if (editing) editor.focus();
          else if (code.textContent !== editor.value) code.textContent = editor.value;
        });
        actions.appendChild(editBtn);

        var runBtn = document.createElement('button');
        runBtn.type = 'button';
        runBtn.className = 'code-action-btn code-run-btn';
        runBtn.innerHTML = '<i class="xi xi-play"></i> <span>' + runText + '</span>';
        runBtn.title = runTitle;
        runBtn.setAttribute('aria-expanded', 'false');
        var runInline = null;
        var runSource = {value: ''};
        function prefetch() {
          if (window.XuPlay && typeof window.XuPlay.warmup === 'function') {
            window.XuPlay.warmup();
          }
        }
        runBtn.addEventListener('mouseenter', prefetch);
        runBtn.addEventListener('focus', prefetch);
        if (editBtn) {
          editBtn.addEventListener('mouseenter', prefetch);
          editBtn.addEventListener('focus', prefetch);
        }
        if (typeof window !== 'undefined' && typeof window.IntersectionObserver === 'function') {
          try {
            var observer = new window.IntersectionObserver(function (entries) {
              entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                  prefetch();
                  observer.unobserve(entry.target);
                }
              });
            }, {rootMargin: '200px 0px'});
            observer.observe(wrapper);
          } catch (_) {}
        }
        runBtn.addEventListener('click', function () {
          runSource.value = prepareCode(currentCode());
          if (!runInline) {
            var result = document.createElement('div');
            result.className = 'code-run-result';
            result.id = 'code-run-result-' + (++resultId);
            var resultHeader = document.createElement('div');
            resultHeader.className = 'code-run-result-header';
            var resultTitle = document.createElement('span');
            resultTitle.textContent = isEn ? 'Output' : '运行结果';
            var meta = document.createElement('span');
            meta.className = 'xu-play-meta';
            meta.setAttribute('role', 'status');
            resultHeader.appendChild(resultTitle);
            resultHeader.appendChild(meta);
            var output = document.createElement('pre');
            output.className = 'xu-play-out';
            output.setAttribute('aria-label', isEn ? 'Execution output' : '执行输出');
            output.setAttribute('aria-live', 'polite');
            output.tabIndex = 0;
            result.appendChild(resultHeader);
            result.appendChild(output);
            wrapper.appendChild(result);
            runBtn.setAttribute('aria-controls', result.id);
            runBtn.setAttribute('aria-expanded', 'true');

            runInline = window.XuPlay.bind({source: runSource, button: runBtn, output: output, meta: meta});
          }
          runInline();
        });
        actions.appendChild(runBtn);
      }

      header.appendChild(actions);
    });
  }

  function initHeroInstallTabs() {
    if (typeof document.querySelectorAll !== 'function') return;
    var installs = document.querySelectorAll('.hero-install');
    if (!installs || !installs.length) return;
    var isWin = /windows|win32|win64/i.test((typeof navigator !== 'undefined' && (navigator.userAgent || navigator.platform)) || '');
    installs.forEach(function (box) {
      if (!box || typeof box.querySelectorAll !== 'function') return;
      var tabs = box.querySelectorAll('.hero-install-tab');
      var panes = box.querySelectorAll('.hero-install-pane');
      if (!tabs || !panes) return;
      function switchTab(target) {
        tabs.forEach(function (tab) {
          var active = tab.getAttribute('data-tab') === target;
          tab.classList.toggle('is-active', active);
          tab.setAttribute('aria-selected', String(active));
        });
        panes.forEach(function (pane) {
          var active = pane.getAttribute('data-pane') === target;
          pane.classList.toggle('is-active', active);
        });
      }
      tabs.forEach(function (tab) {
        if (typeof tab.addEventListener === 'function') {
          tab.addEventListener('click', function () {
            var t = tab.getAttribute('data-tab');
            if (t) switchTab(t);
          });
        }
      });
      if (isWin) {
        switchTab('win');
      }
    });
  }

  function initFaq() {
    if (typeof document === 'undefined' || typeof document.querySelectorAll !== 'function') return;
    var faqList = document.querySelector ? document.querySelector('.faq-list') : null;
    if (!faqList) return;
    var faqItems = faqList.querySelectorAll ? faqList.querySelectorAll('.faq-item') : null;
    if (!faqItems || !faqItems.length) return;

    var docLang = (document.documentElement && document.documentElement.lang) || 'en';
    var isZh = docLang.indexOf('zh') === 0;
    var activeCategory = 'all';
    var searchQuery = '';

    var catLabels = {
      lang: isZh ? '语言与内存' : (docLang === 'ja' ? '言語とメモリ' : (docLang === 'ko' ? '언어 및 메모리' : 'Language & Memory')),
      os: isZh ? '操作系统与内核' : (docLang === 'ja' ? 'OS・カーネル' : (docLang === 'ko' ? '운영체제 및 커널' : 'OS & Kernel')),
      ui: isZh ? '原生桌面 UI' : (docLang === 'ja' ? 'デスクトップ UI' : (docLang === 'ko' ? '데스크톱 UI' : 'Desktop UI')),
      tools: isZh ? '工具链与生态' : (docLang === 'ja' ? 'ツールチェーン' : (docLang === 'ko' ? '툴체인 및 생태계' : 'Toolchain & Ecosystem')),
      xacp: isZh ? 'XACP 协议' : 'XACP Protocol'
    };

    faqItems.forEach(function (item) {
      var id = item.id;
      var cat = item.getAttribute ? item.getAttribute('data-category') : '';
      var answer = item.querySelector ? item.querySelector('.faq-answer') : null;
      if (!answer) return;

      var existingMeta = answer.querySelector ? answer.querySelector('.faq-item-meta') : null;
      if (!existingMeta && (cat || id)) {
        var meta = document.createElement('div');
        meta.className = 'faq-item-meta';

        if (cat && catLabels[cat]) {
          var pill = document.createElement('span');
          pill.className = 'faq-cat-pill';
          pill.textContent = catLabels[cat];
          meta.appendChild(pill);
        }

        if (id) {
          var copyBtn = document.createElement('button');
          copyBtn.type = 'button';
          copyBtn.className = 'faq-copy-anchor';
          copyBtn.title = isZh ? '复制问题直链' : 'Copy link to question';
          if (copyBtn.setAttribute) {
            copyBtn.setAttribute('aria-label', isZh ? '复制问题直链' : 'Copy link to question');
          }
          copyBtn.innerHTML = '<i class="xi xi-link"></i> <span>' + (isZh ? '直链' : 'Link') + '</span>';
          copyBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            var targetHash = '#' + id;
            var origin = (window.location && window.location.origin) || '';
            var pathname = (window.location && window.location.pathname) || '';
            var fullUrl = origin + pathname + targetHash;
            var copied = false;
            if (typeof navigator !== 'undefined' && navigator.clipboard && navigator.clipboard.writeText) {
              navigator.clipboard.writeText(fullUrl).then(function () {
                if (copyBtn.classList && copyBtn.classList.add) copyBtn.classList.add('is-copied');
                copyBtn.innerHTML = '<i class="xi xi-check"></i> <span>' + (isZh ? '已复制' : 'Copied') + '</span>';
                if (typeof setTimeout === 'function') {
                  setTimeout(function () {
                    if (copyBtn.classList && copyBtn.classList.remove) copyBtn.classList.remove('is-copied');
                    copyBtn.innerHTML = '<i class="xi xi-link"></i> <span>' + (isZh ? '直链' : 'Link') + '</span>';
                  }, 2000);
                }
              }).catch(function () {
                if (window.location) window.location.hash = id;
              });
              copied = true;
            }
            if (!copied && window.location) {
              window.location.hash = id;
            }
          });
          meta.appendChild(copyBtn);
        }

        if (answer.insertBefore && answer.firstChild) {
          answer.insertBefore(meta, answer.firstChild);
        } else if (answer.appendChild) {
          answer.appendChild(meta);
        }
      }
    });

    var searchInput = document.getElementById('faq-search');
    var clearBtn = document.getElementById('faq-search-clear');
    var countBadge = document.getElementById('faq-count');
    var expandAllBtn = document.getElementById('faq-expand-all');
    var collapseAllBtn = document.getElementById('faq-collapse-all');
    var catButtons = document.querySelectorAll('.faq-cat-btn');
    var sortSelect = document.getElementById('faq-sort');
    var defaultItems = Array.prototype.slice.call(faqItems);

    function applySort(mode) {
      var sorted = defaultItems.slice();
      if (mode === 'os-first') {
        sorted.sort(function (a, b) {
          var catA = (a.getAttribute && a.getAttribute('data-category')) === 'os' ? 0 : 1;
          var catB = (b.getAttribute && b.getAttribute('data-category')) === 'os' ? 0 : 1;
          if (catA !== catB) return catA - catB;
          return defaultItems.indexOf(a) - defaultItems.indexOf(b);
        });
      } else if (mode === 'ai-first') {
        sorted.sort(function (a, b) {
          var catA = (a.getAttribute && a.getAttribute('data-category')) === 'ai' ? 0 : 1;
          var catB = (b.getAttribute && b.getAttribute('data-category')) === 'ai' ? 0 : 1;
          if (catA !== catB) return catA - catB;
          return defaultItems.indexOf(a) - defaultItems.indexOf(b);
        });
      } else if (mode === 'category') {
        var catPriority = { lang: 1, os: 2, ai: 3, ui: 4, tools: 5, xacp: 6 };
        sorted.sort(function (a, b) {
          var ca = (a.getAttribute && a.getAttribute('data-category')) || '';
          var cb = (b.getAttribute && b.getAttribute('data-category')) || '';
          var pA = catPriority[ca] || 99;
          var pB = catPriority[cb] || 99;
          if (pA !== pB) return pA - pB;
          return defaultItems.indexOf(a) - defaultItems.indexOf(b);
        });
      } else if (mode === 'title') {
        sorted.sort(function (a, b) {
          var hA = a.querySelector ? a.querySelector('h3') : null;
          var hB = b.querySelector ? b.querySelector('h3') : null;
          var tA = (hA ? hA.textContent : '').trim();
          var tB = (hB ? hB.textContent : '').trim();
          return tA.localeCompare ? tA.localeCompare(tB, docLang) : (tA > tB ? 1 : (tA < tB ? -1 : 0));
        });
      }

      var frag = document.createDocumentFragment();
      sorted.forEach(function (item) {
        frag.appendChild(item);
      });
      var emptyEl = document.getElementById('faq-empty-state');
      if (emptyEl && emptyEl.parentNode === faqList) {
        frag.appendChild(emptyEl);
      }
      faqList.appendChild(frag);
      filterFaq();
    }

    if (sortSelect) {
      sortSelect.addEventListener('change', function () {
        var mode = sortSelect.value || 'default';
        applySort(mode);
        try {
          if (window.history && window.history.replaceState && window.location) {
            var url = new URL(window.location.href);
            if (mode === 'default') {
              url.searchParams.delete('sort');
            } else {
              url.searchParams.set('sort', mode);
            }
            window.history.replaceState(null, '', url.toString());
          }
        } catch (e) {}
      });

      try {
        if (window.location && window.location.search) {
          var match = /[?&]sort=([a-z-]+)/i.exec(window.location.search);
          if (match && match[1]) {
            var initialSort = match[1].toLowerCase();
            if (['default', 'os-first', 'ai-first', 'category', 'title'].indexOf(initialSort) !== -1) {
              sortSelect.value = initialSort;
              applySort(initialSort);
            }
          }
        }
      } catch (e) {}
    }

    function filterFaq() {
      var visibleCount = 0;
      var q = searchQuery.trim().toLowerCase();

      faqItems.forEach(function (item) {
        var cat = (item.getAttribute && item.getAttribute('data-category')) || '';
        var matchCat = activeCategory === 'all' || cat === activeCategory;
        var text = (item.textContent || '').toLowerCase();
        var matchQuery = !q || text.indexOf(q) !== -1;

        if (matchCat && matchQuery) {
          if (item.style) item.style.display = '';
          visibleCount++;
          if (q.length >= 2) {
            item.open = true;
          }
        } else {
          if (item.style) item.style.display = 'none';
        }
      });

      if (countBadge) {
        if (isZh) {
          countBadge.textContent = '显示 ' + visibleCount + ' / ' + faqItems.length + ' 个问题';
        } else {
          countBadge.textContent = 'Showing ' + visibleCount + ' of ' + faqItems.length + ' questions';
        }
      }

      var emptyEl = document.getElementById('faq-empty-state');
      if (visibleCount === 0) {
        if (!emptyEl) {
          emptyEl = document.createElement('div');
          emptyEl.id = 'faq-empty-state';
          emptyEl.className = 'faq-empty-state';
          emptyEl.innerHTML = '<i class="xi xi-search" style="font-size:2rem;margin-bottom:0.75rem;display:block;opacity:0.5;"></i><p>' +
            (isZh ? '未找到包含 “' + searchQuery + '” 的相关问题，请尝试换用其他关键词。' : 'No questions found matching "' + searchQuery + '". Try another keyword.') + '</p>';
          if (faqList.appendChild) faqList.appendChild(emptyEl);
        }
        if (emptyEl && emptyEl.style) emptyEl.style.display = '';
      } else if (emptyEl && emptyEl.style) {
        emptyEl.style.display = 'none';
      }
    }

    if (searchInput) {
      searchInput.addEventListener('input', function () {
        searchQuery = searchInput.value || '';
        if (clearBtn) clearBtn.hidden = !searchQuery;
        filterFaq();
      });
      if (clearBtn) {
        clearBtn.addEventListener('click', function () {
          searchInput.value = '';
          searchQuery = '';
          clearBtn.hidden = true;
          if (searchInput.focus) searchInput.focus();
          filterFaq();
        });
      }
    }

    if (expandAllBtn) {
      expandAllBtn.addEventListener('click', function () {
        faqItems.forEach(function (item) {
          if (!item.style || item.style.display !== 'none') {
            item.open = true;
          }
        });
      });
    }

    if (collapseAllBtn) {
      collapseAllBtn.addEventListener('click', function () {
        faqItems.forEach(function (item) {
          item.open = false;
        });
      });
    }

    if (catButtons && catButtons.length) {
      catButtons.forEach(function (btn) {
        btn.addEventListener('click', function () {
          catButtons.forEach(function (b) {
            if (b.classList && b.classList.remove) b.classList.remove('is-active');
            if (b.setAttribute) b.setAttribute('aria-selected', 'false');
          });
          if (btn.classList && btn.classList.add) btn.classList.add('is-active');
          if (btn.setAttribute) btn.setAttribute('aria-selected', 'true');
          activeCategory = (btn.getAttribute && btn.getAttribute('data-cat')) || 'all';
          filterFaq();
        });
      });
    }
  }

  function initGlobalSearch() {
    if (typeof document === 'undefined' || typeof document.createElement !== 'function' || !document.body) return;
    var isEn = document.documentElement.lang === 'en';
    var prefix = isEn ? '' : '/zh';

    var staticEntries = [
      { title: isEn ? 'Get Started' : '起步指南', category: 'doc', desc: isEn ? 'Introduction, install, and first program' : '从零开始安装 Xu、编写首个程序与核心概念概览', href: prefix + '/docs/start/' },
      { title: isEn ? 'Installation' : '安装与工具链', category: 'doc', desc: isEn ? 'Automated scripts and binary downloads' : 'macOS, Linux, Windows 自动化安装脚本与二进制发行包', href: prefix + '/docs/install/' },
      { title: isEn ? 'FAQ' : '常见问题解答', category: 'doc', desc: isEn ? 'Memory safety, zero-GC, concurrency and FFI' : '所有权与借用检查、并发模型、零GC、原生安全边界等高频疑问', href: prefix + '/docs/faq/' },
      { title: isEn ? 'CLI Reference' : '命令行工具集', category: 'doc', desc: isEn ? 'xu build, run, check, test, fmt, lsp, native' : 'xu build, run, check, test, fmt, lsp 及 native 模块命令参数详解', href: prefix + '/docs/cli/' },
      { title: isEn ? 'Modules & Dependencies' : '模块与依赖管理', category: 'doc', desc: isEn ? 'xu.xun manifest, xu.lock, vendor and xu install' : 'xu.xun 清单配置、SemVer 版本管理、xu install 与 xu get', href: prefix + '/docs/modules/' },
      { title: isEn ? 'External Packages' : '官方扩展包生态', category: 'doc', desc: isEn ? 'Redis, MySQL, SQLite, Postgres, Kafka, Mongo' : 'Redis, MySQL, SQLite, Postgres, Kafka, MongoDB 等扩展库', href: prefix + '/docs/packages/' },
      { title: isEn ? 'Native Modules & C FFI' : '原生模块与 C 互操作', category: 'doc', desc: isEn ? '.xulib packaging, C FFI boundaries, linking' : '.xulib 打包规范、C FFI 边界、跨架构切片构建', href: prefix + '/docs/native/' },
      { title: isEn ? 'Desktop UI & WebView' : '原生桌面 UI 与 WebView', category: 'doc', desc: isEn ? 'Retained-mode layout, GPU canvas, components' : '自研保留模式组件架构、GPU 加速画布、WebView 嵌入式集成', href: prefix + '/docs/ui/' },
      { title: isEn ? 'Mobile Apps' : '移动端应用开发', category: 'doc', desc: isEn ? 'iOS & Android targets, touch interactions' : 'iOS 与 Android 跨平台编译、触控事件与移动端界面开发', href: prefix + '/docs/phone/' },
      { title: isEn ? 'VS Code & Cursor' : 'IDE 插件支持', category: 'doc', desc: isEn ? 'Official extension, LSP server, syntax highlighting' : '官方 IDE 插件、LSP 语言服务、语法高亮与 LLDB 调试', href: prefix + '/docs/vscode/' },

      { title: isEn ? '01 Program Skeleton' : '01 程序骨架', category: 'tutorial', desc: isEn ? 'hello world, @main entry, println and << return' : 'hello world, @main 入口, println 与 << 返回语句', href: prefix + '/docs/tutorial/01/' },
      { title: isEn ? '02 Bindings & Constants' : '02 绑定与常量', category: 'tutorial', desc: isEn ? 'name := val binding, $name := reassignment' : 'name := value 声明, $name := value 重新赋值, const 规则', href: prefix + '/docs/tutorial/02/' },
      { title: isEn ? '03 Control Flow' : '03 控制流', category: 'tutorial', desc: isEn ? 'if/else, for loops, <- break, -> continue' : 'if/else, for 循环, <- break, -> continue', href: prefix + '/docs/tutorial/03/' },
      { title: isEn ? '04 Functions & Errors' : '04 函数与错误', category: 'tutorial', desc: isEn ? 'Parameter types, << return, >>> throw, >>> (err)' : '函数参数 name Type, 返回值, >>> 抛出与 >>> (err) 错误捕获', href: prefix + '/docs/tutorial/04/' },
      { title: isEn ? '05 Error Handling' : '05 错误处理模式', category: 'tutorial', desc: isEn ? 'Typed errors, err.msg(), error propagation' : '带负载错误, err.msg(), 错误链与确定性传播', href: prefix + '/docs/tutorial/05/' },
      { title: isEn ? '06 Ownership & Borrowing' : '06 所有权与借用', category: 'tutorial', desc: isEn ? '&T shared borrow, $&T exclusive borrow, RAII' : '只读借用 &T, 独占借用 $&T, RAII 确定性资源释放, 零GC', href: prefix + '/docs/tutorial/06/' },
      { title: isEn ? '07 Arrays & Slices' : '07 数组与切片', category: 'tutorial', desc: isEn ? 'Fixed-size arrays, dynamic slices, slicing' : '固定长度数组, 动态切片, 切片操作与遍历', href: prefix + '/docs/tutorial/07/' },
      { title: isEn ? '08 Enum & Matching' : '08 枚举与匹配', category: 'tutorial', desc: isEn ? 'enum declarations, match pattern matching' : 'enum 声明, match 分支模式匹配', href: prefix + '/docs/tutorial/08/' },
      { title: isEn ? '09 Generics' : '09 泛型编程', category: 'tutorial', desc: isEn ? 'Generic functions and parameterized structs' : '泛型函数与泛型结构体, 类型参数化设计', href: prefix + '/docs/tutorial/09/' },
      { title: isEn ? '10 Concurrency Basics' : '10 并发基础', category: 'tutorial', desc: isEn ? 'xu coroutines, chan channel send and receive' : 'xu 协程启动, chan 通道创建与发送接收', href: prefix + '/docs/tutorial/10/' },
      { title: isEn ? '11 HTTP Server' : '11 HTTP 服务', category: 'tutorial', desc: isEn ? 'High-concurrency HTTP routing and handlers' : 'net/http 搭建高性能 HTTP 路由与请求处理', href: prefix + '/docs/tutorial/11/' },
      { title: isEn ? '12 File Server' : '12 静态文件服务', category: 'tutorial', desc: isEn ? 'Serving static files and MIME types' : '静态资源文件目录托管与 MIME 类型识别', href: prefix + '/docs/tutorial/12/' },
      { title: isEn ? '13 Context & Cancellation' : '13 上下文控制', category: 'tutorial', desc: isEn ? 'Timeouts, cascades, and coroutine cancellation' : 'context 超时控制、级联取消与跨协程传递', href: prefix + '/docs/tutorial/13/' },
      { title: isEn ? '14 TCP Echo' : '14 TCP 网络服务', category: 'tutorial', desc: isEn ? 'net.listen_on, ln.accept, concurrent TCP socket' : 'net.listen_on, ln.accept, 高并发 TCP 套接字', href: prefix + '/docs/tutorial/14/' },
      { title: isEn ? '15 UDP Echo' : '15 UDP 数据报', category: 'tutorial', desc: isEn ? 'net.listen_packet, read_from, write_to UDP' : 'net.listen_packet, read_from, write_to 无连接数据报', href: prefix + '/docs/tutorial/15/' },
      { title: isEn ? '16 Desktop UI' : '16 原生桌面 UI', category: 'tutorial', desc: isEn ? 'Windows, buttons, input fields, state updates' : '创建窗口, 绘制按钮与文本输入框, 状态更新', href: prefix + '/docs/tutorial/16/' },

      { title: isEn ? 'Syntax Freeze Spec' : '语法定稿规范', category: 'doc', desc: isEn ? 'Lexical rules, operators, expressions, grammar' : '词法、操作符、语句结构与语法定义', href: prefix + '/docs/lang/syntax/' },
      { title: isEn ? 'Memory Model' : '内存模型规范', category: 'doc', desc: isEn ? 'Deterministic cleanup, no GC, borrow check' : '确定性释放、无垃圾回收、借用检查与逃逸规则', href: prefix + '/docs/lang/memory/' },
      { title: isEn ? 'Concurrency Model' : '并发架构规范', category: 'doc', desc: isEn ? 'Coroutines, event multiplexing, channel buffers' : '轻量级协程、信道通信与事件多路复用', href: prefix + '/docs/lang/concurrency/' },
      { title: isEn ? 'Type System' : '类型系统规范', category: 'doc', desc: isEn ? 'Primitive types, structs, interfaces, aliases' : '基本类型、结构体、接口与类型转换', href: prefix + '/docs/lang/types/' },
      { title: isEn ? 'EBNF Grammar' : 'EBNF 形式文法', category: 'doc', desc: isEn ? 'Formal Backus-Naur form grammar for Xu' : 'Xu 官方巴科斯范式文法描述', href: prefix + '/docs/lang/ebnf/' },

      { title: '#fmt', category: 'pkg', desc: isEn ? 'Formatted I/O and string interpolation' : '格式化输入输出与字符串拼接', href: prefix + '/api/fmt/' },
      { title: '#strings', category: 'pkg', desc: isEn ? 'UTF-8 string manipulation, splitting, search' : '高性能字符串处理、拆分、查找与修剪', href: prefix + '/api/strings/' },
      { title: '#bytes', category: 'pkg', desc: isEn ? 'Byte slice buffer operations and transforms' : '字节切片与动态字节流缓冲区', href: prefix + '/api/bytes/' },
      { title: '#strconv', category: 'pkg', desc: isEn ? 'Conversions between text and primitive types' : '基础类型与字符串互相转换', href: prefix + '/api/strconv/' },
      { title: '#net', category: 'pkg', desc: isEn ? 'TCP, UDP, and raw IP socket networking' : 'TCP、UDP 及原始 IP 套接字网络通信', href: prefix + '/api/net/' },
      { title: '#net/http', category: 'pkg', desc: isEn ? 'High-concurrency HTTP/1.1 & HTTP/2 server' : '高性能高并发 HTTP 服务端与客户端', href: prefix + '/api/net/http/' },
      { title: '#io', category: 'pkg', desc: isEn ? 'I/O primitives and streaming abstractions' : '基础 I/O 流与读写器接口', href: prefix + '/api/io/' },
      { title: '#os', category: 'pkg', desc: isEn ? 'Process control, env vars, signals and files' : '系统进程控制、环境变量、信号处理与文件操作', href: prefix + '/api/os/' },
      { title: '#sync', category: 'pkg', desc: isEn ? 'Mutex, WaitGroup, Once, and atomics' : '互斥锁、并发等待组与原子操作', href: prefix + '/api/sync/' },
      { title: '#time', category: 'pkg', desc: isEn ? 'Clocks, durations, timers, and sleep' : '高精度时钟、时间段、定时器与休眠', href: prefix + '/api/time/' },
      { title: '#runtime', category: 'pkg', desc: isEn ? 'Runtime core, memory statistics, scheduler' : '语言运行时核心、内存统计与协程调度', href: prefix + '/api/runtime/' },
      { title: '#database/sql', category: 'pkg', desc: isEn ? 'SQL database connection pool and driver API' : 'SQL 数据库通用驱动接口与连接池', href: prefix + '/api/database/sql/' },
      { title: '#encoding/json', category: 'pkg', desc: isEn ? 'Fast JSON serialization and parsing' : '高性能 JSON 序列化与反序列化', href: prefix + '/api/encoding/json/' },
      { title: '#crypto/aes', category: 'pkg', desc: isEn ? 'AES block cipher and GCM/CBC modes' : 'AES 对称分组加密算法', href: prefix + '/api/crypto/aes/' },
      { title: '#crypto/sm4', category: 'pkg', desc: isEn ? 'ShangMi SM4 national standard block cipher' : '国密 SM4 128位分组密码算法', href: prefix + '/api/crypto/sm4/' },
      { title: '#crypto/sm2', category: 'pkg', desc: isEn ? 'ShangMi SM2 elliptic curve public key' : '国密 SM2 椭圆曲线公钥密码算法', href: prefix + '/api/crypto/sm2/' },
      { title: '#crypto/sm3', category: 'pkg', desc: isEn ? 'ShangMi SM3 cryptographic hash function' : '国密 SM3 密码杂凑算法', href: prefix + '/api/crypto/sm3/' },
      { title: '#crypto/tls', category: 'pkg', desc: isEn ? 'TLS 1.2 / 1.3 secure network connections' : 'TLS 安全传输层协议与证书校验', href: prefix + '/api/crypto/tls/' },
      { title: '#ui', category: 'pkg', desc: isEn ? 'Desktop UI window, layout, and renderer' : '原生桌面 UI 窗口、布局与渲染系统', href: prefix + '/api/ui/' },
      { title: '#ui/widgets', category: 'pkg', desc: isEn ? 'Cross-platform native widget components' : '丰富跨平台组件库（按钮、输入框、表格等）', href: prefix + '/api/ui/widgets/' },

      { title: '#redis', category: 'pkg', desc: isEn ? 'Redis key-value client' : 'Redis 高性能键值缓存客户端', href: prefix + '/api/packages/redis/' },
      { title: '#mysql', category: 'pkg', desc: isEn ? 'MySQL database driver' : 'MySQL 原生连接驱动', href: prefix + '/api/packages/mysql/' },
      { title: '#sqlite', category: 'pkg', desc: isEn ? 'SQLite embedded database' : 'SQLite 嵌入式数据库驱动', href: prefix + '/api/packages/sqlite/' },
      { title: '#postgres', category: 'pkg', desc: isEn ? 'PostgreSQL database driver' : 'PostgreSQL 高性能数据库连接驱动', href: prefix + '/api/packages/postgres/' },
      { title: '#kafka', category: 'pkg', desc: isEn ? 'Apache Kafka distributed streaming' : 'Kafka 分布式消息流队列客户端', href: prefix + '/api/packages/kafka/' },

      { title: isEn ? 'Playground' : '在线演练场', category: 'tool', desc: isEn ? 'In-browser WebAssembly compiler sandbox' : '纯浏览器 WebAssembly 客户端沙盒，免安装即时运行代码', href: prefix + '/playground/' },
      { title: isEn ? 'Benchmarks' : '性能实测横测', category: 'tool', desc: isEn ? 'Six-platform cross-language verified benchmarks' : '六大操作系统与架构跨语言实测性能对比图表', href: prefix + '/benchmarks/' },
      { title: isEn ? 'Download SDK' : '下载编译器 SDK', category: 'tool', desc: isEn ? 'Official toolchain archives and install commands' : '官方 Xu 编译器 SDK 与跨平台二进制压缩包', href: prefix + '/download/' },
      { title: isEn ? 'API Catalog' : 'API 索引总览', category: 'tool', desc: isEn ? 'Standard library and package directory' : '标准库与扩展包完整目录与主题索引', href: prefix + '/api/' },
      { title: isEn ? 'Blog' : '技术博客与发布动态', category: 'tool', desc: isEn ? 'Release notes and technical deep dives' : '版本发布说明与核心架构演进技术文章', href: prefix + '/blog/' }
    ];

    function normalizeText(str) {
      return String(str || '').toLowerCase().replace(/[#$&/.():]+/g, ' ').replace(/\s+/g, ' ').trim();
    }

    var dialog = document.createElement('dialog');
    dialog.className = 'global-search-dialog';
    dialog.id = 'global-search-dialog';
    dialog.setAttribute('aria-labelledby', 'global-search-dialog-title');
    dialog.innerHTML = '<div class="global-search-heading">' +
      '<div><h2 id="global-search-dialog-title">' + (isEn ? 'Quick Search' : '全站快捷搜索') + '</h2>' +
      '<p>' + (isEn ? 'Search documentation, tutorials, API packages, specs, and tools' : '输入关键词快速检索文档、教程、API包、核心规范或工具') + '</p></div>' +
      '<button type="button" class="global-search-close" data-search-close title="' + (isEn ? 'Close' : '关闭') + '">×</button>' +
      '</div>' +
      '<div class="global-search-input-box">' +
      '<i class="xi xi-search" aria-hidden="true"></i>' +
      '<input type="search" id="global-search-input" placeholder="' + (isEn ? 'Search docs, packages, e.g. strings, http, ownership, cli...' : '输入关键词，例如 strings、http、所有权、并发、cli...') + '" autocomplete="off" spellcheck="false">' +
      '<kbd class="nav-search-kbd">Esc</kbd>' +
      '</div>' +
      '<div class="global-search-filters" role="group" aria-label="' + (isEn ? 'Filter scope' : '筛选范围') + '">' +
      '<button type="button" class="is-active" data-scope="all">' + (isEn ? 'All' : '全部') + '</button>' +
      '<button type="button" data-scope="doc">' + (isEn ? 'Docs' : '文档') + '</button>' +
      '<button type="button" data-scope="tutorial">' + (isEn ? 'Tutorials' : '教程') + '</button>' +
      '<button type="button" data-scope="pkg">' + (isEn ? 'Packages' : 'API 包') + '</button>' +
      '<button type="button" data-scope="tool">' + (isEn ? 'Tools' : '工具') + '</button>' +
      '</div>' +
      '<p class="global-search-count" role="status" aria-live="polite"></p>' +
      '<ul class="global-search-results" aria-label="' + (isEn ? 'Search results' : '搜索结果') + '"></ul>' +
      '<div class="global-search-footer">' +
      '<span><kbd class="nav-search-kbd">↑</kbd> <kbd class="nav-search-kbd">↓</kbd> ' + (isEn ? 'to navigate' : '导航') + ' · <kbd class="nav-search-kbd">Enter</kbd> ' + (isEn ? 'to select' : '选择') + ' · <kbd class="nav-search-kbd">Esc</kbd> ' + (isEn ? 'to close' : '关闭') + '</span>' +
      '<span>Xu ' + (document.title.match(/v\d+\.\d+\.\d+/) ? document.title.match(/v\d+\.\d+\.\d+/)[0] : 'SDK') + '</span>' +
      '</div>';
    document.body.appendChild(dialog);

    var input = dialog.querySelector('#global-search-input');
    var resultsList = dialog.querySelector('.global-search-results');
    var countEl = dialog.querySelector('.global-search-count');
    var closeBtn = dialog.querySelector('[data-search-close]');
    var filterBtns = dialog.querySelectorAll('.global-search-filters button');
    var activeScope = 'all';
    var selectedIndex = -1;

    // Add local page symbols if on an API page
    var localSymbols = [];
    var articles = document.querySelectorAll('.api-item[id]');
    if (articles && articles.length) {
      var pkgHeading = document.querySelector('main.api-page h1');
      var pkgName = pkgHeading ? pkgHeading.textContent.trim() : '';
      articles.forEach(function (art) {
        var h2 = art.querySelector('h2');
        var code = art.querySelector('pre code');
        var descP = art.querySelector('h3 + p');
        var title = h2 ? h2.textContent.trim() : art.id;
        localSymbols.push({
          title: (pkgName ? pkgName + '.' : '') + title,
          category: 'sym',
          desc: descP ? descP.textContent.trim() : (code ? code.textContent.split('\n')[0] : ''),
          href: '#' + encodeURIComponent(art.id)
        });
      });
    }

    var allEntries = localSymbols.concat(staticEntries);

    function doSearch(query) {
      var norm = normalizeText(query);
      var terms = norm.split(' ').filter(Boolean);
      var filtered = allEntries.filter(function (entry) {
        if (activeScope !== 'all') {
          if (activeScope === 'doc' && entry.category !== 'doc') return false;
          if (activeScope === 'tutorial' && entry.category !== 'tutorial') return false;
          if (activeScope === 'pkg' && entry.category !== 'pkg' && entry.category !== 'sym') return false;
          if (activeScope === 'tool' && entry.category !== 'tool') return false;
        }
        if (!terms.length) return true;
        var searchable = normalizeText(entry.title + ' ' + entry.desc + ' ' + entry.category);
        return terms.every(function (t) { return searchable.indexOf(t) !== -1; });
      });

      function score(e) {
        var t = normalizeText(e.title);
        if (t === norm) return 0;
        if (t.startsWith(norm)) return 1;
        if (t.indexOf(norm) !== -1) return 2;
        return 3;
      }
      if (terms.length) {
        filtered.sort(function (a, b) { return score(a) - score(b); });
      }

      var items = filtered.slice(0, 30);
      resultsList.innerHTML = '';
      selectedIndex = items.length > 0 ? 0 : -1;

      items.forEach(function (entry, idx) {
        var li = document.createElement('li');
        if (idx === 0) li.classList.add('is-selected');

        var a = document.createElement('a');
        a.href = entry.href;

        var badgeClass = 'badge-doc';
        var badgeText = isEn ? 'Doc' : '文档';
        if (entry.category === 'tutorial') { badgeClass = 'badge-doc'; badgeText = isEn ? 'Tutorial' : '教程'; }
        else if (entry.category === 'pkg') { badgeClass = 'badge-pkg'; badgeText = isEn ? 'Package' : '包'; }
        else if (entry.category === 'tool') { badgeClass = 'badge-tool'; badgeText = isEn ? 'Tool' : '工具'; }
        else if (entry.category === 'sym') { badgeClass = 'badge-sym'; badgeText = isEn ? 'Symbol' : '声明'; }

        var top = document.createElement('div');
        top.className = 'global-search-res-top';
        top.innerHTML = '<span class="global-search-badge ' + badgeClass + '">' + badgeText + '</span>' +
          '<span class="global-search-title">' + entry.title + '</span>';

        var desc = document.createElement('div');
        desc.className = 'global-search-desc';
        desc.textContent = entry.desc;

        a.appendChild(top);
        a.appendChild(desc);
        a.addEventListener('click', function () { dialog.close(); });
        li.appendChild(a);
        resultsList.appendChild(li);
      });

      countEl.textContent = filtered.length
        ? (isEn ? 'Found ' + filtered.length + ' results' : '找到 ' + filtered.length + ' 条结果')
        : (isEn ? 'No results found. Try another keyword.' : '未找到匹配结果，请尝试其他关键词。');
    }

    function openDialog() {
      if (dialog.open) { input.focus(); return; }
      activeScope = 'all';
      filterBtns.forEach(function (b) { b.classList.toggle('is-active', b.dataset.scope === 'all'); });
      input.value = '';
      doSearch('');
      dialog.showModal();
      input.focus();
    }

    window.openGlobalSearch = openDialog;

    var openBtn = document.getElementById('global-search-btn');
    if (openBtn) {
      openBtn.addEventListener('click', openDialog);
    }

    closeBtn.addEventListener('click', function () { dialog.close(); });
    dialog.addEventListener('click', function (e) {
      var rect = dialog.getBoundingClientRect();
      if (e.target === dialog && (e.clientX < rect.left || e.clientX > rect.right || e.clientY < rect.top || e.clientY > rect.bottom)) {
        dialog.close();
      }
    });

    filterBtns.forEach(function (btn) {
      btn.addEventListener('click', function () {
        filterBtns.forEach(function (b) { b.classList.remove('is-active'); });
        btn.classList.add('is-active');
        activeScope = btn.dataset.scope;
        doSearch(input.value);
        input.focus();
      });
    });

    input.addEventListener('input', function () { doSearch(input.value); });

    dialog.addEventListener('keydown', function (e) {
      var listItems = resultsList.querySelectorAll('li');
      if (!listItems.length) return;

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        selectedIndex = (selectedIndex + 1) % listItems.length;
        updateSelection(listItems);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        selectedIndex = (selectedIndex - 1 + listItems.length) % listItems.length;
        updateSelection(listItems);
      } else if (e.key === 'Enter') {
        if (selectedIndex >= 0 && selectedIndex < listItems.length) {
          e.preventDefault();
          var link = listItems[selectedIndex].querySelector('a');
          if (link) { link.click(); dialog.close(); }
        }
      }
    });

    function updateSelection(listItems) {
      listItems.forEach(function (li, idx) {
        var isSel = idx === selectedIndex;
        li.classList.toggle('is-selected', isSel);
        if (isSel) {
          li.scrollIntoView({ block: 'nearest' });
        }
      });
    }

    // Global keyboard shortcut: Ctrl/Cmd + K or slash
    document.addEventListener('keydown', function (e) {
      var tag = (e.target && e.target.tagName ? e.target.tagName.toLowerCase() : '');
      var isEditing = tag === 'input' || tag === 'textarea' || tag === 'select' || (e.target && e.target.isContentEditable);
      var isCmdK = (e.key === 'k' || e.key === 'K') && (e.ctrlKey || e.metaKey);
      var isSlash = e.key === '/' && !isEditing && !e.ctrlKey && !e.metaKey && !e.altKey;

      if ((isCmdK || isSlash) && !dialog.open) {
        e.preventDefault();
        openDialog();
      }
    });
  }
})();

