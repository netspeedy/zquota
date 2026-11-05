# Repository Guidelines

## Project Structure & Module Organization

`zquota` is a small Python CLI for displaying Z.ai quota usage and exact reset
windows.

- Keep the runtime CLI in `zquota.py`.
- Keep unit tests in `tests/` and prefer stdlib `unittest` unless the project
  deliberately adopts another test runner.
- Keep user-facing docs in the docs site (`website/`) and `README.md`. The files
  in `docs/` other than `release.md` are pointers kept so old links still land
  somewhere; don't add guides there.
- Keep Debian packaging metadata in `debian/`.
- Keep release helper scripts in `scripts/`.
- Keep the README hero generator in `scripts/readme/`. `make readme-hero` generates
  `assets/zquota-readme-hero.svg`, the social cards (`website/public/og-image.*`
  and `assets/zquota-social-card.png`) and the docs site's mark and icons
  (`website/src/assets/mark.svg`, and `favicon.svg`, `favicon.ico` and
  `apple-touch-icon.png` in `website/public`); edit the script, not the generated
  files. `netspeedy/homebrew-zquota` carries a copy of the script and the same
  SVG, so copy generator changes across.
- Keep GitHub Actions, labels, Dependabot, and release-drafter metadata under
  `.github/`.
- Treat `website/` as a first-party release surface, not a throwaway demo. It
  is the zquota documentation, built with Astro and Starlight, and the front of
  the signed APT repository, which shares its Pages root. The pages are Markdown
  and MDX in `website/src/content/docs`.
- Each sidebar group has its own colour and icon, and each header tab owns some
  of the groups and shows only those in its sidebar. Both are in
  `website/src/lib/sections.ts`, matched to the sidebar in
  `website/astro.config.mjs` by label, so adding or renaming a group means
  updating `sections` and `tabs` there.
- The site's components and styles are shared with the other netspeedy docs
  sites, so their classes, custom properties and elements use the neutral `ns-`
  prefix and they don't name zquota. s3ctl's site is the standard, so carry
  design changes over from there rather than diverging. What's particular to
  zquota (its name, description, links, footer columns and the home page's
  directory line) lives in `website/src/lib/site.ts`, and the pages written for
  it are `HomeTop.astro`, `InstallTabs.astro` and `src/pages/404.astro`,
  alongside the content, `astro.config.mjs`, `src/lib/sections.ts` and the
  palette and mark colours in `theme.css`. Keep it that way, so a change to a
  shared file can be copied between the sites as it is.
- The docs are versioned by release line. Only the latest line lives in
  `website/src/content/docs`; never copy pages into per-version folders. When a
  new minor ships, the release workflow rebuilds the outgoing line from git with
  `SITE_ARCHIVE=vX.Y`, which serves it under `/zquota/vX.Y/`, and both Pages
  workflows publish it beside the latest. Keep page links root-relative
  (`/zquota/...`): archived builds rewrite them into their own line. Links to the APT files (`dists/`, `pool/`, the
  keyring and its fingerprint) are absolute URLs, because they're published
  beside the build rather than in it.
- Keep the website under `website/`, not under `.github/`: Dependabot stopped
  being able to open npm pull requests for manifests under `.github/` in June
  2026 (its create-PR call is rejected as "invalid or unauthorized changes").
- Keep root-level files for build, packaging, license, editor, and repository
  metadata only.
- Do not add GitLab-specific CI, release, or repository metadata to this GitHub
  repository.
- Retired files should be removed rather than kept as dead alternatives.

## Build, Test, and Development Commands

- Format Python code:
  ```bash
  make fmt
  ```
- Check formatting without rewriting files:
  ```bash
  make fmt-check
  ```
- Run static validation:
  ```bash
  make lint
  ```
- Run unit tests and bytecode compilation:
  ```bash
  make test
  ```
- Smoke test the CLI:
  ```bash
  make smoke
  ```
- Build package artifacts when the local environment has `build` installed:
  ```bash
  make build
  ```
- Check version metadata alignment:
  ```bash
  make version-check
  ```
- Build the docs site, then validate the built output (pages, search index,
  icons, share card and every internal link). The check reads `website/dist`,
  so it always runs after the build:
  ```bash
  make website-install
  make website-build
  make website-check
  ```
- Drive the site in headless Chrome: the theme controls, the header and its
  tabs, the version menu and an archived line. It builds its own latest and
  archived copies under `website/.test/`, so it needs no release metadata:
  ```bash
  make website-test
  ```
- Screenshot the built site in both themes at desktop and phone widths:
  ```bash
  make website-capture
  ```
- Serve the site with live reload while editing pages with `make website-dev`.
  When Astro detects an agent it starts the server in the background and
  returns, so stop it afterwards with `cd website && npx astro dev stop`.
  `website/README.md` summarises the folder, its targets and how it's
  published; keep it in step when any of those change.
- Build the Debian package when a Debian build environment is available:
  ```bash
  make package
  ```
- Syntax-check release helper scripts after editing them:
  ```bash
  bash -n scripts/*.sh
  ```

## Coding Style & Naming Conventions

- Python 3.12+ is the minimum supported runtime.
- Runtime code must remain stdlib-only. Development dependencies belong in the
  `dev` optional dependency group in `pyproject.toml`.
- Keep `zquota.py` readable as a single-file CLI: helpers, API parsing, output
  formatters, argument parsing, and entrypoint logic should stay clearly
  separated.
- Keep `main()` thin. Put validation, fetch, render, and loop behavior in
  focused helpers.
- Use type annotations on function signatures.
- Keep production functions documented with docstrings.
- Prefer structured JSON handling over ad hoc string parsing.
- Keep output fields stable unless the change is intentional and documented.
- Avoid broad refactors when a targeted fix is enough.
- Follow `.editorconfig`: Python uses 4 spaces, Markdown/YAML/JSON use 2
  spaces, and Makefiles use tabs.

## CLI Behavior Rules

- The default output is the human-readable quota view.
- Format flags are mutually exclusive: default, `--compact`, `--json`,
  `--jsonl`, and `--raw`.
- Keep exact reset visibility central to the tool. JSON-style outputs should
  preserve script-friendly reset fields such as `resets_at_utc` and
  `reset_epoch_ms`.
- Keep threshold behavior distinct: runtime errors exit `1`, and threshold
  breaches exit `2`.
- Do not make live API calls in tests. Mock `fetch_json()` or test parsing and
  formatting helpers directly.

## Versioning, Release, and Packaging Rules

- The default branch is `main`.
- Stable release tags use `v<major>.<minor>.<patch>`.
- Release candidate tags use `v<major>.<minor>.<patch>-rc.<n>`.
- Keep `VERSION` in `zquota.py` and `project.version` in `pyproject.toml`
  aligned with the stable target version in `debian/changelog`.
- Stable release tags must match the committed source version. RC tags are
  allowed to share the same committed source version as their stable target
  because promotion points the stable tag at the same commit.
- Release-note categories and version bump behavior are shared between
  `.github/release-drafter.yml` and `scripts/next-release.sh`; update them
  together.
- The release automation publishes a source archive, Debian package, Debian
  source package files, `sha256sums.txt`, a signed stable APT repository on
  GitHub Pages, and an updated Homebrew formula to the `homebrew-zquota` tap.
- Keep APT keyring filenames under the `zquota-archive-keyring.*` pattern.
- The Homebrew formula is written by `.github/workflows/publish-homebrew-formula.yml`,
  which fills in the release tarball's URL and SHA256 and pushes it to
  `netspeedy/homebrew-zquota`. Change the formula there; the tap's copy is
  overwritten on each stable release.
- Keep `Makefile` as the contributor-facing source of truth for common local
  validation commands.

## Documentation Sync

- When CLI flags, output formats or fields, exit codes, environment variables,
  error messages or installation behavior change, update the matching site pages
  in `website/src/content/docs` in the same change, and `README.md` and the man
  page (`debian/zquota.1`) where they cover the same thing.
  `test_cli_reference_covers_every_flag` in `tests/test_docs.py` fails when a
  flag is added or removed without updating
  `website/src/content/docs/reference/cli.mdx`.
- The sample output on the site's home page and in the guides is real zquota
  output for a sample response in the shape `tests/test_zquota.py` uses. When an
  output format changes, save such a response as JSON, run zquota against it
  with `--api-url file:///path/to/response.json` (no network needed) and paste
  what it prints, rather than editing the samples by hand.
- Update `docs/release.md` when release workflows, tag rules, or published
  artifacts change.
- Update the site's Installation page when installation, artifact, or APT
  repository behavior changes.
- Update `website/README.md` and the Website section of `docs/release.md` when
  the `make website-*` targets, the site's build inputs, or the workflows that
  publish it change.
- Keep examples realistic, copyable, and free of real secrets.
- Public docs should not reference private machine paths or internal-only
  repository locations.

## GitHub Actions & Public Repo Security

- Workflows that commit or tag do so as `netspeedybot`
  (`45371234+netspeedybot@users.noreply.github.com`), never as
  `github-actions[bot]`. `automated-only.sh` trusts that email, so nobody
  commits or opens pull requests as netspeedybot by hand.
- Treat this as a public repository. Workflow changes are security-sensitive.
- Keep workflow permissions least-privilege.
- Pull request workflows should validate code, not publish artifacts.
- Publishing should stay limited to trusted `v*` and `v*-rc.*` tags or explicit
  recovery dispatches.
- Automation auto-merge may approve and merge only trusted automation authors:
  Dependabot and GitHub automation bot accounts explicitly listed in
  `.github/workflows/automation-auto-merge.yml`.
- Never broaden auto-approval to general contributor pull requests.
- Release and publish tags must point to commits already contained in `main`;
  keep that verification in place.
- Stable APT publishing must remain limited to stable `v<major>.<minor>.<patch>`
  tags. Do not publish prerelease tags to the stable APT repository.
- Do not broaden token permissions, expose secrets to pull requests, or add
  publish jobs without documenting the operational need.

## Commit & Pull Request Guidelines

- Do not create commits unless the user explicitly asks for one.
- Keep changes focused by concern: runtime behavior, tests, docs, and release
  automation should be easy to review.
- Use conventional commit subjects for release-bearing work:
  `feat:`, `fix:`, `perf:`, `build:`, `deps:`, or `release:`.
- Documentation, CI, test, and maintenance-only changes should not cause a
  release bump unless paired with an intentional shipped behavior change.
- Do not mention prompts, AI assistance, or internal instruction sources in PR
  content.

## Agent Checklist

Before making non-trivial changes:

1. Read `AGENTS.md`, `README.md`, and the files directly related to the task.
2. Check the current worktree and do not overwrite unrelated user changes.
3. Prefer existing helpers, Make targets, and workflow patterns.
4. Update tests and docs alongside behavior changes.
5. Run the relevant validation commands before handing work back.

When the change touches normal runtime code, the expected minimum validation is:

```bash
make fmt-check
make lint
make test
make smoke
```

If packaging or release metadata change, also run script syntax checks,
`make version-check`, and `make build` when the local Python environment has the
build tooling installed, and `make package` when a Debian build environment is
available. If the website changes, run `make website-build`, `make website-check`
and `make website-test`, and look at `make website-capture` output for layout
changes.
