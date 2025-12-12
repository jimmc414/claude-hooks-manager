#!/bin/bash
# Worker 1: Core infrastructure (dataclasses, scanner, CLI integration)
# Creates: hooks_manager.py modifications + renderers/ directory structure

cd /mnt/c/python/claude-hooks-manager/worktrees/task-1-core

claude --dangerously-skip-permissions "Worker 1: Set up core visualization infrastructure.

Branch: work/task-1-core (verify with: git branch)

Tasks:
1. Create renderers/ directory with __init__.py
2. Add dataclasses to hooks_manager.py: SkillInfo(name,description,triggers,path), CommandInfo(name,description,path), ExtensionsData(skills,commands,hooks)
3. Add ExtensionScanner class to hooks_manager.py: scan ~/.claude/skills/*/SKILL.md, ~/.claude/commands/*.md, settings.json hooks
4. Create renderers/base.py with abstract BaseRenderer class
5. Create renderers/terminal.py with TerminalRenderer (tree output, uses Colors)
6. Add 'visualize' CLI command to hooks_manager.py with --format, --output, --no-color flags
7. Wire up terminal renderer as default

Commit after each major task with [CHECKPOINT] prefix. Final commit: [COMPLETE].
Start: git branch, then implement step by step."
