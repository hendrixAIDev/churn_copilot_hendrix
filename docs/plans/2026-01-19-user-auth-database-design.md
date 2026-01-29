# User Authentication & Database Design

**Date:** 2026-01-19
**Status:** Approved
**Target:** MVP for 1000 users (centralized web app)

---

## Overview

Replace browser localStorage with PostgreSQL database and add user authentication. Each user has isolated data accessible via email/password login.

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Database | PostgreSQL | Handles concurrent users, works with cloud hosting, free tiers available |
| Schema | Fully normalized | Better querying, data integrity, analytics-ready |
| Auth | Email/password | Simplest for MVP, users expect it |
| Password hashing | bcrypt (cost 12) | Industry standard |
| Session | Streamlit session_state | Built-in, sufficient for MVP |
| Password reset | Manual (contact admin) | Defer email integration to v2 |
| Data isolation | Single-tenant | Each user sees only their data |

---

## Database Schema

### Users & Auth

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_users_email ON users(email);
```

### User Preferences

```sql
CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    sort_by VARCHAR(50) DEFAULT 'date_added',
    sort_descending BOOLEAN DEFAULT TRUE,
    group_by_issuer BOOLEAN DEFAULT FALSE,
    auto_enrich_enabled BOOLEAN DEFAULT TRUE,
    enrichment_min_confidence FLOAT DEFAULT 0.7,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Cards

```sql
CREATE TABLE cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    nickname VARCHAR(255),
    issuer VARCHAR(100) NOT NULL,
    annual_fee INTEGER DEFAULT 0,
    opened_date DATE,
    annual_fee_date DATE,
    closed_date DATE,
    is_business BOOLEAN DEFAULT FALSE,
    notes TEXT,
    raw_text TEXT,
    template_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_cards_user_id ON cards(user_id);
CREATE INDEX idx_cards_issuer ON cards(issuer);
```

### Signup Bonuses

```sql
CREATE TABLE signup_bonuses (
    card_id UUID PRIMARY KEY REFERENCES cards(id) ON DELETE CASCADE,
    points_or_cash VARCHAR(100) NOT NULL,
    spend_requirement FLOAT NOT NULL,
    time_period_days INTEGER NOT NULL,
    deadline DATE,
    spend_progress FLOAT DEFAULT 0,
    achieved BOOLEAN DEFAULT FALSE
);
```

### Card Credits/Perks

```sql
CREATE TABLE card_credits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    amount FLOAT NOT NULL,
    frequency VARCHAR(50) DEFAULT 'monthly',
    notes TEXT
);
CREATE INDEX idx_card_credits_card_id ON card_credits(card_id);
```

### Credit Usage Tracking

```sql
CREATE TABLE credit_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    credit_name VARCHAR(255) NOT NULL,
    last_used_period VARCHAR(20),
    reminder_snoozed_until DATE,
    UNIQUE(card_id, credit_name)
);
CREATE INDEX idx_credit_usage_card_id ON credit_usage(card_id);
```

### Retention Offers

```sql
CREATE TABLE retention_offers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    date_called DATE NOT NULL,
    offer_details TEXT NOT NULL,
    accepted BOOLEAN NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_retention_offers_card_id ON retention_offers(card_id);
```

### Product Changes

```sql
CREATE TABLE product_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    date_changed DATE NOT NULL,
    from_product VARCHAR(255) NOT NULL,
    to_product VARCHAR(255) NOT NULL,
    reason TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_product_changes_card_id ON product_changes(card_id);
```

---

## Authentication Module

### Interface (`src/core/auth.py`)

```python
class AuthService:
    def __init__(self, db: Database):
        self.db = db

    def register(self, email: str, password: str) -> User:
        """Create new user. Raises ValueError if email exists."""

    def login(self, email: str, password: str) -> User | None:
        """Verify credentials. Returns User or None."""

    def get_user(self, user_id: UUID) -> User | None:
        """Fetch user by ID (for session restoration)."""

    def change_password(self, user_id: UUID, old_pw: str, new_pw: str) -> bool:
        """Change password. Returns success."""
```

### Validation Rules

- **Email:** Valid format, stored lowercase, unique
- **Password:** Minimum 8 characters
- **Error messages:** Generic "invalid credentials" (don't reveal if email exists)

---

## Storage Layer

### Adapter Pattern

```python
class StorageInterface(Protocol):
    def get_cards(self) -> list[Card]: ...
    def save_card(self, card: Card) -> Card: ...
    def delete_card(self, card_id: str) -> bool: ...
    def get_preferences(self) -> UserPreferences: ...
    def save_preferences(self, prefs: UserPreferences) -> None: ...

class DatabaseStorage(StorageInterface):
    def __init__(self, db: Database, user_id: UUID):
        self.db = db
        self.user_id = user_id  # All queries scoped to this user
```

This pattern allows the rest of the app to be auth-agnostic. It receives a storage object already scoped to the current user.

---

## UI Integration

### App Flow

```
┌─────────────┐
│ Not logged  │──→ Show Login/Register form
│ in          │
└─────────────┘
       │ successful login
       ▼
┌─────────────┐
│ Logged in   │──→ Show existing app + user menu
└─────────────┘
```

### Session State

```python
st.session_state.user_id      # UUID of logged-in user
st.session_state.user_email   # For display in UI
```

### Login/Register Form

- Tab-based: "Login" | "Register"
- Inline error messages
- Auto-login after registration

---

## File Changes

### New Files

| File | Purpose |
|------|---------|
| `src/core/database.py` | Connection pooling, schema management |
| `src/core/auth.py` | AuthService class |
| `src/core/db_storage.py` | DatabaseStorage implementation |
| `scripts/init_db.py` | Database initialization script |
| `.env.example` | Document required environment variables |

### Modified Files

| File | Changes |
|------|---------|
| `src/core/models.py` | Add User model |
| `src/ui/app.py` | Add login/register, gate app behind auth |
| `requirements.txt` | Add psycopg2-binary, bcrypt |

---

## Implementation Phases

### Phase 1: Database Foundation
- [ ] Create `database.py` with connection and schema
- [ ] Create `init_db.py` script
- [ ] Add dependencies to `requirements.txt`
- [ ] Create `.env.example`

### Phase 2: Authentication
- [ ] Add User model to `models.py`
- [ ] Create `auth.py` with AuthService

### Phase 3: Storage Layer
- [ ] Create `db_storage.py` with full CRUD
- [ ] Unit tests for storage operations

### Phase 4: UI Integration
- [ ] Add login/register forms
- [ ] Add auth gate to main app
- [ ] Add user menu (logout, change password)
- [ ] Replace WebStorage with DatabaseStorage

---

## Environment Variables

```bash
# Required
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Optional (for local development)
# DATABASE_URL=postgresql://localhost:5432/churnpilot
```

---

## Security Considerations

1. **Passwords:** bcrypt with cost factor 12, never logged
2. **SQL injection:** Parameterized queries only
3. **Session:** Server-side via Streamlit (no client tokens)
4. **Data isolation:** All queries include `user_id` in WHERE clause
5. **HTTPS:** Required for production deployment

---

## Future Enhancements (Not in MVP)

- Email-based password reset
- OAuth (Google, GitHub)
- "Remember me" with secure cookies
- Account deletion self-service
- Data export feature
