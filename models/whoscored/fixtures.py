from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class Incident(BaseModel):
    minute: str
    type: int
    subType: int
    playerName: str
    playerId: int
    participatingPlayerName: Optional[str] = None
    participatingPlayerId: Optional[int] = 0
    runningScore: Optional[float] = None
    field: int
    period: int


class Fixture(BaseModel):
    stage_id: int
    game_id: int
    status: int
    start_time: datetime
    home_team_id: int
    home_team: str
    home_yellow_cards: int
    home_red_cards: int
    away_team_id: int
    away_team: str
    away_yellow_cards: int
    away_red_cards: int
    has_incidents_summary: bool
    has_preview: bool
    score_changed_at: Optional[datetime] = None
    elapsed: Optional[str] = None
    last_scorer: Optional[float] = None
    is_top_match: bool
    home_team_country_code: str
    away_team_country_code: str
    comment_count: int
    is_lineup_confirmed: bool
    is_stream_available: bool
    match_is_opta: bool
    home_team_country_name: str
    away_team_country_name: str
    date: datetime
    home_score: Optional[float] = None
    away_score: Optional[float] = None
    incidents: List[Incident] = []
    bets: int
    aggregate_winner_field: int
    winner_field: Optional[float] = None
    period: int
    extra_result_field: int
    home_extratime_score: int
    away_extratime_score: int
    home_penalty_score: int
    away_penalty_score: int
    started_at_utc: Optional[datetime] = None
    first_half_ended_at_utc: Optional[datetime] = None
    second_half_started_at_utc: Optional[datetime] = None
    stage: int
