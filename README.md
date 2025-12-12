# Claude Hooks Manager

A CLI tool to manage Claude Code hooks with enable/disable functionality without removing them.

## Features

- **Enable/Disable hooks** without deleting them
- **List hooks** with status (enabled/disabled)
- **Add hooks** interactively or via command line
- **Import/Export** hooks for backup or sharing
- **Validate** settings.json for issues
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

This tool is designed to be used via the `/hooks` slash command directly within Claude Code conversations. After installation, simply type `/hooks` followed by your command.

### List Hooks

```
/hooks list                    # List all hooks (auto-detects scope)
/hooks --global list           # List global hooks only
/hooks --project list          # List project hooks only
/hooks --json list             # Output as JSON
```

### Enable/Disable Hooks

```
/hooks disable lint            # Disable a hook by name
/hooks enable lint             # Enable a hook
/hooks disable PostToolUse:lint   # Use Event:name if name exists in multiple events
/hooks --force disable-all     # Disable all hooks (skip confirmation)
/hooks enable-all              # Enable all hooks
```

### Create Hooks

Use `create` (or its alias `add`) to make new hooks:

```
/hooks create --name lint --event PostToolUse --matcher "Write|Edit" --command "npm run lint"
/hooks create --name test --event PostToolUse --matcher Write --command "pytest" --timeout 120
/hooks create --name format --event PostToolUse --matcher Write --command "prettier --write ."
```

**Required flags:**
- `--name` - Hook identifier (used for enable/disable/remove)
- `--event` - Event type (use `/hooks events` to see options)
- `--command` - Shell command to execute

**Optional flags:**
- `--matcher` - Tool pattern to match (default: `*` matches all)
- `--timeout` - Seconds before timeout (default: 60)

### Remove Hooks

```
/hooks --force remove lint     # Remove a hook (skip confirmation)
/hooks --force remove-all      # Remove all hooks (skip confirmation)
```

### Show Hook Details

```
/hooks show lint               # Display details of a specific hook
```

### Validate & Inspect

```
/hooks validate                # Check settings.json for issues
/hooks events                  # List available hook event types
```

### Import/Export

```
/hooks export hooks_backup.json    # Export hooks to file
/hooks import hooks_backup.json    # Import hooks from file
```

### Important: Flag Ordering

Global flags (`--json`, `--force`, `--global`, etc.) must come **before** the command:

```
/hooks --json list             # Correct
/hooks --force disable lint    # Correct
/hooks list --json             # Will NOT work
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

### Global Flags

| Flag | Description |
|------|-------------|
| `--global`, `-g` | Target ~/.claude/settings.json |
| `--project`, `-p` | Target ./.claude/settings.json |
| `--json` | Output in JSON format |
| `--quiet`, `-q` | Minimal output (names only) |
| `--dry-run` | Preview changes without applying |
| `--no-color` | Disable colored output |
| `--no-backup` | Skip creating backup before modification |
| `--force`, `-f` | Skip confirmation prompts |

---

## Direct CLI Usage (Under the Hood)

The slash command runs `python3 ~/.claude/hooks_manager.py` with your arguments. You can also run it directly from the terminal:

```bash
# What /hooks list runs under the hood:
python3 ~/.claude/hooks_manager.py list

# What /hooks --json list runs:
python3 ~/.claude/hooks_manager.py --json list

# What /hooks --force disable lint runs:
python3 ~/.claude/hooks_manager.py --force disable lint

# What /hooks create --name lint --event PostToolUse --command "npm run lint" runs:
python3 ~/.claude/hooks_manager.py create --name lint --event PostToolUse --command "npm run lint"
```

### Interactive Mode (Terminal Only)

When running directly from a terminal (not via slash command), you can use interactive mode for creating hooks:

```bash
python3 ~/.claude/hooks_manager.py create
# Prompts for: event type, name, matcher, command, timeout
```

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
