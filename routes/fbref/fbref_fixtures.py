from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from services.fbref.fbref_service import FBREFService


router = APIRouter(tags=["Fbref Fixtures"])

fbs = FBREFService(
    seasons='2526',
    league='ENG-Premier League'
)

@router.get("/fixtures")
async def fixtures(week: Optional[int] = Query(None, description="Optional week to return from JSON")):
    """
    Return fixtures from JSON only.
    - If `week` is provided, return that week.
    - If no week is provided, return the upcoming week (yet to be played) without enrichment.
    """
    try:
        data = fbs.get_fixtures(week)
        return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
