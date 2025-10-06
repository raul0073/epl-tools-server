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
        self.fixture_service = FixtureDifficultyService(league=league, season=season)

        # Safe fetch bootstrap data
        self.bootstrap = self._safe_get_json(f"{self.fantasy.BASE_URL}/bootstrap-static/")
        self.players = {p["id"]: p for p in self.bootstrap.get("elements", [])} if self.bootstrap else {}
        self.teams = {t["id"]: t for t in self.bootstrap.get("teams", [])} if self.bootstrap else {}
        self.element_types = {et["id"]: et for et in self.bootstrap.get("element_types", [])} if self.bootstrap else {}

        # Safe fetch fixtures
        self.fixtures = self._safe_get_json(f"{self.fantasy.BASE_URL}/fixtures/") or []

    # ------------------------
    # Internal safe JSON fetch
    # ------------------------
    def _safe_get_json(self, url: str) -> dict:
        try:
            resp = self.fantasy.session.get(url, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"[ERROR] Request failed for {url}: {e}")
            return {}
        try:
            return resp.json()
        except ValueError:
            print(f"[ERROR] Invalid JSON from {url}: {resp.text[:200]}")
            return {}

    # ------------------------
    # Player filtering & enrichment
    # ------------------------
    def get_players_by_position(self, position_code: int) -> List[Dict[str, Any]]:
        if not self.players:
            return []

        filtered = [p for p in self.players.values() if p.get("element_type") == position_code]
        enriched = []

        filtered.sort(key=lambda p: p.get("total_points", 0), reverse=True)

        for p in filtered[:self.TOP_N]:
            team_id = p.get("team")
            next_fixture = self.get_next_fixture(team_id)
            position_short = self.element_types.get(p.get("element_type"), {}).get("singular_name_short", "UNK")

            expected_points_breakdown = self.compute_expected_points_breakdown(p, next_fixture, position_short)
            expected_points_total = sum(item["value"] for item in expected_points_breakdown)

            enriched.append({
                "id": p.get("id"),
                "web_name": p.get("web_name"),
                "first_name": p.get("first_name"),
                "second_name": p.get("second_name"),
                "team": self.teams.get(team_id, {}).get("name", "Unknown"),
                "team_id": team_id,
                "position": position_short,
                "now_cost": p.get("now_cost", 0) / 10,
                "selected_by_percent": p.get("selected_by_percent", 0),
                "total_points": p.get("total_points", 0),
                "form": float(p.get("form") or 0),
                "event_points": p.get("event_points", 0),
                "minutes": p.get("minutes", 0),
                "next_fixture": next_fixture,
                "expected_points": expected_points_breakdown,
                "expected_points_total": round(expected_points_total, 2)
            })

        enriched.sort(key=lambda x: x["total_points"], reverse=True)
        return enriched

    # ------------------------
    # Next fixture
    # ------------------------
    def get_next_fixture(self, team_id: int) -> Optional[Dict[str, Any]]:
        if not self.fixtures:
            return None

        upcoming = [f for f in self.fixtures if not f.get("finished") and (f.get("team_h") == team_id or f.get("team_a") == team_id)]
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
    # Expected points computation
    # ------------------------
    def compute_expected_points_breakdown(
        self, player: Dict[str, Any], next_fixture: Optional[Dict[str, Any]], position_short: str
    ) -> List[Dict[str, Any]]:
        breakdown = []

        form = float(player.get("form") or 0)
        breakdown.append({
            "source": "form",
            "value": round(form, 2),
            "explanation": f"Current player form is {round(form, 2)}."
        })

        if next_fixture:
            home_modifier = 1.1 if next_fixture.get("home") else 0.9
            home_text = "home advantage" if next_fixture.get("home") else "away disadvantage"
            breakdown.append({
                "source": "home_away",
                "value": round(form * (home_modifier - 1), 2),
                "explanation": f"This fixture has {home_text}."
            })

            fixture_modifier = self.fixture_service.get_fixture_modifier(next_fixture.get("opponent_name", "Unknown"), position_short)
            difficulty_text = (
                "tougher opponent reduces expected points" if fixture_modifier < 0
                else "easier opponent increases expected points" if fixture_modifier > 0
                else "neutral opponent"
            )
            breakdown.append({
                "source": "fixture_difficulty",
                "value": fixture_modifier,
                "explanation": f"Fixture difficulty vs {next_fixture.get('opponent_name', 'Unknown')}: {difficulty_text}."
            })

        return breakdown
