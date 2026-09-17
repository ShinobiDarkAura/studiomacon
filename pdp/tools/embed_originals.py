#!/usr/bin/env python3
"""Rank every original photo against each piece's current site photos, for the picker.

    ~/.venvs/macon-vision/bin/python pdp/tools/embed_originals.py

Uses DINOv2 image features (good at telling objects apart). Each original is embedded
whole and as a centre crop, since pieces are often small in frame. Writes
pdp/_picker/thumbs/*.jpg and pdp/_picker/data.json.
"""
import glob, hashlib, json, os, re, sys
import numpy as np, torch
from PIL import Image, ImageOps
import pillow_heif
from transformers import AutoImageProcessor, AutoModel

pillow_heif.register_heif_opener()
PDP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.expanduser("~/Downloads/Maçon/Unmodified Originals")
OUT = os.path.join(PDP, "_picker")
dev = "mps" if torch.backends.mps.is_available() else "cpu"
proc = AutoImageProcessor.from_pretrained("facebook/dinov2-base")
model = AutoModel.from_pretrained("facebook/dinov2-base").to(dev).eval()


def embed(images):
    with torch.no_grad():
        x = proc(images=images, return_tensors="pt").to(dev)
        h = model(**x).last_hidden_state
        v = torch.cat([h[:, 0], h[:, 1:].mean(1)], 1)
        return torch.nn.functional.normalize(v, dim=1).cpu().numpy()


def crops(im):
    w, h = im.size
    out = [im]
    for f in (0.6, 0.4):
        cw, ch = w * f, h * f
        out.append(im.crop(((w - cw) / 2, (h - ch) / 2, (w + cw) / 2, (h + ch) / 2)))
    return out


products = json.load(open(os.path.join(os.path.dirname(PDP), "_source", "products.json")))
refs, ref_vecs = {}, {}
for p in products:
    s = p["slug"]
    files = sorted(f for f in glob.glob(os.path.join(PDP, "img", s, "*.jpg"))
                   if re.search(r"/(hero|plain-\d+|hand-\d+)\.jpg$", f))
    refs[s] = [os.path.relpath(f, PDP) for f in files]
    ims = [ImageOps.exif_transpose(Image.open(f)).convert("RGB") for f in files]
    ref_vecs[s] = embed(ims)
    print("ref", s, len(files), flush=True)

cands = sorted(f for f in glob.glob(SRC + "/*") if f.lower().endswith((".jpg", ".jpeg", ".png", ".heic")))
names, vecs = [], []
for i, f in enumerate(cands):
    try:
        im = ImageOps.exif_transpose(Image.open(f)).convert("RGB")
    except Exception as e:
        print("skip", f, e); continue
    b = os.path.basename(f)
    thumb = hashlib.md5(b.encode()).hexdigest()[:12] + ".jpg"
    tp = os.path.join(OUT, "thumbs", thumb)
    if not os.path.exists(tp):
        t = im.copy(); t.thumbnail((720, 720)); t.save(tp, quality=82)
    names.append({"file": b, "thumb": "thumbs/" + thumb, "size": list(im.size)})
    vecs.append(embed(crops(im)))
    if i % 25 == 0:
        print(f"{i}/{len(cands)}", flush=True)

rank = {}
for s, rv in ref_vecs.items():
    scores = [float((v @ rv.T).max()) for v in vecs]
    order = np.argsort(scores)[::-1][:60]
    rank[s] = [{"i": int(k), "score": round(scores[k], 3)} for k in order]

json.dump({"products": [{"slug": p["slug"], "name": p["name"], "refs": refs[p["slug"]]} for p in products],
           "files": names, "rank": rank}, open(os.path.join(OUT, "data.json"), "w"))
print("done", len(names))
