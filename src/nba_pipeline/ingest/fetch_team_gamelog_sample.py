from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from nba_api.stats.endpoints import teamgamelog


def main() -> None:
    # Pick a stable, known team_id (Warriors = 1610612744)
    team_id = 1610612744
    season = "2023-24"  # change later as needed

    print(f"Fetching TeamGameLog: team_id={team_id}, season={season}")

    resp = teamgamelog.TeamGameLog(team_id=team_id, season=season)

    payload = resp.get_dict()  # raw-ish API payload
    out_dir = Path("data/raw/nba_api")
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"teamgamelog_team{team_id}_{season}_{ts}.json"

    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote: {out_path.as_posix()}")


if __name__ == "__main__":
    main()
