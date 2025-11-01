# FireKey

FireKey provides a small desktop utility that exports metadata in multiple formats for delivery to downstream tooling.

## Features

- Export metadata as CSV, JSON, or XML (CSV exports automatically create a timestamped directory under `exports/`).
- Generate a `summary.json` file that captures total files, model, token usage, and cost for each CSV export.
- Optionally copy poster frames referenced in the metadata into the export package.
- Quickly open the most recent export folder or copy the CSV path for drag-and-drop workflows.

## Running the app

```bash
python -m firekey.gui
```

A curated data set is bundled with the repository. Modify `data/sample_metadata.json` to integrate with your own pipeline.

## Running tests

```bash
pytest
```
