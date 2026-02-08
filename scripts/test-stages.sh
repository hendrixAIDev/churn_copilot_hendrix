#!/bin/bash
# ChurnPilot Test Stage Runner
# ============================
#
# Usage:
#   ./scripts/test-stages.sh unit         # After implementation
#   ./scripts/test-stages.sh e2e          # Before commit
#   ./scripts/test-stages.sh smoke        # After push to experiment
#   ./scripts/test-stages.sh journey      # Before launch
#   ./scripts/test-stages.sh all          # Run all stages in order
#
# Environment Variables:
#   EXPERIMENT_URL     - Override experiment deployment URL
#   LOCAL_URL          - Override local server URL (default: http://localhost:8501)
#   BROWSER_PROFILE    - Browser profile for journey tests (default: agent1)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV="$PROJECT_DIR/venv/bin"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Defaults
LOCAL_URL="${LOCAL_URL:-http://localhost:8501}"
EXPERIMENT_URL="${EXPERIMENT_URL:-https://churnpilot-experiment.streamlit.app}"

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

check_server() {
    if curl -s --max-time 3 "$LOCAL_URL/_stcore/health" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

check_experiment() {
    if curl -s --max-time 10 "$EXPERIMENT_URL/_stcore/health" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

run_unit_tests() {
    print_header "STAGE 1: Unit Tests"
    print_info "When: After implementation"
    print_info "Purpose: Fast feedback on code correctness"
    echo ""
    
    cd "$PROJECT_DIR"
    $VENV/python -m pytest tests/ \
        --ignore=tests/e2e/ \
        --ignore=tests/remote/ \
        -v --timeout=10 \
        -m "not slow" \
        "$@"
    
    print_success "Unit tests passed!"
}

run_e2e_tests() {
    print_header "STAGE 2: E2E Tests"
    print_info "When: Before commit"
    print_info "Purpose: Verify integrated functionality"
    echo ""
    
    if ! check_server; then
        print_error "Local server not running on $LOCAL_URL"
        print_info "Start with: make run"
        exit 1
    fi
    
    cd "$PROJECT_DIR"
    LOCAL_URL="$LOCAL_URL" $VENV/python -m pytest tests/e2e/ \
        -v --timeout=60 \
        "$@"
    
    print_success "E2E tests passed!"
}

run_smoke_tests() {
    print_header "STAGE 3: Smoke Tests (Remote)"
    print_info "When: After push to experiment branch"
    print_info "Purpose: Quick verification of deployment"
    print_info "URL: $EXPERIMENT_URL"
    echo ""
    
    if ! check_experiment; then
        print_error "Experiment deployment not responding at $EXPERIMENT_URL"
        print_info "Wait for Streamlit Cloud to deploy, then retry"
        exit 1
    fi
    
    cd "$PROJECT_DIR"
    EXPERIMENT_URL="$EXPERIMENT_URL" $VENV/python -m pytest tests/remote/test_smoke_remote.py \
        -v --timeout=60 \
        "$@"
    
    print_success "Smoke tests passed!"
}

run_journey_tests() {
    print_header "STAGE 4: User Journey Tests (Remote)"
    print_info "When: Before launch (merge to main)"
    print_info "Purpose: Comprehensive user flow verification"
    print_info "URL: $EXPERIMENT_URL"
    echo ""
    
    if ! check_experiment; then
        print_error "Experiment deployment not responding at $EXPERIMENT_URL"
        exit 1
    fi
    
    print_info "Note: Full journey tests require browser automation"
    print_info "Sub-agents use browser tool with profile=${BROWSER_PROFILE:-agent1}"
    echo ""
    
    cd "$PROJECT_DIR"
    EXPERIMENT_URL="$EXPERIMENT_URL" $VENV/python -m pytest tests/remote/test_user_journeys_remote.py \
        -v --timeout=120 \
        "$@"
    
    print_success "User journey tests passed!"
}

run_all_stages() {
    print_header "RUNNING ALL TEST STAGES"
    
    run_unit_tests
    run_e2e_tests
    run_smoke_tests
    run_journey_tests
    
    print_header "ALL STAGES PASSED ✓"
}

# Main
case "${1:-}" in
    unit)
        shift
        run_unit_tests "$@"
        ;;
    e2e)
        shift
        run_e2e_tests "$@"
        ;;
    smoke)
        shift
        run_smoke_tests "$@"
        ;;
    journey)
        shift
        run_journey_tests "$@"
        ;;
    all)
        shift
        run_all_stages "$@"
        ;;
    *)
        echo "ChurnPilot Test Stage Runner"
        echo ""
        echo "Usage: $0 <stage> [pytest-args]"
        echo ""
        echo "Stages (run in order):"
        echo "  unit      Unit tests (after implementation)"
        echo "  e2e       E2E tests (before commit)"
        echo "  smoke     Smoke tests (after push to experiment)"
        echo "  journey   User journey tests (before launch)"
        echo "  all       Run all stages in sequence"
        echo ""
        echo "Examples:"
        echo "  $0 unit                    # Run unit tests"
        echo "  $0 e2e -k auth            # Run E2E tests matching 'auth'"
        echo "  $0 smoke --tb=long        # Run smoke tests with full traceback"
        exit 1
        ;;
esac
