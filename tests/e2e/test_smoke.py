"""
ChurnPilot Smoke Tests
======================

Quick verification that the app is working.
Run with: make test-e2e

For sub-agent browser automation testing, see SMOKE_TEST_CHECKLIST below.
"""

import requests
import pytest

BASE_URL = "http://localhost:8501"


def test_homepage_loads():
    """Verify the app responds to HTTP requests."""
    try:
        response = requests.get(BASE_URL, timeout=5)
        assert response.status_code == 200
    except requests.exceptions.ConnectionError:
        pytest.skip("Server not running on :8501")


def test_health_endpoint():
    """Verify health endpoint if it exists."""
    try:
        response = requests.get(f"{BASE_URL}/_stcore/health", timeout=5)
        # Streamlit returns 200 for health
        assert response.status_code == 200
    except requests.exceptions.ConnectionError:
        pytest.skip("Server not running on :8501")


# =============================================================================
# SMOKE TEST CHECKLIST (for sub-agent browser automation)
# =============================================================================
#
# Sub-agents use browser automation (browser tool with profile=agentN) to verify:
#
# 1. [ ] Homepage loads without error
# 2. [ ] Login form visible (if not authenticated)
# 3. [ ] Can enter test credentials
# 4. [ ] After login: dashboard loads
# 5. [ ] Can navigate to main feature (Retention Offers / Analysis)
# 6. [ ] No console errors visible
# 7. [ ] Sample data loads (if using demo mode)
#
# Browser automation pattern:
#   browser(action="open", targetUrl="http://localhost:8501", profile="agent1")
#   browser(action="snapshot", profile="agent1")  # Verify page state
#   browser(action="act", request={"kind": "type", "ref": "...", "text": "..."})
#
# =============================================================================
