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
    if (!source || !button || !output) return;
    var examples = {};
    var worker = null;
    var ready = false;
    var running = false;
    var timer = null;
    var pendingRun = false;
    button.disabled = true;

    function label(stopping) {
      button.innerHTML = stopping
        ? '<i class="xi xi-stop"></i> ' + text('停止运行', 'Stop')
        : '<i class="xi xi-play"></i> ' + (inline ? text('运行', 'Run') : text('运行代码', 'Run Code'));
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
          status(text('就绪 · Ctrl / Cmd + Enter 运行', 'Ready · Ctrl / Cmd + Enter to run'));
          if (pendingRun) {
            pendingRun = false;
            run();
          } else if (autoRunCode && !hasAutoRun) {
            hasAutoRun = true;
            setTimeout(function () {
              if (!button.disabled && !running) button.click();
            }, 60);
          }
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
        if (!example) return;
        source.value = example.source;
        if (help) help.textContent = example.description[en ? 'en' : 'zh'];
        show(text('点击「运行代码」查看结果。', 'Click Run Code to see the result.'), false);
        if (ready && !running) status(text('就绪 · Ctrl / Cmd + Enter 运行', 'Ready · Ctrl / Cmd + Enter to run'));
      });
    }
    var autoRunCode = null;
    var hasAutoRun = false;

    function load() {
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
      fetch(examplesUrl)
        .then(function (response) {
          if (!response.ok) throw new Error('HTTP ' + response.status);
          return response.json();
        })
        .then(function (loaded) {
          examples = loaded;
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
            source.value = customCode;
            if (help) help.textContent = text('来自文档与 API 的示例代码', 'Example code from documentation');
          } else {
            var current = examples[select && select.value] || examples.hello;
            if (help && current) help.textContent = current.description[en ? 'en' : 'zh'];
          }
          startWorker();
        })
        .catch(function () {
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
      worker.postMessage({type: 'run', source: source.value});
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
