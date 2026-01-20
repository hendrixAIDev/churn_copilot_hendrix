"""Progress Indicator component.

Provides progress indicators for multi-step flows, wizards,
and completion tracking.
"""

import streamlit as st
from dataclasses import dataclass
from typing import Optional, List, Literal, Callable


@dataclass
class ProgressStep:
    """Configuration for a progress step.

    Attributes:
        key: Unique identifier for this step.
        label: Step label text.
        description: Optional step description.
        icon: Optional step icon/emoji.
        status: Step status.
    """
    key: str
    label: str
    description: Optional[str] = None
    icon: Optional[str] = None
    status: Literal["pending", "current", "completed", "error"] = "pending"


@dataclass
class ProgressIndicator:
    """Configuration for a progress indicator.

    Attributes:
        key: Unique identifier for this indicator.
        steps: List of progress steps.
        current_step: Index of current step (0-based).
        variant: Display variant.
        show_labels: Whether to show step labels.
        show_numbers: Whether to show step numbers.
        clickable: Whether steps can be clicked to navigate.
    """
    key: str
    steps: List[ProgressStep]
    current_step: int = 0
    variant: Literal["dots", "bar", "steps", "numbered"] = "steps"
    show_labels: bool = True
    show_numbers: bool = True
    clickable: bool = False


# CSS for progress indicator styling
PROGRESS_CSS = """
<style>
/* Progress Container */
.progress-indicator {
    padding: 16px 0;
}

/* Steps Variant */
.progress-steps {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    position: relative;
}

/* Connector Line */
.progress-steps::before {
    content: '';
    position: absolute;
    top: 20px;
    left: 24px;
    right: 24px;
    height: 2px;
    background: #e9ecef;
    z-index: 0;
}

/* Step Item */
.progress-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
    z-index: 1;
    flex: 1;
    max-width: 140px;
}

/* Step Circle */
.step-circle {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.875rem;
    font-weight: 600;
    margin-bottom: 8px;
    transition: all 0.3s ease;
}

/* Step States */
.step-pending .step-circle {
    background: #f8f9fa;
    border: 2px solid #dee2e6;
    color: #6c757d;
}

.step-current .step-circle {
    background: #0066cc;
    border: 2px solid #0066cc;
    color: white;
    box-shadow: 0 4px 12px rgba(0, 102, 204, 0.3);
    transform: scale(1.1);
}

.step-completed .step-circle {
    background: #28a745;
    border: 2px solid #28a745;
    color: white;
}

.step-error .step-circle {
    background: #dc3545;
    border: 2px solid #dc3545;
    color: white;
}

/* Clickable Steps */
.progress-step.clickable {
    cursor: pointer;
}

.progress-step.clickable:hover .step-circle {
    transform: scale(1.05);
}

.progress-step.clickable.step-completed:hover .step-circle {
    background: #1e7e34;
}

/* Step Label */
.step-label {
    font-size: 0.8125rem;
    font-weight: 600;
    color: #495057;
    text-align: center;
    margin-bottom: 4px;
}

.step-pending .step-label {
    color: #6c757d;
}

.step-current .step-label {
    color: #0066cc;
}

.step-completed .step-label {
    color: #28a745;
}

/* Step Description */
.step-description {
    font-size: 0.75rem;
    color: #6c757d;
    text-align: center;
    max-width: 120px;
}

/* Dots Variant */
.progress-dots {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
}

.progress-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    transition: all 0.3s ease;
}

.progress-dot.pending {
    background: #dee2e6;
}

.progress-dot.current {
    background: #0066cc;
    transform: scale(1.3);
    box-shadow: 0 2px 8px rgba(0, 102, 204, 0.3);
}

.progress-dot.completed {
    background: #28a745;
}

/* Bar Variant */
.progress-bar-container {
    background: #e9ecef;
    border-radius: 8px;
    height: 8px;
    overflow: hidden;
    position: relative;
}

.progress-bar-fill {
    height: 100%;
    background: linear-gradient(90deg, #0066cc 0%, #00a3cc 100%);
    border-radius: 8px;
    transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.progress-bar-text {
    display: flex;
    justify-content: space-between;
    margin-top: 8px;
    font-size: 0.8125rem;
}

.progress-bar-label {
    color: #495057;
    font-weight: 500;
}

.progress-bar-percentage {
    color: #0066cc;
    font-weight: 600;
}

/* Numbered Variant */
.progress-numbered {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px;
    background: #f8f9fa;
    border-radius: 8px;
}

.progress-number-current {
    font-size: 1rem;
    font-weight: 700;
    color: #0066cc;
}

.progress-number-total {
    font-size: 1rem;
    color: #6c757d;
}

.progress-number-label {
    font-size: 0.875rem;
    color: #495057;
    margin-left: 8px;
}

/* Mini Progress (inline) */
.progress-mini {
    display: inline-flex;
    align-items: center;
    gap: 8px;
}

.progress-mini-bar {
    width: 100px;
    height: 4px;
    background: #e9ecef;
    border-radius: 2px;
    overflow: hidden;
}

.progress-mini-fill {
    height: 100%;
    background: #0066cc;
    transition: width 0.3s ease;
}

.progress-mini-text {
    font-size: 0.75rem;
    font-weight: 600;
    color: #0066cc;
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
    .progress-steps::before {
        background: #2d2d2d;
    }

    .step-pending .step-circle {
        background: #2d2d2d;
        border-color: #404040;
        color: #adb5bd;
    }

    .step-label {
        color: #f8f9fa;
    }

    .step-pending .step-label {
        color: #adb5bd;
    }

    .step-description {
        color: #adb5bd;
    }

    .progress-dot.pending {
        background: #404040;
    }

    .progress-bar-container {
        background: #2d2d2d;
    }

    .progress-bar-label {
        color: #f8f9fa;
    }

    .progress-numbered {
        background: #2d2d2d;
    }

    .progress-number-label {
        color: #f8f9fa;
    }

    .progress-mini-bar {
        background: #2d2d2d;
    }
}
</style>
"""


def inject_progress_css():
    """Inject the progress indicator CSS styles."""
    st.markdown(PROGRESS_CSS, unsafe_allow_html=True)


def render_progress_indicator(
    config: Optional[ProgressIndicator] = None,
    steps: Optional[List[ProgressStep]] = None,
    current_step: int = 0,
    variant: Literal["dots", "bar", "steps", "numbered"] = "steps",
    show_labels: bool = True,
    show_numbers: bool = True,
    clickable: bool = False,
    key: str = "progress",
    on_step_click: Optional[Callable[[int], None]] = None,
) -> Optional[int]:
    """Render a progress indicator.

    Args:
        config: Optional ProgressIndicator configuration.
        steps: List of progress steps (if config not provided).
        current_step: Current step index (if config not provided).
        variant: Display variant (if config not provided).
        show_labels: Whether to show labels (if config not provided).
        show_numbers: Whether to show numbers (if config not provided).
        clickable: Whether steps are clickable (if config not provided).
        key: Unique key (if config not provided).
        on_step_click: Callback when a step is clicked.

    Returns:
        The clicked step index if clickable and clicked, else None.

    Example:
        ```python
        steps = [
            ProgressStep(key="info", label="Information", status="completed"),
            ProgressStep(key="review", label="Review", status="current"),
            ProgressStep(key="confirm", label="Confirm", status="pending"),
        ]
        render_progress_indicator(steps=steps, current_step=1)
        ```
    """
    inject_progress_css()

    # Use config or individual params
    if config:
        key = config.key
        steps = config.steps
        current_step = config.current_step
        variant = config.variant
        show_labels = config.show_labels
        show_numbers = config.show_numbers
        clickable = config.clickable

    if not steps:
        return None

    clicked_step = None

    # Render based on variant
    if variant == "dots":
        _render_dots_progress(steps, current_step)
    elif variant == "bar":
        _render_bar_progress(steps, current_step)
    elif variant == "numbered":
        _render_numbered_progress(steps, current_step)
    else:  # steps variant
        clicked_step = _render_steps_progress(
            steps, current_step, show_labels, show_numbers, clickable, key, on_step_click
        )

    return clicked_step


def _render_dots_progress(steps: List[ProgressStep], current_step: int) -> None:
    """Render dots-style progress."""
    dots_html = '<div class="progress-dots">'

    for i, step in enumerate(steps):
        if i < current_step:
            state = "completed"
        elif i == current_step:
            state = "current"
        else:
            state = "pending"

        dots_html += f'<div class="progress-dot {state}" title="{step.label}"></div>'

    dots_html += '</div>'
    st.markdown(dots_html, unsafe_allow_html=True)


def _render_bar_progress(steps: List[ProgressStep], current_step: int) -> None:
    """Render bar-style progress."""
    total_steps = len(steps)
    percentage = int(((current_step + 1) / total_steps) * 100)
    current_label = steps[current_step].label if current_step < total_steps else "Complete"

    st.markdown(
        f"""
        <div class="progress-bar-container">
            <div class="progress-bar-fill" style="width: {percentage}%;"></div>
        </div>
        <div class="progress-bar-text">
            <span class="progress-bar-label">{current_label}</span>
            <span class="progress-bar-percentage">{percentage}%</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_numbered_progress(steps: List[ProgressStep], current_step: int) -> None:
    """Render numbered-style progress."""
    total_steps = len(steps)
    current_label = steps[current_step].label if current_step < total_steps else "Complete"

    st.markdown(
        f"""
        <div class="progress-numbered">
            <span class="progress-number-current">{current_step + 1}</span>
            <span class="progress-number-total">/ {total_steps}</span>
            <span class="progress-number-label">{current_label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_steps_progress(
    steps: List[ProgressStep],
    current_step: int,
    show_labels: bool,
    show_numbers: bool,
    clickable: bool,
    key: str,
    on_step_click: Optional[Callable[[int], None]],
) -> Optional[int]:
    """Render steps-style progress."""
    clicked_step = None

    # Use Streamlit columns for the steps layout
    cols = st.columns(len(steps))

    for i, (col, step) in enumerate(zip(cols, steps)):
        with col:
            # Determine step state
            if step.status != "pending":
                state = step.status
            elif i < current_step:
                state = "completed"
            elif i == current_step:
                state = "current"
            else:
                state = "pending"

            # Determine circle content
            if state == "completed":
                content = "✓"
            elif state == "error":
                content = "!"
            elif step.icon:
                content = step.icon
            elif show_numbers:
                content = str(i + 1)
            else:
                content = ""

            clickable_class = "clickable" if clickable and state == "completed" else ""

            # Build step HTML
            html = f"""
            <div class="progress-step step-{state} {clickable_class}">
                <div class="step-circle">{content}</div>
            """

            if show_labels:
                html += f'<div class="step-label">{step.label}</div>'

            if step.description:
                html += f'<div class="step-description">{step.description}</div>'

            html += '</div>'

            st.markdown(html, unsafe_allow_html=True)

            # Handle click for completed steps
            if clickable and state == "completed":
                if st.button(
                    f"Go to {step.label}",
                    key=f"{key}_step_{i}",
                    type="secondary",
                    use_container_width=True,
                ):
                    clicked_step = i
                    if on_step_click:
                        on_step_click(i)

    return clicked_step


def render_mini_progress(
    current: int,
    total: int,
    label: Optional[str] = None,
    show_percentage: bool = True,
    color: str = "#0066cc",
) -> None:
    """Render a mini inline progress indicator.

    Args:
        current: Current progress value.
        total: Total/maximum value.
        label: Optional label text.
        show_percentage: Whether to show percentage.
        color: Progress bar color.

    Example:
        ```python
        render_mini_progress(
            current=3,
            total=10,
            label="Benefits used",
        )
        ```
    """
    inject_progress_css()

    percentage = int((current / max(total, 1)) * 100)

    label_html = f'<span style="color: #6c757d; font-size: 0.75rem; margin-right: 8px;">{label}</span>' if label else ""
    percentage_html = f'<span class="progress-mini-text">{percentage}%</span>' if show_percentage else f'<span class="progress-mini-text">{current}/{total}</span>'

    st.markdown(
        f"""
        <div class="progress-mini">
            {label_html}
            <div class="progress-mini-bar">
                <div class="progress-mini-fill" style="width: {percentage}%; background: {color};"></div>
            </div>
            {percentage_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_completion_progress(
    completed: int,
    total: int,
    label: str = "Complete",
    icon: str = "✓",
) -> None:
    """Render a completion-style progress indicator.

    Args:
        completed: Number of completed items.
        total: Total number of items.
        label: Label text.
        icon: Completion icon.

    Example:
        ```python
        render_completion_progress(
            completed=7,
            total=10,
            label="Benefits tracked",
        )
        ```
    """
    inject_progress_css()

    percentage = int((completed / max(total, 1)) * 100)

    # Determine color based on completion
    if percentage >= 100:
        color = "#28a745"
    elif percentage >= 75:
        color = "#20c997"
    elif percentage >= 50:
        color = "#ffc107"
    else:
        color = "#6c757d"

    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 12px; padding: 12px; background: #f8f9fa; border-radius: 8px;">
            <div style="font-size: 1.5rem;">{icon if percentage >= 100 else "○"}</div>
            <div style="flex: 1;">
                <div style="font-size: 0.875rem; font-weight: 600; color: #212529; margin-bottom: 4px;">{label}</div>
                <div class="progress-bar-container" style="height: 6px;">
                    <div class="progress-bar-fill" style="width: {percentage}%; background: {color};"></div>
                </div>
            </div>
            <div style="font-size: 1rem; font-weight: 700; color: {color};">{completed}/{total}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
