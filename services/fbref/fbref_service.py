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
                home_team = f.get("home_team") or ''
                away_team = f.get("away_team") or ''
                f["temp_id"] = f"{f.get('week')}_{home_team.replace(' ', '')}_{away_team.replace(' ', '')}_{f.get('date')}"
        return fixtures

    # -------------------------
    # READ FROM JSON ONLY, GET UPCOMING FIXTURES OR BY WEEK
    # -------------------------


    def get_fixtures(self, week: Optional[int] = None) -> Dict[str, Any]:
        if not self.fixtures_file.exists():
            return {"meta": {}, "fixtures": []}

        with open(self.fixtures_file, "r", encoding="utf-8") as f:
            fixtures_data = json.load(f)

        fixtures = fixtures_data.get("fixtures", [])

        # Add temp_id to matches without a valid game_id
        for idx, f in enumerate(fixtures):
            if not f.get("game_id"):
                fixtures[idx] = self.add_temp_ids([f])[0]

        if week is not None:
            fixtures_data["fixtures"] = [f for f in fixtures if f.get("week") == week]
        else:
            # --- Find the next round (gameweek) ---
            now = datetime.now()
            next_fixture_dt = None
            next_week = None

            for f in fixtures:
                date_str = f.get("date")
                time_str = f.get("time")

                if not date_str or not time_str:
                    continue

                try:
                    fixture_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                except ValueError:
                    continue

                if fixture_dt > now:
                    if next_fixture_dt is None or fixture_dt < next_fixture_dt:
                        next_fixture_dt = fixture_dt
                        next_week = f.get("week")

            if next_week is not None:
                fixtures_data["fixtures"] = [f for f in fixtures if f.get("week") == next_week]
            else:
                # fallback: return last available week if season is over
                last_week = max((f.get("week") for f in fixtures if f.get("week")), default=None)
                fixtures_data["fixtures"] = [f for f in fixtures if f.get("week") == last_week]

        return fixtures_data


    # -------------------------
    # UPDATE JSON + ENRICH MATCHES
    # -------------------------
    def update_json(self, week: Optional[int] = None) -> Dict[str, Any]:
        # Read schedule from FBref
        df: pd.DataFrame = self.fbref.read_schedule()
        if df is None or df.empty:
            return {"meta": {}, "fixtures": []}
        df = df.fillna(0)

        # Flatten nested dicts/lists
        def flatten_dict(d: dict) -> dict:
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

        # -------------------------
        # PRESERVE EXISTING ENRICHED FLAGS
        # -------------------------
        existing_data = {}
        if self.fixtures_file.exists():
            with open(self.fixtures_file, "r", encoding="utf-8") as f:
                old_data = json.load(f)
                for f_old in old_data.get("fixtures", []):
                    key = f_old.get("game_id") or f_old.get("temp_id")
                    if key:
                        existing_data[str(key)] = {
                            "enriched": f_old.get("enriched", False),
                            "events": f_old.get("events", []),
                        }

        # Assign preserved data back
        for f in fixtures_list:
            key = f.get("game_id") or f.get("temp_id")
            if key and str(key) in existing_data:
                f["enriched"] = existing_data[str(key)]["enriched"]
                f["events"] = existing_data[str(key)]["events"]
            else:
                f["enriched"] = False
                f["events"] = []

        # Filter by week if specified
        if week is not None:
            fixtures_list = [f for f in fixtures_list if f.get("week") == week]

        fixtures_data = {
            "meta": {
                "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "league": self.league,
                "season": self.seasons[0],
            },
            "fixtures": fixtures_list,
        }

        # -------------------------
        # ENRICH ONLY UNENRICHED MATCHES
        # -------------------------
        fixtures_data = self.enrich_completed_fixtures_incremental(fixtures_data)

        # Write JSON
        with open(self.fixtures_file, "w", encoding="utf-8") as f:
            json.dump(fixtures_data, f, ensure_ascii=False, indent=2)

        return fixtures_data

    # -------------------------
    # INCREMENTAL ENRICHMENT
    # -------------------------
    def enrich_completed_fixtures_incremental(self, fixtures_data: dict) -> dict:
        for fixture in fixtures_data.get("fixtures", []):
            game_id = fixture.get("game_id")
            if fixture.get("enriched", False):
                print(f"ℹ️ Match {game_id} already enriched, skipping")
                continue

            if not game_id:
                print(f"⚠️ Match {game_id} invalid, skipping enrichment")
                fixture["events"] = []
                fixture["enriched"] = False
                continue

            # Enrich match
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

        return fixtures_data
