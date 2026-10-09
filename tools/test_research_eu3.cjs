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
