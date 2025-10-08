# services/fantasy/fantasy_service.py
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

import requests
from requests.utils import dict_from_cookiejar, cookiejar_from_dict

# ---------------------------------------------------------------------
# FantasyService
#
# - Uses a requests.Session with sensible headers
# - Supports importing a browser cookie string (paste from DevTools)
# - Persists cookies to disk (encrypted storage recommended in prod)
# - Exposes fallback-safe _safe_get_json for all endpoints
# ---------------------------------------------------------------------


class FantasyService:
    BASE_URL = "https://fantasy.premierleague.com/api"
    SESSION_FILE_DEFAULT = Path("data/fpl/fpl_session.json")
    DEFAULT_HEADERS = {
     "User-Agent": (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
),
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://fantasy.premierleague.com",
        "Referer": "https://fantasy.premierleague.com",
    }

    def __init__(self, team_id: int, cache_dir: str = "data/fpl", session_file: Optional[Path] = None):
        self.team_id = team_id
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Session file where cookies are persisted
        self.session_file = Path(session_file) if session_file else self.SESSION_FILE_DEFAULT
        self.wishlist_file = self.cache_dir / f"wishlist_{self.team_id}.json"

        # requests session
        self.session = requests.Session()
        # Apply default headers (still safe for calling FPL endpoints)
        self.session.headers.update(self.DEFAULT_HEADERS)

        # Try to load persisted cookies automatically
        loaded = self.load_session()
        if loaded:
            print(f"[INFO] FantasyService: loaded session cookies from {self.session_file}")
        else:
            print("[INFO] FantasyService: no persisted session loaded; import cookies or login to access private endpoints")

    # ------------------------
    # Cookie persistence helpers
    # ------------------------
    def save_session(self) -> None:
        """Persist cookies to disk with timestamp. Treat file as secret."""
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        cookies = dict_from_cookiejar(self.session.cookies)
        payload = {"cookies": cookies, "saved_at": int(time.time())}
        try:
            self.session_file.write_text(json.dumps(payload))
            print(f"[INFO] Session saved to {self.session_file}")
        except Exception as e:
            print(f"[ERROR] Saving session failed: {e}")

    def load_session(self) -> bool:
        """Load cookies from disk into session. Returns True if loaded successfully."""
        if not self.session_file.exists():
            return False
        try:
            raw = self.session_file.read_text()
            data = json.loads(raw)
            cookies = data.get("cookies", {})
            self.session.cookies = cookiejar_from_dict(cookies)
            return True
        except Exception as e:
            print(f"[WARN] Failed to load session file: {e}")
            return False

    def import_cookies_from_string(self, cookie_header: str, persist: bool = True) -> None:
        """
        Import cookies from a 'Cookie' header string you paste from browser devtools.
        Example cookie_header: "csrftoken=abc; sessionid=xyz; REMEMBERME=..."
        """
        pairs = [p.strip() for p in cookie_header.split(";") if p.strip()]
        cookie_dict: Dict[str, str] = {}
        for p in pairs:
            if "=" in p:
                k, v = p.split("=", 1)
                cookie_dict[k.strip()] = v.strip()
        if not cookie_dict:
            raise ValueError("No cookies parsed from provided cookie header string.")
        self.session.cookies = cookiejar_from_dict(cookie_dict)
        if persist:
            self.save_session()
        print("[INFO] Imported cookies into session (from cookie header)")

    def set_cookie_dict(self, cookie_dict: Dict[str, str], persist: bool = True) -> None:
        """Directly set cookies from a dict and optionally persist."""
        self.session.cookies = cookiejar_from_dict(cookie_dict)
        if persist:
            self.save_session()
        print("[INFO] Cookies set from dict and saved.")

    # ------------------------
    # Optional programmatic login (works only for non-SSO accounts)
    # ------------------------
    def login(self, email: str, password: str, persist: bool = True) -> bool:
        """
        Attempt programmatic login against users.premierleague.com.
        NOTE: This will not work if your account uses Google/Facebook SSO.
        Prefer cookie import when using Google login.
        """
        login_url = "https://users.premierleague.com/accounts/login/"
        try:
            # Prime session (get any initial cookies)
            r = self.session.get(login_url, timeout=10)
            r.raise_for_status()
        except requests.RequestException as e:
            print(f"[ERROR] Cannot reach login page: {e}")
            return False

        payload = {
            "login": email,
            "password": password,
            "app": "plfpl-web",
            "redirect_uri": "https://fantasy.premierleague.com/"
        }
        try:
            res = self.session.post(login_url, data=payload, timeout=10, allow_redirects=True)
            # The site returns 200 on both success/failure, so check content for failure keywords
            text = (res.text or "").lower()
            if res.status_code != 200 or "invalid login" in text or "please try again" in text:
                print("[ERROR] Login failed. If you use Google SSO this method won't work.")
                return False
        except requests.RequestException as e:
            print(f"[ERROR] Login POST failed: {e}")
            return False

        if persist:
            self.save_session()
        print("[INFO] Programmatic login completed and session persisted.")
        return True

    # ------------------------
    # Internal safe JSON fetch
    # ------------------------
    def _safe_get_json(self, url: str, timeout: int = 10) -> Dict[str, Any]:
        """
        Centralized fetch: uses session (with cookies if present), returns {} on failure.
        Prints helpful debug when 403 occurs.
        """
        try:
            resp = self.session.get(url, timeout=timeout)
            resp.raise_for_status()
        except requests.HTTPError as he:
            status = getattr(he.response, "status_code", None)
            snippet = ""
            try:
                snippet = he.response.text[:500]
            except Exception:
                snippet = ""
            print(f"[ERROR] Request failed for {url}: {he} (status={status})")
            if status == 403:
                print("[ERROR] 403 Forbidden — likely missing/invalid cookies or blocked agent.")
            if snippet:
                print(f"[DEBUG] Response snippet: {snippet}")
            return {}
        except requests.RequestException as e:
            print(f"[ERROR] Request failed for {url}: {e}")
            return {}

        try:
            return resp.json()
        except ValueError:
            print(f"[ERROR] Invalid JSON response from {url}: {resp.text[:400]}")
            return {}

    # ------------------------
    # Public API wrappers
    # ------------------------
    def get_bootstrap(self) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/bootstrap-static/"
        return self._safe_get_json(url)

    def get_fixtures(self) -> List[Dict[str, Any]]:
        url = f"{self.BASE_URL}/fixtures/"
        return self._safe_get_json(url) or []

    def get_team_info(self) -> Dict[str, Any]:
        """Entry info (private for many teams)."""
        url = f"{self.BASE_URL}/entry/{self.team_id}/"
        return self._safe_get_json(url)

    def get_team_picks(self, gw: int) -> Dict[str, Any]:
        """Picks for a specific GW (private endpoint)."""
        url = f"{self.BASE_URL}/entry/{self.team_id}/event/{gw}/picks/"
        picks = self._safe_get_json(url)
        # Best-effort: enrich picks using bootstrap if possible
        bootstrap = self.get_bootstrap()
        players = {p["id"]: p for p in bootstrap.get("elements", [])} if bootstrap else {}
        teams = {t["id"]: t for t in bootstrap.get("teams", [])} if bootstrap else {}
        element_types = {et["id"]: et for et in bootstrap.get("element_types", [])} if bootstrap else {}

        enriched_picks = []
        for pick in picks.get("picks", []):
            player = players.get(pick.get("element"))
            if player:
                pick["player"] = {
                    "id": player["id"],
                    "web_name": player.get("web_name"),
                    "first_name": player.get("first_name"),
                    "second_name": player.get("second_name"),
                    "team": teams.get(player.get("team"), {}).get("name", "Unknown"),
                    "position": element_types.get(player.get("element_type"), {}).get("singular_name_short", "Unknown"),
                    "now_cost": player.get("now_cost", 0) / 10,
                    "selected_by_percent": player.get("selected_by_percent", 0),
                    "total_points": player.get("total_points", 0),
                    "form": player.get("form", 0),
                    "event_points": player.get("event_points", 0),
                    "minutes": player.get("minutes", 0),
                }
            enriched_picks.append(pick)
        picks["picks"] = enriched_picks
        return picks

    def get_my_team(self) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/my-team/{self.team_id}/"
        return self._safe_get_json(url)

    # ------------------------
    # Simple helpers
    # ------------------------
    def can_access_entry(self, entry_id: int) -> bool:
        """
        Check whether the current session can access /entry/{entry_id}/
        Useful to verify that imported cookies are valid for your account.
        """
        url = f"{self.BASE_URL}/entry/{entry_id}/"
        try:
            r = self.session.get(url, timeout=10)
            if r.status_code == 200:
                return True
            if r.status_code == 403:
                return False
            # treat other statuses as not accessible
            return False
        except requests.RequestException as e:
            print(f"[ERROR] can_access_entry request failed: {e}")
            return False

    # ------------------------
    # Wishlist persistence (unchanged)
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
    # Player utilities
    # ------------------------
    def get_players_by_position(self, position_code: int) -> List[Dict[str, Any]]:
        """
        Return raw player elements filtered by element_type.
        For richer/enriched objects, call higher-level services that compute expected points, next fixture, etc.
        """
        bootstrap = self.get_bootstrap()
        players = bootstrap.get("elements", []) if bootstrap else []
        return [p for p in players if p.get("element_type") == position_code]
