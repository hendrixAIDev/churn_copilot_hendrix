"""Tests for WebStorage (browser localStorage-only storage)."""

import json
from datetime import date, datetime
from unittest.mock import Mock, patch, MagicMock

import pytest
from pydantic import ValidationError

from src.core.web_storage import WebStorage, _serialize_for_json, init_web_storage, save_web
from src.core.models import Card, CardData, SignupBonus, Credit
from src.core.library import get_template
from src.core.exceptions import StorageError


class MockSessionState:
    """Mock for Streamlit session state that persists values."""
    def __init__(self):
        self._data = {'cards_data': [], 'storage_initialized': False}

    def __contains__(self, key):
        return key in self._data

    def __getattr__(self, key):
        if key.startswith('_'):
            return object.__getattribute__(self, key)
        return self._data.get(key)

    def __setattr__(self, key, value):
        if key.startswith('_'):
            object.__setattr__(self, key, value)
        else:
            self._data[key] = value


@pytest.fixture
def mock_streamlit():
    """Mock Streamlit session state."""
    with patch('src.core.web_storage.st') as mock_st:
        mock_st.session_state = MockSessionState()
        mock_st.toast = Mock()
        mock_st.info = Mock()
        mock_st.warning = Mock()
        mock_st.error = Mock()
        yield mock_st


@pytest.fixture
def mock_js_eval():
    """Mock streamlit_js_eval."""
    with patch('src.core.web_storage.streamlit_js_eval') as mock:
        yield mock


@pytest.fixture
def sample_card_data():
    """Sample card data for testing."""
    return CardData(
        name="Chase Sapphire Preferred",
        issuer="Chase",
        annual_fee=95,
        signup_bonus=SignupBonus(
            points_or_cash="60,000 points",
            spend_requirement=4000,
            time_period_days=90
        ),
        credits=[]
    )


@pytest.fixture
def sample_card_dict():
    """Sample card as dictionary."""
    return {
        "id": "test-id-123",
        "name": "Chase Sapphire Preferred",
        "issuer": "Chase",
        "annual_fee": 95,
        "signup_bonus": {
            "points_or_cash": "60,000 points",
            "spend_requirement": 4000,
            "time_period_days": 90,
            "deadline": None
        },
        "credits": [],
        "opened_date": "2024-01-15",
        "created_at": "2024-01-15T10:30:00",
        "template_id": None,
        "nickname": None,
        "raw_text": None,
        "credit_usage": {},
        "annual_fee_date": None,
        "notes": None,
        "retention_offers": [],
        "product_changes": [],
        "status": "active"
    }


class TestSerializeForJson:
    """Test JSON serialization helper."""

    def test_serialize_pydantic_model(self, sample_card_data):
        """Test serializing Pydantic model."""
        result = _serialize_for_json(sample_card_data)
        assert isinstance(result, dict)
        assert result["name"] == "Chase Sapphire Preferred"
        assert result["annual_fee"] == 95

    def test_serialize_dict(self):
        """Test serializing dictionary."""
        data = {"key": "value", "number": 42}
        result = _serialize_for_json(data)
        assert result == data

    def test_serialize_list(self, sample_card_data):
        """Test serializing list of models."""
        data = [sample_card_data, sample_card_data]
        result = _serialize_for_json(data)
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(item, dict) for item in result)

    def test_serialize_date(self):
        """Test serializing date objects."""
        test_date = date(2024, 1, 15)
        result = _serialize_for_json(test_date)
        assert result == "2024-01-15"

    def test_serialize_datetime(self):
        """Test serializing datetime objects."""
        test_datetime = datetime(2024, 1, 15, 10, 30, 0)
        result = _serialize_for_json(test_datetime)
        assert result.startswith("2024-01-15T10:30:00")

    def test_serialize_nested(self, sample_card_data):
        """Test serializing nested structures."""
        data = {
            "cards": [sample_card_data],
            "metadata": {
                "created": date(2024, 1, 15),
                "count": 1
            }
        }
        result = _serialize_for_json(data)
        assert isinstance(result["cards"][0], dict)
        assert result["metadata"]["created"] == "2024-01-15"


class TestWebStorage:
    """Test WebStorage class."""

    def test_init_storage(self, mock_streamlit):
        """Test storage initialization."""
        storage = WebStorage()
        assert isinstance(storage, WebStorage)

    def test_get_all_cards_empty(self, mock_streamlit):
        """Test getting all cards when none exist."""
        storage = WebStorage()
        cards = storage.get_all_cards()
        assert cards == []

    def test_get_all_cards(self, mock_streamlit, sample_card_dict):
        """Test getting all cards."""
        mock_streamlit.session_state.cards_data = [sample_card_dict]

        storage = WebStorage()
        cards = storage.get_all_cards()

        assert len(cards) == 1
        assert isinstance(cards[0], Card)
        assert cards[0].name == "Chase Sapphire Preferred"

    def test_get_card_found(self, mock_streamlit, sample_card_dict):
        """Test getting a specific card by ID."""
        mock_streamlit.session_state.cards_data = [sample_card_dict]

        storage = WebStorage()
        card = storage.get_card("test-id-123")

        assert card is not None
        assert card.id == "test-id-123"
        assert card.name == "Chase Sapphire Preferred"

    def test_get_card_not_found(self, mock_streamlit):
        """Test getting a card that doesn't exist."""
        storage = WebStorage()
        card = storage.get_card("nonexistent-id")
        assert card is None

    def test_add_card(self, mock_streamlit, sample_card_data):
        """Test adding a new card."""
        # Mock the save function to avoid JS eval
        with patch('src.core.web_storage.save_web') as mock_save:
            storage = WebStorage()
            card = storage.add_card(
                card_data=sample_card_data,
                opened_date=date(2024, 1, 15)
            )

            assert card.name == "Chase Sapphire Preferred"
            assert card.issuer == "Chase"
            assert card.opened_date == date(2024, 1, 15)
            assert mock_save.called

    def test_add_card_from_template(self, mock_streamlit):
        """Test adding a card from template."""
        template = get_template("amex_platinum")

        with patch('src.core.web_storage.save_web') as mock_save:
            storage = WebStorage()

            card = storage.add_card_from_template(
                template=template,
                nickname="My Platinum",
                opened_date=date(2024, 1, 15),
                signup_bonus=SignupBonus(
                    points_or_cash="80,000 points",
                    spend_requirement=8000,
                    time_period_days=180
                )
            )

            assert card.name == "American Express Platinum"
            assert card.nickname == "My Platinum"
            assert card.issuer == "American Express"
            assert card.annual_fee == 895
            assert len(card.credits) > 0
            assert mock_save.called

    def test_update_card(self, mock_streamlit, sample_card_dict):
        """Test updating a card."""
        mock_streamlit.session_state.cards_data = [sample_card_dict]

        with patch('src.core.web_storage.save_web') as mock_save:
            storage = WebStorage()
            updated_card = storage.update_card(
                "test-id-123",
                {"annual_fee": 125}
            )

            assert updated_card is not None
            assert updated_card.annual_fee == 125
            assert mock_save.called

    def test_update_card_not_found(self, mock_streamlit):
        """Test updating a nonexistent card."""
        with patch('src.core.web_storage.save_web') as mock_save:
            storage = WebStorage()
            updated_card = storage.update_card("nonexistent", {"annual_fee": 125})
            assert updated_card is None
            assert not mock_save.called

    def test_delete_card(self, mock_streamlit, sample_card_dict):
        """Test deleting a card."""
        mock_streamlit.session_state.cards_data = [sample_card_dict]

        with patch('src.core.web_storage.save_web') as mock_save:
            storage = WebStorage()
            result = storage.delete_card("test-id-123")

            assert result is True
            assert mock_save.called

    def test_delete_card_not_found(self, mock_streamlit):
        """Test deleting a nonexistent card."""
        with patch('src.core.web_storage.save_web') as mock_save:
            storage = WebStorage()
            result = storage.delete_card("nonexistent")
            assert result is False
            assert not mock_save.called

    def test_export_data(self, mock_streamlit, sample_card_dict):
        """Test exporting data as JSON."""
        mock_streamlit.session_state.cards_data = [sample_card_dict]

        storage = WebStorage()
        exported = storage.export_data()

        assert isinstance(exported, str)
        data = json.loads(exported)
        assert len(data) == 1
        assert data[0]["name"] == "Chase Sapphire Preferred"

    def test_import_data(self, mock_streamlit, sample_card_dict):
        """Test importing data from JSON."""
        with patch('src.core.web_storage.save_web') as mock_save:
            storage = WebStorage()
            json_data = json.dumps([sample_card_dict])

            count = storage.import_data(json_data)

            assert count == 1
            assert mock_save.called

    def test_import_data_invalid_json(self, mock_streamlit):
        """Test importing invalid JSON."""
        storage = WebStorage()

        with pytest.raises(StorageError, match="Invalid JSON"):
            storage.import_data("not valid json")

    def test_import_data_not_array(self, mock_streamlit):
        """Test importing JSON that's not an array."""
        storage = WebStorage()

        with pytest.raises(StorageError, match="must be a JSON array"):
            storage.import_data('{"key": "value"}')


class TestWebStorageIntegration:
    """Integration tests for WebStorage."""

    def _mock_save_web(self, mock_streamlit):
        """Create a mock save_web that actually updates session state."""
        def save_side_effect(cards_data):
            mock_streamlit.session_state.cards_data = cards_data
        return save_side_effect

    def test_add_multiple_cards(self, mock_streamlit, sample_card_data):
        """Test adding multiple cards."""
        with patch('src.core.web_storage.save_web', side_effect=self._mock_save_web(mock_streamlit)):
            storage = WebStorage()

            card1 = storage.add_card(sample_card_data, opened_date=date(2024, 1, 15))
            card2 = storage.add_card(sample_card_data, opened_date=date(2024, 2, 20))

            assert card1.id != card2.id
            assert len(storage.get_all_cards()) == 2

    def test_update_then_retrieve(self, mock_streamlit, sample_card_data):
        """Test updating a card and retrieving it."""
        with patch('src.core.web_storage.save_web', side_effect=self._mock_save_web(mock_streamlit)):
            storage = WebStorage()

            # Add card
            card = storage.add_card(sample_card_data)

            # Update it
            storage.update_card(card.id, {"annual_fee": 200})

            # Retrieve and verify
            updated = storage.get_card(card.id)
            assert updated.annual_fee == 200

    def test_delete_then_retrieve(self, mock_streamlit, sample_card_data):
        """Test deleting a card and verifying it's gone."""
        with patch('src.core.web_storage.save_web', side_effect=self._mock_save_web(mock_streamlit)):
            storage = WebStorage()

            # Add card
            card = storage.add_card(sample_card_data)
            assert len(storage.get_all_cards()) == 1

            # Delete it
            storage.delete_card(card.id)

            # Try to retrieve
            deleted = storage.get_card(card.id)
            assert deleted is None
            assert len(storage.get_all_cards()) == 0

    def test_export_import_roundtrip(self, mock_streamlit, sample_card_data):
        """Test exporting and re-importing data."""
        with patch('src.core.web_storage.save_web', side_effect=self._mock_save_web(mock_streamlit)):
            storage = WebStorage()

            # Add some cards
            storage.add_card(sample_card_data, opened_date=date(2024, 1, 15))
            storage.add_card(sample_card_data, opened_date=date(2024, 2, 20))

            # Export
            exported = storage.export_data()

            # Clear storage
            mock_streamlit.session_state.cards_data = []

            # Import
            count = storage.import_data(exported)

            assert count == 2
            assert len(storage.get_all_cards()) == 2


class TestUserJourneys:
    """Test critical user journey scenarios."""

    def _mock_save_web(self, mock_streamlit):
        """Create a mock save_web that actually updates session state."""
        def save_side_effect(cards_data):
            mock_streamlit.session_state.cards_data = cards_data
        return save_side_effect

    def test_add_card_from_library_journey(self, mock_streamlit):
        """Test: User adds card from library."""
        template = get_template("amex_platinum")

        with patch('src.core.web_storage.save_web', side_effect=self._mock_save_web(mock_streamlit)):
            storage = WebStorage()

            # Step 1: User selects template and adds card
            card = storage.add_card_from_template(
                template=template,
                nickname="My Platinum Card",
                opened_date=date(2024, 1, 15),
                signup_bonus=SignupBonus(
                    points_or_cash="80,000 points",
                    spend_requirement=8000,
                    time_period_days=180
                )
            )

            # Step 2: Card should be retrievable
            retrieved = storage.get_card(card.id)
            assert retrieved is not None
            assert retrieved.name == "American Express Platinum"
            assert retrieved.nickname == "My Platinum Card"

            # Step 3: Card should appear in all cards
            all_cards = storage.get_all_cards()
            assert len(all_cards) == 1
            assert all_cards[0].id == card.id

    def test_edit_card_journey(self, mock_streamlit, sample_card_dict):
        """Test: User edits an existing card."""
        mock_streamlit.session_state.cards_data = [sample_card_dict]

        with patch('src.core.web_storage.save_web', side_effect=self._mock_save_web(mock_streamlit)):
            storage = WebStorage()

            # Step 1: User retrieves card
            card = storage.get_card("test-id-123")
            assert card.annual_fee == 95

            # Step 2: User updates annual fee
            updated = storage.update_card("test-id-123", {"annual_fee": 125})
            assert updated.annual_fee == 125

            # Step 3: Changes should persist in storage
            retrieved = storage.get_card("test-id-123")
            assert retrieved.annual_fee == 125

    def test_delete_card_journey(self, mock_streamlit, sample_card_dict):
        """Test: User deletes a card."""
        mock_streamlit.session_state.cards_data = [sample_card_dict.copy()]

        with patch('src.core.web_storage.save_web', side_effect=self._mock_save_web(mock_streamlit)):
            storage = WebStorage()

            # Step 1: Verify card exists
            assert storage.get_card("test-id-123") is not None
            assert len(storage.get_all_cards()) == 1

            # Step 2: User deletes card
            result = storage.delete_card("test-id-123")
            assert result is True

            # Step 3: Card should be gone
            assert storage.get_card("test-id-123") is None
            assert len(storage.get_all_cards()) == 0

    def test_import_export_journey(self, mock_streamlit, sample_card_data):
        """Test: User exports data, clears app, then imports."""
        with patch('src.core.web_storage.save_web', side_effect=self._mock_save_web(mock_streamlit)):
            storage = WebStorage()

            # Step 1: User adds cards
            card1 = storage.add_card(sample_card_data, opened_date=date(2024, 1, 15))
            card2 = storage.add_card(sample_card_data, opened_date=date(2024, 2, 20))
            assert len(storage.get_all_cards()) == 2

            # Step 2: User exports data
            exported = storage.export_data()
            assert exported is not None

            # Step 3: Data gets cleared (simulating browser clear)
            mock_streamlit.session_state.cards_data = []
            assert len(storage.get_all_cards()) == 0

            # Step 4: User imports data back
            count = storage.import_data(exported)
            assert count == 2
            assert len(storage.get_all_cards()) == 2

    def test_multiple_cards_management(self, mock_streamlit):
        """Test: User manages multiple cards."""
        templates = [
            get_template("amex_platinum"),
            get_template("chase_sapphire_reserve"),
            get_template("citi_premier"),
        ]

        with patch('src.core.web_storage.save_web', side_effect=self._mock_save_web(mock_streamlit)):
            storage = WebStorage()

            # Add multiple cards
            cards = []
            for template in templates:
                card = storage.add_card_from_template(
                    template=template,
                    opened_date=date(2024, 1, 15)
                )
                cards.append(card)

            # Verify all cards added
            all_cards = storage.get_all_cards()
            assert len(all_cards) == 3

            # Delete one card
            storage.delete_card(cards[1].id)

            # Verify deletion
            all_cards = storage.get_all_cards()
            assert len(all_cards) == 2
            assert cards[1].id not in [c.id for c in all_cards]
