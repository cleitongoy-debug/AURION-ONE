'use strict';
window.AurionMemoryUI={
 pending:null,
 open(){document.querySelectorAll('.page').forEach(x=>x.classList.remove('active'));document.getElementById('memorylab').classList.add('active');this.render();window.scrollTo(0,0)},
 add(){const t=document.getElementById('amTitle').value.trim(),r=document.getElementById('amRef').value.trim(),b=document.getElementById('amBody').value.trim();if(!b){this.status('Cole o texto ou importe um arquivo. Um link sozinho entra na fila, mas não prova leitura.');if(r){AurionMemoryEngine.addSource('link-pendente',t||'URL para ler','LINK PENDENTE DE LEITURA: '+r,r);this.render()}return}const x=AurionMemoryEngine.addSource('referencia',t||'Fonte',b,r);this.status(x.duplicate?'Fonte já catalogada.':'Fonte adicionada à caixa.');this.render()},
 status(t){const e=document.getElementById('amStatus');if(e)e.textContent=t},
 study(){const s=AurionMemoryEngine.study();this.status('SCAN LOCAL concluído: '+s.learned+' registros indexados, '+s.conflicts+' conflitos. Este passo organiza evidências; não treina pesos do modelo.');this.render()},
 importFiles(input){const files=[...(input.files||[])];if(!files.length)return;let done=0;for(const file of files){if(file.size>3*1024*1024){this.status('Arquivo grande ignorado (limite 3 MB): '+file.name);continue}const reader=new FileReader;reader.onload=()=>{AurionMemoryEngine.addSource('arquivo-local',file.name,String(reader.result||''),'POCO:file:'+file.name);done++;this.status('Arquivos importados na fila: '+done);this.render()};reader.onerror=()=>this.status('Falha ao ler: '+file.name);reader.readAsText(file)}input.value=''},
 studyAI(){
  if(this.pending){this.status('Uma análise de modelo já está em andamento.');return}
  let state=AurionMemoryEngine.state(),arr=(state.memories||[]);if(!arr.length){this.status('Primeiro importe uma fonte e aperte ESTUDAR AGORA.');return}
  const src=arr[arr.length-1];
  if(typeof settings!=='function'||typeof native!=='function'){this.status('Ponte PC/Android não encontrada.');return}
  const cfg=settings();
  if(!cfg.agent){this.status('Configure o Home Node na aba Nós antes de pedir estudo ao modelo.');return}
  this.pending={id:src.id,sourceHash:src.sourceHash,title:src.title};
  this.status('Consultando modelo via Home Node. A resposta será anotação não validada, nunca fato confirmado.');
  const prompt='Você é assistente de estudo do AURION. Responda em português do Brasil. Extraia da FONTE: fatos verificáveis com citações de trechos, dúvidas, conflitos, tarefas e limites. Não invente resultados, testes, horas ou fontes. Classifique como HIPÓTESE tudo não confirmado. TÍTULO: '+src.title+'\nORIGEM: '+src.origin+'\nFONTE: '+src.summary;
  native('sendAgent',cfg.agent,cfg.token||'',prompt);
 },
 receive(raw){
  const pending=this.pending;this.pending=null;
  if(!pending)return;
  try{
   const j=JSON.parse(raw);
   if(!j.ok){this.status('Modelo não respondeu: '+(j.error||j.http||'serviço indisponível'));return}
   let body=j.body||'';let obj={};try{obj=JSON.parse(body)}catch{}
   const answer=obj.response||obj.answer||obj.result||body;
   if(!answer||typeof answer!=='string'){this.status('Resposta vazia do modelo.');return}
   const s=AurionMemoryEngine.state();s.notes=s.notes||[];
   s.notes.push({at:new Date().toISOString(),kind:'analise_modelo',sourceHash:pending.sourceHash,title:pending.title,validated:false,text:answer.slice(0,10000)});
   localStorage.setItem('aurionMemoryEngineV1',JSON.stringify(s));
   this.status('Modelo respondeu. Anotação registrada como NÃO VALIDADA; confira origem e provas.');
   this.render();
  }catch(e){this.status('Erro ao tratar resposta do modelo: '+e.message)}
 },
 render(){const s=AurionMemoryEngine.state();document.getElementById('amMemories').textContent=(s.memories||[]).slice(-80).map(x=>x.type+' · '+x.title+'\n'+x.summary+'\nOrigem: '+x.origin).join('\n\n')||'Nenhuma memória consolidada.';document.getElementById('amNotes').textContent=(s.notes||[]).slice(-30).map(x=>x.at+' · '+x.text).join('\n\n')||'Sem ciclos de estudo.'},
 export(){const blob=new Blob([AurionMemoryEngine.export()],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='AURION_MENTE_BACKUP.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),2000)}
};
