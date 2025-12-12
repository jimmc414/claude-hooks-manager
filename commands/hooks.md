---
description: Manage Claude Code hooks (create/enable/disable/list/remove)
argument-hint: [list|create|enable|disable|remove|validate|events] [name] [--global|--project|--json|--force]
allowed-tools: Bash(python3:*)
---

Run the hooks manager with the provided arguments:

```bash
python3 ~/.claude/hooks_manager.py $ARGUMENTS
```

---

## Quick Reference

**Commands:**
- `list` - Show all hooks with enabled/disabled status
- `show <name>` - Display details of a specific hook
- `create` - Create a new hook (use flags: --name, --event, --command, --matcher)
- `enable <name>` - Enable a disabled hook
- `disable <name>` - Disable an active hook
- `enable-all` / `disable-all` - Bulk enable/disable
- `remove <name>` / `remove-all` - Delete hooks permanently
- `validate` - Check settings.json for issues
- `events` - List available hook event types
- `export [file]` / `import <file>` - Backup and restore hooks

**Global flags (must come BEFORE the command):**
- `--global/-g` - Target ~/.claude/settings.json
- `--project/-p` - Target ./.claude/settings.json
- `--json` - Output in JSON format
- `--force/-f` - Skip confirmation prompts
- `--dry-run` - Preview changes without applying

---

## Event Types - When to Use Each

| Event | When It Fires | Best For |
|-------|---------------|----------|
| `PostToolUse` | After Claude edits/writes files | Linting, formatting, tests |
| `PreToolUse` | Before Claude runs a tool | Blocking dangerous commands |
| `Notification` | When Claude sends alerts | Desktop notifications, sounds |
| `Stop` | When Claude finishes a task | Summary notifications, cleanup |
| `SessionStart` | When a session begins | Environment setup |
| `SessionEnd` | When a session ends | Cleanup, logging |

**Most common:** `PostToolUse` for automated code quality checks.

---

## Matcher Patterns

| Pattern | Matches | Use Case |
|---------|---------|----------|
| `*` | All tools | Catch-all hooks |
| `Write` | File creation | New file hooks |
| `Edit` | File modification | Change hooks |
| `Write\|Edit` | Both write and edit | Code quality (most common) |
| `Bash` | Shell commands | Command validation |
| `Read` | File reads | Audit logging |

---

## Common Hook Recipes

### 1. Auto-lint after code changes
```
/hooks create --name lint --event PostToolUse --matcher "Write|Edit" --command "npm run lint --fix"
```

### 2. Run tests after edits
```
/hooks create --name test --event PostToolUse --matcher "Write|Edit" --command "npm test"
```

### 3. Format code with Prettier
```
/hooks create --name format --event PostToolUse --matcher "Write|Edit" --command "npx prettier --write ."
```

### 4. Python: Black + pytest
```
/hooks create --name black --event PostToolUse --matcher "Write|Edit" --command "black ."
/hooks create --name pytest --event PostToolUse --matcher "Write|Edit" --command "pytest -x"
```

### 5. Desktop notification when done
```
/hooks create --name notify --event Stop --command "notify-send 'Claude' 'Task completed'"
```

### 6. Rust: cargo check
```
/hooks create --name cargo-check --event PostToolUse --matcher "Write|Edit" --command "cargo check"
```

### 7. Go: go fmt + go vet
```
/hooks create --name go-fmt --event PostToolUse --matcher "Write|Edit" --command "go fmt ./... && go vet ./..."
```

---

## Helping Users

**If user asks "what hooks should I create?"** - Ask about their:
1. Language/framework (suggests linter/formatter)
2. Whether they want auto-tests
3. If they want notifications

**If user asks "why isn't my hook working?"** - Run:
1. `/hooks list` - Check if it's enabled
2. `/hooks show <name>` - Verify the matcher and command
3. `/hooks validate` - Check for config issues

**If user asks about a specific language**, suggest:
- JavaScript/TypeScript: ESLint, Prettier, Jest
- Python: Black, Ruff, pytest
- Rust: cargo check, cargo clippy, cargo test
- Go: go fmt, go vet, go test

**If user wants to temporarily disable hooks:**
```
/hooks --force disable-all
```
Then re-enable later with `/hooks enable-all`

---

## Examples

```
/hooks list                     # See all hooks
/hooks --json list              # JSON output for scripting
/hooks create --name lint --event PostToolUse --matcher "Write|Edit" --command "npm run lint"
/hooks disable lint             # Temporarily disable
/hooks enable lint              # Re-enable
/hooks --force remove lint      # Delete permanently
/hooks validate                 # Check for issues
/hooks events                   # See all event types
```

---

If an error occurs, explain what went wrong and suggest fixes.
Note: The `create` command in interactive mode requires terminal access - use the flags version via slash command.
