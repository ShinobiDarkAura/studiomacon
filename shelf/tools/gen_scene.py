#!/usr/bin/env python3
"""One GPT Image 2 call: render a reference object into a scene.

Split out from harvest.py so the network call is a separate process — a hung or
rate-limited request can be killed without losing the harvest state, and the same
scene can be re-harvested with different shadow settings for free.
"""
import argparse, base64, os, sys, requests

ENV = "/Users/aco/Documents/git/pipeline/.env"


def key():
    for line in open(ENV, encoding="utf-8"):
        if line.startswith("OPENAI_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("OPENAI_API_KEY not found in " + ENV)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", help="reference image; omitted for plates, which have no subject")
    ap.add_argument("--out", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--size", default="1536x1024")
    a = ap.parse_args()

    hdr = {"Authorization": f"Bearer {key()}"}
    body = {"model": "gpt-image-2", "prompt": a.prompt,
            "size": a.size, "quality": "high", "n": 1}
    if a.ref:
        r = requests.post(
            "https://api.openai.com/v1/images/edits", headers=hdr,
            files={"image[]": (os.path.basename(a.ref), open(a.ref, "rb"), "image/png")},
            data=body, timeout=900,
        )
    else:
        r = requests.post(
            "https://api.openai.com/v1/images/generations", headers=hdr,
            json=body, timeout=900,
        )
    if r.status_code != 200:
        sys.exit(f"HTTP {r.status_code}: {r.text[:600]}")
    open(a.out, "wb").write(base64.b64decode(r.json()["data"][0]["b64_json"]))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
