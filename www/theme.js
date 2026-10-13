(function () {
  var key = 'xu-theme';
  try {
    var saved = localStorage.getItem(key);
    if (saved === 'light' || saved === 'dark') {
      document.documentElement.setAttribute('data-theme', saved);
    }
  } catch (e) {}

  document.addEventListener('DOMContentLoaded', function () {
    var button = document.getElementById('theme-toggle-btn');
    if (!button) return;
    function sync() {
      var light = document.documentElement.getAttribute('data-theme') === 'light';
      button.innerHTML = light
        ? '<i class="xi xi-sun xi-gold"></i> <span>Light</span>'
        : '<i class="xi xi-moon"></i> <span>Dark</span>';
      button.setAttribute('aria-pressed', String(light));
    }
    button.addEventListener('click', function () {
      var next = document.documentElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', next);
      try { localStorage.setItem(key, next); } catch (e) {}
      sync();
    });
    sync();
  });
})();
