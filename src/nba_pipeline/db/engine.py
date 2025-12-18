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
from typing import Any, Callable, Dict, Iterable

from azure.core.credentials import TokenCredential
from azure.identity import ClientSecretCredential, DefaultAzureCredential
from sqlalchemy import event
from sqlalchemy.engine import Engine, URL, create_engine
from sqlalchemy.pool import NullPool

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


def _strip_conn_attrs(conn_str: str, keys: Iterable[str]) -> str:
    """
    Remove any 'key=value' segments (case-insensitive key match) from a semicolon-delimited ODBC string.
    Example keys: ["Trusted_Connection", "Authentication"]
    """
    keys_lc = {k.lower() for k in keys}
    parts = [p for p in conn_str.split(";") if p.strip()]

    kept: list[str] = []
    for p in parts:
        k = p.split("=", 1)[0].strip().lower()
        if k in keys_lc:
            continue
        kept.append(p)

    # Rebuild with trailing semicolon to match common ODBC formatting
    return ";".join(kept) + ";"


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
            "Connection Timeout": "30",
        },
    )

    # NullPool avoids holding connections across token lifetimes; simplest for now.
    engine = create_engine(url, poolclass=NullPool, pool_pre_ping=True)

    @event.listens_for(engine, "do_connect")
    def _inject_token(dialect: Any, conn_rec: Any, cargs: Any, cparams: dict) -> Any:  # noqa: ANN401
        # cargs[0] is the ODBC connection string created by SQLAlchemy/pyodbc
        conn_str = cargs[0]

        # SQLAlchemy's pyodbc dialect may add Trusted_Connection=Yes when no UID/PWD is supplied.
        # Also strip Authentication defensively to avoid driver errors when token injection is used.
        conn_str = _strip_conn_attrs(conn_str, keys=["Trusted_Connection", "Authentication"])

        # Preserve any additional positional args beyond the connection string
        cargs = (conn_str,) + tuple(cargs[1:])

        # Inject fresh token for every new DBAPI connection
        attrs = cparams.get("attrs_before", {})
        attrs.update(token_factory())
        cparams["attrs_before"] = attrs

        return dialect.connect(*cargs, **cparams)

    return engine
