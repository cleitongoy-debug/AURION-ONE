"""Stage-only surgical patch. No application startup, no disk scanning, no mutation of live source."""
from __future__ import annotations
import argparse
import ast
from pathlib import Path
import re

MARK = 'AURION_OPS_5058_INTEGRADO_V1'


def exactly(s, before, after):
    count = s.count(before)
    if count != 1:
        raise ValueError(f'Expected 1 anchor, found {count}: {before[:75]}')
    return s.replace(before, after, 1)


def patch(source):
    if MARK in source:
        return source, 'ALREADY_PATCHED'
    if 'BUILD="2026.09.21-CENTRAL-IMAGEM-AGENTE-14"' not in source:
        raise ValueError('Wrong Evolution build; refusing to patch')
    # Existing UI bug: document.getElementById("library") selected legacy section.
    source = exactly(source,
        '<button onclick="tab(\'library\',this)">SKILLS & BIBLIOTECA</button>',
        '<button onclick="tab(\'library-traces\',this)">SKILLS & BIBLIOTECA</button>')
    source = exactly(source,
        '<section id="library" class="tab"><div class="card"><h3>SKILLS, WORKFLOWS E BIBLIOTECA</h3>',
        '<section id="library-traces" class="tab"><div class="card"><h3>SKILLS, WORKFLOWS E BIBLIOTECA</h3>')
    source = exactly(source,
        '<section id="spaces" class="tab"><div class="card"><h3>ESPACOS (adicionar itens; persistido)</h3><div id="spaces"></div></div></section>',
        '<section id="spaces" class="tab"><div class="card"><h3>ESPACOS (adicionar itens; persistido)</h3><div id="spaces-items"></div></div></section>')
    source = exactly(source,
        "const el=document.getElementById('spaces'); if(!STATE) return;",
        "const el=document.getElementById('spaces-items'); if(!STATE) return;")
    source = exactly(source,
        '@app.get("/api/one/health")',
        'from aurion_ops_integrated import register_ops\nregister_ops(app, ROOT, BUILD)\n\n@app.get("/api/one/health")')
    source = exactly(source,
        '<div class="title">AURION ONE</div>',
        '<div class="title">AURION ONE <span id="opsClock" style="font:700 13px Consolas;color:#9cecff;margin-left:12px">LEME/SP --:--:--</span></div>')
    source = exactly(source,
        '<section id="home" class="tab active"><div class="hero">',
        '''<section id="home" class="tab active"><div class="card" style="border:1px solid #7752b2;background:linear-gradient(100deg,#1b1732,#162b3b);margin-bottom:10px"><b style="color:#ceaaff">◈ AURION · MENTE VIVA · 5058</b><span id="opsMini" style="float:right;color:#a2eaff;font:12px Consolas">Consultando...</span><p>COMANDOS AGENTE: /biblioteca · /diagnostico. Outros comandos documentados no protocolo. 54% CNH: informado pelo operador, não lido da plataforma.</p><div id="opsDetail" style="white-space:pre-wrap;font:12px Consolas;color:#b3d4df"></div><button onclick="opsUpdate()">ATUALIZAR STATUS REAL</button><button onclick="tab('library',this);libraryLoad()">VER BIBLIOTECA</button><button onclick="tab('sessions',this);studyLoad()">ESTUDOS</button><button onclick="tab('conn',this);updateTrifase()">TRI-FASE</button></div><div class="hero">''')
    source = exactly(source,
        'async function scanNow(){',
        '''// ''' + MARK + ''' — status read-only, no secrets or simulated heartbeat.
function opsClockTick(){const el=document.getElementById('opsClock');if(el){el.textContent='LEME/SP '+new Intl.DateTimeFormat('pt-BR',{timeZone:'America/Sao_Paulo',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}).format(new Date())}}
setInterval(opsClockTick,1000);opsClockTick();
async function opsUpdate(){
 const out=document.getElementById('opsDetail'),mini=document.getElementById('opsMini');if(!out)return;
 try{
 const [rs,rt]=await Promise.all([fetch('/api/one/operacional',{cache:'no-store'}),fetch('/api/one/study/sessions',{cache:'no-store'})]);
 const d=rs.ok?await rs.json():null, t=rt.ok?await rt.json():null;
 if(!d||!d.ok)throw Error('Sem endpoint operacional');
 const l=d.library||{},sns=d.sensors||{},sessions=Array.isArray(t?.sessions)?t.sessions:[];
 const finished=sessions.filter(x=>x.finished),secs=finished.reduce((n,x)=>n+Math.max(0,Number(x.seconds)||0),0);
 mini.textContent='RAM '+(sns.ram_percent==null?'—':sns.ram_percent+'%')+' | CAT '+(l.cataloged??'—')+' | SESSÕES '+finished.length;
 out.textContent='CATÁLOGO '+l.status+' / '+(l.checked??'—')+' vistos / '+(l.crossings??'—')+' cruzamentos'+(l.limited?' (LIMITE)':'')+'\\nESTUDOS '+finished.length+' sessões finalizadas · '+(secs/3600).toFixed(2)+'h MEDIDAS · '+(sessions.some(x=>!x.finished)?'SESSÃO ABERTA':'SEM SESSÃO ABERTA')+'\\nPORTAS '+Object.entries(sns.ports||{}).map(([k,v])=>k+':'+v).join('  ')+'\\nTAILSCALE '+(sns.tailscale?.status||'—')+' · ANDROID '+(sns.android?.status||'—')+' · MI BAND PENDENTE';
 }catch(e){mini.textContent='TELEMETRIA INDISPONÍVEL';out.textContent=String(e.message||e)}
}
setTimeout(opsUpdate,1200);setInterval(()=>{if(document.getElementById('home')?.classList.contains('active'))opsUpdate()},60000);
async function scanNow(){''')
    # Guard against ambiguous selectors and syntax errors before staging.
    ids = re.findall(r'\bid="([^"]+)"', source.split('HTML = r"""',1)[1].split('"""',1)[0])
    duplicates = sorted({key for key in ids if ids.count(key)>1})
    if duplicates:
        raise ValueError('Duplicate HTML IDs remain: '+str(duplicates))
    ast.parse(source)
    return source, 'PATCHED_STAGED'


def main():
    pa=argparse.ArgumentParser()
    pa.add_argument('--source',required=True)
    pa.add_argument('--output',required=True)
    args=pa.parse_args()
    p=Path(args.source)
    src=p.read_text(encoding='utf-8-sig')
    dst,state=patch(src)
    target=Path(args.output)
    target.write_text(dst,encoding='utf-8')
    print(state+' '+str(len(dst))+' bytes; live source unchanged')

if __name__=='__main__':main()