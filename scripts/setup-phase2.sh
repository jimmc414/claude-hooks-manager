#!/bin/bash
# Phase 2 Setup: Create worktrees for Workers 2-4
# Run this AFTER Worker 1 commits [COMPLETE]

set -e

echo "=== Setting up Phase 2 workers ==="

# Verify Worker 1 completed
if ! git log work/task-1-core --oneline -1 | grep -q "\[COMPLETE\]"; then
    echo "ERROR: Worker 1 has not committed [COMPLETE] yet"
    echo "Latest commit: $(git log work/task-1-core --oneline -1)"
    exit 1
fi

echo "Worker 1 complete. Creating parallel worktrees..."

# Create worktrees branching from Worker 1's completed work
git worktree add worktrees/task-2-html work/task-1-core -b work/task-2-html
git worktree add worktrees/task-3-markdown work/task-1-core -b work/task-3-markdown
git worktree add worktrees/task-4-tui work/task-1-core -b work/task-4-tui

echo ""
echo "=== Phase 2 Ready ==="
echo ""
echo "Launch these in SEPARATE TERMINALS (they can run in parallel):"
echo ""
echo "  Terminal 1: ./scripts/worker-2-html.sh"
echo "  Terminal 2: ./scripts/worker-3-markdown.sh"
echo "  Terminal 3: ./scripts/worker-4-tui.sh"
echo ""
echo "Monitor progress with:"
echo "  watch -n 5 './scripts/check-progress.sh'"
echo ""
