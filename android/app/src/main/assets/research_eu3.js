/* Original research workflow inspired by EU3; no game assets. */
(function(root){'use strict';
const KEY='aurion_eu3_research_v1';
function engine(storage){
 let state;try{state=JSON.parse(storage.getItem(KEY));}catch(e){}
 if(!state||state.version!==1||!Array.isArray(state.items))state={version:1,items:[]};
 let active=null,last=0;
 const save=()=>storage.setItem(KEY,JSON.stringify(state));
 const get=id=>state.items.find(x=>x.id===id);
 const ready=(x,seen=new Set())=>!!x&&!seen.has(x.id)&&x.dependencies.every(id=>{const dep=get(id);return dep&&dep.status==='VALIDADO'&&ready(dep,new Set([...seen,x.id]));});
 // A failed prerequisite invalidates its entire dependent tree without discarding earlier receipts.
 function markDescendantsForReview(originId){
   const affected=new Set([originId]);let changed=true;
   while(changed){
     changed=false;
     for(const item of state.items){
       if(affected.has(item.id)||!item.dependencies.some(id=>affected.has(id)))continue;
       affected.add(item.id);changed=true;
       if(item.status==='VALIDADO'||item.status==='EM_ESTUDO'){
         item.status='REVISAO_PENDENTE';
         item.review_reason='PRE_REQUISITO_REPROVADO';
       }
       if(active===item.id)active=null;
     }
   }
 }
 // Repair persisted records created before dependency invalidation existed.
 function reconcilePersistedValidation(){
   let changed=false;
   for(const item of state.items){
     if(item.status==='VALIDADO'&&!ready(item)){
       item.status='REVISAO_PENDENTE';
       item.review_reason='PRE_REQUISITO_INCONSISTENTE';
       changed=true;
     }
   }
   if(changed)save();
 }
 function add(title,source,dependencies=[]){if(!title.trim()||!source.trim())throw Error('Informe título e fonte.');if(dependencies.some(id=>!get(id)))throw Error('Pré-requisito desconhecido.');const x={id:Date.now().toString(36)+'-'+Math.random().toString(36).slice(2,8),title:title.slice(0,200),source:source.slice(0,2000),dependencies:[...new Set(dependencies)],status:'CANDIDATO',milliseconds:0,receipts:[]};state.items.push(x);save();return x;}
 function tick(now,visible=true){if(active&&visible){const delta=now-last;if(delta>0&&delta<=5000)get(active).milliseconds+=delta;}last=now;save();}
 function pause(now){tick(now);active=null;save();}
 function start(id,now){const x=get(id);if(!x||!ready(x)||x.status==='VALIDADO')throw Error('Pesquisa bloqueada pelos pré-requisitos ou já validada.');pause(now);active=id;last=now;x.status='EM_ESTUDO';save();}
 function proof(id,range,result,passed){const x=get(id);if(!x||!ready(x)||!range.trim()||!result.trim())throw Error('Informe trecho lido e resultado reproduzível; confira pré-requisitos.');if(active===id)active=null;x.receipts.push({at:new Date().toISOString(),range:range.slice(0,500),result:result.slice(0,4000),passed:!!passed});x.status=passed?'VALIDADO':'EXPERIMENTAL';if(passed)delete x.review_reason;else markDescendantsForReview(id);save();}

 // Offline JSON import. Strict validation prevents truncated/corrupt files from changing the local queue.
 const MAX_JSON_CHARS=2000000,BACKUP_KEY=KEY+'_pre_restore_v1';
 function asObject(v,label){if(!v||typeof v!=='object'||Array.isArray(v))throw Error(label+' inválido.');return v;}
 function allowedKeys(v,keys,label){for(const key of Object.keys(v))if(!keys.includes(key))throw Error(label+': campo desconhecido '+key+'.');}
 function normalizeItem(raw){
   const v=asObject(raw,'Pesquisa');
   allowedKeys(v,['id','title','source','dependencies','status','milliseconds','receipts','review_reason'],'Pesquisa');
   if(typeof v.id!=='string'||!v.id||v.id.length>128)throw Error('ID de pesquisa inválido.');
   if(typeof v.title!=='string'||!v.title.trim()||v.title.length>200)throw Error('Título de pesquisa inválido.');
   if(typeof v.source!=='string'||!v.source.trim()||v.source.length>2000)throw Error('Fonte de pesquisa inválida.');
   if(!Array.isArray(v.dependencies)||v.dependencies.length>50||
       v.dependencies.some(id=>typeof id!=='string'||!id||id.length>128))throw Error('Dependências inválidas.');
   if(new Set(v.dependencies).size!==v.dependencies.length||v.dependencies.includes(v.id))throw Error('Dependência duplicada ou circular.');
   if(!['CANDIDATO','EM_ESTUDO','EXPERIMENTAL','VALIDADO','REVISAO_PENDENTE'].includes(v.status))throw Error('Status de pesquisa desconhecido.');
   if(typeof v.milliseconds!=='number'||!Number.isFinite(v.milliseconds)||v.milliseconds<0||v.milliseconds>1e12)throw Error('Cronômetro inválido.');
   if(!Array.isArray(v.receipts)||v.receipts.length>200)throw Error('Quantidade de provas inválida.');
   const receipts=v.receipts.map(rawReceipt=>{
     const p=asObject(rawReceipt,'Comprovante');
     allowedKeys(p,['at','range','result','passed'],'Comprovante');
     if(typeof p.at!=='string'||p.at.length>64||!Number.isFinite(Date.parse(p.at)))throw Error('Data de prova inválida.');
     if(typeof p.range!=='string'||!p.range.trim()||p.range.length>500)throw Error('Trecho de prova inválido.');
     if(typeof p.result!=='string'||!p.result.trim()||p.result.length>4000)throw Error('Resultado de prova inválido.');
     if(typeof p.passed!=='boolean')throw Error('Validação da prova inválida.');
     return {at:p.at,range:p.range,result:p.result,passed:p.passed};
   });
   const x={id:v.id,title:v.title,source:v.source,dependencies:[...v.dependencies],status:v.status,milliseconds:v.milliseconds,receipts};
   if(v.review_reason!==undefined){
     if(typeof v.review_reason!=='string'||v.review_reason.length>100)throw Error('Motivo de revisão inválido.');
     x.review_reason=v.review_reason;
   }
   return x;
 }
 function planRestore(text){
   if(typeof text!=='string'||text.length>MAX_JSON_CHARS)throw Error('JSON ausente ou maior que 2 milhões de caracteres.');
   let raw;try{raw=JSON.parse(text);}catch(e){throw Error('JSON inválido ou incompleto.');}
   asObject(raw,'Backup');allowedKeys(raw,['version','items'],'Backup');
   if(raw.version!==1||!Array.isArray(raw.items)||raw.items.length>2000)throw Error('Versão ou quantidade de pesquisas incompatível.');
   const received=raw.items.map(normalizeItem);
   const incomingIds=new Set();
   for(const x of received){if(incomingIds.has(x.id))throw Error('IDs repetidos dentro do backup.');incomingIds.add(x.id);}
   const merged=state.items.map(normalizeItem);
   const byId=new Map(merged.map(x=>[x.id,x]));
   let added=0,unchanged=0;
   for(const x of received){
     if(byId.has(x.id)){
       if(JSON.stringify(byId.get(x.id))!==JSON.stringify(x))throw Error('Conflito de ID: '+x.id+'. Exportações diferentes exigem reconciliação manual.');
       unchanged++;continue;
     }
     merged.push(x);byId.set(x.id,x);added++;
   }
   if(merged.length>2500)throw Error('Limite seguro da biblioteca excedido.');
   const visiting=new Set(),visited=new Set();
   function visit(id){
     if(visiting.has(id))throw Error('Ciclo de pré-requisitos detectado.');
     if(visited.has(id))return;
     const x=byId.get(id);if(!x)throw Error('Pré-requisito ausente: '+id+'.');
     visiting.add(id);for(const dep of x.dependencies)visit(dep);visiting.delete(id);visited.add(id);
   }
   for(const x of merged)visit(x.id);
   function depsValidated(x,seen=new Set()){
     if(seen.has(x.id))return false;
     const next=new Set([...seen,x.id]);
     return x.dependencies.every(id=>{const d=byId.get(id);return d.status==='VALIDADO'&&depsValidated(d,next);});
   }
   let review=0;
   for(const x of merged)if(x.status==='VALIDADO'&&!depsValidated(x)){
     x.status='REVISAO_PENDENTE';x.review_reason='PRE_REQUISITO_INCONSISTENTE';review++;
   }
   const proposed={version:1,items:merged};
   const encoded=JSON.stringify(proposed);
   if(encoded.length>MAX_JSON_CHARS)throw Error('Biblioteca resultante ultrapassa limite seguro.');
   return {added,unchanged,review,total:merged.length,encoded,proposed};
 }
 function previewRestore(text){
   const p=planRestore(text);return {added:p.added,unchanged:p.unchanged,review:p.review,total:p.total};
 }
 function restore(text){
   const p=planRestore(text);
   if(p.encoded===JSON.stringify(state))return {added:0,unchanged:p.unchanged,review:0,total:p.total};
   // Preserve the original local content before making any change. Storage failures abort the import.
   if(storage.getItem(BACKUP_KEY)==null)storage.setItem(BACKUP_KEY,JSON.stringify(state));
   storage.setItem(KEY,p.encoded);
   state=p.proposed;active=null;last=0;
   return {added:p.added,unchanged:p.unchanged,review:p.review,total:p.total};
 }

 reconcilePersistedValidation();
 return {add,start,pause,tick,proof,ready,previewRestore,restore,items:()=>JSON.parse(JSON.stringify(state.items)),export:()=>JSON.stringify(state,null,2),active:()=>active};
}
root.AurionResearchEngine=engine;
if(typeof document==='undefined')return;
const e=engine(localStorage),host=document.querySelector('#lab');if(!host)return;
const panel=document.createElement('div');panel.className='card';panel.innerHTML='<h2>🧪 Pesquisa · método EU3</h2><p>Fonte → estudo → experimento → prova → desbloqueio. Tempo registrado nesta sessão, sem transformar resposta de IA em validação. Os registros sobrevivem ao fechamento; exporte para backup.</p><label>Título</label><input id="euTitle"><label>Fonte: ID, caminho, linhas ou print</label><input id="euSource"><label>Pré-requisito validado</label><select id="euDependency"><option value="">Nenhum</option></select><button id="euAdd">ENFILEIRAR PESQUISA</button><div id="euItems"></div><label>Trecho efetivamente lido</label><input id="euRange" placeholder="Arquivo e linhas / página / região do print"><label>Resultado e procedimento reproduzível</label><textarea id="euResult"></textarea><label><input type="checkbox" id="euPassed"> Conferi a prova e o critério foi atendido</label><button id="euProof">REGISTRAR PROVA DA PESQUISA SELECIONADA</button><button id="euPause">PAUSAR</button><button id="euExport">EXPORTAR JSON</button><p><strong>Importação manual:</strong> selecione uma exportação EU3 deste perfil ou de outro dispositivo. Conflitos de ID interrompem a operação sem sobrescrever provas.</p><input id="euImportFile" type="file" accept=".json,application/json"><p id="euImportPreview" aria-live="polite">Nenhum backup escolhido.</p><label><input type="checkbox" id="euImportApprove"> Conferi a origem e autorizo mesclar os registros sem sobrescrever os existentes.</label><button id="euImportApply" disabled>CONFIRMAR IMPORTAÇÃO</button><p id="euStatus" aria-live="polite"></p><p>Acervo localizado: <a href="https://docs.google.com/document/d/1Zh2uT-__vlHAXkz36Ia-_-jXkoRUYcZUsJcF6oc2DSc" target="_blank" rel="noopener">Laboratório de fusão</a> · <a href="https://docs.google.com/document/d/1-oLBlBtPzsvCExOuLvKDZDkW6pnStOAxU2C44ruWcyM" target="_blank" rel="noopener">Índice dos estudos</a> · <a href="https://drive.google.com/drive/folders/1480epyBbO9QGf7y1Nk9Vy1nWIQaPbZy3" target="_blank" rel="noopener">Biblioteca de conhecimento</a>. Acesso ao Drive exige conexão; cadastrar uma fonte não significa lê-la.</p>';host.prepend(panel);
const q=id=>document.getElementById(id);let selected=null;
function label(x){return (selected===x.id?'▶ ':'')+x.title+' · '+x.status+' · '+Math.floor(x.milliseconds/1000)+'s'+(e.ready(x)?'':' · BLOQUEADA');}
function render(){const dependency=q('euDependency').value;q('euItems').replaceChildren();q('euDependency').innerHTML='<option value="">Nenhum</option>';for(const x of e.items()){const b=document.createElement('button');b.dataset.researchId=x.id;b.textContent=label(x);b.onclick=()=>{selected=x.id;q('euStatus').textContent='Selecionada: '+x.title;if(x.status!=='VALIDADO')act(()=>e.start(x.id,performance.now()));};q('euItems').append(b);if(x.status==='VALIDADO'){const o=document.createElement('option');o.value=x.id;o.textContent=x.title;q('euDependency').append(o);}}q('euDependency').value=dependency;}
function act(fn){try{fn();q('euStatus').textContent='Registro salvo localmente.';render();}catch(err){q('euStatus').textContent=err.message;}}
q('euAdd').onclick=()=>act(()=>e.add(q('euTitle').value,q('euSource').value,q('euDependency').value?[q('euDependency').value]:[]));
q('euPause').onclick=()=>act(()=>e.pause(performance.now()));q('euProof').onclick=()=>act(()=>e.proof(selected,q('euRange').value,q('euResult').value,q('euPassed').checked));
q('euExport').onclick=()=>{e.pause(performance.now());if(typeof native==='function'&&typeof AurionAndroid!=='undefined'&&AurionAndroid.exportBackup){native('exportBackup',e.export());return;}const blob=new Blob([e.export()],{type:'application/json'}),url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download='AURION_PESQUISAS_EU3.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};

let pendingBackup=null;
q('euImportFile').onchange=()=>{
 pendingBackup=null;q('euImportApply').disabled=true;q('euImportApprove').checked=false;
 const file=q('euImportFile').files[0];if(!file)return;
 if(file.size>2000000){q('euImportPreview').textContent='Arquivo grande demais. Nada alterado.';return;}
 const reader=new FileReader();
 reader.onload=()=>{
   try{
     const raw=String(reader.result),preview=e.previewRestore(raw);
     pendingBackup=raw;
     q('euImportPreview').textContent='Prévia: '+preview.added+' novos, '+preview.unchanged+' iguais, '+preview.review+' para revisão; total '+preview.total+'. Nenhum dado alterado.';
     q('euImportApply').disabled=false;
   }catch(err){q('euImportPreview').textContent=err.message;}
 };
 reader.onerror=()=>{q('euImportPreview').textContent='Falha na leitura. Nada alterado.';};
 reader.readAsText(file,'UTF-8');
};
q('euImportApply').onclick=()=>{
 if(!pendingBackup||!q('euImportApprove').checked){
   q('euImportPreview').textContent='Confirme a origem antes de importar.';return;
 }
 try{
   e.pause(performance.now());
   const summary=e.restore(pendingBackup);
   pendingBackup=null;q('euImportApprove').checked=false;q('euImportApply').disabled=true;
   q('euImportPreview').textContent='Importação local: '+summary.added+' novos, '+summary.unchanged+' iguais, '+summary.review+' em revisão. Backup anterior preservado localmente.';
   selected=null;render();
 }catch(err){q('euImportPreview').textContent='Importação cancelada: '+err.message;}
};
document.addEventListener('visibilitychange',()=>{if(document.hidden)e.pause(performance.now());});window.addEventListener('pagehide',()=>e.pause(performance.now()));setInterval(()=>{if(!document.hidden&&host.classList.contains('active')){e.tick(performance.now());const items=e.items();q('euItems').querySelectorAll('button').forEach(b=>{const x=items.find(v=>v.id===b.dataset.researchId);if(x)b.textContent=label(x);});}else if(e.active())e.pause(performance.now());},1000);render();
})(typeof window==='undefined'?globalThis:window);
