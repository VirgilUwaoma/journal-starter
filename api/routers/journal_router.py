import logging
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException, Request, Depends
from repositories.postgres_repository import PostgresDB
from services.entry_service import EntryService
import services.llm_service as llm
from models.entry import Entry, EntryCreate
import logging

router = APIRouter()
logger = logging.getLogger("router")


async def get_entry_service() -> AsyncGenerator[EntryService, None]:
    async with PostgresDB() as db:
        yield EntryService(db)


@router.post("/entries")
async def create_entry(entry_data: EntryCreate, entry_service: EntryService = Depends(get_entry_service)):
    """Create a new journal entry."""
    try:
        # Create the full entry with auto-generated fields
        entry = Entry(
            work=entry_data.work,
            struggle=entry_data.struggle,
            intention=entry_data.intention
        )

        # Store the entry in the database
        created_entry = await entry_service.create_entry(entry.model_dump())

        # Return success response (FastAPI handles datetime serialization automatically)
        return {
            "detail": "Entry created successfully",
            "entry": created_entry
        }
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error creating entry: {str(e)}")

# Implements GET /entries endpoint to list all journal entries
# Example response: [{"id": "123", "work": "...", "struggle": "...", "intention": "..."}]


@router.get("/entries")
async def get_all_entries(entry_service: EntryService = Depends(get_entry_service)):
    """Get all journal entries."""
    result = await entry_service.get_all_entries()
    return {"entries": result, "count": len(result)}


@router.get("/entries/{entry_id}")
async def get_entry(request: Request, entry_id: str, entry_service: EntryService = Depends(get_entry_service)):
    """
    Return a single journal entry by ID
    """
    result = await entry_service.get_entry(entry_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Entry not found")
    return result


@router.patch("/entries/{entry_id}")
async def update_entry(entry_id: str, entry_update: dict, entry_service: EntryService = Depends(get_entry_service)):
    """Update a journal entry"""
    result = await entry_service.update_entry(entry_id, entry_update, partial=True)
    if not result:

        raise HTTPException(status_code=404, detail="Entry not found")

    return result

# TODO: Implement DELETE /entries/{entry_id} endpoint to remove a specific entry
# Return 404 if entry not found


@router.delete("/entries/{entry_id}")
async def delete_entry(entry_id: str, entry_service: EntryService = Depends(get_entry_service)):
    """
    Endpoint to delete a specific journal entry
    """

    result = await entry_service.get_entry(entry_id)
    if not result:
        raise HTTPException(
            status_code=404, detail=f"Entry {entry_id} not found")
    else:
        await entry_service.delete_entry(entry_id)
        return {"detail": f"Entry {entry_id} has been deleted successfully"}


@router.delete("/entries")
async def delete_all_entries(entry_service: EntryService = Depends(get_entry_service)):
    """Delete all journal entries"""
    await entry_service.delete_all_entries()
    return {"detail": "All entries deleted"}


@router.post("/entries/{entry_id}/analyze")
async def analyze_entry(entry_id: str, entry_service: EntryService = Depends(get_entry_service)):
    """
    Analyze a journal entry using AI.

    Returns sentiment, summary, key topics, entry_id, and created_at timestamp.

    Response format:
    {
        "entry_id": "string",
        "sentiment": "positive | negative | neutral",
        "summary": "2 sentence summary of the entry",
        "topics": ["topic1", "topic2", "topic3"],
        "created_at": "timestamp"
    }

    TODO: Implement this endpoint. Steps:
    1. Fetch the entry from database using entry_service.get_entry(entry_id)
    2. Return 404 if entry not found
    3. Combine work + struggle + intention into text
    4. Call llm_service.analyze_journal_entry(entry_text)
    5. Return the analysis result with entry_id and created_at timestamp
    """

    try:
        result = await entry_service.get_entry(entry_id)
        if not result:
            raise HTTPException(
                status_code=404, detail=f"Entry {entry_id} not found")
        analysis = await llm.analyze_journal_entry(entry_id, "text")
        return {"analysis": analysis}

    except Exception as e:
        logger.error(str(e))
        raise HTTPException(
            status_code=500, detail=f"Could not analyze entry")
