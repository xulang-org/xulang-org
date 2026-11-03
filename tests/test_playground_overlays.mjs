import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {createRuntime} from '../www/xu-play-runtime.mjs';
const module=await WebAssembly.compile(readFileSync(new URL('../build/playground/xu-play.wasm',import.meta.url)));
const projects=JSON.parse(readFileSync(new URL('../www/xu-play-examples.json',import.meta.url))).projects;
const canvas={};vm.runInNewContext(readFileSync(new URL('../www/xu-play-canvas.js',import.meta.url),'utf8'),canvas);
const click=(x,y)=>[{kind:72,x,y,button:1,buttons:1},{kind:73,x,y,button:1}];
const key=(key,modifiers=0)=>[{kind:78,key,modifiers},{kind:79,key,modifiers}];
function run(runtime,slug,events){const r=runtime.run(projects['widget-'+slug].files['main.xu'],{events});assert.equal(r.exit,0,r.stderr);return r;}
function labels(r){return Array.from(canvas.XuPlayCanvas.frame(r.ui.commands)).filter(c=>c.op==='layout_text').map(c=>c.args.at(-1));}

test('MultiSelect paints its popup, retains multiple checks, unchecks, and dismisses',async()=>{
 const r=await createRuntime(module),open=click(100,108);
 for(const name of ['Design','Develop','Review'])assert.ok(labels(run(r,'multi-select',open)).includes(name),name+' must be visible');
 const first=[...open,...click(100,150)];assert.equal(run(r,'multi-select',first).stdout,'Selected count: 1\n');
 const second=[...first,...click(100,205)];assert.equal(run(r,'multi-select',second).stdout,'Selected count: 2\n');
 const third=[...second,...click(100,150)];assert.equal(run(r,'multi-select',third).stdout,'Selected count: 1\n');
 const closed=run(r,'multi-select',[...third,...key(256)]);assert.ok(!labels(closed).includes('Review'));
});
test('Select paints visible choices and a pointer selects the second option',async()=>{
 const r=await createRuntime(module),open=click(100,108);
 assert.ok(labels(run(r,'select',open)).includes('Develop'));
 assert.equal(run(r,'select',[...open,...click(100,205)]).stdout,'Selected: 1\n');
});
test('ComboBox opens a menu, selects, filters, and closes without losing its value',async()=>{
 const r=await createRuntime(module),open=click(100,125);
 const visible=labels(run(r,'combo-box',open));assert.ok(visible.includes('History 历史'));assert.ok(visible.includes('Output 输出'));
 const chosen=run(r,'combo-box',[...open,...key(264),...key(258)]);assert.equal(chosen.stdout,'Selected: History 历史\n');
 assert.ok(!labels(chosen).includes('Output 输出'));
 const empty=run(r,'combo-box',[...open,...key(88)]);assert.ok(labels(empty).includes('No matches 无匹配项'));
 assert.ok(!labels(run(r,'combo-box',[...open,...key(256)])).includes('History 历史'));
 const backspace=run(r,'combo-box',[...key(257),...key(259)]);assert.equal(backspace.stdout,'Selected: Workspace 工作\n','Backspace removes a complete UTF-8 character');
});
test('Modal opens, traps Tab in both directions, blocks background clicks, and restores focus',async()=>{
 const r=await createRuntime(module),open=click(100,135);
 const opened=run(r,'modal',open);assert.equal(opened.stdout,'Modal: open\nResult: pending\nFocus: 2\n');
 assert.ok(labels(opened).includes('Cancel 取消'));assert.ok(labels(opened).includes('Apply 应用'));
 assert.match(run(r,'modal',[...open,...key(257)]).stdout,/Focus: 3\n/);
 assert.match(run(r,'modal',[...open,...key(257),...key(257)]).stdout,/Focus: 2\n/);
 assert.match(run(r,'modal',[...open,...key(257,1)]).stdout,/Focus: 3\n/);
 assert.match(run(r,'modal',[...open,...click(100,135)]).stdout,/Modal: open/);
 for(const ending of [key(256),click(285,248),click(478,108)]){
   const closed=run(r,'modal',[...open,...ending]);assert.equal(closed.stdout,'Modal: closed\nResult: cancelled\nFocus: 1\n');
   assert.ok(!labels(closed).includes('Apply 应用'));
 }
 const applied=run(r,'modal',[...open,...key(257),...key(258)]);assert.equal(applied.stdout,'Modal: closed\nResult: applied\nFocus: 1\n');
 assert.equal(run(r,'modal',[...open,...click(400,248)]).stdout,applied.stdout);
});
