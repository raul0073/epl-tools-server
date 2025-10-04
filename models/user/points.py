from typing import Dict, List, Optional
from pydantic import BaseModel


class MatchPoints(BaseModel):
    game_id: str
    points: int


class SeasonPoints(BaseModel):
    top_scorer: int
    assist_king: int
    league_champion: Optional[int] = None
    relegated_teams: Optional[int] = None


class Points(BaseModel):
    total_points: int
    last_round_points: int
    matches: Dict[str, List[MatchPoints]]  
    season_points: SeasonPoints
