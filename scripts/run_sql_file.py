from __future__ import annotations
from pathlib import Path
import pyodbc

SERVER = "nba-sql-189800.database.windows.net"
DATABASE = "nba"

def run_sql_file(path: str) -> None:
    sql = Path(path).read_text(encoding="utf-8")

    # NOTE: For AAD-only auth, we’ll switch this connection to Managed Identity / AAD token next.
    # For now, this is a placeholder to prove “run a .sql file end-to-end” once auth is wired.
    conn_str = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server=tcp:{SERVER},1433;"
        f"Database={DATABASE};"
        "Encrypt=yes;TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )

    with pyodbc.connect(conn_str) as conn:
        conn.autocommit = True
        cur = conn.cursor()
        for stmt in [s.strip() for s in sql.split("GO") if s.strip()]:
            cur.execute(stmt)
    print(f"Applied: {path}")

if __name__ == "__main__":
    run_sql_file("infra/sql/001_create_fact_team_game_log.sql")
