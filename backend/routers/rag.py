from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any

from backend.db.database import get_db
from backend.models.feedback import FeedbackItem
from backend.models.episode import RetrievalEpisode
from backend.services.rag.embeddings import embedding_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rag", tags=["RAG"])

def run_reindex_task(db: Session):
    """Background task to re-index all data."""
    try:
        logger.info("Starting background re-indexing...")
        feedback_items = db.query(FeedbackItem).all()
        
        batch_size = 64
        for i in range(0, len(feedback_items), batch_size):
            batch = feedback_items[i:i + batch_size]
            embedding_service.embed_feedback_batch(batch)
            
        episodes = db.query(RetrievalEpisode).all()
        
        for i in range(0, len(episodes), batch_size):
            batch = episodes[i:i + batch_size]
            embedding_service.embed_episode_batch(batch)
            
        logger.info("Background re-indexing complete.")
    except Exception as e:
        logger.error(f"Error during background re-indexing: {e}")

@router.post("/reindex")
def trigger_reindex(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Trigger a full re-indexing of all feedback and episodes in the database.
    Runs in the background.
    """
    background_tasks.add_task(run_reindex_task, db)
    return {"message": "Re-indexing started in the background."}
