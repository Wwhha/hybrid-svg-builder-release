from __future__ import annotations

import copy
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from .svg import SVG, fmt, new_document

TRACER_DEFAULTS = {
    "colormode": "color", "hierarchical": "stacked", "mode": "spline",
    "filter_speckle": 6, "color_precision": 6, "layer_difference": 16,
    "corner_threshold": 65, "length_threshold": 2.5, "max_iterations": 10,
    "splice_threshold": 45, "path_precision": 3,
}


def _deps():
    try:
        import cv2
        import numpy as np
        import resvg_py
        import vtracer
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Install project dependencies with: pip install -e .") from exc
    required = {"cv2": cv2, "numpy": np, "resvg_py": resvg_py, "vtracer": vtracer, "PIL": Image}
    missing = [name for name, module in required.items() if not getattr(module, "__file__", None) or (name == "cv2" and not hasattr(module, "bilateralFilter"))]
    if missing:
        raise RuntimeError("Dependencies are importable but unusable in this process: " + ", ".join(missing) + ". Check filesystem permissions or reinstall with: pip install -e .")
    return cv2, np, resvg_py, vtracer, Image


def trace_curve(source: Path, bbox: list[float], mode: str, audit_base: Path,
                tracer: dict[str, Any] | None = None) -> tuple[Path, Path, int]:
    cv2, np, _, vtracer, Image = _deps()
    audit_base.parent.mkdir(parents=True, exist_ok=True)
    image = np.asarray(Image.open(source).convert("RGB"))
    l, t, w, h = [round(v) for v in bbox]
    crop = cv2.bilateralFilter(image[t:t+h, l:l+w].copy(), 5, 28, 4)
    hsv = cv2.cvtColor(crop, cv2.COLOR_RGB2HSV)
    if mode == "color":
        mask = hsv[:, :, 1] > 32
    elif mode == "dark":
        mask = np.max(crop, axis=2) < 155
    elif mode == "shape":
        mask = (hsv[:, :, 1] > 60) | (np.max(crop, axis=2) < 150)
    else:
        raise ValueError(f"Unsupported curve mask: {mode}")
    if mode == "shape":
        contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        filled = np.zeros(mask.shape, np.uint8)
        for contour in contours:
            if cv2.contourArea(contour) > 12:
                cv2.drawContours(filled, [contour], -1, 1, -1)
        mask = filled > 0
    else:
        count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8))
        keep = [i for i in range(1, count) if stats[i, cv2.CC_STAT_AREA] >= 8]
        mask = np.isin(labels, keep)
    crop_path = audit_base.with_suffix(".crop.png")
    Image.fromarray(np.dstack((crop, mask.astype(np.uint8) * 255)), "RGBA").save(crop_path)
    trace_path = audit_base.with_suffix(".trace.svg")
    params = dict(TRACER_DEFAULTS)
    params.update(tracer or {})
    vtracer.convert_image_to_svg_py(str(crop_path), str(trace_path), **params)
    return crop_path, trace_path, len(list(ET.parse(trace_path).getroot().iter(f"{{{SVG}}}path")))


def load_trace(path: Path) -> ET.Element:
    return ET.parse(path).getroot()


def append_children(parent: ET.Element, source: ET.Element) -> None:
    for child in source:
        parent.append(copy.deepcopy(child))


def trace_group(asset: dict[str, Any], trace_root: ET.Element) -> ET.Element:
    bbox = asset["source_bbox"]
    place = asset.get("placement", {})
    x, y = place.get("x", bbox[0]), place.get("y", bbox[1])
    scale = place.get("scale", 1)
    group = ET.Element(f"{{{SVG}}}g", {"id": asset["id"], "transform": f"translate({fmt(x)} {fmt(y)}) scale({fmt(scale)})"})
    append_children(group, trace_root)
    return group


def render_svg(svg_path: Path, output_png: Path, width: int, background: str = "white") -> None:
    _, _, resvg_py, _, _ = _deps()
    output_png.parent.mkdir(parents=True, exist_ok=True)
    output_png.write_bytes(resvg_py.svg_to_bytes(svg_path=str(svg_path), width=width, background=background))


def build_curve_layer(spec: dict[str, Any], cwd: Path, audit_dir: Path):
    root = new_document(spec["canvas"]["width"], spec["canvas"]["height"])
    records, independent = [], []
    for asset in spec.get("curve_assets", []):
        crop, trace, paths = trace_curve(cwd / spec["source"]["image"], asset["source_bbox"], asset.get("mask", "color"), audit_dir / asset["id"], asset.get("tracer"))
        trace_root = load_trace(trace)
        independent_root = new_document(asset["source_bbox"][2], asset["source_bbox"][3])
        append_children(independent_root, trace_root)
        independent_root.set("viewBox", f"0 0 {fmt(asset['source_bbox'][2])} {fmt(asset['source_bbox'][3])}")
        root.append(trace_group(asset, trace_root))
        records.append({"id": asset["id"], "crop": crop.name, "trace": trace.name, "paths": paths})
        independent.append(independent_root)
    return root, records, independent
