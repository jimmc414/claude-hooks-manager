# Claude Hooks Manager - Implementation Plan

A CLI tool to manage Claude Code hooks with enable/disable functionality without removing them.

---

## Project Structure

```
claude-hooks-manager/
├── hooks_manager.py      # Main CLI tool (single file, no dependencies)
├── commands/
│   └── hooks.md          # Slash command template (copy to .claude/commands/)
├── README.md             # Installation & usage guide
├── LICENSE               # MIT
└── examples/
    └── settings.json     # Example settings with hooks
```

---

## Core Features

### Scope Options (Global vs Project)

| Flag | Target | Path |
|------|--------|------|
| `--global` / `-g` | User settings | `~/.claude/settings.json` |
| `--project` / `-p` | Project settings | `./.claude/settings.json` |
| (default) | Auto-detect | Project if exists, else global |

### Commands

| Command | Description |
|---------|-------------|
| `list` | Show all hooks with enabled/disabled status |
| `enable <name>` | Enable a specific hook by name |
| `disable <name>` | Disable a specific hook by name |
| `enable-all` | Enable all disabled hooks |
| `disable-all` | Disable all active hooks |
| `remove <name>` | Permanently delete a hook |
| `remove-all` | Permanently delete ALL hooks (requires `--confirm`) |
| `add` | Interactive hook creation |
| `export` | Export hooks to standalone JSON file |
| `import <file>` | Import hooks from JSON file |

### Example Usage

```bash
# List all hooks (auto-detect scope)
python hooks_manager.py list

# List global hooks only
python hooks_manager.py list --global

# List project hooks only
python hooks_manager.py list --project

# Disable a hook in global settings
python hooks_manager.py disable lint --global

# Enable a hook in project settings
python hooks_manager.py enable pre-commit --project

# Disable all hooks globally
python hooks_manager.py disable-all --global

# Remove all hooks (requires confirmation)
python hooks_manager.py remove-all --confirm

# Interactive add
python hooks_manager.py add --global
```

---

## Technical Design

### Hook Storage Structure

**Active hooks** (read by Claude Code):
```json
{
  "hooks": {
    "PreToolUse": [...],
    "PostToolUse": [...],
    "Notification": [...],
    "Stop": [...]
  }
}
```

**Disabled hooks** (ignored by Claude Code):
```json
{
  "_disabled_hooks": {
    "PreToolUse": [...],
    "PostToolUse": [...],
    "Notification": [...],
    "Stop": [...]
  }
}
```

### Hook Naming Convention

Since hooks don't have built-in names, we'll add a `_name` field:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "_name": "lint",
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "npm run lint"
          }
        ]
      }
    ]
  }
}
```

- `_name` is ignored by Claude Code (unknown nested field in array item)
- Used by our tool to identify hooks
- Auto-generated if not present (e.g., "PostToolUse-0", "PostToolUse-1")

### Settings File Handling

1. **Read**: Load JSON, preserve all existing keys
2. **Modify**: Move hooks between `hooks` and `_disabled_hooks`
3. **Write**: Pretty-print JSON with 2-space indent, preserve key order

### Error Handling

- Missing settings file: Create with empty hooks structure
- Invalid JSON: Error with line number
- Hook not found: List available hooks
- Permission denied: Suggest sudo or check path

---

## Slash Command Integration

### File: `commands/hooks.md`

```markdown
---
description: Manage Claude Code hooks (enable/disable/list)
argument-hint: [list|enable|disable|enable-all|disable-all|remove] [hook-name] [--global|--project]
allowed-tools: Bash(python3:*)
---

Run the hooks manager with the provided arguments:

python3 ~/.claude/hooks_manager.py $ARGUMENTS

Report the results to me. If listing, format the output nicely.
If an error occurs, explain what went wrong and suggest fixes.
```

### Installation Location

User copies `hooks.md` to either:
- `~/.claude/commands/hooks.md` (available in all projects)
- `.claude/commands/hooks.md` (project-specific)

---

## CLI Implementation Details

### Dependencies

- **None** - stdlib only (`json`, `argparse`, `pathlib`, `os`, `sys`)

### Python Version

- Target: Python 3.8+ (broad compatibility)

### Argument Parser Structure

```python
parser = argparse.ArgumentParser(description="Manage Claude Code hooks")
parser.add_argument("--global", "-g", dest="global_scope", action="store_true")
parser.add_argument("--project", "-p", dest="project_scope", action="store_true")

subparsers = parser.add_subparsers(dest="command", required=True)

# list
list_parser = subparsers.add_parser("list", help="List all hooks")

# enable
enable_parser = subparsers.add_parser("enable", help="Enable a hook")
enable_parser.add_argument("name", help="Hook name")

# disable
disable_parser = subparsers.add_parser("disable", help="Disable a hook")
disable_parser.add_argument("name", help="Hook name")

# enable-all
enable_all_parser = subparsers.add_parser("enable-all", help="Enable all hooks")

# disable-all
disable_all_parser = subparsers.add_parser("disable-all", help="Disable all hooks")

# remove
remove_parser = subparsers.add_parser("remove", help="Remove a hook")
remove_parser.add_argument("name", help="Hook name")

# remove-all
remove_all_parser = subparsers.add_parser("remove-all", help="Remove all hooks")
remove_all_parser.add_argument("--confirm", action="store_true", required=True)

# add
add_parser = subparsers.add_parser("add", help="Add a new hook interactively")
```

### Key Functions

```python
def get_settings_path(global_scope: bool, project_scope: bool) -> Path:
    """Determine which settings.json to use"""

def load_settings(path: Path) -> dict:
    """Load settings.json, return empty dict if missing"""

def save_settings(path: Path, settings: dict) -> None:
    """Write settings.json with pretty formatting"""

def get_hook_name(hook: dict, event_type: str, index: int) -> str:
    """Get or generate hook name"""

def list_hooks(settings: dict) -> list[dict]:
    """Return all hooks with metadata (name, event, enabled)"""

def enable_hook(settings: dict, name: str) -> bool:
    """Move hook from _disabled_hooks to hooks"""

def disable_hook(settings: dict, name: str) -> bool:
    """Move hook from hooks to _disabled_hooks"""

def remove_hook(settings: dict, name: str) -> bool:
    """Delete hook from either location"""
```

---

## Output Format

### List Command

```
Global hooks (~/.claude/settings.json):

  ENABLED:
    [PostToolUse] lint (matcher: Write|Edit)
    [PreToolUse] confirm-bash (matcher: Bash)

  DISABLED:
    [PostToolUse] slow-tests (matcher: Write)

Project hooks (.claude/settings.json):

  ENABLED:
    [Notification] alert (matcher: *)

  DISABLED:
    (none)
```

### Enable/Disable Output

```
Enabled hook 'lint' in ~/.claude/settings.json
```

```
Disabled hook 'lint' in ~/.claude/settings.json
```

### Remove Output

```
Removed hook 'lint' from ~/.claude/settings.json
```

### Remove-All Output

```
Removed 5 hooks from ~/.claude/settings.json:
  - lint (PostToolUse)
  - confirm-bash (PreToolUse)
  - slow-tests (PostToolUse, disabled)
  - alert (Notification)
  - logger (Stop)
```

---

## README.md Outline

1. **Overview** - What it does, why it's useful
2. **Installation**
   - Clone repo
   - Copy `hooks_manager.py` to `~/.claude/`
   - Copy `commands/hooks.md` to `~/.claude/commands/`
3. **Usage**
   - All commands with examples
   - Scope options explained
4. **How It Works**
   - `_disabled_hooks` storage
   - `_name` field convention
5. **Slash Command Usage**
   - `/hooks list`
   - `/hooks disable lint --global`
6. **Examples**
   - Common workflows
7. **Contributing**
8. **License**

---

## Implementation Order

1. [ ] Create `hooks_manager.py` with core CLI structure
2. [ ] Implement `list` command
3. [ ] Implement `enable` / `disable` commands
4. [ ] Implement `enable-all` / `disable-all` commands
5. [ ] Implement `remove` / `remove-all` commands
6. [ ] Implement `add` command (interactive)
7. [ ] Add `export` / `import` commands
8. [ ] Create slash command template
9. [ ] Write README.md
10. [ ] Create example settings.json
11. [ ] Add LICENSE (MIT)
12. [ ] Test all commands manually
13. [ ] Optional: Add unit tests

---

## Future Enhancements (Out of Scope)

- [ ] Backup before modification (`--backup` flag)
- [ ] Hook templates library
- [ ] Sync hooks between global/project
- [ ] Hook validation against Claude Code schema
- [ ] Shell completion scripts (bash/zsh/fish)
