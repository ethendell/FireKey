# FireKey

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
