"""CLI integration tests for hooks_manager."""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from hooks_manager import create_parser, main, EVENT_TYPES


class TestArgumentParser:
    """Tests for argument parser configuration."""

    def test_parser_creation(self, parser):
        """Test parser is created successfully."""
        assert parser is not None
        assert parser.prog == "hooks_manager"

    def test_global_flag(self, parser):
        """Test --global flag is recognized."""
        args = parser.parse_args(["--global", "list"])
        assert args.global_scope is True
        assert args.project_scope is False

    def test_project_flag(self, parser):
        """Test --project flag is recognized."""
        args = parser.parse_args(["--project", "list"])
        assert args.project_scope is True
        assert args.global_scope is False

    def test_global_project_mutually_exclusive(self, parser):
        """Test --global and --project are mutually exclusive."""
        with pytest.raises(SystemExit):
            parser.parse_args(["--global", "--project", "list"])

    def test_json_flag(self, parser):
        """Test --json flag is recognized."""
        args = parser.parse_args(["--json", "list"])
        assert args.json is True

    def test_quiet_flag(self, parser):
        """Test --quiet flag is recognized."""
        args = parser.parse_args(["--quiet", "list"])
        assert args.quiet is True

    def test_dry_run_flag(self, parser):
        """Test --dry-run flag is recognized."""
        args = parser.parse_args(["--dry-run", "list"])
        assert args.dry_run is True

    def test_no_color_flag(self, parser):
        """Test --no-color flag is recognized."""
        args = parser.parse_args(["--no-color", "list"])
        assert args.no_color is True

    def test_no_backup_flag(self, parser):
        """Test --no-backup flag is recognized."""
        args = parser.parse_args(["--no-backup", "list"])
        assert args.no_backup is True

    def test_force_flag(self, parser):
        """Test --force flag is recognized."""
        args = parser.parse_args(["--force", "list"])
        assert args.force is True


class TestSubcommands:
    """Tests for subcommand parsing."""

    def test_list_command(self, parser):
        """Test list command parsing."""
        args = parser.parse_args(["list"])
        assert args.command == "list"

    def test_show_command(self, parser):
        """Test show command parsing."""
        args = parser.parse_args(["show", "hook-name"])
        assert args.command == "show"
        assert args.name == "hook-name"

    def test_events_command(self, parser):
        """Test events command parsing."""
        args = parser.parse_args(["events"])
        assert args.command == "events"

    def test_validate_command(self, parser):
        """Test validate command parsing."""
        args = parser.parse_args(["validate"])
        assert args.command == "validate"

    def test_enable_command(self, parser):
        """Test enable command parsing."""
        args = parser.parse_args(["enable", "hook-name"])
        assert args.command == "enable"
        assert args.name == "hook-name"

    def test_disable_command(self, parser):
        """Test disable command parsing."""
        args = parser.parse_args(["disable", "hook-name"])
        assert args.command == "disable"
        assert args.name == "hook-name"

    def test_enable_all_command(self, parser):
        """Test enable-all command parsing."""
        args = parser.parse_args(["enable-all"])
        assert args.command == "enable-all"

    def test_disable_all_command(self, parser):
        """Test disable-all command parsing."""
        args = parser.parse_args(["disable-all"])
        assert args.command == "disable-all"

    def test_remove_command(self, parser):
        """Test remove command parsing."""
        args = parser.parse_args(["remove", "hook-name"])
        assert args.command == "remove"
        assert args.name == "hook-name"

    def test_remove_all_command(self, parser):
        """Test remove-all command parsing."""
        args = parser.parse_args(["remove-all"])
        assert args.command == "remove-all"

    def test_add_command(self, parser):
        """Test add command parsing."""
        args = parser.parse_args([
            "add",
            "--name", "new-hook",
            "--event", "PostToolUse",
            "--command", "echo test"
        ])
        assert args.command == "add"
        assert args.hook_name == "new-hook"
        assert args.event == "PostToolUse"
        assert args.hook_command == "echo test"

    def test_add_command_with_matcher(self, parser):
        """Test add command with matcher."""
        args = parser.parse_args([
            "add",
            "--name", "new-hook",
            "--event", "PostToolUse",
            "--command", "echo test",
            "--matcher", "Write|Edit"
        ])
        assert args.matcher == "Write|Edit"

    def test_add_command_with_timeout(self, parser):
        """Test add command with timeout."""
        args = parser.parse_args([
            "add",
            "--name", "new-hook",
            "--event", "PostToolUse",
            "--command", "echo test",
            "--timeout", "120"
        ])
        assert args.timeout == 120

    def test_create_alias(self, parser):
        """Test create is alias for add."""
        args = parser.parse_args([
            "create",
            "--name", "new-hook",
            "--event", "PostToolUse",
            "--command", "echo test"
        ])
        assert args.command == "create"

    def test_export_command_with_file(self, parser):
        """Test export command with file."""
        args = parser.parse_args(["export", "output.json"])
        assert args.command == "export"
        assert args.file == "output.json"

    def test_export_command_without_file(self, parser):
        """Test export command without file (stdout)."""
        args = parser.parse_args(["export"])
        assert args.command == "export"
        assert args.file is None

    def test_import_command(self, parser):
        """Test import command."""
        args = parser.parse_args(["import", "input.json"])
        assert args.command == "import"
        assert args.file == "input.json"

    def test_visualize_command(self, parser):
        """Test visualize command."""
        args = parser.parse_args(["visualize"])
        assert args.command == "visualize"
        assert args.format == "terminal"  # default

    def test_visualize_with_format(self, parser):
        """Test visualize command with format."""
        for fmt in ["terminal", "html", "markdown", "tui"]:
            args = parser.parse_args(["visualize", "--format", fmt])
            assert args.format == fmt

    def test_visualize_with_output(self, parser):
        """Test visualize command with output file."""
        args = parser.parse_args(["visualize", "--output", "output.html"])
        assert args.output_file == "output.html"


class TestMainFunction:
    """Tests for main() function."""

    def test_no_command_shows_help(self, capsys):
        """Test that no command shows help."""
        with patch('sys.argv', ['hooks_manager']):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower() or "hooks" in captured.out.lower()

    def test_list_command_execution(self, tmp_path, sample_settings, capsys):
        """Test list command executes successfully."""
        settings_file = tmp_path / ".claude" / "settings.json"
        settings_file.parent.mkdir(parents=True)
        settings_file.write_text(json.dumps(sample_settings, indent=2))

        with patch('sys.argv', ['hooks_manager', '--project', 'list']):
            with patch.object(Path, 'cwd', return_value=tmp_path):
                result = main()

        assert result == 0

    def test_events_command_execution(self, tmp_path, capsys):
        """Test events command executes successfully."""
        settings_dir = tmp_path / ".claude"
        settings_dir.mkdir(parents=True)

        with patch('sys.argv', ['hooks_manager', '--project', 'events']):
            with patch.object(Path, 'cwd', return_value=tmp_path):
                result = main()

        assert result == 0
        captured = capsys.readouterr()
        for event in EVENT_TYPES:
            assert event in captured.out

    def test_validate_command_execution(self, tmp_path, sample_settings, capsys):
        """Test validate command executes successfully."""
        settings_file = tmp_path / ".claude" / "settings.json"
        settings_file.parent.mkdir(parents=True)
        settings_file.write_text(json.dumps(sample_settings, indent=2))

        with patch('sys.argv', ['hooks_manager', '--project', 'validate']):
            with patch.object(Path, 'cwd', return_value=tmp_path):
                result = main()

        assert result == 0

    def test_show_command_execution(self, tmp_path, sample_settings, capsys):
        """Test show command executes successfully."""
        settings_file = tmp_path / ".claude" / "settings.json"
        settings_file.parent.mkdir(parents=True)
        settings_file.write_text(json.dumps(sample_settings, indent=2))

        with patch('sys.argv', ['hooks_manager', '--project', 'show', 'lint']):
            with patch.object(Path, 'cwd', return_value=tmp_path):
                result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "lint" in captured.out


class TestCLIEndToEnd:
    """End-to-end CLI tests using subprocess."""

    @pytest.fixture
    def script_path(self):
        """Get path to hooks_manager.py script."""
        return str(Path(__file__).parent.parent / "hooks_manager.py")

    def test_script_runs(self, script_path):
        """Test script can be executed."""
        result = subprocess.run(
            [sys.executable, script_path, "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()

    def test_version_flag(self, script_path):
        """Test --version flag."""
        result = subprocess.run(
            [sys.executable, script_path, "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "1.0.0" in result.stdout

    def test_list_with_nonexistent_settings(self, script_path, tmp_path):
        """Test list command with non-existent settings."""
        result = subprocess.run(
            [sys.executable, script_path, "--project", "list"],
            capture_output=True,
            text=True,
            cwd=tmp_path
        )
        # Should not crash, just show empty list
        assert result.returncode == 0

    def test_events_command_output(self, script_path):
        """Test events command output contains all event types."""
        result = subprocess.run(
            [sys.executable, script_path, "events"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        for event in EVENT_TYPES:
            assert event in result.stdout

    def test_json_output_format(self, script_path, tmp_path, sample_settings):
        """Test --json flag produces valid JSON."""
        settings_file = tmp_path / ".claude" / "settings.json"
        settings_file.parent.mkdir(parents=True)
        settings_file.write_text(json.dumps(sample_settings, indent=2))

        result = subprocess.run(
            [sys.executable, script_path, "--project", "--json", "list"],
            capture_output=True,
            text=True,
            cwd=tmp_path
        )
        assert result.returncode == 0

        # Output should be valid JSON
        data = json.loads(result.stdout)
        assert "hooks" in data

    def test_export_to_stdout(self, script_path, tmp_path, sample_settings):
        """Test export to stdout."""
        settings_file = tmp_path / ".claude" / "settings.json"
        settings_file.parent.mkdir(parents=True)
        settings_file.write_text(json.dumps(sample_settings, indent=2))

        result = subprocess.run(
            [sys.executable, script_path, "--project", "export"],
            capture_output=True,
            text=True,
            cwd=tmp_path
        )
        assert result.returncode == 0

        # Output should be valid JSON
        data = json.loads(result.stdout)
        assert "hooks" in data
        assert "version" in data

    def test_export_to_file(self, script_path, tmp_path, sample_settings):
        """Test export to file."""
        settings_file = tmp_path / ".claude" / "settings.json"
        settings_file.parent.mkdir(parents=True)
        settings_file.write_text(json.dumps(sample_settings, indent=2))

        export_file = tmp_path / "export.json"

        result = subprocess.run(
            [sys.executable, script_path, "--project", "export", str(export_file)],
            capture_output=True,
            text=True,
            cwd=tmp_path
        )
        assert result.returncode == 0
        assert export_file.exists()

        data = json.loads(export_file.read_text())
        assert "hooks" in data

    def test_visualize_terminal_format(self, script_path, tmp_path, sample_settings):
        """Test visualize command with terminal format."""
        settings_file = tmp_path / ".claude" / "settings.json"
        settings_file.parent.mkdir(parents=True)
        settings_file.write_text(json.dumps(sample_settings, indent=2))

        result = subprocess.run(
            [sys.executable, script_path, "--project", "visualize", "--format", "terminal"],
            capture_output=True,
            text=True,
            cwd=tmp_path
        )
        assert result.returncode == 0
        assert "Claude Code Extensions" in result.stdout

    def test_visualize_markdown_format(self, script_path, tmp_path, sample_settings):
        """Test visualize command with markdown format."""
        settings_file = tmp_path / ".claude" / "settings.json"
        settings_file.parent.mkdir(parents=True)
        settings_file.write_text(json.dumps(sample_settings, indent=2))

        result = subprocess.run(
            [sys.executable, script_path, "--project", "visualize", "--format", "markdown"],
            capture_output=True,
            text=True,
            cwd=tmp_path
        )
        assert result.returncode == 0
        assert "# Claude Code Extensions" in result.stdout

    def test_visualize_html_creates_file(self, script_path, tmp_path, sample_settings):
        """Test visualize command with HTML format creates file."""
        settings_file = tmp_path / ".claude" / "settings.json"
        settings_file.parent.mkdir(parents=True)
        settings_file.write_text(json.dumps(sample_settings, indent=2))

        result = subprocess.run(
            [sys.executable, script_path, "--project", "visualize", "--format", "html"],
            capture_output=True,
            text=True,
            cwd=tmp_path
        )
        assert result.returncode == 0

        # HTML defaults to creating a file
        html_file = tmp_path / "claude-extensions.html"
        assert html_file.exists()


class TestCLIErrorHandling:
    """Tests for CLI error handling."""

    def test_show_nonexistent_hook(self, tmp_path, sample_settings, capsys):
        """Test show command with non-existent hook."""
        settings_file = tmp_path / ".claude" / "settings.json"
        settings_file.parent.mkdir(parents=True)
        settings_file.write_text(json.dumps(sample_settings, indent=2))

        with patch('sys.argv', ['hooks_manager', '--project', 'show', 'nonexistent']):
            with patch.object(Path, 'cwd', return_value=tmp_path):
                result = main()

        assert result == 1

    def test_enable_nonexistent_hook(self, tmp_path, sample_settings):
        """Test enable command with non-existent hook."""
        settings_file = tmp_path / ".claude" / "settings.json"
        settings_file.parent.mkdir(parents=True)
        settings_file.write_text(json.dumps(sample_settings, indent=2))

        with patch('sys.argv', ['hooks_manager', '--project', 'enable', 'nonexistent']):
            with patch.object(Path, 'cwd', return_value=tmp_path):
                result = main()

        assert result == 1

    def test_import_nonexistent_file(self, tmp_path):
        """Test import command with non-existent file."""
        settings_dir = tmp_path / ".claude"
        settings_dir.mkdir(parents=True)

        with patch('sys.argv', ['hooks_manager', '--project', 'import', 'nonexistent.json']):
            with patch.object(Path, 'cwd', return_value=tmp_path):
                result = main()

        assert result == 1

    def test_invalid_settings_json(self, tmp_path, capsys):
        """Test with invalid JSON in settings file."""
        settings_file = tmp_path / ".claude" / "settings.json"
        settings_file.parent.mkdir(parents=True)
        settings_file.write_text("not valid json")

        with patch('sys.argv', ['hooks_manager', '--project', 'list']):
            with patch.object(Path, 'cwd', return_value=tmp_path):
                with pytest.raises(SystemExit):
                    main()
