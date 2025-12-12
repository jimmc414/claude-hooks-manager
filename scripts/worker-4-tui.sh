#!/bin/bash
# Worker 4: TUI Renderer (curses-based interactive)
# Creates: renderers/tui.py (exclusive ownership)

cd /mnt/c/python/claude-hooks-manager/worktrees/task-4-tui

claude --dangerously-skip-permissions "Worker 4: Create TUI renderer using curses (stdlib).

Branch: work/task-4-tui (verify with: git branch)

IMPORTANT: You own renderers/tui.py exclusively. Do NOT modify hooks_manager.py or other renderer files.

Tasks:
1. Read renderers/base.py to understand the BaseRenderer interface
2. Create renderers/tui.py with TUIRenderer class that extends BaseRenderer
3. Use curses (stdlib) for interactive terminal UI
4. Features:
   - Arrow key navigation between Skills/Commands/Hooks sections
   - Enter to expand/collapse sections
   - Detail view for selected items
   - q to quit
5. No external dependencies (curses is stdlib)

The CLI integration will be done by Worker 1. Just create the renderer module.

Commit with [CHECKPOINT] after basic curses setup, [COMPLETE] when navigation works.
Start: git branch, read base.py, then implement."
