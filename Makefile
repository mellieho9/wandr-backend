.PHONY: test test-unit test-integration test-slow install clean

# Install dependencies
install:
	pip install -r requirements.txt

# Run all tests
test:
	pytest

# Run only unit tests (fast)
test-unit:
	pytest -m unit

# Run integration tests
test-integration:
	pytest -m integration

# Run slow tests (requires API keys)
test-slow:
	pytest -m slow

# Run tests with coverage
test-coverage:
	pytest --cov=. --cov-report=html

# Clean up test artifacts
clean:
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf __pycache__/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +

# Run specific test file
test-file:
	pytest $(FILE) -v

# Example: make test-file FILE=tests/unit/test_url_parser.py