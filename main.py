import argparse
import os
from pathlib import Path
from typing import Any

import yaml


REQUIRED_CONFIG_FIELDS = (
    "site_url",
    "library_name",
    "folder_path",
    "file_pattern",
    "output_file",
)

REQUIRED_ENV_VARS = (
    "CLIENT_ID",
    "TENANT_ID",
    "CERTIFICATE_PATH",
    "CERTIFICATE_SECRET",
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
        raise ValueError(
            "Missing required config fields: " + ", ".join(missing)
        )

    return data


def load_sensitive_settings() -> dict[str, str]:
    missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
    if missing:
        raise ValueError(
            "Missing required environment variables: " + ", ".join(missing)
        )

    return {name: os.environ[name] for name in REQUIRED_ENV_VARS}


def run(config: dict[str, Any], secrets: dict[str, str]) -> None:
    """Primary script workflow.

    Replace this implementation with your inventory logic.
    """
    print("Loaded configuration:")
    for key in REQUIRED_CONFIG_FIELDS:
        print(f"- {key}: {config[key]}")

    print("Loaded sensitive settings from environment:")
    for key in REQUIRED_ENV_VARS:
        masked = "***" if key == "CERTIFICATE_SECRET" else secrets[key]
        print(f"- {key}: {masked}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run inventory analysis with a YAML config file."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to YAML config file (e.g., config.yaml)",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    sensitive_settings = load_sensitive_settings()
    run(config, sensitive_settings)
