"""SQLAlchemy engine factory for Azure SQL Database using Entra tokens.

Environment variables:
- AZURE_SQL_SERVER: Azure SQL server host (e.g., myserver.database.windows.net)
- AZURE_SQL_DATABASE: Database name
- Optional auth:
  - AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET for service principal auth
    (falls back to managed identity via DefaultAzureCredential when not set).
"""

from __future__ import annotations

import os
import struct
from typing import Any, Callable, Dict

from azure.identity import ClientSecretCredential, DefaultAzureCredential
from azure.core.credentials import TokenCredential
from sqlalchemy import event
from sqlalchemy.engine import Engine, URL, create_engine

# pyodbc access token constant
COPT_SS_ACCESS_TOKEN = 1256
TOKEN_SCOPE = "https://database.windows.net/.default"


def _build_credential() -> ClientSecretCredential | DefaultAzureCredential:
    """Return the credential for the current environment."""

    client_id = os.getenv("AZURE_CLIENT_ID")
    tenant_id = os.getenv("AZURE_TENANT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")

    if client_id and tenant_id and client_secret:
        return ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
        )

    return DefaultAzureCredential()


def _get_token_packer(credential: TokenCredential) -> Callable[[], Dict[int, bytes]]:
    """Return a callable that packs fresh tokens for pyodbc attrs_before."""

    def _pack_token() -> Dict[int, bytes]:
        token = credential.get_token(TOKEN_SCOPE).token
        token_bytes = token.encode("utf-16-le")
        packed_token = struct.pack("<I", len(token_bytes)) + token_bytes
        return {COPT_SS_ACCESS_TOKEN: packed_token}

    return _pack_token


def make_engine() -> Engine:
    """Create a SQLAlchemy engine configured for Azure SQL and Entra tokens."""

    server = os.getenv("AZURE_SQL_SERVER")
    database = os.getenv("AZURE_SQL_DATABASE")

    if not server:
        raise ValueError("AZURE_SQL_SERVER is required")
    if not database:
        raise ValueError("AZURE_SQL_DATABASE is required")

    credential = _build_credential()
    token_factory = _get_token_packer(credential)

    url = URL.create(
        drivername="mssql+pyodbc",
        username=None,
        password=None,
        host=server,
        port=1433,
        database=database,
        query={
            "driver": "ODBC Driver 18 for SQL Server",
            "Encrypt": "yes",
            "TrustServerCertificate": "no",
            "Authentication": "ActiveDirectoryAccessToken",
        },
    )

    engine = create_engine(url)

    @event.listens_for(engine, "do_connect")
    def _inject_token(dialect: Any, conn_rec: Any, cargs: Any, cparams: dict) -> Any:  # noqa: ANN401
        attrs = cparams.get("attrs_before", {})
        attrs.update(token_factory())
        cparams["attrs_before"] = attrs
        return dialect.connect(*cargs, **cparams)

    return engine
