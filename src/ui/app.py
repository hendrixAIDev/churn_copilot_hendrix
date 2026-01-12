"""Streamlit UI for ChurnPilot."""

import streamlit as st
from datetime import date
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core import (
    CardStorage,
    extract_from_url,
    extract_from_text,
    get_allowed_domains,
)
from src.core.exceptions import ExtractionError, StorageError, FetchError

# Input validation
MAX_INPUT_CHARS = 50000  # Max characters for pasted text

SAMPLE_TEXT = """The Platinum Card from American Express

Annual Fee: $695

Welcome Offer: Earn 80,000 Membership Rewards points after you spend $8,000 on eligible purchases on your new Card in your first 6 months of Card Membership.

Credits and Benefits:
- $200 Airline Fee Credit annually (incidental fees)
- $200 Uber Cash annually ($15/month + $20 in December)
- $240 Digital Entertainment Credit ($20/month for Disney+, Hulu, ESPN+, Peacock, NYT, Audible)
- $200 Hotel Credit (prepaid FHR or THC bookings)
- $189 CLEAR Plus Credit
- $155 Walmart+ membership
- $100 Saks Fifth Avenue Credit ($50 semi-annually)
- Global Lounge Collection access (Centurion, Priority Pass)
- Global Entry/TSA PreCheck fee credit ($100 every 4 years)
"""


def init_session_state():
    """Initialize Streamlit session state."""
    if "storage" not in st.session_state:
        st.session_state.storage = CardStorage()
    if "last_extraction" not in st.session_state:
        st.session_state.last_extraction = None
    if "text_input" not in st.session_state:
        st.session_state.text_input = ""


def render_sidebar():
    """Render the sidebar with app info."""
    with st.sidebar:
        st.title("ChurnPilot")
        st.caption("AI-Powered Card Management")
        st.divider()
        st.markdown("**Quick Links**")
        st.markdown("- [US Credit Card Guide](https://www.uscreditcardguide.com)")
        st.markdown("- [Doctor of Credit](https://www.doctorofcredit.com)")
        st.markdown("- [r/churning](https://reddit.com/r/churning)")


def render_add_card_section():
    """Render the Add Card interface with URL and paste options."""
    st.header("Add Card")
    st.caption("Extract card data from URL or pasted text")

    # Option 1: URL Extraction (recommended)
    st.subheader("Option 1: Extract from URL")
    url_col1, url_col2 = st.columns([4, 1])

    with url_col1:
        url_input = st.text_input(
            "Card Page URL",
            placeholder="https://www.uscreditcardguide.com/amex-platinum/",
            label_visibility="collapsed",
        )

    with url_col2:
        extract_url_btn = st.button("Extract", type="primary", use_container_width=True)

    with st.expander("Supported sites", expanded=False):
        domains = get_allowed_domains()
        st.caption(", ".join(domains))

    if extract_url_btn and url_input:
        with st.spinner("Fetching and extracting (this may take a moment)..."):
            try:
                card_data = extract_from_url(url_input)
                st.session_state.last_extraction = card_data
                st.session_state.source_url = url_input
                st.success(f"Extracted: {card_data.name}")
            except (FetchError, ExtractionError) as e:
                st.error(f"Extraction failed: {e}")

    st.divider()

    # Option 2: Paste Text
    st.subheader("Option 2: Paste Text")

    if st.button("Load Sample (Amex Platinum)"):
        st.session_state.text_input = SAMPLE_TEXT
        st.rerun()

    raw_text = st.text_area(
        "Card Information",
        height=200,
        placeholder="Paste card terms, benefits, or review content here...",
        key="text_input",
    )

    char_count = len(raw_text)
    if char_count > 0:
        if char_count > MAX_INPUT_CHARS:
            st.error(f"{char_count:,} characters - Maximum {MAX_INPUT_CHARS:,} allowed")
        else:
            st.caption(f"{char_count:,} characters")

    extract_text_btn = st.button(
        "Extract from Text",
        type="secondary",
        disabled=char_count > MAX_INPUT_CHARS or char_count == 0,
    )

    if extract_text_btn and raw_text and char_count <= MAX_INPUT_CHARS:
        with st.spinner("Extracting card data..."):
            try:
                card_data = extract_from_text(raw_text)
                st.session_state.last_extraction = card_data
                st.session_state.source_url = None
                st.success(f"Extracted: {card_data.name}")
            except ExtractionError as e:
                st.error(f"Extraction failed: {e}")

    # Show extraction result
    if st.session_state.last_extraction:
        st.divider()
        st.subheader("Extracted Data")
        card_data = st.session_state.last_extraction

        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Card Name", value=card_data.name, key="ext_name")
            st.text_input("Issuer", value=card_data.issuer, key="ext_issuer")
            st.number_input(
                "Annual Fee ($)",
                value=card_data.annual_fee,
                min_value=0,
                key="ext_fee",
            )

        with col2:
            if card_data.signup_bonus:
                st.markdown("**Sign-up Bonus**")
                st.write(f"- {card_data.signup_bonus.points_or_cash}")
                st.write(f"- Spend ${card_data.signup_bonus.spend_requirement:,.0f}")
                st.write(f"- Within {card_data.signup_bonus.time_period_days} days")
            else:
                st.markdown("**Sign-up Bonus**")
                st.write("No SUB found")

        if card_data.credits:
            st.markdown("**Credits/Perks**")
            for credit in card_data.credits:
                notes = f" ({credit.notes})" if credit.notes else ""
                st.write(f"- {credit.name}: ${credit.amount}/{credit.frequency}{notes}")

        opened_date = st.date_input("Card Opened Date (optional)", value=None)

        if st.button("Save Card", type="primary"):
            try:
                card = st.session_state.storage.add_card(
                    card_data,
                    opened_date=opened_date,
                    raw_text=getattr(st.session_state, "source_url", None),
                )
                st.success(f"Saved: {card.name}")
                st.session_state.last_extraction = None
                st.rerun()
            except StorageError as e:
                st.error(f"Failed to save: {e}")


def render_dashboard():
    """Render the card dashboard."""
    st.header("Your Cards")

    cards = st.session_state.storage.get_all_cards()

    if not cards:
        st.info("No cards yet. Use 'Add Card' to extract your first card.")
        return

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Cards", len(cards))
    with col2:
        total_fees = sum(c.annual_fee for c in cards)
        st.metric("Total Annual Fees", f"${total_fees:,}")
    with col3:
        cards_with_sub = sum(1 for c in cards if c.signup_bonus)
        st.metric("Active SUBs", cards_with_sub)

    st.divider()

    # Card list
    for card in cards:
        with st.expander(f"**{card.name}** - {card.issuer}", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Annual Fee:** ${card.annual_fee}")
                if card.opened_date:
                    st.write(f"**Opened:** {card.opened_date}")
                if card.annual_fee_date:
                    days_until = (card.annual_fee_date - date.today()).days
                    if days_until <= 30:
                        st.warning(f"**AF Due:** {card.annual_fee_date} ({days_until} days)")
                    else:
                        st.write(f"**AF Due:** {card.annual_fee_date}")

            with col2:
                if card.signup_bonus:
                    st.write("**SUB:**")
                    st.write(f"- {card.signup_bonus.points_or_cash}")
                    st.write(f"- Spend ${card.signup_bonus.spend_requirement:,.0f} in {card.signup_bonus.time_period_days} days")

            if card.credits:
                st.write("**Credits:**")
                for credit in card.credits:
                    st.write(f"- {credit.name}: ${credit.amount}/{credit.frequency}")

            if st.button("Delete", key=f"del_{card.id}"):
                st.session_state.storage.delete_card(card.id)
                st.rerun()


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="ChurnPilot",
        page_icon="💳",
        layout="wide",
    )

    init_session_state()
    render_sidebar()

    tab1, tab2 = st.tabs(["Add Card", "Dashboard"])

    with tab1:
        render_add_card_section()

    with tab2:
        render_dashboard()


if __name__ == "__main__":
    main()
