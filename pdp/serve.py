#!/usr/bin/env python3
"""Preview server for pdp/: static files, plus two endpoints that edit the
Commission wall (layout and new images) and rebuild the pages.

    python3 pdp/serve.py            # http://localhost:3470/pdp/

Local only: it listens on 127.0.0.1, serves nothing outside pdp/, and only
accepts edits from pages it served itself.
"""
import functools, http.server, io, json, os, re, subprocess, sys, tempfile, threading, time, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WALL = os.path.join(ROOT, "pdp", "img", "commissions-cut")
LAYOUT = os.path.join(WALL, "layout.json")
MAX_UPLOAD = 25 * 1024 * 1024
HIDDEN = ("/pdp/template.html", "/pdp/pages/", "/pdp/partials/", "/pdp/tools/", "/pdp/serve.py", "/pdp/build_pdp.py")
LOCK = threading.Lock()          # one save and rebuild at a time
_session = None


def write_json(path, obj, **kw):
    """Write to a temp file, then swap it in, so a crash never leaves half a file."""
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(obj, f, **kw)
    os.replace(tmp, path)


def rebuild():
    out = subprocess.run([sys.executable, os.path.join(ROOT, "pdp", "build_pdp.py")], cwd=ROOT, capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr[-600:])


def add_image(data, filename, cut):
    """Save an uploaded picture to the wall, cutting the background away if asked."""
    global _session
    from PIL import Image, ImageOps
    Image.MAX_IMAGE_PIXELS = 60_000_000
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
    idx_path = os.path.join(WALL, "index.json")
    with open(idx_path) as f:
        idx = json.load(f)
    idx.append([name, out.width, out.height, bool(cut)])
    write_json(idx_path, idx)
    return name


class BadRequest(Exception):
    pass


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        path = urllib.parse.unquote(self.path.split("?")[0])
        if not path.startswith("/pdp/") and path != "/pdp" or ".." in path or path.startswith(HIDDEN):
            return self.send_error(404)
        return super().do_GET()

    do_HEAD = do_GET

    def reply(self, obj, code=200):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def body(self):
        origin = self.headers.get("Origin")
        if origin and not re.match(r"^http://(localhost|127\.0\.0\.1)(:\d+)?$", origin):
            raise PermissionError("edits are only accepted from the local preview")
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            raise BadRequest("bad length")
        if n <= 0 or n > MAX_UPLOAD:
            raise BadRequest("upload must be under 25 MB")
        return self.rfile.read(n)

    def do_POST(self):
        path, _, qs = self.path.partition("?")
        if path not in ("/api/commission-image", "/api/commission-layout", "/api/picks"):
            return self.send_error(404)
        try:
            data = self.body()
            with LOCK:
                if path == "/api/picks":          # the photo picker's choices
                    write_json(os.path.join(ROOT, "pdp", "_picker", "picks.json"), json.loads(data), indent=1)
                    return self.reply({"saved": True})
                if path == "/api/commission-image":
                    args = urllib.parse.parse_qs(qs)
                    name = add_image(data, args.get("name", ["piece"])[0], args.get("cut", ["1"])[0] == "1")
                    rebuild()
                    return self.reply({"added": name})
                body = json.loads(data)
                layout = {
                    "frame": str(body.get("frame", "3/4")),
                    "removed": [str(n) for n in body.get("removed", [])],
                    "order": [str(n) for n in body.get("order", [])],
                    "pieces": {str(k): {"s": float(v.get("s", 1)), "x": float(v.get("x", 0)), "y": float(v.get("y", 0)),
                                        "name": str(v.get("name", ""))[:80], "date": str(v.get("date", ""))[:40]}
                               for k, v in body.get("pieces", {}).items()},
                }
                write_json(LAYOUT, layout, indent=1)
                rebuild()
                return self.reply({"saved": True})
        except PermissionError as e:
            return self.reply({"error": str(e)}, 403)
        except (BadRequest, ValueError, AttributeError, TypeError) as e:
            return self.reply({"error": str(e)}, 400)
        except Exception as e:
            return self.reply({"error": str(e)}, 500)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3470
    http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Handler, directory=ROOT)).serve_forever()
