#!/usr/bin/env python3
"""Static server that refuses to let HTML be cached.

Assets carry a content stamp in their URL, so they can cache forever. The HTML
cannot — it is the thing that carries those stamped URLs. A cached document hands
the browser yesterday's asset URLs, so a change that has shipped correctly looks
like it never happened, and there is no way to tell the two apart from the page.
That confusion cost several rounds; this removes it.
"""
import functools, json, os, subprocess, sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

REPO = os.path.expanduser("~/Documents/git/studiomacon")
COMP = os.path.join(REPO, "shelf/composition-dressed.json")

ROOT = os.path.expanduser("~/Library/Application Support/studiomacon-site/public")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 3411


class Handler(SimpleHTTPRequestHandler):
    def _cors(self):
        """Let the page saved from one local port post to another.

        The LaunchAgent that normally serves this cannot write inside
        ~/Documents, so the editor falls back to the terminal-started server on
        another port. That is cross-origin, and without these it is refused
        before the request is even sent.
        """
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self):
        """Save the shelf layout back to the composition, then rebuild.

        Only ever writes the one known file, and only fields the editor owns, so
        a stray request cannot reach anything else on disk.
        """
        if self.path.split("?")[0] != "/api/composition":
            self.send_error(404)
            return
        try:
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"] or 0)))
            comp = json.load(open(COMP, encoding="utf-8"))
            edits = {(e["scene"], e["slug"]): e for e in body.get("pieces", [])}
            n = 0
            for sc in comp["scenes"]:
                for o in sc.get("objects", []):
                    e = edits.get((sc["id"], o["slug"]))
                    if not e:
                        continue
                    for k in ("x", "y", "scale", "dx_px", "option", "width"):
                        if k in e:
                            o[k] = e[k]
                    if e.get("tone"):
                        o["tone"] = e["tone"]
                    elif "tone" in o:
                        del o["tone"]
                    n += 1
            with open(COMP, "w", encoding="utf-8") as f:
                json.dump(comp, f, indent=2, ensure_ascii=False)
            out = subprocess.run([sys.executable, os.path.join(REPO, "shelf/tools/build_shelf.py")],
                                 cwd=REPO, capture_output=True, text=True)
            if out.returncode != 0:
                # A failed rebuild used to be reported as success: the page then
                # cleared the editor's local copy and reloaded a stale build, so
                # the work looked lost even though the composition on disk had
                # it. Say so instead, and let the page keep its edits.
                raise RuntimeError("rebuild failed, composition saved:\n"
                                   + (out.stderr or out.stdout).strip()[-500:])
            for name in ("index.html", "shelf.css"):
                src = os.path.join(REPO, "shelf/_site", name)
                if os.path.exists(src):
                    open(os.path.join(ROOT, "shelf", name), "wb").write(open(src, "rb").read())
            msg = json.dumps({"saved": n, "build": (out.stdout or out.stderr).strip()[-400:]}).encode()
        except Exception as exc:                       # report it to the page, do not die
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self._cors()
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(exc)}).encode())
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(msg)))
        self._cors()
        self.end_headers()
        self.wfile.write(msg)

    def end_headers(self):
        path = self.path.split("?")[0]
        if path.endswith((".html", "/")) or "." not in path.rsplit("/", 1)[-1]:
            self.send_header("Cache-Control", "no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
        else:
            self.send_header("Cache-Control", "public, max-age=31536000")
        super().end_headers()


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", PORT),
                        functools.partial(Handler, directory=ROOT)).serve_forever()
