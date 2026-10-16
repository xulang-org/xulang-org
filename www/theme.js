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
        if (window.innerWidth > 860 && document.body.classList.contains('mobile-nav-open')) {
          setMenu(false);
        }
      });
    }

    // Initialize code block copy and run toolbars
    initCodeToolbars();
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

      var wrapper = pre.closest('.code-block-wrapper');
      var header = null;

      if (!wrapper) {
        wrapper = document.createElement('div');
        wrapper.className = 'code-block-wrapper';
        pre.parentNode.insertBefore(wrapper, pre);

        header = document.createElement('div');
        header.className = 'code-block-header';

        var titleSpan = document.createElement('span');
        titleSpan.className = 'code-block-header-title';
        titleSpan.innerHTML = '<i class="xi xi-code xi-brand"></i> <span>Xu</span>';
        header.appendChild(titleSpan);

        wrapper.appendChild(header);
        wrapper.appendChild(pre);
      } else {
        header = wrapper.querySelector('.code-block-header');
        if (!header) {
          header = document.createElement('div');
          header.className = 'code-block-header';
          wrapper.insertBefore(header, wrapper.firstChild);
        }
      }

      if (header.querySelector('.code-actions')) return;

      var actions = document.createElement('div');
      actions.className = 'code-actions';

      var firstLine = rawCode.split('\n')[0].trim();
      var isShellCommand = /^(xu\s+(run|build|test|fmt)|git\s+|curl\s+|#(?:\s|!)|\$)/.test(firstLine) || (rawCode.indexOf('\n') === -1 && firstLine.startsWith('xu '));

      // 复制按钮
      var copyBtn = document.createElement('button');
      copyBtn.type = 'button';
      copyBtn.className = 'code-action-btn code-copy-btn';
      copyBtn.innerHTML = '<i class="xi xi-copy"></i> <span>' + copyText + '</span>';
      copyBtn.title = isEn ? 'Copy code' : '复制代码';
      copyBtn.addEventListener('click', function () {
        navigator.clipboard.writeText(currentCode()).then(function () {
          copyBtn.classList.add('copied');
          copyBtn.innerHTML = '<i class="xi xi-check"></i> <span>' + copiedText + '</span>';
          setTimeout(function () {
            copyBtn.classList.remove('copied');
            copyBtn.innerHTML = '<i class="xi xi-copy"></i> <span>' + copyText + '</span>';
          }, 1500);
        });
      });
      actions.appendChild(copyBtn);

      // 执行按钮（针对 Xu 代码）
      if (!isShellCommand) {
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
            editorHelp.textContent = isEn ? 'Run your changes with Run or Ctrl / Cmd + Enter.' : '修改后点击「运行」，或按 Ctrl / Cmd + Enter。';
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
})();

