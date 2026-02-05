"""Onboarding Wizard component.

Provides a step-by-step guided onboarding experience for first-time users.
"""

import streamlit as st
from typing import Optional, Callable, Literal
from dataclasses import dataclass


# CSS for wizard styling
WIZARD_CSS = """
<style>
/* Wizard Overlay */
.wizard-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.85);
    backdrop-filter: blur(8px);
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: center;
    animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

/* Wizard Container */
.wizard-container {
    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
    border-radius: 24px;
    padding: 48px;
    max-width: 600px;
    width: 90vw;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    position: relative;
    animation: slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideUp {
    from {
        transform: translateY(40px);
        opacity: 0;
    }
    to {
        transform: translateY(0);
        opacity: 1;
    }
}

/* Progress Bar */
.wizard-progress {
    display: flex;
    gap: 8px;
    margin-bottom: 32px;
}

.wizard-progress-step {
    height: 4px;
    flex: 1;
    background: #e9ecef;
    border-radius: 2px;
    transition: background 0.3s ease;
}

.wizard-progress-step.active {
    background: linear-gradient(90deg, #6366f1 0%, #a855f7 100%);
}

.wizard-progress-step.completed {
    background: #10b981;
}

/* Step Content */
.wizard-step {
    text-align: center;
    min-height: 300px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.wizard-icon {
    font-size: 4rem;
    margin-bottom: 24px;
    animation: float 3s ease-in-out infinite;
}

@keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
}

.wizard-title {
    font-size: 2rem;
    font-weight: 800;
    color: #212529;
    margin: 0 0 16px;
    line-height: 1.2;
}

.wizard-highlight {
    background: linear-gradient(90deg, #6366f1 0%, #a855f7 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.wizard-description {
    font-size: 1.125rem;
    color: #6c757d;
    margin: 0 0 32px;
    line-height: 1.6;
}

/* Feature Cards in Step 2 */
.wizard-features {
    display: grid;
    grid-template-columns: 1fr;
    gap: 16px;
    margin-bottom: 32px;
    text-align: left;
}

.wizard-feature {
    background: white;
    border: 2px solid #e9ecef;
    border-radius: 12px;
    padding: 20px;
    transition: all 0.3s ease;
    cursor: pointer;
}

.wizard-feature:hover {
    border-color: #6366f1;
    transform: translateX(4px);
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.1);
}

.wizard-feature-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;
}

.wizard-feature-icon {
    font-size: 1.75rem;
}

.wizard-feature-title {
    font-size: 1.125rem;
    font-weight: 700;
    color: #212529;
    margin: 0;
}

.wizard-feature-desc {
    font-size: 0.9375rem;
    color: #6c757d;
    margin: 0;
    line-height: 1.5;
}

.wizard-feature-badge {
    display: inline-block;
    background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
    color: white;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 12px;
    margin-top: 8px;
}

/* Next Steps List (Step 3) */
.wizard-next-steps {
    text-align: left;
    margin-bottom: 32px;
}

.wizard-next-step {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    padding: 16px;
    background: white;
    border-radius: 12px;
    margin-bottom: 12px;
    border: 2px solid #e9ecef;
}

.wizard-next-step-icon {
    font-size: 1.5rem;
    flex-shrink: 0;
}

.wizard-next-step-content {
    flex: 1;
}

.wizard-next-step-title {
    font-size: 1rem;
    font-weight: 600;
    color: #212529;
    margin: 0 0 4px;
}

.wizard-next-step-desc {
    font-size: 0.875rem;
    color: #6c757d;
    margin: 0;
}

/* Skip Button */
.wizard-skip {
    position: absolute;
    top: 24px;
    right: 24px;
    background: none;
    border: none;
    color: #6c757d;
    font-size: 0.875rem;
    cursor: pointer;
    padding: 8px 16px;
    border-radius: 8px;
    transition: all 0.2s ease;
}

.wizard-skip:hover {
    background: rgba(0, 0, 0, 0.05);
    color: #212529;
}

/* Dark Mode */
@media (prefers-color-scheme: dark) {
    .wizard-container {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
    }

    .wizard-title {
        color: #f8f9fa;
    }

    .wizard-description {
        color: #adb5bd;
    }

    .wizard-feature {
        background: #2d2d2d;
        border-color: #404040;
    }

    .wizard-feature:hover {
        border-color: #6366f1;
        background: #333333;
    }

    .wizard-feature-title {
        color: #f8f9fa;
    }

    .wizard-feature-desc {
        color: #adb5bd;
    }

    .wizard-next-step {
        background: #2d2d2d;
        border-color: #404040;
    }

    .wizard-next-step-title {
        color: #f8f9fa;
    }

    .wizard-next-step-desc {
        color: #adb5bd;
    }

    .wizard-skip {
        color: #adb5bd;
    }

    .wizard-skip:hover {
        background: rgba(255, 255, 255, 0.1);
        color: #f8f9fa;
    }
}

/* Mobile */
@media (max-width: 768px) {
    .wizard-container {
        padding: 32px 24px;
    }

    .wizard-title {
        font-size: 1.5rem;
    }

    .wizard-description {
        font-size: 1rem;
    }
}
</style>
"""


def inject_wizard_css():
    """Inject wizard CSS styles."""
    st.markdown(WIZARD_CSS, unsafe_allow_html=True)


def render_onboarding_wizard(
    current_step: int = 1,
    template_count: int = 18,
    on_complete: Optional[Callable] = None,
    on_skip: Optional[Callable] = None,
    key_prefix: str = "wizard",
) -> Optional[str]:
    """Render the onboarding wizard.

    Args:
        current_step: Current step (1-3).
        template_count: Number of card templates available.
        on_complete: Callback when wizard completes.
        on_skip: Callback when wizard is skipped.
        key_prefix: Unique key prefix.

    Returns:
        Action taken: "next", "skip", "add_card", or None.

    Example:
        ```python
        action = render_onboarding_wizard(
            current_step=st.session_state.get("wizard_step", 1),
            template_count=40,
            on_complete=lambda: mark_wizard_complete(),
            on_skip=lambda: dismiss_wizard(),
        )
        
        if action == "next":
            st.session_state.wizard_step += 1
            st.rerun()
        elif action == "skip":
            st.session_state.wizard_completed = True
            st.rerun()
        ```
    """
    inject_wizard_css()

    clicked_action = None

    # Build progress bar HTML
    progress_html = '<div class="wizard-progress">'
    for i in range(1, 4):
        if i < current_step:
            progress_html += '<div class="wizard-progress-step completed"></div>'
        elif i == current_step:
            progress_html += '<div class="wizard-progress-step active"></div>'
        else:
            progress_html += '<div class="wizard-progress-step"></div>'
    progress_html += '</div>'

    # Render wizard overlay
    st.markdown('<div class="wizard-overlay">', unsafe_allow_html=True)
    st.markdown('<div class="wizard-container">', unsafe_allow_html=True)

    # Skip button at top right
    col_skip1, col_skip2 = st.columns([5, 1])
    with col_skip2:
        if st.button("Skip ✕", key=f"{key_prefix}_skip_btn", help="Skip onboarding"):
            clicked_action = "skip"
            if on_skip:
                on_skip()

    # Progress bar
    st.markdown(progress_html, unsafe_allow_html=True)

    # Step content
    if current_step == 1:
        # Step 1: Welcome
        st.markdown(
            """
            <div class="wizard-step">
                <div class="wizard-icon">✈️</div>
                <h1 class="wizard-title">
                    Welcome to <span class="wizard-highlight">ChurnPilot</span>
                </h1>
                <p class="wizard-description">
                    Your personal credit card churning companion. Track signup bonuses, 
                    maximize benefits, and never miss a deadline again.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    elif current_step == 2:
        # Step 2: Add Your First Card
        st.markdown(
            f"""
            <div class="wizard-step">
                <div class="wizard-icon">💳</div>
                <h1 class="wizard-title">
                    Add Your First Card
                </h1>
                <p class="wizard-description">
                    Choose the method that works best for you
                </p>
                <div class="wizard-features">
                    <div class="wizard-feature">
                        <div class="wizard-feature-header">
                            <span class="wizard-feature-icon">📚</span>
                            <h3 class="wizard-feature-title">Card Library</h3>
                        </div>
                        <p class="wizard-feature-desc">
                            Select from {template_count}+ pre-built templates with all details already filled in
                        </p>
                        <span class="wizard-feature-badge">FASTEST</span>
                    </div>
                    <div class="wizard-feature">
                        <div class="wizard-feature-header">
                            <span class="wizard-feature-icon">🤖</span>
                            <h3 class="wizard-feature-title">AI Extraction</h3>
                        </div>
                        <p class="wizard-feature-desc">
                            Paste any card offer URL and let AI extract all the details automatically
                        </p>
                        <span class="wizard-feature-badge">SMARTEST</span>
                    </div>
                    <div class="wizard-feature">
                        <div class="wizard-feature-header">
                            <span class="wizard-feature-icon">✍️</span>
                            <h3 class="wizard-feature-title">Manual Entry</h3>
                        </div>
                        <p class="wizard-feature-desc">
                            Full control — enter all card details yourself for maximum customization
                        </p>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    elif current_step == 3:
        # Step 3: What's Next
        st.markdown(
            """
            <div class="wizard-step">
                <div class="wizard-icon">🎯</div>
                <h1 class="wizard-title">
                    What's Next?
                </h1>
                <p class="wizard-description">
                    Here's what you can do with ChurnPilot
                </p>
                <div class="wizard-next-steps">
                    <div class="wizard-next-step">
                        <span class="wizard-next-step-icon">💰</span>
                        <div class="wizard-next-step-content">
                            <h4 class="wizard-next-step-title">Track Benefits & Credits</h4>
                            <p class="wizard-next-step-desc">
                                Mark monthly credits as used so you never leave money on the table
                            </p>
                        </div>
                    </div>
                    <div class="wizard-next-step">
                        <span class="wizard-next-step-icon">🎯</span>
                        <div class="wizard-next-step-content">
                            <h4 class="wizard-next-step-title">Monitor 5/24 Status</h4>
                            <p class="wizard-next-step-desc">
                                Know exactly when you can apply for more Chase cards
                            </p>
                        </div>
                    </div>
                    <div class="wizard-next-step">
                        <span class="wizard-next-step-icon">📊</span>
                        <div class="wizard-next-step-content">
                            <h4 class="wizard-next-step-title">View Portfolio Analytics</h4>
                            <p class="wizard-next-step-desc">
                                See your total value, spend progress, and upcoming deadlines
                            </p>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Action buttons
    st.markdown('<div style="margin-top: 32px;"></div>', unsafe_allow_html=True)

    if current_step < 3:
        # Next button for steps 1-2
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                "Continue →" if current_step == 1 else "Add Card Now →",
                key=f"{key_prefix}_next_btn",
                type="primary",
                use_container_width=True,
            ):
                if current_step == 2:
                    # Step 2: Go directly to add card
                    clicked_action = "add_card"
                    if on_complete:
                        on_complete()
                else:
                    clicked_action = "next"
    else:
        # Step 3: Finish button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                "Get Started! 🚀",
                key=f"{key_prefix}_finish_btn",
                type="primary",
                use_container_width=True,
            ):
                clicked_action = "complete"
                if on_complete:
                    on_complete()

    st.markdown('</div>', unsafe_allow_html=True)  # Close wizard-container
    st.markdown('</div>', unsafe_allow_html=True)  # Close wizard-overlay

    return clicked_action


def should_show_wizard(user_id: Optional[str] = None) -> bool:
    """Check if the onboarding wizard should be shown.

    Args:
        user_id: Current user's ID (optional).

    Returns:
        True if wizard should be shown, False otherwise.

    Logic:
        - Never show if user has cards
        - Never show if wizard already completed in session
        - Check DB preference if user_id provided
        - Otherwise show for new users
    """
    # Check session state first (fastest)
    if st.session_state.get("wizard_completed", False):
        return False

    # Check if user has cards (don't show wizard if they do)
    if hasattr(st.session_state, 'storage'):
        cards = st.session_state.storage.get_all_cards()
        if len(cards) > 0:
            return False

    # Check DB preference if user_id provided
    if user_id:
        try:
            from ...core.database import get_cursor

            with get_cursor() as cursor:
                cursor.execute(
                    "SELECT onboarding_completed FROM user_preferences WHERE user_id = %s",
                    (user_id,)
                )
                result = cursor.fetchone()
                if result and result[0]:
                    return False
        except Exception:
            # If DB check fails, continue with default behavior
            pass

    # Default: show wizard for new users
    return True


def mark_wizard_completed(user_id: Optional[str] = None):
    """Mark the onboarding wizard as completed.

    Args:
        user_id: Current user's ID (optional).

    Saves completion state to:
        1. Session state (immediate)
        2. Database (persistent) if user_id provided
    """
    # Mark completed in session
    st.session_state.wizard_completed = True

    # Save to DB if user_id provided
    if user_id:
        try:
            from ...core.database import get_cursor

            with get_cursor() as cursor:
                # Use INSERT ... ON CONFLICT for upsert behavior
                cursor.execute(
                    """
                    INSERT INTO user_preferences (user_id, onboarding_completed)
                    VALUES (%s, TRUE)
                    ON CONFLICT (user_id)
                    DO UPDATE SET onboarding_completed = TRUE, updated_at = CURRENT_TIMESTAMP
                    """,
                    (user_id,)
                )
        except Exception as e:
            # Log error but don't fail - session state is already set
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to save wizard completion to DB: {e}")
