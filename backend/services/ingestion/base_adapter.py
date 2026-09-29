"""
Abstract base class for all ingestion adapters.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import hashlib
import re

from backend.models.feedback import FeedbackItem


class BaseAdapter(ABC):
    """
    Abstract base class for all ingestion adapters (CSV, Reddit, etc.).
    """

    @abstractmethod
    def fetch_data(self, source_path_or_query: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetch raw data from the source.
        For CSV, this reads the file. For APIs, this makes network requests.
        """
        pass

    @abstractmethod
    def parse(self, raw_data: List[Dict[str, Any]]) -> List[FeedbackItem]:
        """
        Parse raw data into FeedbackItem instances.
        """
        pass

    def validate(self, item: FeedbackItem) -> bool:
        """
        Validate a parsed FeedbackItem.
        Returns True if valid, False otherwise.
        """
        if not item.text or not item.text.strip():
            return False
        
        text_val = item.text.lower().strip()
        
        # Source-specific noise filtering
        # Drop very short generic praises like "great app 5 stars"
        if len(text_val) < 25 and any(word in text_val for word in ["great", "good", "love", "awesome", "perfect", "5 stars", "best"]):
            # Unless it also mentions a relevant keyword
            if not any(kw in text_val for kw in ["search", "find", "missing"]):
                return False

        # Drop purely empty/whitespace
        if len(text_val) == 0:
            return False

        return True

    def compute_fingerprint(self, item: FeedbackItem) -> str:
        """
        Compute a SHA-256 fingerprint for deduplication.
        Cross-source dedup: Hash is based purely on normalized text content,
        so identical comments posted across different platforms by the same 
        or different users are collapsed into one.
        """
        text_val = item.text or ""
        text_val = text_val.lower().strip()
        
        # Remove all punctuation and excessive whitespace for a more robust "fuzzy-ish" exact match
        text_val = re.sub(r'[^\w\s]', '', text_val)
        text_val = re.sub(r'\s+', ' ', text_val)

        fingerprint_input = text_val.encode('utf-8')
        return hashlib.sha256(fingerprint_input).hexdigest()

    def process(self, source_path_or_query: str, **kwargs) -> tuple[List[FeedbackItem], int, int]:
        """
        Full pipeline: fetch -> parse -> validate & fingerprint
        Returns: (valid_items, total_fetched, noise_filtered)
        """
        raw_data = self.fetch_data(source_path_or_query, **kwargs)
        parsed_items = self.parse(raw_data)
        
        valid_items = []
        for item in parsed_items:
            if self.validate(item):
                item.fingerprint = self.compute_fingerprint(item)
                valid_items.append(item)
                
        total_fetched = len(parsed_items)
        noise_filtered = total_fetched - len(valid_items)
        
        return valid_items, total_fetched, noise_filtered
