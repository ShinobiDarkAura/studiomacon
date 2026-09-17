#!/usr/bin/env python3
"""Preview server for pdp/: static files, plus one endpoint that saves the
Commission wall layout and rebuilds the pages.

    python3 pdp/serve.py            # http://localhost:3470/pdp/
"""
import functools, http.server, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAYOUT = os.path.join(ROOT, "pdp", "img", "commissions-cut", "layout.json")


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_POST(self):
        if self.path.split("?")[0] != "/api/commission-layout":
            return self.send_error(404)
        try:
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"] or 0)))
            layout = {
                "frame": str(body.get("frame", "3/4")),
                "order": [str(n) for n in body.get("order", [])],
                "pieces": {str(k): {"s": float(v.get("s", 1)), "x": float(v.get("x", 0)), "y": float(v.get("y", 0)),
                                    "name": str(v.get("name", ""))[:80], "date": str(v.get("date", ""))[:40]}
                           for k, v in body.get("pieces", {}).items()},
            }
            with open(LAYOUT, "w") as f:
                json.dump(layout, f, indent=1)
            out = subprocess.run([sys.executable, os.path.join(ROOT, "pdp", "build_pdp.py")],
                                 cwd=ROOT, capture_output=True, text=True)
            if out.returncode != 0:
                raise RuntimeError(out.stderr[-600:])
            reply, code = {"saved": True}, 200
        except Exception as e:
            reply, code = {"error": str(e)}, 500
        data = json.dumps(reply).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3470
    http.server.ThreadingHTTPServer(("", port), functools.partial(Handler, directory=ROOT)).serve_forever()
