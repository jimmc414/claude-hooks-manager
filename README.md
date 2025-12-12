# Claude Hooks Manager

A CLI tool to manage Claude Code hooks with enable/disable functionality without removing them.

## Features

- **Enable/Disable hooks** without deleting them
- **List hooks** with status (enabled/disabled)
- **Add hooks** interactively or via command line
- **Import/Export** hooks for backup or sharing
- **Validate** settings.json for issues
- **Visualize extensions** - see all skills, commands, and hooks in multiple formats
- **Smart name resolution** - use short names when unambiguous
- **Global and project scope** support
- **No dependencies** - Python 3.8+ stdlib only

## Installation

### Quick Install (Copy & Paste)

```bash
# Clone the repository
git clone https://github.com/jimmc414/claude-hooks-manager.git
cd claude-hooks-manager

# Install the hooks manager
mkdir -p ~/.claude
cp hooks_manager.py ~/.claude/
chmod +x ~/.claude/hooks_manager.py

# Install the slash command (recommended)
mkdir -p ~/.claude/commands
cp commands/hooks.md ~/.claude/commands/
```

### Manual Install

1. **Download** `hooks_manager.py` from this repository

2. **Copy to Claude directory:**
   ```bash
   mkdir -p ~/.claude
   cp hooks_manager.py ~/.claude/
   ```

3. **Make executable (Unix/macOS/WSL):**
   ```bash
   chmod +x ~/.claude/hooks_manager.py
   ```

4. **Install slash command (optional but recommended):**
   ```bash
   mkdir -p ~/.claude/commands
   cp commands/hooks.md ~/.claude/commands/
   ```

### Verify Installation

```bash
python3 ~/.claude/hooks_manager.py --version
python3 ~/.claude/hooks_manager.py events
```

### Windows Notes

On Windows without WSL, use:
```powershell
# Create directories
mkdir "$env:USERPROFILE\.claude" -Force
mkdir "$env:USERPROFILE\.claude\commands" -Force

# Copy files
copy hooks_manager.py "$env:USERPROFILE\.claude\"
copy commands\hooks.md "$env:USERPROFILE\.claude\commands\"

# Run with
python "%USERPROFILE%\.claude\hooks_manager.py" list
```

## Usage

This tool can be used two ways:
1. **In Claude Code** - via the `/hooks` slash command
2. **In Terminal** - via `python3 ~/.claude/hooks_manager.py`

Each example below shows both methods side-by-side.

---

### List Hooks

**In Claude Code:**
```
/hooks list
/hooks --global list
/hooks --project list
/hooks --json list
/hooks --quiet list
```

**In Terminal:**
```bash
python3 ~/.claude/hooks_manager.py list
python3 ~/.claude/hooks_manager.py --global list
python3 ~/.claude/hooks_manager.py --project list
python3 ~/.claude/hooks_manager.py --json list
python3 ~/.claude/hooks_manager.py --quiet list
```

---

### Enable/Disable Hooks

**In Claude Code:**
```
/hooks enable lint
/hooks disable lint
/hooks disable PostToolUse:lint
/hooks enable-all
/hooks --force disable-all
```

**In Terminal:**
```bash
python3 ~/.claude/hooks_manager.py enable lint
python3 ~/.claude/hooks_manager.py disable lint
python3 ~/.claude/hooks_manager.py disable PostToolUse:lint
python3 ~/.claude/hooks_manager.py enable-all
python3 ~/.claude/hooks_manager.py --force disable-all
```

---

### Create Hooks

**In Claude Code:**
```
/hooks create --name lint --event PostToolUse --matcher "Write|Edit" --command "npm run lint"
/hooks create --name test --event PostToolUse --matcher Write --command "pytest" --timeout 120
/hooks create --name format --event PostToolUse --matcher Write --command "prettier --write ."
/hooks add --name notify --event Notification --matcher "*" --command "notify-send Claude"
```

**In Terminal:**
```bash
python3 ~/.claude/hooks_manager.py create --name lint --event PostToolUse --matcher "Write|Edit" --command "npm run lint"
python3 ~/.claude/hooks_manager.py create --name test --event PostToolUse --matcher Write --command "pytest" --timeout 120
python3 ~/.claude/hooks_manager.py create --name format --event PostToolUse --matcher Write --command "prettier --write ."
python3 ~/.claude/hooks_manager.py add --name notify --event Notification --matcher "*" --command "notify-send Claude"

# Interactive mode (terminal only):
python3 ~/.claude/hooks_manager.py create
# Prompts for: event type, name, matcher, command, timeout
```

**Required flags:**
- `--name` - Hook identifier (used for enable/disable/remove)
- `--event` - Event type (use `events` command to see options)
- `--command` - Shell command to execute

**Optional flags:**
- `--matcher` - Tool pattern to match (default: `*` matches all)
- `--timeout` - Seconds before timeout (default: 60)

---

### Remove Hooks

**In Claude Code:**
```
/hooks --force remove lint
/hooks --force remove-all
/hooks --dry-run remove lint
```

**In Terminal:**
```bash
python3 ~/.claude/hooks_manager.py --force remove lint
python3 ~/.claude/hooks_manager.py --force remove-all
python3 ~/.claude/hooks_manager.py --dry-run remove lint
```

---

### Show Hook Details

**In Claude Code:**
```
/hooks show lint
/hooks --json show lint
```

**In Terminal:**
```bash
python3 ~/.claude/hooks_manager.py show lint
python3 ~/.claude/hooks_manager.py --json show lint
```

---

### Validate & Inspect

**In Claude Code:**
```
/hooks validate
/hooks --json validate
/hooks events
/hooks --json events
```

**In Terminal:**
```bash
python3 ~/.claude/hooks_manager.py validate
python3 ~/.claude/hooks_manager.py --json validate
python3 ~/.claude/hooks_manager.py events
python3 ~/.claude/hooks_manager.py --json events
```

---

### Import/Export

**In Claude Code:**
```
/hooks export hooks_backup.json
/hooks export
/hooks --force import hooks_backup.json
```

**In Terminal:**
```bash
python3 ~/.claude/hooks_manager.py export hooks_backup.json
python3 ~/.claude/hooks_manager.py export                      # outputs to stdout
python3 ~/.claude/hooks_manager.py export > hooks_backup.json  # redirect to file
python3 ~/.claude/hooks_manager.py --force import hooks_backup.json
```

---

### Visualize Extensions

See all your Claude Code extensions (skills, commands, and hooks) in one view.

**In Claude Code:**
```
/hooks visualize
/hooks visualize --format terminal
/hooks visualize --format html
/hooks visualize --format markdown
/hooks visualize --format tui
/hooks visualize -f html -o report.html
/hooks visualize -f markdown -o EXTENSIONS.md
/hooks visualize --format terminal --output extensions.txt
```

**In Terminal:**
```bash
python3 ~/.claude/hooks_manager.py visualize
python3 ~/.claude/hooks_manager.py visualize --format terminal
python3 ~/.claude/hooks_manager.py visualize --format html
python3 ~/.claude/hooks_manager.py visualize --format markdown
python3 ~/.claude/hooks_manager.py visualize --format tui
python3 ~/.claude/hooks_manager.py visualize -f html -o report.html
python3 ~/.claude/hooks_manager.py visualize -f markdown -o EXTENSIONS.md
python3 ~/.claude/hooks_manager.py visualize --format terminal --output extensions.txt

# Redirect markdown to file:
python3 ~/.claude/hooks_manager.py visualize -f markdown > EXTENSIONS.md
```

**Output Formats:**

| Format | Flag | Description | Default Output |
|--------|------|-------------|----------------|
| `terminal` | `-f terminal` | Colored tree view | stdout |
| `html` | `-f html` | Standalone HTML with dark mode | `claude-extensions.html` |
| `markdown` | `-f markdown` | Tables for docs/reports | stdout |
| `tui` | `-f tui` | Interactive curses UI | interactive |

**Visualize Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--format FORMAT` | `-f` | Output format (terminal/html/markdown/tui) |
| `--output FILE` | `-o` | Write to specific file |

---

### Important: Flag Ordering

Global flags (`--json`, `--force`, `--global`, etc.) must come **before** the command:

```bash
# Correct:
python3 ~/.claude/hooks_manager.py --json list
python3 ~/.claude/hooks_manager.py --force disable lint
python3 ~/.claude/hooks_manager.py --global --json list

# Wrong (will NOT work):
python3 ~/.claude/hooks_manager.py list --json
```

---

## Command Reference

### Commands

| Command | Description |
|---------|-------------|
| `list` | Show all hooks with status |
| `show <name>` | Display details of specific hook |
| `create` | Create a new hook (use flags) |
| `add` | Alias for `create` |
| `enable <name>` | Enable a disabled hook |
| `disable <name>` | Disable an active hook |
| `enable-all` | Enable all disabled hooks |
| `disable-all` | Disable all active hooks |
| `remove <name>` | Delete a hook permanently |
| `remove-all` | Delete ALL hooks |
| `validate` | Check settings.json syntax |
| `events` | List available hook event types |
| `export [file]` | Export hooks to JSON file |
| `import <file>` | Import hooks from JSON file |
| `visualize` | Show all extensions (skills, commands, hooks) |

### Global Flags

| Flag | Short | Description |
|------|-------|-------------|
| `--global` | `-g` | Target ~/.claude/settings.json |
| `--project` | `-p` | Target ./.claude/settings.json |
| `--json` | | Output in JSON format |
| `--quiet` | `-q` | Minimal output (names only) |
| `--dry-run` | | Preview changes without applying |
| `--no-color` | | Disable colored output |
| `--no-backup` | | Skip creating backup before modification |
| `--force` | `-f` | Skip confirmation prompts |
| `--version` | | Show version number |
| `--help` | `-h` | Show help message |

## How It Works

### Hook Storage

Active hooks are stored in `settings.json` under the `hooks` key:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "_name": "lint",
        "matcher": "Write|Edit",
        "hooks": [{ "type": "command", "command": "npm run lint" }]
      }
    ]
  }
}
```

Disabled hooks are moved to `_disabled_hooks` (ignored by Claude Code):

```json
{
  "_disabled_hooks": {
    "PostToolUse": [
      {
        "_name": "lint",
        "matcher": "Write|Edit",
        "hooks": [{ "type": "command", "command": "npm run lint" }]
      }
    ]
  }
}
```

### Hook Naming

The tool uses a `_name` field to identify hooks:
- If present, uses the specified name
- If missing, auto-generates as `EventType#index` (e.g., `PostToolUse#0`)
- Names are case-insensitive

### Name Resolution

When specifying a hook name:
- If unique across all events: use just the name (`lint`)
- If the same name exists in multiple events: use `Event:name` format (`PostToolUse:lint`)
- In interactive mode, you'll be prompted to select if ambiguous

## Supported Hook Events

| Event | Description | Supports |
|-------|-------------|----------|
| PreToolUse | Before tool execution | matcher, prompt |
| PostToolUse | After tool completion | matcher |
| Notification | When Claude sends alerts | matcher |
| Stop | When agent finishes | prompt |
| PermissionRequest | Permission dialog shown | matcher, prompt |
| UserPromptSubmit | Before prompt processing | - |
| SessionStart | Session initialization | matcher |
| SessionEnd | Session cleanup | - |

## Requirements

- Python 3.8+
- No external dependencies (stdlib only)

## License

MIT License - see [LICENSE](LICENSE)
