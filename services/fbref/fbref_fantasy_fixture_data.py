from typing import Optional, Dict
import pandas as pd
import soccerdata as sd
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FixtureDifficultyService:
    """
    Provides numeric fixture difficulty modifiers for FPL players
    based on FBref team stats.
    """

    # Mapping FPL short names → FBref official names
    NAME_MAP = {
        "Man City": "Manchester City",
        "Man Utd": "Manchester United",
        "Spurs": "Tottenham",
        "Newcastle": "Newcastle United",
        "Brighton": "Brighton",
        "West Ham": "West Ham",
        "Wolves": "Wolves",
        "Nott'm Forest": "Nottingham Forest",
        "Leeds": "Leeds United",
        "Sheffield Utd": "Sheffield United",
        "Bournemouth": "Bournemouth",
        "Brentford": "Brentford",
        "Burnley": "Burnley",
        "Chelsea": "Chelsea",
        "Crystal Palace": "Crystal Palace",
        "Everton": "Everton",
        "Fulham": "Fulham",
        "Liverpool": "Liverpool",
        "Arsenal": "Arsenal",
        "Leicester": "Leicester City",
        "Southampton": "Southampton",
        "Sunderland": "Sunderland"
    }

    def __init__(self, league: str, season: Optional[str] = None):
        self.league = league
        self.season = [season] if season else ["2526"]
        self.fbref = sd.FBref(leagues=[league], seasons=self.season)
        self._team_lookup: Dict[str, Dict] = {}
        self._load_team_stats()

    def _load_team_stats(self):
        """
        Load all opponent stats once and cache them.
        Flatten multi-level columns and normalize names.
        """
        logger.info("Loading FBref team stats...")
        stats = self.fbref.read_team_season_stats(stat_type="standard", opponent_stats=True)
        stats = stats.reset_index()
        stats.columns = ["_".join([str(c) for c in col if c]) for col in stats.columns.values]

        # Normalize FBref team names
        stats["team_name"] = stats["team"].str.replace(" Utd", " United", regex=False)
        stats["team_name"] = stats["team_name"].str.replace("Nott'ham Forest", "Nottingham Forest", regex=False)
        stats["team_name"] = stats["team_name"].str.replace("Wolves", "Wolverhampton", regex=False)

        # Strip any "vs " prefix if exists
        stats["team_name"] = stats["team_name"].apply(lambda x: re.sub(r"^vs\s+", "", x))

        # Build team lookup
        self._team_lookup = {row["team_name"]: row.to_dict() for _, row in stats.iterrows()}
        logger.info(f"Loaded {len(self._team_lookup)} teams into team lookup: {list(self._team_lookup.keys())}")

    def get_fixture_modifier(self, fixture_name: str, player_position: str) -> float:
        """
        Returns a numeric fixture difficulty modifier.
        Higher modifier → tougher opponent → negative impact on expected points.

        fixture_name: e.g. "vs Arsenal" or "Arsenal"
        player_position: "GKP" or outfield
        """
        # Remove "vs " prefix if present
        opponent = fixture_name.replace("vs ", "").strip()

        # Map FPL name → FBref official name
        lookup_name = self.NAME_MAP.get(opponent, opponent)
        row = self._team_lookup.get(lookup_name)

        if row is None:
            logger.warning(f"FBref stats not found for opponent '{opponent}' (lookup '{lookup_name}'). Returning neutral 0.0.")
            return 0.0  # neutral

        # Calculate modifier
        try:
            if player_position == "GKP":
                xg_conceded = float(row.get("Per 90 Minutes_xG", 0.0))
                modifier = -xg_conceded
            else:
                xg_conceded = float(row.get("Per 90 Minutes_xG", 0.0))
                goals_conceded = float(row.get("Performance_Gls", 0.0))
                modifier = -(xg_conceded + goals_conceded) / 2
            logger.debug(f"Fixture modifier for '{opponent}' ({player_position}): {modifier}")
        except Exception as e:
            logger.error(f"Error computing modifier for {lookup_name}: {e}")
            modifier = 0.0

        return round(modifier, 2)
