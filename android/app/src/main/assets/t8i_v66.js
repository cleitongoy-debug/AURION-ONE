'use strict';
(function(){
const T8I_TYPES=['t8i_file','t8i_preset','t8i_note','t8i_conversation','t8i_error','t8i_reference','t8i_evidence'];
function el(id){return document.getElementById(id)}
function out(id,text){let n=el(id);if(n)n.textContent=text}
function add(type,title,body,meta={}){return native('memoryAdd',type,title,body,JSON.stringify(meta))}
function list(type){try{return JSON.parse(native('memoryList',type,'',500)||'[]')}catch{return[]}}
window.t8iChooseWorkspace=()=>{native('chooseWorkspace');out('t8iWorkspaceLog','Escolha a pasta raiz. O AURION pedirá permissão persistente do Android.')};
window.t8iPrepareWorkspace=()=>{out('t8iWorkspaceLog','Criando/conferindo depósitos...');native('prepareT8iWorkspace')};
window.t8iArchiveOriginals=()=>{if(!confirm('Copiar os originais selecionados para AURION_T8I/RAW? Arquivos com o mesmo nome serão preservados e não sobrescritos.'))return;out('t8iWorkspaceLog','Copiando originais...');native('archiveT8iOriginals')};
window.t8iBackupNow=()=>{out('t8iWorkspaceLog','Gravando backup T8i...');native('syncT8iWorkspace')};
window.t8iSavePreset=()=>{
 const body={exposure:Number(el('ev').value),temperature:Number(el('temp').value),contrast:Number(el('t8ct').value),saturation:Number(el('t8sat').value),profile:el('t8profile').value,recipe:el('t8iRecipe').value,time:new Date().toISOString()};
 add('t8i_preset','Canon T8i · '+body.profile,JSON.stringify(body),{source:'POCO v6.6',nonDestructive:true});
 out('t8iLog','Preset + receita salvos no cofre local.');t8iRenderVault()
};
window.t8iSaveNote=()=>{
 const type=el('t8iNoteType').value,title=el('t8iNoteTitle').value.trim()||'Registro T8i · '+new Date().toLocaleString('pt-BR'),body=el('t8iNoteBody').value.trim();
 if(!body){out('t8iWorkspaceLog','Digite o conteúdo antes de salvar.');return}
 add(type,title,body,{source:'POCO v6.6',time:new Date().toISOString()});
 el('t8iNoteTitle').value='';el('t8iNoteBody').value='';out('t8iWorkspaceLog','Registro salvo no SQLite. Use BACKUP T8i para copiar ao workspace.');t8iRenderVault()
};
window.t8iPrepareTermux=()=>{
 const cmd='pkg update && pkg install -y python git curl ffmpeg imagemagick exiftool && mkdir -p "$HOME/aurion-t8i"/{logs,backups,luts,previews,exports} && python --version && ffmpeg -version | head -n 1 && exiftool -ver';
 native('copyText','AURION T8i · dependências',cmd);
 add('t8i_evidence','Plano de dependências Termux',cmd,{automaticInstall:false,reason:'Termux exige confirmação do operador'});
 out('t8iDepsLog','Plano copiado. O Termux será aberto; confirme a instalação nele. Revelação CR3 integral permanece no nó PC/LibRaw ou Canon DPP.');
 native('openTermux')
};
window.t8iRenderVault=()=>{
 let all=[];for(const t of T8I_TYPES)all.push(...list(t));
 all.sort((a,b)=>(b.updatedAt||0)-(a.updatedAt||0));
 let count=el('t8iVaultCount');if(count)count.textContent=String(all.length);
 let box=el('t8iVaultList');if(!box)return;
 box.innerHTML=all.slice(0,120).map(x=>'<div class="memory"><small>'+esc(x.type)+' · '+new Date(x.updatedAt).toLocaleString('pt-BR')+'</small><h3>'+esc(x.title)+'</h3><div>'+esc(String(x.body||'')).slice(0,900)+'</div></div>').join('')||'<p class="muted">Nenhum registro T8i ainda.</p>'
};
window.t8iRememberSelection=input=>{
 const files=[...(input?.files||[])];for(const f of files)add('t8i_file',f.name,'Arquivo selecionado pelo WebView',{bytes:f.size,mime:f.type,modified:f.lastModified,uriPersistent:false});
 t8iRenderVault()
};
window.aurionT8iFilesResult=raw=>{try{let x=JSON.parse(raw);out('t8iLog',x.ok?(x.count+' arquivo(s) com URI persistente no cofre.'):('Falha: '+x.error));t8iRenderVault()}catch(e){out('t8iLog',e.message)}};
window.aurionT8iWorkspaceResult=raw=>{try{let x=JSON.parse(raw);out('t8iWorkspaceLog',x.ok?('Depósitos prontos: '+x.folders.join(', ')):('Falha: '+x.error));let s=el('t8iWorkspaceState');if(s)s.textContent=x.ok?'PRONTO':'ERRO';t8iRenderVault()}catch(e){out('t8iWorkspaceLog',e.message)}};
window.aurionT8iArchiveResult=raw=>{try{let x=JSON.parse(raw);out('t8iWorkspaceLog',x.ok?('RAW: '+x.copied+' copiado(s), '+x.skipped+' preservado(s).'):('Arquivamento parcial/falhou: '+(x.error||x.failed+' falha(s)')));t8iRenderVault()}catch(e){out('t8iWorkspaceLog',e.message)}};
window.aurionT8iBackupResult=raw=>{try{let x=JSON.parse(raw);out('t8iWorkspaceLog',x.ok?('Backup criado: '+x.name):('Falha no backup: '+x.error));let s=el('t8iBackupState');if(s)s.textContent=x.ok?'SALVO':'ERRO';t8iRenderVault()}catch(e){out('t8iWorkspaceLog',e.message)}};
const prevWorkspace=window.aurionWorkspaceResult;
window.aurionWorkspaceResult=uri=>{if(typeof prevWorkspace==='function')prevWorkspace(uri);out('t8iWorkspaceLog','Pasta raiz autorizada. Toque em CRIAR / CONFERIR DEPÓSITOS.');let s=el('t8iWorkspaceState');if(s)s.textContent='AUTORIZADO';add('t8i_evidence','Workspace autorizado',String(uri),{time:new Date().toISOString()})};
setTimeout(()=>{try{t8iRenderVault()}catch{}},300);
})();