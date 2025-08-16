# PDF → Audiobook Converter (Streamlit, Python 3.9)

Convert any PDF into a natural‑sounding MP3 audiobook. Upload a PDF, pick a voice, preview a sample, and export the full audio.

## Features
- 📄 Upload PDF
- 🧠 Smart text extraction using **PyMuPDF** (keeps headings & paragraphs reasonably intact)
- 🎙️ Voice options: **British Male / British Female / American Male / American Female**
- 🔊 Preview a short sample before exporting
- 💾 Export **MP3** (handles large PDFs using chunking)
- ⏳ Progress indicator during audio generation
- 🧰 Engines:
  - **Google Cloud Text-to-Speech** (recommended, natural male/female voices)
  - **Amazon Polly** (recommended, natural male/female voices)
  - **gTTS** fallback (accent only; male/female not supported by gTTS)

> ⚠️ **FFmpeg is required by pydub**. Install it and ensure it's on your PATH.

## Quick Start (PyCharm / Python 3.9)

1. **Create virtual environment** (recommended)
   ```bash
   python3.9 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install FFmpeg**
   - Windows (winget): `winget install Gyan.FFmpeg`
   - macOS (Homebrew): `brew install ffmpeg`
   - Ubuntu/Debian: `sudo apt-get update && sudo apt-get install -y ffmpeg`

4. **(Recommended) Configure a TTS provider for natural voices**

   ### Option A: Google Cloud Text-to-Speech
   - Create a GCP project and enable **Text-to-Speech API**.
   - Create a service account key (JSON).
   - Set env var in PyCharm run configuration or terminal:
     ```bash
     set GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\key.json    # Windows
     export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json   # macOS/Linux
     ```

   ### Option B: Amazon Polly
   - Configure AWS credentials (IAM user with Polly access):
     - In `~/.aws/credentials` or Env Vars (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`).
   - Make sure your region supports the chosen voices.

   If neither is configured, the app **falls back to gTTS** (accent works; male/female distinction is not available).

5. **Run the app**
   ```bash
   streamlit run app.py
   ```

6. **Usage**
   - Upload a PDF.
   - (Optional) Choose a page range.
   - Select a voice.
   - Click **Extract & Preview** to hear a short sample.
   - Click **Export as MP3** and download the audiobook.

## How it works
- **PyMuPDF** parses the PDF into blocks/lines/spans and uses font-size heuristics to mark headings (`# Title`) and keep paragraph breaks.
- Text is **chunked** (~4,500 chars) to satisfy TTS API limits and manage memory.
- Each chunk is synthesized to **MP3** and concatenated using **pydub**, then exported as a single MP3.

## Troubleshooting
- *pydub or export errors*: Ensure **FFmpeg** is installed and visible on PATH.
- *gTTS only, no male/female*: That's a limitation of gTTS; use Google Cloud TTS or Amazon Polly for voice gender.
- *Polly auth errors*: Verify AWS credentials and region.
- *Google TTS errors*: Verify `GOOGLE_APPLICATION_CREDENTIALS` points to a valid JSON key and API is enabled.
- *Weird reading order*: PDF extraction is heuristic; scanned PDFs or complex layouts may require OCR (e.g., Tesseract) which isn’t included here.

## Optional tweaks
- Adjust chunk size in `split_into_chunks` (default 4500).
- Change Polly voice IDs in `synthesize_polly` if you prefer other timbres.
- Add SSML for prosody control in Google TTS.

---
Built with ❤️ using Streamlit, PyMuPDF, and your TTS engine of choice.
