# services/fantasy/fantasy_player_model_service.py
from typing import List, Dict, Any, Optional
from services.fantasy.fantasy_service import FantasyService
from services.fbref.fbref_fantasy_fixture_data import FixtureDifficultyService
class FantasyPlayerModelService:
    """
    Fetch all FPL players by position, enrich with next fixture,
    and compute a detailed expected points breakdown using FBref data.
    """

    TOP_N = 20  # only compute top 20 per position per request

    def __init__(self, league: str, season: str = "2526"):
        self.fantasy = FantasyService(team_id=0)
        self.bootstrap = self.fantasy.get_bootstrap()
        self.players = {p["id"]: p for p in self.bootstrap.get("elements", [])}
        self.teams = {t["id"]: t for t in self.bootstrap.get("teams", [])}
        self.element_types = {et["id"]: et for et in self.bootstrap.get("element_types", [])}
        self.fixtures = self.fantasy.session.get(f"{self.fantasy.BASE_URL}/fixtures/").json()
        self.fixture_service = FixtureDifficultyService(league=league, season=season)

    def get_players_by_position(self, position_code: int) -> List[Dict[str, Any]]:
        filtered = [p for p in self.players.values() if p["element_type"] == position_code]
        enriched = []

        # Sort by total points first (preliminary)
        filtered.sort(key=lambda p: p.get("total_points", 0), reverse=True)

        for p in filtered[: self.TOP_N]:
            team_id = p["team"]
            next_fixture = self.get_next_fixture(team_id)
            position_short = self.element_types[p["element_type"]]["singular_name_short"]

            expected_points_breakdown = self.compute_expected_points_breakdown(p, next_fixture, position_short)
            expected_points_total = sum(item["value"] for item in expected_points_breakdown)

            enriched.append({
                "id": p["id"],
                "web_name": p["web_name"],
                "first_name": p["first_name"],
                "second_name": p["second_name"],
                "team": self.teams[team_id]["name"],
                "team_id": team_id,
                "position": position_short,
                "now_cost": p["now_cost"] / 10,
                "selected_by_percent": p["selected_by_percent"],
                "total_points": p["total_points"],
                "form": float(p.get("form") or 0),
                "event_points": p.get("event_points", 0),
                "minutes": p.get("minutes", 0),
                "next_fixture": next_fixture,
                "expected_points": expected_points_breakdown,
                "expected_points_total": round(expected_points_total, 2)  # <-- attach total here
            })

        # Sort final enriched list by expected_points_total DESC first, fallback to total_points
        enriched.sort(key=lambda x: ( x["total_points"]), reverse=True)

        # Return only top N players
        return enriched


    def get_next_fixture(self, team_id: int) -> Optional[Dict[str, Any]]:
        upcoming = [f for f in self.fixtures if not f.get("finished") and (f["team_h"] == team_id or f["team_a"] == team_id)]
        if not upcoming:
            return None
        next_match = sorted(upcoming, key=lambda x: x["event"])[0]
        opponent_id = next_match["team_a"] if next_match["team_h"] == team_id else next_match["team_h"]
        return {
            "opponent": opponent_id,
            "opponent_name": self.teams[opponent_id]["name"],
            "home": next_match["team_h"] == team_id,
            "kickoff_time": next_match.get("kickoff_time")
        }

    def compute_expected_points_breakdown(self, player: Dict[str, Any], next_fixture: Optional[Dict[str, Any]], position_short: str) -> List[Dict[str, Any]]:
        breakdown = []

        # Base form
        form = float(player.get("form") or 0)
        breakdown.append({
            "source": "form",
            "value": round(form, 2),
            "explanation": f"Current player form is {round(form,2)}. Higher form means the player is in better form and likely to perform well."
        })

        if next_fixture:
            # Home/Away modifier
            home_modifier = 1.1 if next_fixture["home"] else 0.9
            home_text = "home advantage" if next_fixture["home"] else "away disadvantage"
            breakdown.append({
                "source": "home_away",
                "value": round(form * (home_modifier - 1), 2),
                "explanation": f"This fixture has {home_text}, modifying expected points accordingly."
            })

            # Fixture difficulty
            fixture_modifier = self.fixture_service.get_fixture_modifier(next_fixture["opponent_name"], position_short)
            difficulty_text = (
                "tougher opponent reduces expected points" if fixture_modifier < 0 
                else "easier opponent increases expected points" if fixture_modifier > 0
                else "neutral opponent"
            )
            breakdown.append({
                "source": "fixture_difficulty",
                "value": fixture_modifier,
                "explanation": f"Fixture difficulty vs {next_fixture['opponent_name']}: {difficulty_text}."
            })

        return breakdown
