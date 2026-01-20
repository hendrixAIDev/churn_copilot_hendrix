"""Pull to Refresh component.

Provides a pull-down-to-refresh gesture pattern commonly found in mobile apps.
Note: This is primarily CSS/visual - actual refresh logic must be handled separately.
"""

import streamlit as st
from dataclasses import dataclass
from typing import Optional, Callable


@dataclass
class PullToRefresh:
    """Configuration for pull to refresh behavior.

    Attributes:
        key: Unique identifier for this component.
        threshold: Pixels to pull before triggering refresh.
        on_refresh: Callback when refresh is triggered.
        loading_text: Text shown during refresh.
        pull_text: Text shown while pulling.
        release_text: Text shown when threshold reached.
    """
    key: str
    threshold: int = 80
    on_refresh: Optional[Callable] = None
    loading_text: str = "Refreshing..."
    pull_text: str = "Pull to refresh"
    release_text: str = "Release to refresh"


# CSS for pull to refresh styling
PULL_TO_REFRESH_CSS = """
<style>
/* Pull to Refresh Container */
.ptr-container {
    position: relative;
    overflow-y: auto;
    overflow-x: hidden;
    -webkit-overflow-scrolling: touch;
}

/* Refresh Indicator */
.ptr-indicator {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 16px;
    transform: translateY(-100%);
    transition: transform 0.2s ease;
    background: linear-gradient(180deg, #f8f9fa 0%, transparent 100%);
    z-index: 10;
}

.ptr-indicator.visible {
    transform: translateY(0);
}

.ptr-indicator.refreshing {
    transform: translateY(0);
}

/* Spinner */
.ptr-spinner {
    width: 24px;
    height: 24px;
    border: 3px solid #e9ecef;
    border-top-color: #0066cc;
    border-radius: 50%;
    animation: ptr-spin 0.8s linear infinite;
    margin-right: 12px;
}

@keyframes ptr-spin {
    to {
        transform: rotate(360deg);
    }
}

/* Pull Arrow */
.ptr-arrow {
    font-size: 1.25rem;
    transition: transform 0.2s ease;
    margin-right: 12px;
}

.ptr-arrow.up {
    transform: rotate(180deg);
}

/* Text */
.ptr-text {
    font-size: 0.875rem;
    color: #6c757d;
    font-weight: 500;
}

/* Success checkmark */
.ptr-success {
    width: 24px;
    height: 24px;
    color: #28a745;
    margin-right: 12px;
}

/* Pull Progress Bar */
.ptr-progress {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: #e9ecef;
    overflow: hidden;
}

.ptr-progress-bar {
    height: 100%;
    background: linear-gradient(90deg, #0066cc 0%, #00a3cc 100%);
    width: 0%;
    transition: width 0.1s ease;
}

.ptr-progress-bar.indeterminate {
    width: 30%;
    animation: ptr-indeterminate 1.5s ease-in-out infinite;
}

@keyframes ptr-indeterminate {
    0% {
        transform: translateX(-100%);
    }
    100% {
        transform: translateX(400%);
    }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
    .ptr-indicator {
        background: linear-gradient(180deg, #1a1a1a 0%, transparent 100%);
    }

    .ptr-spinner {
        border-color: #404040;
        border-top-color: #4da6ff;
    }

    .ptr-text {
        color: #adb5bd;
    }

    .ptr-progress {
        background: #2d2d2d;
    }
}
</style>
"""


def inject_pull_to_refresh_css():
    """Inject the pull to refresh CSS styles."""
    st.markdown(PULL_TO_REFRESH_CSS, unsafe_allow_html=True)


def render_pull_to_refresh_indicator(
    state: str = "idle",
    progress: int = 0,
) -> None:
    """Render a pull to refresh indicator.

    Args:
        state: Current state - 'idle', 'pulling', 'threshold', 'refreshing', 'success'.
        progress: Pull progress as percentage (0-100).

    Example:
        ```python
        # At the top of your scrollable content
        if st.session_state.get("is_refreshing", False):
            render_pull_to_refresh_indicator(state="refreshing")
        ```
    """
    inject_pull_to_refresh_css()

    if state == "idle":
        return

    if state == "refreshing":
        st.markdown(
            """
            <div class="ptr-indicator visible refreshing">
                <div class="ptr-spinner"></div>
                <span class="ptr-text">Refreshing...</span>
            </div>
            <div class="ptr-progress">
                <div class="ptr-progress-bar indeterminate"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif state == "success":
        st.markdown(
            """
            <div class="ptr-indicator visible">
                <span class="ptr-success">✓</span>
                <span class="ptr-text">Updated!</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif state == "threshold":
        st.markdown(
            """
            <div class="ptr-indicator visible">
                <span class="ptr-arrow up">↓</span>
                <span class="ptr-text">Release to refresh</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif state == "pulling":
        st.markdown(
            f"""
            <div class="ptr-indicator visible">
                <span class="ptr-arrow">↓</span>
                <span class="ptr-text">Pull to refresh</span>
            </div>
            <div class="ptr-progress">
                <div class="ptr-progress-bar" style="width: {progress}%;"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_refresh_button(
    key: str,
    label: str = "Refresh",
    icon: str = "🔄",
    on_click: Optional[Callable] = None,
) -> bool:
    """Render a manual refresh button as fallback for pull-to-refresh.

    On desktop or when pull gesture isn't available, users can click this button.

    Args:
        key: Unique key for the button.
        label: Button text label.
        icon: Button icon.
        on_click: Callback when clicked.

    Returns:
        True if button was clicked.

    Example:
        ```python
        if render_refresh_button(
            key="refresh_cards",
            label="Refresh",
            on_click=refresh_data,
        ):
            st.rerun()
        ```
    """
    inject_pull_to_refresh_css()

    # Check if currently refreshing
    is_refreshing = st.session_state.get(f"{key}_refreshing", False)

    if is_refreshing:
        col1, col2 = st.columns([1, 4])
        with col1:
            st.markdown(
                '<div class="ptr-spinner" style="display: inline-block;"></div>',
                unsafe_allow_html=True,
            )
        with col2:
            st.caption("Refreshing...")
        return False

    clicked = st.button(
        f"{icon} {label}",
        key=key,
        type="secondary",
    )

    if clicked:
        st.session_state[f"{key}_refreshing"] = True
        if on_click:
            on_click()
        st.session_state[f"{key}_refreshing"] = False

    return clicked
