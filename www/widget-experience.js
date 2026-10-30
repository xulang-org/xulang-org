/* User-facing component experiences. Native previews never execute Xu code. */
(function () {
  'use strict';
  var root = document.getElementById('widget-experience');
  if (!root) return;
  var scriptURL = new URL(document.currentScript.src);
  var zh = document.documentElement.lang !== 'en';
  var lang = zh ? 'zh' : 'en';
  function t(a, b) { return zh ? a : b; }
  function node(tag, text, className) {
    var el = document.createElement(tag);
    if (text !== undefined) el.textContent = text;
    if (className) el.className = className;
    return el;
  }
  function url(path) { return new URL((zh ? 'zh/' : '') + path, scriptURL); }
  function button(parent, label, action) {
    var el = node('button', label); el.type = 'button';
    el.addEventListener('click', action); parent.appendChild(el); return el;
  }
  function input(parent, type, label, value) {
    var wrap = node('label', label, 'widget-demo-field');
    var el = node(type === 'textarea' ? 'textarea' : 'input');
    if (type !== 'textarea') el.type = type;
    if (value !== undefined) el.value = value;
    wrap.appendChild(el); parent.appendChild(wrap); return el;
  }
  var catalog, current, timer, modal;
  var list = root.querySelector('[data-widget-list]');
  var detail = root.querySelector('[data-widget-detail]');
  var search = root.querySelector('input[type="search"]');
  var category = root.querySelector('select');
  function stop() {
    clearTimeout(timer);
    if (modal) { modal.close(); modal.remove(); modal = null; }
  }
  function draw(c, stage, status) {
    function say(value) { status.textContent = value; }
    function select(values, label) {
      var wrap = node('label', label || t('工作区', 'Workspace'), 'widget-demo-field');
      var el = node('select');
      values.forEach(function (value) { var option = node('option', value); option.value = value; el.appendChild(option); });
      wrap.appendChild(el); stage.appendChild(wrap);
      el.addEventListener('change', function () { say(el.value); });
      return el;
    }
    var slug = c.slug;
    if (['input', 'text-area', 'field', 'field-area', 'password-input'].includes(slug)) {
      var area = ['text-area', 'field-area'].includes(slug);
      var secret = slug === 'password-input';
      var el = input(stage, secret ? 'password' : area ? 'textarea' : 'text', secret ? t('示例密码（请勿输入真实密码）', 'Sample password (do not enter a real password)') : area ? t('项目说明', 'Project description') : t('项目名称', 'Project name'), secret ? 'Xu-demo-123' : 'Xu workspace');
      if (area) el.rows = 4;
      var submitted = false, limit = area ? 400 : 40;
      if (!secret) el.maxLength = limit;
      function validate() {
        var length = Array.from(el.value.trim()).length;
        var valid = length > 0 && length <= limit;
        el.setAttribute('aria-invalid', String(!valid));
        if (!valid) say(length ? t('最多输入 ', 'Use at most ') + limit + t(' 个字符', ' characters') : t('请填写内容', 'Enter a value'));
        return valid;
      }
      el.addEventListener('input', function () { if (submitted && !validate()) return; say(t('已输入 ', 'Characters: ') + Array.from(el.value).length); });
      if (secret) {
        el.id = 'widget-demo-password';
        var reveal = button(stage, t('显示密码', 'Show password'), function () {
          var shown = el.type === 'password'; el.type = shown ? 'text' : 'password';
          reveal.setAttribute('aria-pressed', String(shown));
        });
        reveal.setAttribute('aria-pressed', 'false'); reveal.setAttribute('aria-controls', el.id);
      }
      else {
        button(stage, t('清空', 'Clear'), function () { el.value = ''; el.dispatchEvent(new Event('input')); el.focus(); });
        el.setAttribute('aria-describedby', status.id);
        button(stage, t('保存', 'Save'), function () { submitted = true; if (validate()) say(t('已保存', 'Saved')); else el.focus(); });
      }
    } else if (['checkbox', 'switch', 'radio', 'radio-group', 'multi-select', 'button-group'].includes(slug)) {
      var radio = slug === 'radio' || slug === 'radio-group';
      var values = slug === 'switch' ? [t('实时预览', 'Live preview')] : slug === 'checkbox' ? [t('接收更新', 'Receive updates')] : ['Design', 'Develop', 'Review'];
      values.forEach(function (value, index) {
        var el = input(stage, radio ? 'radio' : 'checkbox', value);
        el.name = 'widget-choice'; el.checked = index === 0;
        if (slug === 'switch') el.setAttribute('role', 'switch');
        el.addEventListener('change', function () { say(Array.from(stage.querySelectorAll('input:checked')).map(function (item) { return item.parentNode.firstChild.textContent; }).join(' · ') || t('未选择', 'None selected')); });
      });
    } else if (['slider', 'range-slider', 'stepper', 'split-view', 'progress'].includes(slug)) {
      var value = 40;
      var el = input(stage, slug === 'stepper' ? 'number' : 'range', t('数值', 'Value'), value);
      el.min = '0'; el.max = '100'; el.step = '5';
      var progress;
      if (slug === 'progress') { progress = node('progress'); progress.max = 100; progress.value = value; stage.appendChild(progress); }
      if (slug === 'range-slider') { var high = input(stage, 'range', t('上限', 'Upper bound'), 80); high.min = '0'; high.max = '100'; high.addEventListener('input', function () { if (+high.value < +el.value) high.value = el.value; say(el.value + ' – ' + high.value); }); }
      var panes;
      if (slug === 'split-view') { panes = node('div', undefined, 'widget-demo-split'); panes.appendChild(node('div', t('工作区', 'Workspace'))); panes.appendChild(node('div', t('预览', 'Preview'))); stage.appendChild(panes); }
      el.addEventListener('input', function () { if (slug === 'stepper') el.value = String(Math.max(0, Math.min(100, Number(el.value) || 0))); if (high && +el.value > +high.value) el.value = high.value; if (progress) progress.value = +el.value; if (panes) panes.style.gridTemplateColumns = Math.max(10, +el.value) + 'fr ' + Math.max(10, 100 - el.value) + 'fr'; say(high ? el.value + ' – ' + high.value : el.value + (slug === 'progress' ? '%' : '')); });
      if (slug === 'stepper') { button(stage, '−', function () { el.stepDown(); el.dispatchEvent(new Event('input')); }); button(stage, '+', function () { el.stepUp(); el.dispatchEvent(new Event('input')); }); }
    } else if (['select', 'combo-box', 'date-picker', 'time-picker', 'color-picker'].includes(slug)) {
      if (slug === 'select') select(['Workspace', 'History', 'Archive']);
      else if (slug === 'combo-box') {
        var el = input(stage, 'text', t('搜索工作区', 'Find a workspace'), '');
        var choices = node('datalist'); choices.id = 'widget-suggestions';
        ['Design', 'Develop', 'Review'].forEach(function (value) { var option = node('option', value); option.value = value; choices.appendChild(option); });
        stage.appendChild(choices); el.setAttribute('list', choices.id); el.addEventListener('input', function () { say(el.value); });
      } else {
        var type = {'date-picker': 'date', 'time-picker': 'time', 'color-picker': 'color'}[slug];
        var el = input(stage, type, c.name, {'date': '2026-10-28', 'time': '14:30', 'color': '#b44532'}[type]);
        el.addEventListener('input', function () { say(el.value); if (type === 'color') stage.style.borderColor = el.value; });
      }
    } else if (slug === 'tree-view') {
      var tree = node('details'); tree.open = true; tree.appendChild(node('summary', 'Xu workspace'));
      ['src/main.xu', 'assets/logo.png', 'xu.xun'].forEach(function (name) { button(tree, name, function () { say(name); }); }); stage.appendChild(tree);
    } else if (['tabs', 'segmented', 'pagination', 'breadcrumbs', 'list-box'].includes(slug)) {
      var values = slug === 'segmented' ? ['Day', 'Week', 'Month'] : slug === 'pagination' ? ['1', '2', '3', '4'] : slug === 'breadcrumbs' ? ['Home', 'Workspace', 'Components'] : ['Overview', 'Activity', 'Settings'];
      var bar = node('div', undefined, slug === 'list-box' ? 'widget-demo-list' : 'widget-demo-tabs');
      stage.appendChild(bar); var content = node('p', values[0]); stage.appendChild(content);
      values.forEach(function (value, index) { var el = button(bar, value, function () { Array.from(bar.children).forEach(function (child) { child.setAttribute('aria-pressed', String(child === el)); }); content.textContent = slug === 'pagination' ? t('第 ', 'Page ') + value + t(' 页 · 当前结果', ' · current results') : value; say(content.textContent); }); el.setAttribute('aria-pressed', String(index === 0)); });
    } else if (slug === 'table') {
      var rows = [['Design', 12], ['Develop', 8], ['Review', 5]], reverse = false;
      var table = node('table'); stage.appendChild(table);
      function paint() { table.textContent = ''; var head = node('tr'); var label = node('th', 'Workspace'); var count = node('th'); button(count, t('成员 ↕', 'Members ↕'), function () { reverse = !reverse; rows.sort(function (a, b) { return reverse ? b[1] - a[1] : a[1] - b[1]; }); paint(); say(t('排序已更新', 'Sort updated')); }); head.appendChild(label); head.appendChild(count); table.appendChild(head); rows.forEach(function (row) { var line = node('tr'); row.forEach(function (cell) { line.appendChild(node('td', String(cell))); }); table.appendChild(line); }); }
      paint();
    } else if (slug === 'chart') {
      var bars = node('div', undefined, 'widget-demo-chart'); stage.appendChild(bars);
      function paint() { bars.textContent = ''; [25, 45, 70, 55, 88].forEach(function (value, i) { value += Math.floor(Math.random() * 10); var bar = node('div'); bar.style.height = value + '%'; bar.title = String(value); bar.setAttribute('aria-label', 'Series ' + (i + 1) + ': ' + value); bars.appendChild(bar); }); }
      paint(); button(stage, t('更换数据', 'Change data'), function () { paint(); say(t('图表已更新', 'Chart updated')); });
    } else if (slug === 'scroll') {
      var panel = node('div', undefined, 'widget-demo-scroll'); panel.tabIndex = 0;
      for (var i = 1; i <= 18; i++) panel.appendChild(node('p', t('项目 ', 'Item ') + i));
      panel.addEventListener('scroll', function () { say(t('滚动位置 ', 'Scroll position ') + Math.round(panel.scrollTop)); }); stage.appendChild(panel);
    } else if (slug === 'web-view') {
      var frame = node('iframe'); frame.title = t('嵌入内容预览', 'Embedded content preview'); frame.setAttribute('sandbox', ''); stage.appendChild(frame);
      function page(name) { frame.srcdoc = '<!doctype html><html><meta charset="utf-8"><body style="font:16px system-ui;padding:24px;background:#f5f3ef;color:#252525"><h2>' + name + '</h2><p>Embedded preview</p></body></html>'; say(name); }
      button(stage, 'Overview', function () { page('Overview'); }); button(stage, 'Activity', function () { page('Activity'); }); page('Overview');
    } else if (slug === 'modal') {
      button(stage, t('打开确认框', 'Open confirmation'), function () {
        if (modal) return;
        modal = node('dialog', undefined, 'widget-demo-dialog'); var opener = document.activeElement;
        var title = node('h3', t('应用更改？', 'Apply changes?')); title.id = 'widget-dialog-title';
        var description = node('p', t('这只是组件体验，不会保存实际数据。', 'This experience does not save real data.')); description.id = 'widget-dialog-description';
        modal.setAttribute('aria-labelledby', title.id); modal.setAttribute('aria-describedby', description.id);
        modal.appendChild(title); modal.appendChild(description);
        function close(value) { modal.close(); modal.remove(); modal = null; say(value); opener.focus(); }
        button(modal, t('取消', 'Cancel'), function () { close(t('已取消', 'Cancelled')); }); button(modal, t('确认', 'Confirm'), function () { close(t('已确认', 'Confirmed')); });
        modal.addEventListener('cancel', function (event) { event.preventDefault(); close(t('已取消', 'Cancelled')); }); document.body.appendChild(modal); modal.showModal();
      });
    } else if (['popover', 'menu', 'context-menu', 'split-button'].includes(slug)) {
      var panel = node('div', undefined, 'widget-demo-popover'); panel.hidden = true;
      var opener = button(stage, slug === 'popover' ? t('偏好设置', 'Preferences') : t('操作 ▾', 'Actions ▾'), function () { panel.hidden = !panel.hidden; opener.setAttribute('aria-expanded', String(!panel.hidden)); }); opener.setAttribute('aria-expanded', 'false');
      if (slug === 'split-button') button(stage, t('保存', 'Save'), function () { say(t('已保存', 'Saved')); });
      if (slug === 'popover') { var option = input(panel, 'checkbox', t('保留历史', 'Keep history')); button(panel, t('应用', 'Apply'), function () { say(option.checked ? t('保留历史：开启', 'History: on') : t('保留历史：关闭', 'History: off')); panel.hidden = true; opener.setAttribute('aria-expanded', 'false'); opener.focus(); }); }
      else ['Open', 'Duplicate', 'Export'].forEach(function (value) { button(panel, value, function () { say(value); panel.hidden = true; opener.setAttribute('aria-expanded', 'false'); opener.focus(); }); });
      stage.appendChild(panel); stage.addEventListener('keydown', function (event) { if (event.key === 'Escape') { panel.hidden = true; opener.setAttribute('aria-expanded', 'false'); opener.focus(); } });
      if (slug === 'context-menu') stage.addEventListener('contextmenu', function (event) { event.preventDefault(); panel.hidden = false; opener.setAttribute('aria-expanded', 'true'); panel.querySelector('button').focus(); });
    } else if (slug === 'tooltip') {
      var tip = node('span', t('更改项目的显示名称', 'Change the displayed project name'), 'widget-demo-tip'); tip.id = 'widget-tip'; tip.setAttribute('role', 'tooltip'); tip.hidden = true;
      var tipFocused = false, tipHovered = false;
      function showTip() { clearTimeout(timer); tip.hidden = false; }
      function hideTip() { clearTimeout(timer); tip.hidden = true; }
      var help = button(stage, t('项目名称 ⓘ', 'Project name ⓘ'), showTip); help.setAttribute('aria-describedby', tip.id);
      help.addEventListener('mouseenter', function () { tipHovered = true; clearTimeout(timer); timer = setTimeout(showTip, 500); });
      help.addEventListener('mouseleave', function () { tipHovered = false; clearTimeout(timer); if (!tipFocused) timer = setTimeout(hideTip, 100); });
      help.addEventListener('focus', function () { tipFocused = true; showTip(); });
      help.addEventListener('blur', function () { tipFocused = false; if (!tipHovered) hideTip(); });
      stage.addEventListener('keydown', function (event) { if (event.key === 'Escape') hideTip(); });
      tip.addEventListener('mouseenter', function () { clearTimeout(timer); });
      tip.addEventListener('mouseleave', function () { if (!tipFocused && !tipHovered) hideTip(); }); stage.appendChild(tip);
    } else if (slug === 'toast-host') {
      var region = node('div', undefined, 'widget-demo-toast'); region.hidden = true; region.setAttribute('role', 'status');
      function dismissToast() { var restore = region.contains(document.activeElement); region.hidden = true; if (restore) toastTrigger.focus(); }
      var toastTrigger = button(stage, t('显示通知', 'Show notification'), function () { region.textContent = ''; region.appendChild(node('span', t('工作区已保存', 'Workspace saved'))); button(region, t('关闭', 'Dismiss'), dismissToast); region.hidden = false; clearTimeout(timer); timer = setTimeout(dismissToast, 5000); }); stage.appendChild(region);
    } else if (slug === 'task-button' || slug === 'spinner') {
      var active = false, trigger;
      var spinner = node('span', undefined, 'widget-demo-spinner'); spinner.hidden = true; spinner.setAttribute('aria-hidden', 'true'); stage.appendChild(spinner);
      stage.setAttribute('aria-busy', 'false');
      function taskState(busy, label, message) {
        active = busy; spinner.hidden = !busy; stage.setAttribute('aria-busy', String(busy));
        trigger.textContent = label; say(message);
      }
      trigger = button(stage, t('开始', 'Start'), function () {
        if (active) { clearTimeout(timer); taskState(false, t('开始', 'Start'), t('已暂停', 'Paused')); return; }
        taskState(true, t('暂停', 'Pause'), t('进行中…', 'In progress…'));
        timer = setTimeout(function () { taskState(false, t('再次开始', 'Run again'), t('已完成', 'Complete')); }, 1800);
      });
    } else if (slug === 'badge') {
      var count = 3, badge = node('span', String(count), 'widget-demo-badge'); stage.appendChild(node('span', t('收件箱 ', 'Inbox '))); stage.appendChild(badge); button(stage, '+1', function () { badge.textContent = String(++count); say(String(count)); }); button(stage, t('清零', 'Clear'), function () { count = 0; badge.textContent = '0'; say('0'); });
    } else if (slug === 'card') {
      var card = node('details', undefined, 'widget-demo-card'); card.appendChild(node('summary', 'Xu workspace')); card.appendChild(node('p', t('将标题、说明和操作组织在同一内容区域。', 'Keep a heading, description and actions in one content region.'))); stage.appendChild(card);
    } else if (slug === 'divider') {
      stage.appendChild(node('p', 'Overview')); var line = node('hr'); stage.appendChild(line); stage.appendChild(node('p', 'Details')); button(stage, t('切换方向', 'Change orientation'), function () { line.classList.toggle('is-vertical'); });
    } else if (slug === 'styled-label') {
      var heading = node('h3', 'Make room for ideas.'); stage.appendChild(heading); var el = input(stage, 'text', t('标题文字', 'Heading text'), heading.textContent); el.addEventListener('input', function () { heading.textContent = el.value; say(t('标题已更新', 'Heading updated')); });
    } else {
      var count = 0;
      var el = button(stage, slug === 'icon-button' ? '☆' : t('保存更改', 'Save changes'), function () { say(t('已完成操作 ', 'Action completed: ') + (++count)); if (slug === 'icon-button') { el.textContent = count % 2 ? '★' : '☆'; el.setAttribute('aria-pressed', String(!!(count % 2))); } });
      if (slug === 'icon-button') { el.setAttribute('aria-label', t('切换收藏', 'Toggle favorite')); el.setAttribute('aria-pressed', 'false'); el.classList.add('widget-demo-icon-button'); }
      var disabled = input(stage, 'checkbox', t('禁用', 'Disabled')); disabled.addEventListener('change', function () { el.disabled = disabled.checked; });
    }
  }
  function show(c, moveFocus) {
    stop(); current = c;
    var workspace = document.getElementById('xu-play-workspace');
    var browsing = new URL(location.href).searchParams.has('widget');
    if (workspace) workspace.hidden = browsing;
    var projectHelp = document.getElementById('xu-play-help');
    if (projectHelp) projectHelp.hidden = browsing;
    detail.textContent = '';
    detail.appendChild(node('p', c.project ? 'Xu / WASM' : t('交互预览 · 不执行 Xu', 'Interactive preview · does not execute Xu'), 'widget-preview-kind'));
    var heading = node('h3', c.name); heading.tabIndex = -1;
    detail.appendChild(heading); detail.appendChild(node('p', c.exercise[lang]));
    if (c.project) {
      var run = node('a', t('打开 Xu 运行示例 ↗', 'Open the Xu example ↗'), 'btn pri'); var target = url('playground/'); target.searchParams.set('example', c.project); target.hash = 'xu-play-workspace'; run.href = target.href; detail.appendChild(run);
    } else {
      var stage = node('div', undefined, 'widget-demo-stage'); var status = node('p', t('等待操作', 'Ready to try'), 'widget-demo-status'); status.id = 'widget-demo-status'; status.setAttribute('role', 'status'); status.setAttribute('aria-live', 'polite'); detail.appendChild(stage); detail.appendChild(status); draw(c, stage, status);
    }
    var docs = node('a', t('查看组件 API →', 'Read component API →'), 'widget-doc-link'); docs.href = url('api/ui/widgets/' + c.slug + '/').href; detail.appendChild(docs);
    Array.from(list.children).forEach(function (el) { el.setAttribute('aria-current', String(el.dataset.widget === c.slug)); });
    if (moveFocus) heading.focus();
  }
  function renderList() {
    list.textContent = '';
    var query = search.value.trim().toLowerCase();
    catalog.components.filter(function (c) { return (!category.value || c.group === category.value) && (c.name + ' ' + c.description.zh + ' ' + c.description.en).toLowerCase().includes(query); }).forEach(function (c) {
      var el = button(list, c.name, function () { var address = new URL(location.href); address.searchParams.delete('example'); address.searchParams.set('widget', c.slug); address.hash = 'widget-experience'; history.replaceState(null, '', address); show(c, true); }); el.dataset.widget = c.slug; el.setAttribute('aria-current', String(current && current.slug === c.slug));
    });
    root.querySelector('[data-widget-count]').textContent = list.children.length + t(' 个组件', ' components');
    if (!list.children.length) list.appendChild(node('p', t('没有匹配的组件，请更换关键词。', 'No matching components. Try another search.')));
  }
  var catalogURL = new URL('widgets.json', scriptURL); catalogURL.search = scriptURL.search;
  fetch(catalogURL).then(function (response) { if (!response.ok) throw new Error('catalog'); return response.json(); }).then(function (value) {
    catalog = value;
    Object.keys(value.groups).forEach(function (key) { var option = node('option', value.groups[key][zh ? 0 : 1]); option.value = key; category.appendChild(option); });
    search.addEventListener('input', renderList); category.addEventListener('change', renderList);
    var params = new URL(location.href).searchParams;
    var requested = params.get('widget');
    var project = params.get('example');
    renderList(); show(value.components.find(function (c) { return requested ? c.slug === requested : project && c.project === project; }) || value.components.find(function (c) { return c.slug === 'button'; }));
    // The asynchronous catalog inserts content above the workspace. Restore the
    // example link's anchor after that insertion so the runnable demo stays in view.
    if (project && location.hash === '#xu-play-workspace') {
      requestAnimationFrame(function () { var workspace = document.getElementById('xu-play-workspace'); if (workspace) workspace.scrollIntoView(); });
    }
    if (requested && !value.components.some(function (c) { return c.slug === requested; })) root.querySelector('[data-widget-count]').textContent = t('未找到该组件，已显示组件目录', 'Component not found; showing the directory');
  }).catch(function () { detail.textContent = t('组件目录暂未加载，请刷新后重试。', 'The component directory could not load. Refresh to retry.'); });
  window.addEventListener('pagehide', stop);
}());
