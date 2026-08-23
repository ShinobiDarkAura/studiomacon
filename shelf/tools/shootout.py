#!/usr/bin/env python3
"""One piece, one prompt, several fal editors — which relights best and cheapest.

Run once to settle the engine choice. Each model gets the identical reference and
the identical prompt, including a REAL cast shadow (bounded so it stays in frame,
which is what the earlier 'contact shadow only' wording destroyed).

    python3 shelf/tools/shootout.py rebi-1
"""
import base64, json, mimetypes, os, sys, time, requests

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV = "/Users/aco/Documents/git/pipeline/.env"
OUT = os.path.join(ROOT, "shelf", "_test", "shootout")

MODELS = [
    # name, endpoint, which field the endpoint wants, approx cost per image
    ("nano-banana", "fal-ai/nano-banana/edit",           "image_urls", 0.039),
    ("seedream-v4", "fal-ai/bytedance/seedream/v4/edit", "image_urls", 0.030),
    ("qwen-edit",   "fal-ai/qwen-image-edit",            "image_url",  0.030),
]

PROMPT = (
    "Product photograph of this exact object resting on a plain seamless pale warm-grey "
    "surface. Nothing else in frame: no shelf, no walls, no props, no vignette. "
    "CAMERA: exactly eye level with the surface, straight on, lens perpendicular to the "
    "object, never looking down. "
    "SHADOW: the object casts ONE real soft-edged shadow onto the surface, falling to the "
    "RIGHT and slightly toward the camera, about as long as the object is wide, clearly "
    "visible on the surface beside it. The shadow must stay COMPLETELY inside the frame "
    "with clear empty surface beyond its tip — it must never touch or run off an edge. "
    "Warm late-afternoon light from camera-left. "
    "FRAMING: the whole object visible well inside the frame including where it meets the "
    "surface, at least 20 percent empty margin on every side. "
    "It must be the SAME OBJECT: same form, proportions, surface finish, colour and patina, "
    "every curve, taper, edge and opening preserved. Do not simplify or restyle it."
)


def key():
    for line in open(ENV, encoding="utf-8"):
        if line.startswith("FAL_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("no FAL_API_KEY")


def data_uri(path):
    mime = mimetypes.guess_type(path)[0] or "image/png"
    return f"data:{mime};base64," + base64.b64encode(open(path, "rb").read()).decode()


def run(model, field, ref, hdr):
    uri = data_uri(ref)
    payload = ({"prompt": PROMPT, "image_urls": [uri], "num_images": 1}
               if field == "image_urls" else {"prompt": PROMPT, "image_url": uri})
    r = requests.post(f"https://queue.fal.run/{model}", headers=hdr, json=payload, timeout=180)
    body = r.json() if r.status_code in (200, 201, 202) else {}
    if "status_url" not in body:
        return None, f"submit rejected: {r.text[:160]}"
    job = body

    for _ in range(150):
        s = requests.get(job["status_url"], headers=hdr, timeout=60).json()
        if s.get("status") == "COMPLETED":
            break
        if s.get("status") in ("FAILED", "ERROR"):
            return None, f"failed: {str(s)[:160]}"
        time.sleep(2)
    else:
        return None, "timeout"

    res = requests.get(job["response_url"], headers=hdr, timeout=120).json()
    imgs = res.get("images") or []
    if not imgs:
        return None, f"no image: {str(res)[:160]}"
    return requests.get(imgs[0]["url"], timeout=180).content, None


def main():
    piece = sys.argv[1] if len(sys.argv) > 1 else "rebi-1"
    ref = os.path.join(ROOT, "shelf/cutouts", f"obj-{piece}.png")
    os.makedirs(OUT, exist_ok=True)
    hdr = {"Authorization": f"Key {key()}", "Content-Type": "application/json"}
    spend = 0.0
    for name, model, field, cost in MODELS:
        print(f"--- {name} ({model})", flush=True)
        blob, err = run(model, field, ref, hdr)
        spend += cost
        if err:
            print(f"    {err}", flush=True)
            continue
        dst = os.path.join(OUT, f"{piece}--{name}.png")
        open(dst, "wb").write(blob)
        print(f"    wrote {os.path.basename(dst)}", flush=True)
    print(f"\nestimated spend ${spend:.2f}")


if __name__ == "__main__":
    main()
