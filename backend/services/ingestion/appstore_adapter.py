"""
Apple App Store ingestion adapter.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import dateutil.parser
import requests

from backend.models.feedback import FeedbackItem, SourceType, ExtractionStatus
from backend.services.ingestion.base_adapter import BaseAdapter

logger = logging.getLogger(__name__)


class AppStoreAdapter(BaseAdapter):
    """
    Adapter for scraping Google Photos reviews from the Apple App Store via iTunes RSS feed.
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
            logger.info(f"Fetching reviews for {app_name} from App Store ({country})...")
            
            # Simple iTunes RSS endpoint (paginated up to 10 pages, 50 results each)
            pages = (limit // 50) + 1
            fetched = 0
            keywords = ['search', 'find', 'retrieve', 'look for', 'missing', 'lost', 'organize', 'ocr', 'recognize']
            
            for page in range(1, min(pages + 1, 11)):
                url = f"https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json"
                resp = requests.get(url, timeout=10)
                if resp.status_code != 200:
                    break
                    
                data = resp.json()
                entries = data.get("feed", {}).get("entry", [])
                
                for entry in entries:
                    if "author" not in entry:
                        continue
                        
                    content = entry.get("content", {}).get("label", "")
                    title = entry.get("title", {}).get("label", "")
                    author = entry.get("author", {}).get("name", {}).get("label", "unknown")
                    rating = entry.get("im:rating", {}).get("label", "0")
                    updated = entry.get("updated", {}).get("label", "")
                    
                    full_text = f"{title} {content}".lower()
                    if any(kw in full_text for kw in keywords):
                        raw_items.append({
                            "review": content,
                            "title": title,
                            "author": author,
                            "rating": int(rating) if rating.isdigit() else 0,
                            "date": updated,
                        })
                    fetched += 1
                
                if fetched >= limit:
                    break
                    
        except Exception as e:
            logger.error(f"App Store scraping error: {e}")
            raise ValueError(f"App Store scraping error: {e}")
            
        logger.info(f"Fetched {fetched} total reviews, found {len(raw_items)} relevant to retrieval.")
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
                "title": raw.get("title")
            }

            author = raw.get("author", "unknown_author")
            thread_id = f"appstore_{author}_{raw.get('date')}"
            
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
