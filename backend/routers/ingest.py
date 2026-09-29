"""
Ingestion API routes.
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Dict
from pydantic import BaseModel, Field

from backend.db.database import get_db
from backend.models.feedback import FeedbackItem, SourceType, ExtractionStatus
from backend.services.ingestion.csv_adapter import CsvJsonAdapter
from backend.services.ingestion.reddit_adapter import RedditAdapter
from backend.services.ingestion.youtube_adapter import YouTubeAdapter
from backend.services.ingestion.playstore_adapter import PlayStoreAdapter
from backend.services.ingestion.appstore_adapter import AppStoreAdapter
from backend.services.ingestion.community_adapter import CommunityAdapter
from backend.services.ingestion.dedup import DedupEngine
from backend.services.extraction.relevance import RelevanceClassifier
from backend.services.extraction.extractor import EpisodeExtractor


router = APIRouter(prefix="/api/ingest", tags=["Ingestion"])


class SourceStats(BaseModel):
    total_fetched: int
    new_ingested: int
    duplicates: int
    noise_filtered: int

class IngestStats(BaseModel):
    ingested: int
    duplicates: int
    skipped: int
    source_breakdown: Dict[str, SourceStats] = Field(default_factory=dict)


class ScrapeRequest(BaseModel):
    source: str
    query: str
    subreddits: Optional[str] = "googlephotos"
    limit: Optional[int] = 100

class ExtractStats(BaseModel):
    relevance_classified: int
    episodes_extracted: int

@router.post("/extract", response_model=ExtractStats)
def trigger_extraction(batch_size: int = 10, db: Session = Depends(get_db)):
    """
    Trigger the AI Extraction Pipeline.
    1. Runs Relevance Classifier on pending items.
    2. Runs Episode Extractor on relevant items.
    """
    try:
        # Step 1: Relevance Classification
        classifier = RelevanceClassifier(db)
        classified_count = classifier.process_batch(batch_size=batch_size)
        
        # Step 2: Episode Extraction
        extractor = EpisodeExtractor(db)
        extracted_count = extractor.process_batch(batch_size=batch_size)
        
        return ExtractStats(
            relevance_classified=classified_count,
            episodes_extracted=extracted_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction pipeline error: {e}")

@router.post("/upload", response_model=IngestStats)
async def upload_feedback(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Accepts CSV or JSON file upload, parses, deduplicates, and saves to database.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")
        
    # Read file content
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")
        
    # Check size limit (e.g., 100MB max) - usually handled by web server, but basic check here
    if len(content) > 100 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 100MB).")

    # Process through adapter
    adapter = CsvJsonAdapter()
    try:
        parsed_items, total_fetched, noise_filtered = adapter.process_file(content, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing file: {e}")
        
    if not parsed_items:
        raise HTTPException(status_code=400, detail="No valid data rows found or all skipped.")

    # Deduplicate and save
    dedup = DedupEngine(db)
    try:
        inserted_count, duplicate_count = dedup.save_new_items(parsed_items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error during save: {e}")
        
    source_stats = SourceStats(
        total_fetched=total_fetched,
        new_ingested=inserted_count,
        duplicates=duplicate_count,
        noise_filtered=noise_filtered
    )
    
    return IngestStats(
        ingested=inserted_count,
        duplicates=duplicate_count,
        skipped=noise_filtered,
        source_breakdown={"csv_upload": source_stats}
    )


@router.post("/scrape", response_model=IngestStats)
def trigger_scrape(request: ScrapeRequest, db: Session = Depends(get_db)):
    """
    Trigger scraping from a specific source (supported: 'reddit', 'youtube').
    """
    source = request.source.lower()
    
    if source == "reddit":
        try:
            adapter = RedditAdapter()
            parsed_items, total_fetched, noise_filtered = adapter.process(
                source_path_or_query=request.query,
                subreddits=request.subreddits,
                limit=request.limit,
                query=request.query
            )
        except ValueError as e:
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error scraping Reddit: {e}")
            
    elif source == "youtube":
        try:
            adapter = YouTubeAdapter()
            parsed_items, total_fetched, noise_filtered = adapter.process(
                source_path_or_query=request.query,
                max_videos=5,
                max_comments_per_video=request.limit or 20
            )
        except ValueError as e:
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error scraping YouTube: {e}")
            
    elif source == "playstore":
        try:
            adapter = PlayStoreAdapter()
            parsed_items, total_fetched, noise_filtered = adapter.process(
                source_path_or_query="com.google.android.apps.photos",
                limit=request.limit or 200
            )
        except ValueError as e:
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error scraping Play Store: {e}")
            
    elif source == "appstore":
        try:
            adapter = AppStoreAdapter()
            parsed_items, total_fetched, noise_filtered = adapter.process(
                source_path_or_query="google-photos",
                app_id=962164605,
                limit=request.limit or 100
            )
        except ValueError as e:
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error scraping App Store: {e}")

    elif source == "community":
        try:
            adapter = CommunityAdapter()
            parsed_items, total_fetched, noise_filtered = adapter.process(
                source_path_or_query=request.query
            )
        except ValueError as e:
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error scraping Community: {e}")
            
    else:
        raise HTTPException(status_code=400, detail=f"Source '{request.source}' is not supported.")

    if not parsed_items:
        source_stats = SourceStats(
            total_fetched=total_fetched,
            new_ingested=0,
            duplicates=0,
            noise_filtered=noise_filtered
        )
        return IngestStats(ingested=0, duplicates=0, skipped=noise_filtered, source_breakdown={source: source_stats})

    dedup = DedupEngine(db)
    try:
        inserted_count, duplicate_count = dedup.save_new_items(parsed_items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error during save: {e}")

    source_stats = SourceStats(
        total_fetched=total_fetched,
        new_ingested=inserted_count,
        duplicates=duplicate_count,
        noise_filtered=noise_filtered
    )

    return IngestStats(
        ingested=inserted_count,
        duplicates=duplicate_count,
        skipped=noise_filtered,
        source_breakdown={source: source_stats}
    )


@router.get("/status")
def get_ingestion_status(db: Session = Depends(get_db)):
    """
    Returns counts of feedback items.
    """
    total = db.query(func.count(FeedbackItem.id)).scalar() or 0
    relevant = db.query(func.count(FeedbackItem.id)).filter(FeedbackItem.is_relevant == True).scalar() or 0
    pending_extraction = db.query(func.count(FeedbackItem.id)).filter(FeedbackItem.extraction_status == ExtractionStatus.PENDING).scalar() or 0
    
    return {
        "total_feedback": total,
        "relevant_feedback": relevant,
        "pending_extraction": pending_extraction
    }


@router.get("/sources")
def get_sources_status(db: Session = Depends(get_db)):
    """
    List configured sources and counts per source.
    """
    stats = {}
    for source in SourceType:
        count = db.query(func.count(FeedbackItem.id)).filter(FeedbackItem.source == source).scalar() or 0
        stats[source.value] = {"count": count}
        
    return {"sources": stats}
