#!/usr/bin/env python3
"""Stage the deployable site into _site/, shipping only reachable files.

build.py already emits optimized WebP derivatives, so the full-resolution
originals never need to leave the repo. Anything not referenced by an HTML page
or the stylesheet is left behind.

    python3 stage_site.py [_site]
"""
import os, re, shutil, sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "_site"
SRC_DIRS = ["assets", "images", "product"]
ROOT_FILES = [f for f in os.listdir(".") if f.endswith(".html")]

def human(n):
    for u in ("B", "KB", "MB"):
        if n < 1024:
            return f"{n:.0f}{u}"
        n /= 1024
    return f"{n:.1f}GB"

def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    # 1. copy everything that could be served
    for f in ROOT_FILES:
        shutil.copy2(f, OUT)
    for d in SRC_DIRS:
        if os.path.isdir(d):
            shutil.copytree(d, os.path.join(OUT, d))
    if os.path.isdir("admin"):
        shutil.copytree("admin", os.path.join(OUT, "admin"))

    before = sum(os.path.getsize(os.path.join(b, f))
                 for b, _, fs in os.walk(OUT) for f in fs)

    # 2. work out what is actually reachable
    keep = set()
    def add(base, ref):
        if ref.startswith(("http", "mailto:", "#", "data:")):
            return
        p = os.path.normpath(os.path.join(base, ref.split("?")[0].split("#")[0]))
        if os.path.exists(p):
            keep.add(os.path.abspath(p))

    for base, _, files in os.walk(OUT):
        for f in files:
            path = os.path.join(base, f)
            if f.endswith((".html", ".css", ".js")):
                keep.add(os.path.abspath(path))
                try:
                    s = open(path, encoding="utf-8").read()
                except UnicodeDecodeError:
                    continue
                for ref in re.findall(r'(?:src|href)="([^"]+)"', s):
                    add(base, ref)
                for ref in re.findall(r'srcset="([^"]+)"', s):
                    for part in ref.split(","):
                        add(base, part.strip().split(" ")[0])
                for ref in re.findall(r'url\(["\']?([^)"\']+)', s):   # css fonts/images
                    add(base, ref)

    # 3. drop the unreachable (the full-res originals)
    removed = 0
    for base, _, files in os.walk(OUT, topdown=False):
        for f in files:
            p = os.path.abspath(os.path.join(base, f))
            if p not in keep:
                os.remove(p)
                removed += 1
        if not os.listdir(base):
            os.rmdir(base)

    after = sum(os.path.getsize(os.path.join(b, f))
                for b, _, fs in os.walk(OUT) for f in fs)
    kept = sum(len(fs) for _, _, fs in os.walk(OUT))
    print(f"staged {kept} files  {human(before)} -> {human(after)}  ({removed} unreferenced dropped)")

    # 4. fail loudly rather than deploying a site with holes in it
    missing = []
    for base, _, files in os.walk(OUT):
        for f in files:
            if not f.endswith(".html"):
                continue
            s = open(os.path.join(base, f), encoding="utf-8").read()
            for ref in re.findall(r'(?:src|href)="([^"]+)"', s):
                if ref.startswith(("http", "mailto:", "#", "data:")):
                    continue
                t = os.path.join(base, ref.split("?")[0].split("#")[0])
                if not os.path.exists(t):
                    missing.append(f"{os.path.join(base, f)} -> {ref}")
    if missing:
        print(f"ERROR: {len(missing)} broken references")
        for m in missing[:10]:
            print("  ", m)
        sys.exit(1)
    print("all references resolve ✓")

if __name__ == "__main__":
    main()
