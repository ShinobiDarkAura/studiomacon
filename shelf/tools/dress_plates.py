#!/usr/bin/env python3
"""Add props to the empty plates, leaving deliberate room for the pieces.

The original dressed references are beautiful but were styled without knowing
where anything would go, so each shelf has only two or three usable gaps. These
are dressed the other way round: props pushed toward the ends, a long clear run
left in the middle. Same rooms, same light, same grade — the empty plates were
made from those references, so the lineage holds.

    python3 shelf/tools/dress_plates.py
"""
import os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "shelf", "plates", "dressed")

STYLE = (
    "Add period archival still-life props to the shelves: small stacks of pale sun-bleached "
    "books lying flat and standing, a speckled off-white ceramic vase, a few dried stems, a "
    "bundle of old papers tied with ribbon, a small brass cup, a worn card box with a paper "
    "label, a rounded pale stone. Warm ivory palette, everything faded and soft, nothing "
    "bright or new, no colour beyond cream, bone, pale grey and dull brass. "
    "ARRANGEMENT IS CRITICAL: cluster the props toward the LEFT and RIGHT ENDS of each shelf "
    "and leave the MIDDLE HALF of every shelf completely bare — a long clear empty run of "
    "shelf surface with nothing on it and nothing overhanging it. Do not spread props evenly "
    "across the shelf. Do not place anything in the centre. "
    "Change nothing else: keep the exact camera angle, framing, shelves, wall, plaster "
    "texture, window shadows, warm vintage grade and the light direction from camera-left. "
    "Photographic, straight on, shallow depth of field."
)

PLATES = {
    "dressed-bronze-b": ("plate-shelf-bronze.png", "1536x1024"),
    "dressed-tall-b":   ("plate-shelf-tall.png",   "1024x1536"),
    "dressed-thresh-b": ("plate-threshold.png",    "1536x1024"),
}


def main():
    engine = sys.argv[1] if len(sys.argv) > 1 else "gpt"
    script = "gen_scene_fal.py" if engine == "fal" else "gen_scene.py"
    for name, (src, size) in PLATES.items():
        ref = os.path.join(ROOT, "shelf/plates", src)
        dst = os.path.join(OUT, f"{name}.png")
        print(f"dressing {name} <- {src} ...", flush=True)
        subprocess.run(
            [sys.executable, os.path.join(ROOT, "shelf/tools", script),
             "--ref", ref, "--out", dst, "--prompt", STYLE, "--size", size],
            check=True,
        )


if __name__ == "__main__":
    main()
