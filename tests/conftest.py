"""Pytest configuration and fixtures for hooks_manager tests."""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from hooks_manager import (
    HooksManager,
    ExtensionScanner,
    HookInfo,
    SkillInfo,
    CommandInfo,
    ExtensionsData,
    create_parser,
)


@pytest.fixture
def sample_settings() -> Dict[str, Any]:
    """Return sample settings.json content with hooks."""
    return {
        "hooks": {
            "PostToolUse": [
                {
                    "_name": "lint",
                    "matcher": "Write|Edit",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "npm run lint --fix",
                            "timeout": 60
                        }
                    ]
                },
                {
                    "_name": "format",
                    "matcher": "Write",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "prettier --write .",
                            "timeout": 30
                        }
                    ]
                }
            ],
            "PreToolUse": [
                {
                    "_name": "confirm-dangerous",
                    "matcher": "Bash",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "python3 ~/.claude/hooks/confirm_dangerous.py",
                            "timeout": 10
                        }
                    ]
                }
            ]
        },
        "_disabled_hooks": {
            "PostToolUse": [
                {
                    "_name": "slow-tests",
                    "matcher": "Write|Edit",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "npm run test:integration",
                            "timeout": 300
                        }
                    ]
                }
            ]
        }
    }


@pytest.fixture
def empty_settings() -> Dict[str, Any]:
    """Return empty settings.json content."""
    return {"hooks": {}, "_disabled_hooks": {}}


@pytest.fixture
def temp_settings_file(tmp_path, sample_settings):
    """Create a temporary settings.json file."""
    settings_dir = tmp_path / ".claude"
    settings_dir.mkdir(parents=True)
    settings_file = settings_dir / "settings.json"
    settings_file.write_text(json.dumps(sample_settings, indent=2))
    return settings_file


@pytest.fixture
def temp_empty_settings_file(tmp_path, empty_settings):
    """Create a temporary empty settings.json file."""
    settings_dir = tmp_path / ".claude"
    settings_dir.mkdir(parents=True)
    settings_file = settings_dir / "settings.json"
    settings_file.write_text(json.dumps(empty_settings, indent=2))
    return settings_file


@pytest.fixture
def temp_claude_dir(tmp_path):
    """Create a temporary .claude directory structure."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir(parents=True)

    # Create commands directory with sample command
    commands_dir = claude_dir / "commands"
    commands_dir.mkdir()

    cmd_file = commands_dir / "test-cmd.md"
    cmd_file.write_text("""# Test Command
This is a test command for unit testing.
""")

    # Create skills directory with sample skill
    skills_dir = claude_dir / "skills"
    skills_dir.mkdir()

    skill_dir = skills_dir / "test-skill"
    skill_dir.mkdir()

    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text("""# Test Skill
This is a test skill for unit testing.
Triggers: test, sample, example
""")

    return claude_dir


@pytest.fixture
def mock_args():
    """Create mock argparse Namespace for HooksManager."""
    class MockArgs:
        def __init__(self):
            self.global_scope = False
            self.project_scope = False
            self.json = False
            self.quiet = False
            self.dry_run = False
            self.no_color = True
            self.no_backup = True
            self.force = True
            self.command = None
            self.name = None
            self.file = None
            self.format = 'terminal'
            self.output_file = None
            self.hook_name = None
            self.event = None
            self.hook_command = None
            self.matcher = '*'
            self.timeout = 60

    return MockArgs()


@pytest.fixture
def hooks_manager(tmp_path, sample_settings, mock_args):
    """Create a HooksManager instance with temporary settings file."""
    settings_dir = tmp_path / ".claude"
    settings_dir.mkdir(parents=True)
    settings_file = settings_dir / "settings.json"
    settings_file.write_text(json.dumps(sample_settings, indent=2))

    # Patch the settings path resolution
    mock_args.project_scope = True

    with patch.object(Path, 'cwd', return_value=tmp_path):
        manager = HooksManager(mock_args)
        manager.settings_path = settings_file
        manager.settings = sample_settings.copy()

    return manager


@pytest.fixture
def sample_hook_info() -> HookInfo:
    """Return a sample HookInfo instance."""
    return HookInfo(
        name="test-hook",
        event="PostToolUse",
        enabled=True,
        matcher="Write|Edit",
        commands=[{"type": "command", "command": "echo test", "timeout": 30}],
        raw={"_name": "test-hook", "matcher": "Write|Edit", "hooks": [{"type": "command", "command": "echo test", "timeout": 30}]}
    )


@pytest.fixture
def sample_skill_info(tmp_path) -> SkillInfo:
    """Return a sample SkillInfo instance."""
    return SkillInfo(
        name="Test Skill",
        description="A test skill for unit testing",
        triggers=["test", "sample"],
        path=tmp_path / "SKILL.md"
    )


@pytest.fixture
def sample_command_info(tmp_path) -> CommandInfo:
    """Return a sample CommandInfo instance."""
    return CommandInfo(
        name="test-cmd",
        description="A test command for unit testing",
        path=tmp_path / "test-cmd.md"
    )


@pytest.fixture
def sample_extensions_data(sample_skill_info, sample_command_info, sample_hook_info) -> ExtensionsData:
    """Return a sample ExtensionsData instance."""
    return ExtensionsData(
        skills=[sample_skill_info],
        commands=[sample_command_info],
        hooks=[sample_hook_info]
    )


@pytest.fixture
def parser():
    """Return the argument parser."""
    return create_parser()


@pytest.fixture(autouse=True)
def reset_stdout(monkeypatch):
    """Ensure stdout.isatty() returns False during tests."""
    monkeypatch.setattr('sys.stdout.isatty', lambda: False)
