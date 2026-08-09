import json, os, sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
URL="https://api.mistral.ai/v1/chat/completions"
MODEL=os.environ.get("MISTRAL_MODEL","mistral-small-latest")
KEY=os.environ.get("MISTRAL_API_KEY","")
if not KEY:
    print("ERROR: MISTRAL_API_KEY not set. Run: export MISTRAL_API_KEY=..."); sys.exit(1)
class H(BaseHTTPRequestHandler):
    def _send(self,o):
        d=json.dumps(o).encode()
        self.send_response(200); self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(d))); self.end_headers(); self.wfile.write(d)
    def do_GET(self): self._send({"status":"ok"})
    def do_POST(self):
        n=int(self.headers.get("Content-Length",0)); b=json.loads(self.rfile.read(n) or b"{}")
        try:
            r=requests.post(URL,headers={"Authorization":f"Bearer {KEY}","Content-Type":"application/json"},
                json={"model":MODEL,"temperature":0,"messages":[{"role":"user","content":b.get("prompt","")}]},timeout=120)
            txt=r.json()["choices"][0]["message"]["content"]
        except Exception as e: txt=f"[gateway error] {e}"
        self._send({"content":txt,"model":MODEL})
    def log_message(self,*a): pass
HTTPServer(("127.0.0.1",int(sys.argv[1]) if len(sys.argv)>1 else 8080),H).serve_forever()
