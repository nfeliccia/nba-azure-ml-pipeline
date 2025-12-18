from __future__ import annotations

"""Smoke tests for nba-azure-ml-pipeline.

DB mode requirements (for Azure SQL connectivity):
- Environment: AZURE_SQL_SERVER, AZURE_SQL_DATABASE
- Auth: managed identity on vm-nba-runner (DefaultAzureCredential) or service principal
  via AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET when running locally.

Example:
    uv run python -m nba_pipeline.smoke_test --db
"""

import argparse
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv


def _db_smoke_test() -> None:
    load_dotenv()

    from sqlalchemy import text

    from nba_pipeline.db import make_engine, warmup

    engine = make_engine()
    print("connecting to Azure SQL ...")
    warmup(engine)

    with engine.connect() as conn:
        db_name = conn.execute(text("SELECT DB_NAME()"))
        row = db_name.one()
        print(f"DB_NAME()={row[0]}")

    print("db smoke test: PASS")


def main() -> None:
    parser = argparse.ArgumentParser(description="nba-azure-ml-pipeline smoke test")
    parser.add_argument("--db", action="store_true", help="run Azure SQL smoke test")
    args = parser.parse_args()

    print("nba-azure-ml-pipeline smoke test")
    print(f"utc_now={datetime.now(timezone.utc).isoformat()}")
    print(f"python={sys.version}")

    try:
        import nba_api  # noqa: F401

        print("nba_api import: OK")
    except Exception as e:  # noqa: BLE001
        print(f"nba_api import: FAIL ({type(e).__name__}: {e})")
        raise

    if args.db:
        _db_smoke_test()

    print("smoke test: PASS")


if __name__ == "__main__":
    main()
