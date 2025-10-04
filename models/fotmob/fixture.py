from pydantic import BaseModel, HttpUrl, field_validator
from typing import Optional
from datetime import datetime

from pydantic import BaseModel

from models.whoscored.fixtures import Fixture

class FotMobFixture(BaseModel):
    round: int
    week: str
    date: datetime
    home_team: str 
    away_team: str
    home_score: int
    away_score: int
    status: str | int
    game_id: str
    url: str
    whoscored_match_id: Optional[str] = None
    whoscored: Optional[dict] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "from_attributes": True,
    }

    @field_validator("home_score", "away_score", mode="before")
    @classmethod
    def parse_score(cls, v):
        try:
            return int(str(v).strip())
        except:
            return 0