"""
Google Play Store ingestion adapter.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from google_play_scraper import reviews, Sort

from backend.config import settings
from backend.models.feedback import FeedbackItem, SourceType, ExtractionStatus
from backend.services.ingestion.base_adapter import BaseAdapter

logger = logging.getLogger(__name__)


class PlayStoreAdapter(BaseAdapter):
    """
    Adapter for scraping Google Photos reviews from the Google Play Store.
    """

    def fetch_data(
        self, 
        app_id: str = "com.google.android.apps.photos", 
        limit: int = 200, 
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Fetch reviews from the Play Store.
        Filters for reviews mentioning search-related keywords.
        """
        raw_items = []
        try:
            logger.info(f"Fetching {limit} reviews for {app_id} from Play Store...")
            
            # Fetch reviews. We use Sort.NEWEST to get the latest, 
            # though Sort.MOST_RELEVANT is also an option.
            result, continuation_token = reviews(
                app_id,
                lang=settings.PLAYSTORE_LANG,
                country='us',
                sort=Sort.NEWEST,
                count=limit
            )
            
            # Keywords related to photo retrieval
            keywords = ['search', 'find', 'retrieve', 'look for', 'missing', 'lost', 'organize', 'ocr', 'recognize']
            
            for review in result:
                content = review.get('content', '').lower()
                
                # Check if any keyword is in the review content
                if any(kw in content for kw in keywords):
                    raw_items.append(review)
                    
        except Exception as e:
            logger.error(f"Play Store scraping error: {e}")
            raise ValueError(f"Play Store scraping error: {e}")
            
        logger.info(f"Fetched {len(result)} total reviews, found {len(raw_items)} relevant to retrieval.")
        return raw_items

    def parse(self, raw_data: List[Dict[str, Any]]) -> List[FeedbackItem]:
        """
        Map Play Store review dictionaries to FeedbackItem instances.
        """
        items = []
        for raw in raw_data:
            text = raw.get("content", "").strip()
            if not text:
                continue
                
            date_val = None
            if raw.get("at"):
                # google-play-scraper returns a datetime object
                date_val = raw["at"]
                if date_val.tzinfo is None:
                    date_val = date_val.replace(tzinfo=timezone.utc)

            platform_metadata = {
                "rating": raw.get("score"),
                "thumbs_up_count": raw.get("thumbsUpCount"),
                "review_created_version": raw.get("reviewCreatedVersion"),
                "reply_content": raw.get("replyContent")
            }

            review_id = raw.get("reviewId")
            # Create a pseudo-URL for the review since there's no direct web link to a specific review easily available
            source_url = f"https://play.google.com/store/apps/details?id=com.google.android.apps.photos&reviewId={review_id}"

            item = FeedbackItem(
                source=SourceType.PLAYSTORE,
                source_url=source_url[:2048],
                author_id=raw.get("userName", "unknown_author")[:255],
                text=text[:10000],
                date=date_val,
                thread_id=review_id,
                parent_id=None,
                platform_metadata=platform_metadata,
                extraction_status=ExtractionStatus.PENDING,
            )
            items.append(item)
            
        return items
