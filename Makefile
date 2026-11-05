PYTHON ?= python3
SRC := zquota.py
TESTS := tests
HERO := scripts/readme
WEBSITE_DIR ?= website

.PHONY: fmt fmt-check lint test smoke version-check build website-install website-dev website-build website-check website-test website-capture readme-hero package clean

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

website-build:
	test -d $(WEBSITE_DIR)/node_modules || (printf 'missing website dependencies; run `make website-install`\n' >&2 && exit 1)
	npm --prefix $(WEBSITE_DIR) run build

website-check:
	test -d $(WEBSITE_DIR)/node_modules || (printf 'missing website dependencies; run `make website-install`\n' >&2 && exit 1)
	npm --prefix $(WEBSITE_DIR) run check

website-test:
	test -d $(WEBSITE_DIR)/node_modules || (printf 'missing website dependencies; run `make website-install`\n' >&2 && exit 1)
	npm --prefix $(WEBSITE_DIR) run test

website-capture:
	test -d $(WEBSITE_DIR)/node_modules || (printf 'missing website dependencies; run `make website-install`\n' >&2 && exit 1)
	npm --prefix $(WEBSITE_DIR) run capture

readme-hero:
	uv run $(HERO)/build_readme_hero.py

package:
	dpkg-buildpackage -us -uc -b

clean:
	rm -rf build dist *.egg-info
	rm -rf _build site
	find . -type d \( -name __pycache__ -o -name .pytest_cache -o -name .ruff_cache -o -name .mypy_cache \) -prune -exec rm -rf {} +
