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
    get_all_templates,
    get_template,
    SignupBonus,
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

    st.divider()

    # Option 3: Select from Library
    st.subheader("Option 3: Select from Library")

    templates = get_all_templates()
    if templates:
        template_options = {"": "-- Select a card --"}
        template_options.update({t.id: f"{t.name} ({t.issuer})" for t in templates})

        selected_id = st.selectbox(
            "Card Type",
            options=list(template_options.keys()),
            format_func=lambda x: template_options[x],
            key="library_select",
        )

        if selected_id:
            template = get_template(selected_id)
            if template:
                st.caption(f"Annual Fee: ${template.annual_fee} | {len(template.credits)} credits included")

                col1, col2 = st.columns(2)
                with col1:
                    lib_nickname = st.text_input(
                        "Nickname (optional)",
                        placeholder="e.g., P2's Platinum",
                        key="lib_nickname",
                    )
                with col2:
                    lib_opened_date = st.date_input(
                        "Opened Date (optional)",
                        value=None,
                        key="lib_opened_date",
                    )

                with st.expander("View included credits", expanded=False):
                    for credit in template.credits:
                        notes = f" ({credit.notes})" if credit.notes else ""
                        st.write(f"- {credit.name}: ${credit.amount}/{credit.frequency}{notes}")

                if st.button("Add Card", type="primary", key="add_from_library"):
                    try:
                        card = st.session_state.storage.add_card_from_template(
                            template=template,
                            nickname=lib_nickname if lib_nickname else None,
                            opened_date=lib_opened_date,
                        )
                        st.success(f"Added: {card.name}" + (f" ({card.nickname})" if card.nickname else ""))
                        st.rerun()
                    except StorageError as e:
                        st.error(f"Failed to add: {e}")
    else:
        st.info("No card templates available in library.")

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


def get_issuer_color(issuer: str) -> str:
    """Get a color associated with a card issuer."""
    colors = {
        "American Express": "#006FCF",
        "Chase": "#124A8D",
        "Capital One": "#D03027",
        "Citi": "#003B70",
        "Discover": "#FF6600",
        "Bank of America": "#E31837",
        "Wells Fargo": "#D71E28",
        "US Bank": "#0C2340",
        "Barclays": "#00AEEF",
        "Bilt": "#000000",
    }
    return colors.get(issuer, "#666666")


def render_card_item(card):
    """Render a single card item with rich display."""
    # Build the header with issuer color indicator
    issuer_color = get_issuer_color(card.issuer)

    # Card title
    title = card.name
    if card.nickname:
        title = f"{card.nickname} ({card.name})"

    with st.container():
        # Use columns for a card-like layout
        header_col, fee_col, action_col = st.columns([5, 2, 1])

        with header_col:
            st.markdown(
                f"<span style='color: {issuer_color}; font-weight: bold;'>{card.issuer}</span> | "
                f"**{title}**",
                unsafe_allow_html=True
            )

        with fee_col:
            if card.annual_fee > 0:
                st.markdown(f"**${card.annual_fee}/yr**")
            else:
                st.markdown("**No AF**")

        with action_col:
            if st.button("X", key=f"del_{card.id}", help="Delete card"):
                st.session_state.storage.delete_card(card.id)
                st.rerun()

        # Expandable details
        with st.expander("View Details", expanded=False):
            detail_col1, detail_col2 = st.columns(2)

            with detail_col1:
                # Basic info
                if card.opened_date:
                    days_held = (date.today() - card.opened_date).days
                    st.write(f"**Opened:** {card.opened_date} ({days_held} days ago)")

                if card.annual_fee_date:
                    days_until_af = (card.annual_fee_date - date.today()).days
                    if days_until_af <= 30:
                        st.error(f"**AF Due:** {card.annual_fee_date} ({days_until_af} days)")
                    elif days_until_af <= 60:
                        st.warning(f"**AF Due:** {card.annual_fee_date} ({days_until_af} days)")
                    else:
                        st.write(f"**AF Due:** {card.annual_fee_date} ({days_until_af} days)")

                # SUB tracking
                if card.signup_bonus:
                    st.write("---")
                    st.write("**Sign-up Bonus:**")
                    st.write(f"  {card.signup_bonus.points_or_cash}")
                    st.write(f"  Spend ${card.signup_bonus.spend_requirement:,.0f} in {card.signup_bonus.time_period_days} days")

                    if card.signup_bonus.deadline:
                        days_left = (card.signup_bonus.deadline - date.today()).days
                        if days_left < 0:
                            st.error(f"  **EXPIRED** ({abs(days_left)} days ago)")
                        elif days_left <= 14:
                            st.error(f"  **Deadline:** {card.signup_bonus.deadline} ({days_left} days left!)")
                        elif days_left <= 30:
                            st.warning(f"  **Deadline:** {card.signup_bonus.deadline} ({days_left} days left)")
                        else:
                            st.write(f"  **Deadline:** {card.signup_bonus.deadline} ({days_left} days left)")

            with detail_col2:
                # Credits
                if card.credits:
                    st.write("**Credits/Perks:**")
                    total_value = 0
                    for credit in card.credits:
                        # Calculate annual value
                        if credit.frequency == "monthly":
                            annual = credit.amount * 12
                        elif credit.frequency == "quarterly":
                            annual = credit.amount * 4
                        elif credit.frequency == "semi-annual" or credit.frequency == "semi-annually":
                            annual = credit.amount * 2
                        else:
                            annual = credit.amount
                        total_value += annual

                        notes = f" *({credit.notes})*" if credit.notes else ""
                        st.write(f"- {credit.name}: ${credit.amount}/{credit.frequency}{notes}")

                    st.write(f"**Total Credit Value:** ~${total_value:,.0f}/year")
                else:
                    st.write("*No credits/perks*")

            # Notes
            if card.notes:
                st.write("---")
                st.write(f"**Notes:** {card.notes}")

        st.write("")  # Spacing between cards


def render_dashboard():
    """Render the card dashboard with filtering, sorting, and rich display."""
    st.header("Your Cards")

    cards = st.session_state.storage.get_all_cards()

    if not cards:
        st.info("No cards yet. Go to 'Add Card' to add your first card.")
        return

    # Calculate metrics
    total_fees = sum(c.annual_fee for c in cards)
    total_credits_value = sum(
        sum(credit.amount for credit in c.credits) for c in cards
    )
    cards_with_sub = [c for c in cards if c.signup_bonus and c.signup_bonus.deadline]
    urgent_subs = [
        c for c in cards_with_sub
        if c.signup_bonus.deadline and (c.signup_bonus.deadline - date.today()).days <= 30
    ]

    # Summary metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Cards", len(cards))
    with col2:
        st.metric("Annual Fees", f"${total_fees:,}")
    with col3:
        st.metric("Credits Value", f"${total_credits_value:,.0f}/yr")
    with col4:
        if urgent_subs:
            st.metric("Urgent SUBs", len(urgent_subs), delta="Action needed", delta_color="inverse")
        else:
            st.metric("Active SUBs", len(cards_with_sub))

    st.divider()

    # Filter and sort controls
    filter_col, sort_col, search_col = st.columns([2, 2, 3])

    with filter_col:
        # Get unique issuers
        issuers = sorted(set(c.issuer for c in cards))
        issuer_filter = st.selectbox(
            "Filter by Issuer",
            options=["All Issuers"] + issuers,
            key="issuer_filter",
        )

    with sort_col:
        sort_option = st.selectbox(
            "Sort by",
            options=["Name (A-Z)", "Name (Z-A)", "Annual Fee (High)", "Annual Fee (Low)", "Date Opened (Recent)", "Date Opened (Oldest)"],
            key="sort_option",
        )

    with search_col:
        search_query = st.text_input(
            "Search",
            placeholder="Search by name or nickname...",
            key="search_query",
        )

    # Apply filters
    filtered_cards = cards

    if issuer_filter != "All Issuers":
        filtered_cards = [c for c in filtered_cards if c.issuer == issuer_filter]

    if search_query:
        query_lower = search_query.lower()
        filtered_cards = [
            c for c in filtered_cards
            if query_lower in c.name.lower() or (c.nickname and query_lower in c.nickname.lower())
        ]

    # Apply sorting
    if sort_option == "Name (A-Z)":
        filtered_cards = sorted(filtered_cards, key=lambda c: c.name.lower())
    elif sort_option == "Name (Z-A)":
        filtered_cards = sorted(filtered_cards, key=lambda c: c.name.lower(), reverse=True)
    elif sort_option == "Annual Fee (High)":
        filtered_cards = sorted(filtered_cards, key=lambda c: c.annual_fee, reverse=True)
    elif sort_option == "Annual Fee (Low)":
        filtered_cards = sorted(filtered_cards, key=lambda c: c.annual_fee)
    elif sort_option == "Date Opened (Recent)":
        filtered_cards = sorted(
            filtered_cards,
            key=lambda c: c.opened_date if c.opened_date else date.min,
            reverse=True
        )
    elif sort_option == "Date Opened (Oldest)":
        filtered_cards = sorted(
            filtered_cards,
            key=lambda c: c.opened_date if c.opened_date else date.max
        )

    # Show filter results count
    if len(filtered_cards) != len(cards):
        st.caption(f"Showing {len(filtered_cards)} of {len(cards)} cards")

    st.divider()

    # Card list with improved display
    if not filtered_cards:
        st.info("No cards match your filters.")
        return

    for card in filtered_cards:
        render_card_item(card)


def render_library_section():
    """Render the Add from Library interface."""
    st.header("Add from Library")
    st.caption("Select a pre-defined card template")

    templates = get_all_templates()
    if not templates:
        st.info("No card templates available yet.")
        return

    # Template selector
    template_options = {t.id: f"{t.name} ({t.issuer})" for t in templates}
    selected_id = st.selectbox(
        "Select Card",
        options=list(template_options.keys()),
        format_func=lambda x: template_options[x],
    )

    template = get_template(selected_id)
    if not template:
        return

    st.divider()

    # Card preview
    st.subheader("Card Details")

    col1, col2 = st.columns(2)
    with col1:
        nickname = st.text_input(
            "Nickname (optional)",
            placeholder="e.g., My Amex Plat, P2's Platinum",
        )
        st.text_input("Card Name", value=template.name, disabled=True)
        st.text_input("Issuer", value=template.issuer, disabled=True)
        st.number_input("Annual Fee ($)", value=template.annual_fee, disabled=True)

    with col2:
        opened_date = st.date_input("Card Opened Date", value=None)

        st.markdown("**Sign-up Bonus (optional)**")
        sub_points = st.text_input(
            "Bonus Amount",
            placeholder="e.g., 80,000 points or $200 cash back",
        )
        sub_spend = st.number_input("Spend Requirement ($)", min_value=0, value=0)
        sub_days = st.number_input(
            "Time Period (days)",
            min_value=0,
            value=90,
            help="Typically 90 days (3 months)",
        )

    # Show credits
    if template.credits:
        st.markdown("**Included Credits/Perks**")
        for credit in template.credits:
            notes = f" - {credit.notes}" if credit.notes else ""
            st.write(f"- {credit.name}: ${credit.amount}/{credit.frequency}{notes}")

    st.divider()

    if st.button("Save Card", type="primary", key="save_library_card"):
        try:
            # Build signup bonus if provided
            signup_bonus = None
            if sub_points and sub_spend > 0:
                signup_bonus = SignupBonus(
                    points_or_cash=sub_points,
                    spend_requirement=sub_spend,
                    time_period_days=sub_days,
                    deadline=None,
                )

            # Create card via storage (using add_card_from_template)
            card = st.session_state.storage.add_card_from_template(
                template=template,
                nickname=nickname if nickname else None,
                opened_date=opened_date,
                signup_bonus=signup_bonus,
            )
            st.success(f"Saved: {card.name}" + (f" ({card.nickname})" if card.nickname else ""))
            st.rerun()
        except StorageError as e:
            st.error(f"Failed to save: {e}")


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="ChurnPilot",
        page_icon="💳",
        layout="wide",
    )

    init_session_state()
    render_sidebar()

    # Two main tabs - Dashboard is primary
    tab1, tab2 = st.tabs(["Dashboard", "Add Card"])

    with tab1:
        render_dashboard()

    with tab2:
        render_add_card_section()


if __name__ == "__main__":
    main()
