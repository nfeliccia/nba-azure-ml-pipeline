
## 2025-12-15 (PM) — Provisioned Azure SQL via Bicep using Azure CLI from Windows PowerShell (IaC + security-first)

**Objective**
- Create a real Azure SQL Server + Azure SQL Database using Infrastructure-as-Code (IaC) so the NBA pipeline has a cloud “system of record”.
- Do it in a way that demonstrates Azure competency for AZ-900 and portfolio purposes:
  - Use Azure CLI
  - Use Bicep (and generate ARM JSON)
  - Follow secure defaults (no public exposure by default)
  - Capture the work in the repo so it’s reproducible.

---

## What I did (high-level narrative)

### 1) Worked locally in Windows PowerShell, not Cloud Shell
- I ran everything from my **Windows workstation** using **Windows PowerShell** as the shell.
- I invoked **Azure CLI** commands (`az ...`) from PowerShell.
- I did **not** use Bash.
- I did **not** use Azure Cloud Shell.
- This matters because it proves I can run Azure provisioning workflows from a “normal” engineering workstation, which is the reality for many enterprise environments.

### 2) Used Azure CLI authentication + subscription context management
- I authenticated with `az login`.
- Initially I hit an identity/subscription mismatch (multiple identities/tenants). I resolved this by selecting the correct tenant/subscription where my resource group exists.
- I confirmed the active subscription context with:
  - `az account list -o table`
- I validated the subscription was enabled and set as default.

**Outcome**
- Azure CLI was correctly pointed at:
  - Subscription: `MightyWorkSubscription`
  - Subscription ID: `659bc9fe-df16-4de2-902f-cf9883772bc7`
  - Tenant: `cce0306d-cc27-4c78-80a1-00e10ecc1da3`

### 3) Captured parameters in PowerShell variables (portable and repeatable)
- In PowerShell I set variables like:
  - `$rg` (resource group name)
  - `$sqlServerName` (globally-unique SQL server name)
  - `$sqlAdminLogin`
  - `$aadLogin` and `$aadObjectId` (for Entra admin assignment)
- These values were then passed into the deployment command.
- This is important: the parameterization keeps the deployment reproducible and avoids hardcoding values inside the template.

### 4) Implemented Infrastructure-as-Code using Bicep
- I created a Bicep template in the repo:
  - `infra/bicep/sql.bicep`
- This template provisions:
  - Azure SQL logical server (`Microsoft.Sql/servers`)
  - Azure SQL database (`Microsoft.Sql/servers/databases`)
  - Entra ID (Azure AD) administrator (`Microsoft.Sql/servers/administrators`)
  - Azure AD-only authentication (`Microsoft.Sql/servers/azureADOnlyAuthentications`)
  - (Optional) firewall rules (present but disabled by default)
- I ran `az deployment group validate` to validate before creation.
- Then I ran `az deployment group create` to deploy it at **resource-group scope**.

### 5) Security-first defaults were enforced
The deployed SQL Server configuration confirms several “good security posture” decisions:
- **Public network access disabled**:
  - `publicNetworkAccess: Disabled`
- **Minimum TLS version = 1.2**
- **Azure AD-only authentication enabled**
- SQL admin password was **not committed** and not stored in files:
  - I prompted for it securely in PowerShell (`Read-Host -AsSecureString`)
  - Converted it only for the duration of the command
  - Then removed the plaintext variable

**Why this matters**
- This is the exact kind of control AZ-900 expects you to understand: identity, network exposure, encryption-in-transit, and secure secrets handling.

### 6) Fixed a real-world deployment sequencing issue (important learning)
- My first attempt failed with a clear ARM error stating that Azure AD-only auth cannot be enabled until the Azure AD admin is configured.
- I corrected the Bicep template by explicitly sequencing the resources (ensuring AAD admin is created before enabling AAD-only auth).
- The final deployment succeeded.

This was a real “cloud engineering” moment:
- Validation can pass while deployment fails due to ordering constraints.
- Knowing how to read ARM errors and adjust IaC is a key practical skill.

### 7) Generated ARM JSON from Bicep (explicit “Bicep → ARM” proof)
- After deploying successfully, I generated the equivalent ARM JSON:
  - `az bicep build --file .\infra\bicep\sql.bicep --outfile .\infra\arm\sql.json`
- This is important for learning/portfolio:
  - It demonstrates that Bicep is a higher-level DSL that compiles to ARM templates.
  - I now have both artifacts in source control.

### 8) Verified success with CLI evidence (trust but verify)
I verified end-to-end success with:
- Deployment state:
  - `az deployment group show ... --query properties.provisioningState`
  - Result: `Succeeded`
- SQL Server existence and key properties:
  - `az sql server show ...`
  - Confirmed: server is `Ready`, public access disabled, TLS 1.2, AAD-only auth enabled, FQDN assigned
- Database existence and status:
  - `az sql db show ...`
  - Confirmed: database `nba` is `Online`

---

## Deliverables produced (in repo + Azure)

### In Azure
- Resource group (already existed): `rg_nba_prediction_26` in `eastus2`
- SQL Server: `nba-sql-189800`
- Database: `nba`
- Entra admin configured and Azure AD-only authentication enabled

### In GitHub repo
- `infra/bicep/sql.bicep` — source IaC template
- `infra/arm/sql.json` — transpiled ARM template artifact
- Git commit pushed via PyCharm

---

## Why this matters for the larger project
This milestone is not “just admin work.”
It establishes the durable cloud foundation for the pipeline:
- All NBA raw/base data will ultimately land here (Azure SQL as the system of record).
- Azure ML feature engineering and training will later read from this database (or from curated exports).
- This is also strong portfolio evidence that I can:
  - Use IaC
  - Use Azure CLI
  - Work with identity + tenants + subscriptions
  - Apply secure defaults (no public exposure by default)
  - Troubleshoot real ARM deployment issues

---

## Next step
- Decide how to connect to the DB for schema creation, given public access is disabled:
  - Option A: temporarily enable public access restricted to my IP (dev convenience, documented as temporary)
  - Option B: private endpoint + private DNS (enterprise-grade; more setup)
- Apply the first schema script to create the initial table for `TeamGameLog` ingestion.



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
