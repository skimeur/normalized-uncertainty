.PHONY: help install lint test check data uaf tolerable all clean

PY ?= python3

help:
	@echo "install    install the package and its development extras"
	@echo "lint       ruff over the whole tree"
	@echo "test       unit tests (synthetic inputs, no data needed)"
	@echo "check      public-safety gate: no restricted code, data or local paths"
	@echo "data       report which third-party sources are present and which are missing"
	@echo "uaf        rebuild every exhibit of 'Uncertain and Asymmetric Forecasts'"
	@echo "tolerable  rebuild every public-data exhibit of 'Tolerable Inflation, Intolerable Uncertainty'"
	@echo "all        check + lint + test + uaf + tolerable"
	@echo ""
	@echo "No data ships with this repository. Point NU_DATA_DIR at the folder"
	@echo "holding the sources of data/README.md before running uaf/tolerable."

install:
	$(PY) -m pip install -e ".[dev]"

lint:
	$(PY) -m ruff check .

test:
	$(PY) -m pytest

check:
	$(PY) scripts/check_public_safe.py

data:
	$(PY) scripts/check_data_sources.py

uaf:
	$(PY) papers/uncertain-and-asymmetric-forecasts/run.py

tolerable:
	$(PY) papers/tolerable-inflation-intolerable-uncertainty/run.py

all: check lint test uaf tolerable

clean:
	rm -rf .pytest_cache .ruff_cache **/__pycache__ build dist *.egg-info
