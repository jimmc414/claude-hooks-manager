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
git clone https://github.com/YOUR_USERNAME/claude-hooks-manager.git
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

### List Hooks

```bash
# List all hooks (auto-detects global vs project)
python ~/.claude/hooks_manager.py list

# List global hooks only
python ~/.claude/hooks_manager.py list --global

# List project hooks only
python ~/.claude/hooks_manager.py list --project

# Output as JSON
python ~/.claude/hooks_manager.py list --json
```

### Enable/Disable Hooks

```bash
# Disable a hook by name
python ~/.claude/hooks_manager.py disable lint

# Enable a hook
python ~/.claude/hooks_manager.py enable lint

# Use Event:name format if the same name exists in multiple events
python ~/.claude/hooks_manager.py disable PostToolUse:lint

# Disable all hooks
python ~/.claude/hooks_manager.py disable-all

# Enable all hooks
python ~/.claude/hooks_manager.py enable-all
```

### Add Hooks

```bash
# Interactive mode
python ~/.claude/hooks_manager.py add

# Non-interactive with flags
python ~/.claude/hooks_manager.py add \
  --name lint \
  --event PostToolUse \
  --matcher "Write|Edit" \
  --command "npm run lint" \
  --timeout 60
```

### Remove Hooks

```bash
# Remove a single hook (with confirmation)
python ~/.claude/hooks_manager.py remove lint

# Remove without confirmation
python ~/.claude/hooks_manager.py remove lint --force

# Remove all hooks (requires confirmation)
python ~/.claude/hooks_manager.py remove-all
```

### Show Hook Details

```bash
python ~/.claude/hooks_manager.py show lint
```

### Validate Settings

```bash
python ~/.claude/hooks_manager.py validate
```

### List Available Events

```bash
python ~/.claude/hooks_manager.py events
```

### Import/Export

```bash
# Export to file
python ~/.claude/hooks_manager.py export hooks_backup.json

# Export to stdout
python ~/.claude/hooks_manager.py export

# Import from file
python ~/.claude/hooks_manager.py import hooks_backup.json
```

## Command Line Options

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

### Commands

| Command | Description |
|---------|-------------|
| `list` | Show all hooks with status |
| `show <name>` | Display details of specific hook |
| `enable <name>` | Enable a disabled hook |
| `disable <name>` | Disable an active hook |
| `enable-all` | Enable all disabled hooks |
| `disable-all` | Disable all active hooks |
| `remove <name>` | Delete a hook permanently |
| `remove-all` | Delete ALL hooks |
| `add` | Add new hook |
| `validate` | Check settings.json syntax |
| `events` | List available hook event types |
| `export [file]` | Export hooks to JSON file |
| `import <file>` | Import hooks from JSON file |

## Slash Command Usage

If you installed the slash command (`commands/hooks.md`), you can use it directly within Claude Code conversations:

### Basic Commands
```
/hooks list
/hooks list --json
/hooks events
/hooks validate
```

### Managing Hooks
```
/hooks disable lint --force
/hooks enable lint
/hooks enable PostToolUse:lint --project
/hooks remove slow-tests --force
```

### Adding Hooks via Slash Command
Since the slash command runs non-interactively, use flags:
```
/hooks add --name lint --event PostToolUse --matcher "Write|Edit" --command "npm run lint"
/hooks add --name test --event PostToolUse --matcher Write --command "pytest" --timeout 120
```

### Important: Flag Ordering
Global flags must come **before** the command name:
```
/hooks --json list           # Correct
/hooks --force disable lint  # Correct
/hooks list --json           # Will NOT work
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
