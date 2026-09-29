import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from groq import Groq

from backend.config import settings
from backend.services.rag.retriever import retriever
from backend.services.rag.context_builder import context_builder

logger = logging.getLogger(__name__)

class Citation(BaseModel):
    source_index: int
    source_type: str
    metadata: Dict[str, Any]
    text_snippet: str

class AnswerResponse(BaseModel):
    answer: str
    citations: List[Citation]
    evidence_count: int
    confidence: str

class QueryEngine:
    """End-to-end RAG pipeline."""
    
    def __init__(self):
        try:
            self.client = Groq(api_key=settings.GROQ_API_KEY)
            self.model = settings.GROQ_MODEL
        except Exception as e:
            logger.error(f"Failed to initialize Groq client in QueryEngine: {e}")
            raise
            
        self.system_prompt = """You are a research analyst. Answer the question using ONLY the evidence provided below. 
Cite specific sources using [Source N] notation in your answer. 
If the evidence is insufficient to answer the question, explicitly say so. 
Never fabricate quotes, statistics, or features.

Evidence:
{context}"""

    def ask(self, question: str, filter_metadata: Optional[Dict[str, Any]] = None) -> AnswerResponse:
        """Process question and generate grounded answer."""
        # 1. Retrieve
        # L2 distance threshold of 1.0 is relatively loose for bge-large normalized vectors.
        # It's better to keep it around 1.2 or don't strictly filter in small datasets.
        retrieved_docs = retriever.retrieve(query=question, top_k=15, similarity_threshold=1.5, filter_metadata=filter_metadata)
        
        # 2. Build context
        context_str = context_builder.build_context(retrieved_docs)
        
        # 3. Build prompt
        sys_msg = self.system_prompt.format(context=context_str)
        messages = [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": question}
        ]
        
        # 4. Generate answer
        logger.info("Generating answer via Groq LLM...")
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                max_tokens=1500
            )
            answer = completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling Groq for RAG answer: {e}")
            answer = f"Sorry, I encountered an error generating the answer: {str(e)}"
            
        # 5. Build citations
        citations = []
        for i, doc in enumerate(retrieved_docs):
            citations.append(Citation(
                source_index=i+1,
                source_type=doc["type"],
                metadata=doc["metadata"],
                text_snippet=doc["document"][:200] + "..." # Just a preview
            ))
            
        # 6. Confidence calculation
        doc_count = len(retrieved_docs)
        if doc_count == 0:
            confidence = "None"
        elif doc_count < 3:
            confidence = "Low"
        elif doc_count < 8:
            confidence = "Medium"
        else:
            confidence = "High"
            
        return AnswerResponse(
            answer=answer,
            citations=citations,
            evidence_count=doc_count,
            confidence=confidence
        )

query_engine = QueryEngine()
