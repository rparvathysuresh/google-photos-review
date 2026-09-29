import logging
from typing import List, Dict, Any

from sentence_transformers import SentenceTransformer

from backend.config import settings
from backend.db.vector_store import vector_store
from backend.models.feedback import FeedbackItem
from backend.models.episode import RetrievalEpisode

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service to generate and store embeddings."""
    
    def __init__(self):
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        logger.info("Embedding model loaded.")

    def embed_feedback_batch(self, items: List[FeedbackItem]):
        """Generate and store embeddings for a batch of FeedbackItems."""
        if not items:
            return
            
        texts = [item.text for item in items]
        embeddings = self.model.encode(texts, normalize_embeddings=True).tolist()
        
        ids = [item.id for item in items]
        metadatas = []
        for item in items:
            meta = {
                "source": item.source.value if hasattr(item.source, 'value') else item.source,
                "date": item.date.isoformat() if item.date else "",
                "is_relevant": item.is_relevant if item.is_relevant is not None else False
            }
            metadatas.append(meta)
            
        vector_store.add_feedback_embeddings(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
        logger.info(f"Embedded and stored {len(items)} feedback items.")

    def embed_episode_batch(self, episodes: List[RetrievalEpisode]):
        """Generate and store embeddings for a batch of RetrievalEpisodes."""
        if not episodes:
            return
            
        texts = []
        for ep in episodes:
            # Build semantic representation
            clues = ", ".join(ep.remembered_clues) if ep.remembered_clues else "none"
            forgotten = ", ".join(ep.forgotten_info) if ep.forgotten_info else "none"
            failures = ", ".join(ep.failure_reason) if ep.failure_reason else "none"
            methods = ", ".join(ep.retrieval_attempt) if ep.retrieval_attempt else "none"
            
            # Use supporting evidence as primary text context if user_goal is None
            goal_text = ep.supporting_evidence or "Unknown goal"
            
            text = f"Goal/Evidence: {goal_text} | Clues: {clues} | Forgotten: {forgotten} | Methods: {methods} | Failures: {failures}"
            texts.append(text)
            
        embeddings = self.model.encode(texts, normalize_embeddings=True).tolist()
        
        ids = [ep.id for ep in episodes]
        metadatas = []
        for ep in episodes:
            meta = {
                "memory_type": ep.memory_type or "",
                "source": ep.source or "",
                "feedback_item_id": ep.feedback_item_id
            }
            metadatas.append(meta)
            
        vector_store.add_episode_embeddings(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
        logger.info(f"Embedded and stored {len(episodes)} retrieval episodes.")

embedding_service = EmbeddingService()
