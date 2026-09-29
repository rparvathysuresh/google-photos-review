import logging
from backend.db.database import SessionLocal
from backend.models.feedback import FeedbackItem
from backend.models.episode import RetrievalEpisode
from backend.services.rag.embeddings import embedding_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_bulk_indexing():
    db = SessionLocal()
    
    logger.info("Starting bulk embedding of FeedbackItems...")
    # Process FeedbackItems in batches of 64
    batch_size = 64
    feedback_items = db.query(FeedbackItem).all()
    
    for i in range(0, len(feedback_items), batch_size):
        batch = feedback_items[i:i + batch_size]
        embedding_service.embed_feedback_batch(batch)
        
    logger.info("Starting bulk embedding of RetrievalEpisodes...")
    episodes = db.query(RetrievalEpisode).all()
    
    for i in range(0, len(episodes), batch_size):
        batch = episodes[i:i + batch_size]
        embedding_service.embed_episode_batch(batch)
        
    logger.info("Bulk indexing complete!")

if __name__ == "__main__":
    run_bulk_indexing()
