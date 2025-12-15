from __future__ import annotations

import sys
from datetime import datetime, timezone


def main() -> None:
    print("nba-azure-ml-pipeline smoke test")
    print(f"utc_now={datetime.now(timezone.utc).isoformat()}")
    print(f"python={sys.version}")

    try:
        import nba_api  # noqa: F401
        print("nba_api import: OK")
    except Exception as e:
        print(f"nba_api import: FAIL ({type(e).__name__}: {e})")
        raise

    print("smoke test: PASS")


if __name__ == "__main__":
    main()
