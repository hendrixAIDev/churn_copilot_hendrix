"""Swipeable Card component.

Provides swipe gesture actions on cards, commonly used for delete/archive actions
in mobile apps.
"""

import streamlit as st
from dataclasses import dataclass
from typing import Optional, Callable, Literal, List


@dataclass
class SwipeAction:
    """Configuration for a swipe action.

    Attributes:
        label: Action text label.
        icon: Action icon/emoji.
        color: Background color for the action.
        on_trigger: Callback when action is triggered.
    """
    label: str
    icon: str
    color: str
    on_trigger: Optional[Callable] = None


@dataclass
class SwipeableCard:
    """Configuration for a swipeable card.

    Attributes:
        key: Unique identifier for the card.
        left_actions: Actions revealed when swiping right.
        right_actions: Actions revealed when swiping left.
        swipe_threshold: Percentage of card width to trigger action.
    """
    key: str
    left_actions: Optional[List[SwipeAction]] = None
    right_actions: Optional[List[SwipeAction]] = None
    swipe_threshold: float = 0.3


# CSS for swipeable card styling
SWIPEABLE_CARD_CSS = """
<style>
/* Swipeable Card Container */
.swipe-container {
    position: relative;
    overflow: hidden;
    border-radius: 12px;
    margin-bottom: 12px;
}

/* Actions Background */
.swipe-actions {
    position: absolute;
    top: 0;
    bottom: 0;
    display: flex;
    align-items: center;
    padding: 0 20px;
}

.swipe-actions.left {
    left: 0;
    background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
    justify-content: flex-start;
}

.swipe-actions.right {
    right: 0;
    background: linear-gradient(90deg, #dc3545 0%, #e85363 100%);
    justify-content: flex-end;
}

/* Action Item */
.swipe-action {
    display: flex;
    flex-direction: column;
    align-items: center;
    color: white;
    font-weight: 600;
    padding: 12px;
}

.swipe-action-icon {
    font-size: 1.5rem;
    margin-bottom: 4px;
}

.swipe-action-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Card Content */
.swipe-content {
    position: relative;
    z-index: 1;
    background: white;
    transition: transform 0.2s ease;
}

.swipe-content.swiping {
    transition: none;
}

/* Quick Action Buttons (fallback for non-touch) */
.quick-actions {
    display: flex;
    gap: 8px;
    padding: 8px 0;
    opacity: 0;
    transition: opacity 0.2s ease;
}

.swipe-container:hover .quick-actions {
    opacity: 1;
}

.quick-action-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
    border: none;
    transition: all 0.15s ease;
}

.quick-action-btn.edit {
    background: #e7f3ff;
    color: #0066cc;
}

.quick-action-btn.edit:hover {
    background: #cce5ff;
}

.quick-action-btn.delete {
    background: #f8d7da;
    color: #721c24;
}

.quick-action-btn.delete:hover {
    background: #f5c6cb;
}

.quick-action-btn.archive {
    background: #fff3cd;
    color: #856404;
}

.quick-action-btn.archive:hover {
    background: #ffeaa7;
}

.quick-action-btn.complete {
    background: #d4edda;
    color: #155724;
}

.quick-action-btn.complete:hover {
    background: #c3e6cb;
}

/* Swipe Hint Animation */
@keyframes swipe-hint {
    0%, 100% {
        transform: translateX(0);
    }
    50% {
        transform: translateX(-10px);
    }
}

.swipe-hint {
    animation: swipe-hint 1.5s ease-in-out 2;
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
    .swipe-content {
        background: #1a1a1a;
    }

    .quick-action-btn.edit {
        background: rgba(0, 102, 204, 0.2);
        color: #4da6ff;
    }

    .quick-action-btn.delete {
        background: rgba(220, 53, 69, 0.2);
        color: #ff6b6b;
    }

    .quick-action-btn.archive {
        background: rgba(255, 193, 7, 0.2);
        color: #ffc107;
    }

    .quick-action-btn.complete {
        background: rgba(40, 167, 69, 0.2);
        color: #51cf66;
    }
}
</style>
"""


def inject_swipeable_card_css():
    """Inject the swipeable card CSS styles."""
    st.markdown(SWIPEABLE_CARD_CSS, unsafe_allow_html=True)


def render_card_with_actions(
    key: str,
    content_renderer: Callable[[], None],
    on_edit: Optional[Callable] = None,
    on_delete: Optional[Callable] = None,
    on_archive: Optional[Callable] = None,
    on_complete: Optional[Callable] = None,
    show_hint: bool = False,
) -> Optional[str]:
    """Render a card with quick action buttons.

    Since Streamlit doesn't support native swipe gestures, this provides
    action buttons that appear on hover/tap.

    Args:
        key: Unique key for this card.
        content_renderer: Function that renders the card content.
        on_edit: Callback for edit action.
        on_delete: Callback for delete action.
        on_archive: Callback for archive action.
        on_complete: Callback for complete/done action.
        show_hint: Whether to animate a swipe hint.

    Returns:
        The action that was triggered, or None.

    Example:
        ```python
        def render_card_content():
            st.markdown("**Card Title**")
            st.caption("Card description")

        action = render_card_with_actions(
            key="card_1",
            content_renderer=render_card_content,
            on_edit=lambda: edit_card("1"),
            on_delete=lambda: delete_card("1"),
        )
        ```
    """
    inject_swipeable_card_css()

    triggered_action = None

    with st.container():
        # Render the main card content
        hint_class = "swipe-hint" if show_hint else ""
        st.markdown(f'<div class="swipe-container {hint_class}">', unsafe_allow_html=True)
        st.markdown('<div class="swipe-content">', unsafe_allow_html=True)

        content_renderer()

        st.markdown('</div>', unsafe_allow_html=True)

        # Quick action buttons
        actions = []
        if on_complete:
            actions.append(("complete", "✓", "Done", on_complete))
        if on_edit:
            actions.append(("edit", "✎", "Edit", on_edit))
        if on_archive:
            actions.append(("archive", "📦", "Archive", on_archive))
        if on_delete:
            actions.append(("delete", "🗑", "Delete", on_delete))

        if actions:
            cols = st.columns(len(actions) + 2)  # Extra cols for spacing

            for i, (action_type, icon, label, callback) in enumerate(actions):
                with cols[i]:
                    if st.button(
                        f"{icon} {label}",
                        key=f"{key}_{action_type}",
                        type="secondary" if action_type != "delete" else "primary",
                    ):
                        triggered_action = action_type
                        if callback:
                            callback()

        st.markdown('</div>', unsafe_allow_html=True)

    return triggered_action


def render_swipe_indicator(
    direction: Literal["left", "right"],
    action: SwipeAction,
    progress: float = 0,
) -> None:
    """Render a swipe action indicator.

    Args:
        direction: Direction being swiped.
        action: The action to display.
        progress: Swipe progress (0-1).

    Example:
        ```python
        # Show delete indicator when swiping left
        render_swipe_indicator(
            direction="left",
            action=SwipeAction(
                label="Delete",
                icon="🗑",
                color="#dc3545",
            ),
            progress=0.5,
        )
        ```
    """
    inject_swipeable_card_css()

    opacity = min(progress * 2, 1)
    scale = 0.8 + (progress * 0.2)

    st.markdown(
        f"""
        <div class="swipe-actions {direction}" style="opacity: {opacity};">
            <div class="swipe-action" style="transform: scale({scale});">
                <span class="swipe-action-icon">{action.icon}</span>
                <span class="swipe-action-label">{action.label}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def create_delete_action(on_delete: Callable) -> SwipeAction:
    """Create a standard delete swipe action."""
    return SwipeAction(
        label="Delete",
        icon="🗑",
        color="#dc3545",
        on_trigger=on_delete,
    )


def create_archive_action(on_archive: Callable) -> SwipeAction:
    """Create a standard archive swipe action."""
    return SwipeAction(
        label="Archive",
        icon="📦",
        color="#ffc107",
        on_trigger=on_archive,
    )


def create_complete_action(on_complete: Callable) -> SwipeAction:
    """Create a standard complete/done swipe action."""
    return SwipeAction(
        label="Done",
        icon="✓",
        color="#28a745",
        on_trigger=on_complete,
    )
