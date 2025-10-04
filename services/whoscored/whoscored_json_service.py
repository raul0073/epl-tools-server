from difflib import SequenceMatcher
import json
from pathlib import Path
from typing import List, Optional
import pandas as pd
from datetime import datetime
from models.fotmob.fixture import FotMobFixture

WHO_JSON_PATH = "data/whoscored/fixtures/ENG-Premier League_2526.json"
class WhoScoredJSONService:
    def __init__(self, json_file: str = WHO_JSON_PATH):
        self.json_file = Path(json_file)
        if not self.json_file.exists():
            raise FileNotFoundError(f"WhoScored fixture file not found: {json_file}")
        self.fixtures: pd.DataFrame = self._load_json()

    def _load_json(self) -> pd.DataFrame:
        import json
        from pathlib import Path

        file_path = Path(self.json_file)
        if not file_path.exists():
            raise FileNotFoundError(f"WhoScored fixture file not found: {self.json_file}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        fixtures = data.get("fixtures", [])
        df = pd.DataFrame(fixtures) if fixtures else pd.DataFrame()

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], utc=True)
        if "home_team" in df.columns:
            df["home_team_lower"] = df["home_team"].str.lower()
        if "away_team" in df.columns:
            df["away_team_lower"] = df["away_team"].str.lower()

        return df

    @staticmethod
    def similar(a: str, b: str) -> float:
        """Return a similarity ratio between 0 and 1."""
        return SequenceMatcher(None, a, b).ratio()

    def enrich_fixture(self, fixture: FotMobFixture) -> FotMobFixture:
        """
        Enrich a FotMobFixture with WhoScored match ID and full match data.
        Always ensures incidents are included if available.
        """
        df = self.fixtures.copy()

        # --- Step 1: Try to match by existing WhoScored game_id ---
        if fixture.whoscored_match_id:
            match_row = df[df["game_id"].astype(str) == str(fixture.whoscored_match_id)]
            if not match_row.empty:
                match_data = match_row.iloc[0].to_dict()
                fixture.whoscored_match_id = str(match_data["game_id"])
                fixture.whoscored = match_data
                return fixture  # ✅ Found exact match

        # --- Step 2: Match by date ±15 min and team similarity ---
        match_ts = pd.Timestamp(fixture.date)
        if match_ts.tzinfo is None:
            match_ts = match_ts.tz_localize("UTC")
        else:
            match_ts = match_ts.tz_convert("UTC")

        df_filtered = df[(df["date"] - match_ts).abs() <= pd.Timedelta(minutes=15)]
        if df_filtered.empty:
            fixture.whoscored_match_id = None
            fixture.whoscored = None
            return fixture

        # Compute best team similarity
        home_lower = fixture.home_team.lower()
        away_lower = fixture.away_team.lower()
        best_score = 0
        best_match = None

        for _, row in df_filtered.iterrows():
            home_score = self.similar(home_lower, row["home_team_lower"])
            away_score = self.similar(away_lower, row["away_team_lower"])
            total_score = home_score + away_score
            if total_score > best_score:
                best_score = total_score
                best_match = row

        if best_match is not None:
            match_data = best_match.to_dict()
            fixture.whoscored_match_id = str(match_data["game_id"])
            fixture.whoscored = match_data
        else:
            fixture.whoscored_match_id = None
            fixture.whoscored = None

        return fixture