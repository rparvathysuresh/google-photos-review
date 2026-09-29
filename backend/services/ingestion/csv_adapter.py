"""
CSV and JSON ingestion adapter.
"""

import csv
import json
import io
from typing import List, Dict, Any, Union
from datetime import datetime, timezone
import dateutil.parser

from backend.models.feedback import FeedbackItem, SourceType, ExtractionStatus
from backend.services.ingestion.base_adapter import BaseAdapter


class CsvJsonAdapter(BaseAdapter):
    """
    Adapter for processing uploaded CSV or JSON files.
    """

    def fetch_data(self, file_content: Union[str, bytes], is_json: bool = False, **kwargs) -> List[Dict[str, Any]]:
        """
        Parse raw file bytes/string into a list of dictionaries.
        """
        if isinstance(file_content, bytes):
            # Try decoding as utf-8, fallback to latin-1
            try:
                content_str = file_content.decode('utf-8')
            except UnicodeDecodeError:
                content_str = file_content.decode('latin-1')
        else:
            content_str = file_content

        if is_json:
            try:
                data = json.loads(content_str)
                if not isinstance(data, list):
                    raise ValueError("JSON root must be an array of objects.")
                return data
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format: {e}")
        else:
            # CSV parsing
            if not content_str.strip():
                raise ValueError("File contains no data rows.")
                
            reader = csv.DictReader(io.StringIO(content_str))
            if not reader.fieldnames:
                raise ValueError("CSV header row is missing or empty.")
                
            return list(reader)

    def parse(self, raw_data: List[Dict[str, Any]]) -> List[FeedbackItem]:
        """
        Map dictionary rows to FeedbackItem instances.
        """
        items = []
        for row in raw_data:
            # Required fields mapping
            text = row.get('text', '').strip()
            if not text:
                continue # Handled by validation in base adapter if we kept it, but easier to skip here or let base validate. We let base validate.
            
            # Map source string to SourceType Enum
            raw_source = row.get('source', '').lower().strip()
            try:
                source = SourceType(raw_source) if raw_source else SourceType.CSV_UPLOAD
            except ValueError:
                source = SourceType.CSV_UPLOAD

            # Map Date
            date_val = None
            raw_date = row.get('date', '').strip()
            if raw_date:
                try:
                    date_val = dateutil.parser.parse(raw_date)
                    if date_val.tzinfo is None:
                        date_val = date_val.replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    pass # Leave as None if unparseable

            item = FeedbackItem(
                source=source,
                source_url=row.get('source_url', '').strip()[:2048], # Truncate to match column size
                author_id=row.get('author_id', '').strip() or None,
                text=text[:10000], # Truncate to reasonable max length as per edge cases
                date=date_val,
                extraction_status=ExtractionStatus.PENDING,
            )
            items.append(item)
            
        return items

    def process_file(self, file_content: bytes, filename: str) -> tuple[List[FeedbackItem], int, int]:
        """
        Helper entrypoint that determines format from filename.
        Returns: (valid_items, total_fetched, noise_filtered)
        """
        is_json = filename.lower().endswith('.json')
        return self.process(file_content, is_json=is_json)
