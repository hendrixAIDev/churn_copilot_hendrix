"""Database schema health tests."""

import pytest
from datetime import datetime, date
import os

# Ensure DATABASE_URL is set for tests
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/churnpilot")

from src.core.database import get_cursor, check_connection
from src.core.db_storage import DatabaseStorage
from src.core.auth import AuthService
from src.core.models import SignupBonus
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
    """Verify database is accessible for schema tests."""

    def test_database_is_connected(self):
        """Database should be reachable."""
        assert check_connection() is True


class TestSchemaHealth:
    """Test database schema is correct."""

    def test_all_required_tables_exist(self):
        """All required tables should exist."""
        required_tables = [
            'users',
            'user_preferences',
            'cards',
            'signup_bonuses',
            'card_credits',
            'credit_usage',
            'retention_offers',
            'product_changes'
        ]

        with get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            existing = {row["table_name"] for row in cur.fetchall()}

        for table in required_tables:
            assert table in existing, f"Missing table: {table}"

    def test_users_table_columns(self):
        """Users table should have required columns."""
        required_columns = ['id', 'email', 'password_hash', 'created_at']

        with get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'users' AND table_schema = 'public'
            """)
            existing = {row["column_name"] for row in cur.fetchall()}

        for col in required_columns:
            assert col in existing, f"Missing column in users: {col}"

    def test_cards_table_columns(self):
        """Cards table should have required columns."""
        required_columns = [
            'id', 'user_id', 'name', 'issuer', 'opened_date',
            'annual_fee', 'nickname', 'notes', 'closed_date'
        ]

        with get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'cards' AND table_schema = 'public'
            """)
            existing = {row["column_name"] for row in cur.fetchall()}

        for col in required_columns:
            assert col in existing, f"Missing column in cards: {col}"

    def test_signup_bonuses_table_columns(self):
        """Signup bonuses table should have required columns."""
        required_columns = [
            'card_id', 'points_or_cash', 'spend_requirement', 'time_period_days'
        ]

        with get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'signup_bonuses' AND table_schema = 'public'
            """)
            existing = {row["column_name"] for row in cur.fetchall()}

        for col in required_columns:
            assert col in existing, f"Missing column in signup_bonuses: {col}"


class TestForeignKeyConstraints:
    """Test foreign key constraints are properly defined."""

    def test_cards_has_user_fk(self):
        """Cards table should have foreign key to users."""
        with get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT tc.table_name, kcu.column_name, ccu.table_name AS foreign_table
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = 'cards'
            """)
            fks = cur.fetchall()

        fk_targets = [(row["column_name"], row["foreign_table"]) for row in fks]
        assert ("user_id", "users") in fk_targets, "cards should have FK to users"

    def test_signup_bonuses_has_card_fk(self):
        """Signup bonuses table should have foreign key to cards."""
        with get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT tc.table_name, kcu.column_name, ccu.table_name AS foreign_table
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = 'signup_bonuses'
            """)
            fks = cur.fetchall()

        fk_targets = [(row["column_name"], row["foreign_table"]) for row in fks]
        assert ("card_id", "cards") in fk_targets, "signup_bonuses should have FK to cards"

    def test_card_credits_has_card_fk(self):
        """Card credits table should have foreign key to cards."""
        with get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT tc.table_name, kcu.column_name, ccu.table_name AS foreign_table
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = 'card_credits'
            """)
            fks = cur.fetchall()

        fk_targets = [(row["column_name"], row["foreign_table"]) for row in fks]
        assert ("card_id", "cards") in fk_targets, "card_credits should have FK to cards"


class TestCascadeDeletes:
    """Test cascade delete behavior."""

    def test_signup_bonus_cascade_on_card_delete(self):
        """Deleting card should cascade delete signup bonus."""
        with get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT rc.delete_rule
                FROM information_schema.referential_constraints rc
                JOIN information_schema.table_constraints tc
                    ON rc.constraint_name = tc.constraint_name
                WHERE tc.table_name = 'signup_bonuses'
            """)
            row = cur.fetchone()

        assert row is not None
        assert row["delete_rule"] == "CASCADE", "signup_bonuses should CASCADE on card delete"

    def test_card_credits_cascade_on_card_delete(self):
        """Deleting card should cascade delete card credits."""
        with get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT rc.delete_rule
                FROM information_schema.referential_constraints rc
                JOIN information_schema.table_constraints tc
                    ON rc.constraint_name = tc.constraint_name
                WHERE tc.table_name = 'card_credits'
            """)
            row = cur.fetchone()

        assert row is not None
        assert row["delete_rule"] == "CASCADE", "card_credits should CASCADE on card delete"


class TestNotNullConstraints:
    """Test NOT NULL constraints on critical columns."""

    def test_users_id_not_null(self):
        """Users.id should be NOT NULL."""
        with get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT is_nullable FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'id'
            """)
            row = cur.fetchone()

        assert row["is_nullable"] == "NO", "users.id should be NOT NULL"

    def test_users_email_not_null(self):
        """Users.email should be NOT NULL."""
        with get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT is_nullable FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'email'
            """)
            row = cur.fetchone()

        assert row["is_nullable"] == "NO", "users.email should be NOT NULL"

    def test_cards_user_id_not_null(self):
        """Cards.user_id should be NOT NULL."""
        with get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT is_nullable FROM information_schema.columns
                WHERE table_name = 'cards' AND column_name = 'user_id'
            """)
            row = cur.fetchone()

        assert row["is_nullable"] == "NO", "cards.user_id should be NOT NULL"

    def test_cards_name_not_null(self):
        """Cards.name should be NOT NULL."""
        with get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT is_nullable FROM information_schema.columns
                WHERE table_name = 'cards' AND column_name = 'name'
            """)
            row = cur.fetchone()

        assert row["is_nullable"] == "NO", "cards.name should be NOT NULL"


class TestIndexes:
    """Test that important indexes exist."""

    def test_users_email_index_or_unique(self):
        """Users.email should have an index (for login lookups)."""
        with get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT indexname FROM pg_indexes
                WHERE tablename = 'users'
                AND indexdef LIKE '%email%'
            """)
            rows = cur.fetchall()

        assert len(rows) > 0, "users.email should have an index"

    def test_cards_user_id_index(self):
        """Cards.user_id should have an index (for user card lookups)."""
        with get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT indexname FROM pg_indexes
                WHERE tablename = 'cards'
                AND indexdef LIKE '%user_id%'
            """)
            rows = cur.fetchall()

        assert len(rows) > 0, "cards.user_id should have an index"


class TestOrphanData:
    """Test for orphaned records."""

    def test_no_orphan_signup_bonuses(self):
        """All signup_bonuses should have valid card_id."""
        with get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT COUNT(*) as cnt FROM signup_bonuses sb
                LEFT JOIN cards c ON sb.card_id = c.id
                WHERE c.id IS NULL
            """)
            orphan_count = cur.fetchone()["cnt"]

        assert orphan_count == 0, f"Found {orphan_count} orphan signup_bonuses"

    def test_no_orphan_card_credits(self):
        """All card_credits should have valid card_id."""
        with get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT COUNT(*) as cnt FROM card_credits cc
                LEFT JOIN cards c ON cc.card_id = c.id
                WHERE c.id IS NULL
            """)
            orphan_count = cur.fetchone()["cnt"]

        assert orphan_count == 0, f"Found {orphan_count} orphan card_credits"

    def test_no_orphan_cards(self):
        """All cards should have valid user_id."""
        with get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT COUNT(*) as cnt FROM cards c
                LEFT JOIN users u ON c.user_id = u.id
                WHERE u.id IS NULL
            """)
            orphan_count = cur.fetchone()["cnt"]

        assert orphan_count == 0, f"Found {orphan_count} orphan cards"

    def test_no_orphan_credit_usage(self):
        """All credit_usage should have valid card_id."""
        with get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT COUNT(*) as cnt FROM credit_usage cu
                LEFT JOIN cards c ON cu.card_id = c.id
                WHERE c.id IS NULL
            """)
            orphan_count = cur.fetchone()["cnt"]

        assert orphan_count == 0, f"Found {orphan_count} orphan credit_usage"


class TestUniqueConstraints:
    """Test unique constraints."""

    def test_users_email_unique(self):
        """Users.email should have unique constraint."""
        with get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT COUNT(*) as cnt FROM information_schema.table_constraints
                WHERE table_name = 'users'
                AND constraint_type = 'UNIQUE'
                AND constraint_name LIKE '%email%'
            """)
            count = cur.fetchone()["cnt"]

        # Email uniqueness might be enforced via unique index instead of constraint
        # Let's check for either
        if count == 0:
            with get_cursor(commit=False) as cur:
                cur.execute("""
                    SELECT COUNT(*) as cnt FROM pg_indexes
                    WHERE tablename = 'users'
                    AND indexdef LIKE '%UNIQUE%'
                    AND indexdef LIKE '%email%'
                """)
                count = cur.fetchone()["cnt"]

        assert count > 0, "users.email should have unique constraint or index"

    def test_cards_id_unique(self):
        """Cards.id should be unique (primary key)."""
        with get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT COUNT(*) as cnt FROM information_schema.table_constraints
                WHERE table_name = 'cards'
                AND constraint_type = 'PRIMARY KEY'
            """)
            count = cur.fetchone()["cnt"]

        assert count > 0, "cards should have primary key"


class TestDataTypes:
    """Test column data types are appropriate."""

    def test_users_id_is_uuid(self):
        """Users.id should be UUID type."""
        with get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT data_type FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'id'
            """)
            row = cur.fetchone()

        assert row["data_type"] == "uuid", "users.id should be UUID"

    def test_cards_id_is_uuid(self):
        """Cards.id should be UUID type."""
        with get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT data_type FROM information_schema.columns
                WHERE table_name = 'cards' AND column_name = 'id'
            """)
            row = cur.fetchone()

        assert row["data_type"] == "uuid", "cards.id should be UUID"

    def test_cards_opened_date_is_date(self):
        """Cards.opened_date should be DATE type."""
        with get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT data_type FROM information_schema.columns
                WHERE table_name = 'cards' AND column_name = 'opened_date'
            """)
            row = cur.fetchone()

        assert row["data_type"] == "date", "cards.opened_date should be DATE"

    def test_cards_annual_fee_is_numeric(self):
        """Cards.annual_fee should be numeric type."""
        with get_cursor(commit=False) as cur:
            cur.execute("""
                SELECT data_type FROM information_schema.columns
                WHERE table_name = 'cards' AND column_name = 'annual_fee'
            """)
            row = cur.fetchone()

        # Could be integer, numeric, or double precision
        assert row["data_type"] in ["integer", "numeric", "double precision", "real"], \
            f"cards.annual_fee should be numeric, got {row['data_type']}"
