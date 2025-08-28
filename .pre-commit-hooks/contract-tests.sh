#!/bin/sh
# .pre-commit-hooks/contract-tests.sh
# Contract Test Validation Pre-commit Hook

echo "🔍 Validating component contracts..."

# Run core contract tests with strict failure policy
pytest tests/contracts/test_core_contracts.py -m contract --maxfail=1 -x -q

# Check exit code
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Contract violation detected!"
    echo ""
    echo "🚫 Cannot commit interface-breaking changes."
    echo ""
    echo "🔧 To fix contract violations:"
    echo "   1. Run: pytest tests/contracts/ -m contract -v"
    echo "   2. Fix failing contract tests"
    echo "   3. Ensure all component interfaces remain stable"
    echo ""
    echo "💡 Contract tests prevent regressions at component boundaries."
    echo "   They must always pass to maintain system stability."
    exit 1
fi

echo "✅ All contracts satisfied"
echo "🛡️  Component interfaces are stable"