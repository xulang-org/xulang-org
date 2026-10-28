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
    var panel = inline ? null : document.getElementById('xu-play-ui');
    var canvas = inline ? null : document.getElementById('xu-play-canvas');
    var uiStatus = inline ? null : document.getElementById('xu-play-ui-status');
    if (!source || !button || !output) return;
    var examples = {};
    var worker = null;
    var ready = false;
    var running = false;
    var timer = null;
    var pendingRun = false;
    var clicks = [];
    var activeSource = null;
    var interactive = false;
    var inputMode = false;
    var queuedInputs = [];
    var pointerActive = false;
    button.disabled = true;

    function label(stopping) {
      button.innerHTML = stopping
        ? '<i class="xi xi-stop"></i> ' + text('停止运行', 'Stop')
        : '<i class="xi xi-play"></i> ' + (inline ? text('运行', 'Run') : text('运行代码', 'Run Code'));
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
    function clearUI() {
      interactive = false;
      clicks = [];
      queuedInputs = [];
      inputMode = pointerActive = false;
      activeSource = null;
      if (panel) panel.hidden = true;
      if (canvas) canvas.setAttribute('aria-disabled', 'true');
    }
    function showUI(result) {
      interactive = false;
      if (!panel || !canvas || !result.ui || result.exit !== 0 || activeSource !== source.value) {
        if (panel) panel.hidden = true;
        return;
      }
      if (!window.XuPlayCanvas) throw new Error('Canvas host is unavailable');
      inputMode = !!result.ui.input;
      var committed = window.XuPlayCanvas.render(canvas, result.ui.commands);
      panel.hidden = !committed;
      interactive = committed && result.ui.interactive && activeSource === source.value && clicks.length < window.XuPlayCanvas.maxEvents;
      canvas.setAttribute('aria-disabled', String(!interactive));
      if (uiStatus) uiStatus.textContent = result.ui.interactive
        ? clicks.length + '/64 · ' + (clicks.length >= 64
          ? text('事件已达上限，重新运行以重置。', 'Event limit reached. Run Code to reset.')
          : (inputMode ? text('真实控件 · 点击 / Tab 聚焦 · Enter/空格激活 · 方向键调节 · Esc 离开。', 'Real widgets · Click / Tab to focus · Enter/Space to activate · Arrows to adjust · Esc to leave.') : text('点击画布，或聚焦画布后按 Enter 点击中心。', 'Click the canvas, or focus it and press Enter to click its center.')))
        : text('静态画面 · 修改代码后重新运行。', 'Static drawing · Edit the source and run again.');
    }
    function clearWorker() {
      clearTimeout(timer);
      if (worker) worker.terminate();
      worker = null;
      ready = running = false;
      interactive = false;
      label(false);
    }
    function failure(message) {
      pendingRun = false;
      clearWorker();
      clearUI();
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
          try {
            showUI(result);
            if (inputMode && queuedInputs.length && activeSource === source.value) {
              clicks = clicks.concat(queuedInputs.splice(0, window.XuPlayCanvas.maxEvents - clicks.length));
              if (interactive) execute();
              else queuedInputs = [];
            }
          }
          catch (error) {
            clearUI();
            status(text('UI 渲染失败', 'UI rendering failed'));
            show(text('UI 渲染失败：', 'UI rendering failed: ') + error.message, true);
          }
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
        clearUI();
        if (running) startWorker();
        source.value = example.source;
        if (help) help.textContent = example.description[en ? 'en' : 'zh'];
        show(text('点击「运行代码」查看结果。', 'Click Run Code to see the result.'), false);
        if (ready && !running) status(readyStatus());
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
      startWorker();
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
            try {
              var selected = new URL(window.location.href).searchParams.get('example');
              if (select && examples[selected]) {
                select.value = selected;
                source.value = examples[selected].source;
                autoRunCode = source.value;
              }
            } catch (_) {}
            var current = examples[select && select.value] || examples.hello;
            if (help && current) help.textContent = current.description[en ? 'en' : 'zh'];
          }
          if (autoRunCode && ready && !running && !hasAutoRun) { hasAutoRun = true; run(); }
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
      clearUI();
      activeSource = source.value;
      execute();
    }
    function execute() {
      running = true;
      if (canvas) canvas.setAttribute('aria-disabled', 'true');
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
      worker.postMessage({type: 'run', source: activeSource || source.value, events: clicks.slice()});
    }
    if (!inline) {
      button.addEventListener('click', run);
      source.addEventListener('input', clearUI);
      if (canvas) {
        function clickAt(x, y) {
          if (!interactive || running || !ready || activeSource !== source.value) return;
          interactive = false;
          clicks.push({x: x, y: y});
          execute();
        }
        canvas.addEventListener('click', function (event) {
          if (inputMode) return;
          var bounds = canvas.getBoundingClientRect();
          if (!bounds.width || !bounds.height) return;
          clickAt(Math.max(0, Math.min(639, Math.floor((event.clientX - bounds.left) * 640 / bounds.width))),
            Math.max(0, Math.min(359, Math.floor((event.clientY - bounds.top) * 360 / bounds.height))));
        });
        canvas.addEventListener('keydown', function (event) {
          if (inputMode) {
            var key = inputKey(event.key);
            if (key) {
              event.preventDefault();
              appendInput({kind: 78, key: key, modifiers: event.shiftKey ? 1 : 0, repeat: event.repeat ? 1 : 0});
              if (event.key === 'Escape' && canvas.blur) canvas.blur();
            }
          } else if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); clickAt(320, 180); }
        });
        function appendInput(input) {
          if (!inputMode || !ready || activeSource !== source.value || (!running && !interactive) ||
              clicks.length + queuedInputs.length >= window.XuPlayCanvas.maxEvents) return;
          if (running) queuedInputs.push(input);
          else { clicks.push(input); execute(); }
        }
        function inputKey(key) {
          return {' ': 32, Escape: 256, Tab: 257, Enter: 258, ArrowLeft: 261, ArrowRight: 262,
            ArrowUp: 263, ArrowDown: 264, Home: 265, End: 266, PageUp: 267, PageDown: 268}[key] || 0;
        }
        function pointerInput(kind, event) {
          var bounds = canvas.getBoundingClientRect();
          if (!bounds.width || !bounds.height) return;
          appendInput({kind: kind,
            x: Math.floor((event.clientX - bounds.left) * 640 / bounds.width),
            y: Math.floor((event.clientY - bounds.top) * 360 / bounds.height),
            button: event.button === 0 ? 1 : 0, buttons: event.buttons || 0});
        }
        canvas.addEventListener('pointerdown', function (event) {
          if (!inputMode || event.button !== 0 || running || !interactive) return;
          event.preventDefault();
          if (canvas.focus) canvas.focus({preventScroll: true});
          pointerActive = true;
          if (canvas.setPointerCapture) canvas.setPointerCapture(event.pointerId);
          pointerInput(72, event);
        });
        canvas.addEventListener('pointermove', function (event) {
          if (inputMode && pointerActive) {
            // Coalesce motion while WASM runs, while preserving down/up order.
            if (queuedInputs.length && queuedInputs.at(-1).kind === 74) queuedInputs.pop();
            pointerInput(74, event);
          }
        });
        canvas.addEventListener('pointerup', function (event) {
          if (!inputMode || !pointerActive) return;
          pointerActive = false;
          pointerInput(73, event);
        });
        canvas.addEventListener('wheel', function (event) {
          if (!inputMode || !ready || activeSource !== source.value || (!running && !interactive)) return;
          event.preventDefault();
          var bounds = canvas.getBoundingClientRect();
          if (!bounds.width || !bounds.height) return;
          // DOM line/page deltas become bounded logical pixels before Xu sees them.
          var unit = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? 360 : 1;
          appendInput({kind: 80,
            x: Math.floor((event.clientX - bounds.left) * 640 / bounds.width),
            y: Math.floor((event.clientY - bounds.top) * 360 / bounds.height),
            dx: Math.max(-100000, Math.min(100000, event.deltaX * unit)),
            dy: Math.max(-100000, Math.min(100000, event.deltaY * unit))});
        }, {passive: false});
        canvas.addEventListener('pointercancel', function () {
          if (inputMode && pointerActive) { pointerActive = false; appendInput({kind: 77}); }
        });
        canvas.addEventListener('lostpointercapture', function () {
          if (inputMode && pointerActive) { pointerActive = false; appendInput({kind: 77}); }
        });
        canvas.addEventListener('keyup', function (event) {
          if (!inputMode) return;
          var key = inputKey(event.key);
          if (key) { event.preventDefault(); appendInput({kind: 79, key: key}); }
        });
        canvas.addEventListener('blur', function (event) {
          // Run Code owns the imminent reset/stop. Starting a blur replay here
          // would turn that same click into Stop before its click handler runs.
          if (event && event.relatedTarget === button) return;
          if (inputMode) { pointerActive = false; appendInput({kind: 77}); }
        });
      }
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
