'use strict';
// AURION ONE - memoria local offline. Nenhum acesso ao Drive/API ocorre aqui.
// FNV-1a e usado APENAS para deduplicacao local, NAO e SHA-256/prova de integridade.
const AURION_MEMORY_KEY='aurionMemoryEngineV1';
const AM_ALLOWED_DESTINATIONS=['DESCOBERTAS#TEMPO#REAL','ATUALIZACOES#DIA','ATUALIZACOES#MES'];
const AM_EVIDENCE=['CODIGO_LIDO','TESTE_SINTETICO','TESTE_FISICO','RELATO_HISTORICO','NAO_TESTADO','BLOQUEADO'];
function amState(){
  try{
    const value=JSON.parse(localStorage.getItem(AURION_MEMORY_KEY)||'{}');
    return value&&typeof value==='object'&&!Array.isArray(value)?value:{};
  }catch{return{}}
}
function amSave(state){localStorage.setItem(AURION_MEMORY_KEY,JSON.stringify(state));}
function amHash(value){
  let h=2166136261;
  for(let i=0;i<value.length;i++){h^=value.charCodeAt(i);h=Math.imul(h,16777619)}
  return (h>>>0).toString(16).padStart(8,'0');
}
function amSensitive(text){
  return /(?:sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9_]{12,}|github_pat_[A-Za-z0-9_]{12,}|AIza[A-Za-z0-9_-]{20,}|\b(?:password|senha|token|api[_ -]?key|chave[_ -]?api|authorization|cookie)\s*[:=]\s*\S+)/i.test(String(text||''));
}
function amArray(s,key){if(!Array.isArray(s[key]))s[key]=[];return s[key];}
function amAddSource(kind,title,body,ref,evidence){
  kind=String(kind||'referencia').trim().slice(0,80);
  title=String(title||'').trim().slice(0,250);
  body=String(body||'');
  ref=String(ref||'').trim().slice(0,1000);
  evidence=AM_EVIDENCE.includes(evidence)?evidence:'RELATO_HISTORICO';
  if(!title||!body.trim()||body.length>20000||amSensitive([title,body,ref].join('\n')))
    return {ok:false,error:'fonte_vazia_longa_ou_credencial'};
  const s=amState(),sources=amArray(s,'sources');
  amArray(s,'memories');amArray(s,'notes');amArray(s,'syncOutbox');
  const raw=[kind,title,body,ref].join('|'),hash=amHash(raw);
  if(sources.some(x=>x.hash===hash&&[x.kind,x.title,x.body,x.ref].join('|')===raw))
    return {ok:true,duplicate:true};
  const id='src_'+Date.now()+'_'+amHash(raw+String(sources.length));
  sources.push({id,kind,title,body,ref,hash,addedAt:new Date().toISOString(),status:'new',evidence});
  try{amSave(s)}catch{return{ok:false,error:'armazenamento_local_indisponivel'}}
  return {ok:true,duplicate:false,id};
}
function amStudy(){
  const s=amState(),sources=amArray(s,'sources'),memories=amArray(s,'memories'),notes=amArray(s,'notes');
  let indexed=0,conflicts=0;
  const now=new Date().toISOString();
  for(const source of sources.filter(x=>x.status!=='studied'&&x.status!=='indexed')){
    const text=String(source.body||'').trim();
    if(!text){source.status='empty';continue}
    if(memories.some(x=>x.sourceHash===source.hash&&x.sourceId===source.id)){source.status='indexed';continue}
    const type=/erro|falha|crash|exception/i.test(text)?'erro':/decis|confirm|valid/i.test(text)?'decisao':/codigo|script|gradle|apk|java|python|json/i.test(text)?'codigo':'conhecimento';
    const entry={id:'mem_'+Date.now()+'_'+indexed,type,title:source.title||source.kind,summary:text.slice(0,1200),
      origin:source.ref||source.kind,sourceId:source.id,sourceHash:source.hash,
      indexedAt:now,evidence:AM_EVIDENCE.includes(source.evidence)?source.evidence:'RELATO_HISTORICO'};
    const conflict=memories.find(x=>x.title===entry.title&&x.summary!==entry.summary);
    if(conflict){entry.conflictWith=conflict.id;conflicts++}
    memories.push(entry);source.status='indexed';indexed++;
  }
  s.lastScan={at:now,indexed,learned:indexed,conflicts,totalSources:sources.length,totalMemories:memories.length,meaning:'registros_indexados_nao_horas_de_estudo'};
  notes.push({at:now,text:'SCAN DOCUMENTAL: '+indexed+' fontes indexadas; '+conflicts+' conflitos. Nao prova estudo.'});
  try{amSave(s)}catch{return{ok:false,error:'armazenamento_local_indisponivel',indexed:0,learned:0,conflicts}}
  return Object.assign({ok:true},s.lastScan);
}
function amTerms(value){
  const stop=new Set(['para','como','mais','sobre','quais','onde','essa','isso','este','esta','aquilo','voce','você','com','sem','das','dos']);
  return [...new Set(String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase()
    .match(/[a-z0-9#_.-]{3,}/g)||[])].filter(t=>!stop.has(t));
}
function amContext(question){
  const terms=amTerms(question);
  if(!terms.length)return '';
  const s=amState();
  return (Array.isArray(s.memories)?s.memories:[])
    .map(m=>{
      const haystack=(String(m.title||'')+' '+String(m.summary||'')).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
      return {m,score:terms.reduce((n,t)=>n+(haystack.includes(t)?1:0),0)};
    }).filter(x=>x.score>0)
    .sort((a,b)=>b.score-a.score).slice(0,8)
    .map(x=>'['+(x.m.evidence||'RELATO_HISTORICO')+'; '+(x.m.type||'referencia')+'] '+(x.m.title||'')+': '+(x.m.summary||'')+' (fonte: '+(x.m.origin||'nao_informada')+')').join('\n');
}
// Outbox apenas local: evento pendente NUNCA equivale a autenticar conta nem sincronizar.
function amQueueSync(sourceId,destination){
  const s=amState(),source=(Array.isArray(s.sources)?s.sources:[]).find(x=>x.id===sourceId);
  if(!source||!AM_ALLOWED_DESTINATIONS.includes(destination))
    return {ok:false,error:'fonte_ou_destino_nao_autorizado'};
  const q=amArray(s,'syncOutbox');
  const previous=q.find(x=>x.sourceId===sourceId&&x.destination===destination);
  if(previous)return {ok:true,duplicate:true,status:previous.status,id:previous.id};
  const id='out_'+Date.now()+'_'+amHash(sourceId+destination);
  q.push({id,sourceId,sourceHash:source.hash,destination,queuedAt:new Date().toISOString(),status:'PENDENTE'});
  try{amSave(s)}catch{return{ok:false,error:'armazenamento_local_indisponivel'}}
  return {ok:true,status:'PENDENTE',id};
}
// Somente um adaptador OAuth externo, apos confirmar o Drive e reler o recibo, deve chamar ack.
function amAcknowledgeSync(id,receipt){
  if(!receipt||receipt.verifiedBy!=='drive_readback'||typeof receipt.fileId!=='string'||!receipt.fileId.trim()
     ||typeof receipt.verifiedAt!=='string'||!receipt.verifiedAt.trim())
    return {ok:false,error:'recibo_de_leitura_do_drive_obrigatorio'};
  const s=amState(),q=amArray(s,'syncOutbox'),entry=q.find(x=>x.id===id);
  if(!entry)return {ok:false,error:'evento_nao_encontrado'};
  if(entry.status==='CONFIRMADO')return {ok:true,duplicate:true};
  entry.status='CONFIRMADO';
  entry.receipt={fileId:receipt.fileId,verifiedAt:receipt.verifiedAt,verifiedBy:'drive_readback'};
  try{amSave(s)}catch{return{ok:false,error:'armazenamento_local_indisponivel'}}
  return {ok:true,status:'CONFIRMADO'};
}
function amSyncStatus(){
  const q=amState().syncOutbox||[];
  return {connected:false,meaning:'sem_teste_oauth_ou_rede',pending:q.filter(x=>x.status==='PENDENTE').length,
    confirmed:q.filter(x=>x.status==='CONFIRMADO').length};
}
function amIntegrity(){
  const s=amState(),sources=Array.isArray(s.sources)?s.sources:[],memories=Array.isArray(s.memories)?s.memories:[];
  const ids=new Set(sources.map(x=>x.id)),missing=memories.filter(x=>x.sourceId&&!ids.has(x.sourceId)).length;
  return {sourceCount:sources.length,memoryCount:memories.length,orphanedMemoryCount:missing,
    conflicts:memories.filter(x=>x.conflictWith).length,sync:amSyncStatus(),
    measuredAt:new Date().toISOString(),census:'memoria_local_deste_dispositivo_apenas'};
}
function amExport(){
  // Acao explicita do operador; nunca envia automaticamente; elimina chaves acidentalmente presentes.
  const s=JSON.parse(JSON.stringify(amState()));
  for(const field of ['sources','memories','notes']){
    if(Array.isArray(s[field]))s[field]=s[field].map(x=>{
      const copy=Object.assign({},x);
      for(const k of ['body','summary','text','ref','origin'])if(amSensitive(copy[k]))copy[k]='[CREDENCIAL_OMITIDA]';
      return copy;
    });
  }
  return JSON.stringify(s,null,2);
}
if(typeof window!=='undefined')window.AurionMemoryEngine={
  state:amState,addSource:amAddSource,study:amStudy,context:amContext,export:amExport,
  queueSync:amQueueSync,acknowledgeSync:amAcknowledgeSync,syncStatus:amSyncStatus,integrity:amIntegrity
};
