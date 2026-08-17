#!/usr/bin/env python3
"""Identity test: does a generated scene preserve the actual piece?

Renders Milo into a shelf scene from the real photo as reference, so the result
can be cut out and compared against the real cutout silhouette-for-silhouette.
If the form and patina drift, generated scenes can't be used for product shots.

One image. GPT Image 2, edits endpoint.
"""
import argparse, base64, os, sys, requests

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV = "/Users/aco/Documents/git/pipeline/.env"

SCENE = (
    "on a pale stone shelf in a quiet archival storage room. Warm late-afternoon window "
    "light from camera-left, soft shadows falling to the right, plaster wall behind, "
    "industrial steel shelf uprights at the edges. Photographic still life, shallow depth "
    "of field, muted warm neutral palette."
)
HOLD = (
    "Reproduce the object EXACTLY as given: identical silhouette, proportions, stance and "
    "surface finish. Do not restyle, redesign, smooth, or re-proportion it. It must remain "
    "the same object, only relit for the scene, sitting on the shelf with a physically "
    "correct contact shadow."
)
PIECES = {
    "milo-1": "Place this exact bronze animal figurine " + SCENE + " " + HOLD +
              " Preserve its dark-to-pale ombre patina gradient and fine tooling texture.",
    "zuma-ring-3": "Place this exact sterling silver ring, standing upright on its band, " +
              SCENE + " " + HOLD +
              " Preserve the open void through the centre of the ring — the shelf must be "
              "visible through it. Keep the exact band thickness, the sculptural crossing "
              "forms at the top, and the brushed satin finish with its soft specular "
              "highlights. Do not thicken, polish, or simplify it.",
}


def key():
    for line in open(ENV, encoding="utf-8"):
        if line.startswith("OPENAI_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("OPENAI_API_KEY not found in " + ENV)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("piece", choices=sorted(PIECES))
    ap.add_argument("--size", default="1536x1024")
    a = ap.parse_args()

    ref = os.path.join(ROOT, "shelf", "cutouts", f"obj-{a.piece}.png")
    out = os.path.join(ROOT, "shelf", "_test", f"identity-{a.piece}.png")

    r = requests.post(
        "https://api.openai.com/v1/images/edits",
        headers={"Authorization": f"Bearer {key()}"},
        files={"image[]": (os.path.basename(ref), open(ref, "rb"), "image/png")},
        data={
            "model": "gpt-image-2",
            "prompt": PIECES[a.piece],
            "size": a.size,
            "quality": "high",
            "n": 1,
        },
        timeout=600,
    )
    if r.status_code != 200:
        sys.exit(f"HTTP {r.status_code}: {r.text[:600]}")
    open(out, "wb").write(base64.b64decode(r.json()["data"][0]["b64_json"]))
    print("wrote", out)


if __name__ == "__main__":
    main()
