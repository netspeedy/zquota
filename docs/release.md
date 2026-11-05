# Release and Website Notes

`zquota` uses the same public-release shape as the other maintained repos: validation first, an automated release candidate, which is promoted to stable automatically when it only holds automated updates, GitHub release assets, and a signed APT repository on GitHub Pages.

## Validation

The `Build and Validate` workflow runs on pull requests, pushes to `main`, and manual dispatches. It checks:

- Python formatting with Black
- Ruff linting
- Pylint
- Unit tests
- CLI smoke tests
- Version consistency between `zquota.py`, `pyproject.toml`, and `debian/changelog`
- Python package build
- GitHub Pages website build and validation
- Debian package and signed APT repository layout smoke tests

## Automation Pull Requests

The `Automation Auto Merge` workflow can approve and merge trusted automation
pull requests after `Build and Validate` has passed for the exact current head
commit.

The trusted author list is intentionally narrow: Dependabot and GitHub
automation bot accounts only. Human contributor pull requests are never
auto-approved by this workflow.

## Draft Releases

The `Release Drafter` workflow updates labels, labels pull requests, and maintains a draft release when releasable commits are present.

The release version is based on conventional commit subjects:

| Commit subject | Version bump |
|---|---|
| `feat: ...` | minor |
| `fix: ...`, `perf: ...`, `build: ...`, `deps: ...`, `packaging: ...`, `release: ...` | patch |
| `type!: ...` or `BREAKING CHANGE:` | major |
| docs, CI, tests, and refactors only | no release by default |

Dependabot titles its pip updates `deps:`, since they change what ships, and the
website's npm updates `chore:`, so a docs-site dependency bump doesn't cut a
release.

## Release Candidates

The `Automated Release Candidate` workflow can create `vX.Y.Z-rc.N` tags after validation succeeds on `main`.

Before tagging, it ensures the committed source versions match the stable target, for example `v1.0.0`. If a future release needs a version metadata update, the workflow commits that update first and waits for the next validation pass before tagging.

Release candidate tags publish prerelease assets through the `Release Assets` workflow. RC tags share the same source version as their stable target because the promotion workflow points the stable tag at the same commit.

## Stable Releases

Once a release candidate's assets publish, the same `Automated Release Candidate` run checks who the release is from (`scripts/automated-only.sh`). If every release-bearing commit since the last stable release came from Dependabot, Renovate or this repository's own workflows, it tags that commit as the stable release, for example `v1.0.0-rc.1` becomes `v1.0.0`, and waits for the stable `Release Assets` and `Publish Signed Debian Repository` runs. If any came from a person, it stops at the candidate, and someone runs the `Promote Release Candidate` workflow when it's ready. The stable tag is pushed with `RELEASE_AUTOMATION_TOKEN`, because a tag pushed with `GITHUB_TOKEN` wouldn't start them. `Promote Release Candidate` also finishes a run that failed partway.

Stable tags publish a GitHub release marked as latest and publish the signed APT repository and the docs site to GitHub Pages.

## Assets

The `Release Assets` workflow attaches:

- `zquota-VERSION.tar.gz`, a source archive for the tagged commit
- `zquota_VERSION-1_all.deb`, the Debian package
- Debian source package files
- `sha256sums.txt`

The stable-only `Publish Signed Debian Repository` workflow publishes:

- a `stable main` APT repository
- `zquota-archive-keyring.asc`
- `zquota-archive-keyring.gpg`
- `zquota-archive-keyring.fingerprint.txt`
- the docs site, which shares the Pages root with the repository

The Python package build is validated in CI, but the runtime remains a simple stdlib-only script.

## Website

The site at https://netspeedy.github.io/zquota/ is the zquota documentation,
built with Astro and Starlight from `website/`. The pages are Markdown and MDX
in `website/src/content/docs`. Run it locally with live reload:

```bash
make website-install
make website-dev
```

Build it, validate the output, drive it in a browser, and take desktop and phone
screenshots in both themes:

```bash
make website-build
make website-check
make website-test
make website-capture
```

`website-test` runs `website/scripts/browser-test.mjs` in headless Chrome. It
builds the site twice into `website/.test/`, as an archived line and as the
latest with that line listed, unpacks the archive the way a Pages build would,
and checks the theme controls, the header, each tab's sidebar, the version menu
(including a long list of lines) and the archived notice. It reads the site
root, the tabs and the pages from the build, and exits non-zero if a check
fails.

`website-check` validates `website/dist`, so it runs after the build. Captures
are written to `website/.captures/`; the first one downloads the Chrome build
Puppeteer pins, since installing the site's dependencies never does. Search only
works in a build, because Pagefind indexes the finished pages.

The build always starts with a fresh content cache (`astro build --force`, which
logs "data store cleared"). Astro notices changes to its config, but not edits
to the Markdown plugins in `website/src/lib`, so without it a plugin change
could leave pages rendered by the old code.

The site shares the Pages root with the APT repository. Both Pages workflows
write the stable release's tag and the archive key's fingerprint to a JSON file
before they build, and pass it to the site in `SITE_METADATA_FILE`, so the
published pages name the release and show the key's fingerprint. Publish Signed
Debian Repository takes them from the tag it's publishing and the key it signed
with; Deploy Pages Site takes them from the restored APT snapshot. Local and
pull request builds fall back to the newest local tag and leave the fingerprint
out. The same JSON is published as `website-metadata.json`. Links from the pages
to the APT files are absolute URLs, because those files aren't part of the
build and `website-check` only follows links into it.

`test_cli_reference_covers_every_flag` in `tests/test_docs.py` fails when a flag
is added to or removed from `build_parser()` without updating
`website/src/content/docs/reference/cli.mdx`.

The favicon, Apple touch icon, `favicon.ico`, the mark and the share card in
`website/` come from `make readme-hero`, along with the README banner.
