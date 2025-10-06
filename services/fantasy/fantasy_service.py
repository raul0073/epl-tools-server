import requests
import json
from pathlib import Path
from typing import Dict, List, Optional, Any


class FantasyService:
    BASE_URL = "https://fantasy.premierleague.com/api"

    def __init__(self, team_id: int, cache_dir: str = "data/fpl"):
        self.team_id = team_id
        self.session = requests.Session()
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.wishlist_file = self.cache_dir / f"wishlist_{self.team_id}.json"

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
        resp = self.session.post(login_url, data=payload)
        if resp.status_code != 200 or "Invalid login" in resp.text:
            raise Exception("FPL login failed")
        return True

    # ------------------------
    # Public Data
    # ------------------------
    def get_bootstrap(self) -> Dict[str, Any]:
        """Fetch global FPL data (players, teams, events)."""
        url = f"{self.BASE_URL}/bootstrap-static/"
        return self.session.get(url).json()

    def get_team_info(self) -> Dict[str, Any]:
        """Basic team info (public)."""
        url = f"{self.BASE_URL}/entry/{self.team_id}/"
        return self.session.get(url).json()

    def get_team_picks(self, gw: int) -> Dict[str, Any]:
        """Squad picks for a specific gameweek (public), enriched with player details."""
        picks_url = f"{self.BASE_URL}/entry/{self.team_id}/event/{gw}/picks/"
        picks_data = self.session.get(picks_url).json()

        # Get player metadata from bootstrap
        bootstrap = self.get_bootstrap()
        players = {p["id"]: p for p in bootstrap.get("elements", [])}
        teams = {t["id"]: t for t in bootstrap.get("teams", [])}
        element_types = {et["id"]: et for et in bootstrap.get("element_types", [])}

        enriched_picks = []
        for pick in picks_data.get("picks", []):
            player = players.get(pick["element"])
            if player:
                pick["player"] = {
                    "id": player["id"],
                    "web_name": player["web_name"],   # short display name
                    "first_name": player["first_name"],
                    "second_name": player["second_name"],
                    "team": teams[player["team"]]["name"],
                    "position": element_types[player["element_type"]]["singular_name_short"],
                    "now_cost": player["now_cost"] / 10,  # cost in millions
                    "selected_by_percent": player["selected_by_percent"],
                    "total_points": player["total_points"],
                    "form": player["form"],
                    "event_points": player["event_points"],
                    "minutes": player["minutes"],
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
        resp = self.session.get(url)
        if resp.status_code != 200:
            raise Exception(f"Failed to fetch my-team: {resp.text}")
        return resp.json()

    # ------------------------
    # Wishlist Persistence
    # ------------------------
    def _load_wishlist(self) -> List[int]:
        if not self.wishlist_file.exists():
            return []
        return json.loads(self.wishlist_file.read_text())

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
        return [p for p in players if p["element_type"] == position_code]

