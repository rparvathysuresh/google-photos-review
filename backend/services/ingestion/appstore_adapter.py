"""
Apple App Store ingestion adapter.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import dateutil.parser

from app_store_scraper import AppStore

from backend.models.feedback import FeedbackItem, SourceType, ExtractionStatus
from backend.services.ingestion.base_adapter import BaseAdapter

logger = logging.getLogger(__name__)


class AppStoreAdapter(BaseAdapter):
    """
    Adapter for scraping Google Photos reviews from the Apple App Store.
    """

    def fetch_data(
        self, 
        app_name: str = "google-photos",
        app_id: int = 962164605, # Google Photos iOS App ID
        country: str = "us",
        limit: int = 100,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Fetch reviews from the App Store.
        Filters for reviews mentioning search-related keywords.
        """
        raw_items = []
        try:
            logger.info(f"Fetching {limit} reviews for {app_name} from App Store ({country})...")
            
            app = AppStore(country=country, app_name=app_name, app_id=app_id)
            app.review(how_many=limit)
            
            keywords = ['search', 'find', 'retrieve', 'look for', 'missing', 'lost', 'organize', 'ocr', 'recognize']
            
            for review in app.reviews:
                content = review.get('review', '').lower()
                
                # Check if any keyword is in the review content
                if any(kw in content for kw in keywords):
                    raw_items.append(review)
                    
        except Exception as e:
            logger.error(f"App Store scraping error: {e}")
            raise ValueError(f"App Store scraping error: {e}")
            
        logger.info(f"Fetched {len(app.reviews)} total reviews, found {len(raw_items)} relevant to retrieval.")
        return raw_items

    def parse(self, raw_data: List[Dict[str, Any]]) -> List[FeedbackItem]:
        """
        Map App Store review dictionaries to FeedbackItem instances.
        """
        items = []
        for raw in raw_data:
            text = raw.get("review", "").strip()
            if not text:
                continue
                
            date_val = None
            if raw.get("date"):
                try:
                    date_val = dateutil.parser.parse(str(raw["date"]))
                    if date_val.tzinfo is None:
                        date_val = date_val.replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    pass

            platform_metadata = {
                "rating": raw.get("rating"),
                "is_edited": raw.get("isEdited"),
                "title": raw.get("title")
            }

            # Generate a pseudo-thread_id from author + date since App Store doesn't give a direct review ID
            author = raw.get("userName", "unknown_author")
            thread_id = f"appstore_{author}_{raw.get('date')}"
            
            # Pseudo URL
            source_url = f"https://apps.apple.com/us/app/google-photos/id962164605#review-{author}"

            item = FeedbackItem(
                source=SourceType.APPSTORE,
                source_url=source_url[:2048],
                author_id=author[:255],
                text=text[:10000],
                date=date_val,
                thread_id=thread_id[:255],
                parent_id=None,
                platform_metadata=platform_metadata,
                extraction_status=ExtractionStatus.PENDING,
            )
            items.append(item)
            
        return items
