"""Test AI extraction rate limiting."""

from uuid import uuid4
from src.core.ai_rate_limit import (
    check_extraction_limit,
    record_extraction,
    get_extraction_count,
    FREE_TIER_MONTHLY_LIMIT,
)

def test_rate_limiting():
    """Test that rate limiting works correctly."""
    # Use a test user ID
    test_user_id = uuid4()
    
    print(f"Testing AI extraction rate limiting...")
    print(f"Free tier limit: {FREE_TIER_MONTHLY_LIMIT} extractions/month\n")
    
    # Initial check - should have all extractions available
    can_extract, remaining, message = check_extraction_limit(test_user_id)
    assert can_extract, "Should be able to extract initially"
    assert remaining == FREE_TIER_MONTHLY_LIMIT, f"Should have {FREE_TIER_MONTHLY_LIMIT} remaining"
    print(f"✓ Initial state: {message}")
    
    # Use up all extractions
    for i in range(FREE_TIER_MONTHLY_LIMIT):
        record_extraction(test_user_id)
        count = get_extraction_count(test_user_id)
        print(f"✓ Recorded extraction #{i+1}: {count}/{FREE_TIER_MONTHLY_LIMIT}")
    
    # Check count
    final_count = get_extraction_count(test_user_id)
    assert final_count == FREE_TIER_MONTHLY_LIMIT, f"Should have used all {FREE_TIER_MONTHLY_LIMIT} extractions"
    
    # Try to extract again - should be blocked
    can_extract, remaining, message = check_extraction_limit(test_user_id)
    assert not can_extract, "Should not be able to extract after limit"
    assert remaining == 0, "Should have 0 remaining"
    print(f"\n✓ Rate limit enforced: {message}")
    
    # Try to use one more - should still be blocked
    can_extract_again, _, _ = check_extraction_limit(test_user_id)
    assert not can_extract_again, "Should still be blocked"
    print(f"✓ Multiple checks work correctly")
    
    print(f"\n✅ All tests passed!")

if __name__ == "__main__":
    test_rate_limiting()
