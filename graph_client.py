from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import requests

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
SNAPSHOT_FILENAME_REGEX = r"^(\d{4}-\d{2}-\d{2})_Raw_Data\.xlsx$"


@dataclass(frozen=True)
class SnapshotFile:
    """Represents a dated inventory snapshot file in SharePoint."""

    name: str
    snapshot_date: date
    web_url: str
    drive_item_id: str


class GraphClient:
    """Lightweight Microsoft Graph client for SharePoint drive operations."""

    def __init__(self, access_token: str, base_url: str = GRAPH_BASE_URL, timeout_s: int = 30) -> None:
        if not access_token:
            raise ValueError("access_token is required")
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            }
        )

    def _get(self, path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = self.session.get(url, params=params, timeout=self.timeout_s)
        response.raise_for_status()
        return response.json()

    def resolve_site_id(self, site_url: str) -> str:
        """Resolve a full SharePoint site URL to a Microsoft Graph site id."""
        cleaned = site_url.replace("https://", "").replace("http://", "")
        host, _, site_path = cleaned.partition("/")
        if not host or not site_path:
            raise ValueError(f"Invalid site URL: {site_url}")

        payload = self._get(f"sites/{host}:/{site_path}")
        site_id = payload.get("id")
        if not site_id:
            raise RuntimeError(f"Unable to resolve site id from URL: {site_url}")
        return site_id

    def resolve_drive_id(self, site_id: str, library_name: str) -> str:
        """Resolve a document library display name to a drive id."""
        payload = self._get(f"sites/{site_id}/drives")
        for drive in payload.get("value", []):
            if drive.get("name") == library_name:
                drive_id = drive.get("id")
                if drive_id:
                    return drive_id
        raise RuntimeError(f"Drive '{library_name}' not found for site '{site_id}'")

    def list_folder_files(self, drive_id: str, folder_path: str) -> list[dict[str, Any]]:
        """List files under a folder path in a SharePoint document library."""
        normalized_path = folder_path.strip("/")
        payload = self._get(f"drives/{drive_id}/root:/{normalized_path}:/children")
        return [item for item in payload.get("value", []) if "file" in item]

    def list_snapshot_files(
        self,
        site_url: str,
        library_name: str,
        folder_path: str,
        filename_pattern: str = SNAPSHOT_FILENAME_REGEX,
    ) -> list[SnapshotFile]:
        """List and sort dated snapshot files in ascending chronological order."""
        site_id = self.resolve_site_id(site_url)
        drive_id = self.resolve_drive_id(site_id=site_id, library_name=library_name)
        files = self.list_folder_files(drive_id=drive_id, folder_path=folder_path)

        matcher = re.compile(filename_pattern)
        snapshots: list[SnapshotFile] = []

        for item in files:
            name = item.get("name", "")
            match = matcher.match(name)
            if not match:
                continue

            date_string = match.group(1)
            parsed_date = datetime.strptime(date_string, "%Y-%m-%d").date()
            snapshots.append(
                SnapshotFile(
                    name=name,
                    snapshot_date=parsed_date,
                    web_url=item.get("webUrl", ""),
                    drive_item_id=item.get("id", ""),
                )
            )

        snapshots.sort(key=lambda snapshot: snapshot.snapshot_date)
        return snapshots
