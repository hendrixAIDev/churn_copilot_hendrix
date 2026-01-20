"""Reusable UI components for ChurnPilot.

This module provides a library of mobile-first, accessible UI components
designed for Streamlit applications. Each component follows consistent
patterns for styling and behavior.

Components:
- BottomSheet: Slide-up modal for mobile-friendly interactions
- StickyActionBar: Fixed action buttons at screen bottom
- TouchFeedback: Haptic-style visual feedback for touch interactions
- PullToRefresh: Pull-down refresh indicator
- SwipeableCard: Cards with swipe gesture actions
- CollapsibleSection: Animated expand/collapse sections
- LoadingStates: Spinners, pulses, and skeleton screens
- EmptyState: Friendly empty state displays with CTAs
- FormField: Enhanced form inputs with validation
- ProgressIndicator: Multi-step progress displays
- Toast: Non-intrusive notifications

Usage:
    from src.ui.components import (
        render_bottom_sheet,
        render_empty_state,
        render_loading_spinner,
    )
"""

# Bottom Sheet
from .bottom_sheet import (
    BottomSheet,
    render_bottom_sheet,
    open_bottom_sheet,
    close_bottom_sheet,
    is_bottom_sheet_open,
)

# Sticky Action Bar
from .sticky_action_bar import (
    StickyActionBar,
    ActionButton,
    render_sticky_action_bar,
    create_action_bar_simple,
)

# Touch Feedback
from .touch_feedback import (
    TouchFeedback,
    render_touch_feedback_button,
    render_touch_list_item,
    inject_touch_feedback_css,
)

# Pull to Refresh
from .pull_to_refresh import (
    PullToRefresh,
    render_pull_to_refresh_indicator,
    render_refresh_button,
)

# Swipeable Card
from .swipeable_card import (
    SwipeableCard,
    SwipeAction,
    render_card_with_actions,
    create_delete_action,
    create_archive_action,
    create_complete_action,
)

# Collapsible Section
from .collapsible import (
    CollapsibleSection,
    render_collapsible_section,
    render_accordion_group,
    render_details_summary,
)

# Loading States
from .loading import (
    LoadingSpinner,
    LoadingPulse,
    LoadingSkeleton,
    render_loading_spinner,
    render_loading_pulse,
    render_skeleton,
    render_skeleton_card,
    render_full_page_loading,
    render_inline_loading,
)

# Empty State
from .empty_state import (
    EmptyState,
    render_empty_state,
    render_inline_empty,
    render_error_state,
    render_no_results_state,
)

# Form Field
from .form_field import (
    FormField,
    FieldGroup,
    render_form_field,
    render_field_feedback,
    render_field_group,
    render_currency_input,
    render_date_input,
    render_select_input,
    render_text_input,
)

# Progress Indicator
from .progress import (
    ProgressIndicator,
    ProgressStep,
    render_progress_indicator,
    render_mini_progress,
    render_completion_progress,
)

# Toast / Snackbar
from .toast import (
    Toast,
    render_toast,
    show_toast_success,
    show_toast_error,
    show_toast_warning,
    show_toast_info,
    render_snackbar,
    render_notification_badge,
    render_status_indicator,
)

__all__ = [
    # Bottom Sheet
    "BottomSheet",
    "render_bottom_sheet",
    "open_bottom_sheet",
    "close_bottom_sheet",
    "is_bottom_sheet_open",
    # Sticky Action Bar
    "StickyActionBar",
    "ActionButton",
    "render_sticky_action_bar",
    "create_action_bar_simple",
    # Touch Feedback
    "TouchFeedback",
    "render_touch_feedback_button",
    "render_touch_list_item",
    "inject_touch_feedback_css",
    # Pull to Refresh
    "PullToRefresh",
    "render_pull_to_refresh_indicator",
    "render_refresh_button",
    # Swipeable Card
    "SwipeableCard",
    "SwipeAction",
    "render_card_with_actions",
    "create_delete_action",
    "create_archive_action",
    "create_complete_action",
    # Collapsible Section
    "CollapsibleSection",
    "render_collapsible_section",
    "render_accordion_group",
    "render_details_summary",
    # Loading States
    "LoadingSpinner",
    "LoadingPulse",
    "LoadingSkeleton",
    "render_loading_spinner",
    "render_loading_pulse",
    "render_skeleton",
    "render_skeleton_card",
    "render_full_page_loading",
    "render_inline_loading",
    # Empty State
    "EmptyState",
    "render_empty_state",
    "render_inline_empty",
    "render_error_state",
    "render_no_results_state",
    # Form Field
    "FormField",
    "FieldGroup",
    "render_form_field",
    "render_field_feedback",
    "render_field_group",
    "render_currency_input",
    "render_date_input",
    "render_select_input",
    "render_text_input",
    # Progress Indicator
    "ProgressIndicator",
    "ProgressStep",
    "render_progress_indicator",
    "render_mini_progress",
    "render_completion_progress",
    # Toast / Snackbar
    "Toast",
    "render_toast",
    "show_toast_success",
    "show_toast_error",
    "show_toast_warning",
    "show_toast_info",
    "render_snackbar",
    "render_notification_badge",
    "render_status_indicator",
]
