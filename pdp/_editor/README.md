# The Maçon editor

A small page for changing the site's words and photographs without touching code.
It runs on your own Mac only — it is never part of the live shop.

## Opening it

Double-click **Maçon Editor.command** in the studiomacon folder. A terminal window
opens (leave it open) and the shop appears in your browser.

Every page has a black bar along the bottom. Press **Edit this page** and the words
you can change are outlined: click one and type. Press **Save & rebuild** when done.

There is also a list view, if you would rather work through the pieces one after
another: http://localhost:3470/pdp/_editor/index.html

## What you can change

On the page itself: every heading and paragraph on the shop, About, Custom, Contact
and Shipping pages, and each piece's name, price, overline and description. Hover a
photograph on a product page for **Make main**, **Hide** and the arrows that reorder it.

In the list view as well: the material rows, the field note, the paragraph about how a
piece is made, and where the Bureau stamp sits on the shop page.

The accordions on a product page stand open while you are editing. The care notes
and the shipping paragraphs are **shared**: changing them on one totem changes every
totem, and the shipping wording is the same across the whole shop. The dimensions
come from each piece's own material rows.

To use a photograph from your drive, hover one on a product page and press
**Replace…**. It is resized and saved beside the others.

Escape puts a block back the way it was before you started typing.

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
