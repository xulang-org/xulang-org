(function () {
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
      if (target && (target.classList.contains('api-example') || target.classList.contains('faq-item'))) {
        target.open = true;
      }
    }
    window.addEventListener('hashchange', revealLinkedDetails);
    revealLinkedDetails();

    // Initialize hero install tab switcher
    initHeroInstallTabs();
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
    var allOpen = Array.from(groups).every(function (g) { return g.classList.contains('is-open'); });
    var nextState = !allOpen;
    groups.forEach(function (g) {
      g.classList.toggle('is-open', nextState);
      var h = g.querySelector('button.side-h');
      if (h) h.setAttribute('aria-expanded', String(nextState));
    });
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
    var runTitle = isEn ? 'Run code on this page' : '在当前页面运行代码';
    var resultId = 0;
    var editorId = 0;

    function prepareCode(value) {
      if (/fn\s+main\s*\(/.test(value)) {
        return /(?:^|\n)\s*@main\b/.test(value) ? value : '@main\n\n' + value;
      }
      // Keep leading imports outside the generated entry point for snippets.
      var lines = value.split('\n');
      var imports = [];
      var start = 0;
      while (start < lines.length) {
        var line = lines[start].trim();
        if (line && line !== '@main' && !/^#(?:[A-Za-z_]|")/.test(line) && !/^\/\//.test(line)) break;
        if (line && line !== '@main') imports.push(lines[start]);
        start++;
      }
      return '@main\n\n' + (imports.length ? imports.join('\n') + '\n\n' : '') +
        'fn main() int {\n    ' + lines.slice(start).join('\n    ') + '\n    << 0\n}\n';
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
      var isRunnable = (kind === 'xu' || kind === 'api') && !pre.closest('.xu-local-only');

      var kindMeta = {
        xu: { icon: 'xi-code xi-brand', title: isEn ? 'Xu Source' : 'Xu 代码', badge: '' },
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

      // 执行按钮（针对可执行 Xu 代码与 API 沙盒）
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
})();

