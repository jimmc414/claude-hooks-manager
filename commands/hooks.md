---
description: Manage Claude Code hooks (enable/disable/list/add/remove)
argument-hint: [list|show|enable|disable|add|remove|validate|events] [name] [--global|--project|--json|--force]
allowed-tools: Bash(python3:*)
---

Run the hooks manager with the provided arguments:

```bash
python3 ~/.claude/hooks_manager.py $ARGUMENTS
```

**Available commands:**
- `list` - Show all hooks with enabled/disabled status
- `show <name>` - Display details of a specific hook
- `enable <name>` - Enable a disabled hook
- `disable <name>` - Disable an active hook
- `enable-all` - Enable all disabled hooks
- `disable-all` - Disable all active hooks
- `remove <name>` - Permanently delete a hook
- `remove-all` - Permanently delete ALL hooks
- `add` - Add a new hook (use flags: --name, --event, --command, --matcher)
- `validate` - Check settings.json for issues
- `events` - List available hook event types
- `export [file]` - Export hooks to JSON
- `import <file>` - Import hooks from JSON

**Options:**
- `--global/-g` - Target global settings (~/.claude/settings.json)
- `--project/-p` - Target project settings (./.claude/settings.json)
- `--json` - Output in JSON format
- `--force/-f` - Skip confirmation prompts
- `--dry-run` - Preview changes without applying
- `--quiet/-q` - Minimal output

**Examples:**
- `/hooks list` - List all hooks
- `/hooks list --json` - List hooks in JSON format
- `/hooks disable lint --force` - Disable hook without confirmation
- `/hooks add --name test --event PostToolUse --matcher Write --command "pytest"` - Add a hook

If an error occurs, explain what went wrong and suggest fixes.
Note: The `add` command in interactive mode requires terminal access - use the flags version via slash command.
