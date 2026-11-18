/* AURION Produção - ferramentas v7.3 - arquivos reais, fila ComfyUI e trilha de auditoria.
   Não faz render 3D/Octane em Android e não faz upload OAuth Drive. */
(function(){
"use strict";
const KEY="aurion_producao_jobs_v1";
const ENGINE_KEY="aurion_comfy_endpoint_v1";
const WF_KEY="aurion_comfy_workflow_v1";
const FILE_MAX=100*1024*1024;
const available="PNG, JPG/JPEG, WEBP (importar e exportar); GIF, TIFF/TIF, BMP, HEIC, DNG/CR3/CR2, EXR, HDR, PSD/PSB, MP4/MOV/WEBM, WAV/MP3, GLB/GLTF, OBJ/MTL, FBX, BLEND, C4D, ZIP (arquivar/importar sem converter).";
function el(tag,attrs,html){const n=document.createElement(tag);Object.entries(attrs||{}).forEach(([k,v])=>n.setAttribute(k,v));if(html!==undefined)n.innerHTML=html;return n}
function safe(s){return escapeHtml(s)}
function say(s){status(s);let l=document.getElementById("toolStatus");if(l)l.textContent=s}
function filename(s){return String(s||"CLIENTE").replace(/[^A-Za-z0-9_.-]/g,"_").slice(0,65)}
function now(){return new Date().toISOString()}
function addAudit(type,msg,result,evidence){
 state.logs=state.logs||[];
 state.logs.push({at:now(),agent:"ARANHA",platform:"AURION_PRODUCAO_ANDROID",type:type,
 activity:msg,result:result,evidence:evidence||""});
 save();renderLogs();
}
function snapshots(){try{return JSON.parse(localStorage.getItem(KEY)||"{}")}catch(e){return {}}}
function archiveCurrent(){if(!state.meta||!(state.meta.job||state.meta.client||state.shots.length||Object.keys(state.refs||{}).length))return;let a=snapshots();a[state.projectKey]=JSON.parse(JSON.stringify(state));localStorage.setItem(KEY,JSON.stringify(a));}
function saveArchive(){archiveCurrent();renderProjects();say("Projeto registrado no catálogo local; imagens preservadas no IndexedDB.")}
function renderProjects(){
 const a=snapshots(),s=document.getElementById("savedProjects");if(!s)return;
 s.innerHTML='<option value="">Selecione um projeto arquivado</option>'+
 Object.keys(a).sort((x,y)=>(a[y].updatedAt||"").localeCompare(a[x].updatedAt||"")).map(k=>
 '<option value="'+safe(k)+'">'+safe((a[k].meta?.client||"CLIENTE")+' · '+(a[k].meta?.job||k))+'</option>').join("");
}
function restoreProject(){
 const key=document.getElementById("savedProjects").value,a=snapshots();
 if(!key||!a[key]){say("Selecione um projeto do catálogo.");return}
 if(!confirm("Salvar sessão atual e abrir projeto arquivado?"))return;
 archiveCurrent();
 state=JSON.parse(JSON.stringify(a[key]));save();restoreMeta();renderAll();show("brief");renderProjects();
 say("Projeto restaurado: "+(state.meta.job||key)+". Verifique se as imagens locais ainda estão armazenadas.");
}
function validateImport(x){
 if(!x||typeof x!=="object"||!x.meta||typeof x.meta!=="object"||!Array.isArray(x.shots||[])||!(x.schema>=1&&x.schema<=4))throw Error("Manifesto AURION inválido ou versão incompatível.");
 return x
}
async function importManifest(input){
 const f=input.files&&input.files[0];input.value="";if(!f)return;
 if(f.size>4*1024*1024){say("Manifesto acima de 4 MB recusado.");return}
 try{
 const incoming=validateImport(JSON.parse(await f.text()));
 if(!confirm("Importar manifesto? A sessão atual será guardada no catálogo local; mídias NÃO acompanham o JSON."))return;
 archiveCurrent();
 const next=blank(),meta=next.meta;
 for(const k of Object.keys(meta))if(typeof incoming.meta[k]==="string")meta[k]=incoming.meta[k].slice(0,10000);
 next.shots=(incoming.shots||[]).slice(0,150).map((s,i)=>({
 uid: "import-"+Date.now()+"-"+i,title:String(s.title||"Cena "+(i+1)),action:String(s.action||""),
 place:String(s.place||""),lens:String(s.lens||"50mm"),camera:String(s.camera||"plano médio"),
 duration:Number(s.duration)||5,format:String(s.format||"16:9"),status:"RASCUNHO",media:null
 }));
 next.logs=(incoming.logs||[]).slice(-350).map(l=>({
 at:String(l.at||now()),agent:String(l.agent||"IMPORTADO"),platform:String(l.platform||""),
 type:String(l.type||"Registro"),activity:String(l.activity||""),result:String(l.result||"IMPORTADO"),
 evidence:String(l.evidence||"")}));
 next.extraAssets=[];
 next.checks={};
 // Nunca reutilizar a chave de mídia de outro aparelho e fingir que as imagens estão aqui.
 state=next;addAudit("Importação","Importado manifesto "+f.name+"; fotos e vídeos não incluídos no JSON.","VALIDADO",f.name);
 save();restoreMeta();renderAll();show("brief");renderProjects();
 say("Manifesto importado. Importe as fotos originais novamente nos slots.");
 }catch(e){say("Falha na importação: "+e.message)}
}
function toDownload(blob,name,mime){
 if(blob.size>20*1024*1024){say("Arquivo grande: exportação direta limitada a 20 MB. Utilize o arquivo original no Drive/PC.");return}
 if(window.AurionAndroid&&AurionAndroid.saveBase64File){
 const r=new FileReader();
 r.onload=()=>{try{AurionAndroid.saveBase64File(name,mime||blob.type||"application/octet-stream",String(r.result).split(",")[1]);say("Exportação enviada ao Android; aguarde a confirmação em Downloads/AURION/EXPORTS.");}
 catch(e){say("Falha ao exportar: "+e.message)}};
 r.onerror=()=>say("Não foi possível ler o arquivo.");r.readAsDataURL(blob);return;
 }
 const url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download=name;
 document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),15000);
 say("Download solicitado ao navegador.");
}
function assetMeta(file,key){
 return {id:"asset-"+Date.now()+"-"+Math.random().toString(36).slice(2,7),name:file.name,
 type:file.type||"application/octet-stream",size:file.size,key:key,importedAt:now(),format:file.name.split(".").pop().toLowerCase()};
}
async function importFiles(input){
 const files=Array.from(input.files||[]);input.value="";
 let ok=0,errors=[];
 state.extraAssets=state.extraAssets||[];
 for(const f of files){
 if(f.size>FILE_MAX){errors.push(f.name+" excede 100 MB");continue}
 try{const key=state.projectKey+"::asset::"+Date.now()+"-"+Math.random().toString(36).slice(2,9);
 await storeBlob(key,f);state.extraAssets.push(assetMeta(f,key));ok++;
 }catch(e){errors.push(f.name+" ("+e.message+")")}}
 save();renderAssets();addAudit("Importação","Arquivados "+ok+" arquivo(s) com nome/tamanho/data; sem conversão.","PRODUZIDO",files.map(f=>f.name).join("; ").slice(0,500));
 say(ok+" arquivo(s) importados para armazenamento local. "+(errors.length?errors.join("; "):"Sem erros."));
}
function renderAssets(){
 const box=document.getElementById("assetList");if(!box)return;
 const a=state.extraAssets||[];
 box.innerHTML=a.length?a.map((f,i)=>
 '<div class="logrow"><b>'+safe(f.name)+'</b> <small>'+Math.round(f.size/1024)+' KB · '+safe(f.format||"bin")+'</small>'+
 '<div class="actions"><button data-exp="'+i+'">EXPORTAR ORIGINAL</button><button data-del="'+i+'">RETIRAR DO CATÁLOGO</button></div></div>').join("")
 :'<p class="muted">Sem mídias adicionais arquivadas.</p>';
}
async function exportAsset(i){
 const a=state.extraAssets||[],f=a[i];if(!f)return;
 try{let b=await readBlob(f.key);if(!b)throw Error("Arquivo original não encontrado neste aparelho.");
 toDownload(b,filename(f.name),f.type)}catch(e){say(e.message)}
}
function deleteAsset(i){
 let f=state.extraAssets?.[i];if(!f)return;
 if(!confirm("Remover "+f.name+" da lista? Não altera arquivos no Drive."))return;
 state.extraAssets.splice(i,1);save();renderAssets();
 addAudit("Catálogo","Removido do catálogo local "+f.name+" (blob armazenado sem alteração).","PRODUZIDO",f.name);
}
async function exportSlot(){
 const kind=document.getElementById("expKind").value,i=Number(document.getElementById("expIndex").value);
 const meta=kind==="view"?state.views?.[i]:state.refs?.[i];
 if(!meta){say("Este slot ainda não possui arquivo importado.");return}
 try{
 let blob=await readBlob(meta.key||fileKey(kind,i));if(!blob)throw Error("Mídia indisponível no IndexedDB.");
 let type=blob.type||meta.type||"image/png";
 toDownload(blob,"AURION_"+filename(state.meta.id||"PERSONAGEM")+"_"+kind+"_"+i+"_"+filename(meta.name),type);
 }catch(e){say("Erro: "+e.message)}
}
async function contactSheet(){
 const c=document.createElement("canvas");c.width=2400;c.height=1360;
 const g=c.getContext("2d");g.fillStyle="#0c0b20";g.fillRect(0,0,c.width,c.height);
 g.fillStyle="#f3c46c";g.font="bold 37px Arial";g.fillText("AURION / "+(state.meta.character||"PERSONAGEM")+" / 360",30,50);
 const W=575,H=580;
 let n=0;
 for(let i=0;i<8;i++){
 const x=30+(i%4)*590,y=80+Math.floor(i/4)*620;
 g.fillStyle="#201735";g.fillRect(x,y,W,H);
 g.fillStyle="#f5e5ff";g.font="bold 23px Arial";g.fillText(ANGLES[i][0]+" · "+ANGLES[i][1],x+14,y+H-22);
 const info=state.views?.[i];if(!info)continue;
 try{
 const b=await readBlob(info.key||fileKey("view",i));if(!b)continue;
 const image=await createImageBitmap(b);
 const ratio=Math.min((W-18)/image.width,(H-60)/image.height);
 const sw=image.width*ratio,sh=image.height*ratio;
 g.drawImage(image,x+(W-sw)/2,y+(H-60-sh)/2,sw,sh);
 image.close();n++;
 }catch(e){ /* missing slot remains marked blank */ }
 }
 c.toBlob(b=>{if(b){toDownload(b,"AURION_360_"+filename(state.meta.id)+".png","image/png");
 addAudit("Model sheet","Prancha PNG 4x2 exportada com "+n+"/8 vistas existentes; nenhuma vista inventada.","PRODUZIDO");}
 else say("Erro ao codificar prancha PNG.");},"image/png");
}
async function convertSlot(){
 const kind=document.getElementById("expKind").value,i=Number(document.getElementById("expIndex").value);
 const type=document.getElementById("expFormat").value,ext=type==="image/jpeg"?"jpg":type.split("/")[1];
 const meta=kind==="view"?state.views?.[i]:state.refs?.[i];
 if(!meta){say("Importe primeiro uma imagem no slot selecionado.");return}
 try{
 const b=await readBlob(meta.key||fileKey(kind,i)),image=await createImageBitmap(b);
 const c=document.createElement("canvas");c.width=image.width;c.height=image.height;
 const g=c.getContext("2d");if(type==="image/jpeg"){g.fillStyle="#fff";g.fillRect(0,0,c.width,c.height)}
 g.drawImage(image,0,0);image.close();
 c.toBlob(blob=>{
 if(!blob){say("O aparelho não oferece este codificador.");return}
 if(blob.type!==type){say("Este navegador não oferece codificação "+ext.toUpperCase()+". Exportação cancelada.");return}
 toDownload(blob,"AURION_"+filename(state.meta.id)+"_"+kind+i+"."+ext,type);
 addAudit("Exportação","Imagem convertida em "+ext+" na resolução original. Cuidado com perfis ICC/EXIF, não preservados no canvas.","PRODUZIDO");
 },type,0.94);
 }catch(e){say("Conversão indisponível: "+e.message)}
}
function localEndpoint(u){
 try{
 const p=new URL(u);let h=p.hostname;
 return p.protocol==="http:" && (h==="localhost"||h==="127.0.0.1"||h.endsWith(".local")||h.endsWith(".ts.net")||/^10\.\d+\.\d+\.\d+$/.test(h)||/^192\.168\.\d+\.\d+$/.test(h)||/^172\.(1[6-9]|2\d|3[01])\.\d+\.\d+$/.test(h));
 }catch(e){return false}
}
function generatorSettings(){
 const e=document.getElementById("comfyEndpoint").value.trim().replace(/\/+$/,"");
 const wf=document.getElementById("comfyWorkflow").value.trim();
 if(!localEndpoint(e))throw Error("Use endereço HTTP privado da sua rede/Tailscale. Ex.: http://192.168.0.3:8188");
 if(!wf)throw Error("Cole um workflow API JSON real do seu ComfyUI (não um workflow visual de exportação UI).");
 let flow=JSON.parse(wf);if(!(flow.prompt||Object.keys(flow).length>0))throw Error("Workflow API vazio.");
 localStorage.setItem(ENGINE_KEY,e);localStorage.setItem(WF_KEY,wf);return {e,wf,flow};
}
function generatorPrompt(){
 const kind=document.getElementById("genKind").value,idx=Number(document.getElementById("genIndex").value);
 return kind==="view"?viewPrompt(Math.max(0,Math.min(7,idx))):(state.shots.length?shotPrompt(Math.max(0,Math.min(idx,state.shots.length-1)),false):identity());
}
function queueReal(){
 if(!(window.AurionAndroid&&AurionAndroid.queueComfy)){say("Fila real requer ponte Android. Instale o APK, conecte-se ao PC e autorize o workflow.");return}
 try{
 const {e,flow}=generatorSettings();
 const prompt=generatorPrompt();let json=JSON.stringify(flow);
 if(json.indexOf("{{POSITIVE}}")===-1){if(!confirm("O workflow NÃO possui o marcador {{POSITIVE}}. Enviar SEM alterar o prompt?"))return}
 json=json.replace(/\{\{POSITIVE\}\}/g,()=>JSON.stringify(prompt).slice(1,-1)).replace(/\{\{NEGATIVE\}\}/g,()=>JSON.stringify("sem troca de identidade, sem artefatos, sem membros extras, sem texto").slice(1,-1));
 let parsed=JSON.parse(json);
 if(!parsed.prompt){parsed={prompt:parsed}} // ComfyUI /prompt
 if(typeof parsed.prompt!=="object"||!Object.keys(parsed.prompt).length)throw Error("Campo prompt inválido.");
 let nodes=Object.values(parsed.prompt);
 if(!nodes.every(n=>n&&typeof n==="object"&&n.class_type&&n.inputs))throw Error("Workflow API não contém nós com class_type/inputs.");
 window.__aurionPendingJob={at:now(),kind:document.getElementById("genKind").value,index:Number(document.getElementById("genIndex").value),engine:e};
 AurionAndroid.queueComfy(e,JSON.stringify(parsed));
 say("Workflow enviado ao bridge. Aguardando resposta HTTP da fila ComfyUI; render NÃO confirmado.");
 }catch(err){say("Gerador não enviado: "+err.message)}
}
window.aurionComfyResult=function(raw){
 try{
 let r=JSON.parse(raw),data=JSON.parse(r.body||"{}");
 if(r.ok&&data.prompt_id){
 window.__aurionLastPrompt=data.prompt_id;document.getElementById("lastPrompt").textContent=data.prompt_id;
 addAudit("Geração - fila","Workflow aceito pela fila ComfyUI; execução/render ainda não confirmados. ID: "+data.prompt_id,"EM ANDAMENTO",data.prompt_id);
 say("ComfyUI aceitou o workflow na fila. ID: "+data.prompt_id+". Consulte Histórico e importe a imagem gerada.");
 }else{
 addAudit("Geração - erro","Falha ao enviar ComfyUI: HTTP "+(r.http||"?")+" "+(r.error||r.body||"").slice(0,250),"ERRO");
 say("ComfyUI rejeitou o job: "+(r.error||r.body||raw).slice(0,260));
 }
 }catch(e){say("Resposta do gerador inválida: "+String(raw).slice(0,350))}
};
function testEngine(){
 const base=document.getElementById("comfyEndpoint").value.trim().replace(/\/+$/,"");
 if(!localEndpoint(base)){say("Informe IP local/Tailscale válido.");return}
 localStorage.setItem(ENGINE_KEY,base);
 if(window.AurionAndroid&&AurionAndroid.testService){
 AurionAndroid.testService("AURION_COMFY_TEST",base+"/system_stats");say("Consultando ComfyUI /system_stats no PC...");
 }else say("Teste de rede disponível somente no APK Android.");
}
function checkLast(){
 const id=window.__aurionLastPrompt,base=document.getElementById("comfyEndpoint").value.trim().replace(/\/+$/,"");
 if(!id){say("Nenhum prompt_id de fila confirmado nesta sessão.");return}
 if(!localEndpoint(base)){say("Configure a rede local.");return}
 if(window.AurionAndroid?.testService){AurionAndroid.testService("AURION_COMFY_HISTORY",base+"/history/"+encodeURIComponent(id));say("Consultando histórico do job "+id+"...")}
}
window.aurionServiceResult=function(raw){
 try{
 const r=JSON.parse(raw);if(!["AURION_COMFY_TEST","AURION_COMFY_HISTORY"].includes(r.label))return;
 let inner=r.result||r.response||r.data||r;
 let code=inner.http||"?";let body=inner.body||"";
 if(r.label==="AURION_COMFY_TEST")say((inner.ok?"PC/ComfyUI respondeu ":"Falha no PC/ComfyUI ")+"HTTP "+code+".");
 else{
 let hist=JSON.parse(body||"{}"),id=window.__aurionLastPrompt;
 const job=hist[id],statusValue=job?.status?.status_str||"não encontrado";
 if(statusValue==="success"){
 addAudit("Geração - histórico","ComfyUI retornou status success para "+id+". Baixe o output no PC e importe manualmente no slot.","VALIDADO",id);
 say("ComfyUI concluiu job "+id+". Saída no PC; importe a imagem manualmente no AURION.");
 }else say("Histórico ComfyUI: "+statusValue+" (HTTP "+code+").");
 }
 }catch(e){say("Resultado de serviço recebido; confira painel do PC.")}
};
function handoff(){
 const summary="AURION <¥> HANDOFF · "+now()+"\nCliente: "+state.meta.client+
 "\nProjeto: "+state.meta.job+"\nPersonagem: "+state.meta.character+
 "\nID: "+state.meta.id+"\nRef. locais: "+Object.keys(state.refs||{}).length+
 "/5\nVistas locais: "+Object.keys(state.views||{}).length+
 "/8\nCenas: "+state.shots.length+"\nArquivos extras: "+(state.extraAssets||[]).length+
 "\nDrive: "+(state.meta.driveFolder||"não informado")+
 "\nÚltimo job ComfyUI: "+(window.__aurionLastPrompt||"não confirmado")+
 "\nRegistro: "+state.logs.length+" linhas.\nLEI: arquivos no Android não foram sincronizados com Drive automaticamente."+
 "\nPendências: validar direitos, Octane (PC), mídias originais, revisão dos resultados.";
 if(window.AurionAndroid?.shareProject){AurionAndroid.shareProject("AURION handoff - "+state.meta.id,summary);
 say("Compartilhamento do Android aberto. Escolha Drive/WhatsApp/Outro aplicativo para enviar.")}
 else{copy(summary);say("Resumo copiado.")}
}
function tri(){
 const e=document.getElementById("triDest").value;
 if(e==="local"){exportManifest();return}
 if(e==="pc"){show("tools");document.getElementById("comfyEndpoint").focus();say("Destino PC: teste rede e envie workflow ComfyUI. Octane só via PC e integração própria.");return}
 if(e==="drive"){openLink(state.meta.driveFolder||"https://drive.google.com/drive/u/0/my-drive");say("Drive aberto. Use o botão Compartilhar ou faça upload manual dos arquivos; não há sync OAuth automático.");}
}
function inject(){
 // Instala um único tab adicional sem modificar a identidade visual ou animações já existentes.
 const nav=document.getElementById("tabs");
 let btn=el("button",{"data-tab":"tools"},"⚙ Ações / Gerador");nav.appendChild(btn);
 const p=el("section",{id:"tools",class:"page"});p.innerHTML=
 '<div class="card"><span class="pill">AURION · AÇÕES REAIS · V7.3</span><h1>Central de ações</h1>'+
 '<p>Formatos suportados dependem do motor. Arquivar não significa converter. Geração efetiva somente via ComfyUI conectado ao PC e workflow válido.</p>'+
 '<h2>Projetos / backup</h2><div class="actions"><button class="primary" id="saveArchive">SALVAR NO CATÁLOGO</button><button id="expJson">EXPORTAR MANIFESTO JSON</button>'+
 '<button id="expCsv">EXPORTAR SHOTLIST CSV</button></div><label>Abrir projeto anterior</label><select id="savedProjects"></select>'+
 '<div class="actions"><button id="restoreProject">ABRIR PROJETO ARQUIVADO</button>'+
 '<label class="btn">IMPORTAR MANIFESTO JSON<input id="importManifest" type="file" accept=".json,application/json" style="display:none"></label></div></div>'+
 '<div class="card"><h2>Importação múltipla · arquivo original</h2>'+
 '<p class="muted">Guarda bytes no aparelho; GLB/OBJ/CR3/EXR/ZIP não têm prévia ou render integrado.</p>'+
 '<label class="btn">+ IMPORTAR ARQUIVOS EM LOTE<input id="importAssets" type="file" multiple style="display:none"></label>'+
 '<p class="muted" style="font-size:12px">'+available+'</p><div id="assetList"></div></div>'+
 '<div class="card"><h2>Exportação de imagens e folha 360</h2>'+
 '<div class="grid"><div><label>Origem</label><select id="expKind"><option value="ref">5 Fotos</option><option value="view">360</option></select></div>'+
 '<div><label>Slot (1 a 8)</label><select id="expIndex">'+Array.from({length:8},(_,i)=>'<option value="'+i+'">'+(i+1)+'</option>').join("")+'</select></div>'+
 '<div><label>Converter imagem para</label><select id="expFormat"><option value="image/png">PNG</option><option value="image/jpeg">JPEG</option><option value="image/webp">WEBP</option></select></div></div>'+
 '<div class="actions"><button id="expOriginal">SALVAR ARQUIVO ORIGINAL</button><button class="primary" id="convertSlot">CONVERTER IMAGEM</button><button id="sheet360">EXPORTAR PRANCHA PNG 360</button></div>'+
 '<p class="muted">Conversão por Canvas não preserva EXIF/ICC/RAW, portanto jamais altera os originais. O 360 exporta imagens existentes; não gera ângulos ausentes.</p></div>'+
 '<div class="card"><h2>Gerador real · ComfyUI no PC</h2>'+
 '<p>O APK envia um workflow API JSON para <code>POST /prompt</code> via rede local. Exige ComfyUI ativo, modelos e nós instalados no PC. Octane requer Cinema 4D/OTOY no PC e não é substituído por este botão.</p>'+
 '<label>URL ComfyUI local ou Tailscale (sem tokens no código)</label><input id="comfyEndpoint" placeholder="http://192.168.0.3:8188">'+
 '<label>Workflow API JSON real (cole o exportado do ComfyUI)</label><textarea id="comfyWorkflow" rows="7" placeholder=\'{"3":{"class_type":"KSampler","inputs":{...}},...}&#10;Adicione {{POSITIVE}} num campo de texto do nó CLIPTextEncode.\'></textarea>'+
 '<div class="grid"><div><label>Tipo</label><select id="genKind"><option value="view">Ângulo T-Pose</option><option value="shot">Cena do storyboard</option></select></div>'+
 '<div><label>Slot / cena (1-8)</label><select id="genIndex">'+Array.from({length:8},(_,i)=>'<option value="'+i+'">'+(i+1)+'</option>').join("")+'</select></div></div>'+
 '<div class="actions"><button id="testComfy">TESTAR PC</button><button id="copyGenerator">COPIAR PROMPT</button><button class="primary" id="queueComfy">ENVIAR WORKFLOW À FILA</button><button id="checkComfy">CONSULTAR RESULTADO</button></div>'+
 '<p class="muted">Último ID aceito pela fila: <code id="lastPrompt">nenhum</code>. Resultado final ainda precisa ser importado. Não é geração local no POCO.</p></div>'+
 '<div class="card"><h2>TRI · comunicação e entrega</h2><p>1. Salvar local · 2. Enviar ao PC pela rede · 3. Compartilhar ao Drive. Operações independentes, sem fingir sincronização.</p>'+
 '<label>Destino de ação</label><select id="triDest"><option value="local">01 - APK local: JSON</option><option value="pc">02 - PC: ComfyUI/Octane</option><option value="drive">03 - Google Drive: upload manual</option></select>'+
 '<div class="actions"><button class="primary" id="triGo">EXECUTAR ATALHO TRI</button><button id="shareHandoff">COMPARTILHAR HANDOFF</button><button id="folderPicker">AUTORIZAR PASTA ANDROID</button><button id="saveWorkspace">SALVAR JSON NA PASTA</button></div>'+
 '<p id="toolStatus" class="status" aria-live="polite">Ações aguardando operador.</p></div>';
 document.querySelector("main").insertBefore(p,document.getElementById("feedback"));
 const on=(id,action)=>document.getElementById(id).addEventListener("click",action);
 on("saveArchive",saveArchive);on("expJson",exportManifest);on("expCsv",exportShotlist);on("restoreProject",restoreProject);
 on("expOriginal",exportSlot);on("convertSlot",convertSlot);on("sheet360",contactSheet);
 on("testComfy",testEngine);on("queueComfy",queueReal);on("checkComfy",checkLast);
 on("copyGenerator",()=>copy(generatorPrompt()));on("triGo",tri);on("shareHandoff",handoff);
 on("folderPicker",chooseProductionFolder);on("saveWorkspace",exportToWorkspace);
 document.getElementById("importManifest").addEventListener("change",function(){importManifest(this)});
 document.getElementById("importAssets").addEventListener("change",function(){importFiles(this)});
 document.getElementById("assetList").addEventListener("click",e=>{
 const b=e.target.closest("button");if(!b)return;
 if(b.dataset.exp!==undefined)exportAsset(Number(b.dataset.exp));
 if(b.dataset.del!==undefined)deleteAsset(Number(b.dataset.del));
 });
 document.getElementById("comfyEndpoint").value=localStorage.getItem(ENGINE_KEY)||"";
 document.getElementById("comfyWorkflow").value=localStorage.getItem(WF_KEY)||"";
 const oldSave=window.saveMeta;window.saveMeta=function(){oldSave();archiveCurrent();renderProjects()};
 const oldNew=window.newProject;window.newProject=function(){archiveCurrent();oldNew();renderProjects();renderAssets()};
 state.extraAssets=state.extraAssets||[];save();renderProjects();renderAssets();
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",inject);else inject();
})();