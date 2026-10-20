from __future__ import annotations

import json
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from hybrid.build import build, package, validate_output
from hybrid.schema import SpecError, validate_spec


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.work = Path(self.temp.name)
        self.image = self.work / "image.png"
        from PIL import Image, ImageDraw
        bitmap = Image.new("RGB", (300, 200), "white")
        draw = ImageDraw.Draw(bitmap)
        draw.line([(220, 80), (240, 50), (260, 80)], fill="black", width=4)
        bitmap.save(self.image)
        self.spec = {
            "schema_version": "1.0",
            "canvas": {"width": 300, "height": 200},
            "source": {"image": self.image.name},
            "white_background": True,
            "layers": [{"id": "01-panel", "elements": [
                {"id": "panel", "kind": "rect", "bbox": [20, 20, 120, 60], "rx": 8,
                 "style": {"fill": "#dce8f7", "stroke": "#4f78a5", "stroke_width": 2, "dasharray": "5 4"}},
                {"id": "cube", "kind": "cube", "bbox": [70, 40, 25, 20],
                 "depth": {"x": 8, "y": 7}, "faces": {"front": "#4c86c8", "top": "#79a8d9", "side": "#386fae"}}
            ]}],
            "curve_assets": [{"id": "curve", "source_bbox": [210, 40, 70, 50],
                              "placement": {"x": 210, "y": 40, "scale": 1}, "mask": "dark"}]
        }
        self.spec_path = self.work / "figure.spec.json"
        self.spec_path.write_text(json.dumps(self.spec), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_full_build_and_validation(self):
        output = self.work / "output"
        audit = build(self.spec_path, output, preview_width=300)
        self.assertEqual(len(audit["curve_assets"]), 1)
        result = validate_output(output)
        self.assertTrue(result["all_valid"])
        self.assertGreaterEqual(result["files"], 4)
        for path in output.rglob("*.svg"):
            tags = [item.tag.split("}")[-1] for item in ET.parse(path).getroot().iter()]
            self.assertNotIn("image", tags)
            self.assertNotIn("text", tags)
        archive = package(output)
        self.assertTrue(archive.is_file())
        self.assertGreater(archive.stat().st_size, 0)

    def test_rejects_invalid_geometry(self):
        self.spec["layers"][0]["elements"][0]["bbox"] = [280, 20, 50, 60]
        self.spec_path.write_text(json.dumps(self.spec), encoding="utf-8")
        with self.assertRaises(SpecError):
            validate_spec(self.spec, source_root=self.work)
        output = self.work / "failed"
        with self.assertRaises(SpecError):
            build(self.spec_path, output)
        self.assertFalse(output.exists())

    def test_rejects_nonempty_output(self):
        output = self.work / "existing"
        output.mkdir()
        (output / "keep.txt").write_text("keep", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            build(self.spec_path, output)
        self.assertTrue((output / "keep.txt").is_file())


class RegressionFixtureTests(unittest.TestCase):
    def test_diesel_framework_fixture(self):
        fixture = ROOT / "tests" / "fixtures" / "diesel_framework.jpg"
        spec = ROOT / "examples" / "diesel-framework" / "diesel-framework.spec.json"
        if not fixture.is_file():
            self.skipTest("Local rights-unverified fixture excluded from Git")
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            image = work / "figure.jpg"
            image.write_bytes(fixture.read_bytes())
            data = json.loads(spec.read_text(encoding="utf-8"))
            data["source"]["image"] = image.name
            local_spec = work / "diesel.spec.json"
            local_spec.write_text(json.dumps(data), encoding="utf-8")
            output = work / "output"
            build(local_spec, output, preview_width=1024)
            result = validate_output(output)
            self.assertTrue(result["all_valid"])
            self.assertEqual(result["files"], 23)

if __name__ == "__main__":
    unittest.main()