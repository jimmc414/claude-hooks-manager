# Preparation for Run 2

## Changes from Run 1

| Aspect | Run 1 | Run 2 |
|--------|-------|-------|
| File structure | Single file (hooks_manager.py) | Separate modules (renderers/*.py) |
| Worker launch | Copy-paste prompts | Shell scripts |
| CLI invocation | `claude -p "prompt"` (broken) | `claude "prompt"` (works) |
| Monitoring | Manual git log | `check-progress.sh` script |

## Pre-Flight Checklist

- [x] Skill patches applied to parallel-orchestrator
- [x] Skill patches applied to parallel-retrospective
- [x] Launch scripts created in `scripts/`
- [x] File scope validated (each worker owns exclusive files)
- [x] CLI invocation pattern confirmed working

## File Ownership Map

| Worker | Exclusive Files | Shared (Read-Only) |
|--------|-----------------|-------------------|
| Worker 1 | hooks_manager.py, renderers/__init__.py, renderers/base.py, renderers/terminal.py | - |
| Worker 2 | renderers/html.py | renderers/base.py |
| Worker 3 | renderers/markdown.py | renderers/base.py |
| Worker 4 | renderers/tui.py | renderers/base.py |

## Execution Order

### Phase 1: Core Infrastructure
```bash
./scripts/setup-worktrees.sh
./scripts/worker-1-core.sh
# Wait for [COMPLETE] commit
```

### Phase 2: Parallel Renderers
```bash
./scripts/setup-phase2.sh

# In 3 separate terminals (can run simultaneously):
./scripts/worker-2-html.sh
./scripts/worker-3-markdown.sh
./scripts/worker-4-tui.sh
```

### Phase 3: Monitor & Integrate
```bash
# Monitor progress
watch -n 5 './scripts/check-progress.sh'

# After all [COMPLETE], integrate
git checkout -b integration/visualize-v2 master
git merge work/task-1-core --no-ff -m "Merge task-1: Core infrastructure"
git merge work/task-2-html --no-ff -m "Merge task-2: HTMLRenderer"
git merge work/task-3-markdown --no-ff -m "Merge task-3: MarkdownRenderer"
git merge work/task-4-tui --no-ff -m "Merge task-4: TUIRenderer"
```

## Expected Outcome

- **Merge conflicts**: 0 (exclusive file ownership)
- **Total commits**: ~8-12 (2-3 per worker)
- **Duration**: ~30-40 minutes

## Known Risks

| Risk | Mitigation |
|------|------------|
| Worker fails to create renderers/ directory | Worker 1 prompt explicitly includes this task |
| Base class interface mismatch | Worker 1 creates base.py, Workers 2-4 read it first |
| CLI invocation fails again | Launch scripts use confirmed working pattern |

## Rollback Plan

If Run 2 fails:
```bash
# Abort integration
git merge --abort
git checkout master

# Remove worktrees
rm -rf worktrees
git worktree prune

# Delete branches
git branch -D work/task-1-core work/task-2-html work/task-3-markdown work/task-4-tui

# Review what went wrong
# Update scripts/skills accordingly
```
