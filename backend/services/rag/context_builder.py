import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ContextBuilder:
    """Assembles retrieved documents into a context window for the LLM."""
    
    def __init__(self, max_context_tokens: int = 6000):
        self.max_context_tokens = max_context_tokens

    def build_context(self, retrieved_docs: List[Dict[str, Any]]) -> str:
        """
        Builds the context string.
        """
        if not retrieved_docs:
            return "No relevant evidence found in the database."
            
        context_parts = []
        
        if len(retrieved_docs) < 3:
            context_parts.append(f"WARNING: Limited evidence available — the following is based on only {len(retrieved_docs)} source(s).\n")
            
        estimated_tokens = 0
        added_count = 0
        
        for i, doc in enumerate(retrieved_docs):
            source = doc['metadata'].get('source', 'unknown')
            date = doc['metadata'].get('date', 'unknown date')
            doc_type = doc['type']
            content = doc['document']
            
            # Simple token estimation (~4 chars per token)
            text = f"[Source {i+1}] [{doc_type} from {source} on {date}]: {content}\n\n"
            tokens = len(text) // 4
            
            if estimated_tokens + tokens > self.max_context_tokens:
                logger.info(f"Hit max token limit at {added_count} documents.")
                break
                
            context_parts.append(text)
            estimated_tokens += tokens
            added_count += 1
            
        return "".join(context_parts)

context_builder = ContextBuilder()
