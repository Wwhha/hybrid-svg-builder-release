# Specification schema 1.0

The source image path is relative to the specification file. Geometry coordinates use source-image pixels.

```json
{
  "schema_version": "1.0",
  "canvas": {"width": 1200, "height": 800},
  "source": {"image": "figure.png"},
  "white_background": true,
  "layers": [
    {
      "id": "01-panels",
      "elements": [
        {
          "id": "blue-panel",
          "kind": "rect",
          "bbox": [100, 80, 600, 220],
          "rx": 16,
          "style": {"fill": "#dce8f7", "stroke": "#4f78a5", "stroke_width": 2.5, "dasharray": "10 6"}
        },
        {
          "id": "model-block",
          "kind": "cube",
          "bbox": [280, 150, 60, 45],
          "depth": {"x": 18, "y": 16},
          "faces": {"front": "#4c86c8", "top": "#79a8d9", "side": "#386fae"}
        },
        {
          "id": "input-to-reference",
          "kind": "arrow",
          "points": [[60, 250], [240, 130]],
          "head": 12,
          "style": {"stroke": "#17191b", "stroke_width": 2.2}
        }
      ]
    }
  ],
  "curve_assets": [
    {
      "id": "spectral-curves",
      "source_bbox": [20, 200, 320, 250],
      "placement": {"x": 20, "y": 200, "scale": 1},
      "mask": "color",
      "tracer": {"color_precision": 6, "layer_difference": 16}
    }
  ]
}
```

## Geometry types

- **rect**: `bbox`; optional `rx` and style.
- **circle**: `cx`, `cy`, `r`; optional style.
- **line**: exactly two `points`.
- **polyline**: at least two `points`; no fill.
- **polygon**: at least three `points`; optional fill.
- **cube**: `bbox`, `depth: {x,y}`, `faces: {front,top,side}`.
- **arrow**: at least two `points`, `head`, optional stroke style.

Every layer and ordinary element has a unique ID. Use lowercase, action-oriented layer IDs, such as `01-reference-branch` and `07-connectors`.

## Curve asset

`source_bbox` is `[x, y, width, height]` in source pixels. `placement` is absolute on the full canvas. `mask` is `color`, `dark` or `shape`. `tracer` values override the safe defaults in `scripts/hybrid/assets.py`.

Text fields do not belong in the schema. Text is authored after import unless the user explicitly requests a different scope.

## Validation failures

- object outside the canvas;
- duplicate IDs;
- unknown type, color or curve mask;
- missing source image;
- coincident arrow endpoints;
- curve placement outside the canvas;
- malformed coordinates or tracer options.