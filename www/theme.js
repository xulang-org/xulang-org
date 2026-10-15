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
  });
})();
