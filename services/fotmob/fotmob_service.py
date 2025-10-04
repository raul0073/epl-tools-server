import json
import pandas as pd
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone
import soccerdata as sd


class FotMobService:
    def __init__(self, league: str, seasons: Optional[str] = None):
        self.league = league
        self.seasons = [seasons] if seasons else [2526]  # ✅ list not int
        self.fotmob = sd.FotMob(leagues=[league], seasons=self.seasons, no_cache=False)
        
    def get_table(self) -> List[dict]:
        df: pd.DataFrame = self.fotmob.read_league_table()
        df = df.fillna(0)

        # Flatten any nested dicts or lists to prevent pd.DataFrame issues
        def flatten_dict(d):
            flat = {}
            for k, v in d.items():
                if isinstance(v, dict):
                    for subk, subv in v.items():
                        flat[f"{k}_{subk}"] = subv
                elif isinstance(v, list):
                    # convert lists to JSON string
                    flat[k] = json.dumps(v, ensure_ascii=False)
                else:
                    flat[k] = v
            return flat

        df_copy = df.copy()
        for col in df_copy.select_dtypes(include=["datetime", "datetimetz"]):
            df_copy[col] = df_copy[col].astype(str)

        # Flatten each row
        flat_records = [flatten_dict(row) for row in df_copy.to_dict(orient="records")]
        return flat_records
    
    def get_fixtures(self) -> dict:
        """
        Fetch fixtures from FotMob and save with metadata.
        JSON structure:
        {
          "meta": { "last_updated": "...", "league": "...", "season": 2526 },
          "fixtures": [ ... ]
        }
        """
        df: pd.DataFrame = self.fotmob.read_schedule()
        if df is None or df.empty:
            return {"meta": {}, "fixtures": []}

        df = df.fillna(0)

        # Flatten any nested dicts or lists to prevent pd.DataFrame issues
        def flatten_dict(d):
            flat = {}
            for k, v in d.items():
                if isinstance(v, dict):
                    for subk, subv in v.items():
                        flat[f"{k}_{subk}"] = subv
                elif isinstance(v, list):
                    # convert lists to JSON string
                    flat[k] = json.dumps(v, ensure_ascii=False)
                else:
                    flat[k] = v
            return flat

        df_copy = df.copy()
        for col in df_copy.select_dtypes(include=["datetime", "datetimetz"]):
            df_copy[col] = df_copy[col].astype(str)

        # Flatten each row
        flat_records = [flatten_dict(row) for row in df_copy.to_dict(orient="records")]

        file_path = Path("data/fotmob/fixtures") / f"{self.league}_{self.seasons[0]}.json"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare output with meta
        output = {
            "meta": {
                "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "league": self.league,
                "season": self.seasons[0],
            },
            "fixtures": flat_records,
        }

        # Save to file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"✅ FotMob fixtures updated: {file_path}")
        return output
