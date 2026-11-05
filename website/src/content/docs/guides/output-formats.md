---
title: Output formats
description: The default view, the compact view, JSON, JSON Lines and the raw response, what each one shows and when to use it.
---

zquota prints the same quota data five ways. Pick one per run; the format flags can't be combined.

| Format | Flag | For |
| --- | --- | --- |
| Default view | none | reading in a terminal |
| Compact | `--compact`, `-c` | a narrow terminal, a status bar, a quick look |
| JSON | `--json`, `-j` | scripts, dashboards and `jq` |
| JSON Lines | `--jsonl` | logs, and appending one line per window to a file |
| Raw | `--raw` | seeing exactly what Z.ai sent |

Giving two of them, such as `--json --compact`, is a usage error. zquota prints its usage line and
`argument -c/--compact: not allowed with argument -j/--json` to standard error and exits with
code 2, before it makes a request.

All five go to standard output. Errors and warnings go to standard error, so redirecting the output
to a file or a pipe never mixes the two.

## Default view

```bash
zquota
```

A block for each window, with its name, a bar, the percentage used and remaining, the limit, used
and remaining figures, a countdown to the reset and the reset time in your timezone. The
[quickstart](/zquota/quickstart/#check-your-quota) shows a full example, and
[Usage and limits](/zquota/windows/usage/) explains the figures.

## Compact

```bash
zquota --compact
```

```text title="Output"
Plan: pro
  5h-rolling     [██████░░░░]    62%  left:  380.0k  reset: 2h 13m 6s
  weekly         [███░░░░░░░]    31%  left:    5.5M  reset: 4d 6h 11m
```

The plan, then one line per window: its short name, a 10-cell bar, the percentage used, what's
left and the countdown to the reset. It doesn't show the reset time itself, so use the default view
or JSON when you need the exact time.

## JSON

```bash
zquota --json
```

One pretty-printed object with the plan, a `quotas` list with every field zquota has for each
window, and `fetched_at`, when the output was made:

```json title="Output, shortened to the first window"
{
  "plan": "pro",
  "quotas": [
    {
      "name": "5-Hour Rolling Token Quota",
      "name_compact": "5h-rolling",
      "type": "TOKENS_LIMIT",
      "percentage_used": 62.0,
      "percentage_remaining": 38.0,
      "usage_limit": 1000000.0,
      "current_value": 620000.0,
      "remaining_units": 380000.0,
      "resets_in": "2h 13m 5s",
      "resets_at": "2026-11-05 09:25:00 GMT",
      "resets_at_utc": "2026-11-05T09:25:00Z",
      "reset_epoch_ms": 1793870700000,
      "timezone": "Europe/London",
      "details": []
    }
  ],
  "fetched_at": "2026-11-05T07:11:54.582029+00:00"
}
```

[JSON output](/zquota/reference/json-output/) describes every field.

## JSON Lines

```bash
zquota --jsonl
```

One compact JSON object per window, each on its own line, carrying the plan with it:

```json title="Output"
{"plan": "pro", "quota": "5h-rolling", "pct_used": 62.0, "pct_remaining": 38.0, "remaining": 380000.0, "resets_in": "2h 13m 5s", "resets_at": "2026-11-05 09:25:00 GMT", "resets_at_utc": "2026-11-05T09:25:00Z", "reset_epoch_ms": 1793870700000}
{"plan": "pro", "quota": "weekly", "pct_used": 31.0, "pct_remaining": 69.0, "remaining": 5520000.0, "resets_in": "4d 6h 11m", "resets_at": "2026-11-09 13:23:00 GMT", "resets_at_utc": "2026-11-09T13:23:00Z", "reset_epoch_ms": 1794230580000}
```

The field names are shorter than in `--json`, and there are fewer of them: no limit or used
figures, no long name, no timezone, no details and no `fetched_at`. Add a timestamp yourself if
you collect lines over time; [Scripts and alerts](/zquota/guides/scripting/#keeping-a-history)
shows one way.

## Raw

```bash
zquota --raw
```

Z.ai's answer, pretty-printed, as long as it's a JSON object. zquota doesn't check `success`, the
`data` object or the `limits` list first, and doesn't name the windows or convert reset times, so
this is the format to use when the other four fail or look wrong. It can't be combined with
`--threshold`, because there are no parsed percentages to check.

## Colour

The default view and the compact view are coloured when standard output is a terminal, and plain
when it's piped or redirected. `--no-color` makes them plain on a terminal too. The JSON formats
are never coloured. zquota doesn't read the `NO_COLOR` environment variable.
