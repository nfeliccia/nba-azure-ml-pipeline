# Architecture

## High level
- Source: NBA API via 
ba_api
- Storage: Azure SQL (raw/base tables)
- Modeling: Azure Machine Learning (feature engineering + training + evaluation)

## Design principles
- Minimize calls to NBA endpoints
- Idempotent loads (no duplicates)
- Backfill window (up to 3 days)
- Features computed in Azure ML, not in Azure SQL
