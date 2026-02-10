import unittest
from datetime import date

from graph_client import GraphClient


class TestGraphClientSnapshotFiltering(unittest.TestCase):
    def test_filters_by_regex_and_sorts_by_captured_date(self) -> None:
        client = GraphClient(access_token="token")

        client.resolve_site_id = lambda site_url: "site-id"  # type: ignore[method-assign]
        client.resolve_drive_id = lambda site_id, library_name: "drive-id"  # type: ignore[method-assign]
        client.list_folder_files = lambda drive_id, folder_path: [  # type: ignore[method-assign]
            {"name": "2024-03-20_Raw_Data.xlsx", "id": "3", "webUrl": "u3", "file": {}},
            {"name": "notes.txt", "id": "x", "webUrl": "ux", "file": {}},
            {"name": "2024-01-15_Raw_Data.xlsx", "id": "1", "webUrl": "u1", "file": {}},
            {"name": "2024-02-10_Raw_Data.xlsx", "id": "2", "webUrl": "u2", "file": {}},
        ]

        snapshots = client.list_snapshot_files(
            site_url="https://contoso.sharepoint.com/sites/inventory",
            library_name="Shared Documents",
            folder_path="/Reports",
            filename_pattern=r"^(\d{4}-\d{2}-\d{2})_Raw_Data\.xlsx$",
        )

        self.assertEqual([s.name for s in snapshots], [
            "2024-01-15_Raw_Data.xlsx",
            "2024-02-10_Raw_Data.xlsx",
            "2024-03-20_Raw_Data.xlsx",
        ])
        self.assertEqual([s.snapshot_date for s in snapshots], [
            date(2024, 1, 15),
            date(2024, 2, 10),
            date(2024, 3, 20),
        ])


if __name__ == "__main__":
    unittest.main()
