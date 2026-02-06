"""Unified extraction pipeline: URL -> Jina Reader -> Claude API.

This module provides a clean, AI-driven extraction pipeline that:
1. Fetches clean Markdown from any URL via Jina Reader
2. Extracts structured card data using Claude as semantic analyzer
3. Returns validated Pydantic models

No brittle HTML parsing - just clean data in, structured data out.
"""

import json
import os
import re
from pathlib import Path
from uuid import UUID
from typing import Optional

from dotenv import load_dotenv

from .models import CardData, SignupBonus, Credit
from .exceptions import ExtractionError
from .fetcher import fetch_card_page
from .enrichment import enrich_card_data, get_enrichment_summary
from .ai_rate_limit import check_extraction_limit, record_extraction

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / ".env")

# AI model selection (configurable via env var)
# Options: "gemini" (free, default), "claude" (paid but higher quality)
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# System prompt - Claude acts as a Credit Card Data Analyst
SYSTEM_PROMPT = """You are a Credit Card Data Analyst specializing in extracting structured information from credit card marketing materials and reviews.

Your job is to:
1. Ignore marketing fluff, ads, and promotional language
2. Extract only factual, quantifiable data about the credit card
3. Be precise with numbers (fees, points, spend requirements)
4. Convert time periods to days (3 months = 90 days)

Always respond with valid JSON only. No explanations, no markdown formatting."""

# User prompt template for extraction
EXTRACTION_PROMPT = """Analyze the following credit card information and extract structured data.

Extract these fields:
- name: Full card name (e.g., "The Platinum Card from American Express")
- issuer: Card issuer (American Express, Chase, Citi, Capital One, Bank of America, Discover, Wells Fargo, US Bank, Barclays, or Other)
- annual_fee: Annual fee in dollars as integer (0 if no fee, -1 if unknown)
- signup_bonus: Current sign-up bonus offer (null if none mentioned)
  - points_or_cash: The bonus value with unit (e.g., "80,000 points", "$200 cash back")
  - spend_requirement: Required spend amount in dollars
  - time_period_days: Days to meet requirement (convert months: 3 months = 90 days)
- credits: List of recurring credits/benefits with dollar value
  - name: Credit name (e.g., "Uber Credit", "Airline Fee Credit")
  - amount: Dollar amount per occurrence
  - frequency: "monthly", "annual", "semi-annual", or "quarterly"
  - notes: Any conditions or limitations (optional)

Return JSON matching this exact schema:
{{
  "name": "string",
  "issuer": "string",
  "annual_fee": number,
  "signup_bonus": {{
    "points_or_cash": "string",
    "spend_requirement": number,
    "time_period_days": number
  }} | null,
  "credits": [
    {{
      "name": "string",
      "amount": number,
      "frequency": "string",
      "notes": "string or null"
    }}
  ]
}}

Content to analyze:
---
{content}
---

Respond with JSON only:"""


def extract_from_url(url: str, timeout: int = 60, user_id: Optional[UUID] = None) -> CardData:
    """Extract structured card data from a URL using Jina + Claude pipeline.

    This is the main entry point for the extraction pipeline:
    1. Rate limit check (if user_id provided)
    2. URL -> Jina Reader (fetches clean Markdown via fetcher module)
    3. Markdown -> Claude (extracts structured data)
    4. CardData -> Auto-enrichment (adds missing credits from library)
    5. JSON -> CardData (validates and returns)

    Args:
        url: URL to extract card data from (must be from allowed domains).
        timeout: HTTP request timeout in seconds.
        user_id: User UUID for rate limiting. If None, rate limiting is skipped.

    Returns:
        CardData object with extracted and auto-enriched fields.

    Raises:
        FetchError: If URL fetch fails or domain not allowed.
        ExtractionError: If AI extraction fails or rate limit exceeded.
    """
    # Step 0: Check rate limit (if user_id provided)
    if user_id:
        can_extract, remaining, message = check_extraction_limit(user_id)
        if not can_extract:
            raise ExtractionError(message)
    
    # Step 1: Fetch clean Markdown via Jina Reader (with domain validation)
    markdown_content = fetch_card_page(url, timeout)

    # Step 2: Extract structured data via AI (Gemini default, Claude fallback)
    card_data = _extract_with_ai(markdown_content)
    
    # Step 2.5: Record extraction (if user_id provided)
    if user_id:
        record_extraction(user_id)

    # Step 3: Auto-enrich with library data (adds missing credits)
    enriched_data, match_result = enrich_card_data(card_data, min_confidence=0.7)

    # Log enrichment for debugging
    if match_result.template_id:
        summary = get_enrichment_summary(card_data, enriched_data, match_result)
        print(f"[Enrichment] {summary}")

    return enriched_data


def _extract_with_ai(content: str, max_content_chars: int = 15000) -> CardData:
    """Extract structured card data using the configured AI provider.
    
    Uses Gemini by default (free tier), falls back to Claude if Gemini fails.
    
    Args:
        content: Clean Markdown content from Jina Reader.
        max_content_chars: Maximum content length to send.
        
    Returns:
        CardData object with extracted fields.
        
    Raises:
        ExtractionError: If extraction fails.
    """
    provider = AI_PROVIDER.lower()
    
    if provider == "gemini":
        try:
            return _extract_with_gemini(content, max_content_chars)
        except ExtractionError as e:
            # If Gemini fails (quota, etc.), fall back to Claude
            import logging
            logging.warning(f"Gemini extraction failed: {e}, falling back to Claude")
            return _extract_with_claude(content, max_content_chars)
    else:
        return _extract_with_claude(content, max_content_chars)


def _extract_with_gemini(content: str, max_content_chars: int = 15000) -> CardData:
    """Extract structured card data from Markdown using Gemini.
    
    Args:
        content: Clean Markdown content from Jina Reader.
        max_content_chars: Maximum content length to send.
        
    Returns:
        CardData object with extracted fields.
        
    Raises:
        ExtractionError: If extraction fails.
    """
    # Get API key
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
        except:
            pass
    
    if not api_key:
        raise ExtractionError("GEMINI_API_KEY not found in environment or Streamlit secrets")
    
    # Truncate content if too long
    if len(content) > max_content_chars:
        content = content[:max_content_chars] + "\n\n[Content truncated...]"
    
    # Lazy import Google GenAI SDK
    try:
        from google import genai
    except ImportError:
        raise ExtractionError("google-genai package not installed")
    
    client = genai.Client(api_key=api_key)
    
    # Combine system prompt and user prompt for Gemini
    full_prompt = f"{SYSTEM_PROMPT}\n\n{EXTRACTION_PROMPT.format(content=content)}"
    
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=full_prompt
        )
        
        response_text = response.text.strip()
        
        # Extract JSON from response
        json_str = _extract_json_from_response(response_text)
        data = json.loads(json_str)
        
        return _parse_to_card_data(data)
        
    except json.JSONDecodeError as e:
        raise ExtractionError("Unable to understand the card information. The page might not contain clear card details.")
    except Exception as e:
        import logging
        logging.error(f"Gemini extraction failed: {e}")
        # Re-raise as ExtractionError so caller can handle fallback
        raise ExtractionError(f"Gemini extraction failed: {str(e)[:100]}")


def _extract_with_claude(content: str, max_content_chars: int = 15000) -> CardData:
    """Extract structured card data from Markdown using Claude.

    Args:
        content: Clean Markdown content from Jina Reader.
        max_content_chars: Maximum content length to send to Claude.

    Returns:
        CardData object with extracted fields.

    Raises:
        ExtractionError: If extraction fails.
    """
    # Get API key (try env var first, then Streamlit secrets as fallback)
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get("ANTHROPIC_API_KEY")
        except:
            pass

    if not api_key:
        raise ExtractionError("ANTHROPIC_API_KEY not found in environment or Streamlit secrets")

    # Truncate content if too long (keep beginning which usually has key info)
    if len(content) > max_content_chars:
        content = content[:max_content_chars] + "\n\n[Content truncated...]"

    # Lazy import Anthropic SDK (saves ~7s on app startup)
    from anthropic import Anthropic
    client = Anthropic(api_key=api_key)

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": EXTRACTION_PROMPT.format(content=content),
                }
            ],
        )

        # Parse response
        response_text = response.content[0].text.strip()

        # Extract JSON from response (handles markdown blocks, prose, etc.)
        json_str = _extract_json_from_response(response_text)

        data = json.loads(json_str)

        return _parse_to_card_data(data)

    except json.JSONDecodeError as e:
        raise ExtractionError("Unable to understand the card information. The page might not contain clear card details. Try a different source or use manual entry.")
    except Exception as e:
        # Log technical details but show user-friendly message
        import logging
        logging.error(f"Extraction failed: {e}")
        raise ExtractionError("Unable to extract card information. Please try again or enter details manually.")


def _extract_json_from_response(response_text: str) -> str:
    """Extract JSON object from Claude's response.

    Handles various response formats:
    - Raw JSON
    - JSON in markdown code blocks (```json ... ```)
    - JSON mixed with prose text

    Args:
        response_text: Raw response from Claude.

    Returns:
        Clean JSON string ready for parsing.

    Raises:
        ExtractionError: If no valid JSON found.
    """
    text = response_text.strip()

    # Method 1: Try to extract from markdown code blocks
    # Match ```json ... ``` or ``` ... ```
    code_block_pattern = r"```(?:json)?\s*(\{[\s\S]*?\})\s*```"
    match = re.search(code_block_pattern, text)
    if match:
        return match.group(1).strip()

    # Method 2: Find the outermost JSON object using brace matching
    # This handles cases where there's text before/after the JSON
    start_idx = text.find("{")
    if start_idx == -1:
        raise ExtractionError("No JSON object found in response (missing opening brace)")

    # Find the matching closing brace
    brace_count = 0
    end_idx = -1
    in_string = False
    escape_next = False

    for i, char in enumerate(text[start_idx:], start=start_idx):
        if escape_next:
            escape_next = False
            continue

        if char == "\\":
            escape_next = True
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            continue

        if in_string:
            continue

        if char == "{":
            brace_count += 1
        elif char == "}":
            brace_count -= 1
            if brace_count == 0:
                end_idx = i + 1
                break

    if end_idx == -1:
        raise ExtractionError("No valid JSON object found (unmatched braces)")

    return text[start_idx:end_idx]


def _parse_to_card_data(data: dict) -> CardData:
    """Parse JSON response into CardData model.

    Args:
        data: Parsed JSON from Claude.

    Returns:
        Validated CardData object.
    """
    # Parse signup bonus
    signup_bonus = None
    if data.get("signup_bonus"):
        sub = data["signup_bonus"]
        signup_bonus = SignupBonus(
            points_or_cash=sub.get("points_or_cash", ""),
            spend_requirement=sub.get("spend_requirement", 0),
            time_period_days=sub.get("time_period_days", 90),
        )

    # Parse credits
    credits = []
    for c in data.get("credits", []):
        credits.append(
            Credit(
                name=c.get("name", "Unknown Credit"),
                amount=c.get("amount", 0),
                frequency=c.get("frequency", "annual"),
                notes=c.get("notes"),
            )
        )

    return CardData(
        name=data.get("name", "Unknown Card"),
        issuer=data.get("issuer", "Unknown"),
        annual_fee=data.get("annual_fee", 0),
        signup_bonus=signup_bonus,
        credits=credits,
    )


def extract_from_text(text: str, user_id: Optional[UUID] = None) -> CardData:
    """Extract structured card data from raw text using Claude.

    Use this when you already have the content (e.g., pasted text).

    Args:
        text: Raw text content to analyze.
        user_id: User UUID for rate limiting. If None, rate limiting is skipped.

    Returns:
        CardData object with extracted and auto-enriched fields.

    Raises:
        ExtractionError: If extraction fails or rate limit exceeded.
    """
    if not text or not text.strip():
        raise ExtractionError("Empty text provided")

    # Check rate limit (if user_id provided)
    if user_id:
        can_extract, remaining, message = check_extraction_limit(user_id)
        if not can_extract:
            raise ExtractionError(message)

    # Extract data via AI (Gemini default, Claude fallback)
    card_data = _extract_with_ai(text)
    
    # Record extraction (if user_id provided)
    if user_id:
        record_extraction(user_id)

    # Auto-enrich with library data (adds missing credits)
    enriched_data, match_result = enrich_card_data(card_data, min_confidence=0.7)

    # Log enrichment for debugging
    if match_result.template_id:
        summary = get_enrichment_summary(card_data, enriched_data, match_result)
        print(f"[Enrichment] {summary}")

    return enriched_data
