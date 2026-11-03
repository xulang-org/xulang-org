/* Run the complete homepage project through the shared WASM worker. */
(function () {
  'use strict';
  function init() {
    var root = document.querySelector('.home-example[data-playground-example]');
    if (!root || !window.XuPlay) return;
    var en = document.documentElement.lang === 'en';
    var button = root.querySelector('[data-home-run]');
    var edit = root.querySelector('[data-home-edit]');
    var reset = root.querySelector('[data-home-reset]');
    var output = root.querySelector('.home-console .xu-play-out');
    var meta = root.querySelector('.home-console [role="status"]');
    var files = Array.from(root.querySelectorAll('code[data-source-file]')).map(function (code) {
      return {code: code, original: code.textContent, editor: null};
    });
    if (!button || !edit || !reset || !output || !files.length) return;
    var source = {value: ''};
    var run = window.XuPlay.bind({source: source, button: button, output: output, meta: meta,
      loadingMessage: en ? 'Preparing your first run…' : '首次运行，正在准备…',
      loadingStatus: en ? 'Preparing…' : '准备中…'});
    if (!run) return;
    var tryLink = document.querySelector('[data-home-try]');
    if (tryLink) tryLink.addEventListener('click', function () { button.click(); });
    button.addEventListener('click', function () {
      source.value = files.map(function (file) {
        return (file.editor ? file.editor.value : file.code.textContent).replace(/^\s*@main\s*$/gm, '');
      }).join('\n\n');
      run();
    });
    edit.addEventListener('click', function () {
      var editing = edit.getAttribute('aria-pressed') !== 'true';
      files.forEach(function (file) {
        var pre = file.code.parentElement;
        if (!file.editor) {
          file.editor = document.createElement('textarea');
          file.editor.className = 'code-block-editor home-code-editor';
          file.editor.value = file.original;
          file.editor.spellcheck = false;
          file.editor.setAttribute('aria-label', file.code.getAttribute('data-source-file'));
          file.editor.rows = Math.max(6, file.original.trim().split('\n').length + 1);
          pre.parentNode.insertBefore(file.editor, pre);
        }
        file.editor.hidden = !editing;
        pre.hidden = editing;
        if (!editing) file.code.textContent = file.editor.value;
      });
      edit.setAttribute('aria-pressed', String(editing));
      reset.hidden = !editing;
      edit.textContent = editing ? (en ? 'Done editing' : '完成编辑') : (en ? 'Edit code' : '编辑代码');
    });
    reset.addEventListener('click', function () {
      files.forEach(function (file) {
        file.code.textContent = file.original;
        if (file.editor) file.editor.value = file.original;
      });
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
}());
