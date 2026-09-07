# Shelf asset pipeline v3

The shelf is one fixed physical system: identical wooden geometry, one tall
window at camera-left, and a warm universal product-lighting rig. Structure is
deterministic; botanical shadows and props vary by plate.

## Plates

1. Start every plate from `shelf-master-wood-v2.png`.
2. Render props and a unique botanical gobo together so props block and reflect
   the light naturally.
3. Keep the central product zone empty.
4. Restore the canonical shelf pixels if generation changes the shelf geometry.
5. Reject dark bottom bars, transparency, additional shelves, or altered camera.

## Products

1. Select the curated catalogue view in `pipeline-v3.json`; never infer it from
   image order.
2. Preserve its clean cutout as immutable identity truth.
3. Render the product alone in the universal left-window lighting rig on a plain
   seamless surface.
4. Harvest object, cast-shadow and contact-shadow layers separately.
5. Prefer low-frequency illumination transfer onto the original product pixels;
   a fully regenerated object is accepted only after identity review.
6. Save the base anchor, physical dimensions, source and rig metadata.

Totems use an eye-level three-quarter view with a restrained 15–25° yaw. The
camera remains level; only the product turns. Newly revealed side surfaces may
be extrapolated, but the known silhouette, construction, texture, and patina
remain identity constraints.

Rings never stand vertically without support. Each ring is explicitly assigned
either a natural three-quarter lean or a flat/slightly top-down presentation.
Jewellery scale is judged against its support and shelf depth before legibility.
When the catalogue view does not show a ring's sidewalls or underside, the
render may extrapolate the simplest plausible continuation of the photographed
geometry. That extrapolation is recorded and reviewed rather than mistaken for
source-grounded detail.

## QA gates

- shelf geometry matches the canonical plate pixel-for-pixel;
- product is not clipped and all openings survive;
- silhouette IoU passes the configured threshold;
- cast shadow falls right under the shared left-window rig;
- contact point matches the stored base anchor;
- color and patina remain faithful to the catalogue source;
- the full vertical contact sheet reads as one room with varied foliage.
