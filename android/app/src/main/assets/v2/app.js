const tabs=[['home','INÍCIO'],['studio','FOTO'],['t8i','T8i / RAW'],['memory','MEMÓRIA'],['accounts','CONTAS'],['lab','LAB'],['settings','CONFIG']];
nav.innerHTML=tabs.map((x,i)=>'<button class="tab '+(i===0?'active':'')+'" onclick="show(\''+x[0]+'\',this)">'+x[1]+'</button>').join('');
function show(id,b){document.querySelectorAll('.pane').forEach(x=>x.classList.remove('active'));document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));document.getElementById(id).classList.add('active');b.classList.add('active');if(id==='memory')memLoad();if(id==='accounts')accLoad()}
function parse(s){try{return JSON.parse(s)}catch{return {raw:s}}}
function diagLoad(){let d=parse(AurionV2.diagnostics());diag.textContent=JSON.stringify(d,null,2);workspace.textContent=d.workspace||'não escolhida'}
function convert(){convertLog.textContent='Selecione a imagem...';AurionV2.convertImage(fmt.value,+quality.value,+bright.value,+contrast.value,+sat.value,+temp.value,+tint.value)}
window.aurionConvertResult=s=>{convertLog.textContent=JSON.stringify(parse(s),null,2)}
window.aurionRawResult=s=>{rawLog.textContent=JSON.stringify(parse(s),null,2)}
window.aurionWorkspaceResult=s=>{workspace.textContent=parse(s).workspace||s;diagLoad()}
function memSave(){let id=AurionV2.saveMemory(memTitle.value,memBody.value,memTags.value);memBody.value='';memLoad()}
function memLoad(){let d=parse(AurionV2.searchMemory(memQ.value||''));memList.textContent=(Array.isArray(d)?d:[]).map(x=>'#'+x.id+' · '+x.ts+'\n'+(x.title||'')+'\n'+(x.body||'')+'\n['+(x.tags||'')+']').join('\n\n')}
function saveSecret(name,id){AurionV2.saveSecret(name,document.getElementById(id).value);document.getElementById(id).value='';accLoad()}
function accLoad(){accLog.textContent=JSON.stringify({github:AurionV2.hasSecret('github_token'),huggingface:AurionV2.hasSecret('hf_token'),pc:AurionV2.hasSecret('pc_token')},null,2)}
function savePcToken(){AurionV2.saveSecret('pc_token',pcToken.value);pcToken.value=''}
function testPc(){pcLog.textContent='testando...';AurionV2.testPc(pcUrl.value,pcToken.value)}
window.aurionPcResult=s=>{pcLog.textContent=JSON.stringify(parse(s),null,2)}
function labSave(){AurionV2.saveMemory('LAB · '+la.value+' + '+lb.value,lh.value,'lab,mix,experimento');lh.value='';alert('Experimento salvo na memória local.')}
diagLoad();