#!/usr/bin/env python3
"""Preview server for pdp/: static files, plus one endpoint that saves the
Commission wall layout and rebuilds the pages.

    python3 pdp/serve.py            # http://localhost:3470/pdp/
"""
import functools, http.server, io, json, os, re, subprocess, sys, time, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WALL = os.path.join(ROOT, "pdp", "img", "commissions-cut")
LAYOUT = os.path.join(WALL, "layout.json")
_session = None


def rebuild():
    out = subprocess.run([sys.executable, os.path.join(ROOT, "pdp", "build_pdp.py")], cwd=ROOT, capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr[-600:])


def add_image(data, filename, cut):
    """Save an uploaded picture to the wall, cutting the background away if asked."""
    global _session
    from PIL import Image, ImageOps
    im = ImageOps.exif_transpose(Image.open(io.BytesIO(data)))
    stem = re.sub(r"[^a-z0-9]+", "-", os.path.splitext(filename)[0].lower()).strip("-")[:40] or "piece"
    stem = f"added-{int(time.time())}-{stem}"
    if cut:
        sys.path.insert(0, os.path.join(ROOT, "shelf", "tools"))
        from cut import offline_session, clean_alpha
        from rembg import remove
        _session = _session or offline_session()
        rgb = im.convert("RGB")
        out = rgb.convert("RGBA")
        out.putalpha(clean_alpha(remove(rgb, session=_session).convert("RGBA").getchannel("A")))
        out = out.crop(out.getbbox())
        name = stem + ".png"
    else:
        out, name = im.convert("RGB"), stem + ".jpg"
    if max(out.size) > 1400:
        k = 1400 / max(out.size)
        out = out.resize((round(out.width * k), round(out.height * k)), Image.LANCZOS)
    out.save(os.path.join(WALL, name), **({"optimize": True} if cut else {"quality": 88}))
    idx = json.load(open(os.path.join(WALL, "index.json")))
    idx.append([name, out.width, out.height, bool(cut)])
    json.dump(idx, open(os.path.join(WALL, "index.json"), "w"))
    return name


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def reply(self, obj, code=200):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        path, _, qs = self.path.partition("?")
        if path == "/api/commission-image":
            try:
                args = urllib.parse.parse_qs(qs)
                data = self.rfile.read(int(self.headers["Content-Length"] or 0))
                name = add_image(data, args.get("name", ["piece"])[0], args.get("cut", ["1"])[0] == "1")
                rebuild()
                return self.reply({"added": name})
            except Exception as e:
                return self.reply({"error": str(e)}, 500)
        if path != "/api/commission-layout":
            return self.send_error(404)
        try:
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"] or 0)))
            layout = {
                "frame": str(body.get("frame", "3/4")),
                "removed": [str(n) for n in body.get("removed", [])],
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
