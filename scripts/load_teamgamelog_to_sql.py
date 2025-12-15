from __future__ import annotations

import argparse
import json
import struct
from datetime import datetime
from pathlib import Path

import pandas as pd
import pyodbc
from azure.identity import ManagedIdentityCredential

SERVER = "nba-sql-189800.database.windows.net"
DATABASE = "nba"
SQL_COPT_SS_ACCESS_TOKEN = 1256


def connect_mi() -> pyodbc.Connection:
    conn_str = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server=tcp:{SERVER},1433;"
        f"Database={DATABASE};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )
    cred = ManagedIdentityCredential()
    token = cred.get_token("https://database.windows.net/.default").token
    token_bytes = token.encode("UTF-16-LE")
    token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)
    return pyodbc.connect(conn_str, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct})


def parse_teamgamelog_json(path: Path) -> pd.DataFrame:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rs = payload["resultSets"][0]
    headers = rs["headers"]
    rows = rs["rowSet"]

    df = pd.DataFrame(rows, columns=headers)

    # Parse date like "APR 14, 2024"
    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"], format="%b %d, %Y", errors="coerce").dt.date

    # Derive home/away from MATCHUP
    df["IS_HOME"] = df["MATCHUP"].str.contains(" vs. ", regex=False)

    return df


def to_sql_rows(df: pd.DataFrame, season: str | None) -> list[tuple]:
    # Map to SQL column order
    cols = [
        "Team_ID", "Game_ID", "GAME_DATE", "MATCHUP",
        "WL", "W", "L", "W_PCT", "MIN",
        "FGM", "FGA", "FG_PCT",
        "FG3M", "FG3A", "FG3_PCT",
        "FTM", "FTA", "FT_PCT",
        "OREB", "DREB", "REB",
        "AST", "STL", "BLK", "TOV", "PF", "PTS",
        "IS_HOME",
    ]

    # Ensure presence
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")

    rows = []
    for r in df[cols].itertuples(index=False, name=None):
        rows.append(r + (season,))
    return rows


def load_to_sql(rows: list[tuple]) -> None:
    create_temp = """
    IF OBJECT_ID('tempdb..#stg_fact_team_game_log') IS NOT NULL DROP TABLE #stg_fact_team_game_log;

    CREATE TABLE #stg_fact_team_game_log (
      team_id INT NOT NULL,
      game_id VARCHAR(12) NOT NULL,
      game_date DATE NOT NULL,
      matchup VARCHAR(32) NOT NULL,

      wl CHAR(1) NULL,
      w SMALLINT NOT NULL,
      l SMALLINT NOT NULL,
      w_pct DECIMAL(6,5) NULL,
      minutes SMALLINT NOT NULL,

      fgm SMALLINT NOT NULL,
      fga SMALLINT NOT NULL,
      fg_pct DECIMAL(6,5) NULL,

      fg3m SMALLINT NOT NULL,
      fg3a SMALLINT NOT NULL,
      fg3_pct DECIMAL(6,5) NULL,

      ftm SMALLINT NOT NULL,
      fta SMALLINT NOT NULL,
      ft_pct DECIMAL(6,5) NULL,

      oreb SMALLINT NOT NULL,
      dreb SMALLINT NOT NULL,
      reb SMALLINT NOT NULL,

      ast SMALLINT NOT NULL,
      stl SMALLINT NOT NULL,
      blk SMALLINT NOT NULL,
      tov SMALLINT NOT NULL,
      pf SMALLINT NOT NULL,
      pts SMALLINT NOT NULL,

      is_home BIT NOT NULL,
      season VARCHAR(7) NULL
    );
    """

    insert_sql = """
    INSERT INTO #stg_fact_team_game_log (
      team_id, game_id, game_date, matchup,
      wl, w, l, w_pct, minutes,
      fgm, fga, fg_pct,
      fg3m, fg3a, fg3_pct,
      ftm, fta, ft_pct,
      oreb, dreb, reb,
      ast, stl, blk, tov, pf, pts,
      is_home,
      season
    )
    VALUES (?,?,?,?, ?,?,?,?, ?,?,?,?, ?,?,?,?, ?,?,?,?, ?,?,?, ?,?,?,?, ?,?)
    """

    merge_sql = """
    MERGE dbo.fact_team_game_log AS tgt
    USING #stg_fact_team_game_log AS src
      ON (tgt.team_id = src.team_id AND tgt.game_id = src.game_id)
    WHEN MATCHED THEN UPDATE SET
      tgt.game_date = src.game_date,
      tgt.matchup = src.matchup,
      tgt.wl = src.wl,
      tgt.w = src.w,
      tgt.l = src.l,
      tgt.w_pct = src.w_pct,
      tgt.minutes = src.minutes,
      tgt.fgm = src.fgm,
      tgt.fga = src.fga,
      tgt.fg_pct = src.fg_pct,
      tgt.fg3m = src.fg3m,
      tgt.fg3a = src.fg3a,
      tgt.fg3_pct = src.fg3_pct,
      tgt.ftm = src.ftm,
      tgt.fta = src.fta,
      tgt.ft_pct = src.ft_pct,
      tgt.oreb = src.oreb,
      tgt.dreb = src.dreb,
      tgt.reb = src.reb,
      tgt.ast = src.ast,
      tgt.stl = src.stl,
      tgt.blk = src.blk,
      tgt.tov = src.tov,
      tgt.pf = src.pf,
      tgt.pts = src.pts,
      tgt.is_home = src.is_home,
      tgt.season = src.season,
      tgt.ingested_utc = SYSUTCDATETIME()
    WHEN NOT MATCHED BY TARGET THEN
      INSERT (
        team_id, game_id, game_date, matchup,
        wl, w, l, w_pct, minutes,
        fgm, fga, fg_pct,
        fg3m, fg3a, fg3_pct,
        ftm, fta, ft_pct,
        oreb, dreb, reb,
        ast, stl, blk, tov, pf, pts,
        is_home,
        season
      )
      VALUES (
        src.team_id, src.game_id, src.game_date, src.matchup,
        src.wl, src.w, src.l, src.w_pct, src.minutes,
        src.fgm, src.fga, src.fg_pct,
        src.fg3m, src.fg3a, src.fg3_pct,
        src.ftm, src.fta, src.ft_pct,
        src.oreb, src.dreb, src.reb,
        src.ast, src.stl, src.blk, src.tov, src.pf, src.pts,
        src.is_home,
        src.season
      );
    """

    with connect_mi() as conn:
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(create_temp)

        cur.fast_executemany = True
        cur.executemany(insert_sql, rows)

        cur.execute(merge_sql)

    print(f"Loaded rows (staged): {len(rows)}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--json", required=True, help="Path to TeamGameLog raw JSON (nba_api get_dict format)")
    p.add_argument("--season", default=None, help="Optional season label like 2023-24")
    args = p.parse_args()

    path = Path(args.json)
    df = parse_teamgamelog_json(path)
    rows = to_sql_rows(df, season=args.season)
    load_to_sql(rows)


if __name__ == "__main__":
    main()
