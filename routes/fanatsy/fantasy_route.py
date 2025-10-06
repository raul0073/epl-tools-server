from fastapi import APIRouter, HTTPException
from services.fantasy.fantasy_service import FantasyService

router = APIRouter(tags=["Fantasy"])


@router.get("/bootstrap")
async def get_bootstrap(team_id: int):
    """
    Fetch global Fantasy Premier League bootstrap-static data (players, teams, events).
    """
    try:
        service = FantasyService(team_id)
        data = service.get_bootstrap()
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/team/{team_id}")
async def get_team_info(team_id: int):
    """
    Fetch basic team info (public).
    """
    try:
        service = FantasyService(team_id)
        data = service.get_team_info()
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/team/{team_id}/picks/{gw}")
async def get_team_picks(team_id: int, gw: int):
    """
    Fetch squad picks for a specific gameweek (public).
    """
    try:
        service = FantasyService(team_id)
        data = service.get_team_picks(gw)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/team/{team_id}/wishlist")
async def get_wishlist(team_id: int):
    """
    Get wishlist players for this team (local persistence).
    """
    try:
        service = FantasyService(team_id)
        data = service.get_wishlist()
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/team/{team_id}/wishlist/add/{player_id}")
async def add_to_wishlist(team_id: int, player_id: int):
    """
    Add player to wishlist.
    """
    try:
        service = FantasyService(team_id)
        data = service.add_to_wishlist(player_id)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/team/{team_id}/wishlist/remove/{player_id}")
async def remove_from_wishlist(team_id: int, player_id: int):
    """
    Remove player from wishlist.
    """
    try:
        service = FantasyService(team_id)
        data = service.remove_from_wishlist(player_id)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/players/{position_code}")
async def get_players_by_position(team_id: int, position_code: int):
    """
    Get players by position (GK=1, DEF=2, MID=3, FWD=4).
    """
    try:
        service = FantasyService(team_id)
        data = service.get_players_by_position(position_code)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
