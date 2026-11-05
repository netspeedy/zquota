---
title: Environment variables
description: The three environment variables zquota reads, their defaults, and how the matching flags override them.
---

zquota reads three environment variables. Each has a flag that overrides it for one run.

| Variable | Flag | Default | What it sets |
| --- | --- | --- | --- |
| `ZAI_API_KEY` | `--api-key` | none | The API key, sent to Z.ai as a bearer token. Required unless `--api-key` is given. |
| `ZAI_TIMEZONE` | `--timezone`, `-z` | `Europe/London` | The IANA timezone for `Resets at` and `resets_at`. |
| `ZAI_API_URL` | `--api-url` | `https://api.z.ai/api/monitor/usage/quota/limit` | The quota endpoint. |

## ZAI_API_KEY

The key zquota sends in the `Authorization: Bearer` header. zquota checks for it after checking the
flags and before making a request; with neither the variable nor `--api-key`, it prints
`ERROR: ZAI_API_KEY is not set` and exits with code 1. An empty `--api-key ''` doesn't override
the variable.

## ZAI_TIMEZONE

An IANA timezone name such as `America/New_York`, `Asia/Tokyo` or `UTC`. `--timezone` overrides it.
A name zquota doesn't recognise, including one shaped like a file path such as `/etc/localtime`,
gets `WARNING: unknown timezone '<name>'; using Europe/London` on standard error, and the run carries
on in `Europe/London`. An empty value counts as unset, so zquota uses `Europe/London` without a
warning.

## ZAI_API_URL

Replaces the quota endpoint, for testing or a proxy. `--api-url` overrides it. When the variable is
set, zquota uses its value even if it's empty, and an empty value fails with
`ERROR: unknown url type: ''`. A `file://` URL reads a saved response from disk; see
[Configuration](/zquota/guides/configuration/#the-endpoint).

## What zquota doesn't read

zquota has no variables for the output format, colour, `--watch` or `--threshold`, and it doesn't
read `NO_COLOR`. It also has no config file. Colour is decided by whether standard output is a
terminal and by `--no-color`.
