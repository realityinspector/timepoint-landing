import http.server
import json
import os
import sys

PORT = int(os.environ.get("PORT", 8080))

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy"}).encode())
            return
        return super().do_GET()

if __name__ == "__main__":
    print(f"Starting server on 0.0.0.0:{PORT}", flush=True)
    sys.stdout.flush()
    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Server listening on port {PORT}", flush=True)
    server.serve_forever()
