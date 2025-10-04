from pydantic import BaseModel

from models.user.leagues import PrivateLeague
from models.user.points import Points
from models.user.prediction import Predictions, SeasonPredictions


class User(BaseModel):
    id: str
    email: str
    name: str
    picture: str
    team_name: str
    predictions: Predictions
    private_leagues: list[PrivateLeague]
    season_predictions: SeasonPredictions
    points: Points
