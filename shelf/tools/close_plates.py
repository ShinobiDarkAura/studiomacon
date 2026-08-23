#!/usr/bin/env python3
"""Close-bay plates styled with props in the pieces' own size class.

Everything that went wrong with scale traces back to the props: a 250mm book
next to a 30mm bronze tells the eye the bronze is nothing. Rather than enlarging
the pieces or muting them, the shelf gets restyled with objects of a comparable
size and the camera moves in. Then true scale reads correctly with no cheating.

Generated from the dressed references so the room, light and grade carry over —
describing a shelf from scratch produced something cleaner and more architectural
than the references, and it was wrong.
"""
import os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "shelf", "plates", "dressed")

COMMON = (
    "Move the camera MUCH CLOSER: a single shallow shelf bay filling the frame, so the "
    "visible run of shelf is only about 30cm wide. Straight on, eye level with the shelf "
    "surface, no downward angle. "
    "RESTYLE the props so everything on the shelf is SMALL — nothing larger than a "
    "cigarette packet. Use: a worn matchbox, a small tin with a paper label, a couple of "
    "index cards and paper tags, a thimble, a jeweller's loupe, two or three small pale "
    "pebbles, a tiny glass vial, a folded scrap of paper, a small brass key. "
    "ABSOLUTELY NO books, no large vases, no bowls, no tall bottles, no dried branches, "
    "nothing big. Everything must be tiny, the sort of thing that fits in a hand. "
    "Cluster the props to the LEFT and RIGHT and leave the MIDDLE of the shelf completely "
    "bare, a clear empty run with nothing on it. "
    "Keep everything else identical: the same warm ivory vintage grade, faded plaster wall, "
    "soft window light from camera-left, film grain and shallow depth of field."
)

PLATES = {
    "close-bay-a": ("dressed/dressed-threshold.png", "1536x1024"),
    "close-bay-b": ("dressed/dressed-shelf-bronze.jpg", "1536x1024"),
}


def main():
    engine = sys.argv[1] if len(sys.argv) > 1 else "gpt"
    script = "gen_scene_fal.py" if engine == "fal" else "gen_scene.py"
    for name, (src, size) in PLATES.items():
        ref = os.path.join(ROOT, "shelf/plates", src)
        dst = os.path.join(OUT, f"{name}.png")
        print(f"{name} <- {os.path.basename(src)}", flush=True)
        subprocess.run(
            [sys.executable, os.path.join(ROOT, "shelf/tools", script),
             "--ref", ref, "--out", dst, "--prompt", COMMON, "--size", size],
            check=True,
        )


if __name__ == "__main__":
    main()
