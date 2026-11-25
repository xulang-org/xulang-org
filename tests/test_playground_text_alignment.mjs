import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {test} from 'node:test';
import assert from 'node:assert/strict';

const scope={};
vm.runInNewContext(readFileSync(new URL('../www/xu-play-canvas.js',import.meta.url),'utf8'),scope);
const host=scope.XuPlayCanvas;
function harness(metrics){
  const calls=[];
  const ctx={setTransform(){},fillRect(){},save(){},restore(){},drawImage(){},
    measureText(text){calls.push({op:'measure',text,baseline:this.textBaseline});return metrics;},
    fillText(...args){calls.push({op:'paint',args,baseline:this.textBaseline});},
    scale(){assert.fail('text must keep natural glyph proportions');}};
  const canvas={ownerDocument:{defaultView:{devicePixelRatio:1},createElement:()=>({getContext:()=>ctx})},getContext:()=>ctx};
  return {canvas,ctx,calls};
}
test('legacy widget text centers its actual ink within the Xu line box',()=>{
  for(const [text,ascent,descent] of [['Apply',11,3],['偏好设置',12,0],['Save 保存',12,2]]){
    const {canvas,calls}=harness({width:1000,actualBoundingBoxAscent:ascent,actualBoundingBoxDescent:descent});
    host.render(canvas,`begin\nlayout_text\t20\t39.25\t14\t#282329\t10\t${text}\npresent\n`);
    const paint=calls.find(c=>c.op==='paint');
    assert.equal(paint.baseline,'alphabetic');
    assert.equal(paint.args[0],text);
    assert.equal(paint.args[1],20);
    assert.equal(paint.args.length,3,'do not impose estimated horizontal advance');
    assert.equal((paint.args[2]-ascent+paint.args[2]+descent)/2,48);
    assert.equal(calls.find(c=>c.op==='measure').baseline,'alphabetic');
  }
});
test('text alignment follows each font size instead of a fixed pixel offset',()=>{
  for(const size of [10,14,22,32]){
    const ascent=size*0.7,descent=size*0.2;
    const {canvas,calls}=harness({actualBoundingBoxAscent:ascent,actualBoundingBoxDescent:descent});
    host.render(canvas,`begin\nlayout_text\t20\t10\t${size}\t#282329\t80\tCancel\npresent\n`);
    const paint=calls.find(c=>c.op==='paint');
    assert.ok(Math.abs((paint.args[2]-ascent+paint.args[2]+descent)/2-(10+size*1.25/2))<1e-10);
  }
});
test('missing ink metrics use font metrics and then an em-box fallback without moving raw text',()=>{
  for(const metrics of [{fontBoundingBoxAscent:12,fontBoundingBoxDescent:4},{width:40},undefined]){
    const {canvas,calls}=harness(metrics);
    host.render(canvas,'begin\nlayout_text\t0\t10\t20\t#282329\t80\tLabel\ntext\t7\t9\t14\t#282329\tRaw\npresent\n');
    const paints=calls.filter(c=>c.op==='paint');
    assert.equal(paints[0].args[2],metrics?.fontBoundingBoxAscent?26.5:28.5);
    assert.deepEqual(paints[1],{op:'paint',args:['Raw',7,9],baseline:'top'});
  }
});
test('input examples keep sans CJK labels un-squeezed and advance wide chars by 2 cells in mono mode',()=>{
  const {canvas,calls}=harness({actualBoundingBoxAscent:11,actualBoundingBoxDescent:3,width:12});
  canvas.dataset={example:'widget-input'};
  host.render(canvas,'begin\nlayout_text\t48\t90\t14\t#282329\t134.4\tUser email 用户邮箱 *\nfont\tmono\nlayout_text\t62\t128\t15\t#282329\t54\ta中b\nfont\tsans\nlayout_text\t32\t48\t12\t#6d626e\t120\t浏览器输入预览\npresent\n');
  const paints=calls.filter(c=>c.op==='paint');
  assert.equal(paints[0].args[0],'User email 用户邮箱 *','UI labels must never be split into overlapping mono cells');
  assert.deepEqual(paints.slice(1,4).map(p=>[p.args[0],p.args[1]]),[['a',62],['中',74],['b',89]]);
  assert.equal(paints[4].args[0],'浏览器输入预览');
});
test('cursor_rect hit testing and clipboard escaping validate inputs safely',()=>{
  const {canvas}=harness({actualBoundingBoxAscent:10,actualBoundingBoxDescent:2});
  host.render(canvas,'begin\ncursor_rect\t48\t114\t500\t44\ttext\ncursor_rect\t446\t117\t32\t32\tpointer\nclipboard\t3\tline1\\nline2\\t\\\\end\npresent\n');
  assert.equal(host.cursorAt(canvas,100,130),'text');
  assert.equal(host.cursorAt(canvas,460,130),'pointer');
  assert.equal(host.cursorAt(canvas,10,10),'');
  assert.deepEqual({...host.clipboardOf(canvas)},{seq:3,text:'line1\nline2\t\\end'});
  assert.throws(()=>host.frame('begin\ncursor_rect\t0\t0\t10\t10\tjavascript:bad\npresent'),/Invalid UI cursor/);
  assert.throws(()=>host.frame('begin\nfont\tcomic\npresent'),/Invalid UI font/);
});
