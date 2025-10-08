# services/fantasy/fantasy_player_model_service.py
from typing import List, Dict, Any, Optional
from services.fantasy.fantasy_service import FantasyService
from services.fbref.fbref_fantasy_fixture_data import FixtureDifficultyService


class FantasyPlayerModelService:
    """
    Fetch FPL players by position, enrich with next fixture,
    and compute expected points breakdown using FBref data.
    """

    TOP_N = 20  # limit top N per position

    def __init__(self, league: str, season: str = "2526"):
        self.fantasy = FantasyService(team_id=0)
        self.fixture_service = FixtureDifficultyService(league=league, season=season)

        # Bootstrap data
        self.bootstrap = self.fantasy.get_bootstrap()
        self.players = {p["id"]: p for p in self.bootstrap.get("elements", [])}
        self.teams = {t["id"]: t for t in self.bootstrap.get("teams", [])}
        self.element_types = {et["id"]: et for et in self.bootstrap.get("element_types", [])}

        # Fixtures
        self.fixtures = self.fantasy.get_fixtures()

    # ------------------------
    # Player enrichment
    # ------------------------
    def get_players_by_position(self, position_code: int) -> List[Dict[str, Any]]:
        """Return top N players by position with enriched expected points"""
        filtered = [p for p in self.players.values() if p.get("element_type") == position_code]
        filtered.sort(key=lambda p: p.get("total_points", 0), reverse=True)

        enriched = []
        for p in filtered[:self.TOP_N]:
            team_id = p.get("team")
            next_fixture = self.get_next_fixture(team_id)
            pos_short = self.element_types.get(p.get("element_type"), {}).get("singular_name_short", "UNK")

            breakdown = self.compute_expected_points_breakdown(p, next_fixture, pos_short)
            total_expected = round(sum(item.get("value", 0) for item in breakdown), 2)

            enriched.append({
                "id": p.get("id"),
                "web_name": p.get("web_name"),
                "first_name": p.get("first_name"),
                "second_name": p.get("second_name"),
                "team": self.teams.get(team_id, {}).get("name", "Unknown"),
                "team_id": team_id,
                "position": pos_short,
                "now_cost": p.get("now_cost", 0) / 10,
                "selected_by_percent": p.get("selected_by_percent", 0),
                "total_points": p.get("total_points", 0),
                "form": float(p.get("form") or 0),
                "event_points": p.get("event_points", 0),
                "minutes": p.get("minutes", 0),
                "next_fixture": next_fixture,
                "expected_points": breakdown,
                "expected_points_total": total_expected
            })

        enriched.sort(key=lambda x: x["total_points"], reverse=True)
        return enriched

    # ------------------------
    # Next fixture
    # ------------------------
    def get_next_fixture(self, team_id: int) -> Optional[Dict[str, Any]]:
        """Return the next upcoming fixture for a team"""
        upcoming = [
            f for f in self.fixtures
            if not f.get("finished") and team_id in (f.get("team_h"), f.get("team_a"))
        ]
        if not upcoming:
            return None

        next_match = sorted(upcoming, key=lambda x: x.get("event", 9999))[0]
        opponent_id = next_match.get("team_a") if next_match.get("team_h") == team_id else next_match.get("team_h")
        return {
            "opponent": opponent_id,
            "opponent_name": self.teams.get(opponent_id, {}).get("name", "Unknown"),
            "home": next_match.get("team_h") == team_id,
            "kickoff_time": next_match.get("kickoff_time")
        }

    # ------------------------
    # Expected points
    # ------------------------
    def compute_expected_points_breakdown(
        self, player: Dict[str, Any], next_fixture: Optional[Dict[str, Any]], position_short: str
    ) -> List[Dict[str, Any]]:
        """Compute expected points from form, home/away, and fixture difficulty"""
        breakdown: List[Dict[str, Any]] = []

        form = float(player.get("form") or 0)
        breakdown.append({"source": "form", "value": round(form, 2),
                          "explanation": f"Current player form is {round(form, 2)}."})

        if next_fixture:
            # Home/away modifier
            home = next_fixture.get("home", False)
            home_mod = 1.1 if home else 0.9
            breakdown.append({"source": "home_away", "value": round(form * (home_mod - 1), 2),
                              "explanation": f"{'Home advantage' if home else 'Away disadvantage'} applied."})

            # Fixture difficulty modifier
            opponent_name = next_fixture.get("opponent_name", "Unknown")
            fixture_mod = self.fixture_service.get_fixture_modifier(opponent_name, position_short)
            difficulty_text = (
                "easier opponent" if fixture_mod > 0 else
                "tougher opponent" if fixture_mod < 0 else
                "neutral opponent"
            )
            breakdown.append({"source": "fixture_difficulty", "value": fixture_mod,
                              "explanation": f"Fixture difficulty vs {opponent_name}: {difficulty_text}."})

        return breakdown
