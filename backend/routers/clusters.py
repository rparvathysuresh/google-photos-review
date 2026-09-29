from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from backend.db.database import get_db
from backend.models.cluster import ProblemCluster
from backend.models.episode import RetrievalEpisode
from backend.services.clustering.clusterer import clusterer
from backend.services.clustering.labeller import labeller

router = APIRouter(prefix="/api/clusters", tags=["Clusters"])

def run_clustering_pipeline():
    """Background task to run UMAP+HDBSCAN and then LLM labeling."""
    res = clusterer.run_clustering()
    if res.get("status") == "success":
        labeller.process_clusters()

@router.post("/recompute")
def trigger_recompute(background_tasks: BackgroundTasks):
    """Trigger the clustering pipeline in the background."""
    background_tasks.add_task(run_clustering_pipeline)
    return {"status": "accepted", "message": "Clustering pipeline triggered in the background."}

@router.get("/")
def list_clusters(db: Session = Depends(get_db)):
    """List all clusters with their profiles."""
    clusters = db.query(ProblemCluster).order_by(ProblemCluster.episode_count.desc()).all()
    return clusters

@router.get("/{cluster_id}")
def get_cluster(cluster_id: str, db: Session = Depends(get_db)):
    """Get detailed profile for a specific cluster."""
    cluster = db.query(ProblemCluster).filter(ProblemCluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return cluster

@router.get("/{cluster_id}/episodes")
def get_cluster_episodes(cluster_id: str, db: Session = Depends(get_db)):
    """Get episodes belonging to a specific cluster."""
    episodes = db.query(RetrievalEpisode).filter(RetrievalEpisode.problem_cluster == cluster_id).all()
    return episodes
