# FireKey

This repository contains the FireKey project.

## Features

- Caches API responses per file in `cache/<filename>.json` to avoid redundant
  work.
- Provides a `--force-reprocess` flag that mirrors a "Force Reprocess" UI
  checkbox and bypasses cached results when enabled.
- Retries transient network or API failures up to three times with a mandatory
  three second pause between attempts.
- Logs all processing errors to `logs/firekey-errors.txt`.

## Usage

```bash
python -m firekey path/to/files --force-reprocess
```

When directories are supplied every file in the directory will be processed.
