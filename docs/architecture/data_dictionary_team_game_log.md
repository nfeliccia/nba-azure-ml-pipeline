## Data Dictionary — `dbo.fact_team_game_log` (TeamGameLog)

### Purpose
Base fact table for `nba_api.stats.endpoints.TeamGameLog` (`resultSets[0]`), stored in Azure SQL for downstream modeling.

### Grain
**One row per team per game** (the same NBA game appears twice: one row for each team).

### Primary Key
- `PK_fact_team_game_log (team_id, game_id)`

### Columns (SQL schema + source mapping)

| Column (SQL) | Type | Null | Default | Source field (TeamGameLog headers) | Notes |
|---|---:|:---:|---|---|---|
| team_id | INT | NO | — | `Team_ID` | NBA team id. |
| game_id | VARCHAR(12) | NO | — | `Game_ID` | Keep as string (leading zeros). NBA IDs are typically 10 chars, but VARCHAR(12) is safe. |
| game_date | DATE | NO | — | `GAME_DATE` | From strings like `"APR 14, 2024"` parsed into a date. |
| matchup | VARCHAR(32) | NO | — | `MATCHUP` | Example: `"GSW vs. UTA"` or `"GSW @ POR"`. |
| wl | CHAR(1) | YES | — | `WL` | `W` or `L`. Nullable in schema (defensive). |
| w | SMALLINT | NO | — | `W` | Season wins-to-date at time of game (as provided by endpoint). |
| l | SMALLINT | NO | — | `L` | Season losses-to-date at time of game. |
| w_pct | DECIMAL(6,5) | YES | — | `W_PCT` | Win pct to date; stored as decimal. |
| minutes | SMALLINT | NO | — | `MIN` | Team total minutes (240 regulation, >240 OT). Renamed from `MIN` to avoid keyword/style issues. |
| fgm | SMALLINT | NO | — | `FGM` | Field goals made. |
| fga | SMALLINT | NO | — | `FGA` | Field goals attempted. |
| fg_pct | DECIMAL(6,5) | YES | — | `FG_PCT` | Field goal percentage. |
| fg3m | SMALLINT | NO | — | `FG3M` | 3PT made. |
| fg3a | SMALLINT | NO | — | `FG3A` | 3PT attempted. |
| fg3_pct | DECIMAL(6,5) | YES | — | `FG3_PCT` | 3PT percentage. |
| ftm | SMALLINT | NO | — | `FTM` | FT made. |
| fta | SMALLINT | NO | — | `FTA` | FT attempted. |
| ft_pct | DECIMAL(6,5) | YES | — | `FT_PCT` | FT percentage. |
| oreb | SMALLINT | NO | — | `OREB` | Offensive rebounds. |
| dreb | SMALLINT | NO | — | `DREB` | Defensive rebounds. |
| reb | SMALLINT | NO | — | `REB` | Total rebounds. |
| ast | SMALLINT | NO | — | `AST` | Assists. |
| stl | SMALLINT | NO | — | `STL` | Steals. |
| blk | SMALLINT | NO | — | `BLK` | Blocks. |
| tov | SMALLINT | NO | — | `TOV` | Turnovers. |
| pf | SMALLINT | NO | — | `PF` | Personal fouls. |
| pts | SMALLINT | NO | — | `PTS` | Points scored. |
| is_home | BIT | NO | — | Derived | Derived from `MATCHUP` (`" vs. "` => home, `" @ "` => away). |
| season | VARCHAR(7) | YES | — | Metadata | Not provided by `rowSet`; populate from extractor config (e.g., `"2023-24"`). Useful for partitioning and sanity checks. |
| ingested_utc | DATETIME2(0) | NO | `SYSUTCDATETIME()` | Metadata | Insert timestamp (UTC) for observability/reprocessing. |

### Indexes
- `IX_fact_team_game_log_game_date` on `(game_date)`
- `IX_fact_team_game_log_team_date` on `(team_id, game_date)`

### Notes / Implementation implications
- This schema intentionally supports **idempotent upserts** keyed on `(team_id, game_id)`.
- `season` is nullable so the table can still accept rows even if we haven’t wired season injection yet, but production loads should populate it.
- `ingested_utc` is server-generated; loader does not need to set it.
