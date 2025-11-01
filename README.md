# FireKey

This repository contains the FireKey project.

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
