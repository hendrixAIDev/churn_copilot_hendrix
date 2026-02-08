# ChurnPilot Testing Guide

## Test Pipeline

Tests are organized into 4 stages, each run at a specific point in the development workflow:

| Stage | When | Command | Purpose |
|-------|------|---------|---------|
| **1. Unit** | After implementation | `make test-unit` | Fast feedback on code correctness |
| **2. E2E** | Before commit | `make test-e2e` | Verify integrated functionality locally |
| **3. Smoke** | After push to experiment | `make test-smoke` | Quick verification of remote deployment |
| **4. Journey** | Before launch | `make test-journey` | Comprehensive user flow verification |

## Quick Start

```bash
# After writing code
make test-unit

# Before committing (or use pre-commit hook)
make pre-commit

# After pushing to experiment branch
make test-smoke

# Before merging to main (launch)
make test-journey
```

## Test Locations

```
tests/
├── conftest.py                    # Shared fixtures and markers
├── pytest.ini                     # Pytest configuration
├── test_*.py                      # Unit tests (40+ files)
├── e2e/
│   └── test_smoke.py             # Local E2E smoke tests
└── remote/
    ├── test_smoke_remote.py      # Remote smoke tests
    └── test_user_journeys_remote.py  # Remote journey tests
```

## Stage Details

### Stage 1: Unit Tests

**When:** After implementing a feature or fix

**What it tests:**
- Individual functions and classes
- Business logic
- Data transformations
- Validation rules

**Run:**
```bash
make test-unit
# Or run specific tests:
./venv/bin/pytest tests/test_auth.py -v
```

### Stage 2: E2E Tests

**When:** Before committing code

**Prerequisites:** Local server running (`make run`)

**What it tests:**
- Full request/response cycles
- Database operations
- Authentication flows
- API integrations

**Run:**
```bash
make run  # In another terminal
make test-e2e
```

### Stage 3: Smoke Tests

**When:** After pushing to experiment branch, before declaring deployment successful

**Prerequisites:** Code pushed to `experiment` branch, Streamlit Cloud deployment complete

**What it tests:**
- App responds on remote URL
- No obvious errors on page load
- Health endpoint accessible

**Run:**
```bash
make deploy-experiment
# Wait for Streamlit Cloud (60-90 seconds)
make test-smoke
```

### Stage 4: User Journey Tests

**When:** Before merging experiment to main (launching to production)

**Prerequisites:** Smoke tests passed, Playwright installed

**What it tests:**
- Complete user workflows end-to-end via real browser automation
- Data persistence across page refreshes
- All critical paths work exactly as a real user would experience them
- AI extraction with test account (quota bypassed)

**User Journeys Tested:**
1. New user signup and onboarding
2. Add first credit card from library
3. **AI extraction from URL** (critical)
4. Delete a card
5. Import card data
6. Data persistence across refresh

**Setup (one-time):**
```bash
make setup-playwright  # Installs Chromium for Playwright
```

**Run:**
```bash
make test-journey

# Run specific journey:
pytest tests/remote/test_user_journeys_remote.py::TestAIExtractionJourney -v -s
```

**Test Account Quota Exception:**
These accounts bypass AI extraction limits in all environments:
- `hendrix.ai.dev@gmail.com` (Hendrix's account)
- `test@churnpilot.dev` (Automated tests)
- Any email starting with: `test_`, `e2e_test_`, `journey_test_`

**Browser Automation:**
Journey tests use Playwright for real browser automation. When sub-agents run these tests, they can also use the OpenClaw `browser` tool with their assigned profile (e.g., `agent1`).

## Pre-Commit Hook

Install the pre-commit hook to automatically run unit + e2e tests before each commit:

```bash
./scripts/install-hooks.sh
```

This prevents committing broken code. To bypass (not recommended):
```bash
git commit --no-verify
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOCAL_URL` | `http://localhost:8501` | Local development server |
| `EXPERIMENT_URL` | `https://churnpilot-experiment.streamlit.app` | Experiment deployment |
| `BROWSER_PROFILE` | `agent1` | Browser profile for journey tests |

Override example:
```bash
EXPERIMENT_URL=https://my-fork.streamlit.app make test-smoke
```

## Pytest Markers

Tests are tagged with markers for selective running:

```bash
# Run only unit tests
pytest -m unit

# Run only E2E tests  
pytest -m e2e

# Run only smoke tests
pytest -m smoke

# Run only journey tests
pytest -m journey

# Skip slow tests
pytest -m "not slow"
```

## Troubleshooting

### E2E tests fail with "Server not running"
```bash
make run  # Start the server first
```

### Smoke tests fail with "Deployment not responding"
Wait 60-90 seconds after `git push` for Streamlit Cloud to deploy.

### Journey tests skip with "Execute via browser automation"
These tests are designed for sub-agent execution with browser automation. Run manually with Selenium or assign to a sub-agent.

## CI/CD Integration

For GitHub Actions or similar:

```yaml
jobs:
  test:
    steps:
      - run: make test-unit
      - run: make run &
      - run: sleep 10 && make test-e2e
  
  deploy-experiment:
    needs: test
    steps:
      - run: make deploy-experiment
      - run: sleep 90 && make test-smoke
```
