# app.py
# PDF → Audiobook Converter (No Billing, Python 3.9)
# Uses Edge TTS (free, no API keys) with UK/US male/female voices.
# Requires: streamlit, PyMuPDF, pydub, gTTS, edge-tts, and FFmpeg on PATH.

import io
import asyncio
from typing import List

import streamlit as st
import fitz  # PyMuPDF
from pydub import AudioSegment
from gtts import gTTS
import edge_tts

VOICE_KEYS = ["British Male", "British Female", "American Male", "American Female"]
EDGE_VOICE_MAP = {
    "British Male": "en-GB-RyanNeural",
    "British Female": "en-GB-SoniaNeural",
    "American Male": "en-US-GuyNeural",
    "American Female": "en-US-JennyNeural",
}

st.set_page_config(page_title="PDF → Audiobook Converter", page_icon="🎧", layout="centered")
st.title("🎧 PDF → Audiobook Converter (No Billing)")
st.caption("Edge TTS (UK/US × Male/Female), gTTS fallback. Page range, preview, and MP3 export included.")

# ---------- PDF extraction (preserve headings & paragraphs heuristically) ----------
def extract_text_preserving_structure(pdf_bytes: bytes, page_start: int = None, page_end: int = None) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    n_pages = len(doc)
    if page_start is None:
        page_start = 1
    if page_end is None or page_end > n_pages:
        page_end = n_pages
    page_start = max(1, page_start)
    page_end = max(page_start, min(n_pages, page_end))

    parts: List[str] = []
    for pno in range(page_start - 1, page_end):
        page = doc[pno]
        pdata = page.get_text("dict")

        spansizes = []
        for block in pdata.get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    size = span.get("size", 0)
                    if size:
                        spansizes.append(size)
        header_threshold = (sorted(spansizes)[int(0.75 * len(spansizes))] if spansizes else 16.0)

        page_parts: List[str] = []
        for block in pdata.get("blocks", []):
            text_buf = []
            max_size = 0.0
            for line in block.get("lines", []):
                line_text = "".join(span.get("text", "") for span in line.get("spans", []))
                line_text = line_text.replace("\r", "").strip()
                if line_text:
                    text_buf.append(line_text)
                for span in line.get("spans", []):
                    if span.get("size", 0) > max_size:
                        max_size = span["size"]
            if not text_buf:
                continue

            block_text = " ".join(text_buf).strip()
            if not block_text:
                continue

            if max_size >= header_threshold and len(block_text) <= 120:
                page_parts.append(f"# {block_text}")
            else:
                page_parts.append(block_text)

        parts.append("\n\n".join(page_parts))

    doc.close()
    text = "\n\n".join(parts)
    while "\n\n\n\n" in text:
        text = text.replace("\n\n\n\n", "\n\n\n")
    return text.strip()

# ---------- Chunking ----------
def split_into_chunks(text: str, max_chars: int = 4500) -> List[str]:
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: List[str] = []
    cur = ""
    for p in paras:
        if len(p) > max_chars:
            sentences = p.replace("\n", " ").split(". ")
            for s in sentences:
                s2 = (s + ("" if s.endswith(".") else ".")).strip()
                if len(cur) + 1 + len(s2) > max_chars:
                    if cur:
                        chunks.append(cur.strip())
                    cur = s2
                else:
                    cur = (cur + " " + s2).strip()
        else:
            if len(cur) + 2 + len(p) > max_chars:
                if cur:
                    chunks.append(cur.strip())
                cur = p
            else:
                cur = (cur + "\n\n" + p).strip() if cur else p
    if cur:
        chunks.append(cur.strip())
    return chunks

# ---------- TTS (Edge TTS primary, gTTS fallback) ----------
async def synthesize_edge_async(text: str, voice_key: str) -> bytes:
    voice = EDGE_VOICE_MAP.get(voice_key, "en-US-JennyNeural")
    communicate = edge_tts.Communicate(text=text, voice=voice, rate="+0%", pitch="+0Hz")
    out = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            out.write(chunk["data"])
    return out.getvalue()

def synthesize_gtts(text: str, voice_key: str) -> bytes:
    tld = "co.uk" if "British" in voice_key else "com"
    tts = gTTS(text=text, lang="en", tld=tld, slow=False)
    bio = io.BytesIO()
    tts.write_to_fp(bio)
    bio.seek(0)
    return bio.read()

def synthesize_segment_to_audiosegment(text: str, voice_key: str) -> AudioSegment:
    try:
        audio_bytes = asyncio.run(synthesize_edge_async(text, voice_key))
        return AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
    except Exception as e:
        try:
            audio_bytes = synthesize_gtts(text, voice_key)
            return AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
        except Exception as e2:
            raise RuntimeError(f"All TTS engines failed: Edge TTS error={e}; gTTS error={e2}")

# ---------- UI ----------
uploaded = st.file_uploader("Upload a PDF file", type=["pdf"])
voice = st.selectbox("Choose Voice", VOICE_KEYS, index=1)

page_range_opt = st.checkbox("Select a page range (optional)")
start_page = end_page = None
if uploaded:
    try:
        tmp_doc = fitz.open(stream=uploaded.read(), filetype="pdf")
        total_pages = len(tmp_doc)
        tmp_doc.close()
        uploaded.seek(0)
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        total_pages = None

    if total_pages:
        st.caption(f"Total pages: {total_pages}")
        if page_range_opt:
            c1, c2 = st.columns(2)
            with c1:
                start_page = st.number_input("Start page (1-based)", min_value=1, max_value=total_pages, value=1, step=1)
            with c2:
                end_page = st.number_input("End page (inclusive)", min_value=1, max_value=total_pages, value=total_pages, step=1)
            if end_page < start_page:
                st.warning("End page is before start page. Adjusting to match start page.")
                end_page = start_page

c1, c2 = st.columns(2)
do_extract = c1.button("Extract & Preview")
do_export = c2.button("Export as MP3")

if "extracted_text" not in st.session_state:
    st.session_state["extracted_text"] = ""
if "preview_audio" not in st.session_state:
    st.session_state["preview_audio"] = None
if "full_audio" not in st.session_state:
    st.session_state["full_audio"] = None

def show_engine_banner():
    st.success("Using **Edge TTS** by default (no billing). Fallback: gTTS. Ensure FFmpeg is installed for MP3 export.")

if do_extract:
    if not uploaded:
        st.error("Please upload a PDF first.")
    else:
        show_engine_banner()
        pdf_bytes = uploaded.read()
        uploaded.seek(0)
        with st.spinner("Extracting text..."):
            text = extract_text_preserving_structure(pdf_bytes, start_page, end_page)
            st.session_state["extracted_text"] = text

        if not text.strip():
            st.error("No extractable text found in the selected pages.")
        else:
            st.success("Text extracted! Generating preview...")
            preview_text = text[:1500]
            try:
                seg = synthesize_segment_to_audiosegment(preview_text, voice)
                bio = io.BytesIO()
                seg.export(bio, format="mp3", bitrate="192k")
                bio.seek(0)
                st.session_state["preview_audio"] = bio.read()
                st.audio(st.session_state["preview_audio"], format="audio/mp3")
                st.caption("Preview generated from the first part of your document.")
            except Exception as e:
                st.error(f"TTS preview failed: {e}")

if do_export:
    if not st.session_state["extracted_text"]:
        st.error("Please run **Extract & Preview** first.")
    else:
        show_engine_banner()
        text = st.session_state["extracted_text"]
        chunks = split_into_chunks(text, max_chars=4500)

        progress = st.progress(0)
        status = st.empty()
        combined = AudioSegment.silent(duration=0)

        for i, ch in enumerate(chunks, start=1):
            status.text(f"Generating audio {i}/{len(chunks)}...")
            try:
                seg = synthesize_segment_to_audiosegment(ch, voice)
            except Exception as e:
                st.error(f"TTS failed on chunk {i}: {e}")
                break
            combined += seg
            progress.progress(int(i * 100 / len(chunks)))

        if len(combined) > 0:
            filename = (uploaded.name.rsplit(".", 1)[0] if uploaded else "audiobook") + ".mp3"
            bio = io.BytesIO()
            combined.export(bio, format="mp3", bitrate="192k")
            bio.seek(0)
            st.session_state["full_audio"] = bio.read()
            st.success("Audiobook ready!")
            st.download_button("⬇️ Download MP3", data=st.session_state["full_audio"], file_name=filename, mime="audio/mpeg")
            st.caption("Tip: If export fails, ensure FFmpeg is installed and on your PATH.")
