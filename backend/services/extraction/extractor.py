"""
Structured Extractor Service.
Extracts retrieval episodes from relevant feedback items using Groq.
"""

import logging
import json
import time
from typing import List, Optional
from sqlalchemy.orm import Session
from groq import Groq

from backend.config import settings
from backend.models.feedback import FeedbackItem, ExtractionStatus
from backend.models.episode import RetrievalEpisode
from backend.services.extraction.prompts import get_extraction_messages
from backend.services.rag.embeddings import embedding_service

logger = logging.getLogger(__name__)


class EpisodeExtractor:
    """
    Uses Groq LLM to extract structured RetrievalEpisode records
    from FeedbackItem text.
    """

    def __init__(self, db: Session):
        self.db = db
        try:
            self.client = Groq(api_key=settings.GROQ_API_KEY)
            self.model = settings.GROQ_MODEL
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            raise

    def extract_episodes(self, item: FeedbackItem) -> bool:
        """
        Extract episodes from a single feedback item.
        Returns True if successful, False if failed.
        """
        try:
            messages = get_extraction_messages(item.text)
            
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.0,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            response_text = completion.choices[0].message.content
            
            try:
                result = json.loads(response_text)
                episodes_data = result.get("episodes", [])
                
                # Create ORM objects
                episodes = []
                for ep_data in episodes_data:
                    episode = RetrievalEpisode(
                        feedback_item_id=item.id,
                        source=item.source.value if hasattr(item.source, 'value') else item.source,
                        source_url=item.source_url,
                        memory_type=ep_data.get("memory_type"),
                        remembered_clues=ep_data.get("remembered_clues", []),
                        forgotten_info=ep_data.get("forgotten_info", []),
                        retrieval_attempt=ep_data.get("retrieval_method", []),
                        failure_reason=[ep_data.get("failure_reason")] if ep_data.get("failure_reason") else [],
                        supporting_evidence=ep_data.get("evidence_quote")
                    )
                    episodes.append(episode)
                
                if episodes:
                    self.db.add_all(episodes)
                    # Hook to auto-index new episodes
                    try:
                        embedding_service.embed_episode_batch(episodes)
                    except Exception as e:
                        logger.error(f"Failed to auto-index episodes: {e}")
                    
                item.extraction_status = ExtractionStatus.COMPLETED
                logger.debug(f"Extracted {len(episodes)} episodes from item {item.id[:8]}")
                return True
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse LLM JSON response for extraction item {item.id}: {e}\nResponse: {response_text}")
                item.extraction_status = ExtractionStatus.FAILED
                return False
                
        except Exception as e:
            logger.error(f"LLM API error during extraction for item {item.id}: {e}")
            return False

    def process_batch(self, batch_size: int = 10, max_retries: int = 3) -> int:
        """
        Process a batch of relevant, pending/failed items with retries.
        """
        items = self.db.query(FeedbackItem).filter(
            # Only process relevant items that are still pending, or failed ones for retry
            FeedbackItem.is_relevant == True,
            FeedbackItem.extraction_status.in_([ExtractionStatus.PENDING, ExtractionStatus.FAILED])
        ).limit(batch_size).all()
        
        if not items:
            return 0
            
        logger.info(f"Extracting episodes for batch of {len(items)} items...")
        
        success_count = 0
        for item in items:
            # Mark processing
            item.extraction_status = ExtractionStatus.PROCESSING
            self.db.commit()
            
            retries = 0
            success = False
            while retries < max_retries and not success:
                success = self.extract_episodes(item)
                if not success:
                    retries += 1
                    if retries < max_retries:
                        logger.warning(f"Retrying extraction for item {item.id} (attempt {retries + 1}/{max_retries})")
                        time.sleep(2 ** retries) # Exponential backoff
                        
            if not success:
                logger.error(f"Failed to extract item {item.id} after {max_retries} attempts.")
                item.extraction_status = ExtractionStatus.FAILED
            else:
                success_count += 1
                
            self.db.commit()
            
        logger.info(f"Successfully extracted episodes for {success_count}/{len(items)} items.")
        return success_count
