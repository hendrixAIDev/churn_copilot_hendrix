"""Tests for localStorage-based session persistence.

Tests the session token save/load/clear functions that use
streamlit_js_eval to access browser localStorage.

Since these functions require a browser (streamlit_js_eval),
we test the logic paths with mocking and verify the JS code generation.
"""

import pytest
from unittest.mock import patch, MagicMock, call
from uuid import uuid4


class MockSessionState(dict):
    """Dict subclass that supports attribute access like st.session_state."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        try:
            del self[name]
        except KeyError:
            raise AttributeError(name)


class TestSaveSessionToken:
    """Test _save_session_token function."""

    @patch("streamlit_js_eval.streamlit_js_eval")
    @patch("src.ui.app.st")
    def test_save_calls_js_eval_with_localstorage(self, mock_st, mock_js_eval):
        """Should call streamlit_js_eval with localStorage.setItem."""
        mock_st.session_state = MockSessionState()

        from src.ui.app import _save_session_token, SESSION_STORAGE_KEY

        token = "a" * 64
        result = _save_session_token(token)

        assert result is True
        mock_js_eval.assert_called_once()
        call_kwargs = mock_js_eval.call_args
        js_code = call_kwargs.kwargs.get("js_expressions", "")
        assert "window.parent.localStorage.setItem" in js_code
        assert SESSION_STORAGE_KEY in js_code
        assert token in js_code

    @patch("src.ui.app.st")
    def test_save_handles_import_error(self, mock_st):
        """Should return False if streamlit_js_eval not available."""
        mock_st.session_state = MockSessionState()

        import sys
        original = sys.modules.get("streamlit_js_eval")
        sys.modules["streamlit_js_eval"] = None

        try:
            # Re-import to pick up the mocked module
            from importlib import reload
            import src.ui.app as app_module

            result = app_module._save_session_token("a" * 64)
            assert result is False
        finally:
            if original:
                sys.modules["streamlit_js_eval"] = original
            else:
                sys.modules.pop("streamlit_js_eval", None)

    @patch("streamlit_js_eval.streamlit_js_eval")
    @patch("src.ui.app.st")
    def test_save_increments_counter(self, mock_st, mock_js_eval):
        """Should use incrementing key to force re-render."""
        mock_st.session_state = MockSessionState()

        from src.ui.app import _save_session_token

        _save_session_token("a" * 64)
        assert mock_st.session_state.get("_session_save_counter") == 1

        _save_session_token("b" * 64)
        assert mock_st.session_state.get("_session_save_counter") == 2


class TestLoadSessionToken:
    """Test _load_session_token function."""

    @patch("streamlit_js_eval.streamlit_js_eval")
    @patch("src.ui.app.st")
    def test_load_calls_js_eval_with_getitem(self, mock_st, mock_js_eval):
        """Should call streamlit_js_eval with localStorage.getItem."""
        mock_st.session_state = MockSessionState()
        mock_js_eval.return_value = "a" * 64

        from src.ui.app import _load_session_token, SESSION_STORAGE_KEY

        result = _load_session_token()

        assert result == "a" * 64
        mock_js_eval.assert_called_once()
        call_kwargs = mock_js_eval.call_args
        js_code = call_kwargs.kwargs.get("js_expressions", "")
        assert "window.parent.localStorage.getItem" in js_code
        assert SESSION_STORAGE_KEY in js_code

    @patch("streamlit_js_eval.streamlit_js_eval")
    @patch("src.ui.app.st")
    def test_load_returns_none_on_first_render(self, mock_st, mock_js_eval):
        """Should return None when JS hasn't executed yet (first render)."""
        mock_st.session_state = MockSessionState()
        mock_js_eval.return_value = None

        from src.ui.app import _load_session_token

        result = _load_session_token()
        assert result is None

    @patch("streamlit_js_eval.streamlit_js_eval")
    @patch("src.ui.app.st")
    def test_load_uses_stable_key(self, mock_st, mock_js_eval):
        """Should use stable key for caching across reruns."""
        mock_st.session_state = MockSessionState()
        mock_js_eval.return_value = "token123"

        from src.ui.app import _load_session_token

        _load_session_token()
        call_kwargs = mock_js_eval.call_args
        key = call_kwargs.kwargs.get("key", "")
        assert key == "session_loader"


class TestClearSessionToken:
    """Test _clear_session_token function."""

    @patch("streamlit_js_eval.streamlit_js_eval")
    @patch("src.ui.app.st")
    def test_clear_calls_js_eval_with_removeitem(self, mock_st, mock_js_eval):
        """Should call streamlit_js_eval with localStorage.removeItem."""
        mock_st.session_state = MockSessionState()

        from src.ui.app import _clear_session_token, SESSION_STORAGE_KEY

        result = _clear_session_token()

        assert result is True
        mock_js_eval.assert_called_once()
        call_kwargs = mock_js_eval.call_args
        js_code = call_kwargs.kwargs.get("js_expressions", "")
        assert "window.parent.localStorage.removeItem" in js_code
        assert SESSION_STORAGE_KEY in js_code


class TestCheckStoredSession:
    """Test check_stored_session function."""

    @patch("src.ui.app.st")
    def test_skip_if_already_authenticated(self, mock_st):
        """Should return True immediately if user_id in session_state."""
        mock_st.session_state = MockSessionState({"user_id": "some-uuid"})

        from src.ui.app import check_stored_session

        result = check_stored_session()
        assert result is True

    @patch("src.ui.app.st")
    def test_skip_if_check_already_done(self, mock_st):
        """Should return False if session check already completed."""
        mock_st.session_state = MockSessionState({"_session_check_done": True})

        from src.ui.app import check_stored_session

        result = check_stored_session()
        assert result is False

    @patch("src.ui.app._load_session_token")
    @patch("src.ui.app.st")
    def test_returns_false_on_first_render(self, mock_st, mock_load):
        """Should return False when JS returns None (first render)."""
        mock_st.session_state = MockSessionState()
        mock_load.return_value = None

        from src.ui.app import check_stored_session

        result = check_stored_session()
        assert result is False
        # Should NOT mark _session_check_done (need to retry on rerun)
        assert "_session_check_done" not in mock_st.session_state

    @patch("src.ui.app._load_session_token")
    @patch("src.ui.app.st")
    def test_marks_done_on_invalid_token(self, mock_st, mock_load):
        """Should mark done when token has wrong length."""
        mock_st.session_state = MockSessionState()
        mock_load.return_value = "short_token"

        from src.ui.app import check_stored_session

        result = check_stored_session()
        assert result is False
        assert mock_st.session_state.get("_session_check_done") is True

    @patch("src.ui.app.AuthService")
    @patch("src.ui.app._load_session_token")
    @patch("src.ui.app.st")
    def test_restores_valid_session(self, mock_st, mock_load, mock_auth_cls):
        """Should restore session state when token is valid."""
        mock_st.session_state = MockSessionState()
        token = "a" * 64
        mock_load.return_value = token

        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.email = "test@example.com"

        mock_auth = MagicMock()
        mock_auth.validate_session.return_value = mock_user
        mock_auth_cls.return_value = mock_auth

        from src.ui.app import check_stored_session

        result = check_stored_session()
        assert result is True
        assert mock_st.session_state["user_id"] == str(mock_user.id)
        assert mock_st.session_state["user_email"] == "test@example.com"
        assert mock_st.session_state["session_token"] == token
        assert mock_st.session_state["_session_check_done"] is True

    @patch("src.ui.app._clear_session_token")
    @patch("src.ui.app.AuthService")
    @patch("src.ui.app._load_session_token")
    @patch("src.ui.app.st")
    def test_clears_expired_session(self, mock_st, mock_load, mock_auth_cls, mock_clear):
        """Should clear localStorage when session is expired/invalid."""
        mock_st.session_state = MockSessionState()
        token = "a" * 64
        mock_load.return_value = token

        mock_auth = MagicMock()
        mock_auth.validate_session.return_value = None  # Expired
        mock_auth_cls.return_value = mock_auth

        from src.ui.app import check_stored_session

        result = check_stored_session()
        assert result is False
        mock_clear.assert_called_once()
        assert mock_st.session_state["_session_check_done"] is True


class TestSessionStorageKey:
    """Test session storage key configuration."""

    def test_storage_key_is_defined(self):
        """SESSION_STORAGE_KEY should be a non-empty string."""
        from src.ui.app import SESSION_STORAGE_KEY
        assert isinstance(SESSION_STORAGE_KEY, str)
        assert len(SESSION_STORAGE_KEY) > 0

    def test_storage_key_value(self):
        """SESSION_STORAGE_KEY should be 'churnpilot_session'."""
        from src.ui.app import SESSION_STORAGE_KEY
        assert SESSION_STORAGE_KEY == "churnpilot_session"


class TestJsCodeSecurity:
    """Test that generated JS code is safe."""

    def test_token_in_js_is_hex_only(self):
        """Tokens should be hex strings - no injection risk."""
        import secrets
        from src.core.auth import SESSION_TOKEN_BYTES

        token = secrets.token_hex(SESSION_TOKEN_BYTES)
        # Verify it's only hex characters
        assert all(c in "0123456789abcdef" for c in token)
        # Verify length
        assert len(token) == SESSION_TOKEN_BYTES * 2

    def test_storage_key_is_safe_for_js(self):
        """Storage key should be alphanumeric + underscores only."""
        from src.ui.app import SESSION_STORAGE_KEY
        assert all(c.isalnum() or c == "_" for c in SESSION_STORAGE_KEY)
