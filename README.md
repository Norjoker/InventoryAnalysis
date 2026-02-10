# InventoryAnalysis

## Usage

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create/update `config.yaml` with non-sensitive settings:

```yaml
site_url: "https://contoso.sharepoint.com/sites/inventory"
library_name: "Shared Documents"
folder_path: "/Reports"
file_pattern: "*.csv"
output_file: "inventory_summary.csv"
```

3. Set sensitive values through environment variables (never hard-code in config):

```bash
export CLIENT_ID="your-client-id"
export TENANT_ID="your-tenant-id"
export CERTIFICATE_PATH="/path/to/certificate.pfx"
export CERTIFICATE_SECRET="your-certificate-secret"
```

4. Run the script with a short command:

```bash
python main.py --config config.yaml
```
