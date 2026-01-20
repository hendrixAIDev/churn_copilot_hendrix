"""Loading States component library.

Provides various loading indicators and skeleton screens for
better perceived performance.
"""

import streamlit as st
from dataclasses import dataclass
from typing import Optional, Literal, List


@dataclass
class LoadingSpinner:
    """Configuration for a loading spinner.

    Attributes:
        size: Size preset - 'sm', 'md', 'lg'.
        color: Spinner color (CSS color value).
        label: Optional text label.
    """
    size: Literal["sm", "md", "lg"] = "md"
    color: str = "#0066cc"
    label: Optional[str] = None


@dataclass
class LoadingPulse:
    """Configuration for a pulsing loading indicator.

    Attributes:
        size: Number of dots.
        color: Dot color.
        label: Optional text label.
    """
    size: int = 3
    color: str = "#0066cc"
    label: Optional[str] = None


@dataclass
class LoadingSkeleton:
    """Configuration for a skeleton loading placeholder.

    Attributes:
        variant: Shape variant - 'text', 'circle', 'rect', 'card'.
        width: Width (CSS value or percentage).
        height: Height (CSS value or pixels).
        count: Number of skeleton elements.
        animate: Whether to show shimmer animation.
    """
    variant: Literal["text", "circle", "rect", "card"] = "text"
    width: str = "100%"
    height: str = "auto"
    count: int = 1
    animate: bool = True


# CSS for loading states
LOADING_CSS = """
<style>
/* Spinner Base */
.loading-spinner {
    display: inline-block;
    border-radius: 50%;
    border-style: solid;
    border-top-color: transparent !important;
    animation: spin 0.8s linear infinite;
}

.loading-spinner.sm {
    width: 16px;
    height: 16px;
    border-width: 2px;
}

.loading-spinner.md {
    width: 32px;
    height: 32px;
    border-width: 3px;
}

.loading-spinner.lg {
    width: 48px;
    height: 48px;
    border-width: 4px;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}

/* Spinner Container */
.spinner-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 24px;
    gap: 12px;
}

.spinner-label {
    font-size: 0.875rem;
    color: #6c757d;
    font-weight: 500;
}

/* Pulse Dots */
.pulse-container {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 16px;
}

.pulse-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    animation: pulse 1.4s ease-in-out infinite;
}

.pulse-dot:nth-child(1) {
    animation-delay: 0s;
}

.pulse-dot:nth-child(2) {
    animation-delay: 0.2s;
}

.pulse-dot:nth-child(3) {
    animation-delay: 0.4s;
}

@keyframes pulse {
    0%, 80%, 100% {
        transform: scale(0.6);
        opacity: 0.5;
    }
    40% {
        transform: scale(1);
        opacity: 1;
    }
}

.pulse-label {
    margin-left: 12px;
    font-size: 0.875rem;
    color: #6c757d;
}

/* Skeleton Base */
.skeleton {
    background: linear-gradient(90deg, #e9ecef 25%, #f8f9fa 50%, #e9ecef 75%);
    background-size: 200% 100%;
    border-radius: 4px;
}

.skeleton.animate {
    animation: shimmer 1.5s ease-in-out infinite;
}

@keyframes shimmer {
    0% {
        background-position: 200% 0;
    }
    100% {
        background-position: -200% 0;
    }
}

/* Skeleton Variants */
.skeleton.text {
    height: 16px;
    margin-bottom: 8px;
    border-radius: 4px;
}

.skeleton.text:last-child {
    width: 60%;
}

.skeleton.circle {
    border-radius: 50%;
}

.skeleton.rect {
    border-radius: 8px;
}

.skeleton.card {
    padding: 16px;
    border-radius: 12px;
}

/* Skeleton Card Layout */
.skeleton-card {
    background: white;
    border-radius: 12px;
    padding: 16px;
    border: 1px solid #e9ecef;
    margin-bottom: 12px;
}

.skeleton-card-header {
    display: flex;
    align-items: center;
    margin-bottom: 16px;
}

.skeleton-avatar {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    margin-right: 12px;
}

.skeleton-card-content {
    margin-bottom: 12px;
}

/* Full Page Loading */
.full-page-loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 60vh;
    gap: 24px;
}

.loading-message {
    font-size: 1.125rem;
    color: #495057;
    font-weight: 500;
    text-align: center;
}

.loading-submessage {
    font-size: 0.875rem;
    color: #6c757d;
    text-align: center;
    max-width: 300px;
}

/* Progress Bar Loading */
.loading-progress {
    width: 100%;
    max-width: 300px;
    height: 4px;
    background: #e9ecef;
    border-radius: 2px;
    overflow: hidden;
}

.loading-progress-bar {
    height: 100%;
    border-radius: 2px;
    transition: width 0.3s ease;
}

.loading-progress-bar.indeterminate {
    width: 30%;
    animation: progress-indeterminate 1.5s ease-in-out infinite;
}

@keyframes progress-indeterminate {
    0% {
        transform: translateX(-100%);
    }
    100% {
        transform: translateX(400%);
    }
}

/* Inline Loading */
.inline-loading {
    display: inline-flex;
    align-items: center;
    gap: 8px;
}

.inline-loading .loading-spinner {
    width: 14px;
    height: 14px;
    border-width: 2px;
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
    .skeleton {
        background: linear-gradient(90deg, #2d2d2d 25%, #3d3d3d 50%, #2d2d2d 75%);
        background-size: 200% 100%;
    }

    .spinner-label,
    .pulse-label {
        color: #adb5bd;
    }

    .skeleton-card {
        background: #1a1a1a;
        border-color: #2d2d2d;
    }

    .loading-message {
        color: #f8f9fa;
    }

    .loading-progress {
        background: #2d2d2d;
    }
}
</style>
"""


def inject_loading_css():
    """Inject the loading states CSS styles."""
    st.markdown(LOADING_CSS, unsafe_allow_html=True)


def render_loading_spinner(
    config: Optional[LoadingSpinner] = None,
    size: Literal["sm", "md", "lg"] = "md",
    color: str = "#0066cc",
    label: Optional[str] = None,
) -> None:
    """Render a loading spinner.

    Args:
        config: Optional LoadingSpinner configuration.
        size: Size preset (if config not provided).
        color: Spinner color (if config not provided).
        label: Text label (if config not provided).

    Example:
        ```python
        render_loading_spinner(size="lg", label="Loading cards...")
        ```
    """
    inject_loading_css()

    # Use config or individual params
    if config:
        size = config.size
        color = config.color
        label = config.label

    html = f"""
    <div class="spinner-container">
        <div class="loading-spinner {size}" style="border-color: {color};"></div>
        {f'<span class="spinner-label">{label}</span>' if label else ''}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_loading_pulse(
    config: Optional[LoadingPulse] = None,
    size: int = 3,
    color: str = "#0066cc",
    label: Optional[str] = None,
) -> None:
    """Render a pulsing dots loading indicator.

    Args:
        config: Optional LoadingPulse configuration.
        size: Number of dots (if config not provided).
        color: Dot color (if config not provided).
        label: Text label (if config not provided).

    Example:
        ```python
        render_loading_pulse(label="Processing...")
        ```
    """
    inject_loading_css()

    # Use config or individual params
    if config:
        size = config.size
        color = config.color
        label = config.label

    dots = "".join([f'<div class="pulse-dot" style="background: {color};"></div>' for _ in range(size)])

    html = f"""
    <div class="pulse-container">
        {dots}
        {f'<span class="pulse-label">{label}</span>' if label else ''}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_skeleton(
    config: Optional[LoadingSkeleton] = None,
    variant: Literal["text", "circle", "rect", "card"] = "text",
    width: str = "100%",
    height: str = "auto",
    count: int = 1,
    animate: bool = True,
) -> None:
    """Render skeleton loading placeholders.

    Args:
        config: Optional LoadingSkeleton configuration.
        variant: Shape variant (if config not provided).
        width: Width CSS value (if config not provided).
        height: Height CSS value (if config not provided).
        count: Number of elements (if config not provided).
        animate: Whether to animate (if config not provided).

    Example:
        ```python
        # Text lines skeleton
        render_skeleton(variant="text", count=3)

        # Avatar skeleton
        render_skeleton(variant="circle", width="48px", height="48px")
        ```
    """
    inject_loading_css()

    # Use config or individual params
    if config:
        variant = config.variant
        width = config.width
        height = config.height
        count = config.count
        animate = config.animate

    animate_class = "animate" if animate else ""

    # Set default heights based on variant
    if height == "auto":
        heights = {
            "text": "16px",
            "circle": "48px",
            "rect": "100px",
            "card": "120px",
        }
        height = heights.get(variant, "16px")

    # For circle, width should equal height
    if variant == "circle" and width == "100%":
        width = height

    for i in range(count):
        # Vary width for text lines
        line_width = width
        if variant == "text" and i == count - 1 and count > 1:
            line_width = "60%"

        html = f"""
        <div class="skeleton {variant} {animate_class}"
             style="width: {line_width}; height: {height};"></div>
        """
        st.markdown(html, unsafe_allow_html=True)


def render_skeleton_card(
    show_avatar: bool = True,
    text_lines: int = 3,
    animate: bool = True,
) -> None:
    """Render a card skeleton placeholder.

    Args:
        show_avatar: Whether to show avatar circle.
        text_lines: Number of text lines.
        animate: Whether to animate.

    Example:
        ```python
        # Show 3 card skeletons while loading
        for _ in range(3):
            render_skeleton_card()
        ```
    """
    inject_loading_css()

    animate_class = "animate" if animate else ""

    avatar_html = ""
    if show_avatar:
        avatar_html = f'<div class="skeleton {animate_class} skeleton-avatar"></div>'

    text_html = ""
    for i in range(text_lines):
        width = "60%" if i == text_lines - 1 else "100%"
        text_html += f'<div class="skeleton {animate_class} text" style="width: {width};"></div>'

    html = f"""
    <div class="skeleton-card">
        <div class="skeleton-card-header">
            {avatar_html}
            <div style="flex: 1;">
                <div class="skeleton {animate_class} text" style="width: 70%;"></div>
                <div class="skeleton {animate_class} text" style="width: 40%; height: 12px;"></div>
            </div>
        </div>
        <div class="skeleton-card-content">
            {text_html}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_full_page_loading(
    message: str = "Loading...",
    submessage: Optional[str] = None,
    show_progress: bool = False,
    progress: Optional[int] = None,
    spinner_color: str = "#0066cc",
) -> None:
    """Render a full-page loading state.

    Args:
        message: Main loading message.
        submessage: Optional secondary message.
        show_progress: Whether to show progress bar.
        progress: Progress percentage (0-100), or None for indeterminate.
        spinner_color: Color for the spinner.

    Example:
        ```python
        render_full_page_loading(
            message="Importing cards...",
            submessage="This may take a few moments",
            show_progress=True,
            progress=45,
        )
        ```
    """
    inject_loading_css()

    # Build progress bar HTML
    progress_html = ""
    if show_progress:
        if progress is not None:
            progress_html = f"""
            <div class="loading-progress">
                <div class="loading-progress-bar" style="width: {progress}%; background: {spinner_color};"></div>
            </div>
            """
        else:
            progress_html = f"""
            <div class="loading-progress">
                <div class="loading-progress-bar indeterminate" style="background: {spinner_color};"></div>
            </div>
            """

    submessage_html = f'<div class="loading-submessage">{submessage}</div>' if submessage else ""

    html = f"""
    <div class="full-page-loading">
        <div class="loading-spinner lg" style="border-color: {spinner_color};"></div>
        <div class="loading-message">{message}</div>
        {submessage_html}
        {progress_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_inline_loading(
    label: str = "Loading...",
    color: str = "#0066cc",
) -> None:
    """Render an inline loading indicator.

    Args:
        label: Text label.
        color: Spinner color.

    Example:
        ```python
        col1, col2 = st.columns(2)
        with col1:
            render_inline_loading("Saving...")
        ```
    """
    inject_loading_css()

    html = f"""
    <div class="inline-loading">
        <div class="loading-spinner sm" style="border-color: {color};"></div>
        <span style="color: #6c757d; font-size: 0.875rem;">{label}</span>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
