# Hybrid SVG Builder

A Codex skill and deterministic Python builder for turning raster scientific schematics into an **editable hybrid SVG package**.

Regular objects are reconstructed as named rectangles, polygons, lines and arrows. Only selected irregular regions, such as spectra and peak outlines, are locally traced. Text is intentionally excluded so it can be typeset independently.

## Why hybrid

A complete auto-trace frequently converts simple rectangles and arrowheads into noisy contour clusters. This project separates four concerns:

1. **Object interpretation** recorded in a checked JSON specification.
2. **Primitive SVG generation** by Python.
3. **Local curve isolation and tracing** with OpenCV masks and VTracer.
4. **Assembly, preview, validation and packaging** in a shared canvas coordinate system.

## Requirements

- Python 3.10 or newer
- `numpy`, `Pillow`, `opencv-python-headless`, `vtracer`, `resvg-py`

Install from this directory:

```bash
python -m pip install -e .
```

## Commands

Create a starter specification next to an image:

```bash
python scripts/hybrid_skill.py prepare --image figure.png --output figure.spec.json
```

Validate it after adding the identified geometry and selected curve crops:

```bash
python scripts/hybrid_skill.py validate-spec figure.spec.json
```

Build into a new directory:

```bash
python scripts/hybrid_skill.py build figure.spec.json --output rebuilt
python scripts/hybrid_skill.py validate rebuilt
python scripts/hybrid_skill.py package rebuilt
```

The build command refuses to overwrite a non-empty output directory.

## Output

```text
rebuilt/
|-- 01_combined_no_text.svg
|-- 02_basic_shapes_only.svg
|-- 03_curves_at_original_positions.svg
|-- assets/basic/<module-id>.svg
|-- assets/curves/<curve-id>.svg
|-- previews/*.png
`-- audit/                 specification snapshot, crops, traces and counts
```

All layers use the source canvas dimensions. Import the basic-shape and curve layers at identical page sizes when compositing them in Illustrator.

## Authoring expectations

The JSON specification is deliberately explicit. Image interpretation remains the model's responsibility; the builder does not infer object types, connector relationships or scientific meaning. This makes the difficult judgment reviewable while keeping output deterministic.

See [references/workflow.md](references/workflow.md), [references/spec-schema.md](references/spec-schema.md), and [SKILL.md](SKILL.md).

## Scope

This is not an exact-trace or OCR tool. It does not reconstruct underlying measurements. Visual fidelity depends on source resolution and crop quality. It has not been validated against every Illustrator release. Retain the source image and use a versioned output directory for every revision.

No source figures are included. Test only with images whose rights permit redistribution.