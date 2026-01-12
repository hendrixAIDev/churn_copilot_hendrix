"""Text preprocessor to clean and filter card terms before AI extraction."""

import re

# Patterns to remove (case-insensitive)
# Note: Be careful with .* - it's greedy and can match too much
BOILERPLATE_PATTERNS = [
    # Legal disclaimers (match to end of line only)
    r"(?i)^by (applying|using|opening).*you (agree|acknowledge|consent).*$",
    r"(?i)^terms and conditions (apply|may apply|subject to).*$",
    r"(?i)^please read (this|these|the following) (agreement|terms).*$",

    # Privacy / Legal footer lines
    r"(?i)^privacy (policy|notice|statement).*$",
    r"(?i)^member fdic.*$",
    r"(?i)^equal (housing|opportunity) lender.*$",
    r"(?i)^©\s*\d{4}.*$",

    # Navigation artifacts (exact matches)
    r"(?i)^back to top$",
    r"(?i)^skip to (main |)content$",
    r"(?i)^table of contents$",
]

# Sections to prioritize (keep these even if near limit)
PRIORITY_KEYWORDS = [
    "annual fee",
    "welcome offer",
    "sign-up bonus",
    "signup bonus",
    "bonus points",
    "bonus miles",
    "cash back",
    "spend requirement",
    "credit",
    "benefit",
    "perk",
    "reward",
    "membership",
    "lounge",
    "global entry",
    "tsa precheck",
]


def preprocess_text(text: str, max_chars: int = 8000) -> str:
    """Clean and filter text before sending to AI extraction.

    Args:
        text: Raw pasted text from user.
        max_chars: Maximum characters to return.

    Returns:
        Cleaned text with boilerplate removed, under max_chars limit.
    """
    if not text:
        return ""

    cleaned = text

    # Normalize whitespace (but preserve paragraph breaks)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)  # Multiple spaces/tabs -> single space
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)  # 3+ newlines -> 2 newlines
    cleaned = re.sub(r"^\s+", "", cleaned, flags=re.MULTILINE)  # Leading whitespace per line

    # Remove boilerplate patterns (MULTILINE so ^ and $ match line boundaries)
    for pattern in BOILERPLATE_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.MULTILINE)

    # Clean up any leftover empty lines from removals
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = cleaned.strip()

    # If still over limit, use smart truncation
    if len(cleaned) > max_chars:
        cleaned = _smart_truncate(cleaned, max_chars)

    return cleaned


def _smart_truncate(text: str, max_chars: int) -> str:
    """Truncate text while preserving priority content.

    Args:
        text: Text to truncate.
        max_chars: Maximum characters.

    Returns:
        Truncated text prioritizing important sections.
    """
    paragraphs = text.split("\n\n")

    # Score paragraphs by priority keyword presence
    scored = []
    for para in paragraphs:
        para_lower = para.lower()
        score = sum(1 for kw in PRIORITY_KEYWORDS if kw in para_lower)
        # Boost paragraphs with dollar amounts (likely fees/credits)
        if re.search(r"\$\d+", para):
            score += 2
        scored.append((score, para))

    # Sort by score (highest first), then rebuild
    scored.sort(key=lambda x: -x[0])

    result = []
    current_len = 0

    for score, para in scored:
        para_len = len(para) + 2  # +2 for \n\n separator
        if current_len + para_len <= max_chars:
            result.append(para)
            current_len += para_len

    return "\n\n".join(result)


def get_char_reduction(original: str, processed: str) -> dict:
    """Get stats on how much text was reduced.

    Args:
        original: Original text.
        processed: Processed text.

    Returns:
        Dict with original_chars, processed_chars, reduction_percent.
    """
    orig_len = len(original)
    proc_len = len(processed)
    reduction = ((orig_len - proc_len) / orig_len * 100) if orig_len > 0 else 0

    return {
        "original_chars": orig_len,
        "processed_chars": proc_len,
        "reduction_percent": round(reduction, 1),
    }
