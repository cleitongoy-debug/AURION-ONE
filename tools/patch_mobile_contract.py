"""AURION ONE: patch mobile HTML contract only; no services/network changes.

Usage (from repository root): python tools/patch_mobile_contract.py
Creates a timestamped backup beside the HTML before writing. Re-run is a no-op.
Does NOT provide remote access, HTTPS, CORS, or an APK.
"""
from pathlib import Path
from datetime import datetime, timezone
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'mobile' / 'aurion-one-live.html'
OLD = "headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt:text}),credentials:'omit'"
NEW = "headers:{'Content-Type':'application/json','Authorization':'Bearer '+token},body:JSON.stringify({text:text,device_id:'poco-mobile',moving:false}),credentials:'omit'"
OLD_FN = "async function sendChat(){let c=cfg(),text=$('prompt').value.trim();if(!text)return;if(!c.node)"
NEW_FN = "async function sendChat(){let c=cfg(),text=$('prompt').value.trim();if(!text)return;let token=window.prompt('Chave de acesso AURION (não será salva):');if(!token)return;if(!c.node)"

def main():
    if not TARGET.is_file():
        sys.exit('Arquivo mobile não encontrado; nada alterado.')
    original = TARGET.read_text(encoding='utf-8')
    if NEW in original and NEW_FN in original:
        print('Contrato já corrigido; nenhuma alteração.')
        return
    if original.count(OLD) != 1 or original.count(OLD_FN) != 1:
        sys.exit('Contrato diferente do auditado; nenhuma alteração. Revisar manualmente.')
    changed = original.replace(OLD_FN, NEW_FN, 1).replace(OLD, NEW, 1)
    backup = TARGET.with_name(TARGET.name + '.bak-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    shutil.copy2(TARGET, backup)
    TARGET.write_text(changed, encoding='utf-8')
    print('HTML atualizado:', TARGET)
    print('Backup para reversão:', backup)
    print('NÃO comprova conexão POCO, HTTPS, CORS, permissão remota ou APK.')

if __name__ == '__main__':
    main()
