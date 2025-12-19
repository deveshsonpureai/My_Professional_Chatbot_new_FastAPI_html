import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader

# ---- Rate limiting imports (MUST be early) ----
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

load_dotenv()

client = OpenAI()
app = FastAPI()

# ---- Initialize limiter FIRST ----
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "Too many requests. Please slow down."}
    )

# ---- Load documents once at startup ----
def load_pdf(path):
    reader = PdfReader(path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)

linkedin = load_pdf("me/Linkedin_Devesh.pdf")
resume = load_pdf("me/Resume_Devesh.pdf")

with open("me/summary_Devesh.txt", "r", encoding="utf-8") as f:
    summary = f.read()

name = "Devesh Sonpure"

system_prompt = f"""
You are acting as {name}. You are answering questions on {name}'s website,
particularly questions related to {name}'s career, background, skills and experience.
Be professional and engaging.
If you don't know the answer, say so politely.
"""

system_prompt += f"\n\n## Summary:\n{summary}\n\n## LinkedIn Profile:\n{linkedin}\n\n## Resume:\n{resume}\n\n"

# ---- Request schema ----
class ChatRequest(BaseModel):
    message: str

# ---- Serve frontend ----
@app.get("/", response_class=HTMLResponse)
def home():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

# ---- Chat endpoint (NOW SAFE) ----
@app.post("/chat")
@limiter.limit("10/minute")   # ✅ limiter exists now
def chat(request: Request, req: ChatRequest):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=300,     # 🔒 token cap
        temperature=0.6,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": req.message}
        ]
    )
    return {"reply": response.choices[0].message.content}
