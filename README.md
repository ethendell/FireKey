# FireKey

This repository contains the FireKey project.

## Metadata helper

Use `firekey.metadata.append_metadata` to append rows to the `metadata.csv`
file without overwriting existing entries. The helper automatically inserts the
following columns when the CSV is created:

- `Filename`
- `Title`
- `Description`
- `Keywords`
- `Date processed` (ISO timestamp generated at runtime)
- `Model used`

### Example

```python
from firekey.metadata import append_metadata

append_metadata(
    "metadata.csv",
    filename="example.txt",
    title="Example",
    description="Short description",
    keywords=["demo", "test"],
    model_used="gpt-5-codex",
)
```
