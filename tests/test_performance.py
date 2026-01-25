"""Performance tests."""

import pytest
import time
from datetime import datetime, date
from uuid import uuid4
import os

# Ensure DATABASE_URL is set for tests
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/churnpilot")

from src.core.db_storage import DatabaseStorage
from src.core.auth import AuthService
from src.core.models import SignupBonus
from src.core.database import get_cursor, check_connection
from src.core.library import get_template


def add_card_helper(storage, template_id, opened_date=None, signup_bonus=None):
    """Helper to add card from template ID."""
    template = get_template(template_id)
    if template is None:
        raise ValueError(f"Template not found: {template_id}")
    return storage.add_card_from_template(
        template=template,
        opened_date=opened_date or date.today(),
        signup_bonus=signup_bonus
    )


class TestDatabaseConnection:
    """Verify database is accessible for performance tests."""

    def test_database_is_connected(self):
        """Database should be reachable."""
        assert check_connection() is True


class TestQueryPerformance:
    """Test query performance is acceptable."""

    @pytest.fixture
    def user_with_many_cards(self):
        """Create user with 50 cards for performance testing."""
        auth = AuthService()
        email = f"perf_test_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        for i in range(50):
            signup_bonus = SignupBonus(
                points_or_cash=f"{(i+1)*1000} points",
                spend_requirement=(i+1)*100,
                time_period_days=90,
                deadline=date(2026, 6, 1)
            ) if i % 3 == 0 else None

            card = add_card_helper(storage, "chase_sapphire_preferred", signup_bonus=signup_bonus)
            card.nickname = f"Card {i}"
            card.notes = f"Notes for card {i}\nWith multiple lines."
            storage.save_card(card)

        return storage

    def test_get_all_cards_performance(self, user_with_many_cards):
        """Getting 50 cards should be under 1 second."""
        storage = user_with_many_cards

        start = time.time()
        cards = storage.get_all_cards()
        elapsed = time.time() - start

        assert len(cards) == 50
        assert elapsed < 1.0, f"get_all_cards took {elapsed:.3f}s, expected < 1.0s"

    def test_add_card_performance(self):
        """Adding a card should be under 200ms."""
        auth = AuthService()
        email = f"add_perf_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        start = time.time()
        add_card_helper(storage, "chase_sapphire_preferred")
        elapsed = time.time() - start

        assert elapsed < 0.2, f"add_card took {elapsed:.3f}s, expected < 0.2s"

    def test_save_card_performance(self):
        """Saving card changes should be under 200ms."""
        auth = AuthService()
        email = f"save_perf_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        card = add_card_helper(storage, "chase_sapphire_preferred")

        start = time.time()
        card.nickname = "Updated Name"
        card.notes = "Updated notes"
        storage.save_card(card)
        elapsed = time.time() - start

        assert elapsed < 0.2, f"save_card took {elapsed:.3f}s, expected < 0.2s"

    def test_delete_card_performance(self):
        """Deleting a card should be under 200ms."""
        auth = AuthService()
        email = f"delete_perf_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        card = add_card_helper(storage, "chase_sapphire_preferred")

        start = time.time()
        storage.delete_card(card.id)
        elapsed = time.time() - start

        assert elapsed < 0.2, f"delete_card took {elapsed:.3f}s, expected < 0.2s"


class TestAuthPerformance:
    """Test authentication performance."""

    def test_login_performance(self):
        """Login should be under 500ms (bcrypt is intentionally slow)."""
        auth = AuthService()
        email = f"login_perf_{datetime.now().timestamp()}@test.com"
        password = "TestPassword123!"
        auth.register(email, password)

        start = time.time()
        user = auth.login(email, password)
        elapsed = time.time() - start

        assert user is not None
        # bcrypt is intentionally slow for security, allow up to 500ms
        assert elapsed < 0.5, f"login took {elapsed:.3f}s, expected < 0.5s"

    def test_register_performance(self):
        """Registration should be under 500ms (bcrypt hashing)."""
        auth = AuthService()
        email = f"register_perf_{datetime.now().timestamp()}@test.com"

        start = time.time()
        user = auth.register(email, "TestPassword123!")
        elapsed = time.time() - start

        assert user is not None
        assert elapsed < 0.5, f"register took {elapsed:.3f}s, expected < 0.5s"


class TestBulkOperationPerformance:
    """Test bulk operation performance."""

    def test_bulk_add_20_cards(self):
        """Adding 20 cards sequentially should be under 5 seconds."""
        auth = AuthService()
        email = f"bulk_add_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        start = time.time()
        for i in range(20):
            add_card_helper(storage, "chase_sapphire_preferred")
        elapsed = time.time() - start

        assert elapsed < 5.0, f"bulk add took {elapsed:.3f}s, expected < 5.0s"

    def test_bulk_edit_20_cards(self):
        """Editing 20 cards sequentially should be under 5 seconds."""
        auth = AuthService()
        email = f"bulk_edit_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        # Create cards first
        cards = []
        for i in range(20):
            card = add_card_helper(storage, "chase_sapphire_preferred")
            cards.append(card)

        # Time the edits
        start = time.time()
        for i, card in enumerate(cards):
            card.nickname = f"Edited Card {i}"
            storage.save_card(card)
        elapsed = time.time() - start

        assert elapsed < 5.0, f"bulk edit took {elapsed:.3f}s, expected < 5.0s"

    def test_bulk_delete_20_cards(self):
        """Deleting 20 cards sequentially should be under 3 seconds."""
        auth = AuthService()
        email = f"bulk_delete_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        # Create cards first
        cards = []
        for i in range(20):
            card = add_card_helper(storage, "chase_sapphire_preferred")
            cards.append(card)

        # Time the deletes
        start = time.time()
        for card in cards:
            storage.delete_card(card.id)
        elapsed = time.time() - start

        assert elapsed < 3.0, f"bulk delete took {elapsed:.3f}s, expected < 3.0s"


class TestDatabaseQueryEfficiency:
    """Test that database queries are efficient."""

    def test_get_all_cards_single_query_pattern(self):
        """get_all_cards should not cause N+1 query problem."""
        auth = AuthService()
        email = f"n1_test_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        storage = DatabaseStorage(user.id)

        # Add cards with signup bonuses
        for i in range(10):
            signup_bonus = SignupBonus(
                points_or_cash=f"{i*1000} points",
                spend_requirement=i*100,
                time_period_days=90,
                deadline=date(2026, 6, 1)
            )
            add_card_helper(storage, "chase_sapphire_preferred", signup_bonus=signup_bonus)

        # Time getting all cards (should be fast even with related data)
        start = time.time()
        cards = storage.get_all_cards()
        elapsed = time.time() - start

        assert len(cards) == 10
        # With efficient queries, this should be very fast
        assert elapsed < 0.5, f"get_all_cards with relations took {elapsed:.3f}s"

        # Verify related data is loaded
        for card in cards:
            assert card.signup_bonus is not None

    def test_simple_query_performance(self):
        """Simple SELECT queries should be very fast."""
        times = []
        for i in range(10):
            start = time.time()
            with get_cursor(commit=False) as cur:
                cur.execute("SELECT 1 as val")
                cur.fetchone()
            times.append(time.time() - start)

        avg_time = sum(times) / len(times)
        assert avg_time < 0.05, f"Average simple query took {avg_time:.4f}s, expected < 0.05s"


class TestConcurrentUserPerformance:
    """Test performance with multiple concurrent users."""

    def test_multiple_users_simultaneous_reads(self):
        """Multiple users reading simultaneously should be fast."""
        auth = AuthService()

        # Create 5 users with cards
        storages = []
        for i in range(5):
            email = f"concurrent_{i}_{datetime.now().timestamp()}@test.com"
            user = auth.register(email, "TestPassword123!")
            storage = DatabaseStorage(user.id)
            for j in range(5):
                add_card_helper(storage, "chase_sapphire_preferred")
            storages.append(storage)

        # Time reading from all users
        start = time.time()
        for storage in storages:
            cards = storage.get_all_cards()
            assert len(cards) == 5
        elapsed = time.time() - start

        # 5 users x 5 cards each should be under 2 seconds
        assert elapsed < 2.0, f"concurrent reads took {elapsed:.3f}s, expected < 2.0s"
