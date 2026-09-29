from typing import Dict, Any, List
from sqlalchemy import func
from backend.db.database import SessionLocal
from backend.models.feedback import FeedbackItem
from backend.models.episode import RetrievalEpisode
from backend.models.cluster import ProblemCluster

class AnalyticsService:
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Aggregate metrics for the top-level dashboard."""
        db = SessionLocal()
        try:
            # 1. Total Raw Feedback
            total_feedback = db.query(FeedbackItem).count()
            
            # 2. Total Extracted Episodes
            total_episodes = db.query(RetrievalEpisode).count()
            
            # 3. Source Distribution
            source_dist = db.query(
                RetrievalEpisode.source, func.count(RetrievalEpisode.id)
            ).group_by(RetrievalEpisode.source).all()
            sources = [{"source": s, "count": c} for s, c in source_dist]
            
            # 4. Top Failure Reasons
            # Since failure_reasons is a JSON array, we can't easily GROUP BY it in SQLite.
            # We'll calculate it in Python for the current scale.
            episodes = db.query(RetrievalEpisode.failure_reason).all()
            failures = {}
            for e in episodes:
                if e[0]:
                    for f in e[0]:
                        failures[f] = failures.get(f, 0) + 1
            top_failures = sorted([{"reason": k, "count": v} for k, v in failures.items()], 
                                  key=lambda x: x["count"], reverse=True)[:5]
                                  
            # 5. Top Clusters
            clusters = db.query(ProblemCluster).order_by(ProblemCluster.episode_count.desc()).limit(5).all()
            top_clusters = [{"id": c.id, "label": c.label, "count": c.episode_count} for c in clusters]
            
            return {
                "total_feedback": total_feedback,
                "total_episodes": total_episodes,
                "source_distribution": sources,
                "top_failure_reasons": top_failures,
                "top_clusters": top_clusters
            }
        finally:
            db.close()

analytics_service = AnalyticsService()
