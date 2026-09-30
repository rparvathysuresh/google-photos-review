import os
import logging
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings
from pydantic import BaseModel

from backend.config import settings

logger = logging.getLogger(__name__)

class VectorStore:
    """Wrapper for ChromaDB operations."""
    
    def __init__(self):
        self._client = None
        self._feedback_collection = None
        self._episode_collection = None

    def _init_db(self):
        if self._client is not None:
            return
            
        # Create persist directory if it doesn't exist
        os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
        
        # Initialize client
        self._client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize collections
        self._feedback_collection = self._client.get_or_create_collection(
            name="feedback_embeddings",
            metadata={"description": "Embeddings for raw FeedbackItem text"}
        )
        
        self._episode_collection = self._client.get_or_create_collection(
            name="episode_embeddings",
            metadata={"description": "Embeddings for structured RetrievalEpisode text"}
        )
        logger.info(f"Initialized ChromaDB at {settings.CHROMA_PERSIST_DIR}")

    @property
    def feedback_collection(self):
        self._init_db()
        return self._feedback_collection
        
    @property
    def episode_collection(self):
        self._init_db()
        return self._episode_collection

    def add_feedback_embeddings(self, ids: List[str], embeddings: List[List[float]], documents: List[str], metadatas: List[Dict[str, Any]]):
        """Batch upsert raw feedback embeddings."""
        # Chroma expects metadatas to contain basic types only. 
        # Convert any booleans/nones to strings if necessary, though chroma usually handles simple types.
        safe_metadatas = []
        for meta in metadatas:
            safe_meta = {}
            for k, v in meta.items():
                if v is None:
                    safe_meta[k] = ""
                elif isinstance(v, bool):
                    safe_meta[k] = str(v).lower()
                else:
                    safe_meta[k] = v
            safe_metadatas.append(safe_meta)
            
        self.feedback_collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=safe_metadatas
        )

    def add_episode_embeddings(self, ids: List[str], embeddings: List[List[float]], documents: List[str], metadatas: List[Dict[str, Any]]):
        """Batch upsert structured episode embeddings."""
        safe_metadatas = []
        for meta in metadatas:
            safe_meta = {}
            for k, v in meta.items():
                if v is None:
                    safe_meta[k] = ""
                elif isinstance(v, list):
                    # Chroma metadata values cannot be lists, must convert to comma-separated string
                    safe_meta[k] = ", ".join([str(item) for item in v if item is not None])
                elif isinstance(v, bool):
                    safe_meta[k] = str(v).lower()
                else:
                    safe_meta[k] = v
            safe_metadatas.append(safe_meta)

        self.episode_collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=safe_metadatas
        )

    def search_feedback(self, query_embedding: List[float], top_k: int = 10, filter_metadata: Optional[Dict[str, Any]] = None):
        """Search feedback embeddings."""
        results = self.feedback_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata,
            include=['documents', 'metadatas', 'distances']
        )
        return results

    def search_episodes(self, query_embedding: List[float], top_k: int = 10, filter_metadata: Optional[Dict[str, Any]] = None):
        """Search episode embeddings."""
        results = self.episode_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata,
            include=['documents', 'metadatas', 'distances']
        )
        return results

    def delete_feedback(self, ids: List[str]):
        """Delete feedback embeddings by ID."""
        self.feedback_collection.delete(ids=ids)

    def delete_episodes(self, ids: List[str]):
        """Delete episode embeddings by ID."""
        self.episode_collection.delete(ids=ids)

    def get_health(self) -> Dict[str, Any]:
        """Check ChromaDB connectivity and counts."""
        try:
            return {
                "status": "ok",
                "feedback_count": self.feedback_collection.count(),
                "episode_count": self.episode_collection.count()
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

vector_store = VectorStore()
