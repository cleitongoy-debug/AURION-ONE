/* Contract: app freeze/sleep must never grow a session stopwatch by missing heartbeat intervals. */
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const src=fs.readFileSync('android/app/src/main/assets/dedication.js','utf8');
let now=1000,tick=null;const listeners={},disk=new Map();
const storage={getItem:k=>disk.has(k)?disk.get(k):null,setItem:(k,v)=>disk.set(k,v),removeItem:k=>disk.delete(k)};
const elems={dedTopic:{value:'Mentoria AURION'},dedCategory:{value:'mentoria_ia'},dedProject:{value:'#AURION#EU3'},dedStatus:{textContent:''}};
class FakeDate extends Date{constructor(...args){super(...(args.length?args:[now]))}static now(){return now}}
const document={hidden:false,addEventListener:(kind,fn)=>listeners[kind]=fn};
const ctx={document,window:{},localStorage:storage,$:id=>elems[id]||null,native:()=>'',Date:FakeDate,
  setTimeout:()=>{},setInterval:fn=>{tick=fn},AURION_ID:'test'};
vm.runInNewContext(src,ctx);
const advance=ms=>{now+=ms;tick()};
ctx.dedStart();advance(1000);advance(1000);assert.equal(ctx.dedActive.last,3000);
advance(60000);
let events=ctx.dedLocal();
assert.equal(ctx.dedActive,null);
assert.equal(ctx.dedUnion(events),2000); // measured 2 s, NOT 62 s
assert.equal(events.filter(x=>x.kind==='sleep').length,1);
assert.equal(events.find(x=>x.kind==='sleep').end-events.find(x=>x.kind==='sleep').start,60000);
assert.equal(events.find(x=>x.kind==='sleep').counted,false);
ctx.dedStart();advance(1000);document.hidden=true;listeners.visibilitychange();
events=ctx.dedLocal();
assert.equal(ctx.dedActive,null);
assert.equal(ctx.dedUnion(events),3000);
assert.equal(events.filter(x=>x.kind==='session').length,2);
assert.equal(events.filter(x=>x.kind==='progress').length,0);
console.log('PASS: 60s freeze excluded, sleep logged, visibility pause and measured sessions preserved.');
