"""Browser-only storage for ChurnPilot web deployment.

This is the CORRECT approach for web apps with pilot users:
- Data stored in user's browser (localStorage)
- Each user has isolated data
- Works on mobile, desktop, tablet
- Survives app redeployments
- No server-side files needed
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
    """Initialize web storage - load data from browser localStorage ONLY.

    This is the correct approach for web deployment with pilot users.
    Data must be in the browser, not on the server.
    """
    # Initialize session state variables
    if "cards_data" not in st.session_state:
        st.session_state.cards_data = []
    if "storage_initialized" not in st.session_state:
        st.session_state.storage_initialized = False
    if "storage_load_attempted" not in st.session_state:
        st.session_state.storage_load_attempted = False

    # Only try to load once per session, but track if we got actual data
    if not st.session_state.storage_load_attempted:
        st.session_state.storage_load_attempted = True

        try:
            # Import here to avoid failure if not installed
            from streamlit_js_eval import streamlit_js_eval

            # Use a more reliable approach with longer timeout
            # Also distinguish between "no data" and "failed to load"
            js_code = f"""
            (function() {{
                return new Promise((resolve) => {{
                    // Wait a bit for storage to be available
                    setTimeout(() => {{
                        try {{
                            const data = localStorage.getItem('{STORAGE_KEY}');
                            console.log('[ChurnPilot] Loading from localStorage...');
                            if (data) {{
                                const parsed = JSON.parse(data);
                                console.log('[ChurnPilot] Loaded', parsed.length, 'cards');
                                resolve({{status: 'loaded', data: parsed}});
                            }} else {{
                                console.log('[ChurnPilot] No data in localStorage');
                                resolve({{status: 'empty', data: null}});
                            }}
                        }} catch (e) {{
                            console.error('[ChurnPilot] Load error:', e);
                            resolve({{status: 'error', error: e.message}});
                        }}
                    }}, 150);  // Slightly longer timeout for reliability
                }});
            }})()
            """

            # Add a unique timestamp to force new evaluation each time
            import time
            result = streamlit_js_eval(js=js_code, key=f"load_storage_{int(time.time())}")

            if result and isinstance(result, dict):
                status = result.get('status')

                if status == 'loaded' and result.get('data'):
                    st.session_state.cards_data = result['data']
                    st.session_state.storage_initialized = True
                    st.toast(f"📱 Loaded {len(result['data'])} cards from browser")
                elif status == 'empty':
                    # Truly empty localStorage - this is fine
                    st.session_state.storage_initialized = True
                    st.info("👋 No saved data - starting fresh")
                elif status == 'error':
                    # Error reading localStorage
                    st.warning(f"⚠️ localStorage error: {result.get('error', 'Unknown')}")
                    st.session_state.storage_initialized = True
            else:
                # streamlit_js_eval returned None - timing issue
                # Don't mark as initialized, will retry on next interaction
                st.warning("⚠️ Still loading... Please refresh if data doesn't appear")

        except ImportError:
            st.error("❌ streamlit-js-eval not installed. Install it for data persistence:\n\n`pip install streamlit-js-eval pyarrow`")
            st.session_state.storage_initialized = True
        except Exception as e:
            st.warning(f"⚠️ Could not load from browser storage: {e}")
            st.session_state.storage_initialized = True


def save_web(cards_data: list[dict]):
    """Save to browser localStorage ONLY.

    This is the correct approach - data stays in user's browser.
    """
    # Update session state
    st.session_state.cards_data = cards_data

    try:
        from streamlit_js_eval import streamlit_js_eval

        # Serialize data
        cards_json = json.dumps(_serialize_for_json(cards_data))

        # Escape for JavaScript string
        cards_json_escaped = cards_json.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')

        js_code = f"""
        (function() {{
            try {{
                const dataStr = '{cards_json_escaped}';
                localStorage.setItem('{STORAGE_KEY}', dataStr);

                // Verify it was saved
                const saved = localStorage.getItem('{STORAGE_KEY}');
                if (saved) {{
                    const parsed = JSON.parse(saved);
                    console.log('[ChurnPilot] Saved', parsed.length, 'cards');
                    return {{success: true, count: parsed.length}};
                }} else {{
                    console.error('[ChurnPilot] Save verification failed');
                    return {{success: false, error: 'Verification failed'}};
                }}
            }} catch (e) {{
                console.error('[ChurnPilot] Save error:', e);
                return {{success: false, error: e.message}};
            }}
        }})()
        """

        # Use unique key each time to avoid caching
        import time
        result = streamlit_js_eval(js=js_code, key=f"save_storage_{len(cards_data)}_{int(time.time())}")

        if result and result.get('success'):
            # Success - data saved
            pass
        elif result:
            st.warning(f"⚠️ Save may have failed: {result.get('error')}")

    except ImportError:
        st.error("❌ Cannot save - streamlit-js-eval not installed")
    except Exception as e:
        st.error(f"❌ Save failed: {e}")


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

        cards = self._load_cards()
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

        cards = self._load_cards()
        cards.append(card.model_dump())
        self._save_cards(cards)

        return card

    def update_card(self, card_id: str, updates: dict) -> Card | None:
        """Update an existing card."""
        cards = self._load_cards()
        serialized_updates = _serialize_for_json(updates)

        for i, card_data in enumerate(cards):
            if card_data.get("id") == card_id:
                cards[i].update(serialized_updates)
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
