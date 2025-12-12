#!/usr/bin/env python3
"""
Claude Code Hooks Manager - CLI tool to manage Claude Code hooks.

Enable, disable, list, and manage hooks without removing them from settings.json.
Supports both global (~/.claude/settings.json) and project (./.claude/settings.json) scopes.
"""

import argparse
import json
import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

__version__ = "1.0.0"

# All Claude Code hook event types
EVENT_TYPES = [
    "PreToolUse",
    "PostToolUse",
    "Notification",
    "Stop",
    "PermissionRequest",
    "UserPromptSubmit",
    "SessionStart",
    "SessionEnd",
]

# Event type descriptions for help
EVENT_INFO = {
    "PreToolUse": ("Before tool execution", "matcher, prompt"),
    "PostToolUse": ("After tool completion", "matcher"),
    "Notification": ("When Claude sends alerts", "matcher"),
    "Stop": ("When agent finishes", "prompt"),
    "PermissionRequest": ("Permission dialog shown", "matcher, prompt"),
    "UserPromptSubmit": ("Before prompt processing", ""),
    "SessionStart": ("Session initialization", "matcher"),
    "SessionEnd": ("Session cleanup", ""),
}

# ANSI color codes
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


@dataclass
class HookInfo:
    """Represents a single hook with metadata."""
    name: str
    event: str
    enabled: bool
    matcher: str
    commands: List[dict] = field(default_factory=list)
    raw: dict = field(default_factory=dict)


class HooksManager:
    """Main class for managing Claude Code hooks."""

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.use_color = self._should_use_color()
        self.settings_path = self._resolve_settings_path()
        self.settings = self._load_settings()

    def _should_use_color(self) -> bool:
        """Determine if color output should be used."""
        if getattr(self.args, 'no_color', False):
            return False
        # Auto-detect: color if stdout is a TTY
        return sys.stdout.isatty()

    def _color(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled."""
        if self.use_color:
            return f"{color}{text}{Colors.RESET}"
        return text

    def _resolve_settings_path(self) -> Path:
        """Determine which settings.json to use."""
        global_path = Path.home() / ".claude" / "settings.json"
        project_path = Path.cwd() / ".claude" / "settings.json"

        if getattr(self.args, 'global_scope', False):
            return global_path
        elif getattr(self.args, 'project_scope', False):
            return project_path
        else:
            # Auto-detect: project if exists, else global
            if project_path.exists():
                return project_path
            return global_path

    def _load_settings(self) -> dict:
        """Load settings.json, return empty dict structure if missing."""
        if not self.settings_path.exists():
            return {"hooks": {}, "_disabled_hooks": {}}

        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                # Ensure required keys exist
                if "hooks" not in settings:
                    settings["hooks"] = {}
                if "_disabled_hooks" not in settings:
                    settings["_disabled_hooks"] = {}
                return settings
        except json.JSONDecodeError as e:
            self._error(f"Invalid JSON in {self.settings_path}: {e}")
            sys.exit(1)

    def _save_settings(self) -> None:
        """Save settings.json with pretty formatting."""
        if getattr(self.args, 'dry_run', False):
            return

        # Create backup unless disabled
        if not getattr(self.args, 'no_backup', False) and self.settings_path.exists():
            backup_path = self.settings_path.with_suffix('.json.bak')
            shutil.copy2(self.settings_path, backup_path)

        # Ensure parent directory exists
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)

        # Clean up empty _disabled_hooks
        if not self.settings.get("_disabled_hooks"):
            self.settings.pop("_disabled_hooks", None)

        with open(self.settings_path, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=2, ensure_ascii=False)
            f.write('\n')

    def _get_hook_name(self, hook: dict, event: str, index: int) -> str:
        """Get or generate a hook name."""
        if "_name" in hook:
            return hook["_name"]
        # Auto-generate name from event and index
        return f"{event}#{index}"

    def _normalize_name(self, name: str) -> str:
        """Normalize hook name for case-insensitive comparison."""
        return name.lower()

    def _find_all_hooks(self) -> List[HookInfo]:
        """Find all hooks (enabled and disabled)."""
        hooks = []

        # Enabled hooks
        for event, event_hooks in self.settings.get("hooks", {}).items():
            if not isinstance(event_hooks, list):
                continue
            for idx, hook in enumerate(event_hooks):
                name = self._get_hook_name(hook, event, idx)
                matcher = hook.get("matcher", "*")
                commands = hook.get("hooks", [])
                hooks.append(HookInfo(
                    name=name,
                    event=event,
                    enabled=True,
                    matcher=matcher,
                    commands=commands,
                    raw=hook
                ))

        # Disabled hooks
        for event, event_hooks in self.settings.get("_disabled_hooks", {}).items():
            if not isinstance(event_hooks, list):
                continue
            for idx, hook in enumerate(event_hooks):
                name = self._get_hook_name(hook, event, idx)
                matcher = hook.get("matcher", "*")
                commands = hook.get("hooks", [])
                hooks.append(HookInfo(
                    name=name,
                    event=event,
                    enabled=False,
                    matcher=matcher,
                    commands=commands,
                    raw=hook
                ))

        return hooks

    def _find_hooks_by_name(self, name: str) -> List[HookInfo]:
        """Find hooks matching the given name (case-insensitive)."""
        all_hooks = self._find_all_hooks()
        normalized = self._normalize_name(name)

        # Check if name includes event prefix (e.g., "PostToolUse:lint")
        if ":" in name:
            event_part, name_part = name.split(":", 1)
            normalized_event = self._normalize_name(event_part)
            normalized_name = self._normalize_name(name_part)
            return [h for h in all_hooks
                    if self._normalize_name(h.name) == normalized_name
                    and self._normalize_name(h.event) == normalized_event]

        return [h for h in all_hooks if self._normalize_name(h.name) == normalized]

    def _resolve_hook(self, name: str) -> Optional[HookInfo]:
        """Resolve a hook name to a single hook, handling disambiguation."""
        matches = self._find_hooks_by_name(name)

        if not matches:
            self._error(f"No hook named '{name}' found")
            self._suggest_hooks(name)
            return None

        if len(matches) == 1:
            return matches[0]

        # Multiple matches - need disambiguation
        if getattr(self.args, 'force', False) or not sys.stdin.isatty():
            # Non-interactive: error with list
            self._error(f"Multiple hooks named '{name}' found. Specify event type:")
            for h in matches:
                print(f"  {h.event}:{h.name}")
            return None

        # Interactive: prompt user to select
        print(f"Multiple hooks named '{name}' found. Select one:")
        for i, h in enumerate(matches, 1):
            status = self._color("enabled", Colors.GREEN) if h.enabled else self._color("disabled", Colors.YELLOW)
            print(f"  [{i}] {h.event}:{h.name} ({status})")

        try:
            choice = input("Enter number (or 'q' to quit): ").strip()
            if choice.lower() == 'q':
                return None
            idx = int(choice) - 1
            if 0 <= idx < len(matches):
                return matches[idx]
        except (ValueError, EOFError):
            pass

        self._error("Invalid selection")
        return None

    def _suggest_hooks(self, name: str) -> None:
        """Suggest similar hook names."""
        all_hooks = self._find_all_hooks()
        if all_hooks:
            print("Available hooks:")
            for h in all_hooks:
                print(f"  {h.event}:{h.name}")

    def _error(self, message: str) -> None:
        """Print error message."""
        print(self._color(f"Error: {message}", Colors.RED), file=sys.stderr)

    def _success(self, message: str) -> None:
        """Print success message."""
        if not getattr(self.args, 'quiet', False):
            print(self._color(message, Colors.GREEN))

    def _info(self, message: str) -> None:
        """Print info message."""
        if not getattr(self.args, 'quiet', False):
            print(message)

    def _confirm(self, message: str) -> bool:
        """Ask for user confirmation."""
        if getattr(self.args, 'force', False):
            return True
        if not sys.stdin.isatty():
            self._error("Confirmation required. Use --force to skip.")
            return False

        try:
            response = input(f"{message} [y/N] ").strip().lower()
            return response in ('y', 'yes')
        except (EOFError, KeyboardInterrupt):
            return False

    def _output_json(self, data: Any) -> None:
        """Output data as JSON."""
        print(json.dumps(data, indent=2, ensure_ascii=False))

    # ==================== Commands ====================

    def cmd_list(self) -> int:
        """List all hooks with their status."""
        hooks = self._find_all_hooks()

        if getattr(self.args, 'json', False):
            data = {
                "scope": "project" if "./.claude" in str(self.settings_path) else "global",
                "path": str(self.settings_path),
                "hooks": [
                    {
                        "name": h.name,
                        "event": h.event,
                        "enabled": h.enabled,
                        "matcher": h.matcher,
                        "commands": h.commands
                    }
                    for h in hooks
                ]
            }
            self._output_json(data)
            return 0

        if getattr(self.args, 'quiet', False):
            for h in hooks:
                print(f"{h.event}:{h.name}")
            return 0

        # Human-readable output
        scope = "Project" if "./.claude" in str(self.settings_path) else "Global"
        print(f"{self._color(scope + ' hooks', Colors.BOLD)} ({self.settings_path}):\n")

        if not hooks:
            print("  (no hooks configured)")
            return 0

        enabled = [h for h in hooks if h.enabled]
        disabled = [h for h in hooks if not h.enabled]

        if enabled:
            print(f"  {self._color('ENABLED:', Colors.GREEN)}")
            for h in enabled:
                print(f"    [{h.event}] {self._color(h.name, Colors.BOLD)} (matcher: {h.matcher})")

        if disabled:
            if enabled:
                print()
            print(f"  {self._color('DISABLED:', Colors.YELLOW)}")
            for h in disabled:
                print(f"    [{h.event}] {self._color(h.name, Colors.BOLD)} (matcher: {h.matcher})")

        return 0

    def cmd_show(self) -> int:
        """Show details of a specific hook."""
        hook = self._resolve_hook(self.args.name)
        if not hook:
            return 1

        if getattr(self.args, 'json', False):
            self._output_json({
                "name": hook.name,
                "event": hook.event,
                "enabled": hook.enabled,
                "matcher": hook.matcher,
                "commands": hook.commands,
                "raw": hook.raw
            })
            return 0

        status = self._color("enabled", Colors.GREEN) if hook.enabled else self._color("disabled", Colors.YELLOW)
        print(f"Hook: {self._color(hook.name, Colors.BOLD)}")
        print(f"Event: {hook.event}")
        print(f"Status: {status}")
        print(f"Matcher: {hook.matcher}")

        if hook.commands:
            print("Commands:")
            for cmd in hook.commands:
                cmd_type = cmd.get("type", "command")
                if cmd_type == "command":
                    timeout = cmd.get("timeout", 60)
                    print(f"  - {cmd.get('command', '(none)')} (timeout: {timeout}s)")
                elif cmd_type == "prompt":
                    print(f"  - [prompt] {cmd.get('prompt', '(none)')[:50]}...")

        return 0

    def cmd_events(self) -> int:
        """List available hook event types."""
        if getattr(self.args, 'json', False):
            data = [
                {"event": event, "description": desc, "supports": supports}
                for event, (desc, supports) in EVENT_INFO.items()
            ]
            self._output_json(data)
            return 0

        print(f"{self._color('Available hook events:', Colors.BOLD)}\n")
        for event, (desc, supports) in EVENT_INFO.items():
            supports_str = f" (supports: {supports})" if supports else ""
            print(f"  {self._color(event, Colors.BLUE):20} - {desc}{self._color(supports_str, Colors.DIM)}")

        return 0

    def cmd_validate(self) -> int:
        """Validate settings.json syntax and hooks."""
        hooks = self._find_all_hooks()
        issues = []
        warnings = []

        # Check for common issues
        for h in hooks:
            if not h.matcher:
                warnings.append(f"Hook '{h.name}' has no matcher (will match nothing)")
            if not h.commands:
                warnings.append(f"Hook '{h.name}' has no commands (no-op hook)")
            if h.event not in EVENT_TYPES:
                issues.append(f"Hook '{h.name}' has unknown event type: {h.event}")

        if getattr(self.args, 'json', False):
            enabled = len([h for h in hooks if h.enabled])
            disabled = len(hooks) - enabled
            self._output_json({
                "valid": len(issues) == 0,
                "path": str(self.settings_path),
                "hooks_count": len(hooks),
                "enabled_count": enabled,
                "disabled_count": disabled,
                "issues": issues,
                "warnings": warnings
            })
            return 0 if not issues else 1

        # Human-readable output
        if not issues:
            print(self._color(f"✓ {self.settings_path} is valid", Colors.GREEN))
        else:
            print(self._color(f"✗ {self.settings_path} has issues:", Colors.RED))
            for issue in issues:
                print(f"  {self._color('ERROR:', Colors.RED)} {issue}")

        enabled = len([h for h in hooks if h.enabled])
        disabled = len(hooks) - enabled
        print(f"✓ {len(hooks)} hooks found ({enabled} enabled, {disabled} disabled)")

        for warning in warnings:
            print(f"  {self._color('⚠ Warning:', Colors.YELLOW)} {warning}")

        return 0 if not issues else 1

    def cmd_enable(self) -> int:
        """Enable a disabled hook."""
        hook = self._resolve_hook(self.args.name)
        if not hook:
            return 1

        if hook.enabled:
            self._info(f"Hook '{hook.name}' is already enabled")
            return 0

        # Move from _disabled_hooks to hooks
        disabled = self.settings.get("_disabled_hooks", {})
        if hook.event in disabled:
            # Find and remove from disabled
            for i, h in enumerate(disabled[hook.event]):
                if self._get_hook_name(h, hook.event, i) == hook.name:
                    disabled[hook.event].pop(i)
                    if not disabled[hook.event]:
                        del disabled[hook.event]
                    break

        # Add to enabled hooks
        if "hooks" not in self.settings:
            self.settings["hooks"] = {}
        if hook.event not in self.settings["hooks"]:
            self.settings["hooks"][hook.event] = []
        self.settings["hooks"][hook.event].append(hook.raw)

        if getattr(self.args, 'dry_run', False):
            self._info(f"Would enable hook '{hook.name}' in {self.settings_path}")
            print("No changes made (dry-run mode)")
            return 0

        self._save_settings()
        self._success(f"Enabled hook '{hook.name}' in {self.settings_path}")
        return 0

    def cmd_disable(self) -> int:
        """Disable an enabled hook."""
        hook = self._resolve_hook(self.args.name)
        if not hook:
            return 1

        if not hook.enabled:
            self._info(f"Hook '{hook.name}' is already disabled")
            return 0

        # Move from hooks to _disabled_hooks
        hooks = self.settings.get("hooks", {})
        if hook.event in hooks:
            for i, h in enumerate(hooks[hook.event]):
                if self._get_hook_name(h, hook.event, i) == hook.name:
                    hooks[hook.event].pop(i)
                    if not hooks[hook.event]:
                        del hooks[hook.event]
                    break

        # Add to disabled hooks
        if "_disabled_hooks" not in self.settings:
            self.settings["_disabled_hooks"] = {}
        if hook.event not in self.settings["_disabled_hooks"]:
            self.settings["_disabled_hooks"][hook.event] = []
        self.settings["_disabled_hooks"][hook.event].append(hook.raw)

        if getattr(self.args, 'dry_run', False):
            self._info(f"Would disable hook '{hook.name}' in {self.settings_path}")
            print("No changes made (dry-run mode)")
            return 0

        self._save_settings()
        self._success(f"Disabled hook '{hook.name}' in {self.settings_path}")
        return 0

    def cmd_enable_all(self) -> int:
        """Enable all disabled hooks."""
        disabled_hooks = self._find_all_hooks()
        disabled_hooks = [h for h in disabled_hooks if not h.enabled]

        if not disabled_hooks:
            self._info("No disabled hooks to enable")
            return 0

        if getattr(self.args, 'dry_run', False):
            self._info(f"Would enable {len(disabled_hooks)} hooks:")
            for h in disabled_hooks:
                print(f"  - {h.event}:{h.name}")
            print("No changes made (dry-run mode)")
            return 0

        # Move all from _disabled_hooks to hooks
        disabled = self.settings.get("_disabled_hooks", {})
        for event, event_hooks in list(disabled.items()):
            if "hooks" not in self.settings:
                self.settings["hooks"] = {}
            if event not in self.settings["hooks"]:
                self.settings["hooks"][event] = []
            self.settings["hooks"][event].extend(event_hooks)

        self.settings["_disabled_hooks"] = {}
        self._save_settings()
        self._success(f"Enabled {len(disabled_hooks)} hooks in {self.settings_path}")
        return 0

    def cmd_disable_all(self) -> int:
        """Disable all enabled hooks."""
        enabled_hooks = self._find_all_hooks()
        enabled_hooks = [h for h in enabled_hooks if h.enabled]

        if not enabled_hooks:
            self._info("No enabled hooks to disable")
            return 0

        if not self._confirm(f"Disable all {len(enabled_hooks)} hooks?"):
            print("Cancelled")
            return 0

        if getattr(self.args, 'dry_run', False):
            self._info(f"Would disable {len(enabled_hooks)} hooks:")
            for h in enabled_hooks:
                print(f"  - {h.event}:{h.name}")
            print("No changes made (dry-run mode)")
            return 0

        # Move all from hooks to _disabled_hooks
        hooks = self.settings.get("hooks", {})
        for event, event_hooks in list(hooks.items()):
            if "_disabled_hooks" not in self.settings:
                self.settings["_disabled_hooks"] = {}
            if event not in self.settings["_disabled_hooks"]:
                self.settings["_disabled_hooks"][event] = []
            self.settings["_disabled_hooks"][event].extend(event_hooks)

        self.settings["hooks"] = {}
        self._save_settings()
        self._success(f"Disabled {len(enabled_hooks)} hooks in {self.settings_path}")
        return 0

    def cmd_remove(self) -> int:
        """Remove a hook permanently."""
        hook = self._resolve_hook(self.args.name)
        if not hook:
            return 1

        if not self._confirm(f"Remove hook '{hook.name}' from {self.settings_path}?"):
            print("Cancelled")
            return 0

        if getattr(self.args, 'dry_run', False):
            self._info(f"Would remove hook '{hook.name}' from {self.settings_path}")
            print("No changes made (dry-run mode)")
            return 0

        # Find and remove from appropriate location
        source = "hooks" if hook.enabled else "_disabled_hooks"
        hooks_dict = self.settings.get(source, {})

        if hook.event in hooks_dict:
            for i, h in enumerate(hooks_dict[hook.event]):
                if self._get_hook_name(h, hook.event, i) == hook.name:
                    hooks_dict[hook.event].pop(i)
                    if not hooks_dict[hook.event]:
                        del hooks_dict[hook.event]
                    break

        self._save_settings()
        self._success(f"Removed hook '{hook.name}' from {self.settings_path}")
        return 0

    def cmd_remove_all(self) -> int:
        """Remove all hooks permanently."""
        all_hooks = self._find_all_hooks()

        if not all_hooks:
            self._info("No hooks to remove")
            return 0

        if not self._confirm(f"Remove ALL {len(all_hooks)} hooks from {self.settings_path}?"):
            print("Cancelled")
            return 0

        if getattr(self.args, 'dry_run', False):
            self._info(f"Would remove {len(all_hooks)} hooks:")
            for h in all_hooks:
                status = "enabled" if h.enabled else "disabled"
                print(f"  - {h.name} ({h.event}, {status})")
            print("No changes made (dry-run mode)")
            return 0

        removed = []
        for h in all_hooks:
            status = "disabled" if not h.enabled else ""
            removed.append(f"  - {h.name} ({h.event}{', ' + status if status else ''})")

        self.settings["hooks"] = {}
        self.settings["_disabled_hooks"] = {}
        self._save_settings()

        self._success(f"Removed {len(all_hooks)} hooks from {self.settings_path}:")
        for line in removed:
            print(line)
        return 0

    def cmd_add(self) -> int:
        """Add a new hook."""
        # Check if we have all required params for non-interactive mode
        has_params = all([
            getattr(self.args, 'hook_name', None),
            getattr(self.args, 'event', None),
            getattr(self.args, 'hook_command', None)
        ])

        if not has_params:
            # Interactive mode required
            if not sys.stdin.isatty():
                self._error("Interactive mode requires a terminal. Use --name, --event, --command flags.")
                return 1
            return self._add_interactive()

        return self._add_non_interactive()

    def _add_interactive(self) -> int:
        """Add hook interactively."""
        print("Add new hook\n")

        # Event type
        print("Event types:")
        for i, event in enumerate(EVENT_TYPES, 1):
            desc, _ = EVENT_INFO[event]
            print(f"  [{i}] {event} - {desc}")

        try:
            choice = input("\nEvent type (number or name): ").strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(EVENT_TYPES):
                    event = EVENT_TYPES[idx]
                else:
                    self._error("Invalid selection")
                    return 1
            else:
                # Match by name (case-insensitive)
                event = None
                for e in EVENT_TYPES:
                    if e.lower() == choice.lower():
                        event = e
                        break
                if not event:
                    self._error(f"Unknown event type: {choice}")
                    return 1

            name = input("Hook name: ").strip()
            if not name:
                self._error("Name is required")
                return 1

            # Check for existing hook with same name
            existing = self._find_hooks_by_name(f"{event}:{name}")
            if existing:
                self._error(f"Hook '{name}' already exists for event {event}")
                return 1

            matcher = input("Matcher pattern (default: *): ").strip() or "*"
            command = input("Command: ").strip()
            if not command:
                self._error("Command is required")
                return 1

            timeout_str = input("Timeout in seconds (default: 60): ").strip()
            timeout = int(timeout_str) if timeout_str else 60

        except (EOFError, KeyboardInterrupt):
            print("\nCancelled")
            return 0

        return self._add_hook(event, name, matcher, command, timeout)

    def _add_non_interactive(self) -> int:
        """Add hook with provided arguments."""
        event = self.args.event
        name = self.args.hook_name
        matcher = getattr(self.args, 'matcher', '*') or '*'
        command = self.args.hook_command
        timeout = getattr(self.args, 'timeout', 60) or 60

        # Validate event type (case-insensitive)
        valid_event = None
        for e in EVENT_TYPES:
            if e.lower() == event.lower():
                valid_event = e
                break

        if not valid_event:
            self._error(f"Unknown event type: {event}")
            print("Valid event types:")
            for e in EVENT_TYPES:
                print(f"  {e}")
            return 1

        # Check for existing hook
        existing = self._find_hooks_by_name(f"{valid_event}:{name}")
        if existing:
            self._error(f"Hook '{name}' already exists for event {valid_event}")
            return 1

        return self._add_hook(valid_event, name, matcher, command, timeout)

    def _add_hook(self, event: str, name: str, matcher: str, command: str, timeout: int) -> int:
        """Add hook to settings."""
        hook_obj = {
            "_name": name,
            "matcher": matcher,
            "hooks": [
                {
                    "type": "command",
                    "command": command,
                    "timeout": timeout
                }
            ]
        }

        if getattr(self.args, 'dry_run', False):
            self._info(f"Would add hook '{name}' to {self.settings_path}:")
            print(json.dumps(hook_obj, indent=2))
            print("No changes made (dry-run mode)")
            return 0

        if "hooks" not in self.settings:
            self.settings["hooks"] = {}
        if event not in self.settings["hooks"]:
            self.settings["hooks"][event] = []

        self.settings["hooks"][event].append(hook_obj)
        self._save_settings()
        self._success(f"Added hook '{name}' to {self.settings_path}")
        return 0

    def cmd_export(self) -> int:
        """Export hooks to a JSON file."""
        hooks = self._find_all_hooks()

        export_data = {
            "version": "1.0",
            "source": str(self.settings_path),
            "hooks": self.settings.get("hooks", {}),
            "_disabled_hooks": self.settings.get("_disabled_hooks", {})
        }

        output_file = getattr(self.args, 'file', None)

        if output_file:
            output_path = Path(output_file)
            if getattr(self.args, 'dry_run', False):
                self._info(f"Would export {len(hooks)} hooks to {output_path}")
                print("No changes made (dry-run mode)")
                return 0

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
                f.write('\n')
            self._success(f"Exported {len(hooks)} hooks to {output_path}")
        else:
            # Output to stdout
            print(json.dumps(export_data, indent=2, ensure_ascii=False))

        return 0

    def cmd_import(self) -> int:
        """Import hooks from a JSON file."""
        import_path = Path(self.args.file)

        if not import_path.exists():
            self._error(f"File not found: {import_path}")
            return 1

        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
        except json.JSONDecodeError as e:
            self._error(f"Invalid JSON in {import_path}: {e}")
            return 1

        # Handle both export format and raw settings format
        if "hooks" in import_data:
            new_hooks = import_data.get("hooks", {})
            new_disabled = import_data.get("_disabled_hooks", {})
        else:
            self._error("Invalid import file format: missing 'hooks' key")
            return 1

        # Count hooks to import
        count = sum(len(hooks) for hooks in new_hooks.values())
        count += sum(len(hooks) for hooks in new_disabled.values())

        if count == 0:
            self._info("No hooks to import")
            return 0

        if not self._confirm(f"Import {count} hooks to {self.settings_path}?"):
            print("Cancelled")
            return 0

        if getattr(self.args, 'dry_run', False):
            self._info(f"Would import {count} hooks to {self.settings_path}")
            print("No changes made (dry-run mode)")
            return 0

        # Merge hooks
        for event, event_hooks in new_hooks.items():
            if "hooks" not in self.settings:
                self.settings["hooks"] = {}
            if event not in self.settings["hooks"]:
                self.settings["hooks"][event] = []
            self.settings["hooks"][event].extend(event_hooks)

        for event, event_hooks in new_disabled.items():
            if "_disabled_hooks" not in self.settings:
                self.settings["_disabled_hooks"] = {}
            if event not in self.settings["_disabled_hooks"]:
                self.settings["_disabled_hooks"][event] = []
            self.settings["_disabled_hooks"][event].extend(event_hooks)

        self._save_settings()
        self._success(f"Imported {count} hooks to {self.settings_path}")
        return 0


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="hooks_manager",
        description="Manage Claude Code hooks - enable, disable, list, and more.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list                      List all hooks (auto-detect scope)
  %(prog)s list --global             List global hooks only
  %(prog)s disable lint              Disable hook named 'lint'
  %(prog)s enable PostToolUse:lint   Enable specific hook by event:name
  %(prog)s add --name test --event PostToolUse --matcher Write --command "pytest"
  %(prog)s export hooks_backup.json  Export hooks to file
"""
    )

    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')

    # Global flags
    scope_group = parser.add_mutually_exclusive_group()
    scope_group.add_argument('--global', '-g', dest='global_scope', action='store_true',
                            help='Target ~/.claude/settings.json')
    scope_group.add_argument('--project', '-p', dest='project_scope', action='store_true',
                            help='Target ./.claude/settings.json')

    parser.add_argument('--json', action='store_true',
                       help='Output in JSON format')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Minimal output')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview changes without applying')
    parser.add_argument('--no-color', action='store_true',
                       help='Disable colored output')
    parser.add_argument('--no-backup', action='store_true',
                       help='Skip creating backup before modification')
    parser.add_argument('--force', '-f', action='store_true',
                       help='Skip confirmation prompts')

    subparsers = parser.add_subparsers(dest='command', metavar='COMMAND')

    # list
    subparsers.add_parser('list', help='List all hooks with status')

    # show
    show_parser = subparsers.add_parser('show', help='Show details of a specific hook')
    show_parser.add_argument('name', help='Hook name (or Event:name)')

    # events
    subparsers.add_parser('events', help='List available hook event types')

    # validate
    subparsers.add_parser('validate', help='Validate settings.json syntax')

    # enable
    enable_parser = subparsers.add_parser('enable', help='Enable a disabled hook')
    enable_parser.add_argument('name', help='Hook name (or Event:name)')

    # disable
    disable_parser = subparsers.add_parser('disable', help='Disable an enabled hook')
    disable_parser.add_argument('name', help='Hook name (or Event:name)')

    # enable-all
    subparsers.add_parser('enable-all', help='Enable all disabled hooks')

    # disable-all
    subparsers.add_parser('disable-all', help='Disable all enabled hooks (requires confirmation)')

    # remove
    remove_parser = subparsers.add_parser('remove', help='Remove a hook permanently')
    remove_parser.add_argument('name', help='Hook name (or Event:name)')

    # remove-all
    subparsers.add_parser('remove-all', help='Remove ALL hooks permanently (requires confirmation)')

    # add / create (aliases)
    add_parser = subparsers.add_parser('add', aliases=['create'], help='Create a new hook (interactive or with flags)')
    add_parser.add_argument('--name', dest='hook_name', help='Hook name')
    add_parser.add_argument('--event', '-e', help='Event type (e.g., PostToolUse)')
    add_parser.add_argument('--matcher', '-m', default='*', help='Matcher pattern (default: *)')
    add_parser.add_argument('--command', '-c', dest='hook_command', help='Command to execute')
    add_parser.add_argument('--timeout', '-t', type=int, default=60, help='Timeout in seconds (default: 60)')

    # export
    export_parser = subparsers.add_parser('export', help='Export hooks to JSON file')
    export_parser.add_argument('file', nargs='?', help='Output file (stdout if not specified)')

    # import
    import_parser = subparsers.add_parser('import', help='Import hooks from JSON file')
    import_parser.add_argument('file', help='Input JSON file')

    return parser


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    manager = HooksManager(args)

    # Route to command handler
    commands = {
        'list': manager.cmd_list,
        'show': manager.cmd_show,
        'events': manager.cmd_events,
        'validate': manager.cmd_validate,
        'enable': manager.cmd_enable,
        'disable': manager.cmd_disable,
        'enable-all': manager.cmd_enable_all,
        'disable-all': manager.cmd_disable_all,
        'remove': manager.cmd_remove,
        'remove-all': manager.cmd_remove_all,
        'add': manager.cmd_add,
        'create': manager.cmd_add,  # alias for add
        'export': manager.cmd_export,
        'import': manager.cmd_import,
    }

    handler = commands.get(args.command)
    if handler:
        return handler()
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
