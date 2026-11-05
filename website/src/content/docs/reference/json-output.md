---
title: JSON output
description: Every field in zquota's --json and --jsonl output, with its type and where it comes from, and what --raw prints.
---

`--json` prints one object for the whole run, and `--jsonl` prints one object per window. Both use
the same values; `--jsonl` has fewer fields with shorter names. Numbers from Z.ai are converted to
floating-point, so `62` becomes `62.0`, and any value zquota doesn't have is `null`.

## --json

```json title="zquota --json"
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
    },
    {
      "name": "Weekly Token Quota",
      "name_compact": "weekly",
      "type": "TOKENS_LIMIT",
      "percentage_used": 31.0,
      "percentage_remaining": 69.0,
      "usage_limit": 8000000.0,
      "current_value": 2480000.0,
      "remaining_units": 5520000.0,
      "resets_in": "4d 6h 11m",
      "resets_at": "2026-11-09 13:23:00 GMT",
      "resets_at_utc": "2026-11-09T13:23:00Z",
      "reset_epoch_ms": 1794230580000,
      "timezone": "Europe/London",
      "details": []
    }
  ],
  "fetched_at": "2026-11-05T07:11:54.582029+00:00"
}
```

### Top level

| Field | Type | Meaning |
| --- | --- | --- |
| `plan` | string | The plan's level from Z.ai's `data.level`, or `unknown` if it had none. |
| `quotas` | array | One object per window, in the order Z.ai listed them. |
| `fetched_at` | string | When zquota wrote the output, in UTC, as ISO 8601 with a `+00:00` offset and microseconds. |

`fetched_at` ends in `+00:00`, while `resets_at_utc` ends in `Z`. Both are valid ISO 8601 and parse
the same way.

### Each window

| Field | Type | From | Meaning |
| --- | --- | --- | --- |
| `name` | string | `type`, `unit`, `number` | The long name, such as `5-Hour Rolling Token Quota`. See [Quota windows](/zquota/windows/). |
| `name_compact` | string | `type`, `unit`, `number` | The short name: `5h-rolling`, `weekly`, `tool/search` or `unknown`. |
| `type` | string or null | `type` | Z.ai's window type, as sent. |
| `percentage_used` | number or null | `percentage` | The share of the window used, as sent. |
| `percentage_remaining` | number or null | `percentage` | 100 minus `percentage_used`, kept between 0 and 100. |
| `usage_limit` | number or null | `usage` | The window's limit. |
| `current_value` | number or null | `currentValue` | How much of it you've used. |
| `remaining_units` | number or null | `remaining` | How much is left. |
| `resets_in` | string or null | `nextResetTime` | Countdown to the reset, such as `2h 13m 5s`, or `now`. See [Reset times](/zquota/windows/reset-times/#the-countdown). |
| `resets_at` | string or null | `nextResetTime` | The reset in the chosen timezone, as `YYYY-MM-DD HH:MM:SS ZONE`. |
| `resets_at_utc` | string or null | `nextResetTime` | The reset in UTC, as ISO 8601 ending in `Z`. |
| `reset_epoch_ms` | integer or null | `nextResetTime` | The reset in milliseconds since 1970 UTC, as Z.ai sent it. |
| `timezone` | string | the timezone setting | The timezone `resets_at` is in, such as `Europe/London`. |
| `details` | array | `usageDetails` | Per-model usage as objects with `model` and `usage`, or empty. |

`model` and `usage` in `details` are Z.ai's `modelCode` and `usage`, as sent, with `unknown` in
place of either if it's missing.

## --jsonl

```json title="zquota --jsonl"
{"plan": "pro", "quota": "5h-rolling", "pct_used": 62.0, "pct_remaining": 38.0, "remaining": 380000.0, "resets_in": "2h 13m 5s", "resets_at": "2026-11-05 09:25:00 GMT", "resets_at_utc": "2026-11-05T09:25:00Z", "reset_epoch_ms": 1793870700000}
{"plan": "pro", "quota": "weekly", "pct_used": 31.0, "pct_remaining": 69.0, "remaining": 5520000.0, "resets_in": "4d 6h 11m", "resets_at": "2026-11-09 13:23:00 GMT", "resets_at_utc": "2026-11-09T13:23:00Z", "reset_epoch_ms": 1794230580000}
```

| Field | Same as in `--json` |
| --- | --- |
| `plan` | `plan` |
| `quota` | `name_compact` |
| `pct_used` | `percentage_used` |
| `pct_remaining` | `percentage_remaining` |
| `remaining` | `remaining_units` |
| `resets_in` | `resets_in` |
| `resets_at` | `resets_at` |
| `resets_at_utc` | `resets_at_utc` |
| `reset_epoch_ms` | `reset_epoch_ms` |

JSON Lines leaves out the long name, `type`, the limit and used figures, `timezone`, `details` and
`fetched_at`. If Z.ai returns no windows at all, `--jsonl` prints one empty line.

## --raw

`--raw` prints Z.ai's answer pretty-printed with two-space indentation, exactly as it was parsed,
once zquota knows it's a JSON object. Nothing is renamed, converted or checked, so the fields are
Z.ai's own, such as `nextResetTime` in milliseconds and `percentage` as Z.ai sends it. The fields
zquota reads from it are listed in [Quota windows](/zquota/windows/#what-it-reads-from-each-window).

## Stability

zquota keeps the field names and meanings above stable for scripts. When one has to change, the
change is deliberate and this page says so.
