"""Comprehensive persistence tests for ChurnPilot.

These tests specifically verify the behaviors that users reported as bugs:
1. Cards appearing immediately after adding (session state update)
2. Cards persisting across page refresh (localStorage sync)
3. Retry logic for initial load

The tests mock Streamlit session_state and streamlit_js_eval to simulate
different browser scenarios.
"""

import json
import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime

# Mock streamlit before importing our modules
import sys
from unittest.mock import MagicMock

# Create mock for streamlit
mock_st = MagicMock()
mock_st.session_state = {}

# Create a property-like behavior for session_state
class MockSessionState(dict):
    """Mock session state that behaves like Streamlit's session_state."""
    def __getattr__(self, key):
        if key in self:
            return self[key]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{key}'")

    def __setattr__(self, key, value):
        self[key] = value

mock_st.session_state = MockSessionState()

sys.modules['streamlit'] = mock_st
sys.modules['streamlit.components'] = MagicMock()
sys.modules['streamlit.components.v1'] = MagicMock()

# Now import our modules
from src.core.web_storage import (
    _serialize_for_json,
    init_web_storage,
    save_web,
    save_to_localstorage,
    WebStorage,
    STORAGE_KEY,
)
from src.core.models import Card, Credit


class TestSessionStateImmediacy:
    """Test that session state is updated IMMEDIATELY after operations.

    This is critical because Streamlit's tab rendering order means the Dashboard
    might render before the Add Card handler runs. Session state must be updated
    synchronously to ensure data is available.
    """

    def setup_method(self):
        """Reset session state before each test."""
        mock_st.session_state.clear()
        mock_st.session_state['cards_data'] = []
        mock_st.session_state['storage_initialized'] = True

    def test_save_web_updates_session_state_first(self):
        """save_web MUST update session_state BEFORE any async operations."""
        # Initial state
        assert mock_st.session_state['cards_data'] == []

        # Save some data
        test_data = [{"id": "test1", "name": "Test Card"}]

        with patch('src.core.web_storage._get_js_eval', return_value=None):
            # Even if JS eval is unavailable, session state should update
            save_web(test_data)

        # Session state should be updated immediately
        assert mock_st.session_state['cards_data'] == test_data

    def test_add_card_updates_session_state_immediately(self):
        """Adding a card should update session_state synchronously."""
        storage = WebStorage()

        # Mock the library template
        from src.core.library import CardTemplate
        from src.core.models import Credit

        template = CardTemplate(
            id="test_card",
            name="Test Card",
            issuer="Test Bank",
            annual_fee=95,
            credits=[],
        )

        with patch('src.core.web_storage._get_js_eval', return_value=None):
            card = storage.add_card_from_template(
                template=template,
                nickname="My Test",
                opened_date=date(2024, 1, 1),
            )

        # Verify session state was updated
        assert len(mock_st.session_state['cards_data']) == 1
        assert mock_st.session_state['cards_data'][0]['name'] == "Test Card"
        assert mock_st.session_state['cards_data'][0]['nickname'] == "My Test"

    def test_multiple_adds_accumulate_correctly(self):
        """Multiple add operations should accumulate in session state."""
        storage = WebStorage()

        from src.core.library import CardTemplate

        templates = [
            CardTemplate(id="card1", name="Card 1", issuer="Bank A", annual_fee=0, credits=[]),
            CardTemplate(id="card2", name="Card 2", issuer="Bank B", annual_fee=95, credits=[]),
            CardTemplate(id="card3", name="Card 3", issuer="Bank C", annual_fee=550, credits=[]),
        ]

        with patch('src.core.web_storage._get_js_eval', return_value=None):
            for i, template in enumerate(templates):
                storage.add_card_from_template(template=template)
                # Verify count after each add
                assert len(mock_st.session_state['cards_data']) == i + 1

        # Final verification
        assert len(mock_st.session_state['cards_data']) == 3
        names = [c['name'] for c in mock_st.session_state['cards_data']]
        assert names == ["Card 1", "Card 2", "Card 3"]


class TestLocalStorageSave:
    """Test that saves to localStorage are properly formatted."""

    def setup_method(self):
        """Reset session state before each test."""
        mock_st.session_state.clear()
        mock_st.session_state['cards_data'] = []
        mock_st.session_state['storage_initialized'] = True

    def test_save_generates_valid_json(self):
        """The JavaScript save should contain valid JSON."""
        test_data = [
            {
                "id": "uuid-123",
                "name": "Amex Platinum",
                "issuer": "American Express",
                "annual_fee": 695,
                "credits": [],
            }
        ]

        # Capture the JS code that would be executed
        captured_js = []

        def mock_js_eval(js, key):
            captured_js.append(js)
            return True

        with patch('src.core.web_storage._get_js_eval', return_value=mock_js_eval):
            save_to_localstorage(test_data)

        # Verify JS was generated
        assert len(captured_js) == 1
        js_code = captured_js[0]

        # The JS should contain the correct storage key
        assert STORAGE_KEY in js_code

        # The JS should contain the card data
        assert "Amex Platinum" in js_code
        assert "American Express" in js_code

    def test_save_escapes_special_characters(self):
        """Special characters in card data should be properly escaped."""
        test_data = [
            {
                "id": "uuid-123",
                "name": "Card with 'quotes' and \"double quotes\"",
                "issuer": "Bank\nWith\nNewlines",
                "annual_fee": 0,
                "notes": "Has backslash \\ and tab\t",
            }
        ]

        captured_js = []

        def mock_js_eval(js, key):
            captured_js.append(js)
            return True

        with patch('src.core.web_storage._get_js_eval', return_value=mock_js_eval):
            save_to_localstorage(test_data)

        # Should not raise any errors
        assert len(captured_js) == 1

        # The JS should be parseable (no syntax errors)
        # We can't execute it, but we can verify it doesn't contain unescaped quotes
        js_code = captured_js[0]

        # Should contain escaped versions
        assert "\\n" in js_code or "\\\\n" in js_code  # Newlines escaped

    def test_save_handles_dates(self):
        """Date objects should be serialized to ISO format."""
        from datetime import date, datetime

        test_data = [
            {
                "id": "uuid-123",
                "name": "Test Card",
                "opened_date": date(2024, 6, 15),
                "created_at": datetime(2024, 6, 15, 10, 30, 0),
            }
        ]

        captured_js = []

        def mock_js_eval(js, key):
            captured_js.append(js)
            return True

        with patch('src.core.web_storage._get_js_eval', return_value=mock_js_eval):
            save_to_localstorage(test_data)

        js_code = captured_js[0]

        # Dates should be ISO formatted
        assert "2024-06-15" in js_code


class TestLocalStorageLoad:
    """Test loading from localStorage, including retry logic."""

    def setup_method(self):
        """Reset session state before each test."""
        mock_st.session_state.clear()

    def test_load_success_on_first_try(self):
        """When JS eval returns data immediately, it should be loaded."""
        test_cards = [{"id": "1", "name": "Card 1"}]

        def mock_js_eval(js, key):
            return test_cards

        mock_st.toast = MagicMock()

        with patch('src.core.web_storage._get_js_eval', return_value=mock_js_eval):
            init_web_storage()

        assert mock_st.session_state['cards_data'] == test_cards
        assert mock_st.session_state['storage_initialized'] == True

    def test_load_handles_empty_storage(self):
        """Empty localStorage should result in empty list."""
        def mock_js_eval(js, key):
            return []  # Empty storage

        mock_st.toast = MagicMock()

        with patch('src.core.web_storage._get_js_eval', return_value=mock_js_eval):
            init_web_storage()

        assert mock_st.session_state['cards_data'] == []
        assert mock_st.session_state['storage_initialized'] == True

    def test_load_retries_on_none(self):
        """When JS eval returns None, should increment retry counter."""
        call_count = [0]

        def mock_js_eval(js, key):
            call_count[0] += 1
            return None  # Simulate timing issue

        mock_st.toast = MagicMock()

        with patch('src.core.web_storage._get_js_eval', return_value=mock_js_eval):
            init_web_storage()

        # Should have incremented retry counter
        assert mock_st.session_state['storage_load_attempts'] == 1
        # Should NOT be marked as initialized (to allow retry)
        assert mock_st.session_state['storage_initialized'] == False

    def test_load_gives_up_after_max_retries(self):
        """After max retries, should mark as initialized to prevent infinite loop."""
        mock_st.session_state['storage_load_attempts'] = 3  # Already at max
        mock_st.session_state['storage_initialized'] = False

        def mock_js_eval(js, key):
            return None

        mock_st.toast = MagicMock()

        with patch('src.core.web_storage._get_js_eval', return_value=mock_js_eval):
            init_web_storage()

        # Should be marked as initialized now (gave up)
        assert mock_st.session_state['storage_initialized'] == True


class TestEndToEndPersistence:
    """End-to-end tests simulating real user workflows."""

    def setup_method(self):
        """Reset session state before each test."""
        mock_st.session_state.clear()
        mock_st.session_state['cards_data'] = []
        mock_st.session_state['storage_initialized'] = True
        mock_st.toast = MagicMock()

    def test_add_then_read_workflow(self):
        """User adds a card, then reads it - should work within same session."""
        storage = WebStorage()

        from src.core.library import CardTemplate

        template = CardTemplate(
            id="amex_plat",
            name="American Express Platinum",
            issuer="American Express",
            annual_fee=695,
            credits=[],
        )

        with patch('src.core.web_storage._get_js_eval', return_value=None):
            # Add card
            card = storage.add_card_from_template(template=template)

            # Immediately read - should find the card
            cards = storage.get_all_cards()

        assert len(cards) == 1
        assert cards[0].name == "American Express Platinum"
        assert cards[0].id == card.id

    def test_add_multiple_then_filter(self):
        """Add multiple cards, then filter by issuer."""
        storage = WebStorage()

        from src.core.library import CardTemplate

        templates = [
            CardTemplate(id="amex1", name="Amex Gold", issuer="American Express", annual_fee=250, credits=[]),
            CardTemplate(id="amex2", name="Amex Platinum", issuer="American Express", annual_fee=695, credits=[]),
            CardTemplate(id="chase1", name="Chase Sapphire", issuer="Chase", annual_fee=550, credits=[]),
        ]

        with patch('src.core.web_storage._get_js_eval', return_value=None):
            for template in templates:
                storage.add_card_from_template(template=template)

            all_cards = storage.get_all_cards()
            amex_cards = [c for c in all_cards if c.issuer == "American Express"]

        assert len(all_cards) == 3
        assert len(amex_cards) == 2

    def test_add_update_delete_workflow(self):
        """Full CRUD workflow."""
        storage = WebStorage()

        from src.core.library import CardTemplate

        template = CardTemplate(
            id="test",
            name="Test Card",
            issuer="Test Bank",
            annual_fee=0,
            credits=[],
        )

        with patch('src.core.web_storage._get_js_eval', return_value=None):
            # Create
            card = storage.add_card_from_template(template=template)
            assert len(storage.get_all_cards()) == 1

            # Update
            updated = storage.update_card(card.id, {"nickname": "My Test Card"})
            assert updated.nickname == "My Test Card"

            # Verify update persisted
            cards = storage.get_all_cards()
            assert cards[0].nickname == "My Test Card"

            # Delete
            deleted = storage.delete_card(card.id)
            assert deleted == True
            assert len(storage.get_all_cards()) == 0

    def test_simulated_page_refresh(self):
        """Simulate what happens on page refresh."""
        # First session - user adds card
        mock_st.session_state.clear()
        mock_st.session_state['cards_data'] = []
        mock_st.session_state['storage_initialized'] = True

        storage1 = WebStorage()

        from src.core.library import CardTemplate
        template = CardTemplate(
            id="test",
            name="Test Card",
            issuer="Test Bank",
            annual_fee=0,
            credits=[],
        )

        saved_to_localstorage = []

        def mock_save_js_eval(js, key):
            # Extract the data that would be saved
            if 'localStorage.setItem' in js:
                # The data is embedded in the JS
                saved_to_localstorage.append(mock_st.session_state['cards_data'].copy())
            return True

        with patch('src.core.web_storage._get_js_eval', return_value=mock_save_js_eval):
            storage1.add_card_from_template(template=template)

        # Verify save was attempted
        assert len(saved_to_localstorage) == 1
        saved_data = saved_to_localstorage[0]

        # Second session - simulate page refresh
        mock_st.session_state.clear()

        def mock_load_js_eval(js, key):
            # Return the saved data
            if 'localStorage.getItem' in js:
                return saved_data
            return True

        mock_st.toast = MagicMock()

        with patch('src.core.web_storage._get_js_eval', return_value=mock_load_js_eval):
            init_web_storage()

        # Data should be loaded from "localStorage"
        assert mock_st.session_state['cards_data'] == saved_data

        # Create new storage instance and verify
        storage2 = WebStorage()
        cards = storage2.get_all_cards()
        assert len(cards) == 1
        assert cards[0].name == "Test Card"


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    def setup_method(self):
        """Reset session state before each test."""
        mock_st.session_state.clear()
        mock_st.session_state['cards_data'] = []
        mock_st.session_state['storage_initialized'] = True

    def test_empty_storage_operations(self):
        """Operations on empty storage should not crash."""
        storage = WebStorage()

        with patch('src.core.web_storage._get_js_eval', return_value=None):
            # Get from empty
            cards = storage.get_all_cards()
            assert cards == []

            # Get specific card from empty
            card = storage.get_card("nonexistent")
            assert card is None

            # Delete from empty
            deleted = storage.delete_card("nonexistent")
            assert deleted == False

    def test_concurrent_add_operations(self):
        """Multiple rapid add operations should all succeed."""
        storage = WebStorage()

        from src.core.library import CardTemplate

        with patch('src.core.web_storage._get_js_eval', return_value=None):
            # Rapid adds
            for i in range(10):
                template = CardTemplate(
                    id=f"card_{i}",
                    name=f"Card {i}",
                    issuer="Bank",
                    annual_fee=i * 100,
                    credits=[],
                )
                storage.add_card_from_template(template=template)

        cards = storage.get_all_cards()
        assert len(cards) == 10

        # Verify all unique IDs
        ids = [c.id for c in cards]
        assert len(set(ids)) == 10

    def test_update_nonexistent_card(self):
        """Updating a card that doesn't exist should return None."""
        storage = WebStorage()

        with patch('src.core.web_storage._get_js_eval', return_value=None):
            result = storage.update_card("fake-id", {"nickname": "test"})

        assert result is None

    def test_import_replaces_existing(self):
        """Import should replace all existing data."""
        mock_st.session_state['cards_data'] = [
            {"id": "old1", "name": "Old Card 1"},
            {"id": "old2", "name": "Old Card 2"},
        ]

        storage = WebStorage()

        new_data = json.dumps([
            {"id": "new1", "name": "New Card 1", "issuer": "Bank", "annual_fee": 0, "credits": [], "created_at": "2024-01-01T00:00:00"},
        ])

        with patch('src.core.web_storage._get_js_eval', return_value=None):
            count = storage.import_data(new_data)

        assert count == 1
        assert len(mock_st.session_state['cards_data']) == 1
        assert mock_st.session_state['cards_data'][0]['name'] == "New Card 1"
