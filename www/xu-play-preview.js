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
  var panButton = document.getElementById('xu-play-preview-pan');
  var panHint = document.getElementById('xu-play-preview-pan-hint');
  var canvas = document.getElementById('xu-play-canvas');
  var narrow = typeof window !== 'undefined' && window.matchMedia ? window.matchMedia('(max-width: 719px), (max-width: 959px) and (max-height: 500px)') : null;
  var panning = false, drag = null;

  function pan(value) {
    if (!panButton) return;
    var available = narrow && narrow.matches && panel.getAttribute('data-preview-size') === 'actual';
    var restoreFocus = !available && document.activeElement === panButton;
    panning = !!value && !!available;
    drag = null;
    panButton.hidden = !available;
    panButton.setAttribute('aria-pressed', String(panning));
    viewport.setAttribute('data-pan', String(panning));
    canvas.inert = panning;
    canvas.tabIndex = panning ? -1 : 0;
    if (panHint) panHint.hidden = !panning;
    if (restoreFocus) actual.focus();
  }

  function size(mode) {
    panel.setAttribute('data-preview-size', mode);
    fit.setAttribute('aria-pressed', String(mode === 'fit'));
    actual.setAttribute('aria-pressed', String(mode === 'actual'));
    // At 100% the viewport, as well as the interactive canvas, is a keyboard
    // entry point so users can scroll without sending arrow keys to Xu.
    viewport.tabIndex = mode === 'actual' ? 0 : -1;
    pan(false);
  }
  fit.addEventListener('click', function () { size('fit'); });
  actual.addEventListener('click', function () { size('actual'); });
  if (panButton) {
    panButton.addEventListener('click', function () { pan(!panning); });
    viewport.addEventListener('pointerdown', function (event) {
      if (!panning || event.button !== 0) return;
      drag = {id:event.pointerId,x:event.clientX,y:event.clientY,left:viewport.scrollLeft,top:viewport.scrollTop};
      viewport.setPointerCapture(event.pointerId);
      event.preventDefault();
    });
    viewport.addEventListener('pointermove', function (event) {
      if (!drag || event.pointerId !== drag.id) return;
      viewport.scrollLeft = drag.left + drag.x - event.clientX;
      viewport.scrollTop = drag.top + drag.y - event.clientY;
      event.preventDefault();
    });
    function endDrag() { drag = null; }
    viewport.addEventListener('pointerup', endDrag);
    viewport.addEventListener('pointercancel', endDrag);
    viewport.addEventListener('lostpointercapture', endDrag);
    if (narrow && narrow.addEventListener) narrow.addEventListener('change', function () { pan(false); });
  }
  expand.addEventListener('click', function () {
    expanded = !expanded;
    panes.classList.toggle('is-preview-expanded', expanded);
    expand.setAttribute('aria-expanded', String(expanded));
    expand.textContent = expanded ? (en ? 'Back to editor' : '返回编辑') : (en ? 'Expand' : '扩大预览');
  });
  size('fit');
}());

/* Narrow workspaces share the same editor and canvas; only presentation changes. */
(function () {
  'use strict';
  function el(id) { return document.getElementById('xu-play-' + id); }
  var root = el('workspace'), navigation = el('mobile-tabs');
  if (!root || !navigation || typeof window.matchMedia !== 'function') return;
  var media = window.matchMedia('(max-width: 719px), (max-width: 959px) and (max-height: 500px)');
  var names = ['files', 'editor', 'preview', 'console'];
  var panels = {files:el('explorer'), editor:el('editor'), preview:el('preview-panel'), console:el('console-panel')};
  var buttons = {};
  var original = {};
  var current = 'editor', followRun = false, detailOpen = false;
  var dialog = el('library'), back = el('library-back');
  names.forEach(function (name) {
    buttons[name] = el('mobile-tab-' + name);
    original[name] = {role:panels[name].getAttribute('role'), label:panels[name].getAttribute('aria-labelledby')};
  });
  function restore(panel, attribute, value) {
    if (value === null) panel.removeAttribute(attribute);
    else panel.setAttribute(attribute, value);
  }
  function template(detail) {
    detailOpen = detail;
    if (!dialog || !back) return;
    if (media.matches) dialog.setAttribute('data-mobile-template', detail ? 'detail' : 'list');
    else dialog.removeAttribute('data-mobile-template');
    back.hidden = !media.matches || !detail;
  }
  function apply() {
    navigation.hidden = !media.matches;
    if (media.matches) root.setAttribute('data-mobile-view', current);
    else root.removeAttribute('data-mobile-view');
    names.forEach(function (name) {
      var selected = name === current;
      buttons[name].setAttribute('aria-selected', String(selected));
      buttons[name].tabIndex = selected ? 0 : -1;
      panels[name].hidden = media.matches && !selected;
      if (media.matches) {
        panels[name].setAttribute('role', 'tabpanel');
        panels[name].setAttribute('aria-labelledby', buttons[name].id);
      } else {
        restore(panels[name], 'role', original[name].role);
        restore(panels[name], 'aria-labelledby', original[name].label);
      }
    });
    el('panes').querySelector('.play-source-pane').hidden = media.matches && current !== 'files' && current !== 'editor';
    el('panes').querySelector('.play-results').hidden = media.matches && current !== 'preview' && current !== 'console';
    template(detailOpen);
  }
  function select(name) {
    if (!panels[name]) return;
    var active = document.activeElement;
    var moveFocus = media.matches && names.some(function (key) {
      return buttons[key] === active || (key !== name && panels[key].contains(active));
    });
    current = name;
    apply();
    if (moveFocus) buttons[name].focus();
  }
  function show(name) { followRun = false; select(name); }
  names.forEach(function (name, index) {
    buttons[name].addEventListener('click', function () { show(name); });
    buttons[name].addEventListener('keydown', function (event) {
      if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
      event.preventDefault();
      var next = event.key === 'Home' ? 0 : event.key === 'End' ? names.length - 1 :
        (index + (event.key === 'ArrowRight' ? 1 : -1) + names.length) % names.length;
      show(names[next]);
      buttons[names[next]].focus();
    });
  });
  if (back) back.addEventListener('click', function () {
    template(false);
    var selected = el('library-list').querySelector('button[aria-current="true"]');
    (selected || el('library-search')).focus();
  });
  window.XuPlayMobile = {
    show:show,
    beginRun:function () { followRun = true; select('console'); },
    cancelRun:function () { followRun = false; },
    completeRun:function (hasUI) {
      if (followRun) select(hasUI ? 'preview' : 'console');
      followRun = false;
    },
    templateList:function () { template(false); },
    templateDetail:function () {
      template(true);
      if (media.matches) {
        var heading = el('library-detail').querySelector('h3');
        if (heading) { heading.tabIndex = -1; heading.focus(); }
      }
    }
  };
  function resize() {
    var active = document.activeElement;
    var focusHidden = media.matches && names.some(function (name) {
      return name !== current && panels[name].contains(active);
    });
    var focusTab = !media.matches && names.some(function (name) { return buttons[name] === active; });
    apply();
    if (focusHidden) buttons[current].focus();
    if (focusTab) {
      var target = current === 'editor' ? el('src') : current === 'files' ? el('add') :
        current === 'preview' ? el('preview-fit') : el('clear');
      target.focus();
    }
  }
  if (media.addEventListener) media.addEventListener('change', resize);
  else media.addListener(resize);
  apply();
}());
