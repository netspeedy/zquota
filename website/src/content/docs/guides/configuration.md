---
title: Configuration
description: Setting the Z.ai API key, the display timezone and the quota endpoint with environment variables or flags, and which one wins.
---

zquota has no config file. It reads three settings, each from a flag or an environment variable,
and the flag wins when both are set:

| Setting | Flag | Environment variable | Default |
| --- | --- | --- | --- |
| API key | `--api-key` | `ZAI_API_KEY` | none, so one of them is required |
| Timezone | `--timezone`, `-z` | `ZAI_TIMEZONE` | `Europe/London` |
| Endpoint | `--api-url` | `ZAI_API_URL` | `https://api.z.ai/api/monitor/usage/quota/limit` |

Everything else is chosen per run with flags, listed in the [CLI reference](/zquota/reference/cli/).

## The API key

zquota sends the key to Z.ai as a bearer token. Keep it in the environment:

```bash
export ZAI_API_KEY='your-api-key'
```

Put that line in your shell's profile, such as `~/.zshrc` or `~/.bashrc`, to have it in every new
terminal. If you'd rather not keep the key in a profile that's backed up or shared, write the same
line into a file of its own with an editor, so the key doesn't pass through your shell history:

```bash title="~/.config/zquota.env"
export ZAI_API_KEY='your-api-key'
```

Then make it readable only by you, and load it from your profile:

```bash
chmod 600 ~/.config/zquota.env
. ~/.config/zquota.env
```

`--api-key` works too, but a key on the command line ends up in your shell history and is visible
to other users in the process list while zquota runs. Use it for a one-off check with a different
key, not as a habit.

An empty `--api-key ''` counts as not given, so zquota falls back to `ZAI_API_KEY`. With neither,
it stops before making a request:

```text
ERROR: ZAI_API_KEY is not set
Set it with: export ZAI_API_KEY='your-api-key'
```

and exits with code 1.

## The timezone

Reset times are shown in `Europe/London` unless you set an IANA timezone name:

```bash
zquota --timezone America/New_York
export ZAI_TIMEZONE=America/New_York
```

An unrecognised name gets a warning and falls back to `Europe/London`.
[Reset times](/zquota/windows/reset-times/#choosing-the-timezone) has the details, including what
the timezone does and doesn't change.

## The endpoint

`ZAI_API_URL` and `--api-url` replace the quota endpoint. You won't need them to use Z.ai; they're
for testing, or for a proxy that sits in front of the API. zquota sends the same request with your
key to whatever address you give, so only point it at endpoints you trust.

The address can also be a `file://` URL. zquota then reads a saved response from disk instead of
asking Z.ai, which is handy for testing a script against a known answer:

```bash
zquota --raw > response.json
zquota --api-url "file://$PWD/response.json" --compact
```

zquota still needs a key for a `file://` address, though it doesn't send it anywhere, so set any
value if `ZAI_API_KEY` isn't set. [Scripts and alerts](/zquota/guides/scripting/#testing-against-a-saved-response)
uses this to test a threshold check.

## Settings that apply to one run

Colour, the output format, `--watch` and `--threshold` have no environment variables. Set them on
each run, or wrap zquota in a shell alias or function if you always want the same ones:

```bash
alias zq='zquota --compact --timezone UTC'
```
