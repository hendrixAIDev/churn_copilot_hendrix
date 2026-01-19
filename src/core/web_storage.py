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

    # Use a unique key per attempt to avoid caching issues
    attempt = st.session_state.storage_load_attempts

    try:
        # Use the library's built-in get_local_storage function
        result_str = get_local_storage(STORAGE_KEY, component_key=f"churnpilot_load_{attempt}")

        # Only process on first successful load
        if not st.session_state.storage_initialized:
            if result_str is not None:
                try:
                    result = json.loads(result_str) if result_str else []
                    if isinstance(result, list):
                        st.session_state.cards_data = result
                        if len(result) > 0:
                            st.toast(f"📱 Loaded {len(result)} cards from browser")
                except json.JSONDecodeError:
                    st.session_state.cards_data = []
                st.session_state.storage_initialized = True
            else:
                # streamlit_js_eval returned None - try again on next rerun
                st.session_state.storage_load_attempts += 1
                if attempt < 3:
                    # Silently retry up to 3 times
                    pass
                else:
                    # Give up after 3 attempts
                    st.session_state.storage_initialized = True

    except Exception as e:
        if not st.session_state.storage_initialized:
            st.warning(f"⚠️ Could not load from browser storage: {e}")
            st.session_state.storage_initialized = True


def save_to_localstorage(cards_data: list[dict]) -> bool:
    """Save data to browser localStorage.

    Uses st.components.v1.html for SYNCHRONOUS JavaScript execution.
    This is critical because streamlit_js_eval components may not execute
    before st.rerun() is called.

    Returns True if save was attempted.
    """
    try:
        from streamlit.components.v1 import html
    except ImportError:
        print("[ChurnPilot] streamlit components not available")
        return False

    try:
        # Serialize data to JSON string
        cards_json = json.dumps(_serialize_for_json(cards_data))

        # Escape for embedding in JavaScript string literal
        # Order matters: backslashes first, then other characters
        escaped_json = (cards_json
            .replace('\\', '\\\\')  # Backslashes
            .replace("'", "\\'")     # Single quotes
            .replace('\n', '\\n')    # Newlines
            .replace('\r', '\\r')    # Carriage returns
            .replace('\t', '\\t')    # Tabs
        )

        # Use HTML component with minimal height (1px ensures JS executes)
        # The JavaScript runs IMMEDIATELY when this component renders
        save_script = f"""
        <script>
        (function() {{
            try {{
                var data = '{escaped_json}';
                localStorage.setItem('{STORAGE_KEY}', data);
                console.log('[ChurnPilot] Saved to localStorage:', data.length, 'bytes');
            }} catch (e) {{
                console.error('[ChurnPilot] Save error:', e);
            }}
        }})();
        </script>
        """

        # height=1 ensures the component renders and JS executes
        # height=0 can cause some browsers to skip JS execution
        html(save_script, height=1)

        print(f"[ChurnPilot] Save script injected, {len(cards_json)} bytes")
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


def sync_to_localstorage():
    """Sync session state to localStorage.

    Call this at the END of the main app render, AFTER all reruns are complete.
    This ensures the JavaScript has time to execute before any page reload.

    IMPORTANT: Only syncs if:
    1. Storage has been successfully initialized (we've loaded from localStorage)
    2. Data has been modified since last sync (_cards_need_sync flag)

    This prevents overwriting localStorage with empty data on page load.
    """
    # Only sync if storage is initialized AND data needs syncing
    if (st.session_state.get("storage_initialized", False) and
            st.session_state.get("_cards_need_sync", False)):
        if "cards_data" in st.session_state:
            save_to_localstorage(st.session_state.cards_data)
            st.session_state._cards_need_sync = False


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
