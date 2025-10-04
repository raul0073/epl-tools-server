import json
from pathlib import Path
from typing import List, Tuple, Dict
from datetime import datetime
from models.fotmob.fixture import FotMobFixture

CORE_PATH = 'data/fotmob/fixtures/ENG-Premier League_2526.json'

class FotMobJSONService:
    """
    Service to read saved FotMob fixtures JSON and provide filtering utilities,
    including access to the meta information.
    """

    def __init__(self):
        self.json_file = Path(CORE_PATH)
        if not self.json_file.exists():
            raise FileNotFoundError(f"Fixture file not found: {CORE_PATH}")
        self.fixtures: List[FotMobFixture] = self._load_fixtures()
        self.meta: Dict = self._load_meta()

    def _load_json_file(self) -> dict:
        with open(self.json_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_fixtures(self) -> List[FotMobFixture]:
        data = self._load_json_file()
        fixtures_list = data.get("fixtures", [])
        return [FotMobFixture(**item) for item in fixtures_list]

    def _load_meta(self) -> dict:
        data = self._load_json_file()
        return data.get("meta", {})

    def all(self) -> List[FotMobFixture]:
        """Return all fixtures"""
        return self.fixtures

    def load_json(self) -> dict:
        """Return full JSON including meta + fixtures"""
        return {
            "meta": self.meta,
            "fixtures": [f.dict() for f in self.fixtures]  # convert Pydantic models to dict
        }

    def get_by_round(self, round_number: int) -> List[FotMobFixture]:
        return [f for f in self.fixtures if f.round == round_number]

    def get_by_week(self, week: str) -> List[FotMobFixture]:
        return [f for f in self.fixtures if f.week == week]

    def get_by_status(self, status: str) -> List[FotMobFixture]:
        return [f for f in self.fixtures if f.status == status]

    def get_by_team(self, team_name: str) -> List[FotMobFixture]:
        return [
            f for f in self.fixtures
            if f.home_team.lower() == team_name.lower() or f.away_team.lower() == team_name.lower()
        ]

    def get_by_date(self, date: datetime) -> List[FotMobFixture]:
        return [f for f in self.fixtures if f.date.date() == date.date()]
