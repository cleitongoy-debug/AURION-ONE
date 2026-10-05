'use strict';
const AURION_MEMORY_KEY='aurionMemoryEngineV1';
function amState(){try{return JSON.parse(localStorage.getItem(AURION_MEMORY_KEY)||'{}')}catch{return{}}}
function amSave(s){localStorage.setItem(AURION_MEMORY_KEY,JSON.stringify(s))}
function amHash(s){let h=2166136261;for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619)}return (h>>>0).toString(16).padStart(8,'0')}
function amAddSource(kind,title,body,ref){
  let s=amState();s.sources=s.sources||[];s.memories=s.memories||[];s.notes=s.notes||[];
  const raw=[kind,title,body,ref].join('|'), hash=amHash(raw);
  if(s.sources.some(x=>x.hash===hash)) return {ok:true,duplicate:true};
  s.sources.push({id:'src_'+Date.now(),kind,title,body,ref,hash,addedAt:new Date().toISOString(),status:'new'});
  amSave(s);return {ok:true,duplicate:false};
}
function amStudy(){
  let s=amState();s.sources=s.sources||[];s.memories=s.memories||[];s.notes=s.notes||[];let learned=0,conflicts=0;
  for(const src of s.sources.filter(x=>x.status!=='studied')){
    const text=(src.body||'').trim();
    if(!text){src.status='empty';continue}
    const type=/erro|falha|crash|exception/i.test(text)?'erro':/decis|confirm|valid/i.test(text)?'decisao':/codigo|script|gradle|apk|java|python|json/i.test(text)?'codigo':'conhecimento';
    const mem={id:'mem_'+Date.now()+'_'+learned,type,title:src.title||src.kind,summary:text.slice(0,1200),origin:src.ref||src.kind,sourceHash:src.hash,learnedAt:new Date().toISOString(),confidence:src.ref?0.85:0.6};
    if(s.memories.some(x=>x.sourceHash===src.hash)){src.status='studied';continue}
    const sameTitle=s.memories.find(x=>x.title===mem.title&&x.summary!==mem.summary);
    if(sameTitle){conflicts++;mem.conflictWith=sameTitle.id}
    s.memories.push(mem);src.status='studied';learned++;
  }
  s.lastScan={at:new Date().toISOString(),learned,conflicts,totalSources:s.sources.length,totalMemories:s.memories.length};
  s.notes.push({at:new Date().toISOString(),text:'SCAN MEMÓRIA: '+learned+' novas memórias; '+conflicts+' conflitos.'});
  amSave(s);return s.lastScan;
}
function amContext(q){
  const s=amState(), terms=String(q||'').toLowerCase().split(/\s+/).filter(Boolean);
  return (s.memories||[]).map(m=>({m,score:terms.reduce((n,t)=>n+((m.title+' '+m.summary).toLowerCase().includes(t)?1:0),0)}))
   .sort((a,b)=>b.score-a.score).slice(0,8).map(x=>'['+x.m.type+'] '+x.m.title+': '+x.m.summary).join('\n');
}
function amExport(){return JSON.stringify(amState(),null,2)}
window.AurionMemoryEngine={state:amState,addSource:amAddSource,study:amStudy,context:amContext,export:amExport};
