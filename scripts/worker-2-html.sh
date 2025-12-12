#!/bin/bash
# Worker 2: HTML Renderer
# Creates: renderers/html.py (exclusive ownership)

cd /mnt/c/python/claude-hooks-manager/worktrees/task-2-html

claude --dangerously-skip-permissions "Worker 2: Create HTML renderer in its own module.

Branch: work/task-2-html (verify with: git branch)

IMPORTANT: You own renderers/html.py exclusively. Do NOT modify hooks_manager.py or other renderer files.

Tasks:
1. Read renderers/base.py to understand the BaseRenderer interface
2. Create renderers/html.py with HTMLRenderer class that extends BaseRenderer
3. Generate standalone HTML with embedded CSS
4. Include collapsible sections for Skills, Commands, Hooks
5. Style with modern CSS (dark mode friendly)

The CLI integration will be done by Worker 1. Just create the renderer module.

Commit with [CHECKPOINT] after basic structure, [COMPLETE] when fully styled.
Start: git branch, read base.py, then implement."
