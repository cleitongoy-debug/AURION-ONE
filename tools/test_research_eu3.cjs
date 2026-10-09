// EU3 isolated tests: research evidence is not human-study telemetry.
const assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
const src=fs.readFileSync('android/app/src/main/assets/research_eu3.js','utf8');
function store(){const d=new Map();return {d,s:{getItem:k=>d.get(k),setItem:(k,v)=>d.set(k,v)}}}
function open(s){const ctx={};vm.runInNewContext(src,ctx);return ctx.AurionResearchEngine(s)}
function statuses(e){return e.items().map(x=>x.status).join(',')}
function chain(e){
 const a=e.add('Fonte A','arquivo:1-20'),b=e.add('Teste B','print:2',[a.id]),c=e.add('Experimento C','arquivo:3',[b.id]);
 assert.throws(()=>e.start(c.id,0));
 for(const [x,label] of [[a,'A'],[b,'B'],[c,'C']]){e.start(x.id,100);e.tick(1100);e.proof(x.id,'Trecho '+label,'Resultado '+label,true)}
 return {a,b,c};
}
{
 const {s}=store();let e=open(s);
 const a=e.add('Fonte A','arquivo:1-20'),b=e.add('Teste B','print:2',[a.id]);
 assert.throws(()=>e.start(b.id,0));e.start(a.id,0);e.tick(1000);e.tick(100000);
 assert.equal(e.items()[0].milliseconds,1000);assert.throws(()=>e.proof(a.id,'','',true));
 e.proof(a.id,'1-20','Reproduzido',true);e.start(b.id,100001);e.tick(101001);e.pause(101501);
 e=open(s);assert.equal(e.active(),null);assert.equal(e.items()[1].milliseconds,1500);
 assert.equal(e.items()[0].status,'VALIDADO');assert.throws(()=>e.add('X','source',['missing']));
}
{
 const {s}=store();let e=open(s);const {a,b,c}=chain(e);
 e.proof(a.id,'Contraprova','Falhou',false);
 assert.equal(statuses(e),'EXPERIMENTAL,REVISAO_PENDENTE,REVISAO_PENDENTE');
 assert.equal(e.items().map(x=>x.receipts.length).join(','),'2,1,1');
 assert.equal(e.items()[1].review_reason,'PRE_REQUISITO_REPROVADO');
 assert.equal(e.ready(e.items()[1]),false);assert.equal(e.ready(e.items()[2]),false);
 assert.throws(()=>e.start(b.id,400));
 e=open(s);assert.equal(statuses(e),'EXPERIMENTAL,REVISAO_PENDENTE,REVISAO_PENDENTE');
 e.start(a.id,450);e.proof(a.id,'Nova prova A','Aprovada',true);
 assert.equal(e.items()[1].status,'REVISAO_PENDENTE');
 e.start(b.id,500);e.proof(b.id,'Nova prova B','Aprovada',true);
 assert.equal(e.items()[2].status,'REVISAO_PENDENTE');
 e.start(c.id,600);e.proof(c.id,'Nova prova C','Aprovada',true);
 assert.equal(statuses(e),'VALIDADO,VALIDADO,VALIDADO');
 assert.equal(e.items().map(x=>x.receipts.length).join(','),'3,2,2');
 assert.equal(Object.hasOwn(e.items()[2],'review_reason'),false);
}
{
 const {s}=store();const e=open(s);const {a,c}=chain(e);
 const d=e.add('Combinada D','arquivo:4',[a.id,c.id]);e.start(d.id,100);e.proof(d.id,'D','OK',true);
 e.proof(a.id,'Contraprova','Falha',false);
 assert.equal(e.items().find(x=>x.id===d.id).status,'REVISAO_PENDENTE');
}
{
 const {d,s}=store();const e=open(s);chain(e);
 const raw=JSON.parse(d.get('aurion_eu3_research_v1'));raw.items[0].status='EXPERIMENTAL';
 d.set('aurion_eu3_research_v1',JSON.stringify(raw));
 const repaired=open(s);
 assert.equal(statuses(repaired),'EXPERIMENTAL,REVISAO_PENDENTE,REVISAO_PENDENTE');
 assert.equal(repaired.items()[2].receipts.length,1);
}
console.log('PASS: EU3 dependency invalidation, review, revalidation, persistence and bounded timer');


// CONTRATO DE RESTAURAÇÃO EU3 — nenhuma importação deve apagar provas locais.
function fresh(){const {d,s}=store();return {d,s,e:open(s)};}
function exported(x){return JSON.stringify({version:1,items:x});}
function item(id,deps=[],status='VALIDADO'){
 return {id,title:id,source:'arquivo:'+id,dependencies:deps,status,milliseconds:0,
   receipts:[{at:'2026-10-09T20:00:00.000Z',range:'linhas 1-2',result:'reproduzido',passed:true}]};
}
{
 const source=fresh(),a=source.e.add('Fonte offline A','arquivo local');
 source.e.start(a.id,0);source.e.proof(a.id,'linhas 1-2','evidência local',true);
 const backup=source.e.export(),target=fresh();
 const preview=target.e.previewRestore(backup);
 assert.equal(preview.added,1);assert.equal(preview.unchanged,0);
 assert.equal(target.d.size,0,'prévia não grava no armazenamento');
 target.e.restore(backup);
 assert.equal(target.e.items()[0].receipts.length,1);
 assert.ok(target.d.has('aurion_eu3_research_v1_pre_restore_v1'),'backup pré-importação retido');
 target.e.restore(backup);
 assert.equal(target.e.items().length,1,'a mesma importação é idempotente');
 assert.throws(()=>target.e.restore(backup.slice(0,-1)),'JSON truncado recusado');
 assert.equal(target.e.items().length,1);
 assert.throws(()=>target.e.restore(exported([{...source.e.items()[0],title:'Alterado'}])),'ID divergente não sobrescreve');
 assert.equal(target.e.items()[0].title,'Fonte offline A');
}
{
 const x=fresh(),before=x.e.export();
 assert.throws(()=>x.e.restore(exported([item('X',['desconhecido'])])),'dependência desconhecida rejeitada');
 assert.throws(()=>x.e.restore(exported([item('A',['B']),item('B',['A'])])),'ciclo rejeitado');
 assert.throws(()=>x.e.restore(exported([item('A'),item('A')])),'duplicação no backup rejeitada');
 assert.throws(()=>x.e.restore(exported([{...item('A'),milliseconds:-1}])),'tempo negativo rejeitado');
 assert.throws(()=>x.e.restore(exported([{...item('A'),receipts:[{...item('A').receipts[0],passed:'true'}]}])),'comprovante inválido rejeitado');
 assert.equal(x.e.export(),before,'nenhuma importação falha altera os dados');
 assert.equal(x.d.size,0,'nenhuma tentativa falha grava no armazenamento');
}
{
 const x=fresh();const raw=exported([item('A',[],'EXPERIMENTAL'),item('B',['A']),item('C',['B'])]);
 assert.equal(x.e.previewRestore(raw).review,2);
 x.e.restore(raw);
 assert.equal(statuses(x.e),'EXPERIMENTAL,REVISAO_PENDENTE,REVISAO_PENDENTE');
 assert.equal(x.e.items()[2].receipts.length,1,'provas antigas mantidas ao marcar revisão');
}
{
 const initial=fresh(),original=initial.e.add('Existente','fonte original');
 const unsafe={getItem:initial.s.getItem,setItem:(k,v)=>{if(k==='aurion_eu3_research_v1')throw Error('quota simulada');initial.s.setItem(k,v)}};
 const e=open(unsafe),before=e.export();
 assert.throws(()=>e.restore(exported([{...original,id:'novo'}])),'gravação indisponível interrompe');
 assert.equal(e.export(),before,'nenhuma alteração de memória em falha de escrita');
}
console.log('PASS: EU3 restore import: idempotência, validação, backup, não-sobrescrita, atomicidade e revisão');
