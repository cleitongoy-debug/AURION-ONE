'use strict';
// All legacy WebView keys remain in place for ANARK. New profiles receive distinct keys.
const AURION_PROFILE = JSON.parse(AurionProfiles.status());
const AURION_ID = AURION_PROFILE.active;
const AURION_TABS = new Set(AURION_PROFILE.people.find(p=>p.id===AURION_ID)?.tabs.split(',')||[]);
const AURION_ALLOWED = id => id==='profiles'||AURION_ID==='anark'||AURION_TABS.has(id);
(function(){
 const get=Storage.prototype.getItem,set=Storage.prototype.setItem,remove=Storage.prototype.removeItem;
 const key=k=>AURION_ID==='anark'?String(k):'aurionProfile:'+AURION_ID+':'+String(k);
 Storage.prototype.getItem=function(k){return get.call(this,key(k))};
 Storage.prototype.setItem=function(k,v){return set.call(this,key(k),v)};
 Storage.prototype.removeItem=function(k){return remove.call(this,key(k))};
})();
function profileRender(){
 document.querySelectorAll('[data-page]').forEach(x=>{x.hidden=!AURION_ALLOWED(x.dataset.page)});
 document.querySelectorAll('section.page').forEach(x=>{if(!AURION_ALLOWED(x.id))x.classList.remove('active')});
 const h=document.getElementById('profileIdentity');if(h)h.textContent=AURION_ID.toUpperCase();
 const owner=document.getElementById('profileOwner');if(owner)owner.hidden=AURION_ID!=='anark';
 if(AURION_ID!=='anark'){
   let guide=document.getElementById('guideOrb');if(guide)guide.hidden=true;
   // Historical ANARK material is not evidence about the current person.
   for(let id of ['portfolioDetected','archiveList','historyMilestones']){let e=document.getElementById(id);if(e)e.textContent='Histórico privado do ANARK não atribuído a este perfil.'}
 }
}
function profileLogout(){AurionProfiles.logout()}
function profileSave(id){
 let box=document.getElementById('profile_'+id),pin=document.getElementById('profilePin_'+id).value;
 let tabs=[...box.querySelectorAll('input:checked')].map(x=>x.value).join(',');
 let exists=AURION_PROFILE.people.find(p=>p.id===id)?.enabled;
 let result=JSON.parse(exists&& !pin?AurionProfiles.grant(id,tabs):AurionProfiles.provision(id,pin,tabs));
 if(result.ok){AURION_PROFILE.people=result.people;}
 document.getElementById('profileLog').textContent=result.ok?'Permissões locais de '+id+' salvas.':'Falha: '+result.error;
 document.getElementById('profilePin_'+id).value='';
}
function profileOwnerSetup(){
 let root=document.getElementById('profileOwner');if(!root||AURION_ID!=='anark')return;
 let ids=['ds','davi','spectra'],labels={ds:'DS · Daiane',davi:'Davi',spectra:'SPECTRA · Brenda'};
 let all='home,project,capture,photo,colorlab,fxlab,video,timeline,motion,audio,convert,t8i,agent,memory,lab,resources,imagegen,comfy,band,portfolio,delivery,dedication,certificates'.split(',');
 root.innerHTML=ids.map(id=>{let p=AURION_PROFILE.people.find(x=>x.id===id),tabs=new Set((p?.tabs||'').split(','));return '<div class="card"><h2>'+labels[id]+'</h2><p>Abas liberadas neste aparelho</p><div id="profile_'+id+'" class="profileGrid">'+all.map(tab=>'<label><input type="checkbox" value="'+tab+'" '+(tabs.has(tab)?'checked':'')+'> '+tab+'</label>').join('')+'</div><input type="password" id="profilePin_'+id+'" placeholder="Código individual (8+ caracteres ao criar)"><button onclick="profileSave(\''+id+'\')">SALVAR '+id.toUpperCase()+'</button></div>'}).join('')+'<p id="profileLog" role="status"></p>';
}
document.addEventListener('DOMContentLoaded',()=>{profileRender();profileOwnerSetup()});
