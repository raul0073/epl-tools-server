from typing import Dict, Optional, List
from pydantic import BaseModel, EmailStr

from models.user.prediction import Predictions, RoundPredictions, MatchPrediction, SeasonPredictions
from models.user.points import Points
from models.user.leagues import PrivateLeague


# -----------------------------
# User Create Schema
# -----------------------------
class UserCreate(BaseModel):
    # user details
    email: EmailStr
    name: Optional[str] = None
    team_name: Optional[str] = None
    picture: Optional[str] = None

    # predictions
    predictions: Optional[Dict[int, RoundPredictions]] = {}

    # season predictions
    season_predictions: Optional[SeasonPredictions] = None

    # points
    points: Optional[Points] = None


# -----------------------------
# User Read Schema
# -----------------------------
class UserRead(BaseModel):
    id: str
    email: EmailStr
    name: Optional[str] = None
    team_name: Optional[str] = None
    picture: Optional[str] = None

    # predictions
    predictions: Optional[Dict[int, RoundPredictions]] = {}

    # season predictions
    season_predictions: Optional[SeasonPredictions] = None

    # points
    points: Optional[Points] = None

    # private leagues
    private_leagues: List[PrivateLeague] = []
