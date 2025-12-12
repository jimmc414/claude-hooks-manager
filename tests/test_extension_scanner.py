"""Tests for ExtensionScanner class."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from hooks_manager import ExtensionScanner, SkillInfo, CommandInfo, HookInfo, ExtensionsData


class TestExtensionScannerInit:
    """Tests for ExtensionScanner initialization."""

    def test_init_default_path(self):
        """Test default settings path is ~/.claude/settings.json."""
        scanner = ExtensionScanner()
        expected_path = Path.home() / ".claude" / "settings.json"
        assert scanner.settings_path == expected_path

    def test_init_custom_path(self, tmp_path):
        """Test custom settings path."""
        custom_path = tmp_path / "custom_settings.json"
        scanner = ExtensionScanner(settings_path=custom_path)
        assert scanner.settings_path == custom_path

    def test_claude_dir_is_home_claude(self):
        """Test claude_dir is set to ~/.claude."""
        scanner = ExtensionScanner()
        expected_dir = Path.home() / ".claude"
        assert scanner.claude_dir == expected_dir


class TestExtensionScannerSkills:
    """Tests for skill scanning."""

    def test_scan_skills_empty_directory(self, tmp_path):
        """Test scanning when skills directory is empty."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        skills_dir = claude_dir / "skills"
        skills_dir.mkdir()

        scanner = ExtensionScanner()
        scanner.claude_dir = claude_dir

        skills = scanner.scan_skills()
        assert skills == []

    def test_scan_skills_no_directory(self, tmp_path):
        """Test scanning when skills directory doesn't exist."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        scanner = ExtensionScanner()
        scanner.claude_dir = claude_dir

        skills = scanner.scan_skills()
        assert skills == []

    def test_scan_skills_with_skill(self, tmp_path):
        """Test scanning with a valid skill."""
        claude_dir = tmp_path / ".claude"
        skills_dir = claude_dir / "skills" / "my-skill"
        skills_dir.mkdir(parents=True)

        skill_file = skills_dir / "SKILL.md"
        skill_file.write_text("""# My Skill
This is a test skill.
Triggers: test, demo
""")

        scanner = ExtensionScanner()
        scanner.claude_dir = claude_dir

        skills = scanner.scan_skills()

        assert len(skills) == 1
        assert skills[0].name == "My Skill"
        assert skills[0].description == "This is a test skill."
        assert skills[0].triggers == ["test", "demo"]

    def test_scan_skills_multiple_skills(self, tmp_path):
        """Test scanning multiple skills."""
        claude_dir = tmp_path / ".claude"

        for name in ["skill-a", "skill-b", "skill-c"]:
            skill_dir = claude_dir / "skills" / name
            skill_dir.mkdir(parents=True)
            skill_file = skill_dir / "SKILL.md"
            skill_file.write_text(f"# {name.title()}\nDescription for {name}")

        scanner = ExtensionScanner()
        scanner.claude_dir = claude_dir

        skills = scanner.scan_skills()

        assert len(skills) == 3
        # Skills should be sorted alphabetically
        assert skills[0].name == "Skill-A"

    def test_scan_skills_no_skill_md(self, tmp_path):
        """Test scanning skill directory without SKILL.md."""
        claude_dir = tmp_path / ".claude"
        skill_dir = claude_dir / "skills" / "incomplete-skill"
        skill_dir.mkdir(parents=True)
        # No SKILL.md file

        scanner = ExtensionScanner()
        scanner.claude_dir = claude_dir

        skills = scanner.scan_skills()
        assert skills == []

    def test_scan_skills_uses_directory_name_as_fallback(self, tmp_path):
        """Test that directory name is used when no # header found."""
        claude_dir = tmp_path / ".claude"
        skill_dir = claude_dir / "skills" / "fallback-skill"
        skill_dir.mkdir(parents=True)

        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("Just a description, no header")

        scanner = ExtensionScanner()
        scanner.claude_dir = claude_dir

        skills = scanner.scan_skills()

        assert len(skills) == 1
        assert skills[0].name == "fallback-skill"


class TestExtensionScannerCommands:
    """Tests for command scanning."""

    def test_scan_commands_empty_directory(self, tmp_path):
        """Test scanning when commands directory is empty."""
        claude_dir = tmp_path / ".claude"
        commands_dir = claude_dir / "commands"
        commands_dir.mkdir(parents=True)

        scanner = ExtensionScanner()
        scanner.claude_dir = claude_dir

        commands = scanner.scan_commands()
        assert commands == []

    def test_scan_commands_no_directory(self, tmp_path):
        """Test scanning when commands directory doesn't exist."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        scanner = ExtensionScanner()
        scanner.claude_dir = claude_dir

        commands = scanner.scan_commands()
        assert commands == []

    def test_scan_commands_with_command(self, tmp_path):
        """Test scanning with a valid command."""
        claude_dir = tmp_path / ".claude"
        commands_dir = claude_dir / "commands"
        commands_dir.mkdir(parents=True)

        cmd_file = commands_dir / "my-command.md"
        cmd_file.write_text("""# My Command
This is a test command.
""")

        scanner = ExtensionScanner()
        scanner.claude_dir = claude_dir

        commands = scanner.scan_commands()

        assert len(commands) == 1
        assert commands[0].name == "My Command"
        assert commands[0].description == "This is a test command."

    def test_scan_commands_multiple_commands(self, tmp_path):
        """Test scanning multiple commands."""
        claude_dir = tmp_path / ".claude"
        commands_dir = claude_dir / "commands"
        commands_dir.mkdir(parents=True)

        for name in ["cmd-a", "cmd-b", "cmd-c"]:
            cmd_file = commands_dir / f"{name}.md"
            cmd_file.write_text(f"# {name.title()}\nDescription for {name}")

        scanner = ExtensionScanner()
        scanner.claude_dir = claude_dir

        commands = scanner.scan_commands()

        assert len(commands) == 3

    def test_scan_commands_uses_filename_as_fallback(self, tmp_path):
        """Test that filename is used when no # header found."""
        claude_dir = tmp_path / ".claude"
        commands_dir = claude_dir / "commands"
        commands_dir.mkdir(parents=True)

        cmd_file = commands_dir / "fallback.md"
        cmd_file.write_text("Just a description, no header")

        scanner = ExtensionScanner()
        scanner.claude_dir = claude_dir

        commands = scanner.scan_commands()

        assert len(commands) == 1
        assert commands[0].name == "fallback"

    def test_scan_commands_ignores_non_md_files(self, tmp_path):
        """Test that non-.md files are ignored."""
        claude_dir = tmp_path / ".claude"
        commands_dir = claude_dir / "commands"
        commands_dir.mkdir(parents=True)

        # Create both .md and non-.md files
        (commands_dir / "valid.md").write_text("# Valid Command")
        (commands_dir / "invalid.txt").write_text("# Invalid")
        (commands_dir / "also-invalid.json").write_text("{}")

        scanner = ExtensionScanner()
        scanner.claude_dir = claude_dir

        commands = scanner.scan_commands()

        assert len(commands) == 1
        assert commands[0].name == "Valid Command"


class TestExtensionScannerHooks:
    """Tests for hook scanning."""

    def test_scan_hooks_no_settings_file(self, tmp_path):
        """Test scanning when settings.json doesn't exist."""
        scanner = ExtensionScanner(settings_path=tmp_path / "nonexistent.json")

        hooks = scanner.scan_hooks()
        assert hooks == []

    def test_scan_hooks_empty_settings(self, tmp_path):
        """Test scanning with empty settings."""
        settings_file = tmp_path / "settings.json"
        settings_file.write_text('{"hooks": {}}')

        scanner = ExtensionScanner(settings_path=settings_file)

        hooks = scanner.scan_hooks()
        assert hooks == []

    def test_scan_hooks_with_enabled_hooks(self, tmp_path, sample_settings):
        """Test scanning enabled hooks."""
        settings_file = tmp_path / "settings.json"
        settings_file.write_text(json.dumps(sample_settings))

        scanner = ExtensionScanner(settings_path=settings_file)

        hooks = scanner.scan_hooks()
        enabled_hooks = [h for h in hooks if h.enabled]

        assert len(enabled_hooks) == 3

    def test_scan_hooks_with_disabled_hooks(self, tmp_path, sample_settings):
        """Test scanning disabled hooks."""
        settings_file = tmp_path / "settings.json"
        settings_file.write_text(json.dumps(sample_settings))

        scanner = ExtensionScanner(settings_path=settings_file)

        hooks = scanner.scan_hooks()
        disabled_hooks = [h for h in hooks if not h.enabled]

        assert len(disabled_hooks) == 1
        assert disabled_hooks[0].name == "slow-tests"

    def test_scan_hooks_invalid_json(self, tmp_path):
        """Test scanning with invalid JSON in settings."""
        settings_file = tmp_path / "settings.json"
        settings_file.write_text("not valid json")

        scanner = ExtensionScanner(settings_path=settings_file)

        hooks = scanner.scan_hooks()
        assert hooks == []

    def test_scan_hooks_hook_without_name(self, tmp_path):
        """Test scanning hook without _name generates name."""
        settings = {
            "hooks": {
                "PostToolUse": [
                    {"matcher": "*", "hooks": []}
                ]
            }
        }
        settings_file = tmp_path / "settings.json"
        settings_file.write_text(json.dumps(settings))

        scanner = ExtensionScanner(settings_path=settings_file)

        hooks = scanner.scan_hooks()

        assert len(hooks) == 1
        assert hooks[0].name == "PostToolUse#0"


class TestExtensionScannerScanAll:
    """Tests for scan_all method."""

    def test_scan_all_returns_extensions_data(self, tmp_path, sample_settings):
        """Test scan_all returns ExtensionsData instance."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        # Create settings file
        settings_file = claude_dir / "settings.json"
        settings_file.write_text(json.dumps(sample_settings))

        # Create a skill
        skill_dir = claude_dir / "skills" / "test-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Test Skill\nDescription")

        # Create a command
        commands_dir = claude_dir / "commands"
        commands_dir.mkdir()
        (commands_dir / "test-cmd.md").write_text("# Test Cmd\nDescription")

        scanner = ExtensionScanner(settings_path=settings_file)
        scanner.claude_dir = claude_dir

        data = scanner.scan_all()

        assert isinstance(data, ExtensionsData)
        assert len(data.skills) == 1
        assert len(data.commands) == 1
        assert len(data.hooks) == 4  # 3 enabled + 1 disabled

    def test_scan_all_empty_environment(self, tmp_path):
        """Test scan_all with empty environment."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        scanner = ExtensionScanner(settings_path=tmp_path / "nonexistent.json")
        scanner.claude_dir = claude_dir

        data = scanner.scan_all()

        assert isinstance(data, ExtensionsData)
        assert data.skills == []
        assert data.commands == []
        assert data.hooks == []


class TestParseSkillFile:
    """Tests for _parse_skill_file method."""

    def test_parse_complete_skill_file(self, tmp_path):
        """Test parsing a complete SKILL.md file."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("""# Complete Skill
This skill does everything.
Triggers: alpha, beta, gamma
Some more content...
""")

        scanner = ExtensionScanner()
        name, description, triggers = scanner._parse_skill_file(skill_file)

        assert name == "Complete Skill"
        assert description == "This skill does everything."
        assert triggers == ["alpha", "beta", "gamma"]

    def test_parse_skill_file_no_triggers(self, tmp_path):
        """Test parsing SKILL.md without triggers."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("""# No Triggers Skill
Just a description.
""")

        scanner = ExtensionScanner()
        name, description, triggers = scanner._parse_skill_file(skill_file)

        assert name == "No Triggers Skill"
        assert description == "Just a description."
        assert triggers == []

    def test_parse_skill_file_empty(self, tmp_path):
        """Test parsing empty SKILL.md."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("")

        scanner = ExtensionScanner()
        name, description, triggers = scanner._parse_skill_file(skill_file)

        assert name == ""
        assert description == ""
        assert triggers == []

    def test_parse_skill_file_nonexistent(self, tmp_path):
        """Test parsing nonexistent file returns empty values."""
        scanner = ExtensionScanner()
        name, description, triggers = scanner._parse_skill_file(tmp_path / "nonexistent.md")

        assert name == ""
        assert description == ""
        assert triggers == []


class TestParseCommandFile:
    """Tests for _parse_command_file method."""

    def test_parse_complete_command_file(self, tmp_path):
        """Test parsing a complete command file."""
        cmd_file = tmp_path / "test-cmd.md"
        cmd_file.write_text("""# Test Command
This command tests things.
More content here.
""")

        scanner = ExtensionScanner()
        name, description = scanner._parse_command_file(cmd_file)

        assert name == "Test Command"
        assert description == "This command tests things."

    def test_parse_command_file_no_header(self, tmp_path):
        """Test parsing command file without header."""
        cmd_file = tmp_path / "no-header.md"
        cmd_file.write_text("""Just a description without header.
More content.
""")

        scanner = ExtensionScanner()
        name, description = scanner._parse_command_file(cmd_file)

        assert name == "no-header"  # Uses filename
        assert description == "Just a description without header."

    def test_parse_command_file_empty(self, tmp_path):
        """Test parsing empty command file."""
        cmd_file = tmp_path / "empty.md"
        cmd_file.write_text("")

        scanner = ExtensionScanner()
        name, description = scanner._parse_command_file(cmd_file)

        assert name == "empty"  # Uses filename
        assert description == ""
