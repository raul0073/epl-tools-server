# -----------------------------
# Helper function to flatten and detect columns
# -----------------------------
import pandas as pd


def flatten_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [
            "_".join([str(part) for part in col if part is not None]).strip("_")
            for col in df.columns.values
        ]
    else:
        df.columns = [str(c) for c in df.columns]
    return df

def detect_columns(df):
    col_map = {}
    for col in df.columns:
        lcol = col.lower()
        if "player" in lcol:
            col_map["player"] = col
        elif "squad" in lcol or "team" in lcol:
            col_map["team"] = col
        elif "pos" in lcol:
            col_map["pos"] = col
        elif "mp" in lcol and "per" not in lcol:
            col_map["MP"] = col
        elif lcol == "g":
            col_map["G"] = col
        elif lcol in ["a", "ast"]:
            col_map["A"] = col
        elif "xg" in lcol and "+" not in lcol:
            col_map["xG"] = col
    return col_map
