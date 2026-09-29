"""
Prompts and Schemas for LLM Extraction Pipeline.
"""

from typing import Dict, Any
import json

# ── Controlled Vocabularies ──────────────────────────────────────

MEMORY_TYPES = [
    "photo", "screenshot", "document", "video", 
    "person_image", "object_image", "other"
]

CLUE_TYPES = [
    "person", "location", "event_trip", "object", 
    "approximate_time", "activity", "visual_appearance", 
    "text_content", "context", "other"
]

FORGOTTEN_INFO_TYPES = [
    "exact_date", "exact_location", "album", "filename", 
    "person_name", "object_name", "search_terms", "other"
]

RETRIEVAL_METHODS = [
    "keyword_search", "timeline_browsing", "album_browsing", 
    "scrolling", "face_person_search", "visual_scanning", 
    "workaround", "other"
]

FAILURE_REASONS = [
    "cannot_formulate_query", "too_many_results", 
    "forgotten_date_location", "context_not_translatable_to_keywords", 
    "difficulty_describing_visual", "uncertainty_between_similar", 
    "feature_missing", "other"
]

# ── Schemas ──────────────────────────────────────────────────────

# The JSON Schema that the LLM must strictly follow
EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "episodes": {
            "type": "array",
            "description": "List of retrieval episodes extracted from the feedback. Can be empty if no specific episodes are mentioned.",
            "items": {
                "type": "object",
                "properties": {
                    "memory_type": {
                        "type": "string",
                        "enum": MEMORY_TYPES,
                        "description": "The type of memory the user is trying to retrieve."
                    },
                    "remembered_clues": {
                        "type": "array",
                        "items": {"type": "string", "enum": CLUE_TYPES},
                        "description": "Information the user remembers about the target."
                    },
                    "forgotten_info": {
                        "type": "array",
                        "items": {"type": "string", "enum": FORGOTTEN_INFO_TYPES},
                        "description": "Critical indexing information the user has forgotten."
                    },
                    "retrieval_method": {
                        "type": "array",
                        "items": {"type": "string", "enum": RETRIEVAL_METHODS},
                        "description": "How the user attempted to find the item."
                    },
                    "is_successful": {
                        "type": ["boolean", "null"],
                        "description": "Whether the retrieval was ultimately successful. Null if unknown."
                    },
                    "failure_reason": {
                        "type": ["string", "null"],
                        "enum": FAILURE_REASONS + [None],
                        "description": "Why the retrieval failed, if applicable."
                    },
                    "evidence_quote": {
                        "type": "string",
                        "description": "A direct, exact quote from the user's text proving this episode."
                    },
                    "user_emotion": {
                        "type": "string",
                        "description": "The emotional state of the user (e.g., frustrated, desperate, happy, nostalgic)."
                    }
                },
                "required": [
                    "memory_type", "remembered_clues", "forgotten_info", 
                    "retrieval_method", "is_successful", "evidence_quote"
                ]
            }
        }
    },
    "required": ["episodes"]
}

# ── Prompts ──────────────────────────────────────────────────────

SYSTEM_PROMPT = f"""You are an expert UX Research Analyst.
Your task is to read user feedback about Google Photos and extract structured "Retrieval Episodes".

A Retrieval Episode is a specific instance where a user describes trying to find a past photo, video, or screenshot.
One piece of feedback might contain 0, 1, or multiple retrieval episodes.

Extract ONLY information present in the text. Do not hallucinate or assume.
Use null for fields where the text does not provide the information.
The `evidence_quote` MUST be an exact, verbatim substring of the provided text.

You MUST respond with a valid JSON object matching this schema:
{json.dumps(EXTRACTION_SCHEMA, indent=2)}
"""

FEW_SHOT_EXAMPLES = [
    {
        "role": "user",
        "content": "I am so frustrated. I know I took a picture of a receipt for a monitor I bought at Best Buy in 2019, but searching 'receipt' or 'Best Buy' brings up nothing. I can't even remember the exact month."
    },
    {
        "role": "assistant",
        "content": json.dumps({
            "episodes": [
                {
                    "memory_type": "document",
                    "remembered_clues": ["object", "text_content", "approximate_time"],
                    "forgotten_info": ["exact_date"],
                    "retrieval_method": ["keyword_search"],
                    "is_successful": False,
                    "failure_reason": "feature_missing",
                    "evidence_quote": "searching 'receipt' or 'Best Buy' brings up nothing",
                    "user_emotion": "frustrated"
                }
            ]
        })
    },
    {
        "role": "user",
        "content": "Search is completely broken for screenshots. I have a screenshot of a funny tweet from last year. I searched for the exact text in the tweet, and Google Photos says no results. But when I manually scroll back to last year, there it is!"
    },
    {
        "role": "assistant",
        "content": json.dumps({
            "episodes": [
                {
                    "memory_type": "screenshot",
                    "remembered_clues": ["text_content", "approximate_time"],
                    "forgotten_info": ["exact_date"],
                    "retrieval_method": ["keyword_search", "scrolling"],
                    "is_successful": True,
                    "failure_reason": "feature_missing",
                    "evidence_quote": "when I manually scroll back to last year, there it is",
                    "user_emotion": "annoyed"
                }
            ]
        })
    }
]

def get_extraction_messages(text: str) -> list:
    """Build the full message array for the LLM extraction call."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(FEW_SHOT_EXAMPLES)
    messages.append({"role": "user", "content": text})
    return messages
