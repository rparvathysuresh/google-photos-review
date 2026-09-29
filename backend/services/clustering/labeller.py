import logging
import json
from collections import Counter
from groq import Groq

from backend.config import settings
from backend.db.database import SessionLocal
from backend.models.episode import RetrievalEpisode
from backend.models.cluster import ProblemCluster

logger = logging.getLogger(__name__)

class ClusterLabeller:
    def __init__(self):
        try:
            self.client = Groq(api_key=settings.GROQ_API_KEY)
            self.model = settings.GROQ_MODEL
        except Exception as e:
            logger.error(f"Failed to init Groq client: {e}")
            raise
            
        self.prompt = """You are a qualitative UX researcher.
Read the following retrieval episodes (user pain points) which belong to a single cluster.
Generate a concise label and a short summary explaining the overarching problem area.
Return ONLY valid JSON with keys: "label" and "summary".

Episodes:
{episodes}"""

    def generate_label(self, episodes: list) -> dict:
        """Call Groq to label the cluster."""
        # Sample up to 8 representative episodes
        sample = episodes[:8]
        episodes_text = "\n\n".join([
            f"Episode {i+1}: Goal: {e.user_goal} | Remembered: {e.remembered_clues} | Failed because: {e.failure_reason}"
            for i, e in enumerate(sample)
        ])
        
        sys_msg = self.prompt.format(episodes=episodes_text)
        
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": sys_msg}],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            content = resp.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            logger.error(f"Groq API error during labeling: {e}")
            return {"label": "Auto-Generated Cluster", "summary": "Failed to generate summary."}

    def process_clusters(self):
        """Build profiles and generate labels for all clusters in DB."""
        db = SessionLocal()
        try:
            # Get all distinct cluster IDs from episodes
            cluster_ids = db.query(RetrievalEpisode.problem_cluster).distinct().all()
            cluster_ids = [c[0] for c in cluster_ids if c[0] and c[0] != "uncategorized"]
            
            # Delete old clusters
            db.query(ProblemCluster).delete()
            
            for cid in cluster_ids:
                episodes = db.query(RetrievalEpisode).filter(RetrievalEpisode.problem_cluster == cid).all()
                if not episodes:
                    continue
                    
                logger.info(f"Profiling cluster {cid} with {len(episodes)} episodes...")
                
                # 1. Label via LLM
                llm_data = self.generate_label(episodes)
                
                # 2. Profile aggregations
                remembered = []
                forgotten = []
                methods = []
                failures = []
                sources = []
                
                for e in episodes:
                    if e.remembered_clues: remembered.extend(e.remembered_clues)
                    if e.forgotten_info: forgotten.extend(e.forgotten_info)
                    if e.retrieval_attempt: methods.extend(e.retrieval_attempt)
                    if e.failure_reason: failures.extend(e.failure_reason)
                    if e.source: sources.append(e.source)
                    
                # 3. Create cluster object
                cluster = ProblemCluster(
                    id=cid,
                    label=llm_data.get("label", "Unknown Cluster"),
                    summary=llm_data.get("summary", ""),
                    episode_count=len(episodes),
                    common_remembered_clues=[k for k,v in Counter(remembered).most_common(5)],
                    common_forgotten_info=[k for k,v in Counter(forgotten).most_common(5)],
                    common_retrieval_methods=[k for k,v in Counter(methods).most_common(5)],
                    common_failure_reasons=[k for k,v in Counter(failures).most_common(5)],
                    source_distribution=dict(Counter(sources)),
                    representative_evidence=[e.id for e in episodes[:3]]
                )
                
                db.add(cluster)
                
            db.commit()
            logger.info("Finished labeling and profiling all clusters.")
        except Exception as e:
            db.rollback()
            logger.error(f"Error in process_clusters: {e}")
        finally:
            db.close()

labeller = ClusterLabeller()
