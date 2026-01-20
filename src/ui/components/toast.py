"""Toast/Snackbar notification system.

Provides non-intrusive notifications that appear briefly and auto-dismiss,
commonly used for success messages, errors, and status updates.
"""

import streamlit as st
from dataclasses import dataclass
from typing import Optional, Callable, Literal, List
from datetime import datetime, timedelta
import time


@dataclass
class Toast:
    """Configuration for a toast notification.

    Attributes:
        key: Unique identifier for this toast.
        message: Toast message text.
        variant: Toast type/style.
        duration_ms: Auto-dismiss duration in milliseconds.
        icon: Optional icon/emoji.
        action_label: Optional action button label.
        action_callback: Optional action button callback.
        dismissible: Whether the toast can be manually dismissed.
    """
    key: str
    message: str
    variant: Literal["success", "error", "warning", "info", "neutral"] = "info"
    duration_ms: int = 4000
    icon: Optional[str] = None
    action_label: Optional[str] = None
    action_callback: Optional[Callable] = None
    dismissible: bool = True


# CSS for toast styling
TOAST_CSS = """
<style>
/* Toast Container (fixed position) */
.toast-container {
    position: fixed;
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 10000;
    display: flex;
    flex-direction: column;
    gap: 12px;
    pointer-events: none;
    max-width: 90vw;
    width: 400px;
}

/* Individual Toast */
.toast {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 20px;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    animation: toast-in 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    pointer-events: auto;
    min-width: 280px;
}

.toast.dismissing {
    animation: toast-out 0.2s ease-in forwards;
}

@keyframes toast-in {
    from {
        transform: translateY(100px);
        opacity: 0;
    }
    to {
        transform: translateY(0);
        opacity: 1;
    }
}

@keyframes toast-out {
    from {
        transform: translateY(0);
        opacity: 1;
    }
    to {
        transform: translateY(20px);
        opacity: 0;
    }
}

/* Toast Variants */
.toast.success {
    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
    color: white;
}

.toast.error {
    background: linear-gradient(135deg, #dc3545 0%, #e85363 100%);
    color: white;
}

.toast.warning {
    background: linear-gradient(135deg, #ffc107 0%, #ffca28 100%);
    color: #212529;
}

.toast.info {
    background: linear-gradient(135deg, #0066cc 0%, #0088ff 100%);
    color: white;
}

.toast.neutral {
    background: #212529;
    color: white;
}

/* Toast Icon */
.toast-icon {
    font-size: 1.25rem;
    flex-shrink: 0;
}

/* Toast Message */
.toast-message {
    flex: 1;
    font-size: 0.9375rem;
    font-weight: 500;
    line-height: 1.4;
}

/* Toast Action */
.toast-action {
    background: rgba(255, 255, 255, 0.2);
    border: none;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 0.8125rem;
    font-weight: 600;
    color: inherit;
    cursor: pointer;
    transition: background 0.2s ease;
    flex-shrink: 0;
}

.toast-action:hover {
    background: rgba(255, 255, 255, 0.3);
}

.toast.warning .toast-action {
    background: rgba(0, 0, 0, 0.1);
}

.toast.warning .toast-action:hover {
    background: rgba(0, 0, 0, 0.2);
}

/* Toast Dismiss Button */
.toast-dismiss {
    background: none;
    border: none;
    color: inherit;
    opacity: 0.7;
    cursor: pointer;
    padding: 4px;
    font-size: 1rem;
    line-height: 1;
    transition: opacity 0.2s ease;
    flex-shrink: 0;
}

.toast-dismiss:hover {
    opacity: 1;
}

/* Progress Bar (for duration) */
.toast-progress {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: rgba(255, 255, 255, 0.3);
    border-radius: 0 0 12px 12px;
    overflow: hidden;
}

.toast-progress-bar {
    height: 100%;
    background: rgba(255, 255, 255, 0.6);
    animation: progress-shrink linear forwards;
}

@keyframes progress-shrink {
    from {
        width: 100%;
    }
    to {
        width: 0%;
    }
}

/* Stacked Toasts */
.toast-stack-count {
    position: absolute;
    top: -8px;
    right: -8px;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: #dc3545;
    color: white;
    font-size: 0.75rem;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

/* Mobile adjustments */
@media (max-width: 480px) {
    .toast-container {
        bottom: 16px;
        left: 16px;
        right: 16px;
        transform: none;
        width: auto;
    }

    .toast {
        min-width: auto;
    }
}

/* Safe area for iOS */
@supports (padding-bottom: env(safe-area-inset-bottom)) {
    .toast-container {
        bottom: calc(24px + env(safe-area-inset-bottom));
    }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
    .toast.neutral {
        background: #2d2d2d;
        border: 1px solid #404040;
    }
}
</style>
"""

# Default icons for toast variants
DEFAULT_ICONS = {
    "success": "✓",
    "error": "✕",
    "warning": "⚠",
    "info": "ℹ",
    "neutral": "•",
}


def inject_toast_css():
    """Inject the toast CSS styles."""
    st.markdown(TOAST_CSS, unsafe_allow_html=True)


def render_toast(
    config: Optional[Toast] = None,
    message: str = "",
    variant: Literal["success", "error", "warning", "info", "neutral"] = "info",
    icon: Optional[str] = None,
    duration_ms: int = 4000,
    key: str = "toast",
) -> None:
    """Render a toast notification.

    Note: For best results, use Streamlit's built-in st.toast() for actual
    toast notifications. This component provides additional styling options.

    Args:
        config: Optional Toast configuration.
        message: Toast message (if config not provided).
        variant: Toast variant (if config not provided).
        icon: Icon/emoji (if config not provided).
        duration_ms: Duration in ms (if config not provided).
        key: Unique key (if config not provided).

    Example:
        ```python
        # Show a success toast
        st.toast("Card saved successfully!", icon="✓")

        # Or use custom styled toast
        render_toast(
            message="Card saved!",
            variant="success",
            icon="💳",
        )
        ```
    """
    inject_toast_css()

    # Use config or individual params
    if config:
        key = config.key
        message = config.message
        variant = config.variant
        icon = config.icon
        duration_ms = config.duration_ms

    # Use default icon if not provided
    if icon is None:
        icon = DEFAULT_ICONS.get(variant, "•")

    # Build toast HTML
    html = f"""
    <div class="toast-container">
        <div class="toast {variant}" style="position: relative;">
            <span class="toast-icon">{icon}</span>
            <span class="toast-message">{message}</span>
            <div class="toast-progress">
                <div class="toast-progress-bar" style="animation-duration: {duration_ms}ms;"></div>
            </div>
        </div>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


def show_toast_success(message: str, icon: str = "✓") -> None:
    """Show a success toast using Streamlit's native toast.

    Args:
        message: Success message.
        icon: Icon to display.

    Example:
        ```python
        show_toast_success("Card added successfully!")
        ```
    """
    st.toast(message, icon=icon)


def show_toast_error(message: str, icon: str = "❌") -> None:
    """Show an error toast using Streamlit's native toast.

    Args:
        message: Error message.
        icon: Icon to display.

    Example:
        ```python
        show_toast_error("Failed to save card")
        ```
    """
    st.toast(message, icon=icon)


def show_toast_warning(message: str, icon: str = "⚠️") -> None:
    """Show a warning toast using Streamlit's native toast.

    Args:
        message: Warning message.
        icon: Icon to display.

    Example:
        ```python
        show_toast_warning("Deadline approaching!")
        ```
    """
    st.toast(message, icon=icon)


def show_toast_info(message: str, icon: str = "ℹ️") -> None:
    """Show an info toast using Streamlit's native toast.

    Args:
        message: Info message.
        icon: Icon to display.

    Example:
        ```python
        show_toast_info("Tip: You can swipe cards to delete them")
        ```
    """
    st.toast(message, icon=icon)


def render_snackbar(
    message: str,
    action_label: Optional[str] = None,
    action_key: str = "snackbar_action",
    variant: Literal["success", "error", "warning", "info", "neutral"] = "neutral",
    dismissible: bool = True,
    dismiss_key: str = "snackbar_dismiss",
) -> Optional[str]:
    """Render a snackbar notification with optional action button.

    Unlike toast, snackbar stays visible until dismissed or action is taken.
    This uses Streamlit widgets for interactivity.

    Args:
        message: Snackbar message.
        action_label: Optional action button label.
        action_key: Key for action button.
        variant: Snackbar style variant.
        dismissible: Whether can be dismissed.
        dismiss_key: Key for dismiss button.

    Returns:
        "action" if action clicked, "dismiss" if dismissed, else None.

    Example:
        ```python
        result = render_snackbar(
            message="Card deleted",
            action_label="Undo",
            variant="neutral",
        )
        if result == "action":
            undo_delete()
        ```
    """
    inject_toast_css()

    snackbar_key = f"snackbar_{action_key}_visible"
    if snackbar_key not in st.session_state:
        st.session_state[snackbar_key] = True

    if not st.session_state[snackbar_key]:
        return None

    clicked = None

    # Build snackbar using Streamlit components
    icon = DEFAULT_ICONS.get(variant, "•")

    with st.container():
        cols = st.columns([0.5, 4, 1.5, 0.5] if action_label else [0.5, 5.5, 0.5])

        with cols[0]:
            st.markdown(f"<span style='font-size: 1.25rem;'>{icon}</span>", unsafe_allow_html=True)

        with cols[1]:
            st.markdown(f"<span style='font-weight: 500;'>{message}</span>", unsafe_allow_html=True)

        if action_label:
            with cols[2]:
                if st.button(action_label, key=action_key, type="secondary"):
                    clicked = "action"
                    st.session_state[snackbar_key] = False

        if dismissible:
            with cols[-1]:
                if st.button("✕", key=dismiss_key, type="secondary"):
                    clicked = "dismiss"
                    st.session_state[snackbar_key] = False

    return clicked


def render_notification_badge(
    count: int,
    max_display: int = 99,
    variant: Literal["error", "warning", "info"] = "error",
) -> None:
    """Render a notification badge with count.

    Args:
        count: Number to display.
        max_display: Maximum number to show (displays "99+" if exceeded).
        variant: Badge color variant.

    Example:
        ```python
        # Show badge next to title
        col1, col2 = st.columns([4, 1])
        with col1:
            st.subheader("Notifications")
        with col2:
            render_notification_badge(count=5)
        ```
    """
    if count <= 0:
        return

    colors = {
        "error": "#dc3545",
        "warning": "#ffc107",
        "info": "#0066cc",
    }
    color = colors.get(variant, "#dc3545")

    display_count = f"{max_display}+" if count > max_display else str(count)

    st.markdown(
        f"""
        <span style="
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 20px;
            height: 20px;
            padding: 0 6px;
            border-radius: 10px;
            background: {color};
            color: white;
            font-size: 0.75rem;
            font-weight: 700;
        ">{display_count}</span>
        """,
        unsafe_allow_html=True,
    )


def render_status_indicator(
    status: Literal["online", "offline", "busy", "away"],
    label: Optional[str] = None,
    size: Literal["sm", "md", "lg"] = "md",
) -> None:
    """Render a status indicator dot.

    Args:
        status: Current status.
        label: Optional label text.
        size: Size preset.

    Example:
        ```python
        render_status_indicator(status="online", label="Synced")
        ```
    """
    colors = {
        "online": "#28a745",
        "offline": "#6c757d",
        "busy": "#dc3545",
        "away": "#ffc107",
    }
    color = colors.get(status, "#6c757d")

    sizes = {
        "sm": "8px",
        "md": "10px",
        "lg": "12px",
    }
    dot_size = sizes.get(size, "10px")

    label_html = f'<span style="margin-left: 8px; font-size: 0.875rem; color: #6c757d;">{label}</span>' if label else ""

    st.markdown(
        f"""
        <span style="display: inline-flex; align-items: center;">
            <span style="
                width: {dot_size};
                height: {dot_size};
                border-radius: 50%;
                background: {color};
                display: inline-block;
                box-shadow: 0 0 0 2px white, 0 0 0 3px {color}40;
            "></span>
            {label_html}
        </span>
        """,
        unsafe_allow_html=True,
    )
