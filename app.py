import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
from fastapi.responses import HTMLResponse   

load_dotenv()

client = OpenAI()
app = FastAPI()

# Load documents once at startup
def load_pdf(path):
    reader = PdfReader(path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)

linkedin = load_pdf("me/Linkedin_Devesh.pdf")
resume = load_pdf("me/Resume_Devesh.pdf")

with open("me/summary_Devesh.txt", "r", encoding="utf-8") as f:
    summary = f.read()


name = "Devesh Sonpure"
system_prompt = f"You are acting as {name}. You are answering questions on {name}'s website, \
particularly questions related to {name}'s career, background, skills and experience. \
Your responsibility is to represent {name} for interactions on the website as faithfully as possible. \
You are given a summary of {name}'s background and LinkedIn profile and {name}'s resume which you can use to answer questions. \
Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
If you don't know the answer, say so. Make sure all your answers are strictly within the scope of professional details only. \
All the answers related to experience should be strictly from the job experience mentioned in these resources only. \
if you do not get the required information within the provided resources, politely inform that you are not sure about it."

system_prompt += f"\n\n## Summary:\n{summary}\n\n## LinkedIn Profile:\n{linkedin}\n\n## Resume:\n{resume}\n\n"

system_prompt += f"With this context, please chat with the user, always staying in character as {name}."



class ChatRequest(BaseModel):
    message: str


# ---- Serve frontend ----
@app.get("/", response_class=HTMLResponse)
def home():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/chat")
def chat(req: ChatRequest):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": req.message}
        ]
    )
    return {"reply": response.choices[0].message.content}
