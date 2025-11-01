# FireKey

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
