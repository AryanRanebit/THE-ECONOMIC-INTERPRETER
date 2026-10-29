"""
Local Development Server for The Economic Interpreter
=====================================================
Serves the redesigned landing page and forwards /api calls to api/index.py.
Run with: python dev_server.py [port]
"""

import sys
import os
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

ROOT_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = ROOT_DIR / "public"
sys.path.insert(0, str(ROOT_DIR))

from api.index import handler as APIHandler

class LocalDevHandler(APIHandler, SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        SimpleHTTPRequestHandler.__init__(self, *args, directory=str(ROOT_DIR), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api" or parsed.path.startswith("/api/"):
            APIHandler.do_GET(self)
        else:
            if parsed.path in ["", "/", "/index.html"]:
                target = PUBLIC_DIR / "index.html"
                if target.exists():
                    self.path = "/public/index.html"
            SimpleHTTPRequestHandler.do_GET(self)

    def do_OPTIONS(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api" or parsed.path.startswith("/api/"):
            APIHandler.do_OPTIONS(self)
        else:
            SimpleHTTPRequestHandler.do_OPTIONS(self)

def run_server(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, LocalDevHandler)
    print(f"\n==================================================")
    print(f"  The Economic Interpreter - Localhost Server")
    print(f"==================================================")
    print(f"  Serving Redesigned Web Application at:")
    print(f"  --> http://localhost:{port}")
    print(f"  --> http://127.0.0.1:{port}")
    print(f"  API Endpoint: http://localhost:{port}/api?action=health")
    print(f"==================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_server(port)
