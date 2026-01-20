"""Empty State component.

Provides friendly empty state displays with illustrations and
call-to-action buttons when there's no content to show.
"""

import streamlit as st
from dataclasses import dataclass
from typing import Optional, Callable, Literal


@dataclass
class EmptyState:
    """Configuration for an empty state display.

    Attributes:
        key: Unique identifier for this empty state.
        title: Main heading text.
        description: Secondary descriptive text.
        illustration: Illustration type or custom emoji/icon.
        action_label: Optional CTA button label.
        action_callback: Optional CTA button callback.
        secondary_action_label: Optional secondary action label.
        secondary_action_callback: Optional secondary action callback.
    """
    key: str
    title: str
    description: Optional[str] = None
    illustration: Literal["cards", "search", "error", "success", "inbox", "chart"] | str = "cards"
    action_label: Optional[str] = None
    action_callback: Optional[Callable] = None
    secondary_action_label: Optional[str] = None
    secondary_action_callback: Optional[Callable] = None


# CSS for empty state styling
EMPTY_STATE_CSS = """
<style>
/* Empty State Container */
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 48px 24px;
    text-align: center;
    min-height: 300px;
}

.empty-state.compact {
    min-height: 200px;
    padding: 32px 16px;
}

/* Illustration */
.empty-illustration {
    font-size: 4rem;
    margin-bottom: 24px;
    line-height: 1;
    animation: float 3s ease-in-out infinite;
}

@keyframes float {
    0%, 100% {
        transform: translateY(0);
    }
    50% {
        transform: translateY(-10px);
    }
}

.empty-illustration.no-animation {
    animation: none;
}

/* SVG Illustration Container */
.empty-svg-illustration {
    width: 120px;
    height: 120px;
    margin-bottom: 24px;
}

/* Title */
.empty-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: #212529;
    margin: 0 0 8px;
}

/* Description */
.empty-description {
    font-size: 0.9375rem;
    color: #6c757d;
    max-width: 360px;
    margin: 0 0 24px;
    line-height: 1.5;
}

/* Actions Container */
.empty-actions {
    display: flex;
    flex-direction: column;
    gap: 12px;
    width: 100%;
    max-width: 280px;
}

.empty-actions.horizontal {
    flex-direction: row;
    justify-content: center;
    max-width: none;
}

/* Primary Action */
.empty-action-primary {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 12px 24px;
    background: linear-gradient(135deg, #0066cc 0%, #0052a3 100%);
    color: white;
    border: none;
    border-radius: 12px;
    font-size: 0.9375rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    width: 100%;
}

.empty-action-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 102, 204, 0.3);
}

/* Secondary Action */
.empty-action-secondary {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 10px 20px;
    background: transparent;
    color: #0066cc;
    border: none;
    border-radius: 8px;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.2s ease;
}

.empty-action-secondary:hover {
    background: rgba(0, 102, 204, 0.08);
}

/* Inline Empty State (for tables/lists) */
.empty-inline {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 24px;
    background: #f8f9fa;
    border-radius: 12px;
    border: 1px dashed #dee2e6;
}

.empty-inline-icon {
    font-size: 2rem;
    flex-shrink: 0;
}

.empty-inline-content {
    text-align: left;
}

.empty-inline-title {
    font-size: 1rem;
    font-weight: 600;
    color: #212529;
    margin-bottom: 4px;
}

.empty-inline-description {
    font-size: 0.875rem;
    color: #6c757d;
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
    .empty-title {
        color: #f8f9fa;
    }

    .empty-description {
        color: #adb5bd;
    }

    .empty-action-secondary {
        color: #4da6ff;
    }

    .empty-action-secondary:hover {
        background: rgba(77, 166, 255, 0.1);
    }

    .empty-inline {
        background: #1a1a1a;
        border-color: #2d2d2d;
    }

    .empty-inline-title {
        color: #f8f9fa;
    }

    .empty-inline-description {
        color: #adb5bd;
    }
}
</style>
"""

# Pre-defined illustrations using emoji
ILLUSTRATIONS = {
    "cards": "💳",
    "search": "🔍",
    "error": "⚠️",
    "success": "✓",
    "inbox": "📭",
    "chart": "📊",
    "document": "📄",
    "folder": "📁",
    "calendar": "📅",
    "notification": "🔔",
    "settings": "⚙️",
    "user": "👤",
    "lock": "🔒",
    "star": "⭐",
    "heart": "❤️",
    "plus": "➕",
}


def inject_empty_state_css():
    """Inject the empty state CSS styles."""
    st.markdown(EMPTY_STATE_CSS, unsafe_allow_html=True)


def render_empty_state(
    config: Optional[EmptyState] = None,
    title: str = "No items yet",
    description: Optional[str] = None,
    illustration: str = "cards",
    action_label: Optional[str] = None,
    action_callback: Optional[Callable] = None,
    secondary_action_label: Optional[str] = None,
    secondary_action_callback: Optional[Callable] = None,
    compact: bool = False,
    animate: bool = True,
    key: str = "empty_state",
) -> Optional[str]:
    """Render an empty state display.

    Args:
        config: Optional EmptyState configuration.
        title: Main heading text (if config not provided).
        description: Secondary text (if config not provided).
        illustration: Illustration type or emoji (if config not provided).
        action_label: CTA button label (if config not provided).
        action_callback: CTA button callback (if config not provided).
        secondary_action_label: Secondary action label (if config not provided).
        secondary_action_callback: Secondary action callback (if config not provided).
        compact: Whether to use compact styling.
        animate: Whether to animate the illustration.
        key: Unique key (if config not provided).

    Returns:
        The key of the action that was clicked, or None.

    Example:
        ```python
        render_empty_state(
            title="No cards yet",
            description="Add your first credit card to start tracking benefits",
            illustration="cards",
            action_label="Add Card",
            action_callback=lambda: st.session_state.update(page="add"),
        )
        ```
    """
    inject_empty_state_css()

    # Use config or individual params
    if config:
        key = config.key
        title = config.title
        description = config.description
        illustration = config.illustration
        action_label = config.action_label
        action_callback = config.action_callback
        secondary_action_label = config.secondary_action_label
        secondary_action_callback = config.secondary_action_callback

    # Get illustration emoji
    illust_emoji = ILLUSTRATIONS.get(illustration, illustration)

    # Build animation class
    anim_class = "" if animate else "no-animation"
    compact_class = "compact" if compact else ""

    clicked_action = None

    # Start container
    st.markdown(f'<div class="empty-state {compact_class}">', unsafe_allow_html=True)

    # Illustration
    st.markdown(
        f'<div class="empty-illustration {anim_class}">{illust_emoji}</div>',
        unsafe_allow_html=True,
    )

    # Title
    st.markdown(f'<h3 class="empty-title">{title}</h3>', unsafe_allow_html=True)

    # Description
    if description:
        st.markdown(f'<p class="empty-description">{description}</p>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Action buttons (using Streamlit buttons for interactivity)
    if action_label or secondary_action_label:
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            if action_label:
                if st.button(
                    action_label,
                    key=f"{key}_primary_action",
                    type="primary",
                    use_container_width=True,
                ):
                    clicked_action = "primary"
                    if action_callback:
                        action_callback()

            if secondary_action_label:
                if st.button(
                    secondary_action_label,
                    key=f"{key}_secondary_action",
                    type="secondary",
                    use_container_width=True,
                ):
                    clicked_action = "secondary"
                    if secondary_action_callback:
                        secondary_action_callback()

    return clicked_action


def render_inline_empty(
    title: str,
    description: Optional[str] = None,
    icon: str = "📭",
    action_label: Optional[str] = None,
    action_callback: Optional[Callable] = None,
    key: str = "inline_empty",
) -> Optional[str]:
    """Render an inline empty state for lists/tables.

    Args:
        title: Main text.
        description: Secondary text.
        icon: Emoji icon.
        action_label: Optional action button label.
        action_callback: Optional action callback.
        key: Unique key.

    Returns:
        The key of the action clicked, or None.

    Example:
        ```python
        render_inline_empty(
            title="No benefits tracked",
            description="Add benefits to this card to track usage",
            icon="💰",
            action_label="Add Benefit",
        )
        ```
    """
    inject_empty_state_css()

    clicked_action = None

    with st.container():
        st.markdown(
            f"""
            <div class="empty-inline">
                <span class="empty-inline-icon">{icon}</span>
                <div class="empty-inline-content">
                    <div class="empty-inline-title">{title}</div>
                    {f'<div class="empty-inline-description">{description}</div>' if description else ''}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if action_label:
            if st.button(action_label, key=f"{key}_action", type="secondary"):
                clicked_action = "action"
                if action_callback:
                    action_callback()

    return clicked_action


def render_error_state(
    title: str = "Something went wrong",
    description: Optional[str] = None,
    retry_label: str = "Try Again",
    retry_callback: Optional[Callable] = None,
    key: str = "error_state",
) -> bool:
    """Render an error state display.

    Args:
        title: Error title.
        description: Error description.
        retry_label: Retry button label.
        retry_callback: Retry callback.
        key: Unique key.

    Returns:
        True if retry was clicked.

    Example:
        ```python
        if render_error_state(
            title="Failed to load cards",
            description="Check your connection and try again",
            retry_callback=refresh_data,
        ):
            st.rerun()
        ```
    """
    return render_empty_state(
        title=title,
        description=description,
        illustration="error",
        action_label=retry_label,
        action_callback=retry_callback,
        key=key,
    ) == "primary"


def render_no_results_state(
    search_term: Optional[str] = None,
    clear_callback: Optional[Callable] = None,
    key: str = "no_results",
) -> bool:
    """Render a no search results state.

    Args:
        search_term: The search term that yielded no results.
        clear_callback: Callback to clear the search.
        key: Unique key.

    Returns:
        True if clear was clicked.

    Example:
        ```python
        if render_no_results_state(
            search_term=query,
            clear_callback=lambda: st.session_state.update(search=""),
        ):
            st.rerun()
        ```
    """
    description = f'No results found for "{search_term}"' if search_term else "No results found"

    return render_empty_state(
        title="No matches",
        description=description,
        illustration="search",
        action_label="Clear Search" if clear_callback else None,
        action_callback=clear_callback,
        key=key,
        compact=True,
    ) == "primary"
