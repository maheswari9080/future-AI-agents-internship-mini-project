from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import AIQuestionRequest, AIResponse
from app.services.ollama_service import ask_ai_assistant, check_ollama_status

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


@router.get("/status")
async def get_ai_status():
    """Check availability of local Ollama AI model."""
    return await check_ollama_status()


@router.post("/ask", response_model=AIResponse)
async def ask_question(
    req: AIQuestionRequest,
    db: Session = Depends(get_db)
):
    """
    Inquire about student records using natural language.
    Grounded in database metrics, with safe offline fallback.
    """
    res = await ask_ai_assistant(db, req.question)
    return AIResponse(
        answer=res["answer"],
        source=res.get("source", "deterministic"),
        context_summary=res.get("context_summary"),
    )
