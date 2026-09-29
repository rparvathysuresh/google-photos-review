"""
Deduplication engine service.
"""

from typing import List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.models.feedback import FeedbackItem
from backend.services.rag.embeddings import embedding_service
import logging

logger = logging.getLogger(__name__)


class DedupEngine:
    """
    Handles deduplication of feedback items by their fingerprints.
    """
    
    def __init__(self, db: Session):
        self.db = db
        
    def filter_duplicates(self, items: List[FeedbackItem]) -> Tuple[List[FeedbackItem], int]:
        """
        Filters a list of FeedbackItems against the database.
        Returns a tuple of (new_items_to_insert, duplicate_count).
        """
        if not items:
            return [], 0
            
        # First, deduplicate within the incoming batch itself
        unique_batch_items = {}
        for item in items:
            if item.fingerprint not in unique_batch_items:
                unique_batch_items[item.fingerprint] = item
                
        batch_duplicates = len(items) - len(unique_batch_items)
        
        # Then, check against the database
        fingerprints_to_check = list(unique_batch_items.keys())
        
        # Query DB for existing fingerprints
        stmt = select(FeedbackItem.fingerprint).where(FeedbackItem.fingerprint.in_(fingerprints_to_check))
        existing_fingerprints = set(self.db.scalars(stmt).all())
        
        # Filter out the existing ones
        new_items = []
        for fingerprint, item in unique_batch_items.items():
            if fingerprint not in existing_fingerprints:
                new_items.append(item)
                
        db_duplicates = len(fingerprints_to_check) - len(new_items)
        total_duplicates = batch_duplicates + db_duplicates
        
        return new_items, total_duplicates

    def save_new_items(self, items: List[FeedbackItem]) -> Tuple[int, int]:
        """
        Deduplicates and saves new items to the database.
        Returns (items_inserted, items_skipped).
        """
        new_items, duplicates = self.filter_duplicates(items)
        
        if new_items:
            self.db.add_all(new_items)
            self.db.commit()
            try:
                embedding_service.embed_feedback_batch(new_items)
            except Exception as e:
                logger.error(f"Failed to auto-index new feedback items: {e}")
            
        return len(new_items), duplicates
