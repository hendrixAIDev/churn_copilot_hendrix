"""Collapsible Section component.

Provides animated collapsible/accordion sections with smooth
expand/collapse transitions.
"""

import streamlit as st
from dataclasses import dataclass
from typing import Optional, Callable, Literal


@dataclass
class CollapsibleSection:
    """Configuration for a collapsible section.

    Attributes:
        key: Unique identifier for this section.
        title: Section header text.
        subtitle: Optional secondary text in header.
        icon: Optional icon for the header.
        default_expanded: Whether section starts expanded.
        badge: Optional badge text (e.g., count).
        badge_color: Badge background color.
    """
    key: str
    title: str
    subtitle: Optional[str] = None
    icon: Optional[str] = None
    default_expanded: bool = False
    badge: Optional[str] = None
    badge_color: str = "#6c757d"


# CSS for collapsible section styling
COLLAPSIBLE_CSS = """
<style>
/* Collapsible Section Container */
.collapsible-section {
    background: white;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    margin-bottom: 12px;
    border: 1px solid #e9ecef;
}

/* Header */
.collapsible-header {
    display: flex;
    align-items: center;
    padding: 16px;
    cursor: pointer;
    user-select: none;
    -webkit-tap-highlight-color: transparent;
    transition: background-color 0.15s ease;
}

.collapsible-header:hover {
    background-color: #f8f9fa;
}

.collapsible-header:active {
    background-color: #e9ecef;
}

/* Icon Container */
.collapsible-icon {
    font-size: 1.25rem;
    margin-right: 12px;
    flex-shrink: 0;
}

/* Title Area */
.collapsible-title-area {
    flex: 1;
    min-width: 0;
}

.collapsible-title {
    font-size: 1rem;
    font-weight: 600;
    color: #212529;
    margin: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.collapsible-subtitle {
    font-size: 0.8125rem;
    color: #6c757d;
    margin-top: 2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* Badge */
.collapsible-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 24px;
    height: 24px;
    padding: 0 8px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
    color: white;
    margin-right: 12px;
}

/* Chevron */
.collapsible-chevron {
    font-size: 1rem;
    color: #adb5bd;
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    flex-shrink: 0;
}

.collapsible-chevron.expanded {
    transform: rotate(180deg);
}

/* Content */
.collapsible-content {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.collapsible-content.expanded {
    max-height: 2000px; /* Large enough for most content */
}

.collapsible-content-inner {
    padding: 0 16px 16px;
    border-top: 1px solid #e9ecef;
}

/* Animated Content Reveal */
.collapsible-content-inner > * {
    opacity: 0;
    transform: translateY(-10px);
    transition: opacity 0.2s ease, transform 0.2s ease;
}

.collapsible-content.expanded .collapsible-content-inner > * {
    opacity: 1;
    transform: translateY(0);
}

/* Accordion Group */
.accordion-group .collapsible-section {
    border-radius: 0;
    margin-bottom: 0;
    border-bottom: none;
}

.accordion-group .collapsible-section:first-child {
    border-radius: 12px 12px 0 0;
}

.accordion-group .collapsible-section:last-child {
    border-radius: 0 0 12px 12px;
    border-bottom: 1px solid #e9ecef;
}

.accordion-group .collapsible-section:only-child {
    border-radius: 12px;
    border-bottom: 1px solid #e9ecef;
}

/* Simple Collapsible (inline style) */
.collapsible-simple {
    border: none;
    box-shadow: none;
    background: transparent;
}

.collapsible-simple .collapsible-header {
    padding: 12px 0;
    border-radius: 8px;
}

.collapsible-simple .collapsible-content-inner {
    border-top: none;
    padding: 0 0 12px;
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
    .collapsible-section {
        background: #1a1a1a;
        border-color: #2d2d2d;
    }

    .collapsible-header:hover {
        background-color: #2d2d2d;
    }

    .collapsible-header:active {
        background-color: #3d3d3d;
    }

    .collapsible-title {
        color: #f8f9fa;
    }

    .collapsible-subtitle {
        color: #adb5bd;
    }

    .collapsible-content-inner {
        border-top-color: #2d2d2d;
    }
}
</style>
"""


def inject_collapsible_css():
    """Inject the collapsible section CSS styles."""
    st.markdown(COLLAPSIBLE_CSS, unsafe_allow_html=True)


def render_collapsible_section(
    config: CollapsibleSection,
    content_renderer: Callable[[], None],
    variant: Literal["card", "simple"] = "card",
) -> bool:
    """Render a collapsible section with animated content.

    Args:
        config: Collapsible section configuration.
        content_renderer: Function that renders the section content.
        variant: Style variant - 'card' (boxed) or 'simple' (inline).

    Returns:
        True if the section is currently expanded, False otherwise.

    Example:
        ```python
        section = CollapsibleSection(
            key="advanced_options",
            title="Advanced Options",
            subtitle="Configure additional settings",
            icon="⚙️",
            badge="3",
            badge_color="#0066cc",
        )

        def render_content():
            st.checkbox("Enable feature A")
            st.checkbox("Enable feature B")

        is_expanded = render_collapsible_section(section, render_content)
        ```
    """
    inject_collapsible_css()

    # Track expanded state
    expanded_key = f"{config.key}_expanded"
    if expanded_key not in st.session_state:
        st.session_state[expanded_key] = config.default_expanded

    is_expanded = st.session_state[expanded_key]

    # Build CSS classes
    variant_class = "collapsible-simple" if variant == "simple" else ""
    expanded_class = "expanded" if is_expanded else ""

    # Render the section structure
    with st.container():
        # Header row with button for toggle
        cols = st.columns([0.1, 0.9] if config.icon else [1])

        # Use first column for icon if present
        col_idx = 0
        if config.icon:
            with cols[0]:
                st.markdown(f"<span style='font-size: 1.25rem;'>{config.icon}</span>", unsafe_allow_html=True)
            col_idx = 1

        with cols[col_idx] if config.icon else cols[0]:
            # Build header content
            header_content = f"**{config.title}**"
            if config.badge:
                header_content += f" `{config.badge}`"
            if config.subtitle:
                header_content += f"\n\n_{config.subtitle}_"

            # Toggle button
            toggle_label = f"{'▼' if is_expanded else '▶'} {config.title}"
            if config.badge:
                toggle_label += f" ({config.badge})"

            if st.button(
                toggle_label,
                key=f"{config.key}_toggle",
                type="secondary",
                use_container_width=True,
            ):
                st.session_state[expanded_key] = not is_expanded
                st.rerun()

        # Content (only render when expanded)
        if is_expanded:
            with st.container():
                content_renderer()

    return is_expanded


def render_accordion_group(
    sections: list[tuple[CollapsibleSection, Callable[[], None]]],
    allow_multiple: bool = False,
) -> list[str]:
    """Render a group of collapsible sections as an accordion.

    Args:
        sections: List of (config, content_renderer) tuples.
        allow_multiple: Whether multiple sections can be open at once.

    Returns:
        List of keys of currently expanded sections.

    Example:
        ```python
        sections = [
            (CollapsibleSection(key="sec1", title="Section 1"), render_sec1),
            (CollapsibleSection(key="sec2", title="Section 2"), render_sec2),
        ]

        expanded = render_accordion_group(sections)
        ```
    """
    inject_collapsible_css()

    expanded_sections = []

    for config, content_renderer in sections:
        expanded_key = f"{config.key}_expanded"
        if expanded_key not in st.session_state:
            st.session_state[expanded_key] = config.default_expanded

        is_expanded = st.session_state.get(expanded_key, False)

        # Toggle button
        toggle_label = f"{'▼' if is_expanded else '▶'} {config.title}"
        if config.badge:
            toggle_label += f" ({config.badge})"
        if config.icon:
            toggle_label = f"{config.icon} {toggle_label}"

        if st.button(
            toggle_label,
            key=f"{config.key}_toggle",
            type="secondary",
            use_container_width=True,
        ):
            if not allow_multiple:
                # Close all other sections
                for other_config, _ in sections:
                    if other_config.key != config.key:
                        st.session_state[f"{other_config.key}_expanded"] = False

            st.session_state[expanded_key] = not is_expanded
            st.rerun()

        # Content
        if is_expanded:
            expanded_sections.append(config.key)
            with st.container():
                content_renderer()

        st.markdown("---")

    return expanded_sections


def render_details_summary(
    summary: str,
    key: str,
    default_open: bool = False,
) -> bool:
    """Render a simple details/summary disclosure element.

    This is a minimal collapsible without extra styling,
    similar to HTML's <details>/<summary>.

    Args:
        summary: Text for the clickable summary line.
        key: Unique key for this element.
        default_open: Whether to start expanded.

    Returns:
        True if currently open.

    Example:
        ```python
        if render_details_summary("Show more details", key="details1"):
            st.write("Here are the details...")
        ```
    """
    open_key = f"{key}_open"
    if open_key not in st.session_state:
        st.session_state[open_key] = default_open

    is_open = st.session_state[open_key]
    icon = "▼" if is_open else "▶"

    if st.button(f"{icon} {summary}", key=f"{key}_toggle", type="secondary"):
        st.session_state[open_key] = not is_open
        st.rerun()

    return is_open
