"""Tests for HooksManager class."""

import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from hooks_manager import HooksManager, HookInfo, EVENT_TYPES, Colors


class TestHooksManagerInit:
    """Tests for HooksManager initialization."""

    def test_init_creates_manager(self, mock_args, tmp_path, sample_settings):
        """Test that HooksManager initializes correctly."""
        settings_dir = tmp_path / ".claude"
        settings_dir.mkdir(parents=True)
        settings_file = settings_dir / "settings.json"
        settings_file.write_text(json.dumps(sample_settings, indent=2))

        mock_args.project_scope = True

        with patch.object(Path, 'cwd', return_value=tmp_path):
            manager = HooksManager(mock_args)

        assert manager.args == mock_args
        assert not manager.use_color  # no_color=True in mock_args

    def test_init_with_missing_settings_creates_empty(self, mock_args, tmp_path):
        """Test that missing settings.json creates empty structure."""
        mock_args.project_scope = True

        with patch.object(Path, 'cwd', return_value=tmp_path):
            manager = HooksManager(mock_args)

        assert manager.settings == {"hooks": {}, "_disabled_hooks": {}}

    def test_color_disabled_with_no_color_flag(self, mock_args, tmp_path, sample_settings):
        """Test that --no-color flag disables colors."""
        settings_dir = tmp_path / ".claude"
        settings_dir.mkdir(parents=True)
        settings_file = settings_dir / "settings.json"
        settings_file.write_text(json.dumps(sample_settings, indent=2))

        mock_args.no_color = True
        mock_args.project_scope = True

        with patch.object(Path, 'cwd', return_value=tmp_path):
            manager = HooksManager(mock_args)

        assert not manager.use_color


class TestHooksManagerFindHooks:
    """Tests for hook finding methods."""

    def test_find_all_hooks_returns_enabled_and_disabled(self, hooks_manager, sample_settings):
        """Test that _find_all_hooks returns both enabled and disabled hooks."""
        hooks = hooks_manager._find_all_hooks()

        # Count expected hooks
        enabled_count = sum(len(h) for h in sample_settings["hooks"].values())
        disabled_count = sum(len(h) for h in sample_settings["_disabled_hooks"].values())

        assert len(hooks) == enabled_count + disabled_count

    def test_find_all_hooks_marks_enabled_correctly(self, hooks_manager):
        """Test that enabled hooks are marked as enabled."""
        hooks = hooks_manager._find_all_hooks()
        enabled_hooks = [h for h in hooks if h.enabled]
        disabled_hooks = [h for h in hooks if not h.enabled]

        assert len(enabled_hooks) == 3  # lint, format, confirm-dangerous
        assert len(disabled_hooks) == 1  # slow-tests

    def test_find_hooks_by_name_case_insensitive(self, hooks_manager):
        """Test that finding hooks by name is case-insensitive."""
        hooks_lower = hooks_manager._find_hooks_by_name("lint")
        hooks_upper = hooks_manager._find_hooks_by_name("LINT")
        hooks_mixed = hooks_manager._find_hooks_by_name("LiNt")

        assert len(hooks_lower) == len(hooks_upper) == len(hooks_mixed) == 1

    def test_find_hooks_by_name_with_event_prefix(self, hooks_manager):
        """Test finding hooks with event:name format."""
        hooks = hooks_manager._find_hooks_by_name("PostToolUse:lint")

        assert len(hooks) == 1
        assert hooks[0].name == "lint"
        assert hooks[0].event == "PostToolUse"

    def test_find_hooks_by_name_no_match(self, hooks_manager):
        """Test that non-existent hook returns empty list."""
        hooks = hooks_manager._find_hooks_by_name("nonexistent")

        assert hooks == []


class TestHooksManagerCommands:
    """Tests for HooksManager command methods."""

    def test_cmd_list_returns_zero(self, hooks_manager):
        """Test that cmd_list returns 0 on success."""
        result = hooks_manager.cmd_list()
        assert result == 0

    def test_cmd_list_json_output(self, hooks_manager, capsys):
        """Test that cmd_list with --json outputs valid JSON."""
        hooks_manager.args.json = True
        hooks_manager.cmd_list()

        captured = capsys.readouterr()
        data = json.loads(captured.out)

        assert "hooks" in data
        assert "path" in data
        assert isinstance(data["hooks"], list)

    def test_cmd_list_quiet_output(self, hooks_manager, capsys):
        """Test that cmd_list with --quiet outputs minimal format."""
        hooks_manager.args.quiet = True
        hooks_manager.cmd_list()

        captured = capsys.readouterr()
        lines = [l for l in captured.out.strip().split('\n') if l]

        # Each line should be in event:name format
        for line in lines:
            assert ':' in line

    def test_cmd_show_existing_hook(self, hooks_manager, capsys):
        """Test showing details of an existing hook."""
        hooks_manager.args.name = "lint"
        result = hooks_manager.cmd_show()

        assert result == 0
        captured = capsys.readouterr()
        assert "lint" in captured.out

    def test_cmd_show_nonexistent_hook(self, hooks_manager, capsys):
        """Test showing details of non-existent hook returns error."""
        hooks_manager.args.name = "nonexistent"
        result = hooks_manager.cmd_show()

        assert result == 1

    def test_cmd_show_json_output(self, hooks_manager, capsys):
        """Test cmd_show with --json outputs valid JSON."""
        hooks_manager.args.name = "lint"
        hooks_manager.args.json = True
        hooks_manager.cmd_show()

        captured = capsys.readouterr()
        data = json.loads(captured.out)

        assert data["name"] == "lint"
        assert data["event"] == "PostToolUse"
        assert data["enabled"] is True

    def test_cmd_events_lists_all_events(self, hooks_manager, capsys):
        """Test that cmd_events lists all event types."""
        result = hooks_manager.cmd_events()

        assert result == 0
        captured = capsys.readouterr()

        for event in EVENT_TYPES:
            assert event in captured.out

    def test_cmd_events_json_output(self, hooks_manager, capsys):
        """Test cmd_events with --json outputs valid JSON."""
        hooks_manager.args.json = True
        hooks_manager.cmd_events()

        captured = capsys.readouterr()
        data = json.loads(captured.out)

        assert len(data) == len(EVENT_TYPES)
        event_names = [e["event"] for e in data]
        for event in EVENT_TYPES:
            assert event in event_names

    def test_cmd_validate_valid_settings(self, hooks_manager, capsys):
        """Test validation of valid settings."""
        result = hooks_manager.cmd_validate()

        assert result == 0

    def test_cmd_validate_json_output(self, hooks_manager, capsys):
        """Test cmd_validate with --json outputs valid JSON."""
        hooks_manager.args.json = True
        hooks_manager.cmd_validate()

        captured = capsys.readouterr()
        data = json.loads(captured.out)

        assert "valid" in data
        assert "hooks_count" in data
        assert data["valid"] is True


class TestHooksManagerEnableDisable:
    """Tests for enable/disable operations."""

    def test_cmd_enable_disabled_hook(self, hooks_manager, tmp_path, sample_settings):
        """Test enabling a disabled hook."""
        # Setup settings file for saving
        settings_file = tmp_path / ".claude" / "settings.json"
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        settings_file.write_text(json.dumps(sample_settings, indent=2))
        hooks_manager.settings_path = settings_file

        hooks_manager.args.name = "slow-tests"
        result = hooks_manager.cmd_enable()

        assert result == 0

        # Verify hook moved to enabled
        assert "slow-tests" in str(hooks_manager.settings.get("hooks", {}))

    def test_cmd_enable_already_enabled(self, hooks_manager, capsys):
        """Test enabling an already enabled hook."""
        hooks_manager.args.name = "lint"
        result = hooks_manager.cmd_enable()

        assert result == 0
        captured = capsys.readouterr()
        assert "already enabled" in captured.out

    def test_cmd_disable_enabled_hook(self, hooks_manager, tmp_path, sample_settings):
        """Test disabling an enabled hook."""
        settings_file = tmp_path / ".claude" / "settings.json"
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        settings_file.write_text(json.dumps(sample_settings, indent=2))
        hooks_manager.settings_path = settings_file

        hooks_manager.args.name = "lint"
        result = hooks_manager.cmd_disable()

        assert result == 0

    def test_cmd_disable_already_disabled(self, hooks_manager, capsys):
        """Test disabling an already disabled hook."""
        hooks_manager.args.name = "slow-tests"
        result = hooks_manager.cmd_disable()

        assert result == 0
        captured = capsys.readouterr()
        assert "already disabled" in captured.out

    def test_cmd_enable_nonexistent(self, hooks_manager):
        """Test enabling non-existent hook returns error."""
        hooks_manager.args.name = "nonexistent"
        result = hooks_manager.cmd_enable()

        assert result == 1

    def test_cmd_disable_nonexistent(self, hooks_manager):
        """Test disabling non-existent hook returns error."""
        hooks_manager.args.name = "nonexistent"
        result = hooks_manager.cmd_disable()

        assert result == 1

    def test_cmd_enable_all(self, hooks_manager, tmp_path, sample_settings):
        """Test enabling all disabled hooks."""
        settings_file = tmp_path / ".claude" / "settings.json"
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        settings_file.write_text(json.dumps(sample_settings, indent=2))
        hooks_manager.settings_path = settings_file

        result = hooks_manager.cmd_enable_all()

        assert result == 0
        # Verify no disabled hooks remain
        assert hooks_manager.settings.get("_disabled_hooks", {}) == {}

    def test_cmd_disable_all(self, hooks_manager, tmp_path, sample_settings):
        """Test disabling all enabled hooks."""
        settings_file = tmp_path / ".claude" / "settings.json"
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        settings_file.write_text(json.dumps(sample_settings, indent=2))
        hooks_manager.settings_path = settings_file

        result = hooks_manager.cmd_disable_all()

        assert result == 0
        # Verify no enabled hooks remain
        assert hooks_manager.settings.get("hooks", {}) == {}


class TestHooksManagerAddRemove:
    """Tests for add/remove operations."""

    def test_cmd_add_with_all_params(self, hooks_manager, tmp_path, sample_settings):
        """Test adding a hook with all required parameters."""
        settings_file = tmp_path / ".claude" / "settings.json"
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        settings_file.write_text(json.dumps(sample_settings, indent=2))
        hooks_manager.settings_path = settings_file

        hooks_manager.args.hook_name = "new-hook"
        hooks_manager.args.event = "PostToolUse"
        hooks_manager.args.hook_command = "echo hello"
        hooks_manager.args.matcher = "Write"
        hooks_manager.args.timeout = 30

        result = hooks_manager.cmd_add()

        assert result == 0

        # Verify hook was added
        hooks = hooks_manager._find_hooks_by_name("new-hook")
        assert len(hooks) == 1

    def test_cmd_add_duplicate_name_fails(self, hooks_manager):
        """Test adding a hook with duplicate name fails."""
        hooks_manager.args.hook_name = "lint"  # Already exists
        hooks_manager.args.event = "PostToolUse"
        hooks_manager.args.hook_command = "echo test"

        result = hooks_manager.cmd_add()

        assert result == 1

    def test_cmd_add_invalid_event_fails(self, hooks_manager):
        """Test adding a hook with invalid event type fails."""
        hooks_manager.args.hook_name = "new-hook"
        hooks_manager.args.event = "InvalidEvent"
        hooks_manager.args.hook_command = "echo test"

        result = hooks_manager.cmd_add()

        assert result == 1

    def test_cmd_remove_existing_hook(self, hooks_manager, tmp_path, sample_settings):
        """Test removing an existing hook."""
        settings_file = tmp_path / ".claude" / "settings.json"
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        settings_file.write_text(json.dumps(sample_settings, indent=2))
        hooks_manager.settings_path = settings_file

        hooks_manager.args.name = "lint"
        result = hooks_manager.cmd_remove()

        assert result == 0

        # Verify hook was removed
        hooks = hooks_manager._find_hooks_by_name("lint")
        assert len(hooks) == 0

    def test_cmd_remove_nonexistent(self, hooks_manager):
        """Test removing non-existent hook returns error."""
        hooks_manager.args.name = "nonexistent"
        result = hooks_manager.cmd_remove()

        assert result == 1

    def test_cmd_remove_all(self, hooks_manager, tmp_path, sample_settings):
        """Test removing all hooks."""
        settings_file = tmp_path / ".claude" / "settings.json"
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        settings_file.write_text(json.dumps(sample_settings, indent=2))
        hooks_manager.settings_path = settings_file

        result = hooks_manager.cmd_remove_all()

        assert result == 0

        # Verify all hooks were removed
        hooks = hooks_manager._find_all_hooks()
        assert len(hooks) == 0


class TestHooksManagerExportImport:
    """Tests for export/import operations."""

    def test_cmd_export_to_stdout(self, hooks_manager, capsys):
        """Test exporting hooks to stdout."""
        hooks_manager.args.file = None
        result = hooks_manager.cmd_export()

        assert result == 0

        captured = capsys.readouterr()
        data = json.loads(captured.out)

        assert "version" in data
        assert "hooks" in data

    def test_cmd_export_to_file(self, hooks_manager, tmp_path):
        """Test exporting hooks to a file."""
        export_file = tmp_path / "export.json"
        hooks_manager.args.file = str(export_file)

        result = hooks_manager.cmd_export()

        assert result == 0
        assert export_file.exists()

        data = json.loads(export_file.read_text())
        assert "hooks" in data

    def test_cmd_import_valid_file(self, hooks_manager, tmp_path, sample_settings):
        """Test importing hooks from a valid file."""
        # Create settings file
        settings_file = tmp_path / ".claude" / "settings.json"
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        settings_file.write_text(json.dumps({"hooks": {}, "_disabled_hooks": {}}, indent=2))
        hooks_manager.settings_path = settings_file
        hooks_manager.settings = {"hooks": {}, "_disabled_hooks": {}}

        # Create import file
        import_data = {
            "version": "1.0",
            "hooks": {
                "PostToolUse": [
                    {"_name": "imported-hook", "matcher": "*", "hooks": []}
                ]
            },
            "_disabled_hooks": {}
        }
        import_file = tmp_path / "import.json"
        import_file.write_text(json.dumps(import_data, indent=2))

        hooks_manager.args.file = str(import_file)
        result = hooks_manager.cmd_import()

        assert result == 0

    def test_cmd_import_nonexistent_file(self, hooks_manager, tmp_path):
        """Test importing from non-existent file fails."""
        hooks_manager.args.file = str(tmp_path / "nonexistent.json")
        result = hooks_manager.cmd_import()

        assert result == 1

    def test_cmd_import_invalid_json(self, hooks_manager, tmp_path):
        """Test importing invalid JSON fails."""
        import_file = tmp_path / "invalid.json"
        import_file.write_text("not valid json")

        hooks_manager.args.file = str(import_file)
        result = hooks_manager.cmd_import()

        assert result == 1


class TestHooksManagerDryRun:
    """Tests for dry-run mode."""

    def test_enable_dry_run_no_changes(self, hooks_manager, tmp_path, sample_settings):
        """Test that dry-run mode doesn't modify settings."""
        settings_file = tmp_path / ".claude" / "settings.json"
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        original_content = json.dumps(sample_settings, indent=2)
        settings_file.write_text(original_content)
        hooks_manager.settings_path = settings_file

        hooks_manager.args.dry_run = True
        hooks_manager.args.name = "slow-tests"
        hooks_manager.cmd_enable()

        # File should be unchanged
        assert settings_file.read_text() == original_content

    def test_disable_dry_run_no_changes(self, hooks_manager, tmp_path, sample_settings):
        """Test that dry-run mode doesn't modify settings."""
        settings_file = tmp_path / ".claude" / "settings.json"
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        original_content = json.dumps(sample_settings, indent=2)
        settings_file.write_text(original_content)
        hooks_manager.settings_path = settings_file

        hooks_manager.args.dry_run = True
        hooks_manager.args.name = "lint"
        hooks_manager.cmd_disable()

        # File should be unchanged
        assert settings_file.read_text() == original_content


class TestHooksManagerUtilities:
    """Tests for utility methods."""

    def test_normalize_name_lowercase(self, hooks_manager):
        """Test that _normalize_name returns lowercase."""
        assert hooks_manager._normalize_name("TEST") == "test"
        assert hooks_manager._normalize_name("TeSt") == "test"
        assert hooks_manager._normalize_name("test") == "test"

    def test_get_hook_name_with_name(self, hooks_manager):
        """Test _get_hook_name with explicit name."""
        hook = {"_name": "my-hook"}
        name = hooks_manager._get_hook_name(hook, "PostToolUse", 0)
        assert name == "my-hook"

    def test_get_hook_name_without_name(self, hooks_manager):
        """Test _get_hook_name generates name from event and index."""
        hook = {}
        name = hooks_manager._get_hook_name(hook, "PostToolUse", 0)
        assert name == "PostToolUse#0"

    def test_color_with_colors_enabled(self, hooks_manager):
        """Test _color applies color when enabled."""
        hooks_manager.use_color = True
        result = hooks_manager._color("test", Colors.GREEN)
        assert Colors.GREEN in result
        assert Colors.RESET in result

    def test_color_with_colors_disabled(self, hooks_manager):
        """Test _color returns plain text when disabled."""
        hooks_manager.use_color = False
        result = hooks_manager._color("test", Colors.GREEN)
        assert result == "test"
        assert Colors.GREEN not in result
