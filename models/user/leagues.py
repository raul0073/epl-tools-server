from datetime import datetime, timezone
from typing import List
from pydantic import BaseModel


class PrivateLeagueRules(BaseModel):
    points_for_bullseye: int = 3
    points_for_win: int = 1
    points_for_loss: int = 0
    points_for_top_scorer: int = 10
    points_for_assist_king: int = 10
    points_for_champion: int = 10
    points_per_relegted_team: int = 5



class LeagueManager(BaseModel):
    user_id: str
    team_name: str
    points: int


class PrivateLeague(BaseModel):
    id: str
    name: str
    rules: PrivateLeagueRules
    code: str
    admin: str  
    managers: List[LeagueManager]
    created_at: datetime = datetime.now(timezone.utc)

