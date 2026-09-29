import logging
import numpy as np
from typing import List, Dict, Any

import umap
from sklearn.cluster import HDBSCAN

from backend.db.vector_store import vector_store
from backend.db.database import SessionLocal
from backend.models.episode import RetrievalEpisode

logger = logging.getLogger(__name__)

class Clusterer:
    """Clustering pipeline using UMAP + HDBSCAN."""
    
    def __init__(self):
        # Initialize UMAP
        self.reducer = umap.UMAP(
            n_components=5, 
            n_neighbors=15, 
            min_dist=0.1, 
            metric='cosine', 
            random_state=42
        )
        
        # Initialize HDBSCAN
        self.clusterer = HDBSCAN(
            min_cluster_size=5,
            min_samples=3,
            metric='euclidean',
            cluster_selection_epsilon=0.0
        )

    def run_clustering(self) -> Dict[str, Any]:
        """
        Fetch all episode embeddings, cluster them, and save assignments to DB.
        """
        logger.info("Starting UMAP + HDBSCAN clustering pipeline...")
        
        # 1. Fetch all episodes from ChromaDB
        # We need both IDs and embeddings
        try:
            results = vector_store.episode_collection.get(include=['embeddings', 'metadatas', 'documents'])
        except Exception as e:
            logger.error(f"Failed to fetch from vector store: {e}")
            return {"status": "error", "message": str(e)}
            
        if not results or not results.get('ids'):
            return {"status": "error", "message": "No episodes found in vector store"}
            
        ids = results['ids']
        embeddings = np.array(results['embeddings'])
        
        if len(ids) < 15:
            return {"status": "error", "message": "Not enough episodes for meaningful clustering (min 15 required)"}
            
        logger.info(f"Fetched {len(ids)} episode embeddings from ChromaDB. Running UMAP...")
        
        # 2. Dimensionality reduction (UMAP)
        reduced_embeddings = self.reducer.fit_transform(embeddings)
        
        logger.info("Running HDBSCAN...")
        
        # 3. Clustering (HDBSCAN)
        labels = self.clusterer.fit_predict(reduced_embeddings)
        
        # 4. Save cluster assignments to SQLite database
        logger.info("Saving cluster assignments to SQLite...")
        
        # We use HDBSCAN labels as cluster IDs directly for now (0, 1, 2, ..., -1 for noise)
        cluster_assignments = {}
        unique_labels = set(labels)
        
        db = SessionLocal()
        try:
            for i, episode_id in enumerate(ids):
                # ChromaDB ID is the episode UUID
                label = labels[i]
                cluster_id = f"cluster_{label}" if label != -1 else "uncategorized"
                
                # Group for our return dict
                if cluster_id not in cluster_assignments:
                    cluster_assignments[cluster_id] = []
                cluster_assignments[cluster_id].append(episode_id)
                
                # Update DB
                episode = db.query(RetrievalEpisode).filter(RetrievalEpisode.id == episode_id).first()
                if episode:
                    episode.problem_cluster = cluster_id
            
            db.commit()
            logger.info("Successfully updated episode cluster assignments in database.")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update database: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            db.close()
            
        return {
            "status": "success",
            "total_episodes": len(ids),
            "clusters_found": len(unique_labels) - (1 if -1 in unique_labels else 0),
            "assignments": {k: len(v) for k, v in cluster_assignments.items()}
        }

clusterer = Clusterer()
