from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber, nltk, random, logging
from gtts import gTTS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("study-backend")

# Ensure NLTK punkt is available without crashing
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    try:
        nltk.download("punkt")
        logger.info("Downloaded NLTK punkt.")
    except Exception as e:
        logger.error(f"Failed to download NLTK punkt: {e}")

app = FastAPI(title="Study Backend", version="1.0.0")

# CORS for Flutter/web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root and health endpoints to avoid 404 confusion
@app.get("/")
def root():
    return {"status": "ok", "message": "Use /docs for API UI."}

@app.get("/health")
def health():
    return {"status": "healthy"}

# Safe PDF text extraction
def read_pdf_bytes(file_bytes: bytes) -> str:
    import io
    text = ""
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
    except Exception as e:
        logger.error(f"PDF read error: {e}")
    return text.strip()

@app.post("/search")
async def search_pdf(file: UploadFile, query: str = Form(...)):
    content = await file.read()
    text = read_pdf_bytes(content)
    if not text:
        return {"results": [], "note": "No readable text found in PDF."}
    try:
        sentences = nltk.sent_tokenize(text) if text else []
    except Exception as e:
        logger.error(f"Tokenize error: {e}")
        sentences = text.split("\n")
    results = [s for s in sentences if query.lower() in s.lower()]
    return {"results": results[:10]}

@app.post("/summarize")
async def summarize_pdf(file: UploadFile):
    content = await file.read()
    text = read_pdf_bytes(content)
    if not text:
        return {"summary": "No content found in PDF."}
    try:
        sentences = nltk.sent_tokenize(text) if text else []
    except Exception as e:
        logger.error(f"Tokenize error: {e}")
        sentences = text.split("\n")
    summary = " ".join(sentences[:5]) if sentences else "No content found in PDF."
    return {"summary": summary}

@app.post("/quiz")
async def generate_quiz(file: UploadFile):
    content = await file.read()
    text = read_pdf_bytes(content)
    if not text:
        return {"quiz": ["No quiz could be generated—PDF had no readable text."]}
    try:
        sentences = nltk.sent_tokenize(text) if text else []
    except Exception as e:
        logger.error(f"Tokenize error: {e}")
        sentences = text.split("\n")
    quiz = []
    for i in range(min(5, len(sentences))):
        words = sentences[i].split()
        if len(words) > 6:
            idx = random.randint(0, len(words) - 1)
            question = " ".join(words[:idx] + ["____"] + words[idx+1:])
            quiz.append({
                "q": question,
                "a": words[idx],
                "tag": random.choice(["Remember", "Apply", "Analyze"])
            })
    return {"quiz": quiz if quiz else ["No quiz could be generated."]}

@app.post("/voice")
async def voice(text: str = Form(...), lang: str = Form("ta")):
    filename = "voice_output.mp3"
    try:
        tts = gTTS(text=text, lang=lang)
        tts.save(filename)
        # Note: Serving static files needs extra setup; for now we return a note.
        return {"audio_url": "/audio/voice_output.mp3", "note": "Static serving not configured on Render."}
    except Exception as e:
        logger.error(f"Voice generation failed: {e}")
        return {"error": f"Voice generation failed: {str(e)}"}
