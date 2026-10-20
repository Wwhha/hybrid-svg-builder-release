---
name: hybrid-svg-builder
description: Reconstruct raster scientific figures and schematics as edit-friendly SVG packages by rebuilding simple geometry and tracing only selected complex curve regions. Use when raster-to-vector conversion must preserve Illustrator-editable rectangles, panels, arrows, cubes, and separate curve assets rather than tracing the whole image.
---

# Hybrid SVG Builder

Produce a **hybrid** vector package: ordinary geometry is rebuilt with SVG primitives, while irregular curve regions alone are mask-isolated and traced. Never convert the complete raster figure into one automatic trace.

## Required workflow

1. Inspect the source image and map its editable objects. Read [references/workflow.md](references/workflow.md) and [references/spec-schema.md](references/spec-schema.md).
2. Create a starter specification with `python scripts/hybrid_skill.py prepare --image <image> --output <spec.json>`. Complete it by transcribing panels, boxes, cubes, arrows, symbols, and curve crops. Keep visible lettering out of `layers` and `curve_assets`.
3. Validate before drawing: `python scripts/hybrid_skill.py validate-spec <spec.json>`.
4. Build: `python scripts/hybrid_skill.py build <spec.json> --output <new-directory>`.
5. Inspect all three previews at readable scale. Check clipped arrows, curve noise, panel alignment, cube stacking, dashes and absent non-text artwork. Correct the spec or crop, then rebuild in a new output directory.
6. Run `python scripts/hybrid_skill.py validate <directory>`, then `package <directory>`.
7. Report the output directory, ZIP, preview, unresolved fidelity issues, and whether native Illustrator import was tested.

## Reconstruction rules

- Use rectangles, circles, lines, polylines, polygons and plain paths for regular geometry. One named layer per conceptual module.
- Build each cube from one front rectangle and two explicit polygons, grouped under one ID.
- Build each arrow from a connector plus a filled triangular head. Do not use SVG markers.
- Use the source coordinate canvas throughout. Place all layers against the same viewBox; do not independently crop the common composition.
- Use curve assets only for spectra, organic contours and similar regions that cannot be described economically. Use the smallest useful crop.
- Choose `color` for saturated colored curves, `dark` for dark monochrome strokes, and `shape` for filled peak regions. If the crop includes an arrow, frame or text, narrow it or correct the isolated crop before tracing.
- Keep text and formulas out of generated SVGs. Do not invent absent labels.
- Preserve the source's connector topology and scientific meaning. Report inconsistencies rather than silently correcting them.

## Deliverables and limits

The builder writes a white-background no-text composite, transparent basic-shape and curve layers, one SVG per named basic module, one tightened SVG per curve asset, three previews, the validated spec snapshot, and a ZIP.

Tracing recovers visual contours, not measured data. State that curve paths are approximations. Generated SVGs must not contain embedded images, external assets, CSS classes, filters, masks, symbols, `<use>`, foreignObject, scripts or animation. Successful XML and render checks do not prove artistic fidelity or a clean native Illustrator experience.