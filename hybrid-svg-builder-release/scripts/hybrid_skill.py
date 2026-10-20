#!/usr/bin/env python3
"""Run the hybrid SVG builder from a source checkout without installation."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hybrid.cli import main

if __name__ == "__main__":
    raise SystemExit(main())