#!/bin/bash
# Claude Code CLI Pre-Tool Hook
# Validates tool execution before running (security gate)

# Hook parameters
TOOL_NAME="${1:-unknown}"
TOOL_PARAMS="${2:-}"

# Dangerous patterns to block
declare -a BLOCKED_PATTERNS=(
    "rm -rf /"
    "DROP DATABASE"
    "DROP TABLE"
    "TRUNCATE TABLE"
    "supabase db reset --force"
    "docker system prune -a"
    "docker volume rm"
    "> /dev/sda"
    "dd if=/dev/zero"
    "mkfs."
    "format c:"
)

# Environment file patterns to block (but allow .example files)
ENV_BLOCKED_PATTERNS=(
    "env\.shared"
    "env\.tier-"
    "\.env\."
    "\.env\.local"
)

ENV_ALLOWED_PATTERNS=(
    "\.env\.example"
    "env\.shared\.example"
    "env\.tier-.*\.example"
)

# Check for blocked patterns
for pattern in "${BLOCKED_PATTERNS[@]}"; do
    if echo "$TOOL_PARAMS" | grep -qi "$pattern"; then
        echo "❌ BLOCKED: Dangerous operation detected: $pattern" >&2
        echo "   Tool: $TOOL_NAME" >&2
        echo "   This operation has been blocked for safety." >&2

        # Log security event
        SECURITY_LOG="$HOME/.claude/logs/security-events.log"
        mkdir -p "$(dirname "$SECURITY_LOG")"
        echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] BLOCKED: $TOOL_NAME - Pattern: $pattern - User: $(whoami)" >> "$SECURITY_LOG"

        # Exit non-zero to block Claude from executing
        exit 1
    fi
done

# Additional safety checks for specific tools

# Block Bash tool with destructive filesystem operations
if [ "$TOOL_NAME" = "Bash" ]; then
    # Check for piping to important system files
    if echo "$TOOL_PARAMS" | grep -E "(>|>>)\s*/etc/" >/dev/null; then
        echo "❌ BLOCKED: Writing to /etc/ requires manual review" >&2
        exit 1
    fi

    # Block chmod on system directories
    if echo "$TOOL_PARAMS" | grep -E "chmod.*(777|666)" >/dev/null; then
        echo "⚠️  WARNING: Overly permissive chmod detected" >&2
        echo "   Consider using more restrictive permissions" >&2
        # Don't block, just warn
    fi
fi

# Block Edit/Write to environment files (strict blocking)
if [ "$TOOL_NAME" = "Edit" ] || [ "$TOOL_NAME" = "Write" ]; then
    FILE_TO_EDIT="$TOOL_PARAMS"

    # Check if it's an allowed example file
    IS_ALLOWED=0
    for allowed_pattern in "${ENV_ALLOWED_PATTERNS[@]}"; do
        if echo "$FILE_TO_EDIT" | grep -qi "$allowed_pattern"; then
            IS_ALLOWED=1
            break
        fi
    done

    # Check if it's a blocked env file
    for blocked_pattern in "${ENV_BLOCKED_PATTERNS[@]}"; do
        if echo "$FILE_TO_EDIT" | grep -qi "$blocked_pattern"; then
            # But skip if it's an allowed example file
            if [ "$IS_ALLOWED" -eq 0 ]; then
                echo "❌ BLOCKED: Direct environment file modification" >&2
                echo "   File: $FILE_TO_EDIT" >&2
                echo "   Pattern: $blocked_pattern" >&2
                echo "   Use /pmoves:env command or edit .example files instead" >&2
                exit 1
            fi
        fi
    done

    # Validate docker-compose files (if yamllint is available)
    if echo "$FILE_TO_EDIT" | grep -q "docker-compose.*\.yml"; then
        if command -v yamllint &>/dev/null; then
            # Schedule validation for after edit completes
            # (We create a temp marker for post-tool hook to check)
            export PMOVES_VALIDATE_YAML="$FILE_TO_EDIT"
        fi
    fi

    # Original sensitive file check (still warn for other cases)
    if echo "$TOOL_PARAMS" | grep -E "(/etc/|/.ssh/|password|secret)" >/dev/null; then
        echo "⚠️  WARNING: Modifying potentially sensitive file" >&2
        echo "   File path contains credential keywords" >&2
        # Don't block, just warn
    fi
fi

# All checks passed
echo "[Hook] Pre-tool validation passed for: $TOOL_NAME" >&2
exit 0
