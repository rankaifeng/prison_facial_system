from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request

class Proxy(BaseHTTPRequestHandler):
    def do_GET(self):
        url = f"http://10.2.50.16{self.path}"
        try:
            resp = urllib.request.urlopen(url)
            self.send_response(200)
            self.send_header("Content-Type", resp.headers.get("Content-Type"))
            self.end_headers()
            self.wfile.write(resp.read())
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(b"Bad Gateway")

HTTPServer(("0.0.0.0", 80), Proxy).serve_forever()
