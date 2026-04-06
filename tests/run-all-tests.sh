#!/bin/bash
# Run all protocol test suites

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo ""
echo "========================================"
echo "  RNAS-OpenWrt Test Suite Runner"
echo "========================================"
echo ""

TOTAL_PASSED=0
TOTAL_FAILED=0

run_suite() {
    local name="$1"
    local script="$2"
    
    echo "----------------------------------------"
    echo "Running $name tests..."
    echo "----------------------------------------"
    
    if [ -f "$script" ]; then
        if bash "$script"; then
            echo -e "${GREEN}$name tests passed${NC}"
            TOTAL_PASSED=$((TOTAL_PASSED + 1))
        else
            echo -e "${RED}$name tests failed${NC}"
            TOTAL_FAILED=$((TOTAL_FAILED + 1))
        fi
    else
        echo -e "${YELLOW}$name test script not found: $script${NC}"
        TOTAL_FAILED=$((TOTAL_FAILED + 1))
    fi
    echo ""
}

cd "$PROJECT_ROOT"

run_suite "PPPoE" "./tests/pppoe/test-pppoe.sh"
run_suite "IPoE" "./tests/ipoe/test-ipoe.sh"
run_suite "L2TP" "./tests/l2tp/test-l2tp.sh"
run_suite "PPTP" "./tests/pptp/test-pptp.sh"
run_suite "SSTP" "./tests/sstp/test-sstp.sh"

echo "========================================"
echo "  Overall Summary"
echo "========================================"
echo "Suites Passed: $TOTAL_PASSED"
echo "Suites Failed: $TOTAL_FAILED"
echo "========================================"

if [ $TOTAL_FAILED -eq 0 ]; then
    echo -e "${GREEN}All test suites passed!${NC}"
    exit 0
else
    echo -e "${RED}Some test suites failed.${NC}"
    exit 1
fi
