from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber, nltk, random
from gtts import gTTS

# Ensure NLTK punkt tokenizer is available
nltk.download('punkt')

app = FastAPI()

# Allow cross-origin requests (important for Flutter app connection)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper function to safely read PDF content
def read_pdf_bytes(file_bytes: bytes) -> str:
    import io
    text = ""
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:  # Only add if text exists
                    text += t + "\n"
    except Exception as e:
        print("PDF read error:", e)
    return text.strip()

# Endpoint: Search for query in PDF
@app.post("/search")
async def search_pdf(file: UploadFile, query: str = Form(...)):
    content = await file.read()
    text = read_pdf_bytes(content)
    sentences = nltk.sent_tokenize(text) if text else []
    results = [s for s in sentences if query.lower() in s.lower()]
    return {"results": results[:10]}

# Endpoint: Summarize PDF
@app.post("/summarize")
async def summarize_pdf(file: UploadFile):
    content = await file.read()
    text = read_pdf_bytes(content)
    sentences = nltk.sent_tokenize(text) if text else []
    summary = " ".join(sentences[:5]) if sentences else "No content found in PDF."
    return {"summary": summary}

# Endpoint: Generate quiz from PDF
@app.post("/quiz")
async def generate_quiz(file: UploadFile):
    content = await file.read()
    text = read_pdf_bytes(content)
    sentences = nltk.sent_tokenize(text) if text else []
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

# Endpoint: Convert text to voice (Tamil default)
@app.post("/voice")
async def voice(text: str = Form(...), lang: str = Form("ta")):
    filename = "voice_output.mp3"
    try:
        tts = gTTS(text=text, lang=lang)
        tts.save(filename)
        return {"audio_url": "/audio/voice_output.mp3"}
    except Exception as e:
        return {"error": f"Voice generation failed: {str(e)}"}
