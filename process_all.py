import time
from backend.db.database import SessionLocal
from backend.services.extraction.relevance import RelevanceClassifier
from backend.services.extraction.extractor import EpisodeExtractor
from backend.models.feedback import FeedbackItem

def run():
    db = SessionLocal()
    classifier = RelevanceClassifier(db)
    extractor = EpisodeExtractor(db)
    
    while True:
        pending_count = db.query(FeedbackItem).filter(FeedbackItem.extraction_status == "pending").count()
        if pending_count == 0:
            print("All items processed!")
            break
            
        print(f"Remaining pending items: {pending_count}")
        
        try:
            c_count = classifier.process_batch(batch_size=5)
            print(f"Classified {c_count} items")
            
            e_count = extractor.process_batch(batch_size=5)
            print(f"Extracted {e_count} items")
            
            # Sleep to avoid rate limits
            print("Sleeping for 35 seconds to reset Groq limits...")
            time.sleep(35)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(30)
            
if __name__ == "__main__":
    run()
