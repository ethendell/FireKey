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
FireKEY is a lightweight desktop application that helps build consistent prompts and metadata for stock submissions.

## Features

- Modular prompt templates stored in the `prompts/` directory. Every `.txt` file contains JSON with a template name, system prompt, and user prompt copy.
- Graphical interface for choosing a template, selecting whether you are working on a photo or video, and providing contextual information.
- Automatic placeholder substitution for `{type}` and `{context}` when you process the prompt.
- Persists the last template you used to `config.json` so you can pick up where you left off.

## Getting Started

1. Ensure you have Python 3.9 or newer available. The application uses Tkinter, which ships with the standard Python distribution.
2. Install dependencies (none beyond the standard library are required).
3. Add or edit prompt templates inside the `prompts/` directory. Use the structure below:

   ```json
   {
     "name": "My Template",
     "system_prompt": "Instructions for the assistant...",
     "user_prompt": "The prompt text that can use {type} and {context}."
   }
   ```

4. Run the application:

   ```bash
   python app.py
   ```

5. Choose a template from the **Prompt Template** dropdown, select a content type, add context, and click **Process** to generate the final prompts.

## Configuration

The application stores the last template you selected in `config.json`. You can delete this file at any time to reset the preference.

## Adding New Templates

To add new behavior, simply drop another `.txt` file in the `prompts/` directory that follows the JSON structure above. The app automatically detects it the next time you launch FireKEY.
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
FireKey is a Tkinter desktop application that helps photographers craft prompts for OpenAI models. It now supports reusable **context profiles** so you can quickly switch between styles such as food, portraits, or landscapes.

## Features

- Manage reusable context profiles stored in `profiles/*.json`.
- Merge profile context with user-provided details before sending it to OpenAI.
- Edit, add, and delete profiles from an in-app manager dialog.

## Getting started

1. (Optional) Create a virtual environment and activate it.
2. Install dependencies:
   ```bash
   pip install openai
   ```
3. Set the `OPENAI_API_KEY` environment variable.
4. Launch FireKey:
   ```bash
   python main.py
   ```

## Profiles

Profiles are stored as JSON files inside the `profiles/` directory. Each file must contain the following shape:

```json
{
  "name": "Food Photography",
  "context": "Describe food dishes, table setup, lighting, and ingredients."
}
```

Add new JSON files manually or use **Manage Profiles** inside the app to create, edit, or delete entries.
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
## Configuration

FireKey now keeps its settings in a `config.json` file. When the
application starts it will:

1. Look for an existing `config.json` (either in the current directory or
   the location provided via `FIREKEY_CONFIG_PATH`).
2. Create one with sensible defaults if it does not already exist.
3. Prompt you to enter your API key if the stored value is blank.

The default configuration looks like:

```json
{
  "api_key": "",
  "default_model": "gpt-4o-mini",
  "default_creativity": 0.4
}
```

## Usage

Run the CLI entry point to ensure your configuration is set up:

```bash
python -m firekey
```

Pass `--show` to display the loaded configuration (with the API key
masked) or `--config` to point to a custom configuration file.
