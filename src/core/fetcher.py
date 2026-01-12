"""URL fetcher to scrape card terms from web pages.

Uses Jina Reader API (r.jina.ai) to fetch clean Markdown from any URL,
including JavaScript-rendered pages. No browser installation required.
"""

import re
from urllib.parse import urlparse

import requests

from .exceptions import FetchError

# Jina Reader API endpoint - converts any URL to clean Markdown
JINA_READER_PREFIX = "https://r.jina.ai/"

# Common card issuer domains
ALLOWED_DOMAINS = [
    "americanexpress.com",
    "chase.com",
    "citi.com",
    "capitalone.com",
    "discover.com",
    "bankofamerica.com",
    "wellsfargo.com",
    "usbank.com",
    "barclays.com",
    # Review sites
    "doctorofcredit.com",
    "thepointsguy.com",
    "nerdwallet.com",
    "creditcards.com",
    "uscreditcardguide.com",
]

# Request headers for Jina Reader
HEADERS = {
    "Accept": "text/plain",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

# Default timeout (Jina can be slow on complex pages)
DEFAULT_TIMEOUT = 60


def fetch_card_page(url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    """Fetch and extract text content from a card terms URL.

    Uses Jina Reader API to handle JavaScript-rendered pages and
    return clean Markdown content.

    Args:
        url: URL to fetch (must be from allowed domains).
        timeout: Request timeout in seconds.

    Returns:
        Extracted text/Markdown content from the page.

    Raises:
        FetchError: If URL is invalid, domain not allowed, or fetch fails.
    """
    # Validate URL
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise FetchError("Invalid URL format")
    except Exception as e:
        raise FetchError(f"Invalid URL: {e}")

    # Check domain is allowed
    domain = parsed.netloc.lower().replace("www.", "")

    if not any(allowed in domain for allowed in ALLOWED_DOMAINS):
        raise FetchError(
            f"Domain '{domain}' not in allowed list. "
            f"Supported: {', '.join(ALLOWED_DOMAINS[:5])}..."
        )

    # Use Jina Reader to fetch clean Markdown
    return _fetch_with_jina(url, timeout)


def _fetch_with_jina(url: str, timeout: int) -> str:
    """Fetch page using Jina Reader API.

    Jina Reader renders JavaScript and returns clean Markdown,
    which is ideal for LLM processing.

    Args:
        url: URL to fetch.
        timeout: Request timeout in seconds.

    Returns:
        Clean Markdown content.

    Raises:
        FetchError: If fetch fails.
    """
    jina_url = f"{JINA_READER_PREFIX}{url}"

    try:
        response = requests.get(jina_url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()

        content = response.text

        # Jina returns Markdown - clean it up a bit
        content = _clean_markdown(content)

        if len(content) < 100:
            raise FetchError("Page returned minimal content - it may require login")

        return content

    except requests.Timeout:
        raise FetchError("Request timed out - try again later")
    except requests.RequestException as e:
        raise FetchError(f"Failed to fetch URL: {e}")


def _clean_markdown(content: str) -> str:
    """Clean up Markdown content from Jina Reader.

    Args:
        content: Raw Markdown from Jina Reader.

    Returns:
        Cleaned Markdown content.
    """
    # Remove excessive blank lines
    content = re.sub(r"\n{3,}", "\n\n", content)

    # Remove image markdown (we don't need images)
    content = re.sub(r"!\[.*?\]\(.*?\)", "", content)

    # Remove excessive whitespace
    content = content.strip()

    return content


def get_allowed_domains() -> list[str]:
    """Return list of allowed domains for display.

    Returns:
        List of allowed domain names.
    """
    return ALLOWED_DOMAINS.copy()
