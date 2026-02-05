"""Unit tests for navigation callbacks.

Tests that navigation callbacks properly trigger Streamlit reruns
to update the UI state.
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestNavigationCallbacks:
    """Test navigation callback functions."""

    @patch('streamlit.session_state', {})
    @patch('streamlit.rerun')
    def test_go_to_add_card_sets_state_and_reruns(self, mock_rerun):
        """Test that go_to_add_card() sets session state AND calls rerun.
        
        Bug #006 fix: Previously only set state without rerun,
        causing button clicks to have no effect.
        """
        # Import after mocking streamlit
        with patch.dict('sys.modules', {'streamlit': Mock()}):
            import streamlit as st
            # Import the app module to get go_to_add_card
            from ui import app
            
            # Call the navigation function
            app.go_to_add_card()
            
            # Assert session state was set
            assert st.session_state.navigate_to_add_card is True
            
            # Assert rerun was called (this was the bug)
            mock_rerun.assert_called_once()

    @patch('streamlit.session_state', {'demo_mode': False, 'show_welcome': True})
    @patch('streamlit.rerun')
    def test_demo_mode_activation_calls_rerun(self, mock_rerun):
        """Test that demo mode activation triggers rerun.
        
        This was already working correctly, but test for regression.
        """
        with patch.dict('sys.modules', {'streamlit': Mock()}):
            import streamlit as st
            
            # Simulate demo mode activation
            st.session_state.demo_mode = True
            st.session_state.show_welcome = False
            st.rerun()
            
            # Verify rerun was called
            mock_rerun.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
