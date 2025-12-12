#!/bin/bash
# Monitor all worker branches for progress

echo "=== Worker Progress ==="
echo ""

for branch in work/task-1-core work/task-2-html work/task-3-markdown work/task-4-tui; do
    if git rev-parse --verify $branch >/dev/null 2>&1; then
        latest=$(git log $branch --oneline -1 2>/dev/null)
        if echo "$latest" | grep -q "\[COMPLETE\]"; then
            status="COMPLETE"
        elif echo "$latest" | grep -q "\[BLOCKED"; then
            status="BLOCKED"
        elif echo "$latest" | grep -q "\[CHECKPOINT\]"; then
            status="IN PROGRESS"
        else
            status="STARTING"
        fi
        echo "$branch: $status"
        echo "  $latest"
    fi
done
echo ""
