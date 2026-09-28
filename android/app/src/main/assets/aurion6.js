'use strict';
// Curated, non-secret factory context. The original archive contains credentials and is never bundled.
const AURION_MILESTONES=[
  ['2025-10-16','Boot LÚMEN V4.0','Início documentado do núcleo LÚMEN e seus operadores.'],
  ['2025-11-02','TOMIM','Projeto infantil: consistência dos personagens, estilo cartoon Kiwi 2D e imagens 752×416.'],
  ['2026-09-18','AURION ONE no POCO','Começo da ponte móvel: painel, agente, PC opcional, Mi Band 9 Pro e fone.'],
  ['2026-09-21','T8i e estúdio','CR3/RAW, preservação de originais, revelação, vídeo, cor e entrega viram módulos prioritários.'],
  ['2026-09-24','Programação controlada','Preservar dados, testar funções e registrar o que foi comprovado.'],
  ['2026-09-25','APK e scan','O Git registra versões Android e um snapshot de serviços locais; snapshot não é status atual.'],
  ['2026-09-27','Painel e pesquisa','Operador pediu scanner de aquecimento, estudo fotográfico e independência offline.'],
  ['2026-09-28','POCO autônomo','História selecionada embutida, cronômetro e orientador local nesta versão.']
];
const AURION_KNOWLEDGE=[
  {terms:['t8i','cr3','raw','canon','lente','foto'],answer:'A T8i pede cópia do CR3 original, organização por projeto e revelação não destrutiva. Este POCO cataloga e edita imagens que o Android decodifica; CR3 completo depende de um motor RAW verificado. As abas Foto, Cor e Entrega ajudam no fluxo. Não chamo um preset salvo de revelação aplicada.'},
  {terms:['pc','gpu','comfy','ollama','nó'],answer:'O app abre e mantém memórias sem PC. Em Configuração → Nós, informe uma URL privada do PC e teste cada endpoint. ComfyUI online em /system_stats ainda não significa geração; é preciso validar workflow, fila e saída.'},
  {terms:['band','relógio','mi fitness','pulseira'],answer:'A Mi Band 9 Pro é tratada separadamente do fone. A aba Band busca Bluetooth e faz teste de notificação com permissões do Android. Mi Fitness instalado não prova leitura de dados nem sincronização.'},
  {terms:['fone','capacete','bluetooth','voz'],answer:'Pareie o fone nas configurações Bluetooth do POCO. O aplicativo não assume controle de botões ou microfone sem teste no dispositivo. Use o chat e a entrada de voz quando estiver parado.'},
  {terms:['api','conta','drive','github','chave','conexão'],answer:'Abra Configuração. Insira chaves na aba Contas, configure PC em Nós e teste. Vermelho significa pendente ou falhou; verde exige resposta recente. O Drive pode ser usado com seletor de arquivos do Android. ChatGPT Plus e Gemini app não fornecem automaticamente crédito de API.'},
  {terms:['memória','contexto','história','dedicação','tempo'],answer:'A linha do tempo traz marcos resumidos do AURION, sem segredos. Memórias novas ficam no banco local e podem ser exportadas. O cronômetro conta sessões iniciadas neste aparelho; as 315,7 horas/6.882 ciclos são uma referência histórica arquivada.'},
  {terms:['imagem','vídeo','editor','cor','entrega','impressão'],answer:'Foto, Cor, FX, Vídeo, Áudio, Conversor e Cliente já estão no menu. Exporte e confira arquivo, dimensão, cor e destino antes de entregar. Algumas opções são prévia ou projeto; a tela de cada módulo indica o limite.'},
  {terms:['agente','inteligente','offline','orientador'],answer:'Eu sou o orientador local embutido: recupero regras e marcos conhecidos e guio você pelas abas sem internet. Para gerar uma resposta nova por modelo, configure uma API na aba Contas ou o Home Node em Nós e use Agente.'}
];
const WORK_KEY='aurion6Work';
function workState(){try{return JSON.parse(localStorage.getItem(WORK_KEY)||'{}')}catch{return{}}}
function saveWork(w){localStorage.setItem(WORK_KEY,JSON.stringify(w));renderWork()}
function fmtDuration(ms){let s=Math.floor(Math.max(0,ms)/1000),h=Math.floor(s/3600);return String(h).padStart(2,'0')+':'+String(Math.floor(s%3600/60)).padStart(2,'0')+':'+String(s%60).padStart(2,'0')}
function workElapsed(w){return (w.total||0)+(w.start?Math.max(0,Date.now()-w.start):0)}
function toggleWork(){let w=workState();if(w.start){w.total=workElapsed(w);w.start=null}else w.start=Date.now();saveWork(w)}
function markMoment(){let title=prompt('Nome do marco desta sessão:');if(!title||!title.trim())return;let w=workState();w.marks=w.marks||[];w.marks.unshift({title:title.trim().slice(0,120),at:Date.now(),elapsed:workElapsed(w)});w.marks=w.marks.slice(0,200);saveWork(w)}
function renderWork(){let w=workState();$('workTimer').textContent=fmtDuration(workElapsed(w));$('workToggle').textContent=w.start?'PAUSAR E SALVAR':'INICIAR CRONÔMETRO';$('workTotal').textContent='Tempo medido no POCO: '+fmtDuration(workElapsed(w));$('workMarks').innerHTML=(w.marks||[]).map(m=>`<div class="milestone"><small>${new Date(m.at).toLocaleString('pt-BR')} · ${fmtDuration(m.elapsed)}</small><b>${esc(m.title)}</b></div>`).join('')||'<p class="muted">Seus marcadores aparecerão aqui.</p>'}
function renderHistory(){let now=Date.now();$('sinceBoot').textContent=Math.floor((now-new Date('2025-10-16T14:40:00-03:00'))/86400000)+' dias';$('sinceOne').textContent=Math.floor((now-new Date('2026-09-18T00:00:00-03:00'))/86400000)+' dias';$('historyMilestones').innerHTML=AURION_MILESTONES.map(m=>`<div class="milestone"><small>${m[0]}</small><b>${esc(m[1])}</b><span>${esc(m[2])}</span></div>`).join('');renderWork()}
function seedFactoryContext(){if(localStorage.getItem('aurion6Seeded'))return;const facts=[
 ['Operador e diretriz','ANARK / Cleiton Luiz Epifanio. AURION ONE é um projeto de IA local, criativa e móvel. Preservar o trabalho, conferir evidências e manter o POCO útil sem rede.'],
 ['Arquitetura de contexto','Pai → Programa → Agente → Memória → Contexto. Distinguir declarado, implementado e testado; registrar origem, hora e resultado.'],
 ['POCO e dispositivos','POCO X7, Mi Band 9 Pro via Mi Fitness e fone/capacete são integrações separadas. Não afirmar conexão apenas por aplicativo instalado.'],
 ['Fotografia e T8i','CR3 original preservado; workspace de RAW, prévias, exportações, presets e logs. Profundidade de cor, lentes, perfis e acabamento para impressão/redes são objetivos de estudo.'],
 ['Painel PC','Há versões históricas do HUD Python e Home Node. Portas locais e scans antigos são snapshots; testar serviço e autenticação antes de marcar online.'],
 ['Identidade e projetos','Visual escuro, cinza militar e ouro. TOMIM é projeto infantil com personagens consistentes; não é operador.'],
 ['Segredos e provedores','Chaves devem ser inseridas no próprio aparelho. Não embutir credenciais de conversas. Provedores via API oficial quando configurados.']
];let ok=true;for(const [title,body] of facts){let id=native('memoryAdd','factory',title,body,JSON.stringify({source:'curadoria AURION v6; histórico do operador',version:6}));if(!(id>0))ok=false}if(ok)localStorage.setItem('aurion6Seeded','1')}
function toggleGuide(){let p=$('guidePanel');p.hidden=!p.hidden;if(!p.hidden)$('guideQuestion').focus()}
function askGuide(){let q=$('guideQuestion').value.trim();if(!q)return;let words=q.toLocaleLowerCase('pt-BR');let hits=AURION_KNOWLEDGE.map(k=>({k,score:k.terms.reduce((n,t)=>n+(words.includes(t)?1:0),0)})).sort((a,b)=>b.score-a.score);let answer=hits[0].score?hits[0].k.answer:'Posso orientar sobre T8i, edição, contexto, conexões, PC, Band e fone com o conhecimento local. Para uma análise nova, use a aba Agente após testar uma rota de IA.';$('guideReply').textContent=answer;$('guideQuestion').value='';native('memoryAdd','conversation','Orientador local · pergunta',q,'{}');native('memoryAdd','conversation','Orientador local · resposta',answer,'{}')}
function recentOk(label){let t=data().tests?.[label];return !!(t?.ok && t.checkedAt && Date.now()-t.checkedAt<300000)}
function renderSetup(){let d=data(),a={};try{a=JSON.parse(native('accountStatus')||'{}')}catch{};let verified=workState().accounts||{};let fresh=k=>!!(verified[k]&&Date.now()-verified[k]<300000);let status=[['GitHub API',fresh('github'),!!a.github],['Drive API',fresh('googleDrive'),!!a.googleDrive],['OpenAI API',fresh('openai'),!!a.openai],['Groq API',fresh('groq'),!!a.groq],['NVIDIA API',fresh('nvidia'),!!a.nvidia],['Gemini API',fresh('gemini'),!!a.gemini],['Hugging Face',fresh('huggingface'),!!a.huggingface],['PC / Home Node',recentOk('Home Node'),!!d.settings?.agent],['ComfyUI',recentOk('ComfyUI'),!!d.settings?.comfy],['Ollama',recentOk('Ollama'),!!d.settings?.ollama]];$('setupStates').innerHTML=status.map(([name,ok,configured])=>`<div class="connectionState"><span>${esc(name)}</span><strong class="${ok?'ok':'bad'}">${ok?'VERIFICADO':'● '+(configured?'AGUARDA TESTE':'AGUARDA CONFIGURAÇÃO')}</strong></div>`).join('')}
const aurionOldService=window.aurionServiceResult;
window.aurionServiceResult=raw=>{let x=JSON.parse(raw);x.result.checkedAt=Date.now();aurionOldService(JSON.stringify(x));renderSetup()};
const aurionOldVault=window.aurionVaultResult;
window.aurionVaultResult=raw=>{aurionOldVault(raw);renderSetup()};
window.aurionAccountResult=raw=>{try{
 let x=JSON.parse(raw),w=workState();w.accounts=w.accounts||{};
 if(x.result?.ok)w.accounts[x.label]=Date.now();else delete w.accounts[x.label];
 localStorage.setItem(WORK_KEY,JSON.stringify(w));
 let names=[];
 if(x.label==='openai'&&x.result?.ok){try{let data=JSON.parse(x.result.body||'{}').data||[];names=data.map(v=>v.id).filter(v=>v.startsWith('gpt-')&&!v.includes('realtime')).sort((a,b)=>(a.includes('mini')?-1:0)-(b.includes('mini')?-1:0)).slice(0,40);$('aiModelList').innerHTML=names.map(v=>'<option value="'+esc(v)+'"></option>').join('');if(!$('aiModel').value||$('aiModel').value.toLowerCase()==='aurion')$('aiModel').value=names.find(v=>v==='gpt-5-mini')||names.find(v=>v.includes('mini'))||names[0]||''}catch{}}
 $('accountLog').textContent=x.label+': '+(x.result?.ok?'CONECTADO · HTTP '+x.result.http+(names.length?' · '+names.length+' modelos de chat encontrados':''):'FALHOU · '+(x.result?.http||x.result?.error||'sem resposta'));
}catch(e){$('accountLog').textContent='Falha ao ler teste: '+e.message}renderSetup()};
function importPastedKeys(){let v=$('keysPaste').value.trim();if(!v){$('keysImportLog').textContent='Cole JSON ou linhas KEY=valor.';return}native('importKeysJson',v);$('keysPaste').value='';$('keysImportLog').textContent='Importando para o cofre...'}
window.aurionKeysResult=raw=>{try{let x=JSON.parse(raw);$('keysImportLog').textContent=x.ok?'Chaves guardadas: '+(x.services||[]).join(', '):'Falha: '+x.error;refreshAccounts();renderSetup();if(x.ok)for(let p of x.services||[])native('testAccount',p)}catch(e){$('keysImportLog').textContent=e.message}};
const aurionPriorAiResult=window.aurionAiResult;
window.aurionAiResult=raw=>{try{let x=JSON.parse(raw);if(x.result?.ok){aurionPriorAiResult(raw);$('agentLog').textContent=(x.result.model?'AURION via '+x.label+' · '+x.result.model+'\n\n':'')+$('agentLog').textContent;return}let info=x.result?.error||'sem resposta';try{let j=JSON.parse(x.result?.body||'{}');info=j.error?.message||j.message||info}catch{}let offline=offlineAnswer(window.aurionPendingQuestion||'');$('agentLog').textContent='A rota '+x.label+' falhou: '+info+'\n\nAURION OFFLINE\n'+offline;native('memoryAdd','conversation','Falha '+x.label,info,JSON.stringify({http:x.result?.http||0}));native('memoryAdd','conversation','Resposta offline',offline,'{}');if(pendingLab){$('labOut'+pendingLab).textContent=info;pendingLab=''}}catch(e){$('agentLog').textContent='Falha na resposta: '+e.message}};
seedFactoryContext();renderHistory();renderSetup();setInterval(()=>{renderWork();if(document.getElementById('history').classList.contains('active'))renderHistory()},1000);

// The full agent chat works without a remote model. Retrieval reports only curated facts.
function offlineAnswer(question){
 const q=question.toLocaleLowerCase('pt-BR').normalize('NFD').replace(/[\u0300-\u036f]/g,'');
 if(/^(oi|ola|bom dia|boa noite|boa tarde|e ai|salve)[!. ]*$/.test(q))return 'Salve, ANARK. Estou funcionando neste POCO sem PC. Posso consultar nosso contexto sobre T8i, painel, agentes, edição, Band, fone e conexões. O que você quer resolver primeiro?';
 const score=k=>k.terms.reduce((n,t)=>n+(q.includes(t.normalize('NFD').replace(/[\u0300-\u036f]/g,''))?2:0),0);
 const hit=AURION_KNOWLEDGE.map(k=>({k,n:score(k)})).sort((a,b)=>b.n-a.n)[0];
 let matches=[];try{const tokens=q.split(/\W+/).filter(x=>x.length>3).slice(0,4);for(const token of tokens)matches.push(...getMemories('factory',token,2));}catch{}
 const unique=[...new Map(matches.map(m=>[m.title,m])).values()].slice(0,2);let references=[];try{for(const token of q.split(/\W+/).filter(x=>x.length>4).slice(0,2))references.push(...getMemories('reference',token,2))}catch{}references=[...new Map(references.map(m=>[m.title,m])).values()].slice(0,1);const excerpt=references.map(m=>{let lower=m.body.toLocaleLowerCase('pt-BR'),i=Math.max(0,lower.indexOf(q.split(/\W+/).find(x=>x.length>4)||''));return m.title+': '+m.body.slice(Math.max(0,i-100),i+350)}).join(' | ');
 if(hit?.n){let answer=hit.k.answer;if(unique.length)answer+='\n\nNa memória de fábrica: '+unique.map(m=>m.title+' — '+m.body).join(' | ').slice(0,900);return answer+(excerpt?'\n\nReferência sincronizada: '+excerpt:'')+'\n\nPara executar uma ação, abra a aba indicada e confira o resultado nela.'}
 if(excerpt)return 'Achei esta referência no contexto importado: '+excerpt+'\n\nÉ uma fonte para consulta, não uma ação executada.';return 'Não tenho uma resposta verificada para essa pergunta no contexto offline. Posso ajudar com T8i/CR3, imagens, vídeo, memória, PC, ComfyUI, Band, fone e configuração. Para análise livre, configure uma API em Contas ou o nó PC; não vou inventar uma resposta.';
}
const guideAskOriginal=askGuide;
function askGuide(){let q=$('guideQuestion').value.trim();if(!q)return;let answer=offlineAnswer(q);$('guideReply').textContent=answer;$('guideQuestion').value='';native('memoryAdd','conversation','Orientador local · pergunta',q,'{}');native('memoryAdd','conversation','Orientador local · resposta',answer,'{}')}
function autoScan(manual=false){
 let lines=[],diag={};try{diag=JSON.parse(native('getDiagnostics')||'{}');lines.push('POCO: '+(diag.model||'Android')+' · '+(diag.network||'sem rede')+' · '+(diag.storageFreeGb??'?')+' GB livres');lines.push('Bluetooth: '+(diag.bluetoothEnabled?'ligado':'desligado')+' · Mi Fitness: '+(diag.miFitness?'instalado':'não detectado'));}catch(e){lines.push('Diagnóstico Android indisponível: '+e.message)}
 let old=getMemories('factory','',100);if(!old.length){localStorage.removeItem('aurion6Seeded');seedFactoryContext();lines.push('Contexto local recuperado.')}else lines.push('Contexto local: '+old.length+' registros.');
 let d=data();if(!d.settings||typeof d.settings!=='object')lines.push('Nó PC não configurado; modo offline ativo.');
 let configured={};try{configured=JSON.parse(native('accountStatus')||'{}')}catch{}
 if(diag.network!=='offline'){
  for(const [provider,present] of Object.entries(configured))if(present)native('testAccount',provider);
  if(d.settings?.agent)native('testService','Home Node',d.settings.agent+'/health');
  if(d.settings?.comfy)native('testService','ComfyUI',d.settings.comfy+'/system_stats');
  if(d.settings?.ollama)native('testService','Ollama',d.settings.ollama+'/api/tags');
  if(manual||Date.now()-Number(localStorage.getItem('aurion6GitSyncAt')||0)>86400000)native('syncGitContext');
  lines.push('Testes de ligações configuradas iniciados; verde só após resposta recente.');
 }else lines.push('Sem rede: scan local concluído; sincronização pendente.');
 $('autoScanLog').textContent=lines.join('\n');renderSetup();renderAll();
}
window.aurionSyncResult=raw=>{try{let x=JSON.parse(raw);if(x.ok)localStorage.setItem('aurion6GitSyncAt',Date.now());$('autoScanLog').textContent+='\nGit: '+(x.ok?'contexto atualizado ('+x.updated+' arquivo(s))':'não sincronizado: '+(x.error||'offline'));renderAll()}catch{}};
window.aurionContextImportResult=raw=>{try{let x=JSON.parse(raw);$('autoScanLog').textContent+='\nDrive/arquivo: '+(x.ok?'contexto importado: '+x.title:'falha: '+x.error);renderAll()}catch{}};
setTimeout(()=>autoScan(false),400);

// v6.3: actionable voice shortcuts, bounded automatic experiments and route failover.
window.aurionUpdateStatus=raw=>{try{const s=JSON.parse(raw);$('updateLog').textContent=s.message;$('installUpdate').disabled=s.state!=='available'&&s.state!=='permission';if(s.state==='available')native('memoryAdd','update','Atualização disponível '+s.version,s.message,'{}')}catch{}};
window.aurionImageResult=raw=>{try{const x=JSON.parse(raw);$('imageLog').textContent=x.ok?'Imagem salva na galeria · '+x.model+' · '+x.bytes+' bytes\n'+x.uri:'Falha: '+x.error}catch(e){$('imageLog').textContent=e.message}};
function generateImage(){let p=$('imagePrompt').value.trim();if(!p){$('imageLog').textContent='Descreva a imagem primeiro.';return}$('imageLog').textContent='Gerando pela Hugging Face; aguardando imagem real...';native('generateImage',p,$('imageModel').value.trim())}
function voiceShortcutMap(){try{return JSON.parse(localStorage.getItem('aurionVoiceShortcuts')||'{}')}catch{return{}}}
function saveVoiceShortcut(){let phrase=$('voicePhrase').value.trim().toLocaleLowerCase('pt-BR'),action=$('voiceAction').value;if(!phrase||phrase.length>80)return;let map=voiceShortcutMap();map[phrase]=action;localStorage.setItem('aurionVoiceShortcuts',JSON.stringify(map));$('voiceLog').textContent='Atalho registrado: '+phrase+' → '+action;native('memoryAdd','shortcut','Voz · '+phrase,action,'{}')}
function voiceCommand(raw){let q=String(raw||'').trim(),normalized=q.toLocaleLowerCase('pt-BR');$('agentText').value=q;$('voiceLog').textContent='Ouvido: '+q;native('memoryAdd','conversation','Comando por voz',q,'{}');let map=voiceShortcutMap();let action=Object.keys(map).find(k=>normalized.startsWith(k));action=action?map[action]:/^(abrir|mostrar) (laboratorio|laboratório)/.test(normalized)?'lab':/^(abrir|mostrar) (camera|câmera)/.test(normalized)?'capture':/^(abrir|mostrar) (memoria|memória)/.test(normalized)?'memory':/^(abrir|mostrar) (config)/.test(normalized)?'setup':/^(gerar|criar) (imagem|foto)/.test(normalized)?'imagegen':/^(atualizar|verificar atualização)/.test(normalized)?'update':/^(cruzar|testar|laboratorio automatico|laboratório automático)/.test(normalized)?'autolab':'chat';
 if(action==='update'){go('setup');native('checkForUpdate')}
 else if(action==='autolab'){go('lab');startAutoLab()}
 else if(action==='imagegen'){go('imagegen');$('imagePrompt').value=q.replace(/^(gerar|criar) (imagem|foto)( de|:)?\s*/i,'');if($('imagePrompt').value)generateImage()}
 else if(action==='chat')sendAgent();else go(action);
}
window.aurionVoiceResult=voiceCommand;
window.aurionHeadsetButton=()=>{$('voiceLog').textContent='Botão do fone recebido · ouvindo comando.'};

let autoExperiment=null,autoAgent=null;
function aiText(x){let body=x.result?.body||'';try{let j=JSON.parse(body);return j.output?.map?.(o=>o.content?.map?.(c=>c.text||'').join('')).join('')||j.candidates?.[0]?.content?.parts?.map?.(v=>v.text||'').join('')||j.choices?.[0]?.message?.content||body}catch{return body}}
function aiError(x){try{let j=JSON.parse(x.result?.body||'{}');return j.error?.message||j.message||x.result?.error||'sem resposta'}catch{return x.result?.error||'sem resposta'}}
function configuredRoutes(){let a={};try{a=JSON.parse(native('accountStatus')||'{}')}catch{}return ['groq','nvidia','gemini','huggingface','openai'].filter(p=>a[p])}
const sendAgentBeforeFailover=sendAgent;
sendAgent=function(){let t=$('agentText').value.trim(),selected=$('aiProvider').value;if(!t)return sendAgentBeforeFailover();if(['offline','local'].includes(selected))return sendAgentBeforeFailover();let routes=[selected,...configuredRoutes().filter(p=>p!==selected)];autoAgent={prompt:t,memory:memoryContext($('memoryQuery').value||t),routes,tried:[]};native('memoryAdd','conversation','Operador',t,JSON.stringify({provider:selected,autoFallback:true}));runAgentRoute()};
function runAgentRoute(){let a=autoAgent;if(!a)return;let p=a.routes.shift();if(!p){let failure=a.tried.join('\n');let answer=offlineAnswer(a.prompt);$('agentLog').textContent='Rotas indisponíveis:\n'+failure+'\n\nAURION OFFLINE\n'+answer;native('memoryAdd','conversation','Fallback offline',answer,JSON.stringify({routes:a.tried}));autoAgent=null;return}$('agentLog').textContent='Tentando '+p+'...\n'+a.tried.join('\n');native('runCloudAi',p,p===$('aiProvider').value?$('aiModel').value.trim():'',a.prompt,a.memory)}
const aiResultBeforeAutomation=window.aurionAiResult;
window.aurionAiResult=raw=>{let x;try{x=JSON.parse(raw)}catch{return aiResultBeforeAutomation(raw)};
 if(autoExperiment&&autoExperiment.active===x.label){let e=autoExperiment;let answer=x.result?.ok?aiText(x):'',error=x.result?.ok?'':aiError(x);if(answer&&x.result?.ok)e.success++;e.attempts.push({route:x.label,model:x.result?.model||'',ok:!!(answer&&x.result?.ok),answer:answer.slice(0,8000),error:error.slice(0,500),http:x.result?.http||0});e.active=null;advanceAutoLab();return}
 if(autoAgent){if(x.result?.ok&&aiText(x).trim()){let a=autoAgent;autoAgent=null;window.aurionPendingQuestion=a.prompt;aiResultBeforeAutomation(raw);$('agentLog').textContent='Rota ativa: '+x.label+' · '+(x.result.model||'modelo automático')+'\n'+(a.tried.length?'Alternativas tentadas: '+a.tried.join('; ')+'\n':'')+'\n'+$('agentLog').textContent;return}autoAgent.tried.push(x.label+': '+aiError(x).slice(0,180));runAgentRoute();return}
 aiResultBeforeAutomation(raw)
};
function startAutoLab(){if(autoExperiment){$('autoLabLog').textContent='Ciclo já em andamento.';return}let routes=configuredRoutes();if(!routes.length){$('autoLabLog').textContent='Nenhuma API configurada. Importe as chaves em Contas.';return}let topics=$('labTopics').value.trim();let prompt=$('labPrompt').value.trim()||(topics?'Cruze estes temas: '+topics+'. Proponha hipótese testável, validação e limites. Não afirme que realizou experimento físico.':'Projeto AURION ONE: proponha um cruzamento verificável entre fotografia Canon T8i, edição de imagem no POCO e fluxo de entrega. Separe hipótese, teste reproduzível, resultado esperado e limite. Não afirme que executou o teste físico.');let criterion=$('labCriterion').value.trim()||'clareza, evidência, viabilidade no POCO';autoExperiment={prompt,criterion,routes:routes.slice(),attempts:[],success:0,active:null,started:Date.now()};$('autoLabLog').textContent='Cruzando rotas disponíveis com o mesmo contexto...';advanceAutoLab()}
function advanceAutoLab(){let e=autoExperiment;if(!e)return;if(e.success>=2||!e.routes.length){let successes=e.attempts.filter(x=>x.ok),comparison=successes.length>1?'Duas respostas registradas; diferenças devem ser conferidas pelo operador.':'Apenas '+successes.length+' rota respondeu; sem comparação válida.';let body=JSON.stringify({prompt:e.prompt,criterion:e.criterion,attempts:e.attempts,comparison,started:e.started,finished:Date.now()});native('memoryAdd','experiment','Laboratório automático · '+new Date().toLocaleString('pt-BR'),body,JSON.stringify({verifiedResponses:successes.length}));$('autoLabLog').textContent=comparison+'\n'+e.attempts.map(x=>x.route+' · '+(x.ok?'resposta '+x.answer.length+' caracteres':'falhou: '+x.error)).join('\n')+'\nRegistrado em Memória.';$('labOutA').textContent=successes[0]?.answer||'Sem resposta';$('labOutB').textContent=successes[1]?.answer||'Sem segunda resposta';autoExperiment=null;return}let next=e.routes.shift();e.active=next;$('autoLabLog').textContent='Executando '+next+' · '+e.attempts.length+' tentativa(s)...';native('runCloudAi',next,'',e.prompt,memoryContext(e.prompt))}
setTimeout(()=>{try{let d=JSON.parse(native('getDiagnostics')||'{}');if(d.network==='offline'||!configuredRoutes().length)return;let key='aurionAutoLabLastAt';if(Date.now()-Number(localStorage.getItem(key)||0)>86400000){localStorage.setItem(key,Date.now());startAutoLab()}}catch{}},9000);
$('aiProvider').addEventListener('change',()=>{let p=$('aiProvider').value;if(p!=='openai'){$('aiModel').value='';$('aiModelList').innerHTML=''}$('accountLog').textContent='Provedor selecionado: '+p+' · Modelo Automático recomendado.'});
