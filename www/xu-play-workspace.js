/* Virtual project files and editor UI. The worker remains the execution boundary. */
(function () {
  'use strict';
  var root = document.getElementById('xu-play-workspace');
  if (!root) return;
  var en = document.documentElement.lang === 'en';
  function text(zh, english) { return en ? english : zh; }
  function el(id) { return document.getElementById('xu-play-' + id); }
  var editor = el('src');
  var tree = el('tree');
  var tabs = el('file-tabs');
  var lines = el('lines');
  var highlight = el('highlight');
  var storageKey = 'xu-play-workspace-v4';
  var projects = Object.create(null);
  var canonicalTemplates = Object.create(null);
  var currentKey = 'hello';
  var active = 'main.xu';
  var files;
  var expanded = new Set(['']);
  var removed = null;
  var saveTimer;
  var token = /\/\/[^\n]*|\/\*[\s\S]*?\*\/|"(?:\\.|[^"\\])*"|#[\w/]+|\b(?:fn|pub|mut|const|if|else|match|for|while|break|continue|xu|true|false|struct|enum|impl|or|int|i64|f64|bool|string|byte)\b|\b\d+(?:\.\d+)?\b|@main|<<|>>/g;

  function icon(name) {
    var node = document.createElement('i');
    node.className = 'xi xi-' + name;
    node.setAttribute('aria-hidden', 'true');
    return node;
  }
  function node(tag, className, value) {
    var result = document.createElement(tag);
    if (className) result.className = className;
    if (value !== undefined) result.textContent = value;
    return result;
  }
  function validPath(path) {
    return path.length <= 160 && /^[a-zA-Z0-9_./-]+$/.test(path) &&
      path.split('/').every(function (part) { return part && part !== '.' && part !== '..'; });
  }
  function isObsoleteCode(src) {
    return typeof src === 'string' && (
      src.includes('widgets.default_theme()') ||
      src.includes('playground.dark_theme()') ||
      src.includes('draw.rgb(16,24,39)') ||
      src.includes('draw.rgb(16,14,18)') ||
      src.includes('draw.rgb(35,31,39)') ||
      src.includes('#101827') ||
      src.includes('#100e12')
    );
  }
  function defaultFiles(template, key) {
    var result = Object.create(null);
    if (template && template.files) {
      Object.keys(template.files).forEach(function (path) {
        if (validPath(path) && typeof template.files[path] === 'string') result[path] = template.files[path];
      });
    } else result['main.xu'] = typeof template === 'string' ? template : template.source;
    result['xu.xun'] = 'module: playground/' + (key || currentKey) + '\nversion: !ver 0.1.0\nxu: !ver ' + root.getAttribute('data-xu-version') + '\n';
    return result;
  }
  try {
    var saved = JSON.parse(sessionStorage.getItem(storageKey));
    if (saved && saved.projects && typeof saved.projects === 'object') {
      Object.keys(saved.projects).slice(0, 32).forEach(function (key) {
        var value = saved.projects[key];
        if (!value || typeof value !== 'object' || typeof value['main.xu'] !== 'string') return;
        if (isObsoleteCode(value['main.xu'])) return;
        var restored = Object.create(null);
        Object.keys(value).slice(0, 32).forEach(function (path) {
          if (validPath(path) && typeof value[path] === 'string') restored[path] = value[path];
        });
        if (typeof restored['main.xu'] === 'string') projects[key] = restored;
      });
      if (Object.hasOwn(projects, saved.selected)) currentKey = saved.selected;
    }
  } catch (_) { /* Private browsing can deny session storage. Editing still works. */ }
  var placeholder = !Object.hasOwn(projects, currentKey);
  var initialSource = editor.value;
  files = projects[currentKey] || defaultFiles(editor.value);
  if (!files['xu.xun']) files['xu.xun'] = defaultFiles('')['xu.xun'];
  projects[currentKey] = files;
  if (projects.custom) {
    var customOption = node('option', '', text('自定义项目', 'Custom project'));
    customOption.value = 'custom';
    el('ex').appendChild(customOption);
  }
  el('ex').value = currentKey;

  function save() {
    if (active !== 'xu.xun') files[active] = editor.value;
    try {
      sessionStorage.setItem(storageKey, JSON.stringify({selected: currentKey, projects: projects}));
      el('save-state').textContent = text('本次会话自动保存', 'Autosaved for this session');
    } catch (_) {
      el('save-state').textContent = text('仅保留在当前页面', 'Kept in this page only');
    }
  }
  function syncScroll() {
    lines.style.transform = 'translateY(' + -editor.scrollTop + 'px)';
    highlight.style.transform = 'translate(' + -editor.scrollLeft + 'px,' + -editor.scrollTop + 'px)';
  }
  function updateCursor() {
    var before = editor.value.slice(0, editor.selectionStart);
    var row = before.split('\n').length;
    var col = before.length - before.lastIndexOf('\n');
    el('cursor').textContent = en ? 'Ln ' + row + ', Col ' + col : '行 ' + row + '，列 ' + col;
  }
  function updateCode() {
    lines.textContent = Array.from({length: editor.value.split('\n').length}, function (_, i) { return i + 1; }).join('\n');
    highlight.textContent = '';
    var source = editor.value;
    var previous = 0;
    if (/\.xu$/.test(active)) {
      token.lastIndex = 0;
      var match;
      while ((match = token.exec(source))) {
        highlight.appendChild(document.createTextNode(source.slice(previous, match.index)));
        var value = match[0];
        var kind = value[0] === '/' ? 'comment' : value[0] === '"' ? 'string' : /^\d/.test(value) ? 'number' : /^(int|i64|f64|bool|string|byte)$/.test(value) ? 'type' : 'keyword';
        highlight.appendChild(node('span', 'syn-' + kind, value));
        previous = token.lastIndex;
      }
    }
    highlight.appendChild(document.createTextNode(source.slice(previous) + '\n'));
    updateCursor();
    syncScroll();
  }
  function tabKeys(event, buttons) {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    var index = buttons.indexOf(event.currentTarget);
    var container = event.currentTarget.parentNode;
    index = event.key === 'Home' ? 0 : event.key === 'End' ? buttons.length - 1 : (index + (event.key === 'ArrowRight' ? 1 : -1) + buttons.length) % buttons.length;
    buttons[index].click();
    container.children[index].focus();
  }
  function renderTabs() {
    tabs.textContent = '';
    Object.keys(files).forEach(function (path, index) {
      var button = node('button');
      button.type = 'button';
      button.id = 'xu-play-file-tab-' + index;
      button.title = path;
      button.setAttribute('role', 'tab');
      button.setAttribute('aria-controls', 'xu-play-editor-panel');
      button.setAttribute('aria-selected', String(path === active));
      button.tabIndex = path === active ? 0 : -1;
      button.appendChild(icon(path.endsWith('.xu') ? 'file-code' : 'file-text'));
      button.appendChild(node('span', '', path.split('/').pop()));
      button.addEventListener('click', function () { open(path); });
      button.addEventListener('keydown', function (event) { tabKeys(event, Array.from(tabs.children)); });
      tabs.appendChild(button);
      if (path === active) el('editor-panel').setAttribute('aria-labelledby', button.id);
    });
  }
  function renderTree() {
    var hierarchy = {folders: Object.create(null), files: []};
    Object.keys(files).sort().forEach(function (path) {
      var parts = path.split('/');
      var parent = hierarchy;
      parts.slice(0, -1).forEach(function (part) {
        parent.folders[part] = parent.folders[part] || {folders: Object.create(null), files: []};
        parent = parent.folders[part];
      });
      parent.files.push(path);
    });
    function folder(name, path, branch) {
      var details = node('details');
      details.open = expanded.has(path);
      var summary = node('summary', path ? '' : 'play-project-root');
      summary.appendChild(icon(path ? 'folder' : 'folder-open'));
      summary.appendChild(node('span', '', name));
      details.appendChild(summary);
      var list = node('ul');
      Object.keys(branch.folders).sort().forEach(function (child) {
        var item = node('li');
        item.appendChild(folder(child, path ? path + '/' + child : child, branch.folders[child]));
        list.appendChild(item);
      });
      branch.files.forEach(function (file) {
        var item = node('li');
        var button = node('button');
        button.type = 'button';
        button.title = file;
        button.setAttribute('aria-current', String(file === active));
        button.appendChild(icon(file.endsWith('.xu') ? 'file-code' : 'file-text'));
        button.appendChild(node('span', '', file.split('/').pop()));
        button.addEventListener('click', function () { open(file); });
        item.appendChild(button);
        list.appendChild(item);
      });
      if (!list.children.length) list.appendChild(node('li', 'play-tree-empty', text('空目录', 'Empty folder')));
      details.appendChild(list);
      details.addEventListener('toggle', function () { if (details.open) expanded.add(path); else expanded.delete(path); });
      return details;
    }
    tree.textContent = '';
    tree.appendChild(folder(currentKey, '', hierarchy));
  }
  function open(path) {
    save();
    active = path;
    editor.value = files[path];
    editor.readOnly = path === 'xu.xun';
    el('remove').disabled = path === 'main.xu' || path === 'xu.xun';
    editor.setAttribute('aria-label', text('编辑 ', 'Edit ') + path);
    editor.scrollTop = editor.scrollLeft = 0;
    editor.setSelectionRange(0, 0);
    el('file-name').textContent = currentKey + ' / ' + path.replaceAll('/', ' / ');
    el('file-kind').textContent = path === 'xu.xun' ? text('项目清单 · 只读', 'Manifest · read only') : path.endsWith('.xu') ? 'Xu' : text('资源文件', 'Asset');
    renderTabs();
    renderTree();
    updateCode();
  }
  function setExample(key, template) {
    if (template) canonicalTemplates[key] = template;
    save();
    removed = null;
    el('undo-remove').hidden = true;
    var replacePlaceholder = placeholder && key === currentKey && files['main.xu'] === initialSource && Object.keys(files).length === 2;
    currentKey = key;
    if (projects[key] && isObsoleteCode(projects[key]['main.xu'])) {
      delete projects[key];
    }
    files = (!replacePlaceholder && projects[key]) || defaultFiles(template, key);
    placeholder = false;
    projects[key] = files;
    if (key === 'custom' && !el('ex').querySelector('option[value="custom"]')) {
      var customOption = node('option', '', text('自定义项目', 'Custom project'));
      customOption.value = 'custom';
      el('ex').appendChild(customOption);
    }
    el('ex').value = key;
    // open() first saves the editor, so switch it to the new project's main file.
    active = 'main.xu';
    editor.value = files[active];
    open(active);
    save();
  }
  function showConsole() {
    var tab = el('console-tab');
    if (tab && typeof tab.click === 'function') tab.click();
  }
  var consoleTab = el('console-tab');
  var previewTab = el('preview-tab');
  var resultTabs = (consoleTab && previewTab) ? [consoleTab, previewTab] : [];
  resultTabs.forEach(function (button, index) {
    button.addEventListener('click', function () {
      resultTabs.forEach(function (tab, i) {
        tab.setAttribute('aria-selected', String(i === index));
        tab.tabIndex = i === index ? 0 : -1;
      });
      if (el('console-panel')) el('console-panel').hidden = index !== 0;
      if (el('preview-panel')) el('preview-panel').hidden = index !== 1;
    });
    button.addEventListener('keydown', function (event) { tabKeys(event, resultTabs); });
  });
    var resetBtn = el('reset');
  if (resetBtn) {
    resetBtn.addEventListener('click', function () {
      var template = canonicalTemplates[currentKey];
      if (!template) return;
      delete projects[currentKey];
      placeholder = false;
      files = defaultFiles(template, currentKey);
      projects[currentKey] = files;
      active = 'main.xu';
      editor.value = files[active];
      open(active);
      save();
      if (el('save-state')) el('save-state').textContent = text('已恢复为默认模板代码', 'Restored to default template');
    });
  }
  el('clear').addEventListener('click', function () { el('out').textContent = ''; });
  el('remove').addEventListener('click', function () {
    if (active === 'main.xu' || active === 'xu.xun') return;
    save();
    removed = {path: active, content: files[active]};
    delete files[active];
    active = 'main.xu';
    editor.value = files[active];
    open(active);
    save();
    el('undo-remove').hidden = false;
  });
  el('undo-remove').addEventListener('click', function () {
    if (!removed) return;
    save();
    files[removed.path] = removed.content;
    var path = removed.path;
    removed = null;
    el('undo-remove').hidden = true;
    open(path);
    save();
  });
  el('add').addEventListener('click', function () {
    el('new-file').hidden = !el('new-file').hidden;
    if (!el('new-file').hidden) el('file-path').focus();
  });
  function cancelFile() {
    el('new-file').hidden = true;
    el('file-path').value = '';
    el('file-error').textContent = '';
    el('add').focus();
  }
  el('cancel-file').addEventListener('click', cancelFile);
  el('file-path').addEventListener('keydown', function (event) { if (event.key === 'Escape') cancelFile(); });
  el('new-file').addEventListener('submit', function (event) {
    event.preventDefault();
    var path = el('file-path').value.trim();
    if (!validPath(path)) {
      el('file-error').textContent = text('使用字母、数字、-、_、. 和 /，不能包含空目录或 ..。', 'Use letters, numbers, -, _, . and /. Empty segments and .. are not allowed.');
      return;
    }
    var conflict = Object.keys(files).some(function (file) {
      return file === path || file.startsWith(path + '/') || path.startsWith(file + '/');
    });
    if (conflict || Object.keys(files).length >= 32) {
      el('file-error').textContent = conflict ? text('该路径已存在或与目录冲突。', 'This path already exists or conflicts with a directory.') : text('每个项目最多 32 个文件。', 'Projects can contain up to 32 files.');
      return;
    }
    save();
    if (removed && removed.path === path) {
      removed = null;
      el('undo-remove').hidden = true;
    }
    files[path] = path.endsWith('.xu') ? '@main\n\n' : '';
    var parts = path.split('/');
    parts.slice(0, -1).forEach(function (_, i) { expanded.add(parts.slice(0, i + 1).join('/')); });
    cancelFile();
    open(path);
    save();
    editor.focus();
  });
  editor.addEventListener('input', function () {
    if (active !== 'xu.xun') files[active] = editor.value;
    updateCode();
    clearTimeout(saveTimer);
    saveTimer = setTimeout(save, 250);
  });
  editor.addEventListener('scroll', syncScroll);
  ['click', 'keyup', 'select'].forEach(function (event) { editor.addEventListener(event, updateCursor); });
  editor.addEventListener('keydown', function (event) {
    if (event.key === 'Tab' && !event.shiftKey && !editor.readOnly) {
      event.preventDefault();
      editor.setRangeText('    ', editor.selectionStart, editor.selectionEnd, 'end');
      editor.dispatchEvent(new Event('input'));
    }
  });
  window.addEventListener('pagehide', save);
  window.XuPlayWorkspace = {
    setExample: setExample,
    getSavedProjects: function () {
      var saved = Object.create(null);
      Object.keys(projects).forEach(function (key) { saved[key] = Object.assign({}, projects[key]); });
      return saved;
    },
    setSource: function (source) { setExample('custom', source); files['main.xu'] = source; editor.value = source; updateCode(); save(); },
    showConsole: showConsole,
    getSource: function () {
      save();
      var paths = Object.keys(files).filter(function (path) { return path.endsWith('.xu'); });
      if (paths.some(function (path) { return path.includes('/') && files[path].trim(); })) {
        throw new Error(text('浏览器暂不支持子目录中的 Xu 包。请把参与运行的 .xu 文件放在项目根目录，或使用本地 SDK。', 'The browser does not yet support Xu packages in subdirectories. Put runnable .xu files in the project root, or use the local SDK.'));
      }
      return paths.filter(function (path) { return !path.includes('/'); }).sort(function (a, b) {
        return a === 'main.xu' ? -1 : b === 'main.xu' ? 1 : a.localeCompare(b);
      }).map(function (path) {
        return files[path].replace(/^\s*@main\s*$/gm, '');
      }).join('\n\n');
    }
  };
  root.classList.add('has-highlight');
  active = 'main.xu';
  editor.value = files[active];
  open(active);
}());
