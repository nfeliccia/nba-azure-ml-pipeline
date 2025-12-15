from __future__ import annotations

import struct
from pathlib import Path

import pyodbc
from azure.identity import DefaultAzureCredential

SERVER = "nba-sql-189800.database.windows.net"
DATABASE = "nba"
SQL_COPT_SS_ACCESS_TOKEN = 1256


def connect() -> pyodbc.Connection:
    conn_str = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server=tcp:{SERVER},1433;"
        f"Database={DATABASE};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )

    cred = DefaultAzureCredential(exclude_interactive_browser_credential=False)

    token = cred.get_token("https://database.windows.net/.default").token
    token_bytes = token.encode("UTF-16-LE")
    token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)

    return pyodbc.connect(conn_str, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct})


def exec_sql_file(path: str) -> None:
    sql = Path(path).read_text(encoding="utf-8")

    with connect() as conn:
        conn.autocommit = True
        cur = conn.cursor()

        batches = [s.strip() for s in sql.split("GO") if s.strip()]
        for stmt in batches:
            cur.execute(stmt)

    print(f"Applied: {path}")


if __name__ == "__main__":
    exec_sql_file("infra/sql/000_bootstrap_vm_identity.sql")
