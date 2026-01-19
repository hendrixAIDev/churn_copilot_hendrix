"""Browser-only storage for ChurnPilot web deployment.

Simplified Architecture:
- Session state is the primary data source during the app session
- localStorage provides persistence across browser sessions
- Save immediately on any data change (no deferred sync)
- Load once at startup
"""

import json
import uuid
from datetime import date, datetime

import streamlit as st
from pydantic import BaseModel

from .exceptions import StorageError
from .models import Card, CardData, SignupBonus
from .library import CardTemplate
from .normalize import normalize_issuer, match_to_library_template


STORAGE_KEY = 'churnpilot_cards'


def _serialize_for_json(obj):
    """Recursively convert Pydantic models and other types for JSON serialization."""
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    elif isinstance(obj, dict):
        return {k: _serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialize_for_json(item) for item in obj]
    elif isinstance(obj, (date, datetime)):
        return obj.isoformat()
    else:
        return obj


def _get_js_eval_available():
    """Check if streamlit_js_eval is available."""
    try:
        from streamlit_js_eval import get_local_storage, set_local_storage
        return True
    except ImportError:
        return False


def _save_to_browser(cards_data: list[dict]) -> bool:
    """Save data directly to browser localStorage.

    Returns True if save was successful.
    """
    if not _get_js_eval_available():
        return False

    try:
        from streamlit_js_eval import set_local_storage

        # Serialize to JSON
        json_str = json.dumps(_serialize_for_json(cards_data))

        # Use incrementing key to force component re-render
        if "_save_counter" not in st.session_state:
            st.session_state._save_counter = 0
        st.session_state._save_counter += 1

        set_local_storage(
            STORAGE_KEY,
            json_str,
            component_key=f"save_{st.session_state._save_counter}"
        )

        print(f"[Storage] Saved {len(cards_data)} cards to localStorage")
        return True

    except Exception as e:
        print(f"[Storage] Save error: {e}")
        return False


def _load_from_browser() -> list[dict] | None:
    """Load data from browser localStorage.

    Returns list of card dicts, or None if not available yet.
    """
    if not _get_js_eval_available():
        return None

    try:
        from streamlit_js_eval import get_local_storage

        # Use stable key for consistent loading
        result = get_local_storage(STORAGE_KEY, component_key="load_stable")

        if result is None:
            return None

        # Parse JSON
        if isinstance(result, str):
            data = json.loads(result) if result else []
        else:
            data = result

        if isinstance(data, list):
            print(f"[Storage] Loaded {len(data)} cards from localStorage")
            return data

        return []

    except Exception as e:
        print(f"[Storage] Load error: {e}")
        return None


def init_web_storage():
    """Initialize web storage - called once at app startup.

    This sets up session state and attempts to load from localStorage.
    Due to Streamlit's rendering model, the first few calls may not
    have data available - this is handled gracefully.
    """
    # Initialize session state
    if "cards_data" not in st.session_state:
        st.session_state.cards_data = []

    if "storage_ready" not in st.session_state:
        st.session_state.storage_ready = False

    if "load_attempts" not in st.session_state:
        st.session_state.load_attempts = 0

    # Already loaded? Skip.
    if st.session_state.storage_ready:
        return

    # Check for js_eval
    if not _get_js_eval_available():
        st.error("Install streamlit-js-eval: `pip install streamlit-js-eval pyarrow`")
        st.session_state.storage_ready = True
        return

    # Try to load from browser
    data = _load_from_browser()

    if data is not None:
        # Got data (could be empty list)
        st.session_state.cards_data = data
        st.session_state.storage_ready = True
        if data:
            st.toast(f"Loaded {len(data)} cards", icon="📱")
    else:
        # Data not available yet - retry a few times
        st.session_state.load_attempts += 1

        if st.session_state.load_attempts < 5:
            # Retry
            import time
            time.sleep(0.05)
            st.rerun()
        else:
            # Give up - assume empty
            st.session_state.storage_ready = True
            print("[Storage] No data after 5 attempts, starting fresh")


def sync_to_localstorage():
    """Sync current session state to localStorage.

    Called at the end of each render to persist any changes.
    """
    if "cards_data" in st.session_state and st.session_state.get("_needs_save"):
        _save_to_browser(st.session_state.cards_data)
        st.session_state._needs_save = False


class WebStorage:
    """Browser localStorage-based storage for web deployment.

    Simple API:
    - get_all_cards() -> list[Card]
    - add_card_from_template(template, ...) -> Card
    - update_card(card_id, updates) -> Card
    - delete_card(card_id) -> bool
    """

    def __init__(self):
        """Initialize storage."""
        if "cards_data" not in st.session_state:
            st.session_state.cards_data = []

    def _get_data(self) -> list[dict]:
        """Get current card data from session state."""
        return st.session_state.cards_data

    def _set_data(self, data: list[dict]):
        """Set card data and save to browser."""
        st.session_state.cards_data = data
        st.session_state._needs_save = True
        # Save immediately
        _save_to_browser(data)

    def get_all_cards(self) -> list[Card]:
        """Get all stored cards."""
        cards = []
        for i, c in enumerate(self._get_data()):
            try:
                # Handle data migration issues
                if isinstance(c.get("credit_usage"), list):
                    c["credit_usage"] = {}
                if isinstance(c.get("retention_offers"), dict):
                    c["retention_offers"] = []

                cards.append(Card.model_validate(c))
            except Exception as e:
                print(f"[Storage] Invalid card {i}: {e}")
        return cards

    def get_card(self, card_id: str) -> Card | None:
        """Get a card by ID."""
        for c in self._get_data():
            if c.get("id") == card_id:
                try:
                    return Card.model_validate(c)
                except:
                    return None
        return None

    def add_card(
        self,
        card_data: CardData,
        opened_date: date | None = None,
        raw_text: str | None = None,
    ) -> Card:
        """Add a card from extracted data."""
        card = Card(
            id=str(uuid.uuid4()),
            name=card_data.name,
            issuer=normalize_issuer(card_data.issuer),
            annual_fee=card_data.annual_fee,
            signup_bonus=card_data.signup_bonus,
            credits=card_data.credits,
            opened_date=opened_date,
            raw_text=raw_text,
            template_id=match_to_library_template(
                card_data.name,
                normalize_issuer(card_data.issuer)
            ),
            created_at=datetime.now(),
        )

        data = list(self._get_data())
        data.append(card.model_dump())
        self._set_data(data)

        return card

    def add_card_from_template(
        self,
        template: CardTemplate,
        nickname: str | None = None,
        opened_date: date | None = None,
        signup_bonus: SignupBonus | None = None,
    ) -> Card:
        """Add a card from a library template."""
        card = Card(
            id=str(uuid.uuid4()),
            name=template.name,
            nickname=nickname,
            issuer=template.issuer,
            annual_fee=template.annual_fee,
            signup_bonus=signup_bonus,
            credits=template.credits,
            opened_date=opened_date,
            template_id=template.id,
            created_at=datetime.now(),
        )

        data = list(self._get_data())
        data.append(card.model_dump())
        self._set_data(data)

        return card

    def update_card(self, card_id: str, updates: dict) -> Card | None:
        """Update a card by ID."""
        data = list(self._get_data())
        updates = _serialize_for_json(updates)

        for i, c in enumerate(data):
            if c.get("id") == card_id:
                data[i] = {**c, **updates}
                self._set_data(data)
                try:
                    return Card.model_validate(data[i])
                except:
                    return None

        return None

    def delete_card(self, card_id: str) -> bool:
        """Delete a card by ID."""
        data = self._get_data()
        new_data = [c for c in data if c.get("id") != card_id]

        if len(new_data) < len(data):
            self._set_data(new_data)
            return True

        return False

    def export_data(self) -> str:
        """Export all data as JSON."""
        return json.dumps(_serialize_for_json(self._get_data()), indent=2)

    def import_data(self, json_data: str) -> int:
        """Import data from JSON, replacing existing."""
        try:
            data = json.loads(json_data)
            if not isinstance(data, list):
                raise ValueError("Must be a JSON array")

            self._set_data(data)
            return len(data)
        except json.JSONDecodeError as e:
            raise StorageError(f"Invalid JSON: {e}")
        except Exception as e:
            raise StorageError(f"Import failed: {e}")


# Legacy aliases for compatibility
def save_web(cards_data: list[dict]):
    """Legacy: Save data (updates session state and browser)."""
    st.session_state.cards_data = cards_data
    st.session_state._needs_save = True
    _save_to_browser(cards_data)
