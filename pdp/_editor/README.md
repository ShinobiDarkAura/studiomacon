# The Maçon editor

A small page for changing the site's words and photographs without touching code.
It runs on your own Mac only — it is never part of the live shop.

## Opening it

Double-click **Maçon Editor.command** in the studiomacon folder. A terminal window
opens (leave it open) and the editor appears in your browser.

If you'd rather type it: `python3 pdp/serve.py` then open
http://localhost:3470/pdp/_editor/index.html

## What you can change

- **Each piece**: its name, price, overline, description, field note, the paragraph
  about how it's made, and the material rows.
- **Photographs**: which one is the main picture (★), which appear at all, and their order.
- **The Bureau stamp** on the shop page: size, position and tilt, with a live preview.

Anything you haven't changed keeps its original wording. A changed field is outlined
in amber and has an **undo** link; **Undo all my changes** puts everything back.

**Save & rebuild** writes your changes and rebuilds the site. Open the shop to see them.

## Where the changes live

In `pdp/content.json` — only what you've changed, nothing else. Delete an entry and
the original wording returns.

## Two people editing

The file is shared through git like everything else. If you and Alex both edit at the
same time on different machines, whoever saves second can overwrite the first. Easiest
rule: one of you at a time, and `git pull` before you start.
