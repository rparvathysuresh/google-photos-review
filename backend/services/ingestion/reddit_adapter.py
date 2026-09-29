"""
Reddit ingestion adapter.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import praw
from praw.exceptions import PRAWException
from prawcore.exceptions import PrawcoreException

from backend.config import settings
from backend.models.feedback import FeedbackItem, SourceType, ExtractionStatus
from backend.services.ingestion.base_adapter import BaseAdapter

logger = logging.getLogger(__name__)


class RedditAdapter(BaseAdapter):
    """
    Adapter for scraping Reddit posts and comments via PRAW.
    """

    def __init__(self):
        if not settings.REDDIT_CLIENT_ID or not settings.REDDIT_CLIENT_SECRET:
            raise ValueError("Reddit credentials missing. Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env")
            
        try:
            self.reddit = praw.Reddit(
                client_id=settings.REDDIT_CLIENT_ID,
                client_secret=settings.REDDIT_CLIENT_SECRET,
                user_agent=settings.REDDIT_USER_AGENT
            )
            # Verify read-only access is working
            self.reddit.read_only = True
        except Exception as e:
            logger.error(f"Failed to initialize Reddit client: {e}")
            raise ValueError(f"Failed to initialize Reddit client: {e}")

    def fetch_data(
        self, 
        subreddits: str = "googlephotos", 
        query: str = "find old photos", 
        limit: int = 100, 
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Fetch posts and top-level comments from Reddit based on a search query.
        `subreddits` can be a single subreddit or multiple separated by '+'.
        """
        raw_items = []
        try:
            subreddit = self.reddit.subreddit(subreddits)
            logger.info(f"Searching Reddit: subreddits='{subreddits}', query='{query}', limit={limit}")
            
            for submission in subreddit.search(query, limit=limit):
                # Add the post itself
                post_data = {
                    "is_post": True,
                    "id": submission.id,
                    "url": f"https://www.reddit.com{submission.permalink}",
                    "author": submission.author.name if submission.author else "deleted",
                    "title": submission.title,
                    "body": submission.selftext,
                    "created_utc": submission.created_utc,
                    "subreddit": submission.subreddit.display_name,
                    "score": submission.score,
                    "num_comments": submission.num_comments
                }
                raw_items.append(post_data)
                
                # Fetch top-level comments
                submission.comments.replace_more(limit=0)
                for comment in submission.comments:
                    comment_data = {
                        "is_post": False,
                        "id": comment.id,
                        "parent_id": submission.id,
                        "url": f"https://www.reddit.com{comment.permalink}",
                        "author": comment.author.name if comment.author else "deleted",
                        "body": comment.body,
                        "created_utc": comment.created_utc,
                        "subreddit": comment.subreddit.display_name,
                        "score": comment.score
                    }
                    raw_items.append(comment_data)
                    
        except (PRAWException, PrawcoreException) as e:
            logger.error(f"Reddit API error: {e}")
            raise ValueError(f"Reddit API error: {e}")
            
        logger.info(f"Fetched {len(raw_items)} total items (posts + comments) from Reddit.")
        return raw_items

    def parse(self, raw_data: List[Dict[str, Any]]) -> List[FeedbackItem]:
        """
        Map Reddit post/comment dictionaries to FeedbackItem instances.
        """
        items = []
        for raw in raw_data:
            # Combine title and body for posts
            if raw.get("is_post"):
                title = raw.get("title", "").strip()
                body = raw.get("body", "").strip()
                # Skip if post has no text (e.g. image only)
                if not title and not body:
                    continue
                text = f"{title}\n\n{body}" if body else title
            else:
                text = raw.get("body", "").strip()
                # Skip deleted or empty comments
                if not text or text == "[deleted]" or text == "[removed]":
                    continue
                    
            date_val = None
            if raw.get("created_utc"):
                date_val = datetime.fromtimestamp(raw["created_utc"], tz=timezone.utc)
                
            platform_metadata = {
                "subreddit": raw.get("subreddit"),
                "score": raw.get("score"),
                "is_post": raw.get("is_post")
            }
            if raw.get("is_post"):
                platform_metadata["num_comments"] = raw.get("num_comments")

            item = FeedbackItem(
                source=SourceType.REDDIT,
                source_url=raw.get("url", "")[:2048],
                author_id=raw.get("author", "unknown_author")[:255],
                text=text[:10000],
                date=date_val,
                thread_id=raw.get("id") if raw.get("is_post") else raw.get("parent_id"),
                parent_id=None if raw.get("is_post") else raw.get("parent_id"),
                platform_metadata=platform_metadata,
                extraction_status=ExtractionStatus.PENDING,
            )
            items.append(item)
            
        return items
