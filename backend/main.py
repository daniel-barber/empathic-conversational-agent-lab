# backend/main.py

from fastapi import FastAPI
from backend.api.chat import router as chat_router
from backend.database.db import create_tables

# Create the FastAPI app
app = FastAPI(
    title="Empathic Conversational Agent API",
    description="Backend API for chatbot and evaluation",
    version="0.1.0",
)

# Initialize database tables at startup
@app.on_event("startup")
async def startup_event():
    create_tables()

# Include the chat API routes
app.include_router(chat_router, prefix="/chat", tags=["Chat"])
