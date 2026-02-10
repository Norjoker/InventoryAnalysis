import argparse
import os
from pathlib import Path
from typing import Any

import yaml

from auth import DEFAULT_DELEGATED_SCOPES, DEFAULT_GRAPH_SCOPE, build_provider_from_env
from graph_client import GraphClient


REQUIRED_CONFIG_FIELDS = (
    "site_url",
    "library_name",
    "folder_path",
    "file_pattern",
    "output_file",
)


def load_config(config_path: str) -> dict[str, Any]:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    if not isinstance(data, dict):
        raise ValueError("Config file must contain a top-level mapping/object")

    missing = [field for field in REQUIRED_CONFIG_FIELDS if not data.get(field)]
    if missing:
        raise ValueError("Missing required config fields: " + ", ".join(missing))

    return data


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def load_device_flow_settings() -> dict[str, Any]:
    return {
        "tenant_id": _require_env("TENANT_ID"),
        "client_id": _require_env("CLIENT_ID"),
        "scopes": os.getenv("GRAPH_SCOPES", " ".join(DEFAULT_DELEGATED_SCOPES)).split(),
        "cache_path": os.getenv("MSAL_CACHE_PATH", ".msal_token_cache.json"),
    }


def load_confidential_flow_settings() -> dict[str, Any]:
    return {
        "tenant_id": _require_env("TENANT_ID"),
        "client_id": _require_env("CLIENT_ID"),
        "private_key_path": _require_env("CERT_PRIVATE_KEY_PATH"),
        "cert_path": _require_env("CERT_PUBLIC_PATH"),
        "thumbprint": _require_env("CERT_THUMBPRINT"),
        "passphrase": os.getenv("CERT_PASSPHRASE"),
        "scope": os.getenv("GRAPH_APP_SCOPE", DEFAULT_GRAPH_SCOPE),
        "cache_path": os.getenv("MSAL_CACHE_PATH", ".msal_token_cache.json"),
    }


def run(config: dict[str, Any], token: str, auth_mode: str) -> None:
    """Primary script workflow."""
    client = GraphClient(access_token=token)
    snapshots = client.list_snapshot_files(
        site_url=config["site_url"],
        library_name=config["library_name"],
        folder_path=config["folder_path"],
        filename_pattern=config["file_pattern"],
    )

    print(f"Authentication mode: {auth_mode}")
    print(f"Found {len(snapshots)} snapshot files matching pattern.")
    for snapshot in snapshots:
        print(f"- {snapshot.snapshot_date.isoformat()} :: {snapshot.name}")

    # Continue downstream processing in chronological order
    for snapshot in snapshots:
        print(f"Processing snapshot: {snapshot.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run inventory analysis with YAML config and Azure AD authentication."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to YAML config file (e.g., config.yaml)",
    )
    parser.add_argument(
        "--auth-mode",
        choices=("device", "confidential"),
        default="device",
        help="Authentication mode: 'device' (default) or 'confidential'.",
    )
    args = parser.parse_args()

    config = load_config(args.config)

    if args.auth_mode == "device":
        auth_settings = load_device_flow_settings()
        provider = build_provider_from_env(cache_path=auth_settings["cache_path"])
        token = provider.acquire_token_device_flow(scopes=auth_settings["scopes"])
    else:
        auth_settings = load_confidential_flow_settings()
        provider = build_provider_from_env(cache_path=auth_settings["cache_path"])
        token = provider.acquire_token_confidential(
            private_key_path=auth_settings["private_key_path"],
            cert_path=auth_settings["cert_path"],
            thumbprint=auth_settings["thumbprint"],
            passphrase=auth_settings["passphrase"],
            scope=auth_settings["scope"],
        )

    run(config=config, token=token, auth_mode=args.auth_mode)
