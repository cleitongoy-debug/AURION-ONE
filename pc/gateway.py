from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
import json,urllib.request,urllib.error
HOST='0.0.0.0';PORT=5057
def req(url,method='GET',body=None):
    data=None if body is None else json.dumps(body).encode()
    r=urllib.request.Request(url,data=data,method=method,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(r,timeout=120) as x:return x.status,x.read(),x.headers.get('Content-Type','application/json')
class H(BaseHTTPRequestHandler):
    def sendj(self,code,obj):
        b=json.dumps(obj,ensure_ascii=False).encode();self.send_response(code);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Access-Control-Allow-Origin','*');self.end_headers();self.wfile.write(b)
    def do_GET(self):
        try:
            if self.path in ('/','/health'):return self.sendj(200,{'ok':True,'service':'AURION PC GATEWAY','version':'1.0','ollama':'http://127.0.0.1:11434','comfy':'http://127.0.0.1:8188'})
            if self.path=='/api/models':
                s,b,c=req('http://127.0.0.1:11434/api/tags');self.send_response(s);self.send_header('Content-Type',c);self.end_headers();return self.wfile.write(b)
            if self.path=='/api/status':
                out={}
                for k,u in {'ollama':'http://127.0.0.1:11434/api/tags','comfy':'http://127.0.0.1:8188/system_stats','aurion':'http://127.0.0.1:5000','openwebui':'http://127.0.0.1:8080'}.items():
                    try:s,_,_=req(u);out[k]={'ok':True,'http':s}
                    except Exception as e:out[k]={'ok':False,'error':str(e)}
                return self.sendj(200,out)
            return self.sendj(404,{'ok':False,'error':'route'})
        except Exception as e:return self.sendj(502,{'ok':False,'error':str(e)})
    def do_POST(self):
        try:
            n=int(self.headers.get('Content-Length','0'));body=json.loads(self.rfile.read(n) or b'{}')
            if self.path in ('/api/prompt','/api/chat'):
                text=body.get('text') or body.get('prompt') or '';model=body.get('model') or 'qwen3.5:4b'
                payload={'model':model,'messages':[{'role':'system','content':'Voce e o agente operacional AURION ONE. Responda em portugues, use apenas estado confirmado e declare incertezas.'},{'role':'user','content':text}],'stream':False}
                s,b,c=req('http://127.0.0.1:11434/api/chat','POST',payload);raw=json.loads(b);return self.sendj(200,{'ok':True,'model':model,'reply':raw.get('message',{}).get('content',''),'raw':raw})
            if self.path=='/api/comfy':
                s,b,c=req('http://127.0.0.1:8188/prompt','POST',body);self.send_response(s);self.send_header('Content-Type',c);self.end_headers();return self.wfile.write(b)
            return self.sendj(404,{'ok':False,'error':'route'})
        except Exception as e:return self.sendj(502,{'ok':False,'error':str(e)})
    def log_message(self,fmt,*args):pass
ThreadingHTTPServer((HOST,PORT),H).serve_forever()
