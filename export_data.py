import os
import json
from backend.db.database import SessionLocal
from backend.models.feedback import FeedbackItem
from backend.models.episode import RetrievalEpisode

def export():
    db = SessionLocal()
    os.makedirs("data/exports", exist_ok=True)
    
    # 1. Export extracted episodes
    episodes = db.query(RetrievalEpisode).all()
    ep_data = []
    for e in episodes:
        ep_data.append({
            "id": e.id,
            "feedback_item_id": e.feedback_item_id,
            "source": e.source,
            "memory_type": e.memory_type,
            "remembered_clues": e.remembered_clues,
            "forgotten_info": e.forgotten_info,
            "retrieval_attempt": e.retrieval_attempt,
            "failure_reason": e.failure_reason,
            "supporting_evidence": e.supporting_evidence
        })
        
    with open("data/exports/extracted_episodes.json", "w") as f:
        json.dump(ep_data, f, indent=2)
        
    # 2. Export YouTube reviews (relevant vs irrelevant)
    yt_items = db.query(FeedbackItem).filter(FeedbackItem.source == 'youtube').all()
    yt_data = []
    for i in yt_items:
        yt_data.append({
            "id": i.id,
            "text": i.text,
            "is_relevant": i.is_relevant,
            "relevance_score": i.relevance_score,
            "extraction_status": i.extraction_status.value
        })
        
    with open("data/exports/youtube_reviews.json", "w") as f:
        json.dump(yt_data, f, indent=2)
        
    print(f"Exported {len(ep_data)} episodes to data/exports/extracted_episodes.json")
    print(f"Exported {len(yt_data)} YouTube reviews to data/exports/youtube_reviews.json")

if __name__ == "__main__":
    export()
