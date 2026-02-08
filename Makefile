# ChurnPilot Project Makefile
# Standard targets for Hendrix projects

.PHONY: run test test-e2e test-all lint setup clean deploy-experiment

# Configuration
VENV = venv/bin
PORT = 8501
APP = src/ui/app.py

# Setup (run once)
setup:
	python3 -m venv venv
	$(VENV)/pip install -r requirements.txt
	../../../libs/setup_project.sh

# Run locally
run:
	$(VENV)/streamlit run $(APP) --server.port $(PORT) --server.headless true

# Run in foreground (for debugging)
run-debug:
	$(VENV)/streamlit run $(APP) --server.port $(PORT)

# Unit tests only
test:
	$(VENV)/python -m pytest tests/ -v --ignore=tests/e2e/ --timeout=10

# E2E tests (requires server running on PORT)
test-e2e:
	$(VENV)/python -m pytest tests/e2e/ -v --timeout=30

# All tests
test-all: test test-e2e

# Quick test (fast subset for CI)
test-quick:
	$(VENV)/python -m pytest tests/test_auth.py tests/test_normalize.py tests/test_periods.py -v --timeout=10

# Lint
lint:
	$(VENV)/ruff check .

# Clean
clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache
	find . -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Deploy to experiment branch
deploy-experiment:
	git add -A
	git commit -m "Deploy to experiment" || true
	git push origin experiment

# Check if server is running
status:
	@lsof -i :$(PORT) 2>/dev/null | grep LISTEN && echo "Server running on :$(PORT)" || echo "Server not running"
