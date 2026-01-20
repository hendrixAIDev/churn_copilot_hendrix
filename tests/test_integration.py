"""Integration tests for full auth + storage flow.

Requires DATABASE_URL to be set to a test database.
Run with: pytest tests/test_integration.py -v
"""

import os
import pytest
from uuid import UUID

# Skip if no database URL
pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set"
)


@pytest.fixture
def clean_db():
    """Provide a clean database state."""
    from src.core.database import get_cursor, init_database

    # Initialize schema
    init_database()

    yield

    # Cleanup - delete test users
    with get_cursor() as cursor:
        cursor.execute("DELETE FROM users WHERE email LIKE 'test_%@example.com'")


class TestFullAuthFlow:
    """Test complete authentication flow."""

    def test_register_login_flow(self, clean_db):
        """Should register and login successfully."""
        from src.core.auth import AuthService

        auth = AuthService()
        email = "test_flow@example.com"
        password = "testpassword123"

        # Register
        user = auth.register(email, password)
        assert user.email == email
        assert user.id is not None

        # Login
        logged_in = auth.login(email, password)
        assert logged_in is not None
        assert logged_in.id == user.id

    def test_storage_with_auth(self, clean_db):
        """Should store and retrieve cards for authenticated user."""
        from src.core.auth import AuthService
        from src.core.db_storage import DatabaseStorage
        from src.core.models import Card
        from datetime import datetime

        # Create user
        auth = AuthService()
        user = auth.register("test_storage@example.com", "testpassword123")

        # Create storage for user
        storage = DatabaseStorage(user.id)

        # Add a card
        from src.core.library import CardTemplate
        from src.core.models import Credit

        template = CardTemplate(
            id="test-card",
            name="Test Card",
            issuer="Test Bank",
            annual_fee=95,
            credits=[Credit(name="Test Credit", amount=10, frequency="monthly")],
        )

        card = storage.add_card_from_template(template, opened_date=None)

        # Retrieve cards
        cards = storage.get_all_cards()
        assert len(cards) == 1
        assert cards[0].name == "Test Card"

        # Delete card
        assert storage.delete_card(card.id) is True
        assert len(storage.get_all_cards()) == 0

    def test_user_isolation(self, clean_db):
        """Should isolate data between users."""
        from src.core.auth import AuthService
        from src.core.db_storage import DatabaseStorage
        from src.core.library import CardTemplate

        auth = AuthService()

        # Create two users
        user1 = auth.register("test_user1@example.com", "password123")
        user2 = auth.register("test_user2@example.com", "password123")

        storage1 = DatabaseStorage(user1.id)
        storage2 = DatabaseStorage(user2.id)

        # User 1 adds a card
        template = CardTemplate(id="t1", name="User1 Card", issuer="Bank", annual_fee=0, credits=[])
        storage1.add_card_from_template(template)

        # User 2 should see no cards
        assert len(storage1.get_all_cards()) == 1
        assert len(storage2.get_all_cards()) == 0
