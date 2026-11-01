/* Preview presentation only; Xu retains drawing coordinates and input state. */
(function () {
  'use strict';
  var panel = document.getElementById('xu-play-preview-panel');
  if (!panel) return;
  var panes = document.getElementById('xu-play-panes');
  var viewport = document.getElementById('xu-play-preview-viewport');
  var fit = document.getElementById('xu-play-preview-fit');
  var actual = document.getElementById('xu-play-preview-actual');
  var expand = document.getElementById('xu-play-preview-expand');
  var en = document.documentElement.lang === 'en';
  var expanded = false;

  function size(mode) {
    panel.setAttribute('data-preview-size', mode);
    fit.setAttribute('aria-pressed', String(mode === 'fit'));
    actual.setAttribute('aria-pressed', String(mode === 'actual'));
    // At 100% the viewport, as well as the interactive canvas, is a keyboard
    // entry point so users can scroll without sending arrow keys to Xu.
    viewport.tabIndex = mode === 'actual' ? 0 : -1;
  }
  fit.addEventListener('click', function () { size('fit'); });
  actual.addEventListener('click', function () { size('actual'); });
  expand.addEventListener('click', function () {
    expanded = !expanded;
    panes.classList.toggle('is-preview-expanded', expanded);
    expand.setAttribute('aria-expanded', String(expanded));
    expand.textContent = expanded ? (en ? 'Back to editor' : '返回编辑') : (en ? 'Expand' : '扩大预览');
  });
  size('fit');
}());
