const runtimeUrl = new URL('xu-play-runtime.mjs', self.location.href);
runtimeUrl.search = self.location.search;

let runtime;
self.onmessage = async function (event) {
  try {
    if (event.data.type === 'init') {
      const {createRuntime} = await import(runtimeUrl.href);
      const wasmUrl = new URL('xu-play.wasm', self.location.href);
      wasmUrl.search = self.location.search;
      const response = await fetch(wasmUrl);
      if (!response.ok) throw new Error('Could not load Xu playground (HTTP ' + response.status + ')');
      let module;
      if (typeof WebAssembly.compileStreaming === 'function') {
        try {
          module = await WebAssembly.compileStreaming(response.clone());
        } catch (_) {
          module = await WebAssembly.compile(await response.arrayBuffer());
        }
      } else {
        module = await WebAssembly.compile(await response.arrayBuffer());
      }
      runtime = await createRuntime(module);
      // Exercise the parser/checker and interpreter while the controller's
      // loading deadline is active. Cold WASM tiering can otherwise consume
      // the first user's 10-second execution budget on slower browsers.
      const warmup = runtime.run('@main\nfn main() int { << 0 }\n');
      if (warmup.exit !== 0) throw new Error('Xu playground initialization failed: ' + warmup.stderr);
      self.postMessage({type: 'ready'});
    } else if (event.data.type === 'run') {
      if (!runtime) throw new Error('Xu playground is not ready');
      self.postMessage({type: 'result', ...runtime.run(event.data.source, {events: event.data.events})});
    }
  } catch (error) {
    self.postMessage({type: 'error', message: error.message || String(error)});
  }
};
