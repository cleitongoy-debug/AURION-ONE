'use strict';
/* One operator action, separate verifiable receipts: local scan + PC sync.
   No device pairing, filesystem modification or external-account permission bypass. */
(function(){
  const byId=id=>document.getElementById(id);
  function setStatus(msg){const e=byId('quickSyncStatus');if(e)e.textContent=msg;}
  window.aurionQuickScan=function(){
    const button=byId('quickSyncButton');
    if(button)button.disabled=true;
    try{
      setStatus('INICIADO: verificações do Android foram solicitadas. Nenhum resultado remoto foi confirmado. Tentando sincronização de memória textual via USB.');
      if(typeof window.AurionAndroid==='undefined'){setStatus('BLOQUEADO: ponte Android indisponível nesta tela. Volte ao perfil titular e entre novamente; nenhuma sincronização foi confirmada.');return;}
      if(typeof native!=='function')throw Error('Ponte Android não disponível');
      native('runHourlySyncNow');
      // Use the sanitized saved loopback endpoint, not an assumed fixed port.
      // Never return or render the stored token. The native bridge retains it.
      const state=JSON.parse(native('pocoPcSyncStatus')||'{}');
      const endpoint=state.configuredEndpoint || 'http://127.0.0.1:5060';
      if(!/^http:\/\/(?:127\.0\.0\.1|localhost):506[0-9]$/.test(endpoint)){
        throw Error('Porta PC fora da faixa USB autorizada');
      }
      native('pocoPcSyncNow',endpoint,'');
    }catch(err){
      setStatus('BLOQUEADO: '+err.message+'. Os dados permanecem no POCO.');
    }finally{if(button)button.disabled=false;}
  };
  function init(){
    const original=window.aurionPocoPcSyncResult;
    window.aurionPocoPcSyncResult=function(raw){
      if(typeof original==='function')original(raw);
      try{
        const x=JSON.parse(raw);
        if(x.ok===true&&x.status==='RECIBOS_PC_E_POCO_CONFIRMADOS'){
          setStatus('SYNC COM RECIBOS: PC confirmou '+x.pcReadbackCount+' registros; POCO importou '+x.imported+' novos. Dados duplicados preservados: '+x.duplicates+'. Verificações online agendadas; Drive/Band NÃO confirmados.');
        }else{
          setStatus('SYNC NÃO CONFIRMADO: '+String(x.error||'sem recibo').slice(0,240)+'. Confirme PC ligado, USB, ADB reverse e token salvo em Conexões. Memória offline preservada.');
        }
      }catch(e){setStatus('Resposta inesperada do PC; sincronização NÃO CONFIRMADA.');}
    };
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
