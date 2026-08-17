#!/usr/bin/env python3
"""Generate the bare shelf plates by emptying the concept references.

Written from scratch rather than described from scratch. Prompting for a shelf
"in the style of" the references produced something cleaner, cooler and more
architectural than the refs — clean stone, grey steel, a room rather than a mood.
Feeding each reference in and asking only for the objects to be removed keeps the
thing that actually matters: the warm ivory grade, the bleached timber, the
straight-on frontal camera, the soft window light from camera-left and the
shadow patterns it throws on the plaster.

It also guarantees the light direction matches the sprites' baked shadows,
because it is literally the same light.

    python3 shelf/tools/plates.py               # all
    python3 shelf/tools/plates.py threshold     # one
"""
import os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "shelf", "plates")
REFS = "/Users/aco/Downloads/Macon/SHELF CONCEPT SITE"

EMPTY = (
    "Remove every object from the shelves. The shelves must be left COMPLETELY BARE: "
    "no vases, no books, no bowls, no dried flowers, no boxes, no papers, no pottery, "
    "no cups, no stones, no frames, no ornaments of any kind. Nothing resting on any "
    "shelf. Continue the shelf surface and the wall cleanly where each object used to "
    "be, with the correct soft shadowing. "
    "Change NOTHING else. Keep the exact same camera angle, framing, focal length and "
    "straight-on frontal view. Keep the shelves themselves, their material, thickness "
    "and edges. Keep the wall, its plaster texture and every shadow the window casts "
    "on it. Keep the warm ivory vintage colour grade, the soft film grain and the "
    "identical light direction from camera-left. Only the objects disappear."
)

PLATES = {
    # name: (reference file, canvas)
    "threshold":    ("ChatGPT Image Jun 10, 2026, 05_47_29 PM.png",     "1536x1024"),
    "shelf-bronze": ("ChatGPT Image Jun 10, 2026, 05_49_04 PM.png",     "1536x1024"),
    "shelf-tall":   ("ChatGPT Image Jun 10, 2026, 05_09_08 PM (1).png", "1024x1536"),
}


def main():
    which = sys.argv[1:] or sorted(PLATES)
    os.makedirs(OUT, exist_ok=True)
    for name in which:
        if name not in PLATES:
            sys.exit(f"unknown plate {name!r}; have {sorted(PLATES)}")
        ref_name, size = PLATES[name]
        ref = os.path.join(REFS, ref_name)
        if not os.path.exists(ref):
            sys.exit("missing reference: " + ref)
        dst = os.path.join(OUT, f"plate-{name}.png")
        print(f"emptying {name} <- {ref_name} ...", flush=True)
        subprocess.run(
            [sys.executable, os.path.join(ROOT, "shelf/tools/gen_scene.py"),
             "--ref", ref, "--out", dst, "--prompt", EMPTY, "--size", size],
            check=True,
        )


if __name__ == "__main__":
    main()
