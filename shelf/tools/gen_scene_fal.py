#!/usr/bin/env python3
"""One Nano Banana call on fal: render a reference object into a scene.

Same contract as gen_scene.py — --ref, --out, --prompt — so harvest.py can swap
engines without knowing anything about either provider.

Nano Banana is roughly a fifth the cost of GPT Image 2, which matters across a
catalogue: the pieces only need relighting, not invention. The plates stay on
GPT Image 2, where a whole room is being built rather than one object relit.
"""
import argparse, base64, mimetypes, os, sys, time, requests

ENV = "/Users/aco/Documents/git/pipeline/.env"
ENDPOINT = "https://queue.fal.run/fal-ai/nano-banana/edit"


def key():
    for line in open(ENV, encoding="utf-8"):
        if line.startswith("FAL_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("FAL_API_KEY not found in " + ENV)


def data_uri(path):
    mime = mimetypes.guess_type(path)[0] or "image/png"
    return f"data:{mime};base64," + base64.b64encode(open(path, "rb").read()).decode()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--size", default=None, help="accepted and ignored; fal follows the reference")
    a = ap.parse_args()

    hdr = {"Authorization": f"Key {key()}", "Content-Type": "application/json"}
    r = requests.post(ENDPOINT, headers=hdr, timeout=120, json={
        "prompt": a.prompt,
        "image_urls": [data_uri(a.ref)],
        "num_images": 1,
        "output_format": "png",
    })
    if r.status_code not in (200, 201, 202):
        sys.exit(f"submit HTTP {r.status_code}: {r.text[:500]}")
    job = r.json()
    status_url, result_url = job.get("status_url"), job.get("response_url")

    for _ in range(180):
        s = requests.get(status_url, headers=hdr, timeout=60).json()
        st = s.get("status")
        if st == "COMPLETED":
            break
        if st in ("FAILED", "ERROR"):
            sys.exit(f"job failed: {str(s)[:500]}")
        time.sleep(2)
    else:
        sys.exit("timed out waiting for fal")

    res = requests.get(result_url, headers=hdr, timeout=120).json()
    imgs = res.get("images") or []
    if not imgs:
        sys.exit(f"no image in result: {str(res)[:400]}")
    url = imgs[0]["url"]
    open(a.out, "wb").write(requests.get(url, timeout=180).content)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
