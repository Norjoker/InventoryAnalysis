from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
from openpyxl.styles import Font
from openpyxl.worksheet.worksheet import Worksheet


def aggregate_inventory_by_sn(file_dates: Sequence[tuple[str | Path, date]]) -> pd.DataFrame:
    """Aggregate inventory rows by serial number (SN) across dated Excel snapshots.

    Each input workbook is read with pandas/openpyxl. Column C's header must be exactly
    ``SN``. For each row where SN is non-empty:
      - on first sighting of an SN, first_seen/last_seen are both set to the file date,
        and A-G values are captured as the first-row values
      - on subsequent sightings, last_seen is updated and A-G values are overwritten as
        the last-row values
    """

    by_sn: dict[str, dict[str, Any]] = {}

    for file_path, snapshot_date in sorted(file_dates, key=lambda item: item[1]):
        workbook_path = Path(file_path)
        frame = pd.read_excel(workbook_path, engine="openpyxl")

        if frame.shape[1] < 3:
            raise ValueError(f"{workbook_path} must contain at least 3 columns (A-C)")

        if frame.columns[2] != "SN":
            raise ValueError(
                f"Column C header must be 'SN' in {workbook_path}, found {frame.columns[2]!r}"
            )

        for _, row in frame.iterrows():
            sn_raw = row.iloc[2]
            if pd.isna(sn_raw):
                continue

            sn = str(sn_raw).strip()
            if not sn:
                continue

            ag_values = tuple(row.iloc[idx] for idx in range(7))

            if sn not in by_sn:
                by_sn[sn] = {
                    "sn": sn,
                    "first_seen": snapshot_date,
                    "last_seen": snapshot_date,
                    "first_col_a": ag_values[0],
                    "first_col_b": ag_values[1],
                    "first_col_c": ag_values[2],
                    "first_col_d": ag_values[3],
                    "first_col_e": ag_values[4],
                    "first_col_f": ag_values[5],
                    "first_col_g": ag_values[6],
                    "last_col_a": ag_values[0],
                    "last_col_b": ag_values[1],
                    "last_col_c": ag_values[2],
                    "last_col_d": ag_values[3],
                    "last_col_e": ag_values[4],
                    "last_col_f": ag_values[5],
                    "last_col_g": ag_values[6],
                }
                continue

            entry = by_sn[sn]
            entry["last_seen"] = snapshot_date
            entry["last_col_a"] = ag_values[0]
            entry["last_col_b"] = ag_values[1]
            entry["last_col_c"] = ag_values[2]
            entry["last_col_d"] = ag_values[3]
            entry["last_col_e"] = ag_values[4]
            entry["last_col_f"] = ag_values[5]
            entry["last_col_g"] = ag_values[6]

    output_columns = [
        "sn",
        "first_seen",
        "last_seen",
        "first_col_a",
        "first_col_b",
        "first_col_c",
        "first_col_d",
        "first_col_e",
        "first_col_f",
        "first_col_g",
        "last_col_a",
        "last_col_b",
        "last_col_c",
        "last_col_d",
        "last_col_e",
        "last_col_f",
        "last_col_g",
    ]

    return pd.DataFrame(by_sn.values(), columns=output_columns).sort_values(
        by="sn", kind="stable"
    ).reset_index(drop=True)


def _format_sheet(
    worksheet: Worksheet,
    *,
    date_columns: Sequence[int],
    header_row: int = 1,
) -> None:
    """Apply lightweight workbook formatting for human-readable output."""
    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions

    for cell in worksheet[header_row]:
        cell.font = Font(bold=True)

    for row_idx in range(header_row + 1, worksheet.max_row + 1):
        for column_idx in date_columns:
            worksheet.cell(row=row_idx, column=column_idx).number_format = "yyyy-mm-dd"


def write_serial_history_workbook(
    file_dates: Sequence[tuple[str | Path, date]],
    output_path: str | Path = "compiled_inventory_serial_history.xlsx",
    include_run_log: bool = True,
) -> Path:
    """Write aggregated inventory serial history to an Excel workbook."""
    output = Path(output_path)
    serial_history = aggregate_inventory_by_sn(file_dates)
    run_log = pd.DataFrame(
        [
            {
                "filename": Path(file_path).name,
                "snapshot_date": snapshot_date,
            }
            for file_path, snapshot_date in sorted(file_dates, key=lambda item: item[1])
        ]
    )

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        serial_history.to_excel(writer, sheet_name="Serial_History", index=False)
        serial_ws = writer.sheets["Serial_History"]
        # first_seen and last_seen columns
        _format_sheet(serial_ws, date_columns=(2, 3))

        if include_run_log:
            run_log.to_excel(writer, sheet_name="Run_Log", index=False)
            run_log_ws = writer.sheets["Run_Log"]
            # snapshot_date column
            _format_sheet(run_log_ws, date_columns=(2,))

    return output
