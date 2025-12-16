# Portfolio Architecture — Option B: Private Endpoint + Private DNS for Azure SQL (No Public Access)

## Goal
Keep `publicNetworkAccess = Disabled` on Azure SQL permanently, while still enabling:
- schema creation (DDL)
- ETL ingestion jobs
- Azure ML feature engineering and training
…all over private networking inside Azure.

This demonstrates enterprise-grade security and networking practices.

---

## High-level design (6 building blocks)

### 1) Resource Group + Core Data Store
- **Resource Group**: `rg_nba_prediction_26`
- **Azure SQL Server + Database**:
  - Server: `nba-sql-189800`
  - DB: `nba`
- **Public network**: disabled (already done)
- **Auth**: Entra ID admin + AAD-only auth (already done)

---

### 2) Virtual Network (VNet)
Create a dedicated VNet for the project, for example:
- VNet: `vnet-nba-ml`
- Address space: `10.40.0.0/16`

Subnets (minimum set):
- `snet-private-endpoints` (for private endpoints only)
  - e.g., `10.40.1.0/24`
- `snet-compute` (for compute that runs ETL + schema scripts)
  - e.g., `10.40.2.0/24`

Notes:
- Private endpoints work best when placed in a subnet where you don’t host random workloads.
- Compute runs in a separate subnet with its own NSG rules.

---

### 3) Private Endpoint (Azure Private Link) for Azure SQL
Create a **Private Endpoint** targeting the SQL Server resource.

Outcome:
- SQL becomes reachable via a **private IP** in the VNet (example: `10.40.1.4`)
- Network path stays on the Azure backbone
- No inbound from public internet required

This is the core “private connectivity to PaaS” capability.

---

### 4) Private DNS Zone + VNet Link
Create and link a **Private DNS Zone** for SQL Private Link:
- Zone: `privatelink.database.windows.net`
- Link: attach the zone to `vnet-nba-ml`

Add/auto-create DNS records:
- `nba-sql-189800.privatelink.database.windows.net -> <private-endpoint-ip>`

Result:
- Any compute inside the VNet resolves:
  - `nba-sql-189800.database.windows.net`
  to the private endpoint (instead of public IP)

This is what makes connectivity “just work” without changing connection strings in code.

---

### 5) Private Compute to run schema + ingestion
Run all SQL schema and ingestion from compute **inside** the VNet, e.g. one of:

**Option 5A: Azure VM (simplest to understand)**
- A small Linux VM in `snet-compute`
- Install: Python, ODBC driver, your repo, run scripts
- Good for early phase learning and debugging

**Option 5B: Azure Container Apps Job (cleaner production posture)**
- Containerize your ingestion and schema-runner scripts
- Run as a scheduled job
- Configure VNet integration to place it in `snet-compute`

**Option 5C: Azure ML Compute / Managed Online Endpoint in VNet**
- Azure ML workspace configured for managed VNet / VNet injection
- Training + feature engineering jobs run in private network
- Reads/writes SQL via private endpoint DNS

For portfolio, “Container Apps Job + Azure ML in VNet” is an excellent story.

---

### 6) CI/CD + IaC Story (reproducible portfolio delivery)
Keep infrastructure reproducible in the repo:
- `infra/bicep/sql.bicep` (already)
- Add:
  - `infra/bicep/network.bicep` (VNet + subnets + NSGs)
  - `infra/bicep/private-endpoint-sql.bicep` (private endpoint + DNS zone + links)
  - Transpile artifacts (optional): `infra/arm/*.json`

Deployment workflow:
1. Deploy network
2. Deploy SQL
3. Deploy private endpoint + private DNS zone
4. Deploy compute (job/VM/AML)
5. Run schema script from private compute
6. Start daily ingestion schedule

---

## Data flow (end-to-end)
1. **Ingestion job** (inside VNet) calls NBA API (may require proxy strategy)
2. Job writes raw/base rows to **Azure SQL** over **private endpoint**
3. **Azure ML pipeline** (inside VNet) reads base tables, generates rolling features, trains models
4. Metrics + artifacts tracked in Azure ML / MLflow
5. Future: batch scoring job writes predictions back to SQL

---

## Security posture (what this demonstrates)
- No public exposure for database traffic
- Private Link connectivity for PaaS
- Private DNS for name resolution in private networks
- Separation of concerns via subnets
- Principle of least privilege: compute can reach SQL privately; random internet clients cannot

---

## Why this is “AZ-900 relevant”
This architecture hits core AZ-900 concepts:
- Virtual Networks, subnets
- Private endpoint (Private Link) vs public endpoints
- DNS and name resolution in Azure
- PaaS security posture and network isolation
- Identity-first authentication with Entra ID
<mermaid>
- flowchart LR
  subgraph Azure["Azure (rg_nba_prediction_26)"]
    subgraph VNet["VNet: vnet-nba-ml (10.40.0.0/16)"]
      subgraph PE["Subnet: snet-private-endpoints (10.40.1.0/24)"]
        PEndpoint["Private Endpoint\n(SQL Private Link)\nPrivate IP: 10.40.1.4"]
      end

      subgraph Compute["Subnet: snet-compute (10.40.2.0/24)"]
        Job["Ingestion + Schema Runner\n(Container App Job or VM)"]
        AML["Azure ML Compute / Jobs\n(Feature Engineering + Training)"]
      end

      DNS["Private DNS Zone\nprivatelink.database.windows.net\n(VNet linked)"]
    end

    SQL["Azure SQL Server\nnba-sql-189800.database.windows.net\nDB: nba\nPublic Network: Disabled\nAAD-only: Enabled"]
  end

  Job -->|ODBC / TDS over Private Link| PEndpoint --> SQL
  AML -->|Read base tables / Write outputs| PEndpoint --> SQL
  DNS -. Name resolves to private IP .-> Job
  DNS -. Name resolves to private IP .-> AML

  Internet["NBA API / External Data Source\n(may require proxy strategy)"] --> Job
</mermaid>
<ascii>
-                      +-----------------------------+
                     |      NBA API (Internet)     |
                     |  (may require proxy later)  |
                     +--------------+--------------+
                                    |
                                    v
+---------------------------------------------------------------------+
|                         Azure: rg_nba_prediction_26                 |
|                                                                     |
|  +-------------------- VNet: vnet-nba-ml (10.40.0.0/16) ----------+ |
|  |                                                               | |
|  |  +---------------- Subnet: snet-compute -------------------+   | |
|  |  |                                                        |   | |
|  |  |  +-------------------+     +-------------------------+  |   | |
|  |  |  | Ingestion / DDL    |     | Azure ML Compute / Jobs|  |   | |
|  |  |  | (Job/VM)           |     | (features + training)  |  |   | |
|  |  |  +---------+----------+     +-----------+-------------+  |   | |
|  |  |            |                            |                |   | |
|  |  +------------|----------------------------|----------------+   | |
|  |               |                            |                    | |
|  |               v                            v                    | |
|  |  +---------------- Subnet: snet-private-endpoints -----------+  | |
|  |  |   +-----------------------------------------------+       |  | |
|  |  |   | Private Endpoint (SQL Private Link)            |       |  | |
|  |  |   | Private IP: 10.40.1.4                          |       |  | |
|  |  |   +-------------------+---------------------------+       |  | |
|  |  +-----------------------|---------------------------+       |  | |
|  |                          |                                   |  | |
|  |                          v                                   |  | |
|  |  +--------------------------------------------------------+ |  | |
|  |  | Azure SQL Server: nba-sql-189800.database.windows.net   | |  | |
|  |  | Database: nba                                            | |  | |
|  |  | Public Network Access: Disabled                          | |  | |
|  |  | Azure AD Only Auth: Enabled                              | |  | |
|  |  +--------------------------------------------------------+ |  | |
|  |                                                               | |
|  |  +---------------------------------------------------------+  | |
|  |  | Private DNS Zone: privatelink.database.windows.net       |  | |
|  |  | Linked to VNet; resolves SQL hostname -> private IP      |  | |
|  |  +---------------------------------------------------------+  | |
|  +---------------------------------------------------------------+ |
+---------------------------------------------------------------------+
</ascii> 