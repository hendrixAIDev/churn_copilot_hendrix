"""Tests for toast notification system.

These tests verify that toast notifications handle edge cases gracefully
and never crash the application.
"""

import pytest
from unittest.mock import patch, MagicMock
import streamlit as st


class TestSafeToast:
    """Test the defensive _safe_toast wrapper."""

    def test_valid_emoji_works(self):
        """Test that valid emoji icons work correctly."""
        from src.ui.components.toast import _safe_toast
        
        with patch.object(st, 'toast') as mock_toast:
            _safe_toast("Test message", "✅")
            mock_toast.assert_called_once_with("Test message", icon="✅")

    def test_invalid_emoji_falls_back_gracefully(self):
        """Test that invalid emoji falls back to no icon instead of crashing."""
        from src.ui.components.toast import _safe_toast
        
        # Simulate StreamlitAPIException on first call (invalid emoji)
        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1 and 'icon' in kwargs:
                raise Exception("Invalid emoji")
            return None
        
        with patch.object(st, 'toast', side_effect=side_effect) as mock_toast:
            # Should not raise, should fall back
            _safe_toast("Test message", "✓")  # Invalid: checkmark symbol, not emoji
            
            # Should have been called twice: once with icon (failed), once without
            assert mock_toast.call_count == 2

    def test_complete_failure_silently_ignored(self):
        """Test that if even fallback fails, we don't crash."""
        from src.ui.components.toast import _safe_toast
        
        with patch.object(st, 'toast', side_effect=Exception("Total failure")):
            # Should not raise any exception
            _safe_toast("Test message", "✅")
            # If we get here without exception, test passes


class TestToastFunctions:
    """Test the public toast functions."""

    def test_show_toast_success_default_icon(self):
        """Test success toast uses correct default icon."""
        from src.ui.components.toast import show_toast_success
        
        with patch('src.ui.components.toast._safe_toast') as mock_safe:
            show_toast_success("Success!")
            mock_safe.assert_called_once_with("Success!", "✅")

    def test_show_toast_error_default_icon(self):
        """Test error toast uses correct default icon."""
        from src.ui.components.toast import show_toast_error
        
        with patch('src.ui.components.toast._safe_toast') as mock_safe:
            show_toast_error("Error!")
            mock_safe.assert_called_once_with("Error!", "❌")

    def test_show_toast_warning_default_icon(self):
        """Test warning toast uses correct default icon."""
        from src.ui.components.toast import show_toast_warning
        
        with patch('src.ui.components.toast._safe_toast') as mock_safe:
            show_toast_warning("Warning!")
            mock_safe.assert_called_once_with("Warning!", "⚠️")

    def test_show_toast_info_default_icon(self):
        """Test info toast uses correct default icon."""
        from src.ui.components.toast import show_toast_info
        
        with patch('src.ui.components.toast._safe_toast') as mock_safe:
            show_toast_info("Info!")
            mock_safe.assert_called_once_with("Info!", "ℹ️")

    def test_custom_icon_passed_through(self):
        """Test that custom icons are passed through."""
        from src.ui.components.toast import show_toast_success
        
        with patch('src.ui.components.toast._safe_toast') as mock_safe:
            show_toast_success("Custom!", icon="🎉")
            mock_safe.assert_called_once_with("Custom!", "🎉")


class TestKnownBadIcons:
    """Test that known problematic icons are handled gracefully.
    
    This serves as a regression test for icons that have caused issues.
    """

    @pytest.mark.parametrize("bad_icon", [
        "✓",      # Checkmark symbol (not emoji) - caused StreamlitAPIException
        "×",      # Multiplication sign
        "√",      # Square root
        ":check:", # Shortcode (not supported)
        "",       # Empty string
    ])
    def test_bad_icons_dont_crash(self, bad_icon):
        """Test that known bad icons don't crash the app."""
        from src.ui.components.toast import _safe_toast
        
        with patch.object(st, 'toast', side_effect=Exception("Invalid")):
            # Should not raise
            _safe_toast("Test", bad_icon)
