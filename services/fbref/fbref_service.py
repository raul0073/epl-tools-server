from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
import soccerdata as sd


class FBREFService:
    def __init__(self, league: str, seasons: Optional[str] = None):
        self.league = league
        self.seasons = [seasons] if seasons else [2526]
        self.fbref = sd.FBref(leagues=[league], seasons=self.seasons)
        self.fixtures_file = Path("data/fbref/fixtures") / f"{self.league}_{self.seasons[0]}.json"
        self.fixtures_file.parent.mkdir(parents=True, exist_ok=True)
        
    def add_temp_ids(self, fixtures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Assign a unique temp_id to every fixture based on week + teams + date"""
        for f in fixtures:
            if "temp_id" not in f or not f["temp_id"]:
                home_team = f.get('home_team') or ''
                away_team = f.get('away_team') or ''
                f["temp_id"] = f"{f.get('week')}_{home_team.replace(' ', '')}_{away_team.replace(' ', '')}_{f.get('date')}"
        return fixtures
    # -------------------------
    # READ FROM JSON ONLY, GET UPCOMING FIXTURES OR BY WEEK
    # -------------------------
    def get_fixtures(self, week: Optional[int] = None):
        """Return fixtures from JSON, optionally filtered by week/round."""
        if not self.fixtures_file.exists():
            print(f"⚠️ Fixtures JSON not found: {self.fixtures_file}")
            return {"meta": {}, "fixtures": []}

        with open(self.fixtures_file, "r", encoding="utf-8") as f:
            fixtures_data = json.load(f)

        fixtures = fixtures_data.get("fixtures", [])
        now = datetime.now(timezone.utc)

        # Add temp_id to all matches with game_id == 0
        for idx, f in enumerate(fixtures):
            if f.get("game_id") == 0:
                fixtures[idx] = self.add_temp_ids([f])[0]

        # Filter by week if specified
        if week is not None:
            fixtures_data["fixtures"] = [f for f in fixtures if f.get("week") == week]
            print(f"🔹 Returning fixtures for week {week}")
        else:
            # Determine upcoming week automatically
            upcoming_week = None
            for f in fixtures:
                try:
                    match_date = datetime.strptime(f.get("date", ""), "%Y-%m-%d").replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
                if match_date >= now:
                    upcoming_week = f.get("week")
                    break
            if upcoming_week:
                fixtures_data["fixtures"] = [f for f in fixtures if f.get("week") == upcoming_week]
                print(f"🔹 No week specified, returning upcoming week: {upcoming_week}")
            else:
                fixtures_data["fixtures"] = fixtures  # fallback: all fixtures

        return fixtures_data

    # -------------------------
    # UPDATE JSON + ENRICH MATCH BY MATCH!!! IF ENRICH=TRUE SKIP
    # -------------------------
    def update_json(self, week: Optional[int] = None):
        """Fetch fresh schedule from FBref, enrich completed matches, rewrite JSON."""
        df: pd.DataFrame = self.fbref.read_schedule()
        if df is None or df.empty:
            print("⚠️ No fixtures found in schedule")
            return {"meta": {}, "fixtures": []}

        df = df.fillna(0)

        # Flatten nested dicts/lists
        def flatten_dict(d):
            flat = {}
            for k, v in d.items():
                if isinstance(v, dict):
                    for subk, subv in v.items():
                        flat[f"{k}_{subk}"] = subv
                elif isinstance(v, list):
                    flat[k] = json.dumps(v, ensure_ascii=False)
                else:
                    flat[k] = v
            return flat

        df_copy = df.copy()
        for col in df_copy.select_dtypes(include=["datetime", "datetimetz"]):
            df_copy[col] = df_copy[col].astype(str)

        fixtures_list = [flatten_dict(row) for row in df_copy.to_dict(orient="records")]

        fixtures_data = {
            "meta": {
                "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "league": self.league,
                "season": self.seasons[0],
            },
            "fixtures": fixtures_list,
        }

        # Filter by week if given
        if week is not None:
            fixtures_data["fixtures"] = [f for f in fixtures_data["fixtures"] if f.get("week") == week]
            print(f"🔹 Updating JSON for week {week}")

        # Enrich completed matches only
        fixtures_data = self.enrich_completed_fixtures_incremental(fixtures_data)

        # Write JSON
        with open(self.fixtures_file, "w", encoding="utf-8") as f:
            json.dump(fixtures_data, f, ensure_ascii=False, indent=2)

        return fixtures_data

    # -------------------------
    # INCREMENTAL ENRICHMENT
    # -------------------------
    def enrich_completed_fixtures_incremental(self, fixtures_data: dict):
        """Go game by game, enrich only if match has passed, not already enriched, and game_id is valid."""
        now = datetime.now(timezone.utc)

        for fixture in fixtures_data.get("fixtures", []):
            game_id = fixture.get("game_id")
            enriched = fixture.get("enriched", False)

            # Skip if already enriched or game_id is 0/None
            if enriched or game_id in [0, None]:
                print(f"⏭️ Skipping fixture {game_id} (already enriched or no valid game_id)")
                continue

            # Parse match date
            match_date_str = fixture.get("date")
            try:
                match_date = datetime.strptime(match_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                match_date = now

            # Only enrich if match has passed
            if match_date < now:
                print(f"[1/1] Retrieving game with id={game_id}")
                try:
                    events_df = self.fbref.read_events(match_id=game_id)
                    fixture["events"] = events_df.to_dict(orient="records") if events_df is not None else []
                    fixture["enriched"] = True
                    print(f"✅ Enriched match {game_id}: {len(fixture['events'])} events")
                except Exception as e:
                    fixture["events"] = []
                    fixture["enriched"] = False
                    print(f"⚠️ Failed to enrich match {game_id}: {e}")
            else:
                fixture["events"] = []
                fixture["enriched"] = False
                print(f"⏳ Match {game_id} not finished, skipping enrichment")

        return fixtures_data
