#!/bin/bash
# Worker 3: Markdown Renderer
# Creates: renderers/markdown.py (exclusive ownership)

cd /mnt/c/python/claude-hooks-manager/worktrees/task-3-markdown

claude --dangerously-skip-permissions "Worker 3: Create Markdown renderer in its own module.

Branch: work/task-3-markdown (verify with: git branch)

IMPORTANT: You own renderers/markdown.py exclusively. Do NOT modify hooks_manager.py or other renderer files.

Tasks:
1. Read renderers/base.py to understand the BaseRenderer interface
2. Create renderers/markdown.py with MarkdownRenderer class that extends BaseRenderer
3. Generate markdown with:
   - Summary section with counts
   - Skills table (Name, Description, Location)
   - Commands table (Name, Description, Location)
   - Hooks table (Name, Event, Status, Matcher)
4. Escape pipe characters in table cells

The CLI integration will be done by Worker 1. Just create the renderer module.

Commit with [CHECKPOINT] after basic structure, [COMPLETE] when tables are complete.
Start: git branch, read base.py, then implement."
