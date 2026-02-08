"""
ChurnPilot Test Configuration
=============================

Test stages and markers:
- unit: Fast unit tests, no external dependencies
- e2e: End-to-end tests, requires local server
- smoke: Quick verification on remote deployment
- journey: Full user journey tests on remote deployment

Usage:
    pytest -m unit           # Unit tests only
    pytest -m e2e            # E2E tests only
    pytest -m smoke          # Smoke tests only
    pytest -m journey        # User journey tests only
"""

import pytest
import os

# Register custom markers
def pytest_configure(config):
    config.addinivalue_line("markers", "unit: Unit tests (fast, no dependencies)")
    config.addinivalue_line("markers", "e2e: End-to-end tests (requires local server)")
    config.addinivalue_line("markers", "smoke: Smoke tests (quick remote verification)")
    config.addinivalue_line("markers", "journey: User journey tests (comprehensive remote)")
    config.addinivalue_line("markers", "slow: Slow tests (skip with -m 'not slow')")


# Environment configuration
@pytest.fixture(scope="session")
def local_url():
    """Local development server URL."""
    return os.getenv("LOCAL_URL", "http://localhost:8501")


@pytest.fixture(scope="session")
def experiment_url():
    """Experiment branch deployment URL."""
    return os.getenv("EXPERIMENT_URL", "https://churnpilot-experiment.streamlit.app")


@pytest.fixture(scope="session")
def production_url():
    """Production deployment URL."""
    return os.getenv("PRODUCTION_URL", "https://churnpilot.streamlit.app")


# Database fixtures
@pytest.fixture(scope="session")
def db_url():
    """Database URL for tests."""
    return os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/churnpilot")
