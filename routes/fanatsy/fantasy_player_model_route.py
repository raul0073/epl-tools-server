# routes/fantasy/fantasy_players_route.py
from fastapi import APIRouter, Query
from typing import Optional
from services.fantasy.fantasy_player_model_service import FantasyPlayerModelService

router = APIRouter(
    tags=["Fantasy Players"]
)

fbs = FantasyPlayerModelService(
    season='2526',
    league='ENG-Premier League'
)
@router.get("/by-position")
def get_players_by_position(
    position_code: Optional[int] = Query(None, description="Position code: 1=GK, 2=DEF, 3=MID, 4=FWD")
):
    """
    Return players filtered by position, enriched with next fixture and expected points.
    If position_code is not provided, returns all players grouped by position.
    """
    

    if position_code:
        players = fbs.get_players_by_position(position_code)
        return {"success": True, "players": players}

    # return all positions grouped
    return {
        "success": True,
        "players": {
            "GK": fbs.get_players_by_position(1),
            "DEF": fbs.get_players_by_position(2),
            "MID": fbs.get_players_by_position(3),
            "FWD": fbs.get_players_by_position(4),
        }
    }
