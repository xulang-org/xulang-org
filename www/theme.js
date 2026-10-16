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

  // 侧边栏菜单分组折叠/收起
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
    btn.setAttribute('data-expanded', String(nextState));
  };

  // 代码块方便的复制与运行按钮
  function initCodeToolbars() {
    var isEn = document.documentElement.lang === 'en';
    var copyText = isEn ? 'Copy' : '复制';
    var copiedText = isEn ? '✓ Copied' : '✓ 已复制';
    var runText = isEn ? 'Run' : '运行';
    var runTitle = isEn ? 'Run in WebAssembly Playground' : '在 WebAssembly 演练场运行';

    var pres = document.querySelectorAll('main.doc pre, main.home pre, .api-item pre');
    pres.forEach(function (pre) {
      if (pre.closest('#bench-src-modal') || pre.classList.contains('xu-play-out') || pre.querySelector('.code-actions')) return;
      var code = pre.querySelector('code');
      if (!code) return;

      var rawCode = (code.textContent || '').trim();
      if (!rawCode) return;

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
      var isShellCommand = /^(xu\s+(run|build|test|fmt)|git\s+|curl\s+|#|\$)/.test(firstLine) || (rawCode.indexOf('\n') === -1 && firstLine.startsWith('xu '));

      // 复制按钮
      var copyBtn = document.createElement('button');
      copyBtn.type = 'button';
      copyBtn.className = 'code-action-btn code-copy-btn';
      copyBtn.innerHTML = '<i class="xi xi-copy"></i> <span>' + copyText + '</span>';
      copyBtn.title = isEn ? 'Copy code' : '复制代码';
      copyBtn.addEventListener('click', function () {
        navigator.clipboard.writeText(rawCode).then(function () {
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
        var runBtn = document.createElement('button');
        runBtn.type = 'button';
        runBtn.className = 'code-action-btn code-run-btn';
        runBtn.innerHTML = '<i class="xi xi-play"></i> <span>' + runText + '</span>';
        runBtn.title = runTitle;
        runBtn.addEventListener('click', function () {
          var finalCode = rawCode;
          var hasMain = /fn\s+main\s*\(/.test(finalCode);
          if (!hasMain) {
            finalCode = '@main\n\nfn main() int {\n    ' + finalCode.split('\n').join('\n    ') + '\n    << 0\n}\n';
          } else if (finalCode.indexOf('@main') === -1) {
            finalCode = '@main\n\n' + finalCode;
          }
          try {
            sessionStorage.setItem('xu-playground-code', finalCode);
          } catch (e) {}
          var targetUrl = (isEn ? '' : '/zh') + '/playground';
          window.location.href = targetUrl;
        });
        actions.appendChild(runBtn);
      }

      header.appendChild(actions);
    });
  }
})();

