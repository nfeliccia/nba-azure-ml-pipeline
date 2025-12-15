 ### 2025-12-15 (AM) — Repo bootstrapped, dev branch created, first NBA API pull succeeded

**Objective**
- Start fresh on the NBA-to-Azure project with a clean, portfolio-quality Git repo.
- Establish a repeatable local dev workflow (PyCharm + venv + editable install).
- Prove the pipeline is “alive” by making at least one real `nba_api` call and producing a normalized dataset that can later be persisted into Azure SQL.
- Keep documentation as a first-class deliverable (ProjectLog.md, docs folder, ADRs).

---

## Work completed

### 1) Repo creation and local setup
- Created the new GitHub repository under my personal account (`nfeliccia`) named:
  - `nba-azure-ml-pipeline`
- Cloned the repo locally to:
  - `C:\projects\nba-azure-ml-pipeline`
- Opened the repo in PyCharm and configured a local Python virtual environment (`.venv`).

### 2) Initial repo structure and documentation scaffolding
- Bootstrapped a documentation-first repository layout, including:
  - `ProjectLog.md` (this file) as a narrative log of decisions, progress, and evidence
  - `README.md` and `pyproject.toml`
  - `docs/architecture`, `docs/decisions`, `docs/howto`, `docs/screenshots`
  - `src/nba_pipeline/...` package layout for production code
  - `data/.gitkeep` and other placeholders where needed so empty directories can be tracked
- Added early documentation artifacts:
  - Architecture stub (`docs/architecture/ARCHITECTURE.md`)
  - ADR stub (`docs/decisions/0001-record-architecture-decisions.md`)
  - Dev setup stub (`docs/howto/DEV_SETUP.md`)
  - Captured ChatGPT conversation notes under `docs/ChatGPTConvo/` (helpful for reproducing reasoning and decisions)

### 3) Git workflow improvements
- Verified `main` is clean and pushed the bootstrap commit to GitHub.
- Created a `dev` branch and pushed it to origin for ongoing development work:
  - `git checkout -b dev`
  - `git push -u origin dev`
- Goal: keep `main` stable, do daily work on `dev`, merge on milestones.

---

## Issues encountered and how they were resolved

### A) Git clone URL error (HTTP 400)
**Symptom**
- `git clone https://github.com/<your-github-username>/nba-azure-ml-pipeline.git` failed with HTTP 400.

**Root cause**
- I literally used the placeholder `<your-github-username>` in the URL instead of my real GitHub username.

**Fix**
- Replaced the placeholder with my real username:
  - `git clone https://github.com/nfeliccia/nba-azure-ml-pipeline.git`

---

### B) Git “dubious ownership” safety check
**Symptom**
- Git refused to operate in the repo folder and warned about “dubious ownership”.
- Repo was owned by `BUILTIN/Administrators` but my user is `AzureAD/NicFeliccia`.

**Fix**
- Added the repo to Git’s safe.directory list:
  - `git config --global --add safe.directory "C:/projects/nba-azure-ml-pipeline"`

**Lesson**
- Corporate/work machines sometimes have directory ownership constraints.
- This is a normal fix, and it is safe when applied to a known directory.

---

### C) Empty directories and `.gitkeep`
**Symptom**
- Git does not track empty directories.
- I attempted to generate `.gitkeep` files broadly and accidentally created placeholders inside `.idea` and `.venv`.

**Fix**
- Removed `.gitkeep` under `.idea` and `.venv` so those folders never get tracked.
- Kept `.gitkeep` only for intentional empty directories:
  - `notebooks/`, `project_notes/`, `tests/`
  - `infra/arm/` and `infra/bicep/` (because `infra/` itself contained only empty subfolders)

**Lesson**
- `.venv/` and `.idea/` should never be committed.
- Use `.gitkeep` only where Git needs a file to track a directory that is intentionally empty.

---

### D) Editable install failure: TOML decode error
**Symptom**
- `python -m pip install -e .` failed with:
  - `tomllib.TOMLDecodeError: Invalid statement (at line 1, column 1)`

**Root cause**
- The `pyproject.toml` file had a UTF-8 BOM at the beginning:
  - Hex showed `EF BB BF` at offset `00000000`.

**Fix**
- Rewrote the file content using UTF-8 without BOM so Python’s TOML parser is happy.
- Verified the BOM was gone using `Format-Hex`.

**Result**
- `python -m pip install -e .` succeeded and installed:
  - `nba_api`, `requests`, `tenacity`, `pyodbc`, `sqlalchemy`, `python-dotenv` plus dependencies

**Lesson**
- Encoding matters. BOM can break TOML parsing.
- Always check with hex view when parsing fails at line 1 column 1.

---

## Key technical milestones achieved

### 1) Smoke test established
- Created a small smoke test script to verify:
  - Python runtime works
  - package imports work
  - basic execution path is stable
- This prevents “mystery failures” later when we add Azure, containers, and scheduled runs.

### 2) First real NBA API extraction succeeded
- Implemented and ran `TeamGameLog` sample extraction:
  - `team_id = 1610612744` (Warriors)
  - `season = "2023-24"`
- Saved raw payload JSON under:
  - `data/raw/nba_api/teamgamelog_team1610612744_2023-24_<timestamp>.json`

**Result**
- Successful API call, exit code 0.
- This proves local connectivity is working for at least this endpoint.

### 3) Normalization succeeded: raw JSON -> pandas DataFrame
- Converted `resultSets[0].headers` + `rowSet` into a DataFrame
- Added two useful transformations:
  - `GAME_DATE` parsed to a date
  - `IS_HOME` derived from `MATCHUP` string
- Verified schema and dtypes:

Key columns (28 total):
- IDs: `Team_ID` (int64), `Game_ID` (object)
- Date/matchup: `GAME_DATE`, `MATCHUP`, derived `IS_HOME`
- Outcome: `WL`, `W`, `L`, `W_PCT`
- Stats: `FGM`, `FGA`, `FG_PCT`, `FG3M`, `FG3A`, `FG3_PCT`, `FTM`, `FTA`, `FT_PCT`, `OREB`, `DREB`, `REB`, `AST`, `STL`, `BLK`, `TOV`, `PF`, `PTS`, `MIN`

This dataset is a strong candidate for the first “base fact” table in Azure SQL.

---

## Decisions made (and why)

### Decision: Use `pyproject.toml` (modern packaging) and editable installs
- Chosen approach:
  - `pyproject.toml` as the source of truth for dependencies
  - `pip install -e .` so local code changes are reflected immediately
- Benefit:
  - Clean modern packaging
  - Easy transition to container builds later
  - Easy alignment with Azure ML and production pipeline code structure

### Decision: Keep the repo structured for long-term portfolio value
- Documentation is not an afterthought:
  - Architecture docs
  - ADRs
  - Project log narrative
  - Captured conversation notes

This supports the meta-goal: show cloud data scientist engineering habits, not just “code that runs once”.

### Decision: Work on `dev` branch
- Use `dev` for daily iteration.
- Merge to `main` on testable milestones.

---

## Evidence: commands and outputs (high value for reproducibility)

- Clone:
  - `git clone https://github.com/nfeliccia/nba-azure-ml-pipeline.git`

- Git safe directory fix:
  - `git config --global --add safe.directory "C:/projects/nba-azure-ml-pipeline"`

- Branch:
  - `git checkout -b dev`
  - `git push -u origin dev`

- Editable install:
  - `python -m pip install -U pip`
  - `python -m pip install -e .`

- NBA API sample pull:
  - `python src/nba_pipeline/ingest/fetch_team_gamelog_sample.py`

- Normalize:
  - `python src/nba_pipeline/ingest/normalize_teamgamelog.py`

---

## Current state summary (end of AM session)
- Repo exists on GitHub and is cleanly structured.
- `dev` branch exists and is tracking origin.
- Local environment is working with editable install.
- First NBA API pull succeeded and the data is normalized into a DataFrame.
- We have enough information to design the first Azure SQL table schema and ingestion pattern.

---

## Next steps (post-lunch plan)
1) Azure SQL provisioning:
   - Create Azure SQL Server + Database (Portal or IaC)
2) Add SQL scripts to repo:
   - Create table for team game log fact data
   - Add idempotent upsert strategy (MERGE or equivalent)
3) Build the first “load to SQL” Python step:
   - Read normalized DataFrame
   - Load into staging
   - MERGE into final table keyed on `(team_id, game_id)`
4) Start backfill strategy:
   - Parameterize season list
   - Loop seasons with minimal API calls
5) Continue documentation:
   - Add an ADR for “Why TeamGameLog is the first ingestion primitive”
   - Extend architecture doc with stage boundaries and responsibilities
