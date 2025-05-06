# backend/api/chat.py

from fastapi import APIRouter
from pydantic import BaseModel
from backend.database.db import insert_chat_pair

router = APIRouter()

# Updated ChatInput model to match frontend
class ChatInput(BaseModel):
    chat_id: str
    pair_number: int
    user_input: str
    llm_response: str

@router.post("/")
async def chat_endpoint(data: ChatInput):
    # Save the user input and LLM response into the database
    insert_chat_pair(
        chat_id=data.chat_id,
        pair_number=data.pair_number,
        user_input=data.user_input,
        llm_response=data.llm_response
    )
    return {"status": "saved", "chat_id": data.chat_id, "pair_number": data.pair_number}
