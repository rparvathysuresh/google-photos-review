"""
Relevance Classifier Service.
Determines if feedback items are actually about photo retrieval.
"""

import logging
import json
from typing import List, Tuple
from sqlalchemy.orm import Session
from groq import Groq

from backend.config import settings
from backend.models.feedback import FeedbackItem, ExtractionStatus

logger = logging.getLogger(__name__)


class RelevanceClassifier:
    """
    Uses Groq LLM to classify whether raw user feedback is relevant
    to the domain of photo retrieval, search, or organization.
    """

    def __init__(self, db: Session):
        self.db = db
        try:
            self.client = Groq(api_key=settings.GROQ_API_KEY)
            self.model = settings.GROQ_MODEL
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            raise

    def build_prompt(self, text: str) -> str:
        """
        Build the classification prompt.
        """
        return f"""You are a research analyst filtering user feedback for a study on "Personal Photo Retrieval".
Your task is to determine if the following user feedback is relevant to our study.

Relevant feedback MUST discuss:
- Searching for, finding, or losing old photos, videos, or screenshots.
- Organizing, tagging, or categorizing photos for the purpose of finding them later.
- Frustrations with search tools, OCR, face recognition, or scrolling endlessly to find a memory.

Irrelevant feedback includes:
- General praise or complaints ("great app", "it crashes", "too expensive").
- Cloud storage space, backup syncing issues, or battery drain.
- Editing photos, filters, or sharing albums with family (unless explicitly related to finding/retrieving).

Respond ONLY with a valid JSON object matching this exact schema:
{{
    "is_relevant": boolean,
    "relevance_score": float (0.0 to 1.0 confidence score),
    "reasoning": "brief 1-sentence explanation"
}}

Feedback to analyze:
\"\"\"
{text}
\"\"\"
"""

    def classify_item(self, item: FeedbackItem) -> bool:
        """
        Classify a single item. Returns True if successful, False if failed.
        """
        try:
            prompt = self.build_prompt(item.text)
            
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a precise classification AI that outputs only raw JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            response_text = completion.choices[0].message.content
            
            try:
                result = json.loads(response_text)
                item.is_relevant = result.get("is_relevant", False)
                item.relevance_score = float(result.get("relevance_score", 0.0))
                
                # If irrelevant, we can mark extraction as completed (or skipped)
                if not item.is_relevant:
                    item.extraction_status = ExtractionStatus.COMPLETED
                else:
                    # Mark as PENDING so the extractor picks it up
                    item.extraction_status = ExtractionStatus.PENDING
                    
                logger.debug(f"Classified item {item.id[:8]} -> Relevant: {item.is_relevant} (Score: {item.relevance_score})")
                return True
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse LLM JSON response for item {item.id}: {e}\nResponse: {response_text}")
                item.extraction_status = ExtractionStatus.FAILED
                return False
                
        except Exception as e:
            logger.error(f"LLM API error during classification for item {item.id}: {e}")
            item.extraction_status = ExtractionStatus.FAILED
            return False

    def process_batch(self, batch_size: int = 10) -> int:
        """
        Process a batch of pending items.
        Returns the number of items successfully classified.
        """
        # Get items that need classification
        items = self.db.query(FeedbackItem).filter(
            FeedbackItem.extraction_status == ExtractionStatus.PENDING,
            FeedbackItem.is_relevant == None
        ).limit(batch_size).all()
        
        if not items:
            return 0
            
        logger.info(f"Classifying relevance for batch of {len(items)} items...")
        
        success_count = 0
        for item in items:
            # Mark processing
            item.extraction_status = ExtractionStatus.PROCESSING
            self.db.commit()
            
            if self.classify_item(item):
                success_count += 1
                
            self.db.commit()
            
        logger.info(f"Successfully classified {success_count}/{len(items)} items.")
        return success_count
