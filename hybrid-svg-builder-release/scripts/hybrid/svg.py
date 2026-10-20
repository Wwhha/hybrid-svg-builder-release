from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from typing import Any

from .schema import SpecError

SVG = "http://www.w3.org/2000/svg"
INK = "#17191b"
ET.register_namespace("", SVG)


def qualified(name: str) -> str:
    return f"{{{SVG}}}{name}"


def element(parent: ET.Element, name: str, **attrs: Any) -> ET.Element:
    clean = {k.rstrip("_").replace("_", "-"): str(v) for k, v in attrs.items() if v is not None}
    return ET.SubElement(parent, qualified(name), clean)


def new_document(width: float, height: float) -> ET.Element:
    return ET.Element(qualified("svg"), {
        "width": fmt(width), "height": fmt(height),
        "viewBox": f"0 0 {fmt(width)} {fmt(height)}", "version": "1.1",
    })


def fmt(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def points(values: list[list[float]]) -> str:
    return " ".join(f"{fmt(x)},{fmt(y)}" for x, y in values)


def _style(attrs: dict[str, Any]) -> dict[str, Any]:
    style = attrs.get("style", {})
    return {
        "fill": style.get("fill", "none"),
        "stroke": style.get("stroke", INK),
        "stroke_width": style.get("stroke_width", 1.8),
        "stroke_dasharray": style.get("dasharray"),
    }


def render_element(parent: ET.Element, item: dict[str, Any]) -> ET.Element:
    kind = item["kind"]
    style = _style(item)
    if kind == "rect":
        x, y, w, h = item["bbox"]
        return element(parent, "rect", id=item["id"], x=x, y=y, width=w, height=h,
                       rx=item.get("rx", 0), fill=style["fill"], stroke=style["stroke"],
                       stroke_width=style["stroke_width"], stroke_dasharray=style["stroke_dasharray"])
    if kind == "circle":
        return element(parent, "circle", id=item["id"], cx=item["cx"], cy=item["cy"], r=item["r"],
                       fill=style["fill"], stroke=style["stroke"], stroke_width=style["stroke_width"])
    if kind == "line":
        (x1, y1), (x2, y2) = item["points"]
        return element(parent, "line", id=item["id"], x1=x1, y1=y1, x2=x2, y2=y2,
                       stroke=style["stroke"], stroke_width=style["stroke_width"],
                       stroke_dasharray=style["stroke_dasharray"], stroke_linecap="round")
    if kind == "polyline":
        return element(parent, "polyline", id=item["id"], points=points(item["points"]),
                       fill="none", stroke=style["stroke"], stroke_width=style["stroke_width"],
                       stroke_dasharray=style["stroke_dasharray"], stroke_linejoin="miter")
    if kind == "polygon":
        return element(parent, "polygon", id=item["id"], points=points(item["points"]),
                       fill=style["fill"], stroke=style["stroke"], stroke_width=style["stroke_width"])
    if kind == "cube":
        x, y, w, h = item["bbox"]
        depth = item.get("depth", {})
        dx, dy = float(depth.get("x", 18)), float(depth.get("y", 16))
        faces = item.get("faces", {})
        g = element(parent, "g", id=item["id"])
        element(g, "polygon", points=points([[x, y], [x + dx, y - dy], [x + w + dx, y - dy], [x + w, y]]),
                fill=faces.get("top", "#f0d39b"), stroke=INK, stroke_width=1.7)
        element(g, "polygon", points=points([[x + w, y], [x + w + dx, y - dy], [x + w + dx, y + h - dy], [x + w, y + h]]),
                fill=faces.get("side", "#cba96f"), stroke=INK, stroke_width=1.7)
        element(g, "rect", x=x, y=y, width=w, height=h, fill=faces.get("front", "#e6bb77"),
                stroke=INK, stroke_width=1.8)
        return g
    if kind == "arrow":
        pts = item["points"]
        g = element(parent, "g", id=item["id"])
        if len(pts) == 2:
            element(g, "line", x1=pts[0][0], y1=pts[0][1], x2=pts[1][0], y2=pts[1][1],
                    stroke=style["stroke"], stroke_width=style["stroke_width"], stroke_linecap="round")
        else:
            element(g, "polyline", points=points(pts), fill="none", stroke=style["stroke"],
                    stroke_width=style["stroke_width"], stroke_linejoin="miter")
        x, y = pts[-1]
        a, b = pts[-2]
        dx, dy = x - a, y - b
        length = math.hypot(dx, dy)
        if not length:
            raise SpecError(f"{item['id']}: arrow endpoints must differ")
        ux, uy = dx / length, dy / length
        head = float(item.get("head", 12))
        tri = [[x, y], [x - head * ux + head * .44 * uy, y - head * uy - head * .44 * ux],
               [x - head * ux - head * .44 * uy, y - head * uy + head * .44 * ux]]
        element(g, "polygon", points=points(tri), fill=style["stroke"], stroke="none", stroke_width=0)
        return g
    raise SpecError(f"Unsupported element type {kind}")