from fastapi import APIRouter
from fastapi.responses import JSONResponse
import soccerdata as sd
import pandas as pd

from routes.fbref.utils import detect_columns, flatten_columns

router = APIRouter(tags=["Fbref Teams"])


# -----------------------------
# Route: get all teams
# -----------------------------
@router.get("/epl/teams")
async def get_epl_teams():
    fbref = sd.FBref(leagues="ENG-Premier League", seasons="2526")
    df = fbref.read_player_season_stats("standard").reset_index()
    df = flatten_columns(df)

    # Detect team column
    col_map = detect_columns(df)
    if "team" not in col_map:
        return JSONResponse(
            content={"error": "Could not detect team column", "columns": df.columns.tolist()},
            status_code=500
        )

    teams = sorted(df[col_map["team"]].dropna().unique())
    team_list = [{"label": t, "value": t.lower().replace(" ", "_")} for t in teams]

    return JSONResponse(content=team_list)
