# ChurnPilot Project Makefile
# ===========================
# Standard targets for Hendrix projects
#
# Test Pipeline:
#   1. make test-unit      → After implementation
#   2. make test-e2e       → Before commit  
#   3. make test-smoke     → After push to experiment
#   4. make test-journey   → Before launch (merge to main)

.PHONY: run test test-unit test-e2e test-smoke test-journey test-all lint setup clean deploy-experiment pre-commit

# Configuration
VENV = venv/bin
PORT = 8501
APP = src/ui/app.py
EXPERIMENT_URL ?= https://churnpilot-experiment.streamlit.app
LOCAL_URL ?= http://localhost:8501

# =============================================================================
# SETUP
# =============================================================================

setup:
	python3 -m venv venv
	$(VENV)/pip install -r requirements.txt
	chmod +x scripts/*.sh
	@echo "✓ Setup complete. Run 'make run' to start the app."
	@echo "→ For journey tests, also run 'make setup-playwright'"

setup-playwright:
	$(VENV)/playwright install chromium
	@echo "✓ Playwright browser installed"

# =============================================================================
# RUN
# =============================================================================

run:
	$(VENV)/streamlit run $(APP) --server.port $(PORT) --server.headless true

run-debug:
	$(VENV)/streamlit run $(APP) --server.port $(PORT)

status:
	@lsof -i :$(PORT) 2>/dev/null | grep LISTEN && echo "✓ Server running on :$(PORT)" || echo "✗ Server not running"

# =============================================================================
# TEST PIPELINE
# =============================================================================

# Stage 1: Unit Tests (after implementation)
test-unit:
	@echo "→ Stage 1: Unit Tests"
	$(VENV)/python -m pytest tests/ \
		--ignore=tests/e2e/ \
		--ignore=tests/remote/ \
		-v --timeout=10 \
		-m "not slow"

# Stage 2: E2E Tests (before commit)
test-e2e:
	@echo "→ Stage 2: E2E Tests"
	@curl -s --max-time 3 $(LOCAL_URL)/_stcore/health > /dev/null || (echo "✗ Server not running. Start with 'make run'" && exit 1)
	LOCAL_URL=$(LOCAL_URL) $(VENV)/python -m pytest tests/e2e/ -v --timeout=60

# Stage 3: Smoke Tests (after push to experiment)
test-smoke:
	@echo "→ Stage 3: Smoke Tests (Remote)"
	@echo "  URL: $(EXPERIMENT_URL)"
	EXPERIMENT_URL=$(EXPERIMENT_URL) $(VENV)/python -m pytest tests/remote/test_smoke_remote.py -v --timeout=60

# Stage 4: User Journey Tests (before launch)
test-journey:
	@echo "→ Stage 4: User Journey Tests (Remote)"
	@echo "  URL: $(EXPERIMENT_URL)"
	EXPERIMENT_URL=$(EXPERIMENT_URL) $(VENV)/python -m pytest tests/remote/test_user_journeys_remote.py -v --timeout=120

# All stages in sequence
test-all:
	./scripts/test-stages.sh all

# Quick test (fast subset)
test-quick:
	$(VENV)/python -m pytest tests/test_auth.py tests/test_normalize.py tests/test_periods.py -v --timeout=10

# Backward compatibility
test: test-unit

# =============================================================================
# PRE-COMMIT WORKFLOW
# =============================================================================

# Run before committing (unit + e2e)
pre-commit: test-unit test-e2e
	@echo "✓ Pre-commit checks passed"

# =============================================================================
# DEPLOYMENT
# =============================================================================

# Deploy to experiment branch
deploy-experiment:
	git add -A
	git commit -m "Deploy to experiment" || true
	git push origin experiment
	@echo "→ Deployed to experiment. Wait for Streamlit Cloud, then run 'make test-smoke'"

# Full experiment workflow: commit → push → smoke test
experiment-full: pre-commit deploy-experiment
	@echo "→ Waiting 60s for Streamlit Cloud deployment..."
	@sleep 60
	$(MAKE) test-smoke

# =============================================================================
# UTILITIES
# =============================================================================

lint:
	$(VENV)/ruff check .

clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache
	find . -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# =============================================================================
# HELP
# =============================================================================

help:
	@echo "ChurnPilot Test Pipeline"
	@echo "========================"
	@echo ""
	@echo "Development:"
	@echo "  make run              Start local server"
	@echo "  make status           Check if server running"
	@echo ""
	@echo "Test Pipeline (run in order):"
	@echo "  make test-unit        Stage 1: Unit tests (after implementation)"
	@echo "  make test-e2e         Stage 2: E2E tests (before commit)"
	@echo "  make test-smoke       Stage 3: Smoke tests (after push to experiment)"
	@echo "  make test-journey     Stage 4: User journey tests (before launch)"
	@echo ""
	@echo "Workflows:"
	@echo "  make pre-commit       Run unit + e2e before committing"
	@echo "  make deploy-experiment Push to experiment branch"
	@echo "  make experiment-full  pre-commit + deploy + smoke test"
	@echo ""
	@echo "Environment Variables:"
	@echo "  LOCAL_URL             Override local URL (default: http://localhost:8501)"
	@echo "  EXPERIMENT_URL        Override experiment URL"
