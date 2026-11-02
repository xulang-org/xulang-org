import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {test} from 'node:test';
import assert from 'node:assert/strict';
const controller=readFileSync(new URL('../www/xu-play-preview.js',import.meta.url),'utf8');
function mount(narrow=true){
 const document={documentElement:{lang:'zh-CN'},activeElement:null};
 class Node {
  constructor(id){this.id='xu-play-'+id;this.attributes={};this.listeners={};this.children=[];this.hidden=false;this.scrollLeft=this.scrollTop=0;this.classList={toggle(){}};}
  setAttribute(k,v){this.attributes[k]=String(v);}
  getAttribute(k){return this.attributes[k]??null;}
  removeAttribute(k){delete this.attributes[k];}
  addEventListener(k,f){(this.listeners[k]||=[]).push(f);}
  send(k,event={}){for(const f of this.listeners[k]||[])f(event);}
  click(){this.focus();this.send('click');}
  focus(){document.activeElement=this;}
  contains(n){return n===this||this.children.some(c=>c.contains(n));}
  setPointerCapture(id){this.captured=id;}
  querySelector(s){return this.queries?.[s]||null;}
 }
 const nodes={};const get=id=>nodes[id]||=new Node(id);
 for(const id of ['workspace','mobile-tabs','panes','explorer','editor','preview-panel','console-panel','preview-viewport','preview-fit','preview-actual','preview-expand','preview-pan','preview-pan-hint','canvas','library','library-back','library-list','library-search','library-detail','src','add','clear'])get(id);
 for(const id of ['files','editor','preview','console'])get('mobile-tab-'+id);
 get('preview-panel').setAttribute('role','region');get('console-panel').setAttribute('role','region');
 get('panes').queries={'.play-source-pane':get('source-wrapper'),'.play-results':get('result-wrapper')};
 get('source-wrapper').children=[get('explorer'),get('editor')];get('result-wrapper').children=[get('preview-panel'),get('console-panel')];
 get('editor').children=[get('src')];get('preview-panel').children=[get('preview-fit'),get('preview-actual'),get('preview-pan'),get('canvas')];
 get('library-list').queries={'button[aria-current="true"]':get('selected-template')};get('library-detail').queries={h3:get('template-heading')};
 get('library').children=[get('library-back'),get('library-search'),get('library-list'),get('library-groups'),get('library-detail')];
 get('library-list').children=[get('selected-template')];get('library-detail').children=[get('template-heading')];
 get('src').value='unchanged source';get('src').scrollTop=80;
 Object.defineProperty(get('canvas'),'width',{value:640,writable:false});Object.defineProperty(get('canvas'),'height',{value:360,writable:false});
 document.getElementById=id=>nodes[id.replace('xu-play-','')];
 const changes=[];const media={matches:narrow,addEventListener(k,f){changes.push(f);}};
 const window={matchMedia:()=>media};vm.runInNewContext(controller,{document,window});
 return {get,window,document,resize(value){media.matches=value;for(const f of changes)f();}};
}
test('phone views keep one accessible panel while preserving editor and canvas state',()=>{
 const p=mount();assert.equal(p.get('workspace').getAttribute('data-mobile-view'),'editor');
 assert.equal(p.get('mobile-tabs').hidden,false);assert.equal(p.get('editor').hidden,false);
 for(const id of ['explorer','preview-panel','console-panel'])assert.equal(p.get(id).hidden,true);
 p.get('mobile-tab-files').click();assert.equal(p.get('explorer').hidden,false);assert.equal(p.get('editor').hidden,true);
 p.window.XuPlayMobile.show('editor');assert.equal(p.get('src').value,'unchanged source');assert.equal(p.get('src').scrollTop,80);
 assert.equal(p.get('canvas').width,640);assert.equal(p.get('canvas').height,360);
 assert.equal(p.get('editor').getAttribute('role'),'tabpanel');assert.equal(p.get('editor').getAttribute('aria-labelledby'),'xu-play-mobile-tab-editor');
});
test('mobile tabs support arrows, Home and End with one Tab entry point',()=>{
 const p=mount();let prevented=0;const key=(id,key)=>p.get('mobile-tab-'+id).send('keydown',{key,preventDefault(){prevented++;}});
 key('editor','ArrowRight');assert.equal(p.get('workspace').getAttribute('data-mobile-view'),'preview');
 assert.equal(p.document.activeElement,p.get('mobile-tab-preview'));
 key('preview','End');assert.equal(p.get('workspace').getAttribute('data-mobile-view'),'console');
 key('console','Home');assert.equal(p.get('workspace').getAttribute('data-mobile-view'),'files');
 key('files','ArrowLeft');assert.equal(p.get('workspace').getAttribute('data-mobile-view'),'console');
 assert.equal(prevented,4);assert.equal(['files','editor','preview','console'].filter(id=>p.get('mobile-tab-'+id).tabIndex===0).length,1);
});
test('fresh run follows its result while manual navigation and edits retain user choice',()=>{
 const p=mount(),api=p.window.XuPlayMobile;
 api.beginRun();assert.equal(p.get('workspace').getAttribute('data-mobile-view'),'console');
 api.completeRun(true);assert.equal(p.get('workspace').getAttribute('data-mobile-view'),'preview');
 api.show('console');api.completeRun(true);assert.equal(p.get('workspace').getAttribute('data-mobile-view'),'console');
 api.beginRun();p.get('mobile-tab-editor').click();api.completeRun(true);assert.equal(p.get('workspace').getAttribute('data-mobile-view'),'editor');
 api.beginRun();api.cancelRun();api.show('editor');api.completeRun(false);assert.equal(p.get('workspace').getAttribute('data-mobile-view'),'editor');
});
test('desktop restores simultaneous panels and meaningful focus without rebuilding resources',()=>{
 const p=mount();p.get('mobile-tab-preview').click();p.resize(false);
 assert.equal(p.get('mobile-tabs').hidden,true);assert.equal(p.get('workspace').getAttribute('data-mobile-view'),null);
 for(const id of ['explorer','editor','preview-panel','console-panel','source-wrapper','result-wrapper'])assert.equal(p.get(id).hidden,false);
 assert.equal(p.get('editor').getAttribute('role'),null);assert.equal(p.get('preview-panel').getAttribute('role'),'region');
 assert.equal(p.document.activeElement,p.get('preview-fit'));p.resize(true);
 assert.equal(p.get('workspace').getAttribute('data-mobile-view'),'preview');assert.equal(p.get('canvas').width,640);
});
test('template detail and back navigation preserve selection and focus',()=>{
 const p=mount();p.window.XuPlayMobile.templateDetail();
 assert.equal(p.get('library').getAttribute('data-mobile-template'),'detail');assert.equal(p.get('library-back').hidden,false);
 assert.equal(p.document.activeElement,p.get('template-heading'));p.get('library-back').click();
 assert.equal(p.get('library').getAttribute('data-mobile-template'),'list');assert.equal(p.document.activeElement,p.get('selected-template'));
 p.resize(false);assert.equal(p.get('library-back').hidden,true);assert.equal(p.get('library').getAttribute('data-mobile-template'),null);
});
test('template dialog keeps focus visible when changing between phone and desktop',()=>{
 const p=mount(false);p.window.XuPlayMobile.templateDetail();p.get('selected-template').focus();p.resize(true);
 assert.equal(p.document.activeElement,p.get('template-heading'));
 p.get('library-back').focus();p.resize(false);assert.equal(p.document.activeElement,p.get('library-search'));
 p.resize(true);assert.equal(p.document.activeElement,p.get('template-heading'));
});
test('100% phone pan scrolls presentation without sending gestures to controls',()=>{
 const p=mount();assert.equal(p.get('preview-pan').hidden,true);p.get('preview-actual').click();assert.equal(p.get('preview-pan').hidden,false);
 p.get('preview-pan').click();assert.equal(p.get('canvas').inert,true);assert.equal(p.get('canvas').tabIndex,-1);
 const v=p.get('preview-viewport'),pointer={button:0,pointerId:1,clientX:100,clientY:80,preventDefault(){}};
 v.send('pointerdown',pointer);v.send('pointermove',{...pointer,clientX:40,clientY:50});
 assert.equal(v.scrollLeft,60);assert.equal(v.scrollTop,30);v.send('pointerup',pointer);
 v.send('pointermove',{...pointer,clientX:0});assert.equal(v.scrollLeft,60);
 p.get('preview-fit').click();assert.equal(p.get('canvas').inert,false);assert.equal(p.get('preview-pan').hidden,true);
 assert.equal(p.get('canvas').width,640);assert.equal(p.get('canvas').height,360);
});
test('leaving phone size restores focus from the disappearing pan control',()=>{
 const p=mount();p.get('preview-actual').click();p.get('preview-pan').click();p.resize(false);
 assert.equal(p.get('preview-pan').hidden,true);assert.equal(p.get('canvas').inert,false);
 assert.equal(p.document.activeElement,p.get('preview-actual'));
});
