import json
import os
from pathlib import Path
from typing import Any

import msal

DEFAULT_GRAPH_SCOPE = "https://graph.microsoft.com/.default"
DEFAULT_DELEGATED_SCOPES = ["Files.Read.All", "Sites.Read.All"]


class AuthConfigError(ValueError):
    """Raised when required auth configuration is missing."""


class TokenProvider:
    """Acquire and cache access tokens via MSAL.

    Primary flow: public client + device code flow.
    Optional flow: confidential client + certificate.
    """

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        cache_path: str = ".msal_token_cache.json",
        authority_host: str = "https://login.microsoftonline.com",
    ) -> None:
        if not tenant_id:
            raise AuthConfigError("TENANT_ID is required")
        if not client_id:
            raise AuthConfigError("CLIENT_ID is required")

        self.tenant_id = tenant_id
        self.client_id = client_id
        self.authority = f"{authority_host.rstrip('/')}/{tenant_id}"
        self.cache_path = Path(cache_path)
        self.cache = self._load_cache()

    def _load_cache(self) -> msal.SerializableTokenCache:
        cache = msal.SerializableTokenCache()
        if self.cache_path.exists():
            cache.deserialize(self.cache_path.read_text(encoding="utf-8"))
        return cache

    def _save_cache(self) -> None:
        if self.cache.has_state_changed:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(self.cache.serialize(), encoding="utf-8")

    def _build_public_client(self) -> msal.PublicClientApplication:
        return msal.PublicClientApplication(
            client_id=self.client_id,
            authority=self.authority,
            token_cache=self.cache,
        )

    def _build_confidential_client(
        self,
        private_key_path: str,
        cert_path: str,
        thumbprint: str,
        passphrase: str | None = None,
    ) -> msal.ConfidentialClientApplication:
        private_key = Path(private_key_path).read_text(encoding="utf-8")
        cert = Path(cert_path).read_text(encoding="utf-8")

        credential: dict[str, Any] = {
            "private_key": private_key,
            "thumbprint": thumbprint,
            "public_certificate": cert,
        }
        if passphrase:
            credential["passphrase"] = passphrase

        return msal.ConfidentialClientApplication(
            client_id=self.client_id,
            authority=self.authority,
            client_credential=credential,
            token_cache=self.cache,
        )

    def acquire_token_device_flow(self, scopes: list[str]) -> str:
        app = self._build_public_client()
        accounts = app.get_accounts()

        if accounts:
            result = app.acquire_token_silent(scopes=scopes, account=accounts[0])
            if result and "access_token" in result:
                self._save_cache()
                return result["access_token"]

        flow = app.initiate_device_flow(scopes=scopes)
        if "user_code" not in flow:
            raise RuntimeError(f"Failed to initiate device flow: {json.dumps(flow, indent=2)}")

        print(flow["message"])
        result = app.acquire_token_by_device_flow(flow)
        if "access_token" not in result:
            raise RuntimeError(f"Failed to acquire token by device flow: {json.dumps(result, indent=2)}")

        self._save_cache()
        return result["access_token"]

    def acquire_token_confidential(
        self,
        private_key_path: str,
        cert_path: str,
        thumbprint: str,
        scope: str = DEFAULT_GRAPH_SCOPE,
        passphrase: str | None = None,
    ) -> str:
        app = self._build_confidential_client(
            private_key_path=private_key_path,
            cert_path=cert_path,
            thumbprint=thumbprint,
            passphrase=passphrase,
        )

        result = app.acquire_token_silent(scopes=[scope], account=None)
        if not result or "access_token" not in result:
            result = app.acquire_token_for_client(scopes=[scope])

        if "access_token" not in result:
            raise RuntimeError(f"Failed to acquire confidential client token: {json.dumps(result, indent=2)}")

        self._save_cache()
        return result["access_token"]


def build_provider_from_env(cache_path: str = ".msal_token_cache.json") -> TokenProvider:
    tenant_id = os.getenv("TENANT_ID", "")
    client_id = os.getenv("CLIENT_ID", "")
    return TokenProvider(tenant_id=tenant_id, client_id=client_id, cache_path=cache_path)
