---
title: Exit codes
description: What zquota's exit codes 0, 1, 2 and 130 mean, and which failures produce each one.
---

| Code | Meaning |
| --- | --- |
| `0` | Success. With `--threshold`, every window is under it. `--version` and `--help` exit with 0 too, as does Ctrl-C while `--watch` is waiting between refreshes. |
| `1` | zquota couldn't get or read the quota, or a flag's value is out of range. |
| `2` | A `--threshold` breach, or a command line zquota couldn't parse. |
| `130` | Ctrl-C while a request was in flight, which ends in a Python traceback. |

## 1: runtime and input errors

Each of these prints `ERROR: <reason>` to standard error:

- no API key in `--api-key` or `ZAI_API_KEY`
- `--watch` below 1, `--threshold` outside 0 to 100, or `--threshold` with `--raw`
- an HTTP error status from Z.ai
- a request that couldn't be made or timed out
- an endpoint that isn't a full URL
- an answer that isn't JSON, isn't a JSON object, has `success` set to false, or has no `data`
  object or `limits` list

With `--watch`, a failed refresh stops the watch with 1. An unknown timezone is only a warning and
doesn't change the exit code.

The few failures zquota doesn't catch, such as a connection that breaks while the answer is being
read, end in a Python traceback, and Python exits with 1 for those too.
[Troubleshooting](/zquota/guides/troubleshooting/) covers each error.

## 2: threshold breach or usage error

With `--threshold PERCENT`, zquota prints the quota first, then exits with 2 if any window's
percentage used is at or above PERCENT. With `--watch`, it stops at the first refresh that breaches.

Python's argument parser also exits with 2 when it can't parse the command line: an unknown or
misspelt flag, two output formats at once, a missing value, or a value of the wrong type such as
`--threshold high`. It prints the usage line and `zquota: error: <reason>` to standard error, and
no request is made. A script that treats 2 as quota pressure can tell the two apart by standard
error, which has no `usage:` line after a breach, or by checking the command by hand before relying
on it.
