from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, Dict, Any
from pydantic import BaseModel

from backend.services.rag.query_engine import query_engine, AnswerResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ask", tags=["RAG"])

class AskRequest(BaseModel):
    question: str
    filters: Optional[Dict[str, Any]] = None

@router.post("/", response_model=AnswerResponse)
def ask_question(request: AskRequest):
    """
    Ask a question against the retrieved evidence database.
    Returns a grounded answer with citations.
    """
    try:
        response = query_engine.ask(request.question, request.filters)
        return response
    except Exception as e:
        logger.error(f"Error answering question '{request.question}': {e}")
        raise HTTPException(status_code=500, detail="Failed to generate answer.")
