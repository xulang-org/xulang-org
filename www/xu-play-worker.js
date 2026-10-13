import {createRuntime} from './xu-play-runtime.mjs';

let runtime;
self.onmessage = async function (event) {
  try {
    if (event.data.type === 'init') {
      const response = await fetch(new URL('xu-play.wasm', self.location.href));
      if (!response.ok) throw new Error('Could not load Xu playground (HTTP ' + response.status + ')');
      runtime = await createRuntime(await response.arrayBuffer());
      self.postMessage({type: 'ready'});
    } else if (event.data.type === 'run') {
      if (!runtime) throw new Error('Xu playground is not ready');
      self.postMessage({type: 'result', ...runtime.run(event.data.source)});
    }
  } catch (error) {
    self.postMessage({type: 'error', message: error.message || String(error)});
  }
};
