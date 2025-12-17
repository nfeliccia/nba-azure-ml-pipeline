Yep — the *direction* is right, with one important nuance:

* Your log shows the Azure side is now “enterprise-grade private” (Private Endpoint/DNS + Bastion + private VM, and Managed Identity SQL execution works)  
* The NBA API call from the Azure VM timed out (cloud egress gets blocked/degraded), so doing acquisition from a residential ISP is the practical workaround 
* **Azure Arc won’t “lend” your home internet connection to the Azure VM.** What it *will* do is let Azure *manage/trigger* your home machine as a connected resource, so the home PC can run the extractor using its own egress, then ship files up to Azure . (Arc = management plane; networking stays where the machine is.)

## Plan: Arc-powered hybrid ingest (home PC = fetch, Azure = load)

### 0) Keep the target architecture you already proved

You already validated the key invariant: **Azure SQL stays private-only and your private VM can execute SQL using Managed Identity**  . We’ll keep that.

### 1) Add a “landing zone” in Azure for raw data

* Create a Storage Account + Blob container like `nba-raw/` (cheap, simple).
* Decide the upload auth method for the home PC:

  * **Fastest dev:** generate a *container-scoped SAS* (time-limited) and store it as an env var on the home PC.
  * **Cleaner long-run:** service principal + `az login --service-principal` for `azcopy` (more setup, less “token in a file”).

(Arc pricing note: Arc itself is mainly a control-plane; **cost comes from add-ons** like Monitor/Defender/Update Manager if you enable them) ([Microsoft Azure][1]).

### 2) Onboard the home PC to Azure Arc (so Azure can “see” it)

* In Azure Portal: Azure Arc → **Servers** → Add → generate the onboarding script for *Windows* and run it on the home PC (this installs the Azure Connected Machine agent and registers it) ([Microsoft Learn][2]).
* If you want non-interactive / repeatable onboarding later, use a service principal onboarding flow ([Microsoft Learn][3]).
* Validate: machine shows up as an Arc-enabled server in the portal ([Azure Docs][4]).

### 3) Prove remote execution: “Run Command” on the Arc machine

This is your killer demo move because it turns the home PC into a managed runner:

* Use **Run command on Arc-enabled servers** to run a simple `python --version` / “hello world” first ([Microsoft Learn][5]).
* Then run your extractor entrypoint the same way (or install it as a scheduled task locally and just use Arc for health checks).

(Arc Run Command exists specifically to execute scripts *without* RDP/SSH into the box) ([Microsoft Learn][5]).

### 4) Home PC job: fetch + normalize + upload (idempotent)

Implement (or adapt) a single command like:

* `python -m nba_pipeline.ingest.fetch_teamgamelog --season 2023-24 --out data/out/`
* Write outputs as:

  * `raw/` JSON (for traceability)
  * `normalized/` Parquet or CSV (for loading)
  * `manifest.json` (row counts, hash, min/max GAME_DATE, etc.)

Then upload:

* `azcopy copy "data/out/*" "https://<acct>.blob.core.windows.net/nba-raw?<SAS>" --recursive`

Data-science mindset: treat each run as a reproducible batch with metadata so you can debug and backfill cleanly.

### 5) Azure side loader: private VM pulls from Blob → loads to private SQL

On `vm-nba-runner`:

* Download the latest batch from Blob (SAS URL or storage key stored *only* on the VM; or use a short-lived SAS you paste when running).
* Load into `dbo.fact_team_game_log` using the MI-based SQL path you already proved (`exec_sql_with_aad.py --cred mi`) .
* Make it idempotent using `(team_id, game_id)` as the natural key (already in your table design) .

### 6) Automation options (pick the one that matches your “pain tolerance”)

* **Simple & reliable:** Windows Task Scheduler on home PC runs nightly; Azure VM loader runs after (manual at first, cron later).
* **More “Azure-native”:** Blob “new file” triggers an Azure Function *with VNet integration* that loads into private SQL using Managed Identity (bigger build, nicer story).

## Do I agree Arc is the next step?

Yes — *if your goal is a portfolio-grade hybrid pattern*: “cloud-private data plane + on-prem acquisition runner managed from Azure.” That matches exactly what your 2025-12-15 log says you wanted to do next .

If you want the **fastest path to first rows in Azure SQL**, Arc is optional: you can run the extractor on the home PC and upload to Blob immediately. Arc becomes the “make it slick + managed + repeatable” layer.

If you want, next message tell me the home PC OS (Windows 10/11?) and whether you prefer **SAS-first** (fast) or **service principal** (cleaner), and I’ll write the exact command checklist you can paste/run.

[1]: https://azure.microsoft.com/en-us/pricing/details/azure-arc/core-control-plane/?utm_source=chatgpt.com "Azure Arc pricing"
[2]: https://learn.microsoft.com/en-us/azure/azure-arc/servers/quick-enable-hybrid-vm?utm_source=chatgpt.com "Connect a machine to Arc-enabled servers (Windows or ..."
[3]: https://learn.microsoft.com/en-us/azure/azure-arc/servers/onboard-service-principal?utm_source=chatgpt.com "Connect hybrid machines to Azure at scale - Azure Arc"
[4]: https://docs.azure.cn/en-us/azure-arc/servers/onboard-portal?utm_source=chatgpt.com "Connect hybrid machines to Azure using a deployment script"
[5]: https://learn.microsoft.com/en-us/azure/azure-arc/servers/run-command?utm_source=chatgpt.com "Run command on Azure Arc-enabled servers (Preview)"
