---
title: Watching live
description: Keeping the quota view on screen with --watch, how often it refreshes, and the three things that stop it.
---

`--watch` keeps zquota running and refreshes the view on a timer, which is handy in a spare
terminal pane while you work:

```bash
zquota --watch 30
```

Each refresh clears the screen, prints a header and then the view:

```text
  zquota - refreshing every 30s  (Ctrl-C to stop)


  Z.ai plan: pro
  ...
```

The interval is a whole number of seconds, 1 or more. `--watch 0` stops with
`ERROR: --watch interval must be >= 1 second` and exit code 1, and a value that isn't a whole
number, such as `--watch 2.5`, is a usage error with exit code 2. `-w 30` is the short form.

## How often it asks

zquota waits the interval after printing, then asks again, so each cycle takes the interval plus
however long the request takes. Every refresh is one request to Z.ai. The screen is cleared before
the request, so it stays blank until the answer arrives, for up to the 20-second request timeout
if Z.ai is slow.

## What stops it

| What happens | What zquota does | Exit code |
| --- | --- | --- |
| You press Ctrl-C while it's waiting | prints a newline and stops | 0 |
| A request fails | prints the error to standard error and stops | 1 |
| `--threshold` is set and a window reaches it | leaves that view on screen and stops | 2 |

A failed refresh ends the watch rather than retrying, so a short network outage stops it and
you'll need to start it again.

Ctrl-C while a request is in flight isn't handled: Python prints a traceback and the exit code is
130.

## Watching until a threshold

With `--threshold`, `--watch` keeps refreshing until a window reaches the percentage you set, then
stops with exit code 2 and leaves the view showing it. That makes it a simple alarm:

```bash
zquota --watch 300 --threshold 90 --compact
echo "zquota stopped with exit code $?"
```

Exit code 1 means it stopped because a request failed, not because of the threshold.

## Formats

`--watch` works with every format, but it always writes the screen-clearing escape codes and the
header, whatever the format and wherever the output goes. Use it to watch, not to log: for a log,
run zquota with `--jsonl` from a timer instead, as in
[Scripts and alerts](/zquota/guides/scripting/#keeping-a-history).
