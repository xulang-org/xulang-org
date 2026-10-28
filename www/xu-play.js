/* Browser-local Xu execution. User programs run in a disposable worker. */
(function () {
  var script = document.currentScript;
  var workerUrl = new URL('xu-play-worker.js', script.src);
  var examplesUrl = new URL('xu-play-examples.json', script.src);
  workerUrl.search = examplesUrl.search = new URL(script.src).search;
  var available = script.getAttribute('data-wasm-available') !== 'false';
  var en = document.documentElement.lang === 'en';
  function text(zh, english) { return en ? english : zh; }

  function bind(options) {
    var inline = !!options;
    var source = inline ? options.source : document.getElementById('xu-play-src');
    var select = inline ? null : document.getElementById('xu-play-ex');
    var button = inline ? options.button : document.getElementById('xu-play-run');
    var output = inline ? options.output : document.getElementById('xu-play-out');
    var meta = inline ? options.meta : document.getElementById('xu-play-meta');
    var help = inline ? null : document.getElementById('xu-play-help');
    var workspace = inline ? null : window.XuPlayWorkspace;
    var library = inline ? null : window.XuPlayLibrary;
    if (!source || !button || !output) return;
    var examples = {};
    var worker = null;
    var ready = false;
    var running = false;
    var timer = null;
    var pendingRun = false;
    var examplesLoading = false;
    button.disabled = true;

    function label(stopping) {
      button.innerHTML = stopping
        ? '<i class="xi xi-stop"></i> ' + text('停止运行', 'Stop')
        : '<i class="xi xi-play"></i> ' + (inline ? text('运行', 'Run') : text('运行代码', 'Run Code'));
    }
    function mainSource(example) {
      return example.files ? example.files[example.entry || 'main.xu'] : example.source;
    }
    function readyStatus() {
      var isMobile = typeof window !== 'undefined' && typeof window.innerWidth === 'number' && (window.innerWidth <= 640 || /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent || ''));
      return isMobile
        ? text('就绪 · 点击「运行代码」', 'Ready · Tap Run Code')
        : text('就绪 · Ctrl / Cmd + Enter 运行', 'Ready · Ctrl / Cmd + Enter to run');
    }
    function status(value) { if (meta) meta.textContent = value; }
    function show(value, error) {
      output.textContent = value;
      output.className = 'xu-play-out' + (error ? ' is-err' : '');
    }
    function clearWorker() {
      clearTimeout(timer);
      if (worker) worker.terminate();
      worker = null;
      ready = running = false;
      label(false);
    }
    function failure(message) {
      pendingRun = false;
      clearWorker();
      button.disabled = false;
      button.textContent = text('重试', 'Retry');
      status(text('加载失败', 'Load failed'));
      show(message, true);
    }
    function startWorker() {
      clearWorker();
      button.disabled = true;
      status(text('正在加载…', 'Loading…'));
      var current;
      try {
        current = new Worker(workerUrl, {type: 'module'});
      } catch (error) {
        failure(text('在线运行器启动失败：', 'Could not start the playground: ') + error.message);
        return;
      }
      worker = current;
      timer = setTimeout(function () {
        failure(text('在线运行器加载超时，请重试。', 'The playground took too long to load. Please retry.'));
      }, 30000);
      current.onmessage = function (event) {
        if (worker !== current) return;
        var result = event.data;
        clearTimeout(timer);
        if (result.type === 'ready') {
          ready = true;
          button.disabled = false;
          label(false);
          status(readyStatus());
          if (pendingRun) {
            pendingRun = false;
            run();
          } else maybeAutoRun();
        } else if (result.type === 'result') {
          running = false;
          label(false);
          if (inline) clearWorker();
          var value = result.stderr + result.stdout;
          if (result.truncated) value += text('\n…输出过长，已截断。', '\n…Output truncated.');
          show(value || text('（无输出）', '(no output)'), result.exit !== 0);
          status('exit ' + result.exit);
        } else if (result.type === 'error') {
          failure(result.message);
        }
      };
      current.onerror = function () {
        if (worker === current) failure(text('在线运行器发生错误，请重试。', 'The playground encountered an error. Please retry.'));
      };
      current.postMessage({type: 'init'});
    }

    if (select) {
      select.disabled = true;
      select.addEventListener('change', function () {
        var example = examples[select.value];
        if (!example && !(workspace && select.value === 'custom')) return;
        if (running) {
          clearWorker();
          startWorker();
        }
        if (workspace) workspace.setExample(select.value, example || source.value);
        else source.value = mainSource(example);
        if (library) library.setActive(select.value);
        if (help) help.textContent = example ? example.description[en ? 'en' : 'zh'] : text('自定义项目', 'Custom project');
        show(text('点击「运行代码」查看结果。', 'Click Run Code to see the result.'), false);
        if (ready && !running) status(readyStatus());
      });
    }
    var autoRunCode = null;
    var hasAutoRun = false;
    function maybeAutoRun() {
      if (!autoRunCode || hasAutoRun || !ready) return;
      hasAutoRun = true;
      setTimeout(function () {
        if (!button.disabled && !running) button.click();
      }, 60);
    }

    function load() {
      if (!inline) loadExamples();
      if (!available) {
        button.disabled = !inline;
        status(text('暂不可用', 'Unavailable'));
        show(text('此版本暂未启用在线运行。可下载 Xu，在本机运行这些示例。',
          'Online execution is not enabled for this deployment. Download Xu to run these examples locally.'), false);
        return;
      }
      if (!window.Worker || !window.WebAssembly) {
        button.disabled = !inline;
        status(text('浏览器不支持', 'Unsupported browser'));
        show(text('此浏览器不支持在线运行，请使用支持 WebAssembly 的现代浏览器。',
          'Use a modern browser with WebAssembly support to run these examples.'), true);
        return;
      }
      if (inline) {
        pendingRun = true;
        startWorker();
        return;
      }
      button.disabled = true;
      status(text('正在加载…', 'Loading…'));
      startWorker();
    }
    function loadExamples() {
      if (examplesLoading) return;
      examplesLoading = true;
      fetch(examplesUrl)
        .then(function (response) {
          if (!response.ok) throw new Error('HTTP ' + response.status);
          return response.json();
        })
        .then(function (loaded) {
          var catalog = loaded.projects ? loaded : {projects: loaded, groups: []};
          examples = catalog.projects;
          if (library) library.load(catalog, workspace && workspace.getSavedProjects);
          if (select) select.disabled = false;
          var customCode = null;
          try {
            if (typeof sessionStorage !== 'undefined' && sessionStorage && sessionStorage.getItem) {
              customCode = sessionStorage.getItem('xu-playground-code');
              if (customCode) sessionStorage.removeItem('xu-playground-code');
            }
            if (!customCode && typeof window !== 'undefined' && window.location && window.location.search) {
              var urlParams = new URLSearchParams(window.location.search);
              customCode = urlParams.get('code');
            }
          } catch (e) {}
          if (customCode) {
            autoRunCode = customCode;
            if (workspace) workspace.setSource(customCode);
            else source.value = customCode;
            if (library) library.setActive('custom');
            if (help) help.textContent = text('来自文档与 API 的示例代码', 'Example code from documentation');
            maybeAutoRun();
          } else {
            var current = examples[select && select.value] || (select && select.value === 'custom' ? null : examples.hello);
            if (workspace && current) workspace.setExample(select.value || 'hello', current);
            if (library) library.setActive(select.value || 'hello');
            if (help) help.textContent = current ? current.description[en ? 'en' : 'zh'] : text('自定义项目', 'Custom project');
          }
        })
        .catch(function () {
          examplesLoading = false;
          failure(text('示例加载失败，请重试。', 'Could not load examples. Please retry.'));
        });
    }
    function run() {
      if (running) {
        show(text('运行已停止。', 'Execution stopped.'), false);
        if (inline) {
          clearWorker();
          status(text('已停止', 'Stopped'));
        } else startWorker();
        return;
      }
      if (!ready) { load(); return; }
      var program;
      try {
        if (workspace) workspace.showConsole();
        program = workspace ? workspace.getSource() : source.value;
      } catch (error) {
        show(error.message, true);
        status(text('项目暂不支持运行', 'Project cannot run yet'));
        return;
      }
      running = true;
      label(true);
      show(text('正在运行…', 'Running…'), false);
      status(text('运行中', 'Running'));
      timer = setTimeout(function () {
        show(text('运行超过 10 秒，已停止。请检查循环或缩小输入。',
          'Execution stopped after 10 seconds. Check loops or reduce the input.'), true);
        if (inline) {
          clearWorker();
          status(text('已超时', 'Timed out'));
        } else startWorker();
      }, 10000);
      worker.postMessage({type: 'run', source: program});
    }
    if (!inline) {
      button.addEventListener('click', run);
      source.addEventListener('keydown', function (event) {
        if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
          event.preventDefault();
          if (!button.disabled) button.click();
        }
      });
    }
    window.addEventListener('pagehide', clearWorker);
    if (inline) button.disabled = false;
    else load();
    return run;
  }
  window.XuPlay = {bind: bind};
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { bind(); });
  else bind();
})();
