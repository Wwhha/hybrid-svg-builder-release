# Operating workflow

## 1. Classify source content

Inspect the image before drawing. Record each non-text object's:

- conceptual role;
- pixel location on the original canvas;
- primitive geometry or local curve asset;
- fill, stroke and approximate stroke width;
- stacking order and overlap with neighboring objects.

Keep the original canvas dimensions. Do not rescale individual crops into inconsistent coordinate systems.

## 2. Represent regular geometry

Use one `layers[]` entry per conceptual module. It becomes a named `<g>` group and an independent module SVG.

- `rect`: rectangles, rounded panels, frames, dashed regions and thin feature slabs.
- `polygon`: cube tops and sides, filled arrowheads and custom solid shapes.
- `line` / `polyline`: connector shafts, axes and schematic icons.
- `arrow`: connector plus vector head.
- `cube`: front rectangle plus top and side polygons.
- `circle`: junction points and round motifs.

Use explicit attributes rather than CSS. Place arrowheads as polygons. Keep each connector in a named group.

## 3. Isolate curve assets

Use `curve_assets[]` only for irregular shapes. Define a tight source bbox and select the mask that cleanly separates desired pixels:

- `color`: saturated colored lines on a pale background.
- `dark`: dark monochrome contours.
- `shape`: filled peak outlines; enclosed contours can be filled.

A crop cannot inherently distinguish a nearby arrow from the desired curve. Inspect `audit/*.crop.png`; narrow the crop or correct the mask if unrelated artwork appears.

## 4. Assemble

Basic geometry and curve placements share original pixel coordinates. The result includes a basic-shape layer, curve layer, and white-background composite.

The independent curve asset uses a tight local canvas. Its large-canvas placement uses `placement.x`, `placement.y` and `placement.scale`.

## 5. Review

Render all previews and inspect them at full-canvas and readable zoom. Check clipped edges, residual source text in curve crops, and unintended neighboring artwork. XML and render checks are necessary but cannot establish scientific correctness. Report fidelity compromises and whether Illustrator was opened natively.