#!/usr/bin/env python3
"""Harmonising pass: hand it a finished composite, ask only for integration.

The model is not being asked to place or invent anything — the composite already
has every piece at the right size in the right spot. Its job is the part
compositing cannot do: unify grain and grade, add bounce light and contact
darkening, match depth of field. That is a far smaller ask than placement, which
is where generating a full shelf broke down.

It still redraws the whole frame, so the pieces are at risk; restoring the real
ones afterwards is a separate step.

    python3 shelf/tools/polish.py shelf/_site/scene-d-bronze.jpg 1536x1024
"""
import os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROMPT = (
    "This is a finished photograph of a shelf holding small cast bronze and silver "
    "objects among vintage props. DO NOT move, resize, rotate, replace, restyle, "
    "duplicate or remove ANYTHING. Every object stays exactly where it is, at exactly "
    "the same size, with exactly the same shape, silhouette, surface and colour. Do not "
    "reinterpret the small metal pieces — they are real products and must not change. "
    "Your only job is to make it read as a single photograph taken in one moment: "
    "unify the film grain and colour grade across the whole frame, add correct soft "
    "contact shadow and subtle warm bounce light where each small piece meets the shelf, "
    "match each piece's edge sharpness and depth of field to the objects beside it, and "
    "settle the pieces into the scene's light. Photographic, straight on, warm ivory, "
    "identical framing."
)


def main():
    src = os.path.join(ROOT, sys.argv[1]) if not os.path.isabs(sys.argv[1]) else sys.argv[1]
    size = sys.argv[2] if len(sys.argv) > 2 else "1536x1024"
    dst = os.path.splitext(src)[0] + "-polished.png"
    subprocess.run(
        [sys.executable, os.path.join(ROOT, "shelf/tools/gen_scene.py"),
         "--ref", src, "--out", dst, "--prompt", PROMPT, "--size", size],
        check=True,
    )
    print("wrote", dst)


if __name__ == "__main__":
    main()
