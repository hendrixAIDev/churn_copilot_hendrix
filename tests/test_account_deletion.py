"""Test account deletion functionality."""

import pytest
from uuid import UUID, uuid4
from src.core.auth import AuthService
from src.core.database import get_cursor
from src.core.db_storage import DatabaseStorage


@pytest.fixture
def auth_service():
    """Create AuthService instance."""
    return AuthService()


@pytest.fixture
def test_user(auth_service):
    """Create a test user."""
    email = f"delete_test_{uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user = auth_service.register(email, password)
    yield user
    # Cleanup (in case test didn't delete)
    try:
        auth_service.delete_user(user.id)
    except Exception:
        pass


@pytest.fixture
def test_user_with_cards(auth_service):
    """Create a test user with cards."""
    email = f"delete_cards_test_{uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user = auth_service.register(email, password)
    
    # Add some cards directly via database
    with get_cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO cards (user_id, name, issuer, annual_fee, opened_date)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (str(user.id), "Test Card 1", "Test Bank", 95, "2024-01-01")
        )
        cursor.execute(
            """
            INSERT INTO cards (user_id, name, issuer, annual_fee, opened_date)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (str(user.id), "Test Card 2", "Test Bank", 0, "2024-01-01")
        )
    
    yield user
    # Cleanup (in case test didn't delete)
    try:
        auth_service.delete_user(user.id)
    except Exception:
        pass


class TestAccountDeletion:
    """Test account deletion functionality."""

    def test_delete_account_success(self, auth_service, test_user):
        """Test successful account deletion."""
        user_id = test_user.id
        
        # Verify user exists
        user = auth_service.get_user(user_id)
        assert user is not None
        
        # Create a session
        token = auth_service.create_session(user_id)
        
        # Delete account
        result = auth_service.delete_account(user_id)
        assert result is True
        
        # Verify user is gone
        user = auth_service.get_user(user_id)
        assert user is None
        
        # Verify sessions are gone
        with get_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM sessions WHERE user_id = %s",
                (str(user_id),)
            )
            count = cursor.fetchone()["count"]
            assert count == 0

    def test_delete_account_with_cards(self, auth_service, test_user_with_cards):
        """Test account deletion when user has cards."""
        user_id = test_user_with_cards.id
        
        # Verify user and cards exist
        with get_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM cards WHERE user_id = %s",
                (str(user_id),)
            )
            card_count = cursor.fetchone()["count"]
            assert card_count > 0
        
        # Delete account
        result = auth_service.delete_account(user_id)
        assert result is True
        
        # Verify all cards are gone (CASCADE should handle this)
        with get_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM cards WHERE user_id = %s",
                (str(user_id),)
            )
            card_count = cursor.fetchone()["count"]
            assert card_count == 0
        
        # Verify user is gone
        user = auth_service.get_user(user_id)
        assert user is None

    def test_delete_account_nonexistent_user(self, auth_service):
        """Test deleting a nonexistent account."""
        fake_user_id = uuid4()
        
        # Should return False for nonexistent user
        result = auth_service.delete_account(fake_user_id)
        assert result is False

    def test_delete_account_cascade_deletion(self, auth_service, test_user_with_cards):
        """Test that all user data is deleted (cascade)."""
        user_id = test_user_with_cards.id
        
        # Delete account
        result = auth_service.delete_account(user_id)
        assert result is True
        
        # Verify all related data is gone
        with get_cursor(commit=False) as cursor:
            # Check cards
            cursor.execute(
                "SELECT COUNT(*) FROM cards WHERE user_id = %s",
                (str(user_id),)
            )
            assert cursor.fetchone()["count"] == 0
            
            # Check user_preferences (may not exist, that's ok)
            cursor.execute(
                "SELECT COUNT(*) FROM user_preferences WHERE user_id = %s",
                (str(user_id),)
            )
            assert cursor.fetchone()["count"] == 0
            
            # Check sessions
            cursor.execute(
                "SELECT COUNT(*) FROM sessions WHERE user_id = %s",
                (str(user_id),)
            )
            assert cursor.fetchone()["count"] == 0
