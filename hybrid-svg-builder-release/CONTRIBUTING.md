# Contributing

Run tests before proposing changes:

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

Keep generated diagrams out of commits. Add a test fixture only when it is synthetic, small, and free of third-party artwork. Preserve the architecture: explicit authoring specification, deterministic simple-shape output, tightly scoped curve tracing, and no generated text.