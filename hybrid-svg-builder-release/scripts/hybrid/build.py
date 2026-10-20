from __future__ import annotations

import copy
import json
import shutil
import zipfile
from pathlib import Path
from typing import Any

from .assets import build_curve_layer, render_svg
from .schema import validate_spec
from .svg import ET, element, new_document, render_element


def build(spec_path: Path, output: Path, *, preview_width: int = 2048) -> dict[str, Any]:
    spec_path = spec_path.resolve()
    cwd = spec_path.parent
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    validate_spec(spec, source_root=cwd)
    existed = output.exists()
    if existed and any(output.iterdir()):
        raise FileExistsError(f"Refusing to overwrite non-empty output: {output}")
    output.mkdir(parents=True, exist_ok=True)
    try:
        return _build(spec_path, spec, output, preview_width)
    except Exception:
        if not existed:
            shutil.rmtree(output, ignore_errors=True)
        raise


def _build(spec_path: Path, spec: dict[str, Any], output: Path, preview_width: int) -> dict[str, Any]:
    for name in ("previews", "assets/basic", "assets/curves", "audit"):
        (output / name).mkdir(parents=True, exist_ok=True)
    width, height = spec["canvas"]["width"], spec["canvas"]["height"]
    basic = new_document(width, height)
    for layer in spec["layers"]:
        group = element(basic, "g", id=layer["id"])
        for item in layer["elements"]:
            render_element(group, item)
    curve_layer, curve_records, independent_curves = build_curve_layer(spec, spec_path.parent, output / "audit")
    basic_path = output / "02_basic_shapes_only.svg"
    curves_path = output / "03_curves_at_original_positions.svg"
    combined_path = output / "01_combined_no_text.svg"
    ET.ElementTree(basic).write(basic_path, encoding="utf-8", xml_declaration=True)
    ET.ElementTree(curve_layer).write(curves_path, encoding="utf-8", xml_declaration=True)
    combined = copy.deepcopy(basic)
    if spec.get("white_background", True):
        background = element(combined, "rect", id="00-white-background", x=0, y=0, width=width, height=height, fill="#ffffff", stroke="none", stroke_width=0)
        combined.remove(background)
        combined.insert(0, background)
    for child in curve_layer:
        combined.append(copy.deepcopy(child))
    ET.ElementTree(combined).write(combined_path, encoding="utf-8", xml_declaration=True)
    for layer in spec["layers"]:
        root = new_document(width, height)
        root.append(copy.deepcopy(next(g for g in basic if g.get("id") == layer["id"])))
        ET.ElementTree(root).write(output / "assets/basic" / f"{layer['id']}.svg", encoding="utf-8", xml_declaration=True)
    for asset, root in zip(spec.get("curve_assets", []), independent_curves):
        ET.ElementTree(root).write(output / "assets/curves" / f"{asset['id']}.svg", encoding="utf-8", xml_declaration=True)
    audit = {"canvas": [width, height], "curve_assets": curve_records, "spec": str(spec_path)}
    (output / "audit/build.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "audit/spec.snapshot.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    for name in ("01_combined_no_text", "02_basic_shapes_only", "03_curves_at_original_positions"):
        render_svg(output / f"{name}.svg", output / "previews" / f"{name}.png", preview_width)
    return audit


def validate_output(output: Path) -> dict[str, Any]:
    files = sorted(output.glob("*.svg")) + sorted((output / "assets").rglob("*.svg"))
    results = []
    for path in files:
        root = ET.parse(path).getroot()
        tags = [n.tag.split("}")[-1] for n in root.iter()]
        results.append({"file": str(path.relative_to(output)), "image": tags.count("image"), "text": tags.count("text"), "valid": "image" not in tags and "text" not in tags})
    return {"files": len(files), "all_valid": bool(files) and all(r["valid"] for r in results), "results": results}


def package(output: Path) -> Path:
    archive = output.parent / f"{output.name}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in output.rglob("*"):
            if path.is_file() and (path.parent.name != "audit" or path.suffix == ".json"):
                zf.write(path, Path(output.name) / path.relative_to(output))
    return archive
