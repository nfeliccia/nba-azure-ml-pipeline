from __future__ import annotations

import json
from typing import Optional

from azure.identity import ClientSecretCredential
from azure.storage.blob import BlobServiceClient, ContentSettings


class BlobUploader:
    """Minimal helper for uploading JSON blobs to Azure Storage."""

    def __init__(
        self,
        *,
        container_name: str,
        account_name: Optional[str] = None,
        connection_string: Optional[str] = None,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ) -> None:
        self.container_client = self._build_container_client(
            container_name=container_name,
            account_name=account_name,
            connection_string=connection_string,
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
        )

    def _build_container_client(
        self,
        *,
        container_name: str,
        account_name: Optional[str],
        connection_string: Optional[str],
        tenant_id: Optional[str],
        client_id: Optional[str],
        client_secret: Optional[str],
    ):
        if connection_string:
            service_client = BlobServiceClient.from_connection_string(connection_string)
        else:
            if not all([account_name, tenant_id, client_id, client_secret]):
                raise ValueError(
                    "Service principal auth requires account_name, tenant_id, client_id, and client_secret."
                )

            account_url = f"https://{account_name}.blob.core.windows.net"
            credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret,
            )
            service_client = BlobServiceClient(account_url=account_url, credential=credential)

        container_client = service_client.get_container_client(container_name)
        if not container_client.exists():
            raise RuntimeError(f"Container '{container_name}' not found or inaccessible.")

        return container_client

    def upload_json(self, blob_path: str, payload: dict) -> int:
        """Upload a JSON payload and return the number of bytes written."""
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        blob_client = self.container_client.get_blob_client(blob_path)
        blob_client.upload_blob(
            body,
            overwrite=True,
            content_settings=ContentSettings(content_type="application/json; charset=utf-8"),
        )
        return len(body)
