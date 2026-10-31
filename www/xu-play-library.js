/* Browse project templates before opening their complete file set. */
(function () {
  'use strict';
  function el(id) { return document.getElementById('xu-play-' + id); }
  var dialog = el('library');
  if (!dialog) return;
  var en = document.documentElement.lang === 'en';
  var lang = en ? 'en' : 'zh';
  function text(zh, english) { return en ? english : zh; }
  function node(tag, className, value) {
    var result = document.createElement(tag);
    if (className) result.className = className;
    if (value !== undefined) result.textContent = value;
    return result;
  }
  function icon(name) {
    var result = node('i', 'xi xi-' + name);
    result.setAttribute('aria-hidden', 'true');
    return result;
  }
  var catalog;
  var group = 'all';
  var selected = 'hello';
  var active = 'hello';
  var savedProjects;
  var drafts = Object.create(null);

  function filePaths(project) {
    var paths = Object.keys(project.files || {'main.xu': project.source});
    return paths.includes('xu.xun') ? paths : paths.concat('xu.xun');
  }
  function refreshDrafts() {
    drafts = savedProjects ? savedProjects() : Object.create(null);
    var files = drafts.custom;
    if (!files) return;
    catalog.projects.custom = {
      group: 'drafts', draft: true, entry: 'main.xu', files: files,
      title: {zh: '自定义项目', en: 'Custom project'},
      description: {zh: '从文档带入的代码与当前会话中保存的文件。', en: 'Code opened from the documentation and files saved in this session.'}
    };
  }
  function projectFor(key) {
    var project = catalog.projects[key];
    return group === 'drafts' && drafts[key] ? Object.assign({}, project, {
      files: drafts[key], draft: true, expected: null, exercise: null,
      description: {zh: '继续编辑这个项目在本次会话中保存的文件。', en: 'Continue editing the files saved for this project in this session.'}
    }) : project;
  }
  function renderDetail(key) {
    var project = projectFor(key);
    var detail = el('library-detail');
    detail.textContent = '';
    detail.appendChild(node('p', 'play-template-kicker', (project.draft ? text('会话草稿', 'SESSION DRAFT') : text('项目模板', 'PROJECT TEMPLATE')) + ' / ' + key));
    detail.appendChild(node('h3', '', project.title[lang]));
    detail.appendChild(node('p', 'play-template-description', project.description[lang]));
    var heading = node('h4', '', text('项目文件', 'Project files'));
    detail.appendChild(heading);
    var fileList = node('ul', 'play-template-files');
    filePaths(project).forEach(function (path) {
      var item = node('li');
      item.appendChild(icon(path.endsWith('.xu') ? 'file-code' : 'file-text'));
      item.appendChild(node('span', '', path));
      if (path === (project.entry || 'main.xu')) item.appendChild(node('small', '', text('入口', 'Entry')));
      fileList.appendChild(item);
    });
    detail.appendChild(fileList);
    var expected = project.expected;
    if (expected) {
      detail.appendChild(node('h4', '', expected.kind === 'diagnostic' ? text('预期：编译诊断', 'Expected: compiler diagnostic') : text('模板预期输出', 'Template output')));
      detail.appendChild(node('pre', 'play-template-expected' + (expected.kind === 'diagnostic' ? ' is-diagnostic' : ''), expected.value || text('（无输出，正常退出）', '(no output, successful exit)')));
    }
    if (project.exercise) {
      detail.appendChild(node('h4', '', text('试着修改', 'Try a change')));
      detail.appendChild(node('p', 'play-template-exercise', project.exercise[lang]));
    }
    el('library-open').textContent = key === active ? text('继续编辑', 'Continue editing') : project.draft ? text('打开草稿', 'Open draft') : text('打开项目', 'Open project');
    el('library-open').appendChild(icon('arrow-right'));
  }
  function render() {
    var query = el('library-search').value.trim().toLowerCase();
    var keys = Object.keys(catalog.projects).filter(function (key) {
      var project = projectFor(key);
      if (group === 'drafts') {
        if (!drafts[key]) return false;
      } else if (project.hidden || (group !== 'all' && project.group !== group)) return false;
      var words = query.split(/\s+/);
      var exercise = project.exercise ? [project.exercise.zh, project.exercise.en] : [];
      var haystack = [key, project.title.zh, project.title.en, project.description.zh, project.description.en].concat(exercise).concat(filePaths(project)).join(' ').toLowerCase();
      return words.every(function (word) { return haystack.includes(word); });
    });
    var navigation = el('library-groups');
    navigation.textContent = '';
    var groups = catalog.groups.slice();
    if (Object.keys(drafts).length) groups.push({id: 'drafts', title: {zh: '我的草稿', en: 'My drafts'}});
    [{id: 'all', title: {zh: '全部', en: 'All projects'}}].concat(groups).forEach(function (category) {
      var button = node('button', '', category.title[lang]);
      button.type = 'button';
      button.setAttribute('aria-pressed', String(category.id === group));
      button.addEventListener('click', function () {
        group = category.id;
        el('library-search').value = '';
        render();
        // Re-rendering replaces the button that received focus.
        Array.from(navigation.children).find(function (item) { return item.getAttribute('aria-pressed') === 'true'; }).focus();
      });
      navigation.appendChild(button);
    });
    var category = catalog.groups.find(function (item) { return item.id === group; });
    el('library-group-help').textContent = group === 'drafts' ? text('本次会话中打开过的项目，保留你添加的文件与修改。', 'Projects opened in this session, including your added files and edits.') : category ? category.description[lang] : text('从语言入门到多个文件，选择你想完成的目标。', 'Choose a goal, from language basics to a project with several files.');
    el('library-count').textContent = keys.length + text(' 个项目', ' projects');
    var list = el('library-list');
    list.textContent = '';
    var empty = !keys.length;
    var ui = empty && group === 'ui' && !query;
    el('library-detail').hidden = empty;
    el('library-empty').hidden = !empty || ui;
    el('library-ui').hidden = !ui;
    el('library-open').disabled = empty;
    if (empty) return;
    if (!keys.includes(selected)) selected = keys[0];
    keys.forEach(function (key) {
      var project = projectFor(key);
      var button = node('button', 'play-template-item');
      button.type = 'button';
      button.setAttribute('aria-current', String(key === selected));
      var title = node('span', 'play-template-item-title', project.title[lang]);
      var badge = project.expected && project.expected.kind === 'diagnostic' ? text('诊断练习', 'Diagnostic') : filePaths(project).length + text(' 个文件', ' files');
      title.appendChild(node('small', '', badge));
      button.appendChild(title);
      button.appendChild(node('span', 'play-template-item-description', project.description[lang]));
      button.addEventListener('click', function () {
        selected = key;
        Array.from(list.children).forEach(function (item) { item.setAttribute('aria-current', String(item === button)); });
        renderDetail(key);
      });
      list.appendChild(button);
    });
    renderDetail(selected);
  }
  el('browse').addEventListener('click', function () {
    if (!catalog) return;
    refreshDrafts();
    selected = active;
    group = 'all';
    el('library-search').value = '';
    render();
    dialog.showModal();
    el('library-search').focus();
  });
  el('library-close').addEventListener('click', function () { dialog.close(); });
  el('library-search').addEventListener('input', render);
  var navGroups = el('library-groups');
  if (navGroups) {
    navGroups.addEventListener('wheel', function (event) {
      if (event.deltaY && !event.deltaX) {
        event.preventDefault();
        navGroups.scrollLeft += event.deltaY;
      }
    }, { passive: false });
  }
  el('library-reset').addEventListener('click', function () {
    group = 'all';
    el('library-search').value = '';
    render();
    el('library-search').focus();
  });
  el('library-open').addEventListener('click', function () {
    if (!catalog.projects[selected]) return;
    el('ex').value = selected;
    el('ex').dispatchEvent(new Event('change'));
    dialog.close();
  });
  window.XuPlayLibrary = {
    load: function (value, getSavedProjects) {
      catalog = {groups: value.groups, projects: Object.assign({}, value.projects)};
      var select = el('ex');
      var current = select.value || 'hello';
      select.textContent = '';
      Object.keys(catalog.projects).concat(['custom']).forEach(function (key) {
        var option = node('option', '', key === 'custom' ? text('自定义项目', 'Custom project') : catalog.projects[key].title[lang]);
        option.value = key;
        select.appendChild(option);
      });
      select.value = current;
      savedProjects = getSavedProjects;
      refreshDrafts();
      el('browse').disabled = false;
    },
    setActive: function (key) {
      refreshDrafts();
      active = key;
      var project = catalog && catalog.projects[key];
      el('project-title').textContent = project ? project.title[lang] : text('自定义项目', 'Custom project');
    }
  };
}());
