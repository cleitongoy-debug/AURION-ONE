/* AURION: local interaction evidence; no ChatGPT.com telemetry or automatic human-attention inference. */
(function(root){
'use strict';
const KEY='aurion_mentoria_ia_v1',MAX_DELTA_MS=8000,MAX_RECORDS=5000;
function create(storage,clock){
 const wall=clock?.wall||(()=>Date.now()),mono=clock?.mono||(()=>performance.now());
 let data;try{data=JSON.parse(storage.getItem(KEY))}catch(e){}
 if(!data||data.version!==1||!Array.isArray(data.bouts)||!Array.isArray(data.gaps)||!Array.isArray(data.messages)){
   data={version:1,bouts:[],gaps:[],messages:[],checkpoint:null};
 }
 let last=null,seq=0,visible=true;
 const save=()=>storage.setItem(KEY,JSON.stringify(data));
 const id=()=>String(wall())+'-'+(++seq)+'-'+Math.random().toString(36).slice(2,8);
 function ensureCapacity(){
   if(data.bouts.length+data.gaps.length+data.messages.length>=MAX_RECORDS)
     throw Error('Diário de mentoria cheio. Exporte o JSON; nenhum registro antigo será descartado.');
 }
 function addGap(from,to,reason){
   if(!Number.isFinite(from)||!Number.isFinite(to)||to<=from)return;
   ensureCapacity();
   data.gaps.push({id:id(),from,to,reason,counted:false});save();
 }
 function observeInput(channel='agente'){
   if(!visible)return;
   const t=wall(),m=mono();
   if(!Number.isFinite(t)||!Number.isFinite(m))return;
   if(last){
     const delta=m-last.mono,calendar=t-last.wall;
     if(delta>0&&delta<=MAX_DELTA_MS&&calendar>=0&&calendar<=MAX_DELTA_MS+2000&&last.channel===channel){
       const b=data.bouts[data.bouts.length-1];
       if(b&&b.id===last.boutId){
         b.end=t;b.measuredMs+=delta;b.inputSignals++;
       }else throw Error('Inconsistência no segmento de mentoria.');
     }else{
       addGap(last.wall,t,'GAP_NAO_AFERIDO');
       ensureCapacity();data.bouts.push({id:id(),start:t,end:t,measuredMs:0,inputSignals:1,channel,proof:'EVENTOS_DE_ENTRADA'});
     }
   }else{
     if(data.checkpoint&&t>data.checkpoint.wall)
       addGap(data.checkpoint.wall,t,'RETOMADA_SEM_MEDICAO');
     ensureCapacity();data.bouts.push({id:id(),start:t,end:t,measuredMs:0,inputSignals:1,channel,proof:'EVENTOS_DE_ENTRADA'});
   }
   const bout=data.bouts[data.bouts.length-1];
   last={wall:t,mono:m,channel,boutId:bout.id};
   data.checkpoint={wall:t,channel};save();
 }
 function message(kind,channel='agente',provider='não identificado'){
   if(!['OPERADOR_ENVIO','IA_RECEBIMENTO','IA_FALHA'].includes(kind))throw Error('Tipo de evento inválido');
   const t=wall();ensureCapacity();
   data.messages.push({id:id(),at:t,kind,channel:String(channel).slice(0,50),provider:String(provider).slice(0,50),contentStored:false});
   // A reply measures an event, not the time the operator was working while waiting.
   save();
 }
 function pause(reason='APLICATIVO_OCULTO'){
   if(last){data.checkpoint={wall:last.wall,channel:last.channel};last=null;save();}
   visible=false;
 }
 function resume(){visible=true;}
 function summary(){
   return {measuredMs:data.bouts.reduce((n,b)=>n+b.measuredMs,0),
     humanInputSignals:data.bouts.reduce((n,b)=>n+b.inputSignals,0),
     userMessages:data.messages.filter(m=>m.kind==='OPERADOR_ENVIO').length,
     replies:data.messages.filter(m=>m.kind==='IA_RECEBIMENTO').length,
     failures:data.messages.filter(m=>m.kind==='IA_FALHA').length,
     gaps:data.gaps.length,
     gapMs:data.gaps.reduce((n,g)=>n+g.to-g.from,0),
     sources:[...new Set(data.bouts.map(b=>b.channel))],
     note:'Apenas atividade de entrada observada no app AURION; sem tempo de leitura, estudo passivo ou ChatGPT externo.'};
 }
 return {observeInput,message,pause,resume,summary,export:()=>JSON.stringify(data,null,2),snapshot:()=>JSON.parse(JSON.stringify(data))};
}
root.AurionMentoriaEngine=create;
if(typeof document==='undefined'||typeof localStorage==='undefined')return;
const ledger=create(localStorage);
function render(){
 const s=ledger.summary(),format=ms=>{const v=Math.floor(ms/1000);return Math.floor(v/3600)+'h '+String(Math.floor(v%3600/60)).padStart(2,'0')+'m '+String(v%60).padStart(2,'0')+'s'};
 const q=document.getElementById('mentoriaPainel');
 if(q)q.textContent='Interação observada: '+format(s.measuredMs)+' · '+s.userMessages+' mensagens do operador · '+s.replies+' respostas · '+s.gaps+' lacunas/sleeps não contados ('+format(s.gapMs)+')';
}
const monitored=new Set(['agentText','guideQuestion','labPrompt']);
document.addEventListener('input',event=>{
 if(!event.target||!monitored.has(event.target.id)||document.hidden)return;
 try{ledger.observeInput(event.target.id);render();}catch(e){const q=document.getElementById('mentoriaPainel');if(q)q.textContent='ERRO: '+e.message;}
});
document.addEventListener('visibilitychange',()=>{if(document.hidden)ledger.pause('APP_OCULTO');else ledger.resume();render();});
root.addEventListener('pagehide',()=>ledger.pause('PAGINA_FECHADA'));
root.aurionInteraction={
 message:(kind,channel,provider)=>{try{ledger.message(kind,channel,provider);render();return true;}catch(e){const q=document.getElementById('mentoriaPainel');if(q)q.textContent='ERRO no registro (mensagem não bloqueada): '+e.message;return false;}},
 summary:()=>ledger.summary(),
 export:()=>ledger.export()
};
root.aurionMentoriaExport=()=>{
 const payload=ledger.export();
 if(typeof native==='function'&&typeof AurionAndroid!=='undefined'&&AurionAndroid.exportBackup){
   native('exportBackup',payload);return;
 }
 const url=URL.createObjectURL(new Blob([payload],{type:'application/json'}));
 const a=document.createElement('a');a.href=url;a.download='AURION_MENTORIA_IA_EVENTOS.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
};
render();
})(typeof window==='undefined'?globalThis:window);
