# PDF to Audiobook Converter 

A Streamlit app to convert PDFs into natural-sounding MP3 audiobooks. No billing or API keys are required. Edge TTS provides UK/US male/female neural voices; gTTS is the fallback.

## Features
- Upload PDF
- Optional page range
- Structure-aware extraction (headings and paragraphs preserved heuristically)
- Voice options:
  - British Male (`en-GB-RyanNeural`)
  - British Female (`en-GB-SoniaNeural`)
  - American Male (`en-US-GuyNeural`)
  - American Female (`en-US-JennyNeural`)
- Voice sample preview
- Extract & Preview (short audio from the document)
- Export full audiobook as MP3 with progress
- Chunked text processing to handle large PDFs

## Requirements
- Python 3.9
- FFmpeg on PATH (required by `pydub`)

## Installation
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

python -m pip install --upgrade pip wheel setuptools
pip install streamlit PyMuPDF gTTS pydub edge-tts
