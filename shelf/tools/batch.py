#!/usr/bin/env python3
"""Harvest every piece in shelf/pieces.json, one at a time, and report.

Keeps going past a failure — one bad piece should not strand the other
seventeen — and prints a table at the end so the flagged ones are obvious.
"""
import json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAP = json.load(open(os.path.join(ROOT, "shelf/pieces.json"), encoding="utf-8"))
PIECES = {k: v for k, v in MAP.items() if not k.startswith("_")}


def main():
    engine = sys.argv[1] if len(sys.argv) > 1 else "fal"
    only = sys.argv[2:]
    rows = []
    for slug, piece in PIECES.items():
        if only and slug not in only:
            continue
        print(f"\n=== {slug} ({piece}) ===", flush=True)
        r = subprocess.run(
            [sys.executable, os.path.join(ROOT, "shelf/tools/harvest.py"),
             piece, "--slug", slug, "--engine", engine],
            cwd=ROOT,
        )
        side = os.path.join(ROOT, "shelf/sprites", f"{piece}.json")
        if r.returncode == 0 and os.path.exists(side):
            m = json.load(open(side))
            rows.append((slug, m["fidelity_iou"], m["verdict"]))
        else:
            rows.append((slug, None, "ERROR"))

    print("\n" + "=" * 46)
    for slug, iou, verdict in rows:
        score = f"{iou:.3f}" if iou is not None else "  -  "
        print(f"{slug:22} {score}  {verdict}")
    bad = [r for r in rows if r[2] != "ok"]
    print(f"\n{len(rows) - len(bad)}/{len(rows)} ok" + (f", {len(bad)} need attention" if bad else ""))


if __name__ == "__main__":
    main()
