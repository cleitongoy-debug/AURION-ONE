(()=>{
const KEY='aurion_morph_v7_session';
let s; try{s=JSON.parse(localStorage.getItem(KEY)||'null')}catch(e){}
if(!s){s={id:'POCO-'+Date.now(),started:new Date().toISOString(),events:[]};localStorage.setItem(KEY,JSON.stringify(s));}
function stamp(type,detail){s.events.push({ts:new Date().toISOString(),type,detail});localStorage.setItem(KEY,JSON.stringify(s));}
stamp('BOOT','AURION MORPH V7 aberto');
const box=document.createElement('div'); box.id='morphV7';
box.innerHTML=`<div style="position:fixed;top:0;left:0;right:0;z-index:99999;background:#090b0d;border-bottom:1px solid #a8842c;color:#e8d18a;padding:7px 10px;font:12px monospace;display:flex;gap:9px;align-items:center;overflow:auto;white-space:nowrap">
<b>MORPH V7</b><span id="morphClock"></span><span id="morphElapsed"></span>
<button id="morphWitness">DEPOIMENTO</button><button id="morphMark">PROTOCOLAR AGORA</button>
<button id="morphExport">EXPORTAR</button><button id="morphDrive">DRIVE</button><span id="morphState">MISSÃO 1 · TESTEMUNHAR</span></div>`;
document.body.appendChild(box); document.body.style.paddingTop='42px';
const start=Date.parse(s.started);
function tick(){const n=new Date(),d=Math.max(0,Date.now()-start),h=Math.floor(d/3600000),m=Math.floor(d%3600000/60000),sec=Math.floor(d%60000/1000);
document.getElementById('morphClock').textContent=n.toLocaleString();
document.getElementById('morphElapsed').textContent='SESSÃO '+String(h).padStart(2,'0')+':'+String(m).padStart(2,'0')+':'+String(sec).padStart(2,'0');}
tick();setInterval(tick,1000);
document.getElementById('morphMark').onclick=()=>{stamp('MARCO_MANUAL','Operador marcou evento');alert('Protocolado: '+new Date().toISOString());};
document.getElementById('morphDrive').onclick=()=>{stamp('DRIVE_OPEN','Destino oficial solicitado');location.href='https://drive.google.com/drive/folders/1WXibNok4F8FYkX6rifQyFdtdfSTQ3xQH?usp=drive_link';};
document.getElementById('morphExport').onclick=()=>{stamp('EXPORT_REQUEST','Exportação solicitada');if(typeof exportBackup==='function')exportBackup();else alert(JSON.stringify(s,null,2));};
document.getElementById('morphWitness').onclick=async()=>{stamp('DEPOIMENTO_OPEN','Questionário aberto');let t='';try{t=await (await fetch('QUESTIONARIO_POCO.txt')).text()}catch(e){t='Questionário indisponível: '+e}
const w=document.createElement('div');w.style='position:fixed;inset:45px 8px 8px;z-index:99998;background:#0b0d10;color:#eee;border:1px solid #a8842c;padding:12px;overflow:auto;white-space:pre-wrap;font:13px monospace';
w.textContent=t; const b=document.createElement('button');b.textContent='FECHAR';b.style='position:sticky;top:0;float:right';b.onclick=()=>w.remove();w.prepend(b);document.body.appendChild(w);};
})();