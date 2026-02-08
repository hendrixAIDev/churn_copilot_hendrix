#!/bin/bash
# Install git hooks for ChurnPilot

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
HOOKS_DIR="$PROJECT_DIR/.git/hooks"

# Create pre-commit hook
cat > "$HOOKS_DIR/pre-commit" << 'EOF'
#!/bin/bash
# ChurnPilot Pre-Commit Hook
# Runs unit tests + e2e tests before allowing commit

echo "→ Running pre-commit tests..."

# Get project root
PROJECT_DIR="$(git rev-parse --show-toplevel)"
cd "$PROJECT_DIR"

# Run pre-commit tests
make pre-commit

if [ $? -ne 0 ]; then
    echo ""
    echo "✗ Pre-commit tests failed. Commit aborted."
    echo "  Fix the issues and try again, or use --no-verify to skip."
    exit 1
fi

echo "✓ Pre-commit tests passed"
EOF

chmod +x "$HOOKS_DIR/pre-commit"
echo "✓ Installed pre-commit hook"
echo "  Hook runs: make pre-commit (unit + e2e tests)"
echo "  Skip with: git commit --no-verify"
