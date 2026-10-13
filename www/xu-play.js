/* Xu homepage playground: load the compiler-frontend wasm and eval source. */
(function () {
  var script = document.currentScript;
  var wasmUrl = new URL('xu-play.wasm', script.src).href;
  var available = script.getAttribute('data-wasm-available') !== 'false';
  var EXAMPLES = {
    hello: '@main\n\nfn main() int {\n    println("hello")\n    << 0\n}\n',
    hello_errors: '@main\n\n#errors\n\nfn main() int {\n    println("hello")\n    << 0\n}\n',
    ints: '@main\n\nfn add(a int, b int) int {\n    << a + b\n}\n\nfn main() int {\n    println(add(40, 2))\n    << 0\n}\n',
    control: '@main\n\nfn main() int {\n    age := 16\n    if age >= 18 {\n        println("adult")\n    } else {\n        println("minor")\n    }\n    match age {\n        0:13 { println("child") }\n        13:20 { println("teen") }\n        else { println("adult") }\n    }\n    mut n := 3\n    while n > 0 {\n        println(n)\n        n -= 1\n    }\n    for i in 0:5 {\n        println(i)\n    }\n    << 0\n}\n',
    bindings: '@main\n\nconst max = 100\n\nfn main() int {\n    name := "Xu"\n    mut age := 20\n    age += 1\n    println(name)\n    println(age)\n    println(max)\n    << 0\n}\n'
  };

  var wasm = null;
  var loading = null;

  function $id(id) {
    return document.getElementById(id);
  }

  function decode(ptr, len) {
    if (!len) return '';
    var mem = wasm.instance.exports.memory;
    return new TextDecoder('utf-8').decode(new Uint8Array(mem.buffer, ptr, len));
  }

  function loadWasm() {
    if (wasm) return Promise.resolve(wasm);
    if (loading) return loading;
    loading = fetch(wasmUrl)
      .then(function (r) {
        if (!r.ok) throw new Error('failed to fetch Xu playground (' + r.status + ')');
        return r.arrayBuffer();
      })
      .then(function (buf) {
        return WebAssembly.instantiate(buf, {});
      })
      .then(function (w) {
        wasm = w;
        return w;
      });
    return loading;
  }

  function runSource(src) {
    return loadWasm().then(function (w) {
      var exp = w.instance.exports;
      var bytes = new TextEncoder().encode(src);
      var p = exp.xu_alloc(bytes.length);
      new Uint8Array(exp.memory.buffer, p, bytes.length).set(bytes);
      var code = exp.xu_eval(p, bytes.length);
      var out = decode(exp.xu_stdout_ptr(), exp.xu_stdout_len());
      var err = decode(exp.xu_stderr_ptr(), exp.xu_stderr_len());
      exp.xu_free(p, bytes.length);
      return { exit: code, stdout: out, stderr: err };
    });
  }

  function showResult(r) {
    var out = $id('xu-play-out');
    var meta = $id('xu-play-meta');
    if (!out) return;
    var text = '';
    if (r.stderr) text += r.stderr;
    if (r.stdout) text += r.stdout;
    if (!text) text = '(no output)\n';
    out.textContent = text;
    out.className = 'xu-play-out' + (r.exit !== 0 && r.stderr ? ' is-err' : '');
    if (meta) meta.textContent = 'exit ' + r.exit;
  }

  function bind() {
    var ta = $id('xu-play-src');
    var sel = $id('xu-play-ex');
    var btn = $id('xu-play-run');
    var out = $id('xu-play-out');
    if (!ta || !btn) return;

    if (sel) {
      sel.addEventListener('change', function () {
        var k = sel.value;
        if (EXAMPLES[k]) ta.value = EXAMPLES[k];
      });
    }

    if (!available) {
      btn.disabled = true;
      if (out) out.textContent = document.documentElement.lang === 'en'
        ? 'Online execution is not enabled for this deployment. Download Xu to run these examples locally.'
        : '此版本暂未启用在线运行。可下载 Xu，在本机运行这些示例。';
      return;
    }

    btn.addEventListener('click', function () {
      btn.disabled = true;
      if (out) out.textContent = 'running…';
      runSource(ta.value)
        .then(showResult)
        .catch(function (e) {
          showResult({ exit: 1, stdout: '', stderr: String(e) + '\n' });
        })
        .then(function () {
          btn.disabled = false;
        });
    });

    loadWasm().catch(function (e) {
      if (out) {
        out.textContent = 'Could not load Xu wasm: ' + e + '\n';
        out.className = 'xu-play-out is-err';
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bind);
  } else {
    bind();
  }
})();
