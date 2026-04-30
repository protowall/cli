#!/bin/bash
# ProtoWall CLI smoke test
# Usage: ./scripts/test-cli.sh [base-url]

set -euo pipefail

BASE="${1:-https://protowall.app}"
PASS=0
FAIL=0

export PROTOWALL_API_URL="$BASE"

if [ -z "${PROTOWALL_API_KEY:-}" ]; then
  echo "Error: PROTOWALL_API_KEY is not set"
  exit 1
fi

check() {
  local label="$1" expected="$2" actual="$3"
  if [ "$actual" = "$expected" ]; then
    echo "  ✓ $label"
    PASS=$((PASS + 1))
  else
    echo "  ✗ $label (expected $expected, got $actual)"
    FAIL=$((FAIL + 1))
  fi
}

echo ""
echo "ProtoWall CLI smoke test"
echo "Target: $BASE"
echo ""

# --- List projects ---
echo "Projects"
output=$(protowall projects 2>&1) && status=0 || status=$?
check "List projects succeeds" "0" "$status"

# --- Create project ---
output=$(protowall project create "CLI Smoke Test" "https://example.com" 2>&1) && status=0 || status=$?
check "Create project succeeds" "0" "$status"

slug=$(echo "$output" | python3 -c "import sys,json; print(json.load(sys.stdin)['slug'])" 2>/dev/null || echo "")
if [ -z "$slug" ]; then
  echo "  ✗ Could not parse slug — aborting"
  exit 1
fi
echo "  (slug: $slug)"

# --- Get project ---
echo ""
echo "Project detail"
output=$(protowall project "$slug" 2>&1) && status=0 || status=$?
check "Get project succeeds" "0" "$status"

invite_count=$(echo "$output" | python3 -c "import sys,json; print(json.load(sys.stdin)['invite_count'])" 2>/dev/null || echo "")
check "Invite count is 0" "0" "$invite_count"

# --- Send invite ---
echo ""
echo "Invites"
output=$(protowall invite "$slug" "cli-smoke@protowall.app" 2>&1) && status=0 || status=$?
check "Send invite succeeds" "0" "$status"

invite_id=$(echo "$output" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")
inv_status=$(echo "$output" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "")
check "Invite status is PENDING" "PENDING" "$inv_status"

# --- List invites ---
output=$(protowall invites "$slug" 2>&1) && status=0 || status=$?
check "List invites succeeds" "0" "$status"

count=$(echo "$output" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
check "Has 1 invite" "1" "$count"

# --- Audit log ---
echo ""
echo "Audit"
output=$(protowall audit "$slug" 2>&1) && status=0 || status=$?
check "Audit log succeeds" "0" "$status"

total=$(echo "$output" | python3 -c "import sys,json; print(json.load(sys.stdin)['total'])" 2>/dev/null || echo "0")
check "Has audit events" "true" "$([ "$total" -ge 1 ] && echo true || echo false)"

# --- Revoke ---
echo ""
echo "Revoke"
if [ -n "$invite_id" ]; then
  output=$(protowall revoke "$slug" "$invite_id" 2>&1) && status=0 || status=$?
  check "Revoke succeeds" "0" "$status"

  rev_status=$(echo "$output" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "")
  check "Status is REVOKED" "REVOKED" "$rev_status"
fi

# --- Rotate secret ---
echo ""
echo "Origin secret"
output=$(protowall rotate-secret "$slug" 2>&1) && status=0 || status=$?
check "Rotate secret succeeds" "0" "$status"

secret=$(echo "$output" | python3 -c "import sys,json; print(json.load(sys.stdin)['origin_secret'])" 2>/dev/null || echo "")
check "Secret starts with pw_proj_" "true" "$(echo "$secret" | grep -q '^pw_proj_' && echo true || echo false)"

# --- Analytics (Pro-only — both 0 and tier_required exit are valid) ---
echo ""
echo "Analytics"
output=$(protowall usage "$slug" 7 2>&1) && status=0 || status=$?
if [ "$status" = "0" ]; then
    window=$(echo "$output" | python3 -c "import sys,json; print(json.load(sys.stdin)['window_days'])" 2>/dev/null || echo "")
    check "usage window=7" "7" "$window"
else
    case "$output" in
        *tier_required*) echo "  ✓ usage tier-gated to Pro (free tier)"; PASS=$((PASS+1)) ;;
        *) echo "  ✗ usage failed unexpectedly: $output"; FAIL=$((FAIL+1)) ;;
    esac
fi

# Invalid range
output=$(protowall usage "$slug" 90 2>&1) && status=0 || status=$?
case "$output" in
    *validation_error*) echo "  ✓ usage rejects range=90"; PASS=$((PASS+1)) ;;
    *tier_required*) echo "  ✓ usage tier-gated (free tier)"; PASS=$((PASS+1)) ;;
    *) echo "  ✗ usage range=90 unexpected: $output"; FAIL=$((FAIL+1)) ;;
esac

# --- Delete project ---
echo ""
echo "Cleanup"
output=$(protowall project delete "$slug" 2>&1) && status=0 || status=$?
check "Delete project succeeds" "0" "$status"

# Verify deleted
protowall project "$slug" 2>&1 && deleted=false || deleted=true
check "Project is gone" "true" "$deleted"

# --- Summary ---
echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
