"""Mobile Bottom Sheet Pattern component.

A modal that slides up from the bottom of the screen, commonly used for
mobile-first interfaces. Provides a native mobile app-like experience.
"""

import streamlit as st
from dataclasses import dataclass
from typing import Optional, Callable, Literal


@dataclass
class BottomSheet:
    """Configuration for a bottom sheet modal.

    Attributes:
        key: Unique identifier for this bottom sheet instance.
        title: Optional header title for the sheet.
        height: Height preset - 'auto', 'half', 'full', or specific pixels.
        show_handle: Whether to show the drag handle indicator.
        dismissible: Whether the sheet can be dismissed by clicking outside.
        on_dismiss: Callback when sheet is dismissed.
    """
    key: str
    title: Optional[str] = None
    height: Literal["auto", "half", "full"] | int = "auto"
    show_handle: bool = True
    dismissible: bool = True
    on_dismiss: Optional[Callable] = None


# CSS for bottom sheet styling
BOTTOM_SHEET_CSS = """
<style>
/* Bottom Sheet Overlay */
.bottom-sheet-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 9998;
    animation: fadeIn 0.2s ease-out;
}

/* Bottom Sheet Container */
.bottom-sheet {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: white;
    border-radius: 20px 20px 0 0;
    box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.15);
    z-index: 9999;
    animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    max-height: 90vh;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}

.bottom-sheet.height-auto {
    min-height: 200px;
    max-height: 80vh;
}

.bottom-sheet.height-half {
    height: 50vh;
}

.bottom-sheet.height-full {
    height: 90vh;
    border-radius: 20px 20px 0 0;
}

/* Drag Handle */
.bottom-sheet-handle {
    width: 36px;
    height: 5px;
    background: #dee2e6;
    border-radius: 3px;
    margin: 12px auto 8px;
    cursor: grab;
}

.bottom-sheet-handle:active {
    cursor: grabbing;
    background: #adb5bd;
}

/* Header */
.bottom-sheet-header {
    padding: 8px 20px 16px;
    border-bottom: 1px solid #e9ecef;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-shrink: 0;
}

.bottom-sheet-title {
    font-size: 1.125rem;
    font-weight: 600;
    color: #212529;
    margin: 0;
}

.bottom-sheet-close {
    background: none;
    border: none;
    font-size: 1.5rem;
    color: #6c757d;
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 8px;
    transition: background 0.2s;
}

.bottom-sheet-close:hover {
    background: #f8f9fa;
    color: #212529;
}

/* Content */
.bottom-sheet-content {
    padding: 20px;
    overflow-y: auto;
    flex: 1;
    -webkit-overflow-scrolling: touch;
}

/* Animations */
@keyframes slideUp {
    from {
        transform: translateY(100%);
    }
    to {
        transform: translateY(0);
    }
}

@keyframes fadeIn {
    from {
        opacity: 0;
    }
    to {
        opacity: 1;
    }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
    .bottom-sheet {
        background: #1a1a1a;
        box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.4);
    }

    .bottom-sheet-handle {
        background: #495057;
    }

    .bottom-sheet-header {
        border-bottom-color: #2d2d2d;
    }

    .bottom-sheet-title {
        color: #f8f9fa;
    }

    .bottom-sheet-close:hover {
        background: #2d2d2d;
    }
}

/* Safe area padding for iOS */
@supports (padding-bottom: env(safe-area-inset-bottom)) {
    .bottom-sheet-content {
        padding-bottom: calc(20px + env(safe-area-inset-bottom));
    }
}
</style>
"""


def render_bottom_sheet(
    config: BottomSheet,
    content_renderer: Callable[[], None],
) -> bool:
    """Render a bottom sheet modal.

    Args:
        config: Bottom sheet configuration.
        content_renderer: Function that renders the sheet's content.

    Returns:
        True if the sheet is currently open, False otherwise.

    Example:
        ```python
        sheet = BottomSheet(key="add_card", title="Add Card")

        if st.button("Open Sheet"):
            st.session_state.add_card_sheet_open = True

        if st.session_state.get("add_card_sheet_open", False):
            def render_content():
                st.text_input("Card Name")
                if st.button("Save"):
                    st.session_state.add_card_sheet_open = False

            render_bottom_sheet(sheet, render_content)
        ```
    """
    open_key = f"{config.key}_sheet_open"
    is_open = st.session_state.get(open_key, False)

    if not is_open:
        return False

    # Inject CSS
    st.markdown(BOTTOM_SHEET_CSS, unsafe_allow_html=True)

    # Determine height class
    if isinstance(config.height, int):
        height_style = f"height: {config.height}px;"
        height_class = ""
    else:
        height_style = ""
        height_class = f"height-{config.height}"

    # Build the sheet HTML structure
    sheet_html = f"""
    <div class="bottom-sheet-overlay" id="{config.key}-overlay"></div>
    <div class="bottom-sheet {height_class}" style="{height_style}" id="{config.key}-sheet">
    """

    # Add drag handle if enabled
    if config.show_handle:
        sheet_html += '<div class="bottom-sheet-handle"></div>'

    # Add header if title is provided
    if config.title:
        sheet_html += f"""
        <div class="bottom-sheet-header">
            <h3 class="bottom-sheet-title">{config.title}</h3>
        </div>
        """

    sheet_html += '<div class="bottom-sheet-content">'

    # Start the sheet container
    st.markdown(sheet_html, unsafe_allow_html=True)

    # Render the content using Streamlit widgets
    with st.container():
        content_renderer()

    # Close button (separate for click handling)
    col1, col2, col3 = st.columns([5, 1, 1])
    with col3:
        if st.button("✕ Close", key=f"{config.key}_close_btn", type="secondary"):
            st.session_state[open_key] = False
            if config.on_dismiss:
                config.on_dismiss()
            st.rerun()

    # Close the sheet HTML
    st.markdown('</div></div>', unsafe_allow_html=True)

    return True


def open_bottom_sheet(key: str) -> None:
    """Open a bottom sheet by key.

    Args:
        key: The unique key of the bottom sheet to open.
    """
    st.session_state[f"{key}_sheet_open"] = True


def close_bottom_sheet(key: str) -> None:
    """Close a bottom sheet by key.

    Args:
        key: The unique key of the bottom sheet to close.
    """
    st.session_state[f"{key}_sheet_open"] = False


def is_bottom_sheet_open(key: str) -> bool:
    """Check if a bottom sheet is currently open.

    Args:
        key: The unique key of the bottom sheet to check.

    Returns:
        True if the sheet is open, False otherwise.
    """
    return st.session_state.get(f"{key}_sheet_open", False)
