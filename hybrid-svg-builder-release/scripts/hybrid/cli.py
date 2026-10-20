from __future__ import annotations

import argparse
import json
from pathlib import Path

from .build import build, package, validate_output
from .schema import validate_spec


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="hybrid-svg")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--image", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("validate-spec")
    p.add_argument("spec", type=Path)
    p = sub.add_parser("build")
    p.add_argument("spec", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--preview-width", type=int, default=2048)
    p = sub.add_parser("validate")
    p.add_argument("output", type=Path)
    p = sub.add_parser("package")
    p.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    if args.command == "prepare":
        from PIL import Image
        image = args.image.resolve()
        if not image.is_file():
            parser.error(f"Image not found: {image}")
        if args.output.exists():
            parser.error(f"Refusing to overwrite: {args.output}")
        with Image.open(image) as im:
            width, height = im.size
        spec = {"schema_version": "1.0", "canvas": {"width": width, "height": height},
                "source": {"image": image.name}, "white_background": True, "layers": [], "curve_assets": []}
        args.output.write_text(json.dumps(spec, indent=2), encoding="utf-8")
        print(args.output)
    elif args.command == "validate-spec":
        validate_spec(json.loads(args.spec.read_text(encoding="utf-8")), source_root=args.spec.parent)
        print("OK")
    elif args.command == "build":
        print(json.dumps(build(args.spec, args.output, preview_width=args.preview_width), indent=2))
    elif args.command == "validate":
        result = validate_output(args.output)
        print(json.dumps(result, indent=2))
        return 0 if result["all_valid"] else 1
    elif args.command == "package":
        print(package(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())