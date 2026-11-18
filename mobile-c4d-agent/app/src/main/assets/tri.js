/* AURION TRI • evidências locais, sem telemetria inventada.
 * PC=API AURION autenticada, Drive=compartilhamento explícito do operador,
 * POCO=histórico local do dispositivo. Nenhum dado privado é enviado automaticamente.
 */
(function(){
'use strict';
const $=id=>document.getElementById(id);
const key='aurion_tri_20261014_v1';
const initial={version:1,events:[],lastLive:null};
let st;
try{st=JSON.parse(localStorage.getItem(key)||'null')}catch(e){st=null}
if(!st||!Array.isArray(st.events))st=initial;
function now(){return new Date().toISOString()}
function store(){st.events=st.events.slice(-150);localStorage.setItem(key,JSON.stringify(st));draw()}
function add(action,quality,details){
 st.events.push({event_id:'poco-'+Date.now().toString(36)+'-'+st.events.length,origin:'POCO',at_utc:now(),action,quality,details:String(details).slice(0,1500)});
 store();
}
function safeData(x){return x&&typeof x==='object'?x:{}}
function draw(){
 const panel=$('triHistory');if(!panel)return;
 $('triCounter').textContent=st.events.length+' eventos locais';
 $('triLast').textContent=st.lastLive?('Último PC comprovado: '+st.lastLive):'PC ainda não confirmado nesta instalação';
 panel.textContent=st.events.length?st.events.slice(-12).reverse().map(e=>e.at_utc+'  ['+e.quality+'] '+e.action+'\n'+e.details).join('\n\n'):'Sem telemetria atual. O histórico abaixo é documental, não uma conexão comprovada.';
}
window.triPc=async function(){
 $('triResult').textContent='Testando AURION via conexão autenticada…';
 const x=safeData(await api('aurion','/api/status','GET'));
 if(x.aurion==='online'){
   st.lastLive=now();
   add('status_PC','CONFIRMADO','API AURION respondeu /api/status. Ollama: '+(x.ollama||'não informado')+'.');
   $('triResult').textContent='PC confirmado por API nesta sessão. Ollama: '+(x.ollama||'desconhecido')+'. Conexão com Drive é uma etapa separada.';
 }else {
   add('status_PC','FALHOU',x.error||x.detail||'Resposta sem aurion=online');
   $('triResult').textContent='PC NÃO confirmado: '+String(x.error||x.detail||'Resposta sem indicador online')+'. Verifique Tailscale, endereço/porta e token.';
 }
};
window.triScan=async function(){
 if(!confirm('Executar um novo scan somente leitura no PC via API AURION autenticada? O PC precisa estar ligado e a conexão liberada.'))return;
 $('triResult').textContent='Aguardando resultado do scan do PC (até 35 s)…';
 const x=safeData(await api('aurion','/api/scan','POST',{}));
 if(x.scanned_at){
  add('scan_PC','CONFIRMADO','Carimbo devolvido pelo PC: '+x.scanned_at+'. Inventário recebido: '+Object.keys(x).length+' campos. Não comprova cobertura de todos os discos.');
  $('triResult').textContent='Scan concluído conforme carimbo do serviço: '+x.scanned_at+'. Atenção: confira cobertura e erros, não confunda resposta com índice completo.';
 }else{
  add('scan_PC','FALHOU',x.error||x.detail||'Sem campo scanned_at verificável');
  $('triResult').textContent='Não foi possível comprovar novo scan: '+String(x.error||x.detail||'sem scanned_at');
 }
};
window.triMark=()=>{
 const body=String($('triManual').value||'').trim();
 if(body.length<5)return alert('Descreva uma evidência verificável.');
 add('evidência_manual','RELATO_NÃO_VERIFICADO',body);
 $('triManual').value='';
};
window.triExport=()=>{
 const capsule={
  schema:'AURION_TRI_CAPSULE_v1',
  exported_at_utc:now(),
  source:'POCO - relato local',
  stages:{PC:st.lastLive?'status confirmado em '+st.lastLive:'não confirmado nesta instalação',Drive:'pendente de seleção no compartilhamento Android',POCO:'log local'},
  historical_reference:[
   {title:'FIO_MESTRE_DA_TEIA_TAILSCALE_20261011',state:'DOCUMENTAL',summary:'TRI-fase PC->Drive->POCO via Tailscale; conexões em tempo real não inferidas.'},
   {title:'AURION_COLETA_INDEX_MASTER',state:'FALHA_HISTORICA',summary:'Índice histórico com 0 arquivos catalogados e estado com 1013246 erros (conforme diário em Drive, 13/10).'}
  ],
  events:st.events
 };
 const data=JSON.stringify(capsule,null,2);
 $('triResult').textContent='Cápsula produzida; escolha Google Drive no compartilhamento para registrar na pasta autorizada. Não haverá upload sem ação sua.';
 if(typeof Aurion!=='undefined'&&Aurion.shareText)Aurion.shareText('AURION_TRI_'+new Date().toISOString().slice(0,10)+'.json',data);
 else $('triResult').textContent=data;
};
window.triImport=()=>{
 const raw=$('triPaste').value.trim();if(raw.length>200000)return alert('Arquivo grande demais.');
 try{
  const data=JSON.parse(raw);
  if(data.schema!=='AURION_TRI_CAPSULE_v1'||!Array.isArray(data.events))throw Error('Cápsula incompatível');
  const incoming=data.events.filter(e=>e&&typeof e==='object'&&typeof e.action==='string'&&typeof e.quality==='string').slice(-150);
  const seen=new Set(st.events.map(e=>e.event_id));
  let count=0;
  incoming.forEach(e=>{
   if(typeof e.event_id!=='string'||seen.has(e.event_id))return;
   st.events.push({event_id:e.event_id.slice(0,100),origin:'IMPORTAÇÃO',at_utc:String(e.at_utc||'').slice(0,35),action:e.action.slice(0,70),quality:'IMPORTADO_'+e.quality.slice(0,45),details:String(e.details||'').slice(0,1500)});
   seen.add(e.event_id);count++;
  });
  add('importação_TRI','IMPORTADO',count+' evidências adicionadas; a importação não prova eventos relatados.');
  $('triPaste').value='';$('triResult').textContent=count+' eventos importados. Classificados como IMPORTADOS, não confirmados.';
 }catch(e){$('triResult').textContent='Arquivo inválido: '+e.message}
};
window.triClear=()=>{
 if(confirm('Limpar somente os eventos locais da TRI? Isto não apaga documentos do Drive.')){st.events=[];st.lastLive=null;store()}
};
draw();
})();