"""Tests for Evolution Core read-only tri-phase. No real network calls."""
import json
import pathlib
import sys
import unittest
import urllib.error

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from aurion_trifase_v1 import probe,snapshot,tailscale_probe,adb_probe

class Response:
    status=200
    def __init__(self,data):self.data=data
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def read(self,limit):return json.dumps(self.data).encode()

def opener(data):
    def fn(req,timeout):return Response(data)
    return fn

class Proc:
    returncode=0
    def __init__(self,out):self.stdout=out

class TriFaseTest(unittest.TestCase):
    def test_evolution_identity(self):
        self.assertEqual(probe('http://127.0.0.1:5058/api/one/boot','evolution',opener=opener({'ok':True,'build':'2026.09.21-CENTRAL-IMAGEM-AGENTE-14'}))['status'],'ONLINE')
    def test_wrong_service_no_green(self):
        self.assertEqual(probe('http://127.0.0.1:5058/api/one/boot','evolution',opener=opener({'ok':True,'build':'fake'}))['status'],'UNVERIFIED')
    def test_openwebui_auth_required(self):
        def deny(req,timeout):raise urllib.error.HTTPError(req.full_url,401,'unauthorized',{},None)
        self.assertEqual(probe('http://127.0.0.1:8080/api/models','webui',opener=deny)['status'],'AUTH_REQUIRED')
    def test_url_allowlist(self):
        self.assertEqual(probe('https://example.com/x','ollama')['status'],'BLOCKED')
    def test_comfyui(self):
        self.assertEqual(probe('http://127.0.0.1:8188/system_stats','comfyui',opener=opener({'system':{}}))['status'],'ONLINE')
    def test_ollama(self):
        self.assertEqual(probe('http://127.0.0.1:11434/api/tags','ollama',opener=opener({'models':[]}))['status'],'ONLINE')
    def test_tailscale_omits_ip_and_id(self):
        def run(argv,**kw):return Proc(json.dumps({'BackendState':'Running','Self':{'TailscaleIPs':['100.9.9.9']},'Peer':{'privateDevice':{}}}))
        s=json.dumps(tailscale_probe(runner=run))
        self.assertIn('CONNECTED',s);self.assertNotIn('privateDevice',s);self.assertNotIn('100.9.9.9',s)
    def test_adb_omits_device_serial(self):
        def run(argv,**kw):return Proc('List of devices attached\\nSERIAL789\\tdevice\\n')
        s=json.dumps(adb_probe(runner=run))
        self.assertNotIn('SERIAL789',s)
    def test_never_exposes_api_key(self):
        def fail(argv,**kw):raise FileNotFoundError()
        s=json.dumps(snapshot(opener=opener({'models':[]}),runner=fail,env={'OPENAI_API_KEY':'DELIBERATELY_NOT_REAL_KEY'}))
        self.assertNotIn('DELIBERATELY_NOT_REAL_KEY',s)
        self.assertIn('NOT_TESTED',s)
    def test_no_android_is_not_poco(self):
        def run(argv,**kw):return Proc('List of devices attached\\n')
        self.assertFalse(adb_probe(runner=run)['authorized'])
    def test_core_routes_and_ui_present(self):
        core=(ROOT/'AURION_ONE.py').read_text(encoding='utf-8')
        self.assertIn('@app.get("/api/one/trifase")',core)
        self.assertIn('id="trifaseStatus"',core)
        self.assertIn('function updateTrifase()',core)

if __name__=='__main__': unittest.main()
