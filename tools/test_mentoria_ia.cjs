/* Synthetic tests: study time vs observed input vs unverified gaps. No PC/POCO needed. */
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('android/app/src/main/assets/mentoria_ia.js','utf8');
let wall=1000,mono=1000;
const disk=new Map(),storage={getItem:k=>disk.has(k)?disk.get(k):null,setItem:(k,v)=>disk.set(k,v)};
const root={};vm.runInNewContext(source,{window:root,document:undefined,localStorage:undefined});
const e=root.AurionMentoriaEngine(storage,{wall:()=>wall,mono:()=>mono});
function pulse(ms){wall+=ms;mono+=ms;e.observeInput('agentText');}
e.observeInput('agentText');assert.equal(e.summary().measuredMs,0);
pulse(1000);pulse(1000);assert.equal(e.summary().measuredMs,2000);
pulse(60000);assert.equal(e.summary().measuredMs,2000);
assert.equal(e.summary().gaps,1);assert.equal(e.summary().gapMs,60000);
pulse(1500);assert.equal(e.summary().measuredMs,3500);
e.message('OPERADOR_ENVIO','agentText','local');
e.message('IA_RECEBIMENTO','agentText','local');
assert.equal(e.summary().userMessages,1);assert.equal(e.summary().replies,1);
e.pause('APP_OCULTO');wall+=90000;mono+=90000;e.resume();e.observeInput('agentText');
assert.equal(e.summary().measuredMs,3500);assert.equal(e.summary().gaps,2);
e.message('IA_FALHA','agentText','cloud');assert.equal(e.summary().failures,1);
const e2=root.AurionMentoriaEngine(storage,{wall:()=>wall,mono:()=>mono});
wall+=40000;mono+=40000;e2.observeInput('agentText');
assert.equal(e2.summary().measuredMs,3500);
assert.equal(e2.summary().gaps,3);
assert.ok(e2.snapshot().messages.every(x=>x.contentStored===false));
assert.equal(e2.summary().gapMs,190000);
assert.ok(!e2.export().includes('texto da mensagem privada'));
assert.throws(()=>e2.message('MENSAGEM_DESCONHECIDA','agentText','cloud'));
console.log('PASS: mentoria input observado, lacunas/sleeps, retomada, eventos, sem texto privado.');
