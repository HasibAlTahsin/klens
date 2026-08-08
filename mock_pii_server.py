#!/usr/bin/env python3
"""
Controlled PII test server. Echoes the prompt's PII into 'content'
so the DETECTOR is tested, not the LLM. This isolates KLEnS's true
detection accuracy from model output variability.
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        try:
            body = json.loads(self.rfile.read(length))
        except Exception:
            body = {}
        # prompt-এ যে PII আছে সেটাই content-এ ফেরত দাও (guaranteed echo):
        prompt = body.get('prompt', '')
        resp = json.dumps({
            "index": 0,
            "content": prompt,   # ← ground-truth PII এখানে নিশ্চিত থাকবে
            "tokens": [],
            "stop": True,
            "model": "mock-controlled-test",
        })
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(resp.encode())

    def log_message(self, *a):
        pass  # চুপ

if __name__ == '__main__':
    print('[mock] Controlled PII server on 127.0.0.1:8080')
    HTTPServer(('127.0.0.1', 8080), Handler).serve_forever()
