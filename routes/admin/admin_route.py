from typing import Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from services.fbref.fbref_service import FBREFService
from services.utils.points_resolver_service import PointsResolverService

router = APIRouter(
    tags=["Admin Actions"]
)

# Initialize FBREFService for Premier League 25/26
fbs = FBREFService(
    seasons='2526',
    league='ENG-Premier League'
)

# -----------------------------
# Route: Update FBref JSON + resolve points automatically
# -----------------------------
@router.get("/update")
async def update(
    background_tasks: BackgroundTasks,
    week: Optional[int] = Query(None, description="Optional week to return from JSON")
):
    """
    Update FBref JSON for a given week (or upcoming if none).
    Points resolver runs automatically after the update.
    """
    try:
        # Update FBref JSON
        data = fbs.update_json(week)

        # Trigger points resolver in background immediately
        resolver = PointsResolverService()
        background_tasks.add_task(resolver.resolve_and_save_all_users)

        return JSONResponse(content={
            "status": "success",
            "message": "FBref JSON updated. Points resolver running in background.",
            "data": data
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

