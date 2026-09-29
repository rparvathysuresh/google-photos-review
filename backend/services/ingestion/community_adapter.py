"""
Google Photos Community ingestion adapter.
"""

import logging
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from bs4 import BeautifulSoup

from backend.models.feedback import FeedbackItem, SourceType, ExtractionStatus
from backend.services.ingestion.base_adapter import BaseAdapter

logger = logging.getLogger(__name__)


class CommunityAdapter(BaseAdapter):
    """
    Adapter for scraping Google Photos Community Support forum.
    Note: Google Support is heavily JS-driven, so simple requests might not get all data.
    This provides a best-effort HTML scraper.
    """

    def fetch_data(
        self, 
        query: str = "find photos", 
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Best-effort scrape of the Google Support search page.
        """
        raw_items = []
        # Google support search URL
        url = f"https://support.google.com/photos/search?q={requests.utils.quote(query)}"
        
        try:
            logger.info(f"Fetching community threads for query: {query}")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # The structure of Google Support can change. We look for generic result links.
            # Usually they are in <a> tags with class containing 'result' or inside a specific div.
            results = soup.find_all('a', class_=lambda c: c and 'search-result' in c.lower())
            
            # If we don't find standard results, try finding any thread links
            if not results:
                results = [a for a in soup.find_all('a', href=True) if '/photos/thread/' in a['href']]
                
            for res in results[:20]: # Limit to top 20
                thread_url = res['href']
                if not thread_url.startswith('http'):
                    thread_url = "https://support.google.com" + thread_url
                    
                title = res.get_text(strip=True)
                
                raw_items.append({
                    "title": title,
                    "url": thread_url,
                    "body": f"Community thread title: {title}. Note: Requires deep-scraping to retrieve full replies.",
                    "author": "community_user",
                    "thread_id": thread_url.split('/')[-1].split('?')[0] if '/' in thread_url else "unknown"
                })
                
        except Exception as e:
            logger.error(f"Community scraping error: {e}")
            raise ValueError(f"Community scraping error: {e}. Note: Google Support may block automated requests.")
            
        logger.info(f"Fetched {len(raw_items)} community thread stubs.")
        return raw_items

    def parse(self, raw_data: List[Dict[str, Any]]) -> List[FeedbackItem]:
        """
        Map Community dictionaries to FeedbackItem instances.
        """
        items = []
        for raw in raw_data:
            title = raw.get("title", "").strip()
            body = raw.get("body", "").strip()
            text = f"{title}\n\n{body}" if body else title
            
            if not text:
                continue
                
            item = FeedbackItem(
                source=SourceType.COMMUNITY,
                source_url=raw.get("url", "")[:2048],
                author_id=raw.get("author", "unknown")[:255],
                text=text[:10000],
                date=datetime.now(timezone.utc), # Fallback date
                thread_id=raw.get("thread_id", "")[:255],
                parent_id=None,
                platform_metadata={},
                extraction_status=ExtractionStatus.PENDING,
            )
            items.append(item)
            
        return items
