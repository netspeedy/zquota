---
title: Reset times
description: Where zquota's reset time comes from, the countdown, the local time, UTC and epoch milliseconds, and how the timezone is chosen.
---

Each window in Z.ai's answer carries `nextResetTime`, the moment it next resets, in milliseconds
since 1970 UTC. zquota doesn't work the time out itself. It takes that value and shows it as a
countdown and as a time you can plan around, in your timezone.

## The four forms

The JSON output carries the reset time four ways, and the other views pick from them:

| Form | JSON field | Example | Shown in |
| --- | --- | --- | --- |
| Countdown | `resets_in` | `2h 13m 6s` | default view (`Resets in`), compact view (`reset:`), JSON, JSON Lines |
| Local time | `resets_at` | `2026-11-05 09:25:00 GMT` | default view (`Resets at`), JSON, JSON Lines |
| UTC | `resets_at_utc` | `2026-11-05T09:25:00Z` | JSON, JSON Lines |
| Epoch milliseconds | `reset_epoch_ms` | `1793870700000` | JSON, JSON Lines |

`reset_epoch_ms` is Z.ai's value as an integer, and `resets_at_utc` is the same moment in ISO 8601
with a `Z`. If Z.ai's value has a fraction of a second, `resets_at_utc` keeps it, as in
`2026-11-05T09:25:00.123000Z`, while `resets_at` drops it.

For scripts, use `resets_at_utc` or `reset_epoch_ms`. They're the same whatever timezone zquota is
using, and the countdown changes every second.

## The countdown

`resets_in` is the time from when zquota got its answer to the reset, rounded down to whole
seconds. It shows the three largest units that aren't zero, out of days, hours, minutes and
seconds:

| Seconds to the reset | `resets_in` |
| --- | --- |
| 8,007 | `2h 13m 27s` |
| 90,061 | `1d 1h 1m` (the second is past the third unit, so it's dropped) |
| 3,605 | `1h 5s` (zero minutes are skipped) |
| 59 | `59s` |
| 0 or less | `now` |

`now` means the reset time Z.ai sent has already passed, or is this second. The next request
should bring the window's new reset time.

## The local time

`resets_at` is the reset time converted to your timezone, as `YYYY-MM-DD HH:MM:SS` and the zone's
abbreviation from the tz database: `GMT` or `BST` for `Europe/London`, `EST` or `EDT` for
`America/New_York`, `JST` for `Asia/Tokyo`, `UTC` for `UTC`.

The conversion uses the offset in force at the reset, not the one in force now, so a window that
resets after the clocks change shows the new abbreviation. A window that resets at 12:00 UTC on
28 March 2027, the day after London's clocks go forward, shows as `2027-03-28 13:00:00 BST`.

## Choosing the timezone

zquota uses the first of these that's set and not empty:

1. `--timezone` or `-z`
2. the `ZAI_TIMEZONE` environment variable
3. `Europe/London`

Give an IANA timezone name, such as `Europe/London`, `America/New_York`, `Asia/Tokyo` or `UTC`:

```bash
zquota --timezone Asia/Tokyo
export ZAI_TIMEZONE=UTC
```

The timezone only changes `resets_at` and the JSON `timezone` field. `resets_in`, `resets_at_utc`
and `reset_epoch_ms` come out the same in every timezone.

If zquota doesn't recognise the name, it warns on standard error and carries on in
`Europe/London`, with exit code 0 if nothing else goes wrong:

```text
WARNING: unknown timezone 'Mars/Olympus'; using Europe/London
```

Check the name against the tz database's, which pair a region with a city, such as
`Europe/Paris` or `America/Los_Angeles`. With `--watch`, the warning is printed once, on the first
refresh, so it's on screen until the second one clears it.

## Windows without a reset time

If a window has no `nextResetTime`, or it isn't a number that makes a date, zquota leaves the
`Resets in` and `Resets at` lines out of the default view, shows `reset: -` in the compact view,
and sets all four fields to `null` in JSON.
