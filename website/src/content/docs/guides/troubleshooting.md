---
title: Troubleshooting
description: What each zquota error and warning means and what to do about it, from a missing key to a response it can't read.
---

zquota prints errors to standard error as `ERROR: <reason>` and exits with code 1, apart from usage
errors, which exit with 2. When the answer from Z.ai looks wrong rather than failing outright, run
`zquota --raw` to see exactly what came back.

## ZAI_API_KEY is not set

```text
ERROR: ZAI_API_KEY is not set
Set it with: export ZAI_API_KEY='your-api-key'
```

zquota found no key in `--api-key` or `ZAI_API_KEY`, so it didn't make a request. Export the
variable in the shell you're running from, or in the job's environment for cron and timers, which
don't read your shell profile. An empty `--api-key ''` counts as no key.
[Configuration](/zquota/guides/configuration/#the-api-key) has ways to keep the key out of your
history.

## HTTP errors

```text
ERROR: HTTP 401: Unauthorized
```

Z.ai answered with an error status. zquota prints the status, its reason and then the body of the
response on the following lines, if there was one and it arrived, because Z.ai's explanation is
usually in the body. A 401 or 403 usually means the key is wrong, has been revoked or can't read the quota
endpoint. A 404 means the endpoint address is wrong, so check `ZAI_API_URL` and `--api-url`.

## The request failed

```text
ERROR: request failed: [Errno 8] nodename nor servname provided, or not known
```

zquota didn't get a whole answer. The reason after the colon usually comes from the system, and
varies between operating systems: a name that doesn't resolve, a refused or reset connection, a
certificate problem, or `timed out` when Z.ai went quiet for 20 seconds, before answering or
part-way through. Two reasons come from zquota itself:

| Reason | What it means |
| --- | --- |
| `the response broke off after N bytes` | The connection closed before the whole answer arrived. |
| `invalid HTTP response: ...` | Whatever answered doesn't speak HTTP, often a wrong port in the endpoint or a proxy problem. |

Check your network, any proxy in the way, and the endpoint address if you've changed it.

## Errors about the response

| Error | What it means |
| --- | --- |
| `ERROR: response was not valid JSON: ...` | The answer wasn't JSON, often an HTML error page from a proxy or a wrong endpoint. |
| `ERROR: API response was JSON, but not a JSON object` | The answer was JSON but not an object, such as a list. |
| `ERROR: <message from Z.ai>` | The answer had `success` set to false, and this is its `msg`. Without a `msg`, it reads `API returned success=false`. |
| `ERROR: API response does not contain a valid data object` | There's no `data` object in the answer. |
| `ERROR: API response does not contain a valid limits list` | There's a `data` object, but no `limits` list in it. |

`zquota --raw` shows the answer as long as it's a JSON object, which is what to look at, or to
attach to an issue with your key and anything private removed. If Z.ai has changed the shape of the
answer, zquota will need changing too.

## unknown url type

```text
ERROR: unknown url type: 'api.z.ai/api/monitor/usage/quota/limit'
```

`--api-url` or `ZAI_API_URL` isn't a full URL. It needs its scheme, `https://` (or `file://` for a
saved response). `ERROR: unknown url type: ''` means `ZAI_API_URL` is set but empty; an empty
variable still replaces the default endpoint, so unset it with `unset ZAI_API_URL`.

## Unknown timezone

```text
WARNING: unknown timezone 'Mars/Olympus'; using Europe/London
```

The name you gave in `--timezone` or `ZAI_TIMEZONE` isn't in the tz database, so reset times are
shown in `Europe/London`. This is a warning: the exit code isn't affected. Use a name like
`America/New_York` or `UTC`, not a file path such as `/etc/localtime`, which gets the same warning.
An empty `ZAI_TIMEZONE` counts as unset and gets no warning.

## Usage errors

```text
usage: zquota [-h] [--version] [-j | --jsonl | --raw | -c] [--no-color]
              [--timezone TIMEZONE] [--api-key API_KEY] [--api-url API_URL]
              [--watch SECONDS] [--threshold PERCENT]
zquota: error: argument --jsonl: not allowed with argument -c/--compact
```

The command line didn't parse: an unknown or misspelt flag, two output formats at once, or a value
of the wrong type, such as `--watch soon`. zquota exits with code 2 and makes no request. That's the
same code a `--threshold` breach uses, so a script that checks for 2 should be tested by hand first.

`--watch` and `--threshold` values that parse but are out of range get their own errors and exit
with 1:

```text
ERROR: --watch interval must be >= 1 second
ERROR: --threshold must be between 0 and 100
ERROR: --threshold cannot be used with --raw
```

## Garbled bars or a UnicodeEncodeError

The views use Unicode block and box-drawing characters. If the bars show as question marks or
boxes, your terminal font doesn't have them; pick another font or use `--json`. If zquota stops with
`UnicodeEncodeError`, its output encoding isn't UTF-8: set a UTF-8 locale, such as
`LANG=C.UTF-8`, or `PYTHONIOENCODING=utf-8` for that run.

## Other tracebacks

zquota turns the failures it expects into `ERROR:` lines, so a Python traceback means something it
didn't expect. Run it again, and if the same traceback keeps coming back,
[open an issue](https://github.com/netspeedy/zquota/issues) with it.
