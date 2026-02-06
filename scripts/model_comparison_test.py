#!/usr/bin/env python3
"""
Model Comparison Test: Gemini 1.5 Flash vs Claude Haiku 3.5

Tests both models on ChurnPilot's three AI extraction tasks:
1. URL card extraction
2. Text extraction  
3. Spreadsheet import

Measures accuracy against known ground truth.
"""

import os
import json
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Load env
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

# Test data with known ground truth
GROUND_TRUTH = {
    "chase_sapphire_preferred": {
        "name": "Chase Sapphire Preferred",
        "issuer": "Chase",
        "annual_fee": 95,
        "signup_bonus": {
            "points_or_cash": "60,000 points",
            "spend_requirement": 4000,
            "time_period_days": 90
        }
    },
    "amex_gold": {
        "name": "American Express Gold Card",
        "issuer": "American Express",
        "annual_fee": 250,
        "signup_bonus": {
            "points_or_cash": "60,000 points",
            "spend_requirement": 6000,
            "time_period_days": 180
        },
        "credits": [
            {"name": "Uber Credit", "amount": 10, "frequency": "monthly"},
            {"name": "Dining Credit", "amount": 10, "frequency": "monthly"},
        ]
    }
}

# Sample text for extraction (simulating pasted card info)
SAMPLE_TEXT = """
Chase Sapphire Preferred® Card

Annual Fee: $95
Welcome Offer: Earn 60,000 bonus points after you spend $4,000 on purchases 
in the first 3 months from account opening.

Key Benefits:
- 3X points on dining
- 3X points on streaming services  
- 2X points on travel
- 1X points on everything else

Points are worth 25% more when redeemed for travel through Chase Ultimate Rewards.
"""

SAMPLE_CSV = """Card Name,Annual Fee,Status,Opened Date,Signup Bonus,Spend Requirement,SUB Period
Chase Sapphire Preferred,$95,Active,2024-01-15,60000 points,$4000,3 months
Amex Gold,$250,Active,2024-03-01,60000 MR,$6000,6 months
Citi Double Cash,$0,Active,2023-06-10,,$,"""

# System prompt for extraction (same as production)
SYSTEM_PROMPT = """You are a Credit Card Data Analyst. Extract structured information from credit card content.
Always respond with valid JSON only. No explanations, no markdown formatting."""

EXTRACTION_PROMPT = """Extract card details from this content. Return JSON with:
- name: Full card name
- issuer: Card issuer (Chase, Amex, Citi, etc.)
- annual_fee: Annual fee as integer (0 if none)
- signup_bonus: Object with points_or_cash, spend_requirement, time_period_days (or null)
- credits: Array of recurring credits with name, amount, frequency (or empty array)

Content:
{content}

Return ONLY valid JSON:"""

CSV_PROMPT = """Parse this spreadsheet into a JSON array of cards. For each card extract:
- card_name, issuer, annual_fee, opened_date, sub_reward, sub_spend_requirement, sub_time_period_days

Spreadsheet:
{content}

Return ONLY a JSON array:"""


@dataclass
class TestResult:
    model: str
    task: str
    success: bool
    latency_ms: int
    accuracy_score: float  # 0-100
    extracted_data: dict
    errors: list[str]


def extract_with_gemini(prompt: str, system: str = "") -> tuple[str, int]:
    """Call Gemini 2.0 Flash API (free tier)."""
    from google import genai
    
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not set")
    
    client = genai.Client(api_key=api_key)
    
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    
    start = time.time()
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=full_prompt
    )
    latency = int((time.time() - start) * 1000)
    
    return response.text, latency


def extract_with_claude_haiku(prompt: str, system: str = "") -> tuple[str, int]:
    """Call Claude Haiku 3.5 API."""
    from anthropic import Anthropic
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    
    client = Anthropic(api_key=api_key)
    
    start = time.time()
    response = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=2048,
        system=system if system else "You are a helpful assistant.",
        messages=[{"role": "user", "content": prompt}]
    )
    latency = int((time.time() - start) * 1000)
    
    return response.content[0].text, latency


def parse_json_response(text: str) -> dict:
    """Extract JSON from model response."""
    import re
    
    # Try to find JSON in response
    text = text.strip()
    
    # Remove markdown code blocks
    if "```json" in text:
        match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            text = match.group(1)
    elif "```" in text:
        match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            text = match.group(1)
    
    # Try to find JSON object or array
    if not text.startswith('{') and not text.startswith('['):
        match = re.search(r'[\[{].*[\]}]', text, re.DOTALL)
        if match:
            text = match.group(0)
    
    return json.loads(text)


def calculate_accuracy(extracted: dict, ground_truth: dict) -> tuple[float, list[str]]:
    """Calculate accuracy score (0-100) and list of errors."""
    errors = []
    correct = 0
    total = 0
    
    # Check name (fuzzy match)
    total += 1
    if ground_truth.get("name", "").lower() in extracted.get("name", "").lower() or \
       extracted.get("name", "").lower() in ground_truth.get("name", "").lower():
        correct += 1
    else:
        errors.append(f"Name mismatch: expected '{ground_truth.get('name')}', got '{extracted.get('name')}'")
    
    # Check issuer
    total += 1
    if extracted.get("issuer", "").lower() == ground_truth.get("issuer", "").lower():
        correct += 1
    else:
        errors.append(f"Issuer mismatch: expected '{ground_truth.get('issuer')}', got '{extracted.get('issuer')}'")
    
    # Check annual fee
    total += 1
    try:
        extracted_fee = int(extracted.get("annual_fee", -1))
        if extracted_fee == ground_truth.get("annual_fee"):
            correct += 1
        else:
            errors.append(f"Annual fee mismatch: expected {ground_truth.get('annual_fee')}, got {extracted_fee}")
    except (ValueError, TypeError):
        errors.append(f"Annual fee not a number: {extracted.get('annual_fee')}")
    
    # Check signup bonus (if expected)
    if ground_truth.get("signup_bonus"):
        gt_sub = ground_truth["signup_bonus"]
        ex_sub = extracted.get("signup_bonus") or {}
        
        # Check spend requirement
        total += 1
        try:
            ex_spend = int(ex_sub.get("spend_requirement", 0))
            if ex_spend == gt_sub.get("spend_requirement"):
                correct += 1
            else:
                errors.append(f"SUB spend mismatch: expected {gt_sub.get('spend_requirement')}, got {ex_spend}")
        except (ValueError, TypeError):
            errors.append(f"SUB spend not a number")
        
        # Check time period
        total += 1
        try:
            ex_days = int(ex_sub.get("time_period_days", 0))
            if ex_days == gt_sub.get("time_period_days"):
                correct += 1
            else:
                errors.append(f"SUB days mismatch: expected {gt_sub.get('time_period_days')}, got {ex_days}")
        except (ValueError, TypeError):
            errors.append(f"SUB days not a number")
    
    return (correct / total * 100) if total > 0 else 0, errors


def test_text_extraction(model_fn, model_name: str) -> TestResult:
    """Test text extraction capability."""
    prompt = EXTRACTION_PROMPT.format(content=SAMPLE_TEXT)
    
    try:
        response, latency = model_fn(prompt, SYSTEM_PROMPT)
        extracted = parse_json_response(response)
        accuracy, errors = calculate_accuracy(extracted, GROUND_TRUTH["chase_sapphire_preferred"])
        
        return TestResult(
            model=model_name,
            task="Text Extraction",
            success=True,
            latency_ms=latency,
            accuracy_score=accuracy,
            extracted_data=extracted,
            errors=errors
        )
    except Exception as e:
        return TestResult(
            model=model_name,
            task="Text Extraction",
            success=False,
            latency_ms=0,
            accuracy_score=0,
            extracted_data={},
            errors=[str(e)]
        )


def test_csv_parsing(model_fn, model_name: str) -> TestResult:
    """Test CSV/spreadsheet parsing capability."""
    prompt = CSV_PROMPT.format(content=SAMPLE_CSV)
    
    try:
        response, latency = model_fn(prompt, SYSTEM_PROMPT)
        extracted = parse_json_response(response)
        
        # Check if we got an array with expected cards
        errors = []
        correct = 0
        total = 3  # We have 3 cards in the CSV
        
        if isinstance(extracted, list):
            if len(extracted) >= 2:
                correct += 1  # Got multiple cards
            
            # Check first card (CSP)
            if any("sapphire" in str(c.get("card_name", "")).lower() for c in extracted):
                correct += 1
            else:
                errors.append("Missing Chase Sapphire Preferred")
            
            # Check second card (Amex Gold)  
            if any("gold" in str(c.get("card_name", "")).lower() for c in extracted):
                correct += 1
            else:
                errors.append("Missing Amex Gold")
        else:
            errors.append("Response was not a JSON array")
        
        accuracy = (correct / total * 100) if total > 0 else 0
        
        return TestResult(
            model=model_name,
            task="CSV Parsing",
            success=True,
            latency_ms=latency,
            accuracy_score=accuracy,
            extracted_data=extracted if isinstance(extracted, list) else [extracted],
            errors=errors
        )
    except Exception as e:
        return TestResult(
            model=model_name,
            task="CSV Parsing",
            success=False,
            latency_ms=0,
            accuracy_score=0,
            extracted_data={},
            errors=[str(e)]
        )


def test_url_extraction(model_fn, model_name: str) -> TestResult:
    """Test URL extraction (using realistic webpage content)."""
    # Simulated webpage content (like what Jina Reader would return)
    webpage_content = """
    # Chase Sapphire Preferred® Card
    
    ## Card Details
    - Annual Fee: $95
    - Welcome Bonus: Earn 60,000 bonus points after you spend $4,000 on purchases in the first 3 months
    
    ## Rewards
    - 5X on travel purchased through Chase Travel
    - 3X on dining, including eligible delivery services
    - 3X on select streaming services
    - 2X on all other travel purchases
    - 1X on all other purchases
    
    ## Benefits
    - No foreign transaction fees
    - Trip cancellation/interruption insurance
    - Auto rental collision damage waiver
    - 25% more value when you redeem for travel through Chase
    
    ## Issuer: Chase Bank
    """
    
    try:
        prompt = EXTRACTION_PROMPT.format(content=webpage_content)
        response, latency = model_fn(prompt, SYSTEM_PROMPT)
        extracted = parse_json_response(response)
        accuracy, errors = calculate_accuracy(extracted, GROUND_TRUTH["chase_sapphire_preferred"])
        
        return TestResult(
            model=model_name,
            task="URL Extraction",
            success=True,
            latency_ms=latency,
            accuracy_score=accuracy,
            extracted_data=extracted,
            errors=errors
        )
    except Exception as e:
        return TestResult(
            model=model_name,
            task="URL Extraction",
            success=False,
            latency_ms=0,
            accuracy_score=0,
            extracted_data={},
            errors=[str(e)]
        )


def print_result(result: TestResult):
    """Pretty print a test result."""
    status = "✅" if result.success and result.accuracy_score >= 80 else "⚠️" if result.success else "❌"
    print(f"\n{status} {result.model} - {result.task}")
    print(f"   Latency: {result.latency_ms}ms")
    print(f"   Accuracy: {result.accuracy_score:.0f}%")
    if result.errors:
        print(f"   Issues: {', '.join(result.errors[:3])}")


def main():
    print("=" * 60)
    print("MODEL COMPARISON: Gemini 1.5 Flash vs Claude Haiku 3.5")
    print("=" * 60)
    
    results = []
    
    # Test Gemini
    print("\n🔷 Testing Gemini 1.5 Flash...")
    try:
        results.append(test_text_extraction(extract_with_gemini, "Gemini 1.5 Flash"))
        print_result(results[-1])
        
        results.append(test_csv_parsing(extract_with_gemini, "Gemini 1.5 Flash"))
        print_result(results[-1])
        
        results.append(test_url_extraction(extract_with_gemini, "Gemini 1.5 Flash"))
        print_result(results[-1])
    except Exception as e:
        print(f"   ❌ Gemini tests failed: {e}")
    
    # Test Claude Haiku
    print("\n🟠 Testing Claude Haiku 3.5...")
    try:
        results.append(test_text_extraction(extract_with_claude_haiku, "Claude Haiku 3.5"))
        print_result(results[-1])
        
        results.append(test_csv_parsing(extract_with_claude_haiku, "Claude Haiku 3.5"))
        print_result(results[-1])
        
        results.append(test_url_extraction(extract_with_claude_haiku, "Claude Haiku 3.5"))
        print_result(results[-1])
    except Exception as e:
        print(f"   ❌ Claude tests failed: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    gemini_results = [r for r in results if "Gemini" in r.model]
    haiku_results = [r for r in results if "Haiku" in r.model]
    
    if gemini_results:
        avg_gemini = sum(r.accuracy_score for r in gemini_results) / len(gemini_results)
        avg_gemini_latency = sum(r.latency_ms for r in gemini_results) / len(gemini_results)
        print(f"\nGemini 1.5 Flash:")
        print(f"  Average Accuracy: {avg_gemini:.0f}%")
        print(f"  Average Latency: {avg_gemini_latency:.0f}ms")
        print(f"  Cost: FREE (60 req/min)")
    
    if haiku_results:
        avg_haiku = sum(r.accuracy_score for r in haiku_results) / len(haiku_results)
        avg_haiku_latency = sum(r.latency_ms for r in haiku_results) / len(haiku_results)
        print(f"\nClaude Haiku 3.5:")
        print(f"  Average Accuracy: {avg_haiku:.0f}%")
        print(f"  Average Latency: {avg_haiku_latency:.0f}ms")
        print(f"  Cost: $0.25/$1.25 per 1M tokens")
    
    print("\n" + "=" * 60)
    
    # Recommendation
    if gemini_results and haiku_results:
        if avg_gemini >= avg_haiku - 10:  # Within 10% accuracy
            print("📊 RECOMMENDATION: Use Gemini 1.5 Flash")
            print("   Similar accuracy, FREE, good for free tier users")
        else:
            print("📊 RECOMMENDATION: Use Claude Haiku 3.5")
            print(f"   Better accuracy (+{avg_haiku - avg_gemini:.0f}%), worth the cost")


if __name__ == "__main__":
    main()
