"""
# ProjectLog.md
# Example local run:
#   python -m nba_pipeline.ingest.run_extract --config config/extract.yaml
"""

from __future__ import annotations

import argparse
import os
import time
from datetime import datetime, timezone
from typing import List

import yaml
from dotenv import load_dotenv
from nba_api.stats.endpoints import teamgamelog

from nba_pipeline.ops.blob_uploader import BlobUploader


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch NBA TeamGameLog data and upload raw JSON to Azure Blob.")
    parser.add_argument(
        "--config",
        default="config/extract.yaml",
        help="Path to YAML config file (default: config/extract.yaml).",
    )
    return parser.parse_args(argv)


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not data:
        raise ValueError(f"Config file {path} is empty.")
    return data


def generate_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def validate_payload(payload: dict) -> None:
    if "resultSets" not in payload or not payload["resultSets"]:
        raise ValueError("Unexpected payload shape: missing 'resultSets'.")
    first_result = payload["resultSets"][0]
    if "headers" not in first_result or "rowSet" not in first_result:
        raise ValueError("Unexpected payload shape: missing 'headers' or 'rowSet' in first result set.")


def fetch_teamgamelog(team_id: int, season: str, retries: int = 3, base_backoff: float = 1.0) -> dict:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            response = teamgamelog.TeamGameLog(team_id=team_id, season=season)
            payload = response.get_dict()
            validate_payload(payload)
            return payload
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt == retries:
                raise
            sleep_for = base_backoff * (2 ** (attempt - 1))
            time.sleep(sleep_for)

    raise RuntimeError(f"Failed to fetch TeamGameLog after {retries} attempts: {last_error}")  # safety net


def build_blob_path(blob_prefix: str, run_id: str, filename_template: str, team_id: int, season: str) -> str:
    cleaned_prefix = blob_prefix.strip("/ ")
    filename = filename_template.format(team_id=team_id, season=season, run_id=run_id)
    return f"{cleaned_prefix}/{run_id}/raw/nba_api/teamgamelog/{filename}"


def resolve_storage_settings(config: dict) -> tuple[str, str]:
    azure_cfg = config.get("azure", {})
    account_name = os.getenv("AZURE_STORAGE_ACCOUNT") or azure_cfg.get("storage_account")
    container_name = os.getenv("AZURE_STORAGE_CONTAINER") or azure_cfg.get("container")
    if not account_name:
        raise ValueError("Storage account name missing. Set AZURE_STORAGE_ACCOUNT or config.azure.storage_account.")
    if not container_name:
        raise ValueError("Storage container missing. Set AZURE_STORAGE_CONTAINER or config.azure.container.")
    return account_name, container_name


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = parse_args(argv)
    config = load_config(args.config)

    endpoint = config.get("endpoint")
    if endpoint != "teamgamelog":
        raise ValueError(f"Unsupported endpoint '{endpoint}'. Only 'teamgamelog' is supported.")

    teams: List[int] = config.get("teams", [])
    seasons: List[str] = config.get("seasons", [])
    if not teams or not seasons:
        raise ValueError("Config must include non-empty 'teams' and 'seasons' lists.")

    output_cfg = config.get("output", {})
    blob_prefix: str = output_cfg.get("blob_prefix", "runs")
    filename_template: str = output_cfg.get(
        "filename_template",
        "teamgamelog_team{team_id}_season{season}_{run_id}.json",
    )

    account_name, container_name = resolve_storage_settings(config)
    run_id = generate_run_id()

    uploader = BlobUploader(
        account_name=account_name,
        container_name=container_name,
        connection_string=os.getenv("AZURE_STORAGE_CONNECTION_STRING"),
        tenant_id=os.getenv("AZURE_TENANT_ID"),
        client_id=os.getenv("AZURE_CLIENT_ID"),
        client_secret=os.getenv("AZURE_CLIENT_SECRET"),
    )

    print(f"Starting run_id={run_id} for {len(teams)} teams x {len(seasons)} seasons")
    for team_id in teams:
        for season in seasons:
            payload = fetch_teamgamelog(team_id=team_id, season=season)
            blob_path = build_blob_path(blob_prefix, run_id, filename_template, team_id, season)
            bytes_uploaded = uploader.upload_json(blob_path, payload)
            print(f"uploaded team_id={team_id} season={season} blob_path={blob_path} bytes={bytes_uploaded}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
