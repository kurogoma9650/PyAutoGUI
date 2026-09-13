# Evidence Format

Each run writes to:

```text
artifacts/<application>/<timestamp>_<scenario>_<run-id>/
```

Files:

- `manifest.json`: environment and target metadata.
- `actions.jsonl`: one structured action entry per line.
- `result.json`: final machine-readable status.
- `result.md`: concise human-readable summary.
- `screenshots/*.png`: named checkpoints.

The evidence schema starts at version `1`.
