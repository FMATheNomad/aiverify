.PHONY: test build publish clean install

test:
	python -m pytest tests/ -v

build:
	python -m build

publish:
	python -m twine upload dist/*

clean:
	rm -rf dist/ build/ *.egg-info/ .aiverifyrc
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

lint:
	ruff check aiverify/ tests/
