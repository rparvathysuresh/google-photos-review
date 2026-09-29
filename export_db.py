import csv
import json
from sqlalchemy.orm import Session
from backend.db.database import SessionLocal
from backend.models.feedback import FeedbackItem

def export_to_csv(filepath: str):
    db: Session = SessionLocal()
    try:
        items = db.query(FeedbackItem).all()
        print(f"Found {len(items)} feedback items in the database.")
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'id', 'source', 'author_id', 'date', 'thread_id', 
                'text', 'platform_metadata', 'ingested_at'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for item in items:
                writer.writerow({
                    'id': item.id,
                    'source': item.source.value if item.source else '',
                    'author_id': item.author_id,
                    'date': item.date.isoformat() if item.date else '',
                    'thread_id': item.thread_id,
                    'text': item.text.replace('\n', '  '),
                    'platform_metadata': json.dumps(item.platform_metadata) if item.platform_metadata else '{}',
                    'ingested_at': item.ingested_at.isoformat() if item.ingested_at else ''
                })
        print(f"Exported successfully to {filepath}")
    except Exception as e:
        print(f"Error exporting database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    export_to_csv("data/exported_feedback.csv")
