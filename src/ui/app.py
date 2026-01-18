"""Streamlit UI for ChurnPilot."""

import streamlit as st
from datetime import date
import sys
from pathlib import Path


# Custom CSS for cleaner UI
CUSTOM_CSS = """
<style>
    /* Card container styling */
    .card-container {
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        transition: box-shadow 0.2s ease;
        color: #262730;
    }
    .card-container:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }

    /* Status badges */
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 500;
        margin-right: 4px;
    }
    .badge-warning { background: #fff3cd; color: #856404; }
    .badge-success { background: #d4edda; color: #155724; }
    .badge-danger { background: #f8d7da; color: #721c24; }
    .badge-info { background: #cce5ff; color: #004085; }
    .badge-muted { background: #e9ecef; color: #6c757d; }

    /* Benefits progress bar - no text content */
    .benefits-progress {
        background: #e9ecef; /* no text content */
        border-radius: 4px;
        height: 6px;
        overflow: hidden;
        margin: 4px 0;
    }
    .benefits-progress-fill {
        background: linear-gradient(90deg, #28a745 0%, #20c997 100%); /* no text content */
        height: 100%;
        transition: width 0.3s ease;
    }

    /* Summary card styling */
    .summary-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        color: #262730;
    }
    .summary-value {
        font-size: 2rem;
        font-weight: 700;
        color: #212529;
    }
    .summary-label {
        font-size: 0.875rem;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Compact button styling */
    .stButton > button {
        border-radius: 8px;
        font-size: 0.875rem;
        padding: 4px 12px;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Better metric styling */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
    }

    /* Checkbox styling in benefits */
    .benefit-item {
        padding: 8px 12px;
        margin: 4px 0;
        border-radius: 8px;
        background: #f8f9fa;
        border-left: 3px solid #dee2e6;
        color: #262730;
    }
    .benefit-item.used {
        background: #d4edda;
        border-left-color: #28a745;
        color: #155724;
    }
    .benefit-item.unused {
        background: #fff3cd;
        border-left-color: #ffc107;
        color: #856404;
    }
</style>
"""

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
    get_display_name,
    CreditUsage,
    get_current_period,
    get_period_display_name,
    is_credit_used_this_period,
    is_reminder_snoozed,
    get_unused_credits_count,
    mark_credit_used,
    mark_credit_unused,
    snooze_all_reminders,
    RetentionOffer,
    calculate_five_twenty_four_status,
    get_five_twenty_four_timeline,
    validate_opened_date,
    validate_annual_fee,
    validate_signup_bonus,
    validate_card_name,
    has_errors,
    has_warnings,
    get_error_messages,
    get_warning_messages,
    ValidationWarning,
    ValidationError,
)
from src.core.preferences import PreferencesStorage, UserPreferences
from src.core.exceptions import ExtractionError, StorageError, FetchError
from datetime import timedelta

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
    if "prefs_storage" not in st.session_state:
        st.session_state.prefs_storage = PreferencesStorage()
    if "prefs" not in st.session_state:
        st.session_state.prefs = st.session_state.prefs_storage.get_preferences()
    if "last_extraction" not in st.session_state:
        st.session_state.last_extraction = None
    if "text_input" not in st.session_state:
        st.session_state.text_input = ""


def render_sidebar():
    """Render the sidebar with app info and quick stats."""
    with st.sidebar:
        st.title("ChurnPilot")
        st.caption("Credit Card Management")

        # Quick stats
        cards = st.session_state.storage.get_all_cards()
        if cards:
            st.divider()
            st.markdown("**Quick Stats**")

            # Cards by issuer
            issuers = {}
            for card in cards:
                issuers[card.issuer] = issuers.get(card.issuer, 0) + 1

            for issuer, count in sorted(issuers.items(), key=lambda x: -x[1]):
                st.caption(f"{issuer}: {count}")

            # Portfolio Value Widget
            st.divider()
            st.markdown("**Portfolio Value**")

            # Calculate total fees
            total_fees = sum(c.annual_fee for c in cards)

            # Calculate total annual benefits value
            total_benefits_value = 0
            for card in cards:
                for credit in card.credits:
                    if credit.frequency == "monthly":
                        total_benefits_value += credit.amount * 12
                    elif credit.frequency == "quarterly":
                        total_benefits_value += credit.amount * 4
                    elif credit.frequency in ["semi-annual", "semi-annually"]:
                        total_benefits_value += credit.amount * 2
                    else:
                        total_benefits_value += credit.amount

            # Net value
            net_value = total_benefits_value - total_fees

            # Display metrics
            st.metric("Annual Fees", f"${total_fees:,.0f}")
            st.metric("Benefits Value", f"${total_benefits_value:,.0f}")

            if net_value >= 0:
                st.metric("Net Value", f"${net_value:,.0f}", delta="Positive ROI")
            else:
                st.metric("Net Value", f"${net_value:,.0f}", delta="Negative", delta_color="inverse")

            # Utilization info
            if total_benefits_value > 0:
                utilization_pct = min(100, (total_benefits_value / max(1, total_fees)) * 100)
                st.caption(f"Value extraction: {utilization_pct:.0f}% of fees")

            # SUB pending value
            pending_subs = [
                c for c in cards
                if c.signup_bonus and not c.sub_achieved and c.signup_bonus.deadline
            ]
            if pending_subs:
                st.caption(f"+ {len(pending_subs)} pending SUBs")

            # 5/24 Status
            st.divider()
            five_24 = calculate_five_twenty_four_status(cards)
            st.markdown("**Chase 5/24 Status**")

            if five_24["status"] == "under":
                st.success(f"{five_24['count']}/5 - Can apply")
            elif five_24["status"] == "at":
                st.warning(f"{five_24['count']}/5 - At limit")
            else:
                st.error(f"{five_24['count']}/5 - Over limit")

            if five_24["next_drop_off"]:
                st.caption(f"Next drop: {five_24['next_drop_off']} ({five_24['days_until_drop']}d)")

            with st.expander("What is 5/24?"):
                st.caption("Chase denies applications if you've opened 5+ personal cards from ANY issuer in the past 24 months.")
                st.caption("Business cards don't count (except Cap1, Discover, TD Bank).")

            # Upcoming deadlines
            upcoming = []
            for card in cards:
                if card.signup_bonus and card.signup_bonus.deadline:
                    days_left = (card.signup_bonus.deadline - date.today()).days
                    if 0 <= days_left <= 30:
                        upcoming.append((card, days_left, "SUB"))
                if card.annual_fee_date:
                    days_left = (card.annual_fee_date - date.today()).days
                    if 0 <= days_left <= 30:
                        upcoming.append((card, days_left, "AF"))

            if upcoming:
                st.divider()
                st.markdown("**Upcoming (30 days)**")
                for card, days, deadline_type in sorted(upcoming, key=lambda x: x[1]):
                    name = card.nickname or card.name[:15]
                    if deadline_type == "SUB":
                        st.warning(f"{name}: SUB in {days}d")
                    else:
                        st.error(f"{name}: AF in {days}d")
        else:
            # Empty state for sidebar
            st.divider()
            st.caption("No cards tracked yet.")
            st.caption("Add your first card to see stats and deadlines here.")

        # Export data
        if cards:
            st.divider()
            st.markdown("**Data**")
            # Generate JSON export
            import json
            cards_data = [card.model_dump(mode='json') for card in cards]
            json_str = json.dumps(cards_data, indent=2, default=str)
            st.download_button(
                label="Export (JSON)",
                data=json_str,
                file_name="churnpilot_cards.json",
                mime="application/json",
            )

        st.divider()
        st.markdown("**Resources**")
        st.markdown("[US Credit Card Guide](https://www.uscreditcardguide.com)")
        st.markdown("[Doctor of Credit](https://www.doctorofcredit.com)")
        st.markdown("[r/churning](https://reddit.com/r/churning)")

        st.divider()
        st.caption(f"Library: {len(get_all_templates())} templates")


def render_add_card_section():
    """Render the Add Card interface."""
    st.header("Add Card")

    # Quick add from library (primary method)
    st.subheader("Quick Add from Library")

    templates = get_all_templates()
    if templates:
        # Group templates by issuer for better organization
        issuers = sorted(set(t.issuer for t in templates))

        col1, col2 = st.columns([3, 2])

        with col1:
            # Filter by issuer first
            selected_issuer = st.selectbox(
                "Issuer",
                options=["All Issuers"] + issuers,
                key="add_issuer_filter",
            )

        # Filter templates
        filtered_templates = templates
        if selected_issuer != "All Issuers":
            filtered_templates = [t for t in templates if t.issuer == selected_issuer]

        with col2:
            template_options = {"": "-- Select card --"}
            template_options.update({t.id: t.name for t in filtered_templates})

            selected_id = st.selectbox(
                "Card",
                options=list(template_options.keys()),
                format_func=lambda x: template_options[x],
                key="library_select",
            )

        if selected_id:
            template = get_template(selected_id)
            if template:
                # Show card preview
                st.markdown(f"**{template.name}** - ${template.annual_fee}/yr")

                col1, col2 = st.columns(2)
                with col1:
                    lib_nickname = st.text_input(
                        "Nickname",
                        placeholder="e.g., P2's Card",
                        key="lib_nickname",
                    )
                with col2:
                    lib_opened_date = st.date_input(
                        "Opened Date",
                        value=None,
                        key="lib_opened_date",
                    )

                # Optional SUB entry
                with st.expander("Add Sign-up Bonus (optional)"):
                    sub_col1, sub_col2 = st.columns(2)
                    with sub_col1:
                        lib_sub_bonus = st.text_input(
                            "Bonus Amount",
                            placeholder="e.g., 80,000 points",
                            key="lib_sub_bonus",
                        )
                        lib_sub_spend = st.number_input(
                            "Spend Requirement ($)",
                            min_value=0,
                            value=0,
                            step=500,
                            key="lib_sub_spend",
                        )
                    with sub_col2:
                        lib_sub_days = st.number_input(
                            "Time Period (days)",
                            min_value=0,
                            value=90,
                            step=30,
                            key="lib_sub_days",
                        )
                        st.caption("Deadline will be calculated from opened date")

                if st.button("Add Card", type="primary", key="add_from_library", use_container_width=True):
                    # Validate inputs before saving
                    validation_results = []
                    validation_results.append(validate_opened_date(lib_opened_date))
                    validation_results.append(validate_annual_fee(template.annual_fee))
                    validation_results.append(validate_signup_bonus(
                        lib_sub_bonus,
                        lib_sub_spend,
                        lib_sub_days,
                        lib_opened_date
                    ))

                    # Show errors (blocking)
                    if has_errors(validation_results):
                        for error_msg in get_error_messages(validation_results):
                            st.error(error_msg)
                        st.stop()

                    # Show warnings (non-blocking)
                    if has_warnings(validation_results):
                        for warning_msg in get_warning_messages(validation_results):
                            st.warning(warning_msg)

                    try:
                        # Build SUB if provided
                        signup_bonus = None
                        if lib_sub_bonus and lib_sub_spend > 0 and lib_sub_days > 0:
                            from datetime import timedelta
                            deadline = None
                            if lib_opened_date:
                                deadline = lib_opened_date + timedelta(days=lib_sub_days)
                            signup_bonus = SignupBonus(
                                points_or_cash=lib_sub_bonus,
                                spend_requirement=float(lib_sub_spend),
                                time_period_days=lib_sub_days,
                                deadline=deadline,
                            )

                        card = st.session_state.storage.add_card_from_template(
                            template=template,
                            nickname=lib_nickname if lib_nickname else None,
                            opened_date=lib_opened_date,
                            signup_bonus=signup_bonus,
                        )
                        st.success(f"Added: {card.name}")
                        st.rerun()
                    except StorageError as e:
                        st.error(f"Failed: {e}")

                # Credits preview
                if template.credits:
                    with st.expander(f"View {len(template.credits)} included credits"):
                        for credit in template.credits:
                            notes = f" *({credit.notes})*" if credit.notes else ""
                            st.caption(f"- {credit.name}: ${credit.amount}/{credit.frequency}{notes}")

    st.divider()

    # Import from spreadsheet (collapsed by default)
    with st.expander("Import from Spreadsheet"):
        st.markdown("""
        **Import your existing credit card tracking spreadsheet!**

        ChurnPilot uses AI to understand your spreadsheet format automatically - works with:
        - Google Sheets
        - Excel files
        - CSV files
        - Any language (English, Chinese, etc.)
        - Any column names or layout

        We'll extract card names, fees, SUB status, benefits, and usage tracking.
        """)

        st.warning("""
        ⚠️ **Privacy Notice**: Do not include sensitive information like card numbers, CVV, or full account numbers in your spreadsheet.
        While we don't store this data, it may be sent to our AI service for parsing. Only include card names, fees, dates, and benefit information.
        """)

        st.divider()

        # Import method selection
        import_method = st.radio(
            "Choose import method:",
            ["Google Sheets URL", "Upload File", "Paste CSV/TSV Data"],
            horizontal=True,
            key="import_method_radio"
        )

        spreadsheet_data = None

        if import_method == "Google Sheets URL":
            st.info("💡 Make sure your Google Sheet is shared as 'Anyone with the link can view'")
            sheet_url = st.text_input(
                "Google Sheets URL:",
                placeholder="https://docs.google.com/spreadsheets/d/...",
                key="import_sheet_url"
            )
            if sheet_url and st.button("Fetch from Google Sheets", key="import_fetch_sheets"):
                try:
                    import re
                    # Extract sheet ID and gid
                    sheet_id_match = re.search(r'/d/([a-zA-Z0-9-_]+)', sheet_url)
                    gid_match = re.search(r'[#&]gid=(\d+)', sheet_url)

                    if sheet_id_match:
                        sheet_id = sheet_id_match.group(1)
                        gid = gid_match.group(1) if gid_match else "0"

                        # Build export URL
                        export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=tsv&gid={gid}"

                        # Fetch the data
                        import urllib.request
                        with urllib.request.urlopen(export_url) as response:
                            spreadsheet_data = response.read().decode('utf-8')

                        st.success("✓ Fetched spreadsheet data!")
                    else:
                        st.error("Invalid Google Sheets URL format")
                except Exception as e:
                    st.error(f"Failed to fetch: {e}")

        elif import_method == "Upload File":
            uploaded_file = st.file_uploader(
                "Upload CSV or Excel file",
                type=["csv", "xlsx", "xls", "tsv"],
                help="Upload your credit card tracking file",
                key="import_file_uploader"
            )
            if uploaded_file:
                try:
                    if uploaded_file.name.endswith(('.xlsx', '.xls')):
                        try:
                            import pandas as pd
                        except ImportError:
                            st.error("📦 Missing dependency: pandas is required for Excel files.")
                            st.info("Run: `pip install pandas openpyxl`")
                            return

                        try:
                            df = pd.read_excel(uploaded_file)
                            spreadsheet_data = df.to_csv(sep='\t', index=False)
                        except ImportError as ie:
                            if 'openpyxl' in str(ie):
                                st.error("📦 Missing dependency: openpyxl is required for Excel files.")
                                st.info("Run: `pip install openpyxl`")
                            else:
                                st.error(f"Failed to read Excel file: {ie}")
                            return
                    else:
                        spreadsheet_data = uploaded_file.getvalue().decode('utf-8')
                    st.success(f"Loaded {uploaded_file.name}")
                except Exception as e:
                    st.error(f"Failed to read file: {e}")

        elif import_method == "Paste CSV/TSV Data":
            st.info("💡 Copy your spreadsheet data (select all cells, Ctrl+C) and paste here.")
            spreadsheet_data = st.text_area(
                "Paste your spreadsheet data:",
                height=200,
                placeholder="Paste your spreadsheet data here...\nInclude column headers in the first row.",
                key="import_text_area"
            )

        # Parse and preview
        if spreadsheet_data and st.button("Parse Spreadsheet", type="primary", key="import_parse_btn"):
            with st.spinner("🤖 AI is analyzing your spreadsheet..."):
                try:
                    from src.core.importer import import_from_csv

                    parsed_cards, errors = import_from_csv(spreadsheet_data, skip_closed=True)

                    # Handle results (best-effort)
                    if not parsed_cards and errors:
                        # Complete failure
                        st.error("❌ Failed to parse any cards")
                        with st.expander("Error details"):
                            for error in errors:
                                st.error(f"• {error}")
                        return

                    elif not parsed_cards:
                        # No cards found
                        st.warning("No cards found. Make sure your spreadsheet has card data and try again.")
                        return

                    else:
                        # Partial or complete success
                        if errors:
                            # Partial success - some cards failed
                            st.warning(f"⚠️ Parsed {len(parsed_cards)} cards successfully, but {len(errors)} failed")
                            with st.expander(f"Show {len(errors)} error(s)"):
                                for error in errors:
                                    st.error(f"• {error}")
                            st.info("✓ You can still import the successfully parsed cards below")
                        else:
                            # Complete success
                            st.success(f"✓ Parsed {len(parsed_cards)} cards successfully!")

                        # Store in session state for preview
                        st.session_state.parsed_import = parsed_cards
                        st.session_state.import_errors = errors

                        st.divider()
                        st.subheader("Preview")

                        for i, card in enumerate(parsed_cards, 1):
                            # Build title with urgency indicator
                            title = f"{i}. {card.card_name} - ${card.annual_fee}/yr"

                            # Add urgency badge if SUB is active
                            if card.sub_reward and not card.sub_achieved:
                                days_remaining = card.get_days_remaining()
                                if days_remaining is not None:
                                    if days_remaining < 0:
                                        title += " ⚠️ EXPIRED"
                                    elif days_remaining <= 30:
                                        title += f" 🔴 {days_remaining} days left"
                                    elif days_remaining <= 60:
                                        title += f" 🟡 {days_remaining} days left"
                                    else:
                                        title += f" 🟢 {days_remaining} days left"

                            with st.expander(title, expanded=(i <= 3)):
                                col1, col2 = st.columns(2)

                                with col1:
                                    st.markdown(f"**Status:** {card.status or 'N/A'}")
                                    st.markdown(f"**Opened:** {card.opened_date or 'Unknown'}")

                                    if card.sub_reward:
                                        st.markdown(f"**SUB:** {card.sub_reward}")
                                        st.markdown(f"- Spend: ${card.sub_spend_requirement}")
                                        st.markdown(f"- Period: {card.sub_time_period_days} days")

                                        # Show calculated or existing deadline
                                        deadline = card.calculate_deadline()
                                        if deadline:
                                            days_remaining = card.get_days_remaining()
                                            if days_remaining is not None:
                                                if days_remaining < 0:
                                                    st.markdown(f"- Deadline: {deadline} ⚠️ **EXPIRED ({abs(days_remaining)} days ago)**")
                                                elif days_remaining <= 30:
                                                    st.markdown(f"- Deadline: {deadline} 🔴 **URGENT ({days_remaining} days left)**")
                                                elif days_remaining <= 60:
                                                    st.markdown(f"- Deadline: {deadline} 🟡 **Soon ({days_remaining} days left)**")
                                                else:
                                                    st.markdown(f"- Deadline: {deadline} 🟢 ({days_remaining} days left)")
                                            else:
                                                st.markdown(f"- Deadline: {deadline}")
                                        elif card.opened_date and card.sub_time_period_days:
                                            st.info("💡 Auto-calculated deadline will be set on import")

                                        st.markdown(f"- Achieved: {'✓ Yes' if card.sub_achieved else '○ No'}")

                                    # Show auto-calculated annual fee date
                                    annual_fee_date = card.calculate_annual_fee_date()
                                    if annual_fee_date:
                                        st.markdown(f"**Next Annual Fee:** {annual_fee_date}")

                                with col2:
                                    if card.benefits:
                                        st.markdown(f"**Benefits ({len(card.benefits)}):**")
                                        for benefit in card.benefits:
                                            status_icon = "✓" if benefit.get("is_used") else "○"
                                            st.caption(f"{status_icon} ${benefit['amount']} {benefit['name']} ({benefit['frequency']})")

                except Exception as e:
                    st.error(f"Failed to parse: {e}")
                    import traceback
                    with st.expander("Error details"):
                        st.code(traceback.format_exc())

        # Import button
        if st.session_state.get("parsed_import"):
            st.divider()

            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f"Ready to import {len(st.session_state.parsed_import)} cards")
            with col2:
                if st.button("Import All Cards", type="primary", use_container_width=True, key="import_all_btn"):
                    with st.spinner("Importing cards..."):
                        try:
                            from src.core.importer import SpreadsheetImporter

                            importer = SpreadsheetImporter()
                            imported = importer.import_cards(st.session_state.parsed_import)

                            st.success(f"✓ Successfully imported {len(imported)} cards!")
                            st.session_state.parsed_import = None
                            st.balloons()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Import failed: {e}")
                            import traceback
                            with st.expander("Error details"):
                                st.code(traceback.format_exc())

    st.divider()

    # Advanced extraction (collapsed by default)
    with st.expander("Advanced: Extract card details from URL or Text"):
        st.markdown("""
        **Use AI to extract card information from online sources**

        This feature can automatically read card details from:
        - Credit card guide websites (e.g., US Credit Card Guide, The Points Guy)
        - Bank card pages with terms and benefits
        - Card comparison sites
        - Copied text from any source with card information

        Perfect for quickly adding cards that aren't in our library yet.
        """)

        st.divider()

        tab1, tab2 = st.tabs(["From URL", "From Text"])

        with tab1:
            st.caption("Paste a URL to a card's information page")
            url_col1, url_col2 = st.columns([4, 1])
            with url_col1:
                url_input = st.text_input(
                    "URL",
                    placeholder="https://www.uscreditcardguide.com/...",
                    label_visibility="collapsed",
                    key="extract_url_input"
                )
            with url_col2:
                extract_url_btn = st.button("Extract", type="secondary", use_container_width=True, key="extract_url_btn")

            if extract_url_btn and url_input:
                with st.spinner("Extracting card details from URL..."):
                    try:
                        card_data = extract_from_url(url_input)
                        st.session_state.last_extraction = card_data
                        st.session_state.source_url = url_input
                        st.success(f"Extracted: {card_data.name}")
                    except (FetchError, ExtractionError) as e:
                        st.error(f"Failed: {e}")

        with tab2:
            st.caption("Paste any text containing card details (terms, benefits, etc.)")
            raw_text = st.text_area(
                "Paste card info",
                height=150,
                placeholder="Paste card terms, benefits page content, or any text about the card...",
                key="extract_text_input",
            )

            if st.button("Extract", key="extract_text_btn", type="secondary", disabled=len(raw_text) < 50):
                with st.spinner("Extracting card details from text..."):
                    try:
                        card_data = extract_from_text(raw_text)
                        st.session_state.last_extraction = card_data
                        st.session_state.source_url = None
                        st.success(f"Extracted: {card_data.name}")
                    except ExtractionError as e:
                        st.error(f"Failed: {e}")

    # Show extraction result
    if st.session_state.last_extraction:
        st.divider()
        render_extraction_result()


def render_extraction_result():
    """Render the extracted card data for review and saving."""
    card_data = st.session_state.last_extraction

    st.subheader("Review Extracted Card")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**{card_data.name}**")
        st.caption(f"Issuer: {card_data.issuer}")
        st.caption(f"Annual Fee: ${card_data.annual_fee}")

        if card_data.signup_bonus:
            st.markdown("**Sign-up Bonus**")
            st.write(f"- {card_data.signup_bonus.points_or_cash}")
            st.write(f"- Spend ${card_data.signup_bonus.spend_requirement:,.0f} in {card_data.signup_bonus.time_period_days} days")

    with col2:
        if card_data.credits:
            st.markdown(f"**{len(card_data.credits)} Credits/Perks**")
            for credit in card_data.credits[:5]:
                st.caption(f"- {credit.name}: ${credit.amount}/{credit.frequency}")
            if len(card_data.credits) > 5:
                st.caption(f"... and {len(card_data.credits) - 5} more")

    # Show enrichment info if card was matched to library
    from src.core import match_to_library_with_confidence
    match_result = match_to_library_with_confidence(card_data.name, card_data.issuer)
    if match_result.template_id:
        st.success(f"✨ Auto-enriched from '{match_result.template.name}' template ({int(match_result.confidence * 100)}% match)")
        if len(card_data.credits) > 0:
            st.caption(f"ℹ️ Benefits above were automatically added from our library. Review and save if correct.")

    # Save form
    st.markdown("---")
    save_col1, save_col2, save_col3 = st.columns([2, 2, 1])

    with save_col1:
        ext_nickname = st.text_input("Nickname", key="ext_nickname", placeholder="Optional")

    with save_col2:
        ext_opened_date = st.date_input("Opened Date", value=None, key="ext_opened_date")

    with save_col3:
        st.write("")
        st.write("")
        if st.button("Save Card", type="primary", key="save_extracted"):
            # Validate inputs before saving
            validation_results = []
            validation_results.append(validate_opened_date(ext_opened_date))
            validation_results.append(validate_annual_fee(card_data.annual_fee))
            if card_data.signup_bonus:
                validation_results.append(validate_signup_bonus(
                    card_data.signup_bonus.points_or_cash,
                    card_data.signup_bonus.spend_requirement,
                    card_data.signup_bonus.time_period_days,
                    ext_opened_date
                ))

            # Show errors (blocking)
            if has_errors(validation_results):
                for error_msg in get_error_messages(validation_results):
                    st.error(error_msg)
                st.stop()

            # Show warnings (non-blocking)
            if has_warnings(validation_results):
                for warning_msg in get_warning_messages(validation_results):
                    st.warning(warning_msg)

            try:
                card = st.session_state.storage.add_card(
                    card_data,
                    opened_date=ext_opened_date,
                    raw_text=getattr(st.session_state, "source_url", None),
                )
                # Update nickname if provided
                if ext_nickname:
                    st.session_state.storage.update_card(card.id, {"nickname": ext_nickname})
                st.success(f"Saved: {card.name}")
                st.session_state.last_extraction = None
                st.rerun()
            except StorageError as e:
                st.error(f"Failed: {e}")

    if st.button("Discard", key="discard_extracted"):
        st.session_state.last_extraction = None
        st.rerun()


def render_card_edit_form(card, editing_key: str):
    """Render an inline edit form for a card."""
    with st.container():
        st.markdown("---")
        st.markdown("**Edit Card**")

        col1, col2 = st.columns(2)

        with col1:
            new_nickname = st.text_input(
                "Nickname",
                value=card.nickname or "",
                key=f"edit_nickname_{card.id}",
                placeholder="e.g., P2's Card",
            )

            new_opened_date = st.date_input(
                "Opened Date",
                value=card.opened_date,
                key=f"edit_opened_{card.id}",
            )

        with col2:
            new_af_date = st.date_input(
                "Annual Fee Due Date",
                value=card.annual_fee_date,
                key=f"edit_af_date_{card.id}",
            )

            new_is_business = st.checkbox(
                "Business Card",
                value=card.is_business,
                key=f"edit_is_business_{card.id}",
                help="Business cards don't count toward 5/24 (except Cap1, Discover, TD Bank)"
            )

        # Notes field (full width)
        new_notes = st.text_area(
            "Notes",
            value=card.notes or "",
            key=f"edit_notes_{card.id}",
            height=100,
        )

        # SUB tracking fields (only show if card has SUB)
        new_sub_progress = None
        new_sub_achieved = None
        new_sub_reward = None
        if card.signup_bonus:
            st.markdown("**Signup Bonus**")

            # Reward text input (full width)
            new_sub_reward = st.text_input(
                "Reward 🎁",
                value=card.signup_bonus.points_or_cash,
                key=f"edit_sub_reward_{card.id}",
                placeholder="e.g., 80,000 MR points, $500 cash, 1 free night",
                help="What you'll earn when you complete the spending requirement"
            )

            sub_col1, sub_col2 = st.columns(2)

            with sub_col1:
                new_sub_progress = st.number_input(
                    f"Spending Progress (of ${card.signup_bonus.spend_requirement:,.0f})",
                    min_value=0.0,
                    max_value=float(card.signup_bonus.spend_requirement * 2),  # Allow overspend
                    value=float(card.sub_spend_progress or 0),
                    step=100.0,
                    key=f"edit_sub_progress_{card.id}",
                )

            with sub_col2:
                new_sub_achieved = st.checkbox(
                    "SUB Achieved",
                    value=card.sub_achieved,
                    key=f"edit_sub_achieved_{card.id}",
                )

        # Retention Offers section
        st.markdown("**Retention Offers**")
        if card.retention_offers:
            for i, offer in enumerate(card.retention_offers):
                status_icon = "✓" if offer.accepted else "✗"
                st.caption(f"{status_icon} {offer.date_called}: {offer.offer_details}")
                if offer.notes:
                    st.caption(f"   Notes: {offer.notes}")

        # Add retention offer form (in expander)
        with st.expander("➕ Add Retention Offer"):
            ret_col1, ret_col2 = st.columns(2)
            with ret_col1:
                ret_date = st.date_input(
                    "Date Called",
                    value=date.today(),
                    key=f"ret_date_{card.id}",
                )
                ret_offer = st.text_input(
                    "Offer Details",
                    placeholder="e.g., 20,000 points after $2,000 spend in 3 months",
                    key=f"ret_offer_{card.id}",
                )
            with ret_col2:
                ret_accepted = st.checkbox(
                    "Accepted",
                    value=False,
                    key=f"ret_accepted_{card.id}",
                )
                ret_notes = st.text_input(
                    "Notes (optional)",
                    placeholder="e.g., Called before AF posted",
                    key=f"ret_notes_{card.id}",
                )

            if st.button("Add Offer", key=f"add_retention_{card.id}"):
                if ret_offer:
                    # Add to retention_offers list
                    new_offer = RetentionOffer(
                        date_called=ret_date,
                        offer_details=ret_offer,
                        accepted=ret_accepted,
                        notes=ret_notes if ret_notes else None,
                    )
                    updated_offers = list(card.retention_offers) + [new_offer]
                    st.session_state.storage.update_card(card.id, {"retention_offers": updated_offers})
                    st.success("Retention offer added!")
                    st.rerun()
                else:
                    st.error("Please enter offer details")

        # Product Change History section
        st.markdown("**Product Change History**")
        if card.product_change_history:
            for i, pc in enumerate(card.product_change_history):
                st.caption(f"{pc.date_changed}: {pc.from_product} → {pc.to_product}")
                if pc.reason:
                    st.caption(f"   Reason: {pc.reason}")
                if pc.notes:
                    st.caption(f"   Notes: {pc.notes}")
        else:
            st.caption("No product changes recorded")

        # Add product change form (in expander)
        with st.expander("➕ Add Product Change"):
            pc_col1, pc_col2 = st.columns(2)
            with pc_col1:
                pc_date = st.date_input(
                    "Date Changed",
                    value=date.today(),
                    key=f"pc_date_{card.id}",
                )
                pc_from = st.text_input(
                    "From Product",
                    value=card.name,
                    key=f"pc_from_{card.id}",
                    help="Original card name (pre-filled with current card)"
                )
                pc_to = st.text_input(
                    "To Product",
                    placeholder="e.g., Chase Freedom Unlimited",
                    key=f"pc_to_{card.id}",
                    help="New card name after product change"
                )
            with pc_col2:
                pc_reason = st.selectbox(
                    "Reason",
                    options=["Avoid annual fee", "Upgrade for SUB", "Better rewards category", "Other"],
                    key=f"pc_reason_{card.id}",
                )
                pc_notes = st.text_input(
                    "Notes (optional)",
                    placeholder="e.g., Called retention line first",
                    key=f"pc_notes_{card.id}",
                )

            if st.button("Add Product Change", key=f"add_pc_{card.id}"):
                if pc_from and pc_to:
                    # Add to product_change_history list
                    from src.core import ProductChange
                    new_pc = ProductChange(
                        date_changed=pc_date,
                        from_product=pc_from,
                        to_product=pc_to,
                        reason=pc_reason if pc_reason != "Other" else None,
                        notes=pc_notes if pc_notes else None,
                    )
                    updated_history = list(card.product_change_history) + [new_pc]
                    st.session_state.storage.update_card(card.id, {"product_change_history": updated_history})
                    st.success("Product change recorded!")
                    st.rerun()
                else:
                    st.error("Please enter both from and to product names")

        # Save/Cancel buttons
        btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 4])

        with btn_col1:
            if st.button("Save", key=f"save_{card.id}", type="primary"):
                # Validate inputs before saving
                validation_results = []
                validation_results.append(validate_opened_date(new_opened_date))
                validation_results.append(validate_opened_date(new_af_date))  # Annual fee date should also not be in past inappropriately

                # Show errors (blocking)
                if has_errors(validation_results):
                    for error_msg in get_error_messages(validation_results):
                        st.error(error_msg)
                    st.stop()

                # Show warnings (non-blocking)
                if has_warnings(validation_results):
                    for warning_msg in get_warning_messages(validation_results):
                        st.warning(warning_msg)

                # Build updates dict
                updates = {}
                if new_nickname != (card.nickname or ""):
                    updates["nickname"] = new_nickname if new_nickname else None
                if new_opened_date != card.opened_date:
                    updates["opened_date"] = new_opened_date
                if new_af_date != card.annual_fee_date:
                    updates["annual_fee_date"] = new_af_date
                if new_notes != (card.notes or ""):
                    updates["notes"] = new_notes if new_notes else None
                if new_is_business != card.is_business:
                    updates["is_business"] = new_is_business

                # SUB progress updates
                if card.signup_bonus:
                    # Check if reward text changed
                    if new_sub_reward and new_sub_reward != card.signup_bonus.points_or_cash:
                        # Create updated signup_bonus object
                        updated_bonus = SignupBonus(
                            points_or_cash=new_sub_reward,
                            spend_requirement=card.signup_bonus.spend_requirement,
                            time_period_days=card.signup_bonus.time_period_days,
                            deadline=card.signup_bonus.deadline
                        )
                        updates["signup_bonus"] = updated_bonus

                    if new_sub_progress is not None:
                        # Store None if 0 to keep data clean
                        progress_val = new_sub_progress if new_sub_progress > 0 else None
                        if progress_val != card.sub_spend_progress:
                            updates["sub_spend_progress"] = progress_val
                    if new_sub_achieved is not None and new_sub_achieved != card.sub_achieved:
                        updates["sub_achieved"] = new_sub_achieved

                if updates:
                    st.session_state.storage.update_card(card.id, updates)

                st.session_state[editing_key] = False
                st.rerun()

        with btn_col2:
            if st.button("Cancel", key=f"cancel_{card.id}"):
                st.session_state[editing_key] = False
                st.rerun()

        st.markdown("---")


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


def render_card_item(card, show_issuer_header: bool = True, selection_mode: bool = False):
    """Render a single card item with compact display.

    Args:
        card: Card object to render.
        show_issuer_header: Whether to show issuer (False when grouped by issuer).
        selection_mode: Whether to show selection checkbox for bulk operations.
    """
    issuer_color = get_issuer_color(card.issuer)

    # Simplified card name (without issuer since it's shown separately)
    display_name = get_display_name(card.name, card.issuer)
    if card.nickname:
        display_name = f"{card.nickname} ({display_name})"

    # Check if this card is being edited or expanded
    editing_key = f"editing_{card.id}"
    expanded_key = f"expanded_{card.id}"
    is_editing = st.session_state.get(editing_key, False)
    is_expanded = st.session_state.get(expanded_key, False)

    # Calculate unused benefits count (excluding snoozed)
    unused_benefits = 0
    is_all_snoozed = False
    if card.credits:
        # Check if all reminders are snoozed for this card
        if card.benefits_reminder_snoozed_until and card.benefits_reminder_snoozed_until > date.today():
            is_all_snoozed = True
        else:
            unused_benefits = get_unused_credits_count(card.credits, card.credit_usage)

    # Create status badges
    status_badges = []
    if card.signup_bonus and not card.sub_achieved:
        if card.signup_bonus.deadline:
            days_left = (card.signup_bonus.deadline - date.today()).days
            if days_left < 0:
                status_badges.append(('<span class="badge badge-danger">SUB EXPIRED</span>', 0))
            elif days_left <= 14:
                status_badges.append((f'<span class="badge badge-danger">SUB {days_left}d</span>', 1))
            elif days_left <= 30:
                status_badges.append((f'<span class="badge badge-warning">SUB {days_left}d</span>', 2))
        else:
            status_badges.append(('<span class="badge badge-info">SUB Active</span>', 3))

    if unused_benefits > 0 and not is_all_snoozed:
        status_badges.append((f'<span class="badge badge-warning">{unused_benefits} Benefits</span>', 2))

    # Show enrichment badge if card is from library
    if card.template_id:
        status_badges.append(('<span class="badge badge-info">✨ Library</span>', 4))

    # Sort badges by priority (lower number = higher priority)
    status_badges.sort(key=lambda x: x[1])
    badge_html = ' '.join([b[0] for b in status_badges[:3]])  # Limit to 3 badges

    with st.container():
        # Main row: [checkbox] | issuer | name | badges | fee | actions
        if selection_mode:
            if show_issuer_header:
                select_col, header_col, badge_col, fee_col, expand_col, edit_col, del_col = st.columns([0.4, 3.1, 2.5, 1, 0.5, 0.5, 0.5])
            else:
                select_col, header_col, badge_col, fee_col, expand_col, edit_col, del_col = st.columns([0.4, 3.6, 2.5, 1, 0.5, 0.5, 0.5])

            with select_col:
                is_selected = st.checkbox(
                    "",
                    value=card.id in st.session_state.selected_cards,
                    key=f"select_{card.id}",
                    label_visibility="collapsed"
                )
                if is_selected:
                    st.session_state.selected_cards.add(card.id)
                else:
                    st.session_state.selected_cards.discard(card.id)
        else:
            if show_issuer_header:
                header_col, badge_col, fee_col, expand_col, edit_col, del_col = st.columns([3.5, 2.5, 1, 0.5, 0.5, 0.5])
            else:
                header_col, badge_col, fee_col, expand_col, edit_col, del_col = st.columns([4, 2.5, 1, 0.5, 0.5, 0.5])

        with header_col:
            if show_issuer_header:
                st.markdown(
                    f"<div style='padding: 4px 0;'>"
                    f"<span style='color: {issuer_color}; font-weight: 600; font-size: 0.9rem;'>{card.issuer}</span><br>"
                    f"<span style='font-weight: 500; font-size: 1.05rem;'>{display_name}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(f"<div style='padding: 4px 0; font-weight: 500; font-size: 1.05rem;'>{display_name}</div>", unsafe_allow_html=True)

        with badge_col:
            if badge_html:
                st.markdown(f"<div style='padding: 8px 0;'>{badge_html}</div>", unsafe_allow_html=True)

        with fee_col:
            if card.annual_fee > 0:
                st.markdown(f"<div style='padding: 8px 0; text-align: right;'>${card.annual_fee}/yr</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='padding: 8px 0; text-align: right; color: #28a745;'>No AF</div>", unsafe_allow_html=True)

        with expand_col:
            expand_icon = "▼" if not is_expanded else "▲"
            if st.button(expand_icon, key=f"expand_{card.id}", help="Show/hide details"):
                st.session_state[expanded_key] = not is_expanded
                st.rerun()

        with edit_col:
            if st.button("✎" if not is_editing else "✕", key=f"edit_{card.id}", help="Edit card"):
                st.session_state[editing_key] = not is_editing
                st.rerun()

        with del_col:
            if st.button("🗑", key=f"del_{card.id}", help="Delete card"):
                st.session_state[f"confirm_delete_{card.id}"] = True
                st.rerun()

        # Delete confirmation
        confirm_key = f"confirm_delete_{card.id}"
        if st.session_state.get(confirm_key, False):
            st.warning(f"Delete **{card.nickname or display_name}**? This cannot be undone.")
            cancel_col, confirm_col, spacer_col = st.columns([1, 1, 4])
            with cancel_col:
                if st.button("Cancel", key=f"cancel_del_{card.id}"):
                    st.session_state[confirm_key] = False
                    st.rerun()
            with confirm_col:
                if st.button("Delete", key=f"confirm_del_{card.id}", type="primary"):
                    st.session_state.storage.delete_card(card.id)
                    st.session_state[confirm_key] = False
                    st.rerun()
            return

        # Edit form
        if is_editing:
            render_card_edit_form(card, editing_key)
            return

        # Show SUB progress inline if active (not achieved)
        if card.signup_bonus and not card.sub_achieved:
            # Show reward at the top prominently
            st.markdown(
                f"<div style='margin-bottom: 10px; padding: 8px 12px; background: linear-gradient(135deg, #e7f3ff 0%, #cfe9ff 100%); "
                f"border-radius: 6px; border-left: 4px solid #0066cc;'>"
                f"<span style='font-size: 0.85rem; color: #004085; font-weight: 500;'>🎁 REWARD</span><br>"
                f"<span style='font-size: 1.1rem; color: #003366; font-weight: 700;'>{card.signup_bonus.points_or_cash}</span>"
                f"</div>",
                unsafe_allow_html=True
            )

            sub_col1, sub_col2 = st.columns([4, 1])

            with sub_col1:
                if card.sub_spend_progress is not None:
                    progress = min(card.sub_spend_progress / card.signup_bonus.spend_requirement, 1.0)
                    remaining = max(0, card.signup_bonus.spend_requirement - card.sub_spend_progress)

                    # Progress percentage
                    progress_pct = int(progress * 100)

                    # Create visual progress bar with HTML/CSS
                    if progress >= 1.0:
                        bar_color = "#28a745"
                        text_color = "#155724"
                    elif progress >= 0.75:
                        bar_color = "#20c997"
                        text_color = "#0c5460"
                    elif progress >= 0.5:
                        bar_color = "#ffc107"
                        text_color = "#856404"
                    else:
                        bar_color = "#6c757d"
                        text_color = "#383d41"

                    st.markdown(
                        f"<div style='margin-bottom: 4px;'>"
                        f"<span style='font-weight: 600; color: {text_color};'>Spending Progress: {progress_pct}%</span>"
                        f"<span style='float: right; color: #6c757d;'>${card.sub_spend_progress:,.0f} / ${card.signup_bonus.spend_requirement:,.0f}</span>"
                        f"</div>"
                        f"<div style='background: #e9ecef; border-radius: 4px; height: 8px; overflow: hidden;'><!-- no text content -->"
                        f"<div style='background: {bar_color}; height: 100%; width: {progress_pct}%; transition: width 0.3s;'><!-- no text content --></div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                    if remaining > 0:
                        st.caption(f"💳 ${remaining:,.0f} remaining to unlock reward")
                    else:
                        st.caption("✓ Spend requirement met!")
                else:
                    st.markdown(
                        f"<div style='color: #6c757d;'>"
                        f"<span style='font-weight: 600;'>Spend Target:</span> ${card.signup_bonus.spend_requirement:,.0f}"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                # Show deadline info inline
                if card.signup_bonus.deadline:
                    days_left = (card.signup_bonus.deadline - date.today()).days
                    if days_left < 0:
                        st.markdown('<span class="badge badge-danger">Deadline Passed</span>', unsafe_allow_html=True)
                    elif days_left <= 14:
                        st.markdown(f'<span class="badge badge-danger">⏰ {days_left} days left</span>', unsafe_allow_html=True)
                    elif days_left <= 30:
                        st.markdown(f'<span class="badge badge-warning">⏰ {days_left} days left</span>', unsafe_allow_html=True)
                    else:
                        st.caption(f"Deadline: {card.signup_bonus.deadline} ({days_left}d)")

            with sub_col2:
                if st.button("✓ Complete", key=f"sub_complete_{card.id}", help="Mark signup bonus as achieved", use_container_width=True):
                    st.session_state.storage.update_card(card.id, {"sub_achieved": True})
                    st.rerun()

        # Show unused benefits indicator (preview row)
        if unused_benefits > 0 and not is_all_snoozed:
            st.markdown(
                f"<div style='background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%); "
                f"padding: 10px 14px; border-radius: 8px; margin: 8px 0; "
                f"border-left: 4px solid #ffc107; display: flex; justify-content: space-between; align-items: center;'>"
                f"<span style='color: #856404; font-weight: 600;'>⚡ {unused_benefits} benefit(s) available this period</span>"
                f"</div>",
                unsafe_allow_html=True
            )
            snooze_col1, snooze_col2 = st.columns([6, 1])
            with snooze_col2:
                if st.button("Dismiss", key=f"snooze_all_{card.id}", help="Snooze reminders for 30 days", use_container_width=True):
                    snooze_until = date.today() + timedelta(days=30)
                    st.session_state.storage.update_card(card.id, {"benefits_reminder_snoozed_until": snooze_until})
                    st.rerun()
        elif is_all_snoozed:
            # Show option to unsnooze
            days_until_unsnooze = (card.benefits_reminder_snoozed_until - date.today()).days
            st.markdown(
                f"<div style='background: #e9ecef; padding: 8px 14px; border-radius: 8px; margin: 8px 0; "
                f"display: flex; justify-content: space-between; align-items: center;'>"
                f"<span style='color: #6c757d; font-size: 0.9rem;'>🔕 Reminders snoozed ({days_until_unsnooze}d remaining)</span>"
                f"</div>",
                unsafe_allow_html=True
            )
            unsnooze_col1, unsnooze_col2 = st.columns([6, 1])
            with unsnooze_col2:
                if st.button("Restore", key=f"unsnooze_{card.id}", help="Show benefit reminders again", use_container_width=True):
                    st.session_state.storage.update_card(card.id, {"benefits_reminder_snoozed_until": None})
                    st.rerun()

        # Expanded details (only show when expanded)
        if is_expanded:
            st.markdown("---")
            detail_col1, detail_col2 = st.columns(2)

            with detail_col1:
                if card.opened_date:
                    days_held = (date.today() - card.opened_date).days
                    st.caption(f"Opened: {card.opened_date} ({days_held}d ago)")

                if card.annual_fee_date:
                    days_until_af = (card.annual_fee_date - date.today()).days
                    if days_until_af <= 30:
                        st.error(f"Annual Fee Due: {card.annual_fee_date} ({days_until_af}d)")
                    else:
                        st.caption(f"Annual Fee Due: {card.annual_fee_date} ({days_until_af}d)")

                if card.signup_bonus:
                    if card.sub_achieved:
                        st.markdown(
                            f"<div style='background: #d4edda; padding: 8px 12px; border-radius: 6px; border-left: 4px solid #28a745;'>"
                            f"<span style='font-size: 0.8rem; color: #155724; font-weight: 500;'>✓ SUB EARNED</span><br>"
                            f"<span style='color: #0c5c2c; font-weight: 600;'>{card.signup_bonus.points_or_cash}</span>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.caption(f"SUB: {card.signup_bonus.points_or_cash}")

                if card.notes:
                    st.caption(f"Notes: {card.notes}")

            with detail_col2:
                if card.credits:
                    st.markdown("**Benefits Tracker:**")
                    total_value = 0

                    for credit in card.credits:
                        # Calculate annual value
                        if credit.frequency == "monthly":
                            annual = credit.amount * 12
                        elif credit.frequency == "quarterly":
                            annual = credit.amount * 4
                        elif credit.frequency in ["semi-annual", "semi-annually"]:
                            annual = credit.amount * 2
                        else:
                            annual = credit.amount
                        total_value += annual

                        # Get current period for this credit
                        period_name = get_period_display_name(credit.frequency)
                        is_used = is_credit_used_this_period(credit.name, credit.frequency, card.credit_usage)

                        # Create visual benefit item
                        if is_used:
                            bg_color = "#d4edda"
                            border_color = "#28a745"
                            icon = "✓"
                            icon_color = "#28a745"
                        else:
                            bg_color = "#fff3cd"
                            border_color = "#ffc107"
                            icon = "○"
                            icon_color = "#856404"

                        # Checkbox for marking as used
                        checkbox_key = f"credit_{card.id}_{credit.name}"

                        col1, col2 = st.columns([0.3, 5])
                        with col1:
                            st.markdown(
                                f"<div style='font-size: 1.5rem; color: {icon_color}; text-align: center;'>{icon}</div>",
                                unsafe_allow_html=True
                            )
                        with col2:
                            used = st.checkbox(
                                f"**${credit.amount}** {credit.name}",
                                value=is_used,
                                key=checkbox_key,
                                help=f"{period_name} - click to mark as {'unused' if is_used else 'used'}",
                                label_visibility="visible"
                            )

                        # Update if changed
                        if used != is_used:
                            new_usage = dict(card.credit_usage)  # Copy
                            if used:
                                new_usage = mark_credit_used(credit.name, credit.frequency, new_usage)
                            else:
                                new_usage = mark_credit_unused(credit.name, new_usage)
                            # Save to storage
                            st.session_state.storage.update_card(card.id, {"credit_usage": new_usage})
                            st.rerun()

                        st.caption(f"↻ Resets: {period_name}")
                        st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

                    # Total value summary
                    st.markdown(
                        f"<div style='background: #e7f3ff; padding: 10px; border-radius: 6px; margin-top: 12px;'>"
                        f"<span style='font-weight: 600; color: #004085;'>Annual Value: ~${total_value:,.0f}</span>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

        st.write("")  # Spacing


def render_empty_dashboard():
    """Render a welcoming empty state when no cards exist."""
    st.markdown("---")

    # Centered welcome message
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### Welcome to ChurnPilot!")
        st.write("Start tracking your credit cards to manage benefits and deadlines.")

        st.markdown("**Quick start:**")
        st.markdown("1. Switch to the **Add Card** tab above")
        st.markdown("2. Select a card from the library or paste card details")
        st.markdown("3. Track your credits and signup bonus deadlines")

        st.markdown("---")

        # Show available templates count
        templates = get_all_templates()
        st.info(f"Library includes {len(templates)} popular card templates ready to use.")

        # Popular cards quick suggestions
        st.markdown("**Popular cards in library:**")
        popular = ["amex_platinum", "chase_sapphire_reserve", "capital_one_venture_x"]
        for template_id in popular:
            template = get_template(template_id)
            if template:
                st.caption(f"- {template.name} (${template.annual_fee}/yr)")


def render_empty_filter_results(issuer_filter: str, search_query: str):
    """Render empty state when filters return no results."""
    st.info("No cards match your filters.")

    col1, col2, col3 = st.columns([1, 1, 3])

    with col1:
        if issuer_filter != "All Issuers":
            if st.button("Clear Issuer Filter"):
                st.session_state["issuer_filter"] = "All Issuers"
                st.rerun()

    with col2:
        if search_query:
            if st.button("Clear Search"):
                st.session_state["search_query"] = ""
                st.rerun()

    # Helpful suggestions
    st.caption("Try adjusting your filters or search term.")


def export_cards_to_csv(cards):
    """Export cards to CSV format.

    Args:
        cards: List of Card objects to export

    Returns:
        CSV string ready for download
    """
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    # CSV header
    writer.writerow([
        "Card Name",
        "Issuer",
        "Nickname",
        "Annual Fee",
        "Opened Date",
        "Annual Fee Date",
        "Is Business",
        "Closed Date",
        "SUB Reward",
        "SUB Spend Requirement",
        "SUB Deadline",
        "SUB Achieved",
        "Credits (Name: Amount, Frequency)",
        "Notes"
    ])

    # Data rows
    for card in cards:
        # Format credits
        credits_str = "; ".join([
            f"{c.name}: ${c.amount}, {c.frequency}"
            for c in card.credits
        ]) if card.credits else ""

        # Format SUB info
        sub_reward = card.signup_bonus.points_or_cash if card.signup_bonus else ""
        sub_requirement = card.signup_bonus.spend_requirement if card.signup_bonus else ""
        sub_deadline = card.signup_bonus.deadline if card.signup_bonus else ""

        writer.writerow([
            card.name,
            card.issuer,
            card.nickname or "",
            card.annual_fee,
            card.opened_date or "",
            card.annual_fee_date or "",
            "Yes" if card.is_business else "No",
            card.closed_date or "",
            sub_reward,
            sub_requirement,
            sub_deadline,
            "Yes" if card.sub_achieved else "No",
            credits_str,
            card.notes or ""
        ])

    return output.getvalue()


def render_dashboard():
    """Render the card dashboard with filtering, sorting, and grouping."""
    col_header, col_export = st.columns([3, 1])
    with col_header:
        st.header("Your Cards")
    with col_export:
        st.write("")  # Spacing

    cards = st.session_state.storage.get_all_cards()

    if not cards:
        render_empty_dashboard()
        return

    # Export button in the column
    with col_export:
        csv_data = export_cards_to_csv(cards)
        st.download_button(
            label="Export to CSV",
            data=csv_data,
            file_name=f"churnpilot_cards_{date.today()}.csv",
            mime="text/csv",
            help="Download all cards as CSV spreadsheet"
        )

    # Calculate comprehensive metrics
    total_fees = sum(c.annual_fee for c in cards)

    # Calculate total annual credits value
    total_credits_value = 0
    for c in cards:
        for credit in c.credits:
            if credit.frequency == "monthly":
                total_credits_value += credit.amount * 12
            elif credit.frequency == "quarterly":
                total_credits_value += credit.amount * 4
            elif credit.frequency in ["semi-annual", "semi-annually"]:
                total_credits_value += credit.amount * 2
            else:
                total_credits_value += credit.amount

    # Calculate benefits usage stats
    total_benefits = sum(len(c.credits) for c in cards)
    unused_benefits_total = sum(get_unused_credits_count(c.credits, c.credit_usage) for c in cards)

    # SUB tracking
    cards_with_sub = [c for c in cards if c.signup_bonus and not c.sub_achieved]
    urgent_subs = [
        c for c in cards_with_sub
        if c.signup_bonus.deadline and (c.signup_bonus.deadline - date.today()).days <= 30
    ]

    # Net value calculation (credits - fees)
    net_value = total_credits_value - total_fees

    # Summary metrics row with enhanced styling
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("💳 Total Cards", len(cards))

    with col2:
        st.metric("💰 Annual Fees", f"${total_fees:,}")

    with col3:
        st.metric("🎁 Benefits Value", f"${total_credits_value:,.0f}/yr")

    with col4:
        if urgent_subs:
            st.metric("⚠️ Urgent SUBs", len(urgent_subs), delta=f"{len(urgent_subs)} need attention", delta_color="inverse")
        elif cards_with_sub:
            st.metric("🎯 Active SUBs", len(cards_with_sub))
        else:
            st.metric("✓ All SUBs", "Complete")

    # Secondary metrics row
    if total_benefits > 0:
        st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)
        metric_col1, metric_col2, metric_col3 = st.columns(3)

        with metric_col1:
            if net_value > 0:
                st.metric("📊 Net Value", f"${net_value:,.0f}/yr", delta="Positive", delta_color="normal")
            else:
                st.metric("📊 Net Value", f"-${abs(net_value):,.0f}/yr", delta="Negative", delta_color="inverse")

        with metric_col2:
            if unused_benefits_total > 0:
                st.metric("⚡ Pending Benefits", unused_benefits_total, delta="Action available", delta_color="off")
            else:
                st.metric("✓ Benefits Status", "All used")

        with metric_col3:
            usage_pct = int(((total_benefits - unused_benefits_total) / total_benefits * 100)) if total_benefits > 0 else 0
            st.metric("📈 Usage Rate", f"{usage_pct}%")

    st.divider()

    # Initialize selected cards in session state
    if "selected_cards" not in st.session_state:
        st.session_state.selected_cards = set()

    # Bulk actions row (selection mode toggle)
    bulk_col1, bulk_col2 = st.columns([1, 7])

    with bulk_col1:
        selection_mode = st.checkbox("Select", key="selection_mode", help="Enable multi-select to delete multiple cards")

    # Clear selection when exiting selection mode
    if not selection_mode and st.session_state.selected_cards:
        st.session_state.selected_cards = set()

    # Get current preferences
    prefs = st.session_state.prefs

    # Filter, sort, group controls
    filter_col, sort_col, group_col, search_col = st.columns([2, 2, 1, 3])

    with filter_col:
        issuers = sorted(set(c.issuer for c in cards))
        issuer_filter = st.selectbox(
            "Filter",
            options=["All Issuers"] + issuers,
            key="issuer_filter",
        )

    with sort_col:
        # Map user-friendly names to preference values
        sort_options = {
            "Date Added": "date_added",
            "Date Opened": "date_opened",
            "Name (A-Z)": "name_asc",
            "Name (Z-A)": "name_desc",
            "Annual Fee (High)": "fee_desc",
            "Annual Fee (Low)": "fee_asc",
        }
        # Find current selection from prefs
        current_sort = next(
            (k for k, v in sort_options.items() if v == prefs.sort_by),
            "Date Added"
        )
        sort_option = st.selectbox(
            "Sort",
            options=list(sort_options.keys()),
            index=list(sort_options.keys()).index(current_sort),
            key="sort_option",
        )
        # Save preference if changed
        new_sort_value = sort_options[sort_option]
        if new_sort_value != prefs.sort_by:
            prefs.sort_by = new_sort_value
            st.session_state.prefs_storage.save_preferences(prefs)

    with group_col:
        group_by_issuer = st.checkbox(
            "Group",
            value=prefs.group_by_issuer,
            key="group_by_issuer",
            help="Group cards by issuer"
        )
        # Save preference if changed
        if group_by_issuer != prefs.group_by_issuer:
            prefs.group_by_issuer = group_by_issuer
            st.session_state.prefs_storage.save_preferences(prefs)

    with search_col:
        search_query = st.text_input(
            "Search",
            placeholder="Search by name or nickname...",
            key="search_query",
            label_visibility="collapsed",
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
    from datetime import datetime as dt
    if sort_option == "Date Added":
        # Sort by created_at, newest first (cards without created_at go last)
        filtered_cards = sorted(
            filtered_cards,
            key=lambda c: c.created_at if c.created_at else dt.min,
            reverse=True
        )
    elif sort_option == "Date Opened":
        filtered_cards = sorted(
            filtered_cards,
            key=lambda c: c.opened_date if c.opened_date else date.min,
            reverse=True
        )
    elif sort_option == "Name (A-Z)":
        filtered_cards = sorted(filtered_cards, key=lambda c: c.name.lower())
    elif sort_option == "Name (Z-A)":
        filtered_cards = sorted(filtered_cards, key=lambda c: c.name.lower(), reverse=True)
    elif sort_option == "Annual Fee (High)":
        filtered_cards = sorted(filtered_cards, key=lambda c: c.annual_fee, reverse=True)
    elif sort_option == "Annual Fee (Low)":
        filtered_cards = sorted(filtered_cards, key=lambda c: c.annual_fee)

    # Clean up selection - only keep cards that are currently visible
    if selection_mode:
        filtered_card_ids = {c.id for c in filtered_cards}
        st.session_state.selected_cards = st.session_state.selected_cards.intersection(filtered_card_ids)

    # Show filter results count and bulk delete button
    if len(filtered_cards) != len(cards):
        count_col, action_col = st.columns([6, 2])
        with count_col:
            st.caption(f"Showing {len(filtered_cards)} of {len(cards)} cards")
        with action_col:
            if selection_mode and st.session_state.selected_cards:
                if st.button(f"Delete {len(st.session_state.selected_cards)} Selected", type="primary", use_container_width=True, key="bulk_delete_btn"):
                    st.session_state.confirm_bulk_delete = True
                    st.rerun()
    else:
        if selection_mode and st.session_state.selected_cards:
            action_col1, action_col2 = st.columns([6, 2])
            with action_col2:
                if st.button(f"Delete {len(st.session_state.selected_cards)} Selected", type="primary", use_container_width=True, key="bulk_delete_btn2"):
                    st.session_state.confirm_bulk_delete = True
                    st.rerun()

    # Bulk delete confirmation
    if st.session_state.get("confirm_bulk_delete", False):
        st.warning(f"⚠️ Delete {len(st.session_state.selected_cards)} cards? This cannot be undone.")
        confirm_col1, confirm_col2, confirm_col3 = st.columns([1, 1, 4])
        with confirm_col1:
            if st.button("Cancel", key="cancel_bulk_delete"):
                st.session_state.confirm_bulk_delete = False
                st.rerun()
        with confirm_col2:
            if st.button("Delete All", key="confirm_bulk_delete_btn", type="primary"):
                # Delete all selected cards
                for card_id in st.session_state.selected_cards:
                    st.session_state.storage.delete_card(card_id)
                st.session_state.selected_cards = set()
                st.session_state.confirm_bulk_delete = False
                st.success("Cards deleted successfully!")
                st.rerun()

    st.divider()

    # Card list
    if not filtered_cards:
        render_empty_filter_results(issuer_filter, search_query)
        return

    # Render cards (grouped or flat)
    if group_by_issuer and issuer_filter == "All Issuers":
        # Group by issuer
        issuers_in_list = sorted(set(c.issuer for c in filtered_cards))
        for issuer in issuers_in_list:
            issuer_color = get_issuer_color(issuer)
            st.markdown(
                f"<h4 style='color: {issuer_color}; margin-bottom: 0;'>{issuer}</h4>",
                unsafe_allow_html=True
            )
            issuer_cards = [c for c in filtered_cards if c.issuer == issuer]
            for card in issuer_cards:
                render_card_item(card, show_issuer_header=False, selection_mode=selection_mode)
            st.write("")  # Space between groups
    else:
        # Flat list
        for card in filtered_cards:
            render_card_item(card, show_issuer_header=True, selection_mode=selection_mode)


def render_action_required_tab():
    """Render the Action Required tab showing urgent items."""
    st.header("Action Required")

    storage = CardStorage()
    cards = storage.get_all_cards()

    if not cards:
        st.info("No cards yet. Add cards to see action items.")
        return

    today = date.today()

    # Collect urgent items
    urgent_subs = []
    upcoming_fees = []
    unused_credits = []
    missing_data = []

    for card in cards:
        display_name = get_display_name(card.name, card.issuer)
        if card.nickname:
            display_name = f"{card.nickname} ({display_name})"

        # Check SUB deadlines
        if card.signup_bonus and card.signup_bonus.deadline and not card.sub_achieved:
            days_left = (card.signup_bonus.deadline - today).days
            if days_left <= 30:
                urgent_subs.append({
                    "card": card,
                    "display_name": display_name,
                    "days_left": days_left,
                    "deadline": card.signup_bonus.deadline,
                    "requirement": card.signup_bonus.spend_requirement,
                    "reward": card.signup_bonus.points_or_cash
                })

        # Check annual fees
        if card.annual_fee > 0 and card.annual_fee_date:
            try:
                fee_date = datetime.strptime(card.annual_fee_date, "%Y-%m-%d").date()
                days_until = (fee_date - today).days
                if 0 <= days_until <= 60:
                    upcoming_fees.append({
                        "card": card,
                        "display_name": display_name,
                        "days_until": days_until,
                        "fee_date": fee_date,
                        "amount": card.annual_fee
                    })
            except:
                pass

        # Check unused credits
        for credit in card.credits:
            if credit.amount > 0:
                is_used = is_credit_used_this_period(credit.name, credit.frequency, card.credit_usage)
                if not is_used:
                    unused_credits.append({
                        "card": card,
                        "display_name": display_name,
                        "credit_name": credit.name,
                        "amount": credit.amount,
                        "frequency": credit.frequency
                    })

        # Check missing opened_date (blocks 5/24 tracking)
        if not card.opened_date and not card.closed_date:
            missing_data.append({
                "card": card,
                "display_name": display_name
            })

    # Display urgent items
    total_items = len(urgent_subs) + len(upcoming_fees) + len(unused_credits) + len(missing_data)

    if total_items == 0:
        st.success("All clear! No urgent action items.")
        return

    st.info(f"{total_items} items need attention")

    # Section 1: Urgent SUB deadlines (< 30 days)
    if urgent_subs:
        st.subheader(f"Signup Bonuses ({len(urgent_subs)})")
        st.caption("Complete minimum spend before deadline to earn bonus")

        urgent_subs.sort(key=lambda x: x["days_left"])

        for item in urgent_subs:
            days = item["days_left"]
            if days < 0:
                urgency = "EXPIRED"
                color = "#dc3545"
            elif days <= 7:
                urgency = "URGENT"
                color = "#dc3545"
            elif days <= 14:
                urgency = "SOON"
                color = "#fd7e14"
            else:
                urgency = "ATTENTION"
                color = "#ffc107"

            st.markdown(
                f"<div style='padding: 12px; margin: 8px 0; border-left: 4px solid {color}; background: #f8f9fa; border-radius: 4px; color: #262730;'>"
                f"<span style='font-weight: 600;'>[{urgency}] {item['display_name']}</span><br>"
                f"<span style='color: #6c757d; font-size: 0.9rem;'>"
                f"Deadline: {item['deadline']} ({days} days) | "
                f"Requirement: ${item['requirement']:,.0f} | "
                f"Reward: {item['reward']}"
                f"</span>"
                f"</div>",
                unsafe_allow_html=True
            )

    # Section 2: Upcoming annual fees
    if upcoming_fees:
        st.subheader(f"Annual Fees ({len(upcoming_fees)})")
        st.caption("Consider calling for retention offers or canceling before fee posts")

        upcoming_fees.sort(key=lambda x: x["days_until"])

        for item in upcoming_fees:
            days = item["days_until"]
            if days <= 14:
                color = "#dc3545"
            elif days <= 30:
                color = "#fd7e14"
            else:
                color = "#ffc107"

            st.markdown(
                f"<div style='padding: 12px; margin: 8px 0; border-left: 4px solid {color}; background: #f8f9fa; border-radius: 4px; color: #262730;'>"
                f"<span style='font-weight: 600;'>{item['display_name']}</span><br>"
                f"<span style='color: #6c757d; font-size: 0.9rem;'>"
                f"Fee: ${item['amount']:.0f} | Due: {item['fee_date']} ({days} days)"
                f"</span>"
                f"</div>",
                unsafe_allow_html=True
            )

    # Section 3: Unused credits
    if unused_credits:
        st.subheader(f"Unused Credits ({len(unused_credits)})")
        st.caption("Check off benefits as you use them - changes sync to Dashboard")

        # Group by card
        credits_by_card = {}
        for item in unused_credits:
            card_name = item["display_name"]
            if card_name not in credits_by_card:
                credits_by_card[card_name] = []
            credits_by_card[card_name].append(item)

        for card_name, credits in credits_by_card.items():
            total_value = sum(c["amount"] for c in credits)
            with st.expander(f"{card_name} - ${total_value:.0f} available", expanded=True):
                for credit in credits:
                    # Get current period for display
                    from src.core import get_current_period
                    period = get_current_period(credit['frequency'])

                    # Format period nicely for display
                    if credit['frequency'].lower() == 'monthly':
                        # "2026-01" -> "2026 Jan"
                        year, month_num = period.split('-')
                        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                        period_display = f"{year} {month_names[int(month_num) - 1]}"
                    else:
                        # "2024-Q1" -> "2024 Q1", "2024-H1" -> "2024 H1", "2024" -> "2024"
                        period_display = period.replace('-', ' ')

                    # Build display label with period
                    benefit_label = f"{credit['credit_name']}: ${credit['amount']:.0f} ({credit['frequency']}) {period_display}"

                    # Checkbox that marks the credit as used when checked
                    checkbox_key = f"use_{credit['card'].id}_{credit['credit_name']}"
                    is_checked = st.checkbox(
                        benefit_label,
                        value=False,
                        key=checkbox_key
                    )

                    # If checkbox state changed to checked, mark credit as used
                    if is_checked:
                        from src.core import mark_credit_used
                        new_usage = mark_credit_used(
                            credit['credit_name'],
                            credit['frequency'],
                            credit['card'].credit_usage,
                            date.today()
                        )
                        storage.update_card(credit['card'].id, {"credit_usage": new_usage})
                        st.rerun()

    # Section 4: Missing data
    if missing_data:
        st.subheader(f"Missing Data ({len(missing_data)})")
        st.caption("Add opened dates to enable 5/24 tracking and deadline calculations")

        for item in missing_data:
            st.markdown(
                f"<div style='padding: 8px; margin: 4px 0; border-left: 3px solid #6c757d; background: #f8f9fa; border-radius: 4px; color: #262730;'>"
                f"<span style='font-weight: 500;'>{item['display_name']}</span> - No opened date"
                f"</div>",
                unsafe_allow_html=True
            )

def render_five_twenty_four_tab():
    """Render the 5/24 tracking tab."""
    st.header("Chase 5/24 Rule Tracker")

    cards = st.session_state.storage.get_all_cards()

    if not cards:
        st.info("Add cards with opened dates to track your 5/24 status.")
        return

    # Calculate status
    five_24 = calculate_five_twenty_four_status(cards)

    # Status summary
    col1, col2, col3 = st.columns(3)

    with col1:
        if five_24["status"] == "under":
            st.success(f"**{five_24['count']}/5**")
            st.caption("You can apply for Chase cards")
        elif five_24["status"] == "at":
            st.warning(f"**{five_24['count']}/5**")
            st.caption("At limit - risky to apply")
        else:
            st.error(f"**{five_24['count']}/5**")
            st.caption("Over limit - will be denied")

    with col2:
        if five_24["next_drop_off"]:
            st.metric("Next Card Drops", f"{five_24['days_until_drop']} days")
            st.caption(f"On {five_24['next_drop_off']}")
        else:
            st.info("No cards in 24-month window")

    with col3:
        personal_count = len([c for c in cards if not c.is_business and c.opened_date])
        business_count = len([c for c in cards if c.is_business and c.opened_date])
        st.metric("Total Cards", personal_count + business_count)
        st.caption(f"{personal_count} personal, {business_count} business")

    st.divider()

    # Explanation
    with st.expander("What is the 5/24 rule?"):
        st.markdown("""
        **The Chase 5/24 Rule**: Chase will deny your application if you've opened **5 or more personal credit cards
        from ANY issuer** in the past 24 months.

        **What counts toward 5/24:**
        - **Personal credit cards** from any bank (including charge cards like Amex Platinum if they're personal)
        - Authorized user cards (can be removed from credit report)
        - Store cards on major networks (Visa, MC, Amex, Discover)
        - Any card that appears on your **personal credit report**

        **What doesn't count:**
        - **Business cards** from most issuers (they don't report to personal credit)
          - **EXCEPTION**: Capital One, Discover, and TD Bank business cards DO count (they report to personal credit)
        - Denied applications

        **Key principle**: If a card reports on your personal credit report, it counts toward 5/24 - whether it's a
        charge card or traditional credit card doesn't matter, and whether it's open or closed doesn't matter.

        **Drop-off timing**: Cards drop off on the **first day of the 25th month** after opening.
        Example: Card opened Jan 15, 2024 → drops off Feb 1, 2026.
        """)

    # Timeline of cards
    st.subheader("5/24 Timeline")

    timeline = get_five_twenty_four_timeline(cards)

    if not timeline:
        st.info("No cards currently counting toward 5/24.")
        return

    # Display timeline
    for item in timeline:
        card = item["card"]
        drop_off = item["drop_off_date"]
        days = item["days_until"]

        display_name = get_display_name(card.name, card.issuer)
        if card.nickname:
            display_name = f"{card.nickname} ({display_name})"

        # Color code by urgency
        if days <= 30:
            color = "#28a745"  # Green - drops soon
        elif days <= 180:
            color = "#ffc107"  # Yellow
        else:
            color = "#6c757d"  # Gray

        st.markdown(
            f"<div style='padding: 12px; margin: 8px 0; border-left: 4px solid {color}; background: #f8f9fa; border-radius: 4px; color: #262730;'>"
            f"<span style='font-weight: 600;'>{display_name}</span><br>"
            f"<span style='color: #6c757d; font-size: 0.9rem;'>Opened: {card.opened_date} | Drops off: {drop_off} ({days} days)</span>"
            f"</div>",
            unsafe_allow_html=True
        )


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="ChurnPilot",
        page_icon="💳",
        layout="wide",
    )

    # Inject custom CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    init_session_state()
    render_sidebar()

    # Show welcome message for new users
    cards = st.session_state.storage.get_all_cards()
    if len(cards) == 0:
        st.markdown("""
        <div style="padding: 1.2rem; background-color: rgba(33, 195, 84, 0.1); border: 1px solid rgba(33, 195, 84, 0.3); border-radius: 0.5rem; border-left: 4px solid rgba(33, 195, 84, 0.8);">

        <div style="font-size: 1.1rem; margin-bottom: 0.5rem;">👋 <strong>Welcome to ChurnPilot!</strong></div>

        <p style="margin: 0.5rem 0;">ChurnPilot helps you track credit card signup bonuses, benefits, and deadlines.</p>

        <p style="margin-top: 1rem; margin-bottom: 0.3rem;"><strong>Quick Start:</strong></p>
        <ol style="margin-top: 0.3rem;">
        <li style="margin: 0.3rem 0;">Switch to the <strong style="padding: 2px 6px; border-radius: 4px; border: 1px solid rgba(33, 195, 84, 0.5); background-color: rgba(33, 195, 84, 0.15);">Add Card</strong> tab above to add your first card</li>
        <li style="margin: 0.3rem 0;">Select from library, extract from URL, or import a spreadsheet</li>
        </ol>

        <p style="margin-top: 1rem; margin-bottom: 0.3rem;"><strong>What ChurnPilot tracks:</strong></p>
        <ul style="margin-top: 0.3rem;">
        <li style="margin: 0.2rem 0;">Benefit usage (Uber credits, hotel credits, etc.)</li>
        <li style="margin: 0.2rem 0;">Signup bonus deadlines (don't miss out on points!)</li>
        <li style="margin: 0.2rem 0;">Annual fee dates (call for retention offers in time)</li>
        <li style="margin: 0.2rem 0;">Chase 5/24 status (know when you can apply for more Chase cards)</li>
        </ul>

        </div>
        """, unsafe_allow_html=True)

    # Four main tabs (reordered: Dashboard → Action Required → Add Card → 5/24 Tracker)
    tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Action Required", "Add Card", "5/24 Tracker"])

    with tab1:
        render_dashboard()

    with tab2:
        render_action_required_tab()

    with tab3:
        render_add_card_section()

    with tab4:
        render_five_twenty_four_tab()


if __name__ == "__main__":
    main()
