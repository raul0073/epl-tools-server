from fastapi import APIRouter
from fastapi.responses import JSONResponse
import soccerdata as sd
import pandas as pd

from routes.fbref.utils import detect_columns, flatten_columns

router = APIRouter(tags=["Fbref Players"])

# -----------------------------
# Route: get all players with 3-4 standard stats
# -----------------------------
@router.get("/epl/players")
async def get_epl_players():
    fbref = sd.FBref(leagues="ENG-Premier League", seasons="2526")
    df = fbref.read_player_season_stats("standard").reset_index()
    df = flatten_columns(df)
    col_map = detect_columns(df)
    print(df.columns)
    # Ensure required columns
    required = ["player", "team", "pos"]
    missing = [k for k in required if k not in col_map]
    if missing:
        return JSONResponse(
            content={"error": f"Missing columns: {missing}", "all_columns": df.columns.tolist()},
            status_code=500
        )

  # Select relevant columns
    cols = ["player", "team", "pos", "Playing Time_Starts", "Performance_Gls",
            "Performance_Ast", "Expected_xG", "Expected_xAG"]
    players_df = df[cols].copy()

    # Build player list
    player_list = []
    for _, row in players_df.iterrows():
        player_list.append({
            "label": str(row["player"]),
            "team": str(row["team"]),
            "position": str(row["pos"]),
            "value": str(row["player"]).lower().replace(" ", "_"),
            "starts": row["Playing Time_Starts"],
            "goals": row["Performance_Gls"],
            "assists": row["Performance_Ast"],
            "xG": row["Expected_xG"],
            "xGA": row["Expected_xAG"]
        })

    return JSONResponse(content=player_list)
