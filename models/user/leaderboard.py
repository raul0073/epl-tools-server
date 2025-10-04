from pydantic import BaseModel
from typing import List, Optional

# -----------------------------
# Individual user leaderboard stats
# -----------------------------
class UserLeaderboardStats(BaseModel):
    user_id: str
    name: Optional[str] = None
    team_name: Optional[str] = None
    totalPoints: int
    exactPredictions: int
    correctPredictions: int
    position: Optional[int] = None  # rank in the leaderboard
    deltaPosition: Optional[int] = None  # change from previous snapshot (up/down)


# -----------------------------
# Leaderboard snapshot for a round
# -----------------------------
class LeaderboardSnapshot(BaseModel):
    round_number: int
    snapshot: List[UserLeaderboardStats]


# -----------------------------
# Multiple snapshots
# -----------------------------
class AllSnapshots(BaseModel):
    snapshots: List[LeaderboardSnapshot]
