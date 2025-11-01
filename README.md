# FireKey

FireKey now ships with lightweight helpers for tracking token usage when calling
language-model APIs. The package centres around the following building blocks:

- `TokenUsageTracker` estimates prompt tokens before each call, tallies actual
  usage, and prints per-file usage/cost lines along with a final run summary.
- `TrackedAPIClient` wraps any callable API client so tracking happens
  automatically without changing the underlying request logic.
- `CSVLogger` can persist the captured metrics and appends a summary comment at
  the bottom of the CSV output.
- `TrackingSession` ties the tracker and logger together, guaranteeing that the
  summary line is printed at the end of each run.

```python
from pathlib import Path

from firekey import (
    CSVLogger,
    TokenUsageTracker,
    TrackingSession,
    TrackedAPIClient,
    default_completion_extractor,
    default_usage_extractor,
)


def send_to_api(*, prompt: str, model: str, **kwargs):
    ...  # call the actual API and return the raw response


def run(files_to_prompts):
    tracker = TokenUsageTracker()
    csv_logger = CSVLogger(Path("reports/usage.csv"))
    client = TrackedAPIClient(send_to_api, tracker, default_model="gpt-4o-mini")

    with TrackingSession(tracker, csv_logger) as session:
        for file_name, prompt in files_to_prompts:
            response, record = client(
                file_name=file_name,
                prompt=prompt,
                completion_text_extractor=default_completion_extractor,
                usage_extractor=default_usage_extractor,
                return_record=True,
            )
            session.record(record)
            # handle `response` as required by your workflow
```

The helper functions in `firekey.demo` showcase the tracker with a deterministic
mock client and can serve as a quick integration reference.
