"""Browser-only storage for ChurnPilot web deployment.

Architecture:
- Data stored in user's browser (localStorage)
- Session state serves as in-memory cache
- All operations update session state FIRST (immediate UI updates)
- localStorage is updated asynchronously for persistence

Key Insight: Streamlit tab rendering order means we must process
operations BEFORE tabs render. This module provides the storage
primitives; the UI layer handles operation timing.
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


def init_web_storage():
    """Initialize web storage - load data from browser localStorage.

    This function:
    1. Initializes session state variables
    2. Attempts to load data from localStorage on first run
    3. Sets up the storage_initialized flag to prevent repeated loads

    IMPORTANT: Due to streamlit_js_eval timing, data may not be available
    on the very first render. The UI should handle this gracefully.
    """
    # Initialize session state variables
    if "cards_data" not in st.session_state:
        st.session_state.cards_data = []
    if "storage_initialized" not in st.session_state:
        st.session_state.storage_initialized = False
    if "storage_load_attempts" not in st.session_state:
        st.session_state.storage_load_attempts = 0

    # Try to load from localStorage
    try:
        from streamlit_js_eval import get_local_storage
    except ImportError:
        if not st.session_state.storage_initialized:
            st.error("❌ streamlit-js-eval not installed. Run: `pip install streamlit-js-eval pyarrow`")
            st.session_state.storage_initialized = True
        return

    # IMPORTANT: Use a STABLE key so the component can return its value
    # on subsequent renders. Changing keys creates new components that
    # haven't had time to execute their JavaScript.
    try:
        # Use the library's built-in get_local_storage function with STABLE key
        result_str = get_local_storage(STORAGE_KEY, component_key="churnpilot_load_stable")

        # Debug logging
        print(f"[ChurnPilot] Load result: type={type(result_str)}, value={str(result_str)[:100] if result_str else 'None'}...")

        # CRITICAL FIX: Always process valid data, even after "giving up"
        # The streamlit_js_eval component often returns data ONE RENDER AFTER
        # we've already given up. So we check for data even if initialized,
        # as long as cards_data is still empty.
        should_process = (
            not st.session_state.storage_initialized or
            (st.session_state.storage_initialized and len(st.session_state.cards_data) == 0)
        )

        if result_str is not None and should_process:
            try:
                result = json.loads(result_str) if result_str else []
                if isinstance(result, list) and len(result) > 0:
                    # Only update if we got actual data
                    st.session_state.cards_data = result
                    print(f"[ChurnPilot] Loaded {len(result)} cards from localStorage")
                    st.toast(f"📱 Loaded {len(result)} cards from browser")
                    st.session_state.storage_initialized = True
                    # CRITICAL: Trigger rerun so Dashboard re-renders with new data
                    # Without this, data arrives after Dashboard has already rendered empty
                    st.rerun()
            except json.JSONDecodeError as e:
                print(f"[ChurnPilot] JSON decode error: {e}")
            st.session_state.storage_initialized = True
        elif result_str is None and not st.session_state.storage_initialized:
            # streamlit_js_eval returned None - component hasn't executed yet
            # This is normal on the first render. The component will execute
            # and the value will be available on the next render.
            st.session_state.storage_load_attempts += 1
            attempt = st.session_state.storage_load_attempts
            print(f"[ChurnPilot] Load returned None, attempt {attempt}/4")
            if attempt < 4:
                # Trigger rerun - the SAME component key will now return its value
                st.rerun()
            else:
                # Give up retrying, but DON'T mark as fully initialized yet
                # The component may still return data on the next natural render
                print("[ChurnPilot] Stopping retries, will check again on next render")
                st.session_state.storage_initialized = True

    except Exception as e:
        print(f"[ChurnPilot] Load exception: {e}")
        if not st.session_state.storage_initialized:
            st.warning(f"⚠️ Could not load from browser storage: {e}")
            st.session_state.storage_initialized = True


def save_to_localstorage(cards_data: list[dict]) -> bool:
    """Save data to browser localStorage.

    Uses streamlit_js_eval's set_local_storage for reliable execution.
    This is more reliable than st.components.v1.html because it's designed
    specifically for localStorage operations and handles timing better.

    Returns True if save was attempted.
    """
    try:
        from streamlit_js_eval import set_local_storage
    except ImportError:
        print("[ChurnPilot] streamlit_js_eval not available for saving")
        return False

    try:
        # Serialize data to JSON string
        cards_json = json.dumps(_serialize_for_json(cards_data))

        # Track save attempts for unique component keys
        if "_save_counter" not in st.session_state:
            st.session_state._save_counter = 0
        st.session_state._save_counter += 1

        # Use set_local_storage from streamlit_js_eval
        # CRITICAL: Use a UNIQUE component_key each time, otherwise Streamlit
        # won't re-render the component and the save won't execute!
        save_key = f"churnpilot_save_{st.session_state._save_counter}"
        set_local_storage(STORAGE_KEY, cards_json, component_key=save_key)

        print(f"[ChurnPilot] Save via set_local_storage (key={save_key}), {len(cards_json)} bytes")
        return True

    except Exception as e:
        print(f"[ChurnPilot] localStorage save error: {e}")
        return False


def save_web(cards_data: list[dict]):
    """Save to browser localStorage.

    ALWAYS updates session state first for immediate UI availability.
    Note: We DON'T call save_to_localstorage here because st.rerun()
    might race with the JavaScript execution. Instead, we rely on
    sync_to_localstorage() being called at the end of each render.
    """
    # ALWAYS update session state first - this ensures the data is
    # available immediately for the current session
    st.session_state.cards_data = cards_data

    # Mark that data has changed and needs syncing
    st.session_state._cards_need_sync = True
    print(f"[ChurnPilot] save_web called, {len(cards_data)} cards, _cards_need_sync=True")


def sync_to_localstorage():
    """Sync session state to localStorage.

    Call this at the END of the main app render, AFTER all reruns are complete.
    This ensures the JavaScript has time to execute before any page reload.

    Sync conditions:
    - If _cards_need_sync is True: ALWAYS sync (user modified data)
    - If storage_initialized is False: DON'T sync (might overwrite with empty)
    """
    need_sync = st.session_state.get("_cards_need_sync", False)
    has_cards = "cards_data" in st.session_state
    cards_count = len(st.session_state.cards_data) if has_cards else 0
    print(f"[ChurnPilot] sync_to_localstorage called: need_sync={need_sync}, has_cards={has_cards}, count={cards_count}")

    # If data was modified, ALWAYS sync regardless of initialization status
    # This handles the case where st.rerun() was called after adding a card
    if need_sync:
        if has_cards:
            save_to_localstorage(st.session_state.cards_data)
            st.session_state._cards_need_sync = False
            print(f"[ChurnPilot] Synced {cards_count} cards to localStorage")


class WebStorage:
    """Browser localStorage-only storage for web deployment.

    This is the CORRECT approach for web apps:
    - Data in user's browser
    - Works on mobile, desktop, tablet
    - Each user has isolated data
    - No server-side files
    """

    def __init__(self):
        """Initialize web storage."""
        if "cards_data" not in st.session_state:
            st.session_state.cards_data = []

    def _load_cards(self) -> list[dict]:
        """Load raw card data from session state (synced with browser)."""
        return st.session_state.cards_data

    def _save_cards(self, cards: list[dict]) -> None:
        """Save raw card data to browser localStorage."""
        save_web(cards)

    def get_all_cards(self) -> list[Card]:
        """Retrieve all stored cards."""
        raw_cards = self._load_cards()
        return [Card.model_validate(c) for c in raw_cards]

    def get_card(self, card_id: str) -> Card | None:
        """Retrieve a single card by ID."""
        cards = self._load_cards()
        for card_data in cards:
            if card_data.get("id") == card_id:
                return Card(**card_data)
        return None

    def add_card(
        self,
        card_data: CardData,
        opened_date: date | None = None,
        raw_text: str | None = None,
    ) -> Card:
        """Add a new card from extracted data."""
        normalized_issuer = normalize_issuer(card_data.issuer)
        template_id = match_to_library_template(card_data.name, normalized_issuer)

        card = Card(
            id=str(uuid.uuid4()),
            name=card_data.name,
            issuer=normalized_issuer,
            annual_fee=card_data.annual_fee,
            signup_bonus=card_data.signup_bonus,
            credits=card_data.credits,
            opened_date=opened_date,
            raw_text=raw_text,
            template_id=template_id,
            created_at=datetime.now(),
        )

        # Make a copy to avoid mutation issues
        cards = list(self._load_cards())
        cards.append(card.model_dump())
        self._save_cards(cards)

        return card

    def add_card_from_template(
        self,
        template: CardTemplate,
        nickname: str | None = None,
        opened_date: date | None = None,
        signup_bonus: SignupBonus | None = None,
    ) -> Card:
        """Add a new card from a library template."""
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

        # Make a copy to avoid mutation issues
        cards = list(self._load_cards())
        cards.append(card.model_dump())
        self._save_cards(cards)

        return card

    def update_card(self, card_id: str, updates: dict) -> Card | None:
        """Update an existing card."""
        cards = list(self._load_cards())  # Copy
        serialized_updates = _serialize_for_json(updates)

        for i, card_data in enumerate(cards):
            if card_data.get("id") == card_id:
                cards[i] = {**card_data, **serialized_updates}
                self._save_cards(cards)
                return Card.model_validate(cards[i])

        return None

    def delete_card(self, card_id: str) -> bool:
        """Delete a card by ID."""
        cards = self._load_cards()
        original_len = len(cards)

        cards = [c for c in cards if c.get("id") != card_id]

        if len(cards) < original_len:
            self._save_cards(cards)
            return True

        return False

    def export_data(self) -> str:
        """Export all data as JSON string."""
        cards = self._load_cards()
        return json.dumps(_serialize_for_json(cards), indent=2)

    def import_data(self, json_data: str) -> int:
        """Import data from JSON string, replacing existing data."""
        try:
            cards = json.loads(json_data)
            if not isinstance(cards, list):
                raise ValueError("Import data must be a JSON array")

            self._save_cards(cards)
            return len(cards)
        except json.JSONDecodeError as e:
            raise StorageError(f"Invalid JSON: {e}")
        except Exception as e:
            raise StorageError(f"Import failed: {e}")
