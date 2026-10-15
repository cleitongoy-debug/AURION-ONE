'use strict';
const el=id=>document.getElementById(id);
const onMobile=typeof Aurion!=='undefined';
let lastReply='',requestSeq=0;
const pending={};
window.NativeReply=function(id,content){
 if(pending[id]){pending[id](decode(content));delete pending[id]}
};
function decode(raw){try{return JSON.parse(raw)}catch(e){return {error:String(raw)}}}
function api(profile,path,method,body){
 if(!onMobile)return Promise.resolve({error:'Abra no APK Android para conectar ao PC'});
 return new Promise(resolve=>{
  const id='req'+(++requestSeq);pending[id]=resolve;
  Aurion.request(profile,path,method,JSON.stringify(body||{}),id);
 });
}
function tab(id){
 document.querySelectorAll('main section').forEach(x=>x.classList.toggle('active',x.id===id));
 document.querySelectorAll('nav button').forEach(x=>x.classList.toggle('active',x.dataset.tab===id));
}
function bubble(text,mine){
 const n=document.createElement('div');n.className='bubble '+(mine?'fromMe':'fromBot');n.textContent=String(text??'');
 el('log').appendChild(n);el('log').scrollTop=el('log').scrollHeight;
 return n;
}
const guide=[
 ['octane render cuda', 'O OctaneRender 2022.1 para Cinema 4D 2023 depende do PC e da GPU NVIDIA. Este APK faz modelagem local simplificada e exporta scripts para o C4D. Não executa o render Octane no Android.'],
 ['cinema 4d c4d', 'Use a aba 3D para criar cubo, esfera, cilindro, torus e plano. Selecione e ajuste posição, escala e material. Pressione Exportar script C4D para criar código Python executável no Cinema 4D do PC.'],
 ['script python código', 'No C4D Python, use import c4d; doc=c4d.documents.GetActiveDocument(); obj=c4d.BaseObject(c4d.Ocube); doc.InsertObject(obj); c4d.EventAdd(). Gere objetos pela aba 3D para receber o código completo.'],
 ['cabelo hair física', 'No PC: Hair Object, guias, restrições e material do Hair Renderer. Para Octane, consulte compatibilidade do plugin e as opções de renderização de cabelos da sua versão.'],
 ['material textura', 'No Android você altera cor básica no objeto; textura PBR/Octane completa exige materiais e renderizador compatíveis no PC.'],
 ['animação keyframe', 'No app, use a linha do tempo experimental para rotação. Animação por keyframes e export animado ainda estão pendentes.'],
 ['rea engenharia reversa', 'REA é uma ferramenta de análise de software autorizada e auditável. Ele não transforma binários Windows em aplicativos Android. Instalação e análise acontecem no PC.'],
 ['yellow yelow yellowstar', 'YellowStar citado no histórico do Drive não será executado nem incluído no APK: há registro de bloqueio de segurança. Use apenas instalações e licenças oficiais de Octane/Cinema 4D.'],
 ['offline inteligência local', 'Estou em modo offline: assistente por base de conhecimento e regras, não um modelo neural completo. Notas que você registrar permanecem neste dispositivo.'],
 ['export glb obj fbx', 'Nesta versão, as cenas são salvas em JSON e podem ser convertidas para scripts Python do C4D. Exportação OBJ, GLB e FBX real ainda está pendente.'],
 ['render 3d', 'A viewport 3D funciona offline no Android. Este protótipo utiliza projeção no canvas, não Octane, Redshift nem path tracing.'],
 ['scan drive git', 'Drive e GitHub não são acessados automaticamente no modo offline. Para integrá-los com autenticação e histórico, use o agente do PC.']
];
function offlineAsk(prompt){
 const q=prompt.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');
 const notes=JSON.parse(localStorage.getItem('aurion_offline_notes')||'[]');
 let candidates=guide.map(([tags,answer])=>({tags,answer}));
 for(const n of notes)candidates.push({tags:n.title.toLowerCase(),answer:n.text});
 let ranked=candidates.map(c=>({c,score:c.tags.split(' ').reduce((s,t)=>s+(q.includes(t)?t.length:0),0)})).sort((a,b)=>b.score-a.score);
 if(ranked.length&&ranked[0].score>3)return 'AURION OFFLINE · BASE LOCAL\n\n'+ranked[0].c.answer;
 if(/cubo|cube|esfera|sphere|cilindro|torus|plano/.test(q)){
  let type=/esfera|sphere/.test(q)?'sphere':/cilindro/.test(q)?'cylinder':/torus/.test(q)?'torus':/plano/.test(q)?'plane':'cube';
  modelAdd(type);return 'Objeto adicionado à sua cena 3D local: '+type+'. Abra a aba 3D para ajustar. Esta foi uma ação local, sem PC.';
 }
 return 'AURION OFFLINE · LAB\n\nTenho recursos locais para modelagem 3D, exportação Python, estudo C4D/Octane e suas notas pessoais. Ainda não tenho um modelo de linguagem completo embarcado. Para respostas livres, configure o AURION ONE do PC na aba Conexão. Para ensinar um assunto novo, use a opção “Adicionar conhecimento offline” nesta aba.';
}
async function sendChat(){
 const txt=el('message').value.trim();if(!txt)return;
 bubble(txt,true);el('message').value='';
 const mode=el('chatMode')?el('chatMode').value:'offline';
 const pendingBubble=bubble('Processando…',false);
 let response='';
 if(mode==='offline')response=offlineAsk(txt);
 else {
  const a=await api('aurion','/api/prompt','POST',{text:txt,device_id:'poco-cinema',moving:false});
  response=a.answer||a.error||a.detail||JSON.stringify(a);
 }
 pendingBubble.remove();lastReply=response;bubble(response,false);
}
function useChatInEditor(){
 if(!lastReply)return alert('Envie primeiro uma mensagem ao agente');
 const fenced=lastReply.match(/\x60\x60\x60(?:python)?\s*([\s\S]*?)\x60\x60\x60/i);
 el('code').value=fenced?fenced[1].trim():lastReply;tab('editor');
}
function addKnowledge(){
 let title=el('noteTitle').value.trim(),body=el('noteText').value.trim();
 if(!title||!body)return alert('Preencha assunto e conteúdo.');
 let notes=JSON.parse(localStorage.getItem('aurion_offline_notes')||'[]');
 if(notes.length>=100)return alert('Limite local de 100 notas. Exporte suas notas antes de substituir.');
 notes.push({title:title.substring(0,100),text:body.substring(0,5000)});
 localStorage.setItem('aurion_offline_notes',JSON.stringify(notes));
 el('noteTitle').value='';el('noteText').value='';
 el('knowledgeStatus').textContent=notes.length+' notas salvas apenas neste dispositivo.';
}
async function checkStatus(){
 const [a,c]=await Promise.all([api('aurion','/api/status','GET'),api('c4d','/api/status','GET')]);
 el('pcflag').textContent='AURION: '+(a.aurion||'offline');
 el('c4dflag').textContent='C4D: '+(c.bridge||'offline');
 el('pcflag').classList.toggle('online',a.aurion==='online');
 el('c4dflag').classList.toggle('online',c.bridge==='online');
 el('status').textContent='AURION ONE\n'+JSON.stringify(a,null,2)+'\n\nC4D BRIDGE\n'+JSON.stringify(c,null,2);
}
async function checkInventory(){
 const x=await api('aurion','/api/inventory','GET');el('status').textContent=JSON.stringify(x,null,2);
}
function saveConnection(p){
 const url=el(p+'Url').value.trim(),token=el(p+'Token').value.trim();
 if(!onMobile)return alert('Configure pelo APK Android');
 const ok=Aurion.put(p+'_url',url)&&Aurion.put(p+'_token',token);
 el('configStatus').textContent=ok?'Conexão armazenada. Confira o status na aba Cinema.':'Endereço inválido. Use IPv4 de rede privada e porta, com token de pelo menos 12 caracteres.';
 if(ok)el(p+'Token').value='';
}
function saveScript(){
 if(!onMobile){el('editorStatus').textContent='Abra o APK para salvar.';return}
 el('editorStatus').textContent='Resultado: '+Aurion.save(el('scriptName').value||'script',el('code').value);
}
async function queueScript(){
 const code=el('code').value;
 if(!code.trim())return;
 if(!confirm('Enviar Python ao PC para revisão manual antes de executar no C4D?'))return;
 const a=await api('c4d','/api/scripts','POST',{name:el('scriptName').value,code});
 el('editorStatus').textContent=JSON.stringify(a,null,2);
}
const templates={
 cube:'import c4d\ndoc=c4d.documents.GetActiveDocument()\nobj=c4d.BaseObject(c4d.Ocube)\nobj.SetName("AURION_Cubo")\ndoc.InsertObject(obj)\nc4d.EventAdd()\nprint("Cubo criado")',
 camera:'import c4d\ndoc=c4d.documents.GetActiveDocument()\ncamera=c4d.BaseObject(c4d.Ocamera)\ncamera.SetName("AURION_Camera")\ndoc.InsertObject(camera)\nc4d.EventAdd()',
 light:'import c4d\ndoc=c4d.documents.GetActiveDocument()\nlight=c4d.BaseObject(c4d.Olight)\nlight.SetName("AURION_Luz")\ndoc.InsertObject(light)\nc4d.EventAdd()',
 material:'import c4d\ndoc=c4d.documents.GetActiveDocument()\nmat=c4d.BaseMaterial(c4d.Mmaterial)\nmat.SetName("AURION_Material")\ndoc.InsertMaterial(mat)\nc4d.EventAdd()',
 octane:'import c4d\nprint("Cinema 4D:", c4d.GetC4DVersion())\nprint("Confira Extensions > Octane e a licença autorizada no PC.")'
};
function loadTemplate(){const v=el('template').value;if(v&&templates[v])el('code').value=templates[v]}
if(onMobile)for(const p of ['aurion','c4d'])el(p+'Url').value=Aurion.get(p+'_url')||'';
