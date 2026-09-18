"""AURION ONE: one-time idempotent upgrade for the existing home-node portal.
Run on the Windows PC from the repository; never stores or prints credentials.
"""
from pathlib import Path
import ast
import sys

root = Path(__file__).resolve().parents[1]
app = root / 'aurion_remote' / 'app.py'
source = app.read_text(encoding='utf-8')
if 'async def run_inventory_scan(' in source:
    print('[AURION] Scan panel already installed.')
    sys.exit(0)

anchor = '@app.get("/api/status", dependencies=[Depends(require_token)])'
assert source.count(anchor) == 1, 'Unexpected app.py version: no changes made'
endpoint = '''@app.post("/api/scan", dependencies=[Depends(require_token)])
async def run_inventory_scan() -> dict:
    """Run only the fixed local inventory script; never accept shell input."""
    import asyncio
    import sys
    script = Path(__file__).resolve().parents[1] / "scripts" / "scan_system.py"
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, str(script),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=35)
        if proc.returncode != 0:
            raise HTTPException(status_code=503, detail="Falha no scan: " + stderr.decode(errors="replace")[-300:])
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        raise HTTPException(status_code=504, detail="Scan excedeu 35 segundos")
    except OSError as exc:
        raise HTTPException(status_code=503, detail="Scan indisponível: " + type(exc).__name__) from exc
    path = Path(__file__).resolve().parents[1] / "data" / "inventory.json"
    return json.loads(path.read_text(encoding="utf-8"))


'''
source = source.replace(anchor, endpoint + anchor, 1)
old = '<div class=\'card\'><button onclick=\'loadInventory()\'>Atualizar inventário</button></div>'
new = '<div class=\'card\'><button onclick=\'runScan()\'>Iniciar scan do PC</button><button onclick=\'loadInventory()\'>Ver inventário salvo</button><pre id=\'scanStatus\' aria-live=\'polite\'></pre></div>'
assert source.count(old) == 1, 'Portal HTML changed: no changes made'
source = source.replace(old, new, 1)
anchor_js = 'async function loadInventory(){'
assert source.count(anchor_js) == 1, 'Portal JavaScript changed: no changes made'
js = '''async function runScan(){
scanStatus.textContent='Escaneando PC...';
try {const r=await fetch('/api/scan',{method:'POST',headers:{'Authorization':'Bearer '+savedToken()}});
const data=await r.json();if(!r.ok)throw Error(data.detail||'Erro HTTP '+r.status);
inventory.textContent=JSON.stringify(data,null,2);scanStatus.textContent='Scan concluído: '+data.scanned_at;
}catch(e){scanStatus.textContent='Falha no scan: '+e.message;}
}
'''
source = source.replace(anchor_js, js + anchor_js, 1)
ast.parse(source)
app.write_text(source, encoding='utf-8')
print('[AURION] Scan panel installed. Restart the home-node server to activate.')
