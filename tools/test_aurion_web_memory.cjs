'use strict';
// TESTE SINTETICO: localStorage simulado. Nenhum Drive/PC/POCO real e acessado.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const script=fs.readFileSync(path.join(__dirname,'../android/app/src/main/assets/aurion_memory_engine.js'),'utf8');
const disk=new Map();
function boot(){
  const localStorage={
    getItem(key){return disk.has(key)?disk.get(key):null},
    setItem(key,value){disk.set(key,String(value))},
    removeItem(key){disk.delete(key)}
  };
  const sandbox={window:{},localStorage,Date,Math,Set,JSON,String,Array,Object,RegExp};
  vm.runInNewContext(script,sandbox,{filename:'aurion_memory_engine.js'});
  return sandbox.window.AurionMemoryEngine;
}
const memory=boot();
assert.equal(memory.context('astronomia'),'','Nao deve inventar contexto de outra pergunta');
assert.equal(memory.context(''),'','Pergunta vazia nao deve retornar toda a memoria');
assert.equal(memory.integrity().sourceCount,0);
assert.equal(memory.syncStatus().connected,false,'Offline nao equivale a login');
const one=memory.addSource('codigo','Memoria ONE','Backup SQLite no Android deve guardar registros e origem','repo:aurion/one','CODIGO_LIDO');
assert.equal(one.ok,true);
assert.equal(memory.addSource('codigo','Memoria ONE','Backup SQLite no Android deve guardar registros e origem','repo:aurion/one','CODIGO_LIDO').duplicate,true);
assert.equal(memory.addSource('doc','segredo','token=NAO_EXPORTAR','origem','RELATO_HISTORICO').ok,false);
assert.equal(memory.study().indexed,1);
assert.equal(memory.study().indexed,0,'Reindexacao sem mudancas e idempotente');
assert.equal(memory.context('observatorio sideral'),'');
assert.match(memory.context('Backup Android'),/Memoria ONE/);
assert.match(memory.context('Backup Android'),/CODIGO_LIDO/);
const other=memory.addSource('relato','Memoria ONE','Backup antigo apresentou travamento de perfil','relato:historico');
assert.equal(other.ok,true);
assert.equal(memory.study().conflicts,1,'Conflitos com mesma referencia devem ficar visiveis');
assert.equal(memory.integrity().conflicts,1);
const queued=memory.queueSync(one.id,'ATUALIZACOES#DIA');
assert.equal(queued.status,'PENDENTE');
assert.equal(memory.syncStatus().pending,1);
assert.equal(memory.queueSync(one.id,'ATUALIZACOES#DIA').duplicate,true);
assert.equal(memory.queueSync(one.id,'ROOT').ok,false,'Nao enfileirar escrita na raiz');
assert.equal(memory.acknowledgeSync(queued.id,{}).ok,false,'Nao afirmar sync sem readback');
assert.equal(memory.syncStatus().confirmed,0);
const restored=boot();
assert.equal(restored.syncStatus().pending,1,'Fila deve sobreviver a reinicializacao');
assert.equal(restored.integrity().memoryCount,2);
assert.equal(restored.acknowledgeSync(queued.id,{verifiedBy:'drive_readback',fileId:'file-test',verifiedAt:'2026-10-09T12:00:00Z'}).status,'CONFIRMADO');
assert.equal(restored.syncStatus().confirmed,1);
assert.equal(restored.syncStatus().pending,0);
const legacy=JSON.parse(disk.get('aurionMemoryEngineV1'));
legacy.sources.push({id:'src_legacy',kind:'historico',title:'antigo',body:'senha:nao_vazar',ref:'local',hash:'legacy',status:'studied'});
disk.set('aurionMemoryEngineV1',JSON.stringify(legacy));
assert.doesNotMatch(restored.export(),/nao_vazar/,'Exportacao deve filtrar tokens de legado');
assert.equal(restored.integrity().sourceCount,3);
console.log('PASS: 18 verificacoes offline/memoria/sync simulados; nenhum login, escrita Drive ou teste fisico');
