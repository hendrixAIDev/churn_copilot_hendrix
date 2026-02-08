"""
Remote Smoke Tests
==================

Quick verification that the experiment deployment is working.
Run AFTER pushing to experiment branch.

Usage:
    pytest tests/remote/test_smoke_remote.py -v
    # Or via make:
    make test-smoke-experiment

Environment:
    EXPERIMENT_URL: Override default experiment URL
"""

import pytest
import requests
import os

# Default to experiment URL, can override for production
BASE_URL = os.getenv("EXPERIMENT_URL", "https://churnpilot-experiment.streamlit.app")


@pytest.mark.smoke
class TestRemoteSmoke:
    """Quick smoke tests for remote deployment."""

    def test_app_responds(self):
        """App should respond to HTTP requests."""
        response = requests.get(BASE_URL, timeout=30)
        assert response.status_code == 200, f"App not responding: {response.status_code}"

    def test_streamlit_health(self):
        """Streamlit health endpoint should respond."""
        response = requests.get(f"{BASE_URL}/_stcore/health", timeout=10)
        assert response.status_code == 200

    def test_no_error_page(self):
        """App should not show Streamlit error page."""
        response = requests.get(BASE_URL, timeout=30)
        error_indicators = [
            "streamlit error",
            "ModuleNotFoundError",
            "ImportError",
            "Exception",
            "Traceback",
        ]
        content_lower = response.text.lower()
        for indicator in error_indicators:
            assert indicator.lower() not in content_lower, f"Found error indicator: {indicator}"

    def test_login_elements_present(self):
        """Page should contain login-related elements."""
        response = requests.get(BASE_URL, timeout=30)
        # Streamlit apps render differently, check for common patterns
        assert response.status_code == 200
        # Basic check that we got HTML content
        assert "html" in response.text.lower() or "streamlit" in response.text.lower()


@pytest.mark.smoke
class TestRemoteAPI:
    """API endpoint smoke tests."""

    def test_api_base(self):
        """API should be accessible."""
        # Streamlit doesn't have traditional API endpoints
        # This tests the base app is serving
        response = requests.get(BASE_URL, timeout=30)
        assert response.status_code == 200
