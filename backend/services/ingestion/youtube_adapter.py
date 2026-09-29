"""
YouTube ingestion adapter.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import dateutil.parser

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from backend.config import settings
from backend.models.feedback import FeedbackItem, SourceType, ExtractionStatus
from backend.services.ingestion.base_adapter import BaseAdapter

logger = logging.getLogger(__name__)


class YouTubeAdapter(BaseAdapter):
    """
    Adapter for scraping YouTube video comments via YouTube Data API v3.
    """

    def __init__(self):
        if not settings.YOUTUBE_API_KEY:
            raise ValueError("YouTube API key missing. Please set YOUTUBE_API_KEY in .env")
            
        try:
            self.youtube = build('youtube', 'v3', developerKey=settings.YOUTUBE_API_KEY)
        except Exception as e:
            logger.error(f"Failed to initialize YouTube client: {e}")
            raise ValueError(f"Failed to initialize YouTube client: {e}")

    def fetch_data(
        self, 
        query: str = "Google Photos tips photo search", 
        max_videos: int = 5,
        max_comments_per_video: int = 20,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Search for videos and fetch top-level comments for each video.
        """
        raw_items = []
        try:
            logger.info(f"Searching YouTube: query='{query}', max_videos={max_videos}")
            
            # 1. Search for videos
            search_response = self.youtube.search().list(
                q=query,
                part='id,snippet',
                type='video',
                maxResults=max_videos
            ).execute()

            # Note: The search endpoint costs 100 quota units per request. 
            # CommentThreads costs 1 unit per request.
            # Free tier is 10,000 units/day.

            for search_result in search_response.get('items', []):
                video_id = search_result['id']['videoId']
                video_title = search_result['snippet']['title']
                
                logger.info(f"Fetching comments for video: {video_id} ({video_title})")
                
                try:
                    # 2. Fetch comments for each video
                    comments_response = self.youtube.commentThreads().list(
                        part='snippet',
                        videoId=video_id,
                        maxResults=max_comments_per_video,
                        textFormat='plainText'
                    ).execute()
                    
                    for item in comments_response.get('items', []):
                        top_comment = item['snippet']['topLevelComment']['snippet']
                        comment_data = {
                            "video_id": video_id,
                            "video_title": video_title,
                            "comment_id": item['id'],
                            "author_name": top_comment.get('authorDisplayName', 'unknown'),
                            "text": top_comment.get('textDisplay', ''),
                            "like_count": top_comment.get('likeCount', 0),
                            "published_at": top_comment.get('publishedAt')
                        }
                        raw_items.append(comment_data)
                        
                except HttpError as e:
                    # Sometimes comments are disabled for a video
                    if e.resp.status == 403 and "commentsDisabled" in str(e):
                        logger.warning(f"Comments are disabled for video {video_id}")
                    else:
                        logger.error(f"Error fetching comments for video {video_id}: {e}")
                        
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            raise ValueError(f"YouTube API error: {e}")
            
        logger.info(f"Fetched {len(raw_items)} total comments from YouTube.")
        return raw_items

    def parse(self, raw_data: List[Dict[str, Any]]) -> List[FeedbackItem]:
        """
        Map YouTube comment dictionaries to FeedbackItem instances.
        """
        items = []
        for raw in raw_data:
            text = raw.get("text", "").strip()
            if not text:
                continue
                
            date_val = None
            published_at = raw.get("published_at")
            if published_at:
                try:
                    date_val = dateutil.parser.parse(published_at)
                    if date_val.tzinfo is None:
                        date_val = date_val.replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    pass

            video_id = raw.get("video_id")
            source_url = f"https://www.youtube.com/watch?v={video_id}&lc={raw.get('comment_id')}" if video_id else ""

            platform_metadata = {
                "video_id": video_id,
                "video_title": raw.get("video_title"),
                "like_count": raw.get("like_count")
            }

            item = FeedbackItem(
                source=SourceType.YOUTUBE,
                source_url=source_url[:2048],
                author_id=raw.get("author_name", "unknown_author")[:255],
                text=text[:10000],
                date=date_val,
                thread_id=video_id,
                parent_id=None,
                platform_metadata=platform_metadata,
                extraction_status=ExtractionStatus.PENDING,
            )
            items.append(item)
            
        return items
