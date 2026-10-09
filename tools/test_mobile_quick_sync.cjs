'use strict';
// Simulado: prova apenas logica JavaScript; nao conecta POCO, USB nem PC.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const script=fs.readFileSync(path.join(__dirname,'../android/app/src/main/assets/mobile_quick_sync.js'),'utf8');
function runWith(endpoint,bridge=true){
  const calls=[],widgets={
    quickSyncButton:{disabled:false},
    quickSyncStatus:{textContent:''}
  };
  const sandbox={
    window:bridge?{AurionAndroid:{}}:{},
    document:{readyState:'complete',getElementById:id=>widgets[id]||null},
    native:(method,...args)=>{
      calls.push({method,args});
      if(method==='pocoPcSyncStatus')return JSON.stringify({configuredEndpoint:endpoint});
    },JSON,Error
  };
  vm.runInNewContext(script,sandbox,{filename:'mobile_quick_sync.js'});
  sandbox.window.aurionQuickScan();
  return{calls,widgets};
}
function syncCalls(output){return output.calls.filter(x=>x.method==='pocoPcSyncNow')}
let result=runWith('http://127.0.0.1:5063');
assert.equal(syncCalls(result).length,1);
assert.equal(syncCalls(result)[0].args[0],'http://127.0.0.1:5063');
assert.equal(syncCalls(result)[0].args[1],'');
assert.equal(result.widgets.quickSyncButton.disabled,false);
console.log('PASS: porta 5063 do PC preservada sem revelar token');

result=runWith('http://localhost:5069');
assert.equal(syncCalls(result)[0].args[0],'http://localhost:5069');
console.log('PASS: fallback 5069 autorizado');

result=runWith('');
assert.equal(syncCalls(result)[0].args[0],'http://127.0.0.1:5060');
console.log('PASS: primeiro uso defaults local 5060');

for(const bad of ['http://8.8.8.8:5060','https://example.com:5060','http://127.0.0.1:9999']){
 result=runWith(bad);
 assert.equal(syncCalls(result).length,0);
 assert.match(result.widgets.quickSyncStatus.textContent,/BLOQUEADO/);
}
console.log('PASS: destinos externos e porta nao permitida bloqueados');

result=runWith('http://127.0.0.1:5060',false);
assert.equal(syncCalls(result).length,0);
assert.match(result.widgets.quickSyncStatus.textContent,/BLOQUEADO/);
console.log('PASS: falta de ponte Android nunca vira sync ficticio');
