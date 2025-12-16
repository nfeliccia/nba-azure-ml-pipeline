from __future__ import annotations

import json
from pathlib import Path
import pandas as pd


def load_teamgamelog_json(path: str | Path) -> pd.DataFrame:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))

    rs = payload["resultSets"][0]
    headers = rs["headers"]
    rows = rs["rowSet"]

    df = pd.DataFrame(rows, columns=headers)

    # Parse date like "APR 14, 2024"
    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"], format="%b %d, %Y", errors="coerce").dt.date

    # Derive home/away from MATCHUP (e.g., "GSW vs. UTA" or "GSW @ POR")
    df["IS_HOME"] = df["MATCHUP"].str.contains(" vs. ", regex=False)

    return df


if __name__ == "__main__":
    # point this at your most recent raw file
    raw_path = Path("data/raw/nba_api").glob("teamgamelog_team*_*.json")
    latest = max(raw_path, key=lambda p: p.stat().st_mtime)
    df = load_teamgamelog_json(latest)
    print(latest)
    print(df.head())
    print(df.dtypes)
