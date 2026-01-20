"""Form Field wrapper component.

Provides consistent styling and enhanced UX for form inputs,
including labels, help text, validation states, and accessibility.
"""

import streamlit as st
from dataclasses import dataclass
from typing import Optional, Any, Literal, List


@dataclass
class FormField:
    """Configuration for a form field wrapper.

    Attributes:
        key: Unique identifier for this field.
        label: Field label text.
        help_text: Optional help/hint text.
        required: Whether the field is required.
        error: Error message to display.
        success: Success message to display.
        prefix: Optional prefix text/icon.
        suffix: Optional suffix text/icon.
    """
    key: str
    label: str
    help_text: Optional[str] = None
    required: bool = False
    error: Optional[str] = None
    success: Optional[str] = None
    prefix: Optional[str] = None
    suffix: Optional[str] = None


@dataclass
class FieldGroup:
    """Configuration for a group of related fields.

    Attributes:
        key: Unique identifier for this group.
        label: Group label text.
        description: Optional group description.
        fields: List of field keys in this group.
        collapsible: Whether the group can be collapsed.
    """
    key: str
    label: str
    description: Optional[str] = None
    fields: Optional[List[str]] = None
    collapsible: bool = False


# CSS for form field styling
FORM_FIELD_CSS = """
<style>
/* Form Field Container */
.form-field {
    margin-bottom: 20px;
}

/* Label */
.field-label {
    display: flex;
    align-items: center;
    margin-bottom: 6px;
    font-size: 0.875rem;
    font-weight: 600;
    color: #212529;
}

.field-label-text {
    flex: 1;
}

.field-required {
    color: #dc3545;
    margin-left: 4px;
}

.field-optional {
    color: #6c757d;
    font-weight: 400;
    font-size: 0.8125rem;
    margin-left: 8px;
}

/* Help Text */
.field-help {
    font-size: 0.8125rem;
    color: #6c757d;
    margin-top: 4px;
    line-height: 1.4;
}

/* Input Container */
.field-input-container {
    position: relative;
    display: flex;
    align-items: stretch;
}

/* Prefix/Suffix */
.field-prefix,
.field-suffix {
    display: flex;
    align-items: center;
    padding: 0 12px;
    background: #f8f9fa;
    border: 1px solid #ced4da;
    color: #6c757d;
    font-size: 0.875rem;
}

.field-prefix {
    border-right: none;
    border-radius: 8px 0 0 8px;
}

.field-suffix {
    border-left: none;
    border-radius: 0 8px 8px 0;
}

/* States */
.form-field.has-error .field-input-container input,
.form-field.has-error .field-input-container select,
.form-field.has-error .field-input-container textarea {
    border-color: #dc3545;
    background-color: #fff8f8;
}

.form-field.has-success .field-input-container input,
.form-field.has-success .field-input-container select,
.form-field.has-success .field-input-container textarea {
    border-color: #28a745;
    background-color: #f8fff8;
}

/* Error/Success Messages */
.field-error {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.8125rem;
    color: #dc3545;
    margin-top: 6px;
}

.field-success {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.8125rem;
    color: #28a745;
    margin-top: 6px;
}

/* Field Group */
.field-group {
    background: #f8f9fa;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 24px;
}

.field-group-header {
    margin-bottom: 16px;
}

.field-group-label {
    font-size: 1rem;
    font-weight: 600;
    color: #212529;
    margin: 0 0 4px;
}

.field-group-description {
    font-size: 0.875rem;
    color: #6c757d;
}

.field-group-content {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

/* Inline Fields */
.fields-inline {
    display: flex;
    gap: 16px;
}

.fields-inline > .form-field {
    flex: 1;
    margin-bottom: 0;
}

/* Character Counter */
.field-counter {
    text-align: right;
    font-size: 0.75rem;
    color: #6c757d;
    margin-top: 4px;
}

.field-counter.near-limit {
    color: #ffc107;
}

.field-counter.at-limit {
    color: #dc3545;
}

/* Focus Styles (applied via JavaScript in real implementation) */
.form-field.focused .field-prefix,
.form-field.focused .field-suffix {
    border-color: #0066cc;
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
    .field-label {
        color: #f8f9fa;
    }

    .field-help {
        color: #adb5bd;
    }

    .field-prefix,
    .field-suffix {
        background: #2d2d2d;
        border-color: #404040;
        color: #adb5bd;
    }

    .field-group {
        background: #1a1a1a;
    }

    .field-group-label {
        color: #f8f9fa;
    }

    .form-field.has-error .field-input-container input,
    .form-field.has-error .field-input-container select,
    .form-field.has-error .field-input-container textarea {
        background-color: #2d1f1f;
    }

    .form-field.has-success .field-input-container input,
    .form-field.has-success .field-input-container select,
    .form-field.has-success .field-input-container textarea {
        background-color: #1f2d1f;
    }
}
</style>
"""


def inject_form_field_css():
    """Inject the form field CSS styles."""
    st.markdown(FORM_FIELD_CSS, unsafe_allow_html=True)


def render_form_field(
    config: Optional[FormField] = None,
    label: str = "",
    help_text: Optional[str] = None,
    required: bool = False,
    error: Optional[str] = None,
    success: Optional[str] = None,
    prefix: Optional[str] = None,
    suffix: Optional[str] = None,
    key: str = "field",
) -> None:
    """Render form field wrapper (label, help, etc.) before an input.

    Call this BEFORE rendering the actual Streamlit input widget.

    Args:
        config: Optional FormField configuration.
        label: Field label (if config not provided).
        help_text: Help text (if config not provided).
        required: Whether required (if config not provided).
        error: Error message (if config not provided).
        success: Success message (if config not provided).
        prefix: Prefix text (if config not provided).
        suffix: Suffix text (if config not provided).
        key: Unique key (if config not provided).

    Example:
        ```python
        render_form_field(
            label="Email Address",
            help_text="We'll never share your email",
            required=True,
        )
        email = st.text_input("Email", label_visibility="collapsed", key="email")

        # With validation
        error = validate_email(email)
        render_field_feedback(error=error)
        ```
    """
    inject_form_field_css()

    # Use config or individual params
    if config:
        key = config.key
        label = config.label
        help_text = config.help_text
        required = config.required
        error = config.error
        success = config.success
        prefix = config.prefix
        suffix = config.suffix

    # Determine state classes
    state_class = ""
    if error:
        state_class = "has-error"
    elif success:
        state_class = "has-success"

    # Build label HTML
    required_marker = '<span class="field-required">*</span>' if required else '<span class="field-optional">(optional)</span>'

    st.markdown(
        f"""
        <div class="form-field {state_class}">
            <label class="field-label">
                <span class="field-label-text">{label}</span>
                {required_marker if label else ''}
            </label>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_field_feedback(
    error: Optional[str] = None,
    success: Optional[str] = None,
    help_text: Optional[str] = None,
    char_count: Optional[int] = None,
    max_chars: Optional[int] = None,
) -> None:
    """Render feedback (error/success/help) after an input field.

    Call this AFTER rendering the actual Streamlit input widget.

    Args:
        error: Error message to display.
        success: Success message to display.
        help_text: Help text to display.
        char_count: Current character count.
        max_chars: Maximum allowed characters.

    Example:
        ```python
        description = st.text_area("Description", key="desc")
        render_field_feedback(
            error=None if len(description) > 0 else "Required",
            char_count=len(description),
            max_chars=500,
        )
        ```
    """
    inject_form_field_css()

    html_parts = []

    # Error message
    if error:
        html_parts.append(f'<div class="field-error">⚠ {error}</div>')

    # Success message
    if success:
        html_parts.append(f'<div class="field-success">✓ {success}</div>')

    # Help text (only show if no error/success)
    if help_text and not error and not success:
        html_parts.append(f'<div class="field-help">{help_text}</div>')

    # Character counter
    if char_count is not None and max_chars is not None:
        counter_class = ""
        if char_count >= max_chars:
            counter_class = "at-limit"
        elif char_count >= max_chars * 0.9:
            counter_class = "near-limit"

        html_parts.append(
            f'<div class="field-counter {counter_class}">{char_count}/{max_chars}</div>'
        )

    if html_parts:
        st.markdown("".join(html_parts), unsafe_allow_html=True)


def render_field_group(
    label: str,
    description: Optional[str] = None,
    key: str = "group",
) -> None:
    """Start a field group container.

    Use with a Streamlit container for grouping related fields.

    Args:
        label: Group label.
        description: Optional group description.
        key: Unique key.

    Example:
        ```python
        render_field_group("Personal Information", "Enter your details")
        with st.container():
            name = st.text_input("Name")
            email = st.text_input("Email")
        ```
    """
    inject_form_field_css()

    desc_html = f'<p class="field-group-description">{description}</p>' if description else ""

    st.markdown(
        f"""
        <div class="field-group">
            <div class="field-group-header">
                <h4 class="field-group-label">{label}</h4>
                {desc_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_currency_input(
    label: str,
    key: str,
    default: float = 0.0,
    help_text: Optional[str] = None,
    required: bool = False,
    currency_symbol: str = "$",
) -> float:
    """Render a currency input field with prefix.

    Args:
        label: Field label.
        key: Unique key.
        default: Default value.
        help_text: Optional help text.
        required: Whether required.
        currency_symbol: Currency symbol prefix.

    Returns:
        The entered currency value.

    Example:
        ```python
        amount = render_currency_input(
            label="Annual Fee",
            key="annual_fee",
            default=0.0,
            help_text="Enter 0 if no annual fee",
        )
        ```
    """
    render_form_field(label=label, help_text=help_text, required=required, prefix=currency_symbol)

    value = st.number_input(
        label,
        min_value=0.0,
        value=default,
        step=1.0,
        key=key,
        label_visibility="collapsed",
    )

    return value


def render_date_input(
    label: str,
    key: str,
    default: Any = None,
    help_text: Optional[str] = None,
    required: bool = False,
    min_value: Any = None,
    max_value: Any = None,
) -> Any:
    """Render a date input field.

    Args:
        label: Field label.
        key: Unique key.
        default: Default value.
        help_text: Optional help text.
        required: Whether required.
        min_value: Minimum date.
        max_value: Maximum date.

    Returns:
        The selected date.

    Example:
        ```python
        opened_date = render_date_input(
            label="Card Opened Date",
            key="opened_date",
            required=True,
        )
        ```
    """
    render_form_field(label=label, help_text=help_text, required=required)

    value = st.date_input(
        label,
        value=default,
        min_value=min_value,
        max_value=max_value,
        key=key,
        label_visibility="collapsed",
    )

    return value


def render_select_input(
    label: str,
    options: List[str],
    key: str,
    default: Optional[str] = None,
    help_text: Optional[str] = None,
    required: bool = False,
    placeholder: str = "Select an option",
) -> Optional[str]:
    """Render a select/dropdown input field.

    Args:
        label: Field label.
        options: List of options.
        key: Unique key.
        default: Default selected value.
        help_text: Optional help text.
        required: Whether required.
        placeholder: Placeholder text.

    Returns:
        The selected option.

    Example:
        ```python
        issuer = render_select_input(
            label="Card Issuer",
            options=["Chase", "Amex", "Citi", "Capital One"],
            key="issuer",
            required=True,
        )
        ```
    """
    render_form_field(label=label, help_text=help_text, required=required)

    # Add placeholder option
    options_with_placeholder = [placeholder] + list(options)
    default_index = 0 if default is None else options_with_placeholder.index(default)

    value = st.selectbox(
        label,
        options=options_with_placeholder,
        index=default_index,
        key=key,
        label_visibility="collapsed",
    )

    return None if value == placeholder else value


def render_text_input(
    label: str,
    key: str,
    default: str = "",
    help_text: Optional[str] = None,
    required: bool = False,
    placeholder: Optional[str] = None,
    max_chars: Optional[int] = None,
    multiline: bool = False,
) -> str:
    """Render a text input field with all enhancements.

    Args:
        label: Field label.
        key: Unique key.
        default: Default value.
        help_text: Optional help text.
        required: Whether required.
        placeholder: Placeholder text.
        max_chars: Maximum characters allowed.
        multiline: Whether to use text area.

    Returns:
        The entered text.

    Example:
        ```python
        nickname = render_text_input(
            label="Card Nickname",
            key="nickname",
            placeholder="e.g., P2's Card",
            max_chars=50,
        )
        ```
    """
    render_form_field(label=label, required=required)

    if multiline:
        value = st.text_area(
            label,
            value=default,
            placeholder=placeholder,
            max_chars=max_chars,
            key=key,
            label_visibility="collapsed",
        )
    else:
        value = st.text_input(
            label,
            value=default,
            placeholder=placeholder,
            max_chars=max_chars,
            key=key,
            label_visibility="collapsed",
        )

    # Render feedback
    if max_chars:
        render_field_feedback(
            help_text=help_text,
            char_count=len(value),
            max_chars=max_chars,
        )
    elif help_text:
        render_field_feedback(help_text=help_text)

    return value
