# Usage Guide

This guide covers day-to-day use of `zquota`.

## Installation

On Debian and Ubuntu hosts, install from the signed APT repository:

```bash
sudo install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://netspeedy.github.io/zquota/zquota-archive-keyring.gpg \
  | sudo tee /etc/apt/keyrings/zquota-archive-keyring.gpg >/dev/null

sudo tee /etc/apt/sources.list.d/zquota.sources >/dev/null <<'EOF'
Types: deb deb-src
URIs: https://netspeedy.github.io/zquota/
Suites: stable
Components: main
Signed-By: /etc/apt/keyrings/zquota-archive-keyring.gpg
EOF

sudo apt update
sudo apt install zquota
```

The release archive and standalone script are also published from the GitHub releases page.

## Authentication

`zquota` expects a Z.ai API key. The safest normal setup is to keep it in your shell environment:

```bash
export ZQUOTA_API_KEY='your-api-key'
```

You can also pass it directly:

```bash
zquota --api-key 'your-api-key'
```

Passing secrets on the command line can leave them in shell history and process listings, so the environment variable is preferred.

## Timezones

Reset times are displayed in `Europe/London` by default. Override that with:

```bash
zquota --timezone America/New_York
```

or:

```bash
export ZQUOTA_TIMEZONE=America/New_York
zquota
```

Use an IANA timezone name such as `Europe/London`, `UTC`, `America/New_York`, or `Asia/Tokyo`.

## Common Commands

Pretty terminal output:

```bash
zquota
```

Compact terminal output:

```bash
zquota --compact
```

Machine-readable JSON:

```bash
zquota --json
```

JSON Lines:

```bash
zquota --jsonl
```

Raw upstream response:

```bash
zquota --raw
```

Live dashboard:

```bash
zquota --watch 30
```

Threshold alert:

```bash
zquota --threshold 80
```

## JSON Fields

Each quota item contains display-friendly and script-friendly reset fields:

| Field | Description |
|---|---|
| `resets_in` | Compact duration until reset, such as `30m` or `6d 2h 1m` |
| `resets_at` | Local reset time using the selected timezone |
| `resets_at_utc` | UTC reset time in ISO-8601 form |
| `reset_epoch_ms` | Upstream reset time as epoch milliseconds |
| `timezone` | Timezone used for the local display field |

Example:

```bash
zquota --json | jq '.quotas[] | select(.name_compact == "5h-rolling")'
```

## Cron Example

This exits with code `2` when any quota reaches 80 percent. A runtime error still exits with code `1`.

```cron
*/10 * * * * ZQUOTA_API_KEY=your-api-key /usr/local/bin/zquota --threshold 80 >/tmp/zquota.log 2>&1
```

## Troubleshooting

### Missing API key

```text
ERROR: ZQUOTA_API_KEY is not set
```

Set `ZQUOTA_API_KEY` or pass `--api-key`.

### Unknown timezone

If an invalid timezone is supplied, `zquota` prints a warning and falls back to `Europe/London`.

### HTTP errors

`zquota` prints the HTTP status, reason, and response body when the server provides one. Check that the API key is valid and that the quota endpoint has not changed.

### Invalid JSON or response shape

Use `--raw` to inspect the upstream response:

```bash
zquota --raw
```
