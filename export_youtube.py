import csv
import json
from sqlalchemy.orm import Session
from backend.db.database import SessionLocal
from backend.models.feedback import FeedbackItem, SourceType

def export_youtube():
    db: Session = SessionLocal()
    try:
        items = db.query(FeedbackItem).filter(FeedbackItem.source == SourceType.YOUTUBE).all()
        print(f"Found {len(items)} YouTube feedback items.")
        
        filepath = "data/youtube_reviews.csv"
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['video_title', 'author', 'text', 'like_count']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for item in items:
                meta = item.platform_metadata or {}
                writer.writerow({
                    'video_title': meta.get('video_title', ''),
                    'author': item.author_id,
                    'text': item.text.replace('\n', '  '),
                    'like_count': meta.get('like_count', 0)
                })
        print(f"Exported to {filepath}")
    finally:
        db.close()

if __name__ == "__main__":
    export_youtube()
