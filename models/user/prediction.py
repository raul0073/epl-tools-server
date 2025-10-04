

from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel


# -----------------------------
# Match prediction schema
# -----------------------------
class MatchPrediction(BaseModel):
    game_id: str 
    home_team: Optional[str] = None
    away_team: Optional[str] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    created_at: datetime = datetime.now(timezone.utc)

# -----------------------------
# Round prediction schema
# -----------------------------
class RoundPredictions(BaseModel):
    matches: List[MatchPrediction]
    
    
Predictions = Dict[str, RoundPredictions]  

# -----------------------------
# Season-long predictions
# -----------------------------
class SeasonPredictions(BaseModel):
    top_scorer: Optional[str] = None
    league_champion: Optional[str] = None
    assist_king: Optional[str] = None
    relegated_teams: Optional[List[str]] = []
    created_at: Optional[datetime] = None
    
