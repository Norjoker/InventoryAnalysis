# InventoryAnalysis

This project now uses an `msal`-based auth module with two paths:

1. **Primary:** Device code flow (interactive sign-in, token cached locally).
2. **Optional:** Confidential client with certificate (for unattended/scheduled jobs).

## Usage

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Create/update `config.yaml` with non-sensitive settings

```yaml
site_url: "https://contoso.sharepoint.com/sites/inventory"
library_name: "Shared Documents"
folder_path: "/Reports"
file_pattern: "*.csv"
output_file: "inventory_summary.csv"
```

### 3. Configure environment variables

#### Device code flow (default / recommended)

```bash
export CLIENT_ID="your-public-client-app-id"
export TENANT_ID="your-tenant-id"
# Optional: delegated scopes (space-separated)
export GRAPH_SCOPES="Files.Read.All Sites.Read.All"
# Optional: location for the token cache file
export MSAL_CACHE_PATH=".msal_token_cache.json"
```

#### Confidential client flow (optional, scheduled jobs)

```bash
export CLIENT_ID="your-confidential-client-app-id"
export TENANT_ID="your-tenant-id"
export CERT_PRIVATE_KEY_PATH="/secure/path/private_key.pem"
export CERT_PUBLIC_PATH="/secure/path/public_cert.pem"
export CERT_THUMBPRINT="certificate_thumbprint_without_spaces"
# Optional: passphrase if your private key is encrypted
export CERT_PASSPHRASE="private-key-passphrase"
# Optional: app scope (defaults to Graph .default)
export GRAPH_APP_SCOPE="https://graph.microsoft.com/.default"
# Optional: location for the token cache file
export MSAL_CACHE_PATH=".msal_token_cache.json"
```

### 4. Run

**Device code flow (default):**

```bash
python main.py --config config.yaml
```

**Confidential client flow:**

```bash
python main.py --config config.yaml --auth-mode confidential
```

## Token caching behavior

The auth module uses `msal.SerializableTokenCache` and persists it to `MSAL_CACHE_PATH` (default: `.msal_token_cache.json`).

- On first run with device flow, you'll be prompted to authenticate via the shown verification URL/code.
- On subsequent runs, the script attempts `acquire_token_silent(...)` first.
- If refresh is possible, no interactive prompt appears.

> Treat the cache file as sensitive because it can contain refresh token state.

## Azure app registration requirements

You can use one app registration for both flows, or separate registrations per flow.

### Minimum Microsoft Graph permissions

For read-only access to files and sites:

- **Delegated (device flow):**
  - `Files.Read.All`
  - `Sites.Read.All`
- **Application (confidential flow):**
  - `Files.Read.All`
  - `Sites.Read.All`

If you only need a narrower surface area, you may use more restrictive permissions where possible.

## Consent/setup steps

1. Go to **Azure Portal → Microsoft Entra ID → App registrations → Your App**.
2. Under **Authentication**:
   - For device flow, enable **Allow public client flows** (`Yes`).
3. Under **API permissions**:
   - Add Microsoft Graph permissions listed above.
   - Click **Grant admin consent** (required for `*.Read.All` in many tenants).
4. (Confidential flow only) Under **Certificates & secrets**:
   - Upload your public certificate (`.cer`),
   - Keep your private key (`.pem`) securely outside source control.
5. Note your **Application (client) ID** and **Directory (tenant) ID**.

## Security notes

- Do not commit certificate private keys, passphrases, or token cache files.
- Prefer storing secrets in a secret manager (Key Vault, CI secret store, etc.).
- Use separate app registrations and least privilege for automation vs. interactive usage.
