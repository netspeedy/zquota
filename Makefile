PYTHON ?= python3
SRC := zquota.py
TESTS := tests
HERO := scripts/readme
WEBSITE_DIR ?= website
SITE_URL ?= https://netspeedy.github.io/zquota/
SITE_RELEASE_VERSION ?= $(shell git describe --tags --always --dirty 2>/dev/null || printf '%s' dev)
SITE_COMMIT ?= $(shell git rev-parse --short HEAD 2>/dev/null || printf '%s' local)
SITE_BUILD_DATE ?= $(shell date -u +%Y-%m-%dT%H:%M:%SZ)
SITE_APT_FINGERPRINT ?= Published alongside stable release builds.

.PHONY: fmt fmt-check lint test smoke version-check build website-install website-dev website-check website-build readme-hero package clean

fmt:
	$(PYTHON) -m black $(SRC) $(TESTS) $(HERO)

fmt-check:
	$(PYTHON) -m black --check $(SRC) $(TESTS) $(HERO)

lint:
	$(PYTHON) -m ruff check $(SRC) $(TESTS) $(HERO)
	$(PYTHON) -m pylint $(SRC)

test:
	$(PYTHON) -m unittest discover -s $(TESTS)
	$(PYTHON) -m py_compile $(SRC)

smoke:
	$(PYTHON) $(SRC) --version
	$(PYTHON) $(SRC) --help >/dev/null

version-check:
	bash scripts/check-version-consistency.sh

build:
	$(PYTHON) -m build

website-install:
	npm --prefix $(WEBSITE_DIR) ci

website-dev:
	test -d $(WEBSITE_DIR)/node_modules || (printf 'missing website dependencies; run `make website-install`\n' >&2 && exit 1)
	npm --prefix $(WEBSITE_DIR) run dev

website-check:
	test -d $(WEBSITE_DIR)/node_modules || (printf 'missing website dependencies; run `make website-install`\n' >&2 && exit 1)
	npm --prefix $(WEBSITE_DIR) run check

website-build:
	test -d $(WEBSITE_DIR)/node_modules || (printf 'missing website dependencies; run `make website-install`\n' >&2 && exit 1)
	PUBLIC_SITE_URL=$(SITE_URL) \
	PUBLIC_RELEASE_VERSION=$(SITE_RELEASE_VERSION) \
	PUBLIC_COMMIT=$(SITE_COMMIT) \
	PUBLIC_BUILD_DATE=$(SITE_BUILD_DATE) \
	PUBLIC_APT_FINGERPRINT='$(SITE_APT_FINGERPRINT)' \
	npm --prefix $(WEBSITE_DIR) run build

readme-hero:
	uv run $(HERO)/build_readme_hero.py

package:
	dpkg-buildpackage -us -uc -b

clean:
	rm -rf build dist *.egg-info
	rm -rf _build site
	find . -type d \( -name __pycache__ -o -name .pytest_cache -o -name .ruff_cache -o -name .mypy_cache \) -prune -exec rm -rf {} +
