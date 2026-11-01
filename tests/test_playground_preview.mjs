import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {test} from 'node:test';
import assert from 'node:assert/strict';

const controller = readFileSync(new URL('../www/xu-play-preview.js', import.meta.url), 'utf8');

function mount(lang = 'zh-CN') {
  const nodes = {};
  for (const id of ['panel', 'viewport', 'fit', 'actual', 'expand']) {
    nodes[id] = {attributes:{}, listeners:{},
      setAttribute(name, value) { this.attributes[name] = value; },
      addEventListener(name, handler) { this.listeners[name] = handler; },
      click() { this.listeners.click(); }
    };
  }
  const classes = new Set();
  const panes = {classList:{toggle(name, value) { value ? classes.add(name) : classes.delete(name); }}};
  // Display changes must leave the existing canvas and running Xu state intact.
  const canvas = Object.freeze({width:1280,height:720});
  const ids = Object.fromEntries(Object.entries(nodes).map(([key,value]) => [
    'xu-play-preview-' + key, value
  ]));
  ids['xu-play-panes'] = panes;
  ids['xu-play-canvas'] = canvas;
  vm.runInNewContext(controller, {document:{documentElement:{lang}, getElementById:id=>ids[id]}});
  return {...nodes, classes, canvas};
}

test('100% exposes a keyboard scrolling entry point; Fit restores fitted presentation', () => {
  const {panel,viewport,fit,actual,canvas} = mount();
  assert.equal(panel.attributes['data-preview-size'], 'fit');
  assert.equal(viewport.tabIndex, -1);
  actual.click();
  assert.equal(panel.attributes['data-preview-size'], 'actual');
  assert.equal(actual.attributes['aria-pressed'], 'true');
  assert.equal(fit.attributes['aria-pressed'], 'false');
  assert.equal(viewport.tabIndex, 0);
  fit.click();
  assert.equal(fit.attributes['aria-pressed'], 'true');
  assert.equal(actual.attributes['aria-pressed'], 'false');
  assert.equal(viewport.tabIndex, -1);
  assert.equal(canvas.width, 1280);
  assert.equal(canvas.height, 720);
});

test('expanded preview returns to the editor and preserves the selected size in both languages', () => {
  for (const [lang,open,close] of [['en','Expand','Back to editor'],['zh-CN','扩大预览','返回编辑']]) {
    const {panel,actual,expand,classes} = mount(lang);
    actual.click();
    expand.click();
    assert.ok(classes.has('is-preview-expanded'));
    assert.equal(expand.attributes['aria-expanded'], 'true');
    assert.equal(expand.textContent, close);
    expand.click();
    assert.ok(!classes.has('is-preview-expanded'));
    assert.equal(expand.attributes['aria-expanded'], 'false');
    assert.equal(expand.textContent, open);
    assert.equal(panel.attributes['data-preview-size'], 'actual');
  }
});

test('preview controller leaves other pages alone', () => {
  vm.runInNewContext(controller, {document:{getElementById:()=>null}});
});
