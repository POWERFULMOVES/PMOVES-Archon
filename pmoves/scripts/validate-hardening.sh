#!/bin/bash
# PMOVES.AI Docker Hardening Validation Script
#
# Usage:
#   ./validate-hardening.sh [service_name]

main() {
    local target_service="${1:-}"
    local file="pmoves/docker-compose.hardened.yml"
    local passed=0 warnings=0 errors=0

    echo "PMOVES.AI Docker Hardening Validation"
    echo "======================================"

    if [[ ! -f "$file" ]]; then
        echo "[ERROR] File not found: $file"
        exit 1
    fi

    echo "[INFO] Checking: $file"
    echo ""

    # Get services
    local services=$(grep '^  [a-z]' "$file" | grep ':$' | sed 's/  \([^:]*\):.*/\1/' | grep -v 'services\|secrets\|networks\|volumes' || true)

    for service in $services; do
        if [[ -n "$target_service" && "$service" != "$target_service" ]]; then
            continue
        fi

        echo "[INFO] Validating: $service"

        # Check user
        if grep -A 10 "^  ${service}:" "$file" | grep -q "^    user:"; then
            local user=$(grep -A 10 "^  ${service}:" "$file" | grep "^    user:" | sed 's/.*user: *//' | tr -d '"')
            if [[ "$user" =~ ^[0-9]+:[0-9]+$ ]]; then
                local uid=$(echo "$user" | cut -d: -f1)
                if [[ "$uid" != "0" ]]; then
                    echo "[PASS] Non-root user: $user"
                    ((passed++))
                else
                    echo "[FAIL] Runs as root: $user"
                    ((errors++))
                fi
            fi
        else
            echo "[WARN] No user directive"
            ((warnings++))
        fi

        # Check read_only
        if grep -A 10 "^  ${service}:" "$file" | grep -q "^    read_only:"; then
            local readonly=$(grep -A 10 "^  ${service}:" "$file" | grep "^    read_only:" | sed 's/.*read_only: *//')
            if [[ "$readonly" == "true" ]]; then
                echo "[PASS] Read-only filesystem"
                ((passed++))
            fi
        else
            echo "[WARN] No read_only directive"
            ((warnings++))
        fi

        # Check cap_drop
        if grep -A 20 "^  ${service}:" "$file" | grep -q 'cap_drop:.*ALL'; then
            echo "[PASS] All capabilities dropped"
            ((passed++))
        else
            echo "[WARN] No cap_drop: [\"ALL\"]"
            ((warnings++))
        fi

        # Check no-new-privileges
        if grep -A 20 "^  ${service}:" "$file" | grep -q "no-new-privileges:true"; then
            echo "[PASS] No-new-privileges enabled"
            ((passed++))
        else
            echo "[WARN] No no-new-privileges"
            ((warnings++))
        fi

        # Check resource limits
        if grep -A 50 "^  ${service}:" "$file" | grep -A 10 "deploy:" | grep -q "limits:"; then
            echo "[PASS] Resource limits defined"
            ((passed++))
        else
            echo "[WARN] No resource limits"
            ((warnings++))
        fi

        echo ""
    done

    echo "======================================"
    echo "Summary: $passed passed, $warnings warnings, $errors errors"

    if [[ $errors -gt 0 ]]; then
        exit 1
    fi
    exit 0
}

main "$@"
