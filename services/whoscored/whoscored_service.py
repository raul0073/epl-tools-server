import json
from pathlib import Path
from typing import Optional, List
import pandas as pd
from datetime import datetime, timezone
import soccerdata as sd


class WhoScoredService:
    def __init__(self, league: str, seasons: Optional[str] = None):
        self.league = league
        self.seasons = [seasons] if seasons else [2526]
        # no_cache ensures fresh data every time
        self.ws = sd.WhoScored(leagues=[league], seasons=self.seasons, no_cache=True)

    def get_fixtures(self) -> dict:
        """
        Fetch all fixtures from WhoScored and ALWAYS overwrite the JSON.
        Past and future fixtures are updated fully.
        Returns JSON-like dict with meta + fixtures.
        """
        df: pd.DataFrame = self.ws.read_schedule(force_cache=False)
        if df is None or df.empty:
            return {"meta": {}, "fixtures": []}

        df = df.fillna(0)
        df["date"] = pd.to_datetime(df["date"], utc=True)

        file_path = Path("data/whoscored/fixtures") / f"{self.league}_{self.seasons[0]}.json"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert all fixtures to list of dicts
        final_fixtures: List[dict] = df.to_dict(orient="records")

        # Convert datetime columns to ISO strings for JSON
        datetime_cols = df.select_dtypes(include=["datetime", "datetimetz"]).columns
        for fixture in final_fixtures:
            for col in datetime_cols:
                fixture[col] = fixture[col].isoformat()

        # Prepare output with meta
        output = {
            "meta": {
                "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "league": self.league,
                "season": self.seasons[0],
            },
            "fixtures": final_fixtures,
        }

        # ALWAYS overwrite JSON file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"✅ WhoScored fixtures fully updated: {file_path}")
        return output

    def get_missing_players(self, match_id: int) -> List[dict]:
        df = self.ws.read_missing_players(match_id=match_id)
        if df is None or df.empty:
            return []
        return df.reset_index().to_dict(orient="records")
