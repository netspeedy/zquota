---
title: Scripts and alerts
description: Using --threshold and the exit codes in scripts and cron, reading zquota's JSON with jq, keeping a history, and testing against a saved response.
---

zquota is built to be called from scripts. The JSON formats give you every value, and the exit code
says whether a window is over the line you set or whether zquota couldn't get an answer at all.

## The exit codes to check

| Code | Meaning |
| --- | --- |
| `0` | It printed the quota, and no window has reached `--threshold` (or you didn't set one). |
| `1` | It couldn't get or read the quota: no API key, a request that failed, an error from Z.ai, a response it couldn't parse, or an invalid `--watch` or `--threshold` value. |
| `2` | `--threshold` is set and at least one window is at or above it. |

Quota pressure has its own code so a script can treat it differently from a broken key or a
network failure. One catch: a command line zquota can't parse, such as a misspelt flag or
`--json --compact`, also exits with 2, because that's what Python's argument parser does. It prints
`usage:` and the problem to standard error and makes no request. Run your command by hand once
before you rely on the 2. [Exit codes](/zquota/reference/exit-codes/) has the full list.

## A threshold check

`--threshold` takes a percentage from 0 to 100. zquota prints the quota in whichever format you
chose, then exits with 2 if any window's `percentage_used` is at or above it. Windows without a
percentage are skipped.

This script prints nothing while every window is under 80%, so it's quiet in cron until there's
something to say:

```sh title="zquota-check"
#!/bin/sh
# Print the quota only when a Z.ai window is at 80% or more, or when the check fails.
out=$(zquota --compact --threshold 80 2>&1)
code=$?
case $code in
  0) ;;
  2) printf 'Z.ai quota is at or over 80%%:\n%s\n' "$out" ;;
  *) printf 'zquota failed (exit %s):\n%s\n' "$code" "$out" ;;
esac
```

`--threshold` can't be combined with `--raw`; zquota stops with
`ERROR: --threshold cannot be used with --raw` and exit code 1.

## Running it from cron

cron runs jobs with a short `PATH` and none of your shell's environment, so tell it where zquota
is and load the API key yourself. `command -v zquota` prints its path: `/usr/bin/zquota` for the
Debian package, and a path under Homebrew's `bin`, such as `/opt/homebrew/bin/zquota`, for
Homebrew.

With the key in a file only you can read, as in
[Configuration](/zquota/guides/configuration/#the-api-key), these crontab lines run the check every
ten minutes, and cron mails you whatever it prints:

```text title="crontab -e"
PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin
*/10 * * * * . "$HOME/.config/zquota.env" && "$HOME/bin/zquota-check"
```

Putting `ZAI_API_KEY=...` in the crontab itself works too, but leaves the key in a file that
`crontab -l` shows.

## Reading JSON with jq

`--json` has every field for every window. Pick out one window by its short name:

```bash
zquota --json | jq -r '.quotas[] | select(.name_compact == "5h-rolling") | .resets_at_utc'
```

```text title="Output"
2026-11-05T09:25:00Z
```

Or summarise them all:

```bash
zquota --json | jq -r '.quotas[] | "\(.name_compact): \(.percentage_used)% used, resets \(.resets_at)"'
```

```text title="Output"
5h-rolling: 62.0% used, resets 2026-11-05 09:25:00 GMT
weekly: 31.0% used, resets 2026-11-09 13:23:00 GMT
```

Percentages and figures are floating-point numbers, so `62` comes through as `62.0`. For anything
that compares or schedules, use `resets_at_utc` or `reset_epoch_ms` rather than `resets_at`, which
depends on the timezone, or `resets_in`, which changes every second.
[JSON output](/zquota/reference/json-output/) lists every field.

## Keeping a history

zquota doesn't store anything between runs, and `--jsonl` lines don't say when they were made, so
add a timestamp as you collect them. This appends one line per window:

```bash
zquota --jsonl \
  | jq -c --arg t "$(date -u +%Y-%m-%dT%H:%M:%SZ)" '{checked_at: $t, quota, pct_used, resets_at_utc}' \
  >> ~/zquota-history.jsonl
```

```json title="~/zquota-history.jsonl"
{"checked_at":"2026-11-05T07:22:54Z","quota":"5h-rolling","pct_used":62.0,"resets_at_utc":"2026-11-05T09:25:00Z"}
{"checked_at":"2026-11-05T07:22:54Z","quota":"weekly","pct_used":31.0,"resets_at_utc":"2026-11-09T13:23:00Z"}
```

Run it from cron or a systemd timer. Don't use `--watch` for this: it writes screen-clearing codes
and a header into the output.

## Testing against a saved response

To try a script without waiting for real usage to cross your threshold, save a response with
`--raw`, edit the percentages, and point zquota at the file with a `file://` address:

```bash
zquota --raw > response.json
ZAI_API_KEY=test zquota --api-url "file://$PWD/response.json" --compact --threshold 80
```

zquota reads the file instead of calling Z.ai. It still insists on an API key, but doesn't send it
anywhere for a `file://` address. The countdown is worked out from the current time, so it shrinks
as the saved reset times get closer, and reads `now` once they've passed.
