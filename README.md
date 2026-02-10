# InventoryAnalysis

Pulls dated Excel inventory snapshots from SharePoint (Microsoft Graph), aggregates inventory by serial number (`SN`), and writes an Excel report.

## Setup

1. **Create and activate a virtual environment**
   ```bash
   python -m venv .venv && source .venv/bin/activate
   ```
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure `config.yaml`**
   ```yaml
   site_url: "https://contoso.sharepoint.com/sites/inventory"
   library_name: "Shared Documents"
   folder_path: "/Reports"
   file_pattern: "^(\\d{4}-\\d{2}-\\d{2})_Raw_Data\\.xlsx$"
   output_file: "compiled_inventory_serial_history.xlsx"
   ```
4. **Set environment variables**
   ```bash
   export TENANT_ID="<tenant-id>"
   export CLIENT_ID="<app-client-id>"
   export GRAPH_SCOPES="Files.Read.All Sites.Read.All"
   ```

## Azure app registration notes

- Create an app registration in **Microsoft Entra ID**.
- Enable **Allow public client flows** for device code authentication.
- Add Microsoft Graph delegated permissions:
  - `Files.Read.All`
  - `Sites.Read.All`
- Grant admin consent if required by your tenant.
- Use the app's **Application (client) ID** as `CLIENT_ID` and tenant ID as `TENANT_ID`.

## One-command run example

```bash
TENANT_ID="<tenant-id>" CLIENT_ID="<app-id>" GRAPH_SCOPES="Files.Read.All Sites.Read.All" python main.py --config config.yaml --auth-mode device
```

## Logging and validation behavior

The aggregator now logs:
- number of files discovered,
- number of files successfully processed,
- number of unique SNs,
- output workbook location.

Validation includes:
- required worksheet columns A-G,
- column C header must be exactly `SN`,
- malformed snapshot filenames and unreadable workbooks raise clear errors (or can be skipped when `skip_invalid_files=True`).
