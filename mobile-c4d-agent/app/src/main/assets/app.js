'use strict';
const el=id=>document.getElementById(id);
const onMobile=typeof Aurion!=='undefined';
let lastReply='';
function tab(id){
 document.querySelectorAll('main section').forEach(x=>x.classList.toggle('active',x.id===id));
 document.querySelectorAll('nav button').forEach(x=>x.classList.toggle('active',x.dataset.tab===id));
}
function json(raw){try{return JSON.parse(raw)}catch(e){return {error:String(raw)}}}
function api(profile,path,method,body){
 if(!onMobile)return {error:'Abra no APK Android para conectar ao PC'};
 return json(Aurion.call(profile,path,method,JSON.stringify(body||{})));
}
function escapeStr(v){return String(v??'')}
function bubble(text,mine){
 const n=document.createElement('div');n.className='bubble '+(mine?'fromMe':'fromBot');n.textContent=escapeStr(text);
 el('log').appendChild(n);el('log').scrollTop=el('log').scrollHeight;
}
function sendChat(){
 const txt=el('message').value.trim();if(!txt)return;
 bubble(txt,true);el('message').value='';bubble('Consultando agente local…',false);
 setTimeout(()=>{
  const a=api('aurion','/api/prompt','POST',{text:txt,device_id:'poco-cinema',moving:false});
  el('log').lastChild.remove();
  lastReply=a.answer||a.error||a.detail||JSON.stringify(a);
  bubble(lastReply,false);
 },50);
}
function useChatInEditor(){if(!lastReply)return alert('Envie primeiro uma mensagem ao agente');
 const fenced=lastReply.match(/\x60\x60\x60(?:python)?\s*([\s\S]*?)\x60\x60\x60/i);
 el('code').value=fenced?fenced[1].trim():lastReply;tab('editor');
}
function checkStatus(){
 const a=api('aurion','/api/status','GET'), c=api('c4d','/api/status','GET');
 el('pcflag').textContent='AURION: '+(a.aurion||'offline');
 el('c4dflag').textContent='C4D: '+(c.bridge||'offline');
 el('pcflag').classList.toggle('online',a.aurion==='online');
 el('c4dflag').classList.toggle('online',c.bridge==='online');
 el('status').textContent='AURION ONE\n'+JSON.stringify(a,null,2)+'\n\nC4D BRIDGE\n'+JSON.stringify(c,null,2);
}
function checkInventory(){
 const x=api('aurion','/api/inventory','GET');el('status').textContent=JSON.stringify(x,null,2);
}
function saveConnection(p){
 const prefix=p==='aurion'?'aurion':'c4d';
 const url=el(prefix+'Url').value.trim(),token=el(prefix+'Token').value.trim();
 if(!onMobile)return alert('Configure pelo APK Android');
 const ok=Aurion.put(prefix+'_url',url)&&Aurion.put(prefix+'_token',token);
 el('configStatus').textContent=ok?'Conexão armazenada. Verifique o status na aba Cinema.':'Endereço inválido. Use endereço IPv4 da rede privada e porta; informe token.';
 if(ok)el(prefix+'Token').value='';
}
function saveScript(){
 if(!onMobile){el('editorStatus').textContent='Abra o APK para salvar.';return}
 const name=el('scriptName').value||'script',code=el('code').value;
 el('editorStatus').textContent='Resultado: '+Aurion.save(name,code);
}
function queueScript(){
 const code=el('code').value;
 if(!code.trim())return;
 if(!confirm('Enviar o script Python ao PC para revisão e aprovação manual no Cinema 4D?'))return;
 const a=api('c4d','/api/scripts','POST',{name:el('scriptName').value,code});
 el('editorStatus').textContent=JSON.stringify(a,null,2);
}
const templates={
 cube:'import c4d\ndoc=c4d.documents.GetActiveDocument()\nobj=c4d.BaseObject(c4d.Ocube)\nobj.SetName("AURION_Cubo")\ndoc.InsertObject(obj)\nc4d.EventAdd()\nprint("Cubo criado")',
 camera:'import c4d\ndoc=c4d.documents.GetActiveDocument()\ncamera=c4d.BaseObject(c4d.Ocamera)\ncamera.SetName("AURION_Camera")\ndoc.InsertObject(camera)\nc4d.EventAdd()',
 light:'import c4d\ndoc=c4d.documents.GetActiveDocument()\nlight=c4d.BaseObject(c4d.Olight)\nlight.SetName("AURION_Luz")\ndoc.InsertObject(light)\nc4d.EventAdd()',
 material:'import c4d\ndoc=c4d.documents.GetActiveDocument()\nmat=c4d.BaseMaterial(c4d.Mmaterial)\nmat.SetName("AURION_Material")\ndoc.InsertMaterial(mat)\nc4d.EventAdd()',
 octane:'import c4d\nprint("Versão Cinema 4D:", c4d.GetC4DVersion())\nprint("Verifique o menu Extensions > Octane e sua licença no PC.")\nprint("Octane não é executado no Android.")'
};
function loadTemplate(){const v=el('template').value;if(v&&templates[v])el('code').value=templates[v]}
if(onMobile){
 for(const p of ['aurion','c4d'])el(p+'Url').value=Aurion.get(p+'_url')||'';
}
