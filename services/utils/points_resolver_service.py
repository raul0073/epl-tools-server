from typing import Dict, List, Optional
from datetime import datetime
from bson import ObjectId
from db.mongo_client import collection, fix_id
from models.user.points import MatchPoints, Points, SeasonPoints
from models.user.register_models import MatchPrediction
from models.fotmob.fixture import FotMobFixture
from services.fotmob.fotmob_json_service import FotMobJSONService
from services.users.update.user_service import UserUpdateService


class PointsResolverService:
    def __init__(self):
        self.fixtures: List[FotMobFixture] = self._load_fixtures()

    def _load_fixtures(self) -> List[FotMobFixture]:
        fotmob_service = FotMobJSONService()
        return fotmob_service._load_fixtures()

    @staticmethod
    def calculate_points(
        actual_home: Optional[int],
        actual_away: Optional[int],
        pred_home: Optional[int],
        pred_away: Optional[int],
    ) -> int:
        if actual_home is None or actual_away is None or pred_home is None or pred_away is None:
            return 0

        # Exact score
        if actual_home == pred_home and actual_away == pred_away:
            return 3

        # Correct outcome
        actual_outcome = (
            "draw" if actual_home == actual_away else "home" if actual_home > actual_away else "away"
        )
        pred_outcome = (
            "draw" if pred_home == pred_away else "home" if pred_home > pred_away else "away"
        )

        if actual_outcome == pred_outcome:
            return 1

        return 0

    async def resolve_and_save_all_users(self):
        """
        Loads all users from MongoDB, calculates points for each match,
        aggregates total, last round, and season points, then saves back.
        """
        users_cursor = collection.find({})
        users = [fix_id(u) async for u in users_cursor]

        # Group fixtures by round
        fixtures_by_round: Dict[int, List[FotMobFixture]] = {}
        for f in self.fixtures:
            fixtures_by_round.setdefault(f.round, []).append(f)

        for user_doc in users:
            user_id = str(user_doc["id"])
            user_predictions: Dict[int, Dict[str, MatchPrediction]] = user_doc.get("predictions", {})

            matches_points: Dict[str, List[MatchPoints]] = {}
            total_points = 0
            last_round_points = 0

            # Process rounds in order
            for round_number in sorted(fixtures_by_round.keys()):
                round_fixtures = fixtures_by_round[round_number]
                round_points_list: List[MatchPoints] = []

                for fixture in round_fixtures:
                    user_pred: Optional[MatchPrediction] = None
                    if user_predictions.get(round_number):
                        key = fixture.game_id
                        user_pred = user_predictions[round_number].get(key)

                    actual_home = int(fixture.home_score) if fixture.home_score is not None else None
                    actual_away = int(fixture.away_score) if fixture.away_score is not None else None

                    pred_home = user_pred.home_score if user_pred else None
                    pred_away = user_pred.away_score if user_pred else None

                    points = self.calculate_points(actual_home, actual_away, pred_home, pred_away)

                    round_points_list.append(MatchPoints(game_id=fixture.game_id, points=points))
                    total_points += points

                matches_points[str(round_number)] = round_points_list
                last_round_points = sum(mp.points for mp in round_points_list)

            # Build season points from user_doc
            season_points = SeasonPoints(
                top_scorer=user_doc.get("points", {}).get("season_points", {}).get("top_scorer", 0),
                assist_king=user_doc.get("points", {}).get("season_points", {}).get("assist_king", 0),
                league_champion=user_doc.get("points", {}).get("season_points", {}).get("league_champion"),
                relegated_teams=user_doc.get("points", {}).get("season_points", {}).get("relegated_teams"),
            )

            # Build final Points object
            user_points = Points(
                total_points=total_points,
                last_round_points=last_round_points,
                matches=matches_points,
                season_points=season_points,
            )

            # Save back
            await UserUpdateService.update_points(user_id, user_points)
