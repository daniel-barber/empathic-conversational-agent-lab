# backend/chat_routes.py

from dotenv import load_dotenv
load_dotenv()

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .replicate_client_chatbot import ReplicateClientChatbot

app = FastAPI(title="Empathic Chatbot API")

# load token
API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
if not API_TOKEN:
    raise RuntimeError("Missing REPLICATE_API_TOKEN environment variable")

# instantiate your chatbot
chatbot = ReplicateClientChatbot(api_token=API_TOKEN)

class Message(BaseModel):
    text: str

@app.post("/chat")
async def chat(message: Message):
    """
    Accepts JSON { "text": "<user question>" }
    Returns      { "reply": "<assistant answer>" }
    """
    try:
        answer = chatbot.generate_response(message.text)
        return {"reply": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
