from __future__ import annotations

import re
from pathlib import Path
from typing import Any

ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


class SpecError(ValueError):
    pass


def _fail(message: str) -> None:
    raise SpecError(message)


def _number(value: Any, where: str, *, low: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail(f"{where}: expected a number")
    if value != value or value in (float("inf"), float("-inf")):
        _fail(f"{where}: finite number required")
    if low is not None and value < low:
        _fail(f"{where}: must be >= {low}")
    return float(value)


def _color(value: Any, where: str) -> str:
    if value == "none":
        return value
    if not isinstance(value, str) or not HEX_RE.fullmatch(value):
        _fail(f"{where}: use #RRGGBB or 'none'")
    return value


def _bbox(value: Any, where: str, width: float, height: float) -> list[float]:
    if not isinstance(value, list) or len(value) != 4:
        _fail(f"{where}: expected [x, y, width, height]")
    x, y, w, h = (_number(v, where) for v in value)
    if w <= 0 or h <= 0 or x < 0 or y < 0 or x + w > width or y + h > height:
        _fail(f"{where}: outside the canvas")
    return [x, y, w, h]


def _points(value: Any, where: str, width: float, height: float) -> list[list[float]]:
    if not isinstance(value, list) or len(value) < 2:
        _fail(f"{where}: expected at least two [x, y] points")
    result = []
    for point in value:
        if not isinstance(point, list) or len(point) != 2:
            _fail(f"{where}: each point must be [x, y]")
        x, y = _number(point[0], where), _number(point[1], where)
        if not 0 <= x <= width or not 0 <= y <= height:
            _fail(f"{where}: point outside the canvas")
        result.append([x, y])
    return result


def _id(value: Any, where: str, seen: set[str]) -> str:
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        _fail(f"{where}: use 1-64 letters, digits, dot, underscore or hyphen")
    if value in seen:
        _fail(f"{where}: duplicate id {value!r}")
    seen.add(value)
    return value


def validate_spec(data: dict[str, Any], *, source_root: Path | None = None) -> dict[str, Any]:
    if not isinstance(data, dict) or data.get("schema_version") != "1.0":
        _fail("schema_version must be '1.0'")
    canvas = data.get("canvas")
    if not isinstance(canvas, dict):
        _fail("canvas is required")
    width = _number(canvas.get("width"), "canvas.width", low=1)
    height = _number(canvas.get("height"), "canvas.height", low=1)
    source = data.get("source")
    if not isinstance(source, dict) or not isinstance(source.get("image"), str):
        _fail("source.image is required")
    if source_root and not (source_root / source["image"]).is_file():
        _fail(f"source.image not found: {source_root / source['image']}")
    seen: set[str] = set()
    layers = data.get("layers")
    if not isinstance(layers, list) or not layers:
        _fail("layers must be a non-empty array")
    for li, layer in enumerate(layers):
        where = f"layers[{li}]"
        if not isinstance(layer, dict):
            _fail(f"{where}: expected an object")
        _id(layer.get("id"), f"{where}.id", seen)
        elements = layer.get("elements")
        if not isinstance(elements, list) or not elements:
            _fail(f"{where}.elements must be a non-empty array")
        for ei, element in enumerate(elements):
            ew = f"{where}.elements[{ei}]"
            if not isinstance(element, dict):
                _fail(f"{ew}: expected an object")
            kind = element.get("kind")
            if kind not in {"rect", "circle", "line", "polyline", "polygon", "cube", "arrow"}:
                _fail(f"{ew}.kind: unsupported {kind!r}")
            _id(element.get("id"), f"{ew}.id", seen)
            style = element.get("style", {})
            if not isinstance(style, dict):
                _fail(f"{ew}.style: expected an object")
            if "fill" in style:
                _color(style["fill"], f"{ew}.style.fill")
            if "stroke" in style:
                _color(style["stroke"], f"{ew}.style.stroke")
            if "stroke_width" in style:
                _number(style["stroke_width"], f"{ew}.style.stroke_width", low=0)
            if kind in {"rect", "cube"}:
                _bbox(element.get("bbox"), f"{ew}.bbox", width, height)
                if kind == "rect" and element.get("rx") is not None:
                    _number(element["rx"], f"{ew}.rx", low=0)
            elif kind == "circle":
                cx = _number(element.get("cx"), f"{ew}.cx")
                cy = _number(element.get("cy"), f"{ew}.cy")
                r = _number(element.get("r"), f"{ew}.r", low=0)
                if not (0 <= cx - r and cx + r <= width and 0 <= cy - r and cy + r <= height):
                    _fail(f"{ew}: circle outside the canvas")
            else:
                _points(element.get("points"), f"{ew}.points", width, height)
                if kind == "arrow":
                    _number(element.get("head", 12), f"{ew}.head", low=1)
    assets = data.get("curve_assets", [])
    if not isinstance(assets, list):
        _fail("curve_assets must be an array")
    for ai, asset in enumerate(assets):
        aw = f"curve_assets[{ai}]"
        _id(asset.get("id"), f"{aw}.id", seen)
        _bbox(asset.get("source_bbox"), f"{aw}.source_bbox", width, height)
        place = asset.get("placement", {})
        if not isinstance(place, dict):
            _fail(f"{aw}.placement: expected an object")
        x = _number(place.get("x"), f"{aw}.placement.x")
        y = _number(place.get("y"), f"{aw}.placement.y")
        scale = _number(place.get("scale", 1), f"{aw}.placement.scale", low=0.001)
        w, h = asset["source_bbox"][2] * scale, asset["source_bbox"][3] * scale
        if x < 0 or y < 0 or x + w > width or y + h > height:
            _fail(f"{aw}.placement: outside the canvas")
        mode = asset.get("mask", "color")
        if mode not in {"color", "dark", "shape"}:
            _fail(f"{aw}.mask: expected color, dark or shape")
        if "tracer" in asset and not isinstance(asset["tracer"], dict):
            _fail(f"{aw}.tracer: expected an object")
    return data