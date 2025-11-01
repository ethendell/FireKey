# FireKey

FireKEY is a Tkinter-based desktop application that generates stock photo metadata using OpenAI's API.

## Requirements

- Python 3.10+
- OpenAI API key available as the `OPENAI_API_KEY` environment variable

Install dependencies:

```bash
pip install openai pillow opencv-python pandas tkinter
```

## Usage

```bash
python firekey_app.py
```

1. Launch the application and click **Browse** to choose a folder containing images.
2. Press **Process Folder** to send each image to the OpenAI API for metadata generation.
3. A `metadata.csv` file will be created inside the selected folder when processing completes.
