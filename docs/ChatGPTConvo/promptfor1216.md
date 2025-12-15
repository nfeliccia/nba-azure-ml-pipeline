Hey ChatGPT. Continuing my project: nba-azure-ml-pipeline.

Context:
- We built a full Option B secure Azure architecture:
  - Azure SQL Server + DB (publicNetworkAccess disabled, AAD-only auth)
  - VNet vnet-nba-ml with subnets (private endpoints, compute, Bastion)
  - Private endpoint + private DNS zone privatelink.database.windows.net for SQL
  - Linux VM vm-nba-runner (no public IP) + Azure Bastion
  - ODBC Driver 18 installed, pyodbc works
  - scripts/exec_sql_with_aad.py runs SQL using either Azure CLI credential or VM Managed Identity
  - We bootstrapped VM identity permissions and successfully created dbo.fact_team_game_log in Azure SQL using Managed Identity

Problem:
- nba_api calls to stats.nba.com from the Azure VM time out (likely cloud IP blocking), so direct ingestion from Azure is unreliable.

What I want today:
- Pursue a hybrid ingest pattern using Azure Arc:
  - Onboard my home PC with Azure Arc.
  - Run NBA API extraction on the home PC (uses home ISP egress).
  - Get data into Azure without exposing Azure SQL publicly.
  - Preferred flow: home PC -> Azure Blob Storage (raw JSON/Parquet) -> Azure VM (inside VNet) loads into Azure SQL via private endpoint.
- I want this to be portfolio-grade: secure, documented, and automated.
- Please give me a step-by-step plan with concrete commands (Arc onboarding overview, blob upload approach, and VM-side loader that consumes from blob and MERGEs into dbo.fact_team_game_log).
- Also suggest how to structure repo folders/scripts so the “extract” and “load” stages are cleanly separated.
