'use strict';
// Verificacao SINTETICA de Biblioteca e Portfólio; sem telefone, Google, PC ou upload.
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const path=require('node:path');
const assets=path.join(__dirname,'../android/app/src/main/assets');
const script=fs.readFileSync(path.join(assets,'archive_gallery.js'),'utf8');
const html=fs.readFileSync(path.join(assets,'index.html'),'utf8');
let checked=0;
const disk=new Map(),dom=new Map(),listeners={};
const dummy=id=>({
  id, value:'',textContent:'',innerHTML:'',options:[],dataset:{},isConnected:true,
  querySelectorAll:()=>[],addEventListener:()=>{},scrollIntoView:()=>{},click:()=>{},
});
function el(id){if(!dom.has(id))dom.set(id,dummy(id));return dom.get(id)}
const window={go:()=>{},addEventListener:()=>{},AurionMemoryEngine:{addSource:()=>({ok:true})}};
const localStorage={
  getItem:k=>disk.has(k)?disk.get(k):null,
  setItem:(k,v)=>disk.set(k,String(v))
};
const document={
  readyState:'loading',getElementById:el,querySelectorAll:()=>[],
  addEventListener:(name,fn)=>{listeners[name]=fn},
  createElement:()=>({alt:'',loading:'',src:''})
};
const sandbox={window,document,localStorage,AURION_ID:'anark',Date,Math,Set,JSON,
  String,Array,Object,RegExp,Number,Map,URL,Promise,navigator:{onLine:false},
  getMemories:()=>[],dedMerged:()=>[],setTimeout:()=>{},console};
vm.runInNewContext(script,sandbox,{filename:'archive_gallery.js'});
assert.equal(window.AurionVisualArchive.books.length,10);checked++;
assert.deepEqual(Array.from(window.AurionVisualArchive.books.map(x=>x.name)),[
  'CONHECIMENTO','VIVÊNCIA','ERROS','PROGRAMAS','ASSINATURAS',
  'DEPOIMENTOS','HISTÓRICO','AGENTES','CLIENTES','ESTUDOS']);checked++;
assert.equal(window.AurionVisualArchive.services.length,7);checked++;
for(const id of ['library','libraryBookGrid','galleryCoverInput','librarySourceTitle',
  'portfolioVisualGrid','serviceReportLearning','libraryServiceSelect']){
  assert.match(html,new RegExp('id="'+id+'"'),'Falta '+id);checked++;
}
assert.match(html,/archive_gallery\.css/);checked++;
assert.match(html,/archive_gallery\.js/);checked++;
sandbox.AURION_ID='anark';
el('libraryBookSelect').value='10';
el('librarySourceTitle').value='3D Start';
el('librarySourceRef').value='curso:imagem:2026';
el('librarySourceObservation').value='58% observados no print, sem horas medidas';
window.gallerySaveBookRef();checked++;
assert.equal(window.AurionVisualArchive.localState().books.length,1);checked++;
el('librarySourceTitle').value='3D Start';
el('librarySourceRef').value='curso:imagem:2026';
window.gallerySaveBookRef();checked++;
assert.equal(window.AurionVisualArchive.localState().books.length,1,'ID repetido duplicado');
el('librarySourceTitle').value='Outra fonte';
el('librarySourceRef').value='token=SEGREDO';
window.gallerySaveBookRef();checked++;
assert.equal(window.AurionVisualArchive.localState().books.length,1,'Segredo registrado em fonte');
el('libraryServiceSelect').value='3D & VFX';
el('serviceReportTitle').value='Exemplo de serviço';
el('serviceReportRef').value='prova:teste-sintetico';
el('serviceReportLearning').value='Aprendizado com material autorizado';
window.gallerySaveService();checked++;
assert.equal(window.AurionVisualArchive.localState().reports.length,1);checked++;
el('serviceReportTitle').value='Exemplo de serviço';
el('serviceReportRef').value='prova:teste-sintetico';
window.gallerySaveService();checked++;
assert.equal(window.AurionVisualArchive.localState().reports.length,1);checked++;
sandbox.AURION_ID='daia';
assert.equal(window.AurionVisualArchive.localState().books.length,0,'Perfil diferente enxerga dados anark');checked++;
assert.equal(window.AurionVisualArchive.localState().reports.length,0,'Perfil diferente enxerga relatos anark');checked++;
assert.match(script,/indexedDB\.open\('aurion_local_covers_v1'/);checked++;
assert.match(script,/image\/jpeg/);checked++;
assert.match(html,/CAPAS: escolhidas da galeria/);checked++;
console.log('PASS: '+checked+' checagens sinteticas de biblioteca, perfis, cards, dados, seguranca e acervo. Sem teste WebView/POCO.');
