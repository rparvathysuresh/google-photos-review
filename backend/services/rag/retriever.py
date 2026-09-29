import logging
from typing import List, Dict, Any, Optional

from backend.db.vector_store import vector_store
from backend.services.rag.embeddings import embedding_service

logger = logging.getLogger(__name__)

class Retriever:
    """Retrieves relevant evidence from vector store."""
    
    def __init__(self):
        pass

    def retrieve(self, query: str, top_k: int = 20, similarity_threshold: float = 1.0, filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search both feedback and episode collections for the query.
        Merge and deduplicate results.
        Note: ChromaDB default distance is L2. Lower is more similar.
        """
        logger.info(f"Retrieving evidence for query: {query}")
        
        # 1. Embed query
        query_embedding = embedding_service.model.encode([query], normalize_embeddings=True).tolist()[0]
        
        # 2. Search both collections
        feedback_results = vector_store.search_feedback(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_metadata=filter_metadata
        )
        
        episode_results = vector_store.search_episodes(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_metadata=filter_metadata
        )
        
        # 3. Merge and normalize results
        merged_results = []
        
        # Process feedback results
        if feedback_results and feedback_results.get('ids') and feedback_results['ids'][0]:
            for i in range(len(feedback_results['ids'][0])):
                distance = feedback_results['distances'][0][i]
                if distance <= similarity_threshold:
                    merged_results.append({
                        "id": feedback_results['ids'][0][i],
                        "document": feedback_results['documents'][0][i],
                        "metadata": feedback_results['metadatas'][0][i],
                        "distance": distance,
                        "type": "raw_feedback"
                    })
                    
        # Process episode results
        if episode_results and episode_results.get('ids') and episode_results['ids'][0]:
            for i in range(len(episode_results['ids'][0])):
                distance = episode_results['distances'][0][i]
                if distance <= similarity_threshold:
                    merged_results.append({
                        "id": episode_results['ids'][0][i],
                        "document": episode_results['documents'][0][i],
                        "metadata": episode_results['metadatas'][0][i],
                        "distance": distance,
                        "type": "episode"
                    })
                    
        # 4. Sort by distance (lower is better for L2)
        merged_results.sort(key=lambda x: x["distance"])
        
        # 5. Deduplicate by feedback_id
        # We prefer episodes over raw feedback if they point to the same feedback_id
        seen_feedback_ids = set()
        deduped_results = []
        
        for res in merged_results:
            # Determine the underlying feedback_item_id
            if res["type"] == "raw_feedback":
                f_id = res["id"]
            else:
                f_id = res["metadata"].get("feedback_item_id")
                
            if f_id not in seen_feedback_ids:
                seen_feedback_ids.add(f_id)
                deduped_results.append(res)
                
            if len(deduped_results) >= top_k:
                break
                
        logger.info(f"Retrieved {len(deduped_results)} unique documents after dedup.")
        return deduped_results

retriever = Retriever()
