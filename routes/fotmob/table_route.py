
from fastapi import APIRouter,HTTPException
from typing import List

from services.fotmob.fotmob_service import FotMobService

router = APIRouter(tags=["Fotmob Table"])


fotmob_service = FotMobService(
    seasons='2526',
    league='ENG-Premier League'
)


@router.get("/table", response_model=List[dict])
async def fixtures():
    try:
        return fotmob_service.get_table()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
 