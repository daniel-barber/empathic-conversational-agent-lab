# backend/api/chat.py

from fastapi import APIRouter
from pydantic import BaseModel
from backend.database.db import insert_chat_pair
from backend.database.db import insert_chat_pair, get_active_prompt_id
from typing import Optional


router = APIRouter()

# Updated ChatInput model to match frontend
class ChatInput(BaseModel):
    chat_id: str
    pair_number: int
    user_input: str
    llm_response: str
    prompt_id: Optional[int] = None

@router.post("/")
async def chat_endpoint(data: ChatInput):
    prompt_id = data.prompt_id or get_active_prompt_id()
    # Save the user input and LLM response into the database
    insert_chat_pair(
        chat_id=data.chat_id,
        pair_number=data.pair_number,
        user_input=data.user_input,
        llm_response=data.llm_response,
        prompt_id    = prompt_id

    )
    return {
        "status": "saved",
        "chat_id": data.chat_id,
        "pair_number": data.pair_number,
        "prompt_id": prompt_id
    }