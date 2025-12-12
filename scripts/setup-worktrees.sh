#!/bin/bash
# Orchestrator Setup Script
# Creates all worktrees for parallel workers

set -e

echo "=== Setting up parallel workflow ==="

# Clean up any existing worktrees
rm -rf worktrees 2>/dev/null || true
git worktree prune

# Create worktrees directory
mkdir -p worktrees

# Create worktree for Worker 1 (from master)
echo "Creating worktree for Worker 1 (core)..."
git worktree add worktrees/task-1-core -b work/task-1-core

echo ""
echo "=== Setup Complete ==="
echo ""
echo "PHASE 1: Run Worker 1 first (creates base infrastructure)"
echo "  ./scripts/worker-1-core.sh"
echo ""
echo "Wait for Worker 1 to commit [COMPLETE], then run:"
echo "  ./scripts/setup-phase2.sh"
echo ""
