import requests
import json
from pathlib import Path
from typing import Dict, List, Any


class FantasyService:
    BASE_URL = "https://fantasy.premierleague.com/api"

    def __init__(self, team_id: int, cache_dir: str = "data/fpl"):
        self.team_id = team_id
        self.session = requests.Session()
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.wishlist_file = self.cache_dir / f"wishlist_{self.team_id}.json"

    # ------------------------
    # Internal helper
    # ------------------------
    def _safe_get_json(self, url: str) -> Dict[str, Any]:
        """Perform GET request and safely parse JSON."""
        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[ERROR] Request failed for {url}: {e}")
            return {}

        try:
            return resp.json()
        except ValueError:
            print(f"[ERROR] Invalid JSON response from {url}:")
            print(resp.text[:200])
            return {}

    # ------------------------
    # Authentication
    # ------------------------
    def login(self, email: str, password: str):
        """Login to FPL (needed for private /my-team endpoint)."""
        login_url = "https://users.premierleague.com/accounts/login/"
        payload = {
            "login": email,
            "password": password,
            "app": "plfpl-web",
            "redirect_uri": "https://fantasy.premierleague.com/"
        }
        try:
            resp = self.session.post(login_url, data=payload, timeout=10)
            if resp.status_code != 200 or "Invalid login" in resp.text:
                raise Exception("FPL login failed")
        except requests.RequestException as e:
            raise Exception(f"Login request failed: {e}")
        return True

    # ------------------------
    # Public Data
    # ------------------------
    def get_bootstrap(self) -> Dict[str, Any]:
        """Fetch global FPL data (players, teams, events)."""
        url = f"{self.BASE_URL}/bootstrap-static/"
        return self._safe_get_json(url)

    def get_team_info(self) -> Dict[str, Any]:
        """Basic team info (public)."""
        url = f"{self.BASE_URL}/entry/{self.team_id}/"
        return self._safe_get_json(url)

    def get_team_picks(self, gw: int) -> Dict[str, Any]:
        """Squad picks for a specific gameweek (public), enriched with player details."""
        picks_url = f"{self.BASE_URL}/entry/{self.team_id}/event/{gw}/picks/"
        picks_data = self._safe_get_json(picks_url)

        bootstrap = self.get_bootstrap()
        players = {p["id"]: p for p in bootstrap.get("elements", [])}
        teams = {t["id"]: t for t in bootstrap.get("teams", [])}
        element_types = {et["id"]: et for et in bootstrap.get("element_types", [])}

        enriched_picks = []
        for pick in picks_data.get("picks", []):
            player = players.get(pick.get("element"))
            if player:
                pick["player"] = {
                    "id": player["id"],
                    "web_name": player["web_name"],
                    "first_name": player["first_name"],
                    "second_name": player["second_name"],
                    "team": teams.get(player["team"], {}).get("name", "Unknown"),
                    "position": element_types.get(player["element_type"], {}).get("singular_name_short", "Unknown"),
                    "now_cost": player["now_cost"] / 10,
                    "selected_by_percent": player.get("selected_by_percent", 0),
                    "total_points": player.get("total_points", 0),
                    "form": player.get("form", 0),
                    "event_points": player.get("event_points", 0),
                    "minutes": player.get("minutes", 0),
                }
            enriched_picks.append(pick)

        picks_data["picks"] = enriched_picks
        return picks_data

    # ------------------------
    # Private Data (requires login)
    # ------------------------
    def get_my_team(self) -> Dict[str, Any]:
        """Full current squad (requires auth)."""
        url = f"{self.BASE_URL}/my-team/{self.team_id}/"
        data = self._safe_get_json(url)
        if not data:
            print(f"[WARN] No data returned for my-team of team {self.team_id}")
        return data

    # ------------------------
    # Wishlist Persistence
    # ------------------------
    def _load_wishlist(self) -> List[int]:
        if not self.wishlist_file.exists():
            return []
        try:
            return json.loads(self.wishlist_file.read_text())
        except json.JSONDecodeError:
            print("[WARN] Wishlist file corrupted, resetting")
            return []

    def _save_wishlist(self, wishlist: List[int]):
        self.wishlist_file.write_text(json.dumps(wishlist))

    def add_to_wishlist(self, player_id: int):
        wishlist = self._load_wishlist()
        if player_id not in wishlist:
            wishlist.append(player_id)
        self._save_wishlist(wishlist)
        return wishlist

    def remove_from_wishlist(self, player_id: int):
        wishlist = self._load_wishlist()
        wishlist = [pid for pid in wishlist if pid != player_id]
        self._save_wishlist(wishlist)
        return wishlist

    def get_wishlist(self) -> List[int]:
        return self._load_wishlist()

    # ------------------------
    # Player Utilities
    # ------------------------
    def get_players_by_position(self, position_code: int) -> List[Dict[str, Any]]:
        """
        Filter players by position.
        Position codes:
          1 = GK, 2 = DEF, 3 = MID, 4 = FWD
        """
        bootstrap = self.get_bootstrap()
        players = bootstrap.get("elements", [])
        return [p for p in players if p.get("element_type") == position_code]
