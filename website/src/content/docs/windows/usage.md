---
title: Usage and limits
description: How zquota draws the usage bar and colours it, how it rounds the limit, used and remaining figures, and the per-model details.
---

Every window Z.ai reports has a percentage used and, usually, three figures behind it: the
window's limit, what you've used and what's left. zquota prints them as Z.ai sends them, rounded
for reading in the terminal views and exact in JSON.

## Percentages

`percentage_used` is Z.ai's `percentage` as it arrives. `percentage_remaining` is 100 minus that,
kept between 0 and 100. The default view prints both without trailing zeros, so `62` rather than
`62.0`, and `62.5` when Z.ai sends a fraction:

```text
  │  [██████████████░░░░░░░░░░] 62% used
  │  Remaining: 38%
```

`--threshold` compares against `percentage_used`, so a window counts as over the line once its
percentage is at or above the number you give.

## The bar

The bar is 24 cells wide in the default view and 10 in the compact view. zquota fills the share of
cells that matches the percentage, rounded down and kept between empty and full, so 62% fills 14 of
24 cells (6 of 10 in the compact view) and only 100% or more fills them all.

On a terminal it colours the bar, and in the default view the percentage beside it, by how much
you've used:

| Used | Colour |
| --- | --- |
| below 70% | green |
| 70% to below 90% | yellow |
| 90% and above | red |

The colours are fixed; `--threshold` doesn't move them. zquota only colours output when standard
output is a terminal, so piped or redirected output is always plain, and `--no-color` turns colour
off on a terminal too.

## Limit, used and remaining

The default view shows three figures for each window:

| Line | Response field | JSON field |
| --- | --- | --- |
| `Limit` | `usage` | `usage_limit` |
| `Used` | `currentValue` | `current_value` |
| `Remaining` | `remaining` | `remaining_units` |

The compact view shows only what's left, after `left:`. Both views round large figures to one
decimal place: a million and over is shown in millions, a thousand and over in thousands, and
anything smaller as it is.

| Value | Shown as |
| --- | --- |
| 2,480,000 | `2.5M` |
| 620,000 | `620.0k` |
| 1,234.5 | `1.2k` |
| 999,999 | `1000.0k` |
| 12 | `12` |

zquota doesn't add units. For the token windows the figures are tokens; for the tool and search
window they're whatever Z.ai counts. JSON has the exact values, as floating-point numbers such as
`620000.0`.

## Per-model details

When a window has `usageDetails`, the default view lists each entry under `Details`, with the
model code and its usage as Z.ai sent them:

```text
  │  Resets at:   2026-11-05 09:25:00 GMT
  │  Details:
  │    • glm-4.5: 1234
  ──────────────────────────────────
```

The same entries are in the JSON `details` list as `model` and `usage`, with `unknown` standing in
for either one when it's missing. The compact view and JSON Lines leave details out.

## Missing figures

Any figure Z.ai leaves out, or sends as something other than a number, is left out of the default
view, shown as `-` in the compact view and `null` in JSON. A window without a percentage has no bar
or `Remaining` percentage, and `--threshold` skips it.
