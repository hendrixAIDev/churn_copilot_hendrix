"""Touch Feedback component.

Provides haptic-style visual feedback for touch interactions,
making the app feel more responsive and native-like on mobile.
"""

import streamlit as st
from dataclasses import dataclass
from typing import Optional, Callable, Literal


@dataclass
class TouchFeedback:
    """Configuration for touch feedback styling.

    Attributes:
        feedback_type: Type of visual feedback effect.
        duration_ms: Duration of the feedback animation in milliseconds.
        color: Optional custom color for the feedback effect.
        scale: Scale factor for press effect (0.95 = 95% of original size).
    """
    feedback_type: Literal["ripple", "scale", "highlight", "bounce"] = "scale"
    duration_ms: int = 150
    color: Optional[str] = None
    scale: float = 0.97


# CSS for touch feedback styling
TOUCH_FEEDBACK_CSS = """
<style>
/* Touch Feedback Base */
.touch-feedback {
    position: relative;
    overflow: hidden;
    -webkit-tap-highlight-color: transparent;
    user-select: none;
    cursor: pointer;
}

/* Scale Feedback */
.touch-feedback.scale-effect {
    transition: transform 0.15s cubic-bezier(0.4, 0, 0.2, 1);
}

.touch-feedback.scale-effect:active {
    transform: scale(0.97);
}

/* Bounce Feedback */
.touch-feedback.bounce-effect {
    transition: transform 0.2s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.touch-feedback.bounce-effect:active {
    transform: scale(0.95);
}

/* Highlight Feedback */
.touch-feedback.highlight-effect {
    transition: background-color 0.15s ease;
}

.touch-feedback.highlight-effect:active {
    background-color: rgba(0, 0, 0, 0.08);
}

/* Ripple Feedback */
.touch-feedback.ripple-effect {
    position: relative;
    overflow: hidden;
}

.touch-feedback.ripple-effect::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 0;
    height: 0;
    background: rgba(0, 0, 0, 0.1);
    border-radius: 50%;
    transform: translate(-50%, -50%);
    transition: width 0.3s ease, height 0.3s ease, opacity 0.3s ease;
    opacity: 0;
}

.touch-feedback.ripple-effect:active::after {
    width: 200%;
    height: 200%;
    opacity: 1;
}

/* Touch-optimized Button */
.touch-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 12px 24px;
    border-radius: 12px;
    font-size: 1rem;
    font-weight: 600;
    border: none;
    cursor: pointer;
    position: relative;
    overflow: hidden;
    -webkit-tap-highlight-color: transparent;
    user-select: none;
    min-height: 48px; /* Touch target size */
    min-width: 48px;
    transition: all 0.15s ease;
}

/* Primary Touch Button */
.touch-btn.primary {
    background: linear-gradient(135deg, #0066cc 0%, #0052a3 100%);
    color: white;
    box-shadow: 0 4px 12px rgba(0, 102, 204, 0.25);
}

.touch-btn.primary:hover {
    box-shadow: 0 6px 16px rgba(0, 102, 204, 0.35);
    transform: translateY(-1px);
}

.touch-btn.primary:active {
    transform: scale(0.97) translateY(0);
    box-shadow: 0 2px 8px rgba(0, 102, 204, 0.2);
}

/* Secondary Touch Button */
.touch-btn.secondary {
    background: #f8f9fa;
    color: #495057;
    border: 1px solid #dee2e6;
}

.touch-btn.secondary:hover {
    background: #e9ecef;
}

.touch-btn.secondary:active {
    transform: scale(0.97);
    background: #dee2e6;
}

/* Danger Touch Button */
.touch-btn.danger {
    background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
    color: white;
    box-shadow: 0 4px 12px rgba(220, 53, 69, 0.25);
}

.touch-btn.danger:hover {
    box-shadow: 0 6px 16px rgba(220, 53, 69, 0.35);
}

.touch-btn.danger:active {
    transform: scale(0.97);
}

/* Success Touch Button */
.touch-btn.success {
    background: linear-gradient(135deg, #28a745 0%, #1e7e34 100%);
    color: white;
    box-shadow: 0 4px 12px rgba(40, 167, 69, 0.25);
}

.touch-btn.success:hover {
    box-shadow: 0 6px 16px rgba(40, 167, 69, 0.35);
}

.touch-btn.success:active {
    transform: scale(0.97);
}

/* Ghost Touch Button */
.touch-btn.ghost {
    background: transparent;
    color: #0066cc;
}

.touch-btn.ghost:hover {
    background: rgba(0, 102, 204, 0.08);
}

.touch-btn.ghost:active {
    background: rgba(0, 102, 204, 0.15);
    transform: scale(0.97);
}

/* Icon Button */
.touch-btn.icon-only {
    padding: 12px;
    border-radius: 50%;
}

/* Full Width */
.touch-btn.full-width {
    width: 100%;
}

/* Disabled State */
.touch-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none !important;
}

/* Touch List Item */
.touch-list-item {
    display: flex;
    align-items: center;
    padding: 16px;
    background: white;
    border-bottom: 1px solid #e9ecef;
    transition: background-color 0.15s ease;
    cursor: pointer;
    -webkit-tap-highlight-color: transparent;
}

.touch-list-item:active {
    background-color: #f8f9fa;
}

.touch-list-item:last-child {
    border-bottom: none;
}

/* Touch Card */
.touch-card {
    background: white;
    border-radius: 16px;
    padding: 16px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    transition: all 0.2s ease;
    cursor: pointer;
    -webkit-tap-highlight-color: transparent;
}

.touch-card:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.touch-card:active {
    transform: scale(0.98);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
    .touch-btn.secondary {
        background: #2d2d2d;
        color: #f8f9fa;
        border-color: #404040;
    }

    .touch-btn.secondary:hover {
        background: #3d3d3d;
    }

    .touch-btn.ghost {
        color: #4da6ff;
    }

    .touch-btn.ghost:hover {
        background: rgba(77, 166, 255, 0.1);
    }

    .touch-list-item {
        background: #1a1a1a;
        border-color: #2d2d2d;
    }

    .touch-list-item:active {
        background-color: #2d2d2d;
    }

    .touch-card {
        background: #1a1a1a;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }
}
</style>
"""


def inject_touch_feedback_css():
    """Inject the touch feedback CSS styles."""
    st.markdown(TOUCH_FEEDBACK_CSS, unsafe_allow_html=True)


def render_touch_feedback_button(
    label: str,
    key: str,
    variant: Literal["primary", "secondary", "danger", "success", "ghost"] = "primary",
    icon: Optional[str] = None,
    full_width: bool = False,
    disabled: bool = False,
    on_click: Optional[Callable] = None,
) -> bool:
    """Render a button with touch feedback styling.

    Args:
        label: Button text label.
        key: Unique key for the button.
        variant: Button style variant.
        icon: Optional emoji or icon.
        full_width: Whether button should fill container width.
        disabled: Whether the button is disabled.
        on_click: Optional callback function.

    Returns:
        True if the button was clicked, False otherwise.

    Example:
        ```python
        if render_touch_feedback_button(
            label="Save",
            key="save_btn",
            variant="success",
            icon="💾",
        ):
            save_data()
        ```
    """
    # Inject CSS
    inject_touch_feedback_css()

    # Construct display label
    display_label = f"{icon} {label}" if icon else label

    # Map variant to Streamlit button type
    button_type = "primary" if variant in ["primary", "success", "danger"] else "secondary"

    clicked = st.button(
        display_label,
        key=key,
        type=button_type,
        disabled=disabled,
        use_container_width=full_width,
    )

    if clicked and on_click:
        on_click()

    return clicked


def render_touch_list_item(
    title: str,
    key: str,
    subtitle: Optional[str] = None,
    left_icon: Optional[str] = None,
    right_icon: Optional[str] = "›",
    on_click: Optional[Callable] = None,
) -> bool:
    """Render a touchable list item.

    Args:
        title: Main text for the item.
        key: Unique key for the item.
        subtitle: Optional secondary text.
        left_icon: Optional icon on the left.
        right_icon: Optional icon on the right (default: chevron).
        on_click: Optional callback function.

    Returns:
        True if the item was clicked, False otherwise.

    Example:
        ```python
        if render_touch_list_item(
            title="Account Settings",
            key="settings_item",
            subtitle="Manage your account",
            left_icon="⚙️",
        ):
            navigate_to_settings()
        ```
    """
    inject_touch_feedback_css()

    # Build the item HTML
    html = '<div class="touch-list-item touch-feedback scale-effect">'

    if left_icon:
        html += f'<span style="font-size: 1.5rem; margin-right: 16px;">{left_icon}</span>'

    html += '<div style="flex: 1;">'
    html += f'<div style="font-weight: 500; color: #212529;">{title}</div>'
    if subtitle:
        html += f'<div style="font-size: 0.875rem; color: #6c757d; margin-top: 2px;">{subtitle}</div>'
    html += '</div>'

    if right_icon:
        html += f'<span style="color: #adb5bd; font-size: 1.25rem;">{right_icon}</span>'

    html += '</div>'

    st.markdown(html, unsafe_allow_html=True)

    # Use a hidden button for click handling
    clicked = st.button("", key=key, label_visibility="collapsed")

    if clicked and on_click:
        on_click()

    return clicked
