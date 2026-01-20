"""Sticky Action Bar component.

A fixed bar at the bottom of the screen for primary actions,
providing easy thumb access on mobile devices.
"""

import streamlit as st
from dataclasses import dataclass
from typing import Optional, List, Callable, Literal


@dataclass
class ActionButton:
    """Configuration for an action button in the sticky bar.

    Attributes:
        label: Button text label.
        icon: Optional emoji or icon character.
        on_click: Callback when button is clicked.
        primary: Whether this is the primary action.
        disabled: Whether the button is disabled.
        key: Unique key for the button.
    """
    label: str
    icon: Optional[str] = None
    on_click: Optional[Callable] = None
    primary: bool = False
    disabled: bool = False
    key: Optional[str] = None


@dataclass
class StickyActionBar:
    """Configuration for a sticky action bar.

    Attributes:
        key: Unique identifier for this action bar.
        buttons: List of action buttons to display.
        position: Where to position the bar - 'bottom' or 'top'.
        show_divider: Whether to show a divider line.
        blur_background: Whether to apply blur effect to background.
    """
    key: str
    buttons: List[ActionButton]
    position: Literal["bottom", "top"] = "bottom"
    show_divider: bool = True
    blur_background: bool = True


# CSS for sticky action bar styling
STICKY_ACTION_BAR_CSS = """
<style>
/* Sticky Action Bar Container */
.sticky-action-bar {
    position: fixed;
    left: 0;
    right: 0;
    z-index: 1000;
    padding: 12px 16px;
    display: flex;
    gap: 12px;
    justify-content: center;
    align-items: center;
}

.sticky-action-bar.position-bottom {
    bottom: 0;
    border-top: 1px solid #e9ecef;
    background: rgba(255, 255, 255, 0.95);
}

.sticky-action-bar.position-top {
    top: 0;
    border-bottom: 1px solid #e9ecef;
    background: rgba(255, 255, 255, 0.95);
}

.sticky-action-bar.blur-bg {
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
}

.sticky-action-bar.no-divider {
    border: none;
}

/* Action Button Base */
.action-btn {
    flex: 1;
    max-width: 200px;
    padding: 12px 20px;
    border-radius: 12px;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    border: none;
    outline: none;
}

/* Primary Action Button */
.action-btn.primary {
    background: linear-gradient(135deg, #0066cc 0%, #0052a3 100%);
    color: white;
    box-shadow: 0 4px 12px rgba(0, 102, 204, 0.3);
}

.action-btn.primary:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0, 102, 204, 0.4);
}

.action-btn.primary:active:not(:disabled) {
    transform: translateY(0);
    box-shadow: 0 2px 8px rgba(0, 102, 204, 0.3);
}

/* Secondary Action Button */
.action-btn.secondary {
    background: #f8f9fa;
    color: #495057;
    border: 1px solid #dee2e6;
}

.action-btn.secondary:hover:not(:disabled) {
    background: #e9ecef;
    border-color: #ced4da;
}

.action-btn.secondary:active:not(:disabled) {
    background: #dee2e6;
}

/* Disabled State */
.action-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

/* Icon */
.action-btn-icon {
    font-size: 1.1rem;
}

/* Safe area padding for iOS */
@supports (padding-bottom: env(safe-area-inset-bottom)) {
    .sticky-action-bar.position-bottom {
        padding-bottom: calc(12px + env(safe-area-inset-bottom));
    }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
    .sticky-action-bar.position-bottom,
    .sticky-action-bar.position-top {
        background: rgba(26, 26, 26, 0.95);
        border-color: #2d2d2d;
    }

    .action-btn.secondary {
        background: #2d2d2d;
        color: #f8f9fa;
        border-color: #404040;
    }

    .action-btn.secondary:hover:not(:disabled) {
        background: #404040;
    }
}

/* Add padding to main content to prevent overlap */
.sticky-bar-content-spacer {
    height: 80px;
}
</style>
"""


def render_sticky_action_bar(config: StickyActionBar) -> Optional[str]:
    """Render a sticky action bar.

    Args:
        config: Sticky action bar configuration.

    Returns:
        The key of the clicked button, or None if no button was clicked.

    Example:
        ```python
        buttons = [
            ActionButton(label="Cancel", key="cancel"),
            ActionButton(label="Save", icon="💾", primary=True, key="save"),
        ]
        bar = StickyActionBar(key="edit_bar", buttons=buttons)

        clicked = render_sticky_action_bar(bar)
        if clicked == "save":
            save_changes()
        elif clicked == "cancel":
            cancel_editing()
        ```
    """
    # Inject CSS
    st.markdown(STICKY_ACTION_BAR_CSS, unsafe_allow_html=True)

    # Build CSS classes
    classes = ["sticky-action-bar", f"position-{config.position}"]
    if config.blur_background:
        classes.append("blur-bg")
    if not config.show_divider:
        classes.append("no-divider")

    # Track which button was clicked
    clicked_button = None

    # Create the action bar container
    # We use Streamlit columns inside a container for the buttons
    with st.container():
        # Add spacer to prevent content overlap
        st.markdown('<div class="sticky-bar-content-spacer"></div>', unsafe_allow_html=True)

        # Create button columns
        cols = st.columns(len(config.buttons))

        for i, button in enumerate(config.buttons):
            with cols[i]:
                button_key = button.key or f"{config.key}_btn_{i}"
                button_type = "primary" if button.primary else "secondary"

                # Construct label with icon
                label = f"{button.icon} {button.label}" if button.icon else button.label

                if st.button(
                    label,
                    key=button_key,
                    type=button_type,
                    disabled=button.disabled,
                    use_container_width=True,
                ):
                    clicked_button = button.key or button.label
                    if button.on_click:
                        button.on_click()

    return clicked_button


def create_action_bar_simple(
    key: str,
    primary_label: str,
    primary_callback: Optional[Callable] = None,
    secondary_label: Optional[str] = None,
    secondary_callback: Optional[Callable] = None,
    primary_icon: Optional[str] = None,
    secondary_icon: Optional[str] = None,
) -> StickyActionBar:
    """Create a simple action bar with up to two buttons.

    Args:
        key: Unique identifier for this action bar.
        primary_label: Label for the primary button.
        primary_callback: Callback for primary button click.
        secondary_label: Optional label for secondary button.
        secondary_callback: Optional callback for secondary button.
        primary_icon: Optional icon for primary button.
        secondary_icon: Optional icon for secondary button.

    Returns:
        Configured StickyActionBar instance.

    Example:
        ```python
        bar = create_action_bar_simple(
            key="save_bar",
            primary_label="Save Changes",
            primary_icon="💾",
            secondary_label="Cancel",
        )
        render_sticky_action_bar(bar)
        ```
    """
    buttons = []

    if secondary_label:
        buttons.append(ActionButton(
            label=secondary_label,
            icon=secondary_icon,
            on_click=secondary_callback,
            primary=False,
            key=f"{key}_secondary",
        ))

    buttons.append(ActionButton(
        label=primary_label,
        icon=primary_icon,
        on_click=primary_callback,
        primary=True,
        key=f"{key}_primary",
    ))

    return StickyActionBar(key=key, buttons=buttons)
