from __future__ import annotations

import argparse
import struct
from pathlib import Path

import pyodbc
from azure.identity import AzureCliCredential, ManagedIdentityCredential

SERVER = "nba-sql-189800.database.windows.net"
DATABASE = "nba"
SQL_COPT_SS_ACCESS_TOKEN = 1256


def get_credential(which: str):
    if which == "cli":
        return AzureCliCredential()
    if which == "mi":
        return ManagedIdentityCredential()
    raise ValueError("credential must be 'cli' or 'mi'")


def connect(credential_kind: str) -> pyodbc.Connection:
    conn_str = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server=tcp:{SERVER},1433;"
        f"Database={DATABASE};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )

    cred = get_credential(credential_kind)
    token = cred.get_token("https://database.windows.net/.default").token
    token_bytes = token.encode("UTF-16-LE")
    token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)

    return pyodbc.connect(conn_str, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct})


def exec_sql_file(path: str, credential_kind: str) -> None:
    sql = Path(path).read_text(encoding="utf-8")

    with connect(credential_kind) as conn:
        conn.autocommit = True
        cur = conn.cursor()
        batches = [s.strip() for s in sql.split("GO") if s.strip()]
        for stmt in batches:
            cur.execute(stmt)

    print(f"Applied: {path} (cred={credential_kind})")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sql", default="infra/sql/000_bootstrap_vm_identity.sql")
    p.add_argument("--cred", choices=["cli", "mi"], default="cli")
    args = p.parse_args()
    exec_sql_file(args.sql, args.cred)


if __name__ == "__main__":
    main()
