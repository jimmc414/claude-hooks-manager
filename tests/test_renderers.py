"""Tests for renderer classes."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from hooks_manager import ExtensionsData, SkillInfo, CommandInfo, HookInfo, Colors
from renderers import TerminalRenderer, HTMLRenderer, MarkdownRenderer
from renderers.base import BaseRenderer


class TestBaseRenderer:
    """Tests for BaseRenderer abstract class."""

    def test_base_renderer_is_abstract(self):
        """Test that BaseRenderer cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseRenderer()

    def test_render_to_file(self, tmp_path, sample_extensions_data):
        """Test render_to_file writes content to file."""
        # Use a concrete implementation
        renderer = TerminalRenderer(use_color=False)
        output_file = tmp_path / "output.txt"

        renderer.render_to_file(sample_extensions_data, output_file)

        assert output_file.exists()
        content = output_file.read_text()
        assert "Claude Code Extensions" in content


class TestTerminalRenderer:
    """Tests for TerminalRenderer class."""

    def test_init_default_color(self):
        """Test default color setting is True."""
        renderer = TerminalRenderer()
        assert renderer.use_color is True

    def test_init_no_color(self):
        """Test color can be disabled."""
        renderer = TerminalRenderer(use_color=False)
        assert renderer.use_color is False

    def test_render_returns_string(self, sample_extensions_data):
        """Test render returns a string."""
        renderer = TerminalRenderer(use_color=False)
        result = renderer.render(sample_extensions_data)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_includes_header(self, sample_extensions_data):
        """Test render includes header."""
        renderer = TerminalRenderer(use_color=False)
        result = renderer.render(sample_extensions_data)

        assert "Claude Code Extensions" in result

    def test_render_includes_sections(self, sample_extensions_data):
        """Test render includes all sections."""
        renderer = TerminalRenderer(use_color=False)
        result = renderer.render(sample_extensions_data)

        assert "Skills" in result
        assert "Commands" in result
        assert "Hooks" in result

    def test_render_empty_data(self):
        """Test render with empty data."""
        renderer = TerminalRenderer(use_color=False)
        empty_data = ExtensionsData(skills=[], commands=[], hooks=[])
        result = renderer.render(empty_data)

        assert "(none)" in result

    def test_render_skill_info(self, sample_skill_info):
        """Test rendering skill information."""
        renderer = TerminalRenderer(use_color=False)
        data = ExtensionsData(skills=[sample_skill_info], commands=[], hooks=[])
        result = renderer.render(data)

        assert sample_skill_info.name in result
        assert sample_skill_info.description in result

    def test_render_command_info(self, sample_command_info):
        """Test rendering command information."""
        renderer = TerminalRenderer(use_color=False)
        data = ExtensionsData(skills=[], commands=[sample_command_info], hooks=[])
        result = renderer.render(data)

        assert f"/{sample_command_info.name}" in result

    def test_render_hook_info(self, sample_hook_info):
        """Test rendering hook information."""
        renderer = TerminalRenderer(use_color=False)
        data = ExtensionsData(skills=[], commands=[], hooks=[sample_hook_info])
        result = renderer.render(data)

        assert sample_hook_info.name in result
        assert sample_hook_info.event in result
        assert "enabled" in result

    def test_render_disabled_hook(self, tmp_path):
        """Test rendering disabled hook."""
        disabled_hook = HookInfo(
            name="disabled-hook",
            event="PostToolUse",
            enabled=False,
            matcher="*",
            commands=[],
            raw={}
        )
        renderer = TerminalRenderer(use_color=False)
        data = ExtensionsData(skills=[], commands=[], hooks=[disabled_hook])
        result = renderer.render(data)

        assert "disabled" in result

    def test_color_applied_when_enabled(self, sample_extensions_data):
        """Test that ANSI codes are included when color is enabled."""
        renderer = TerminalRenderer(use_color=True)
        result = renderer.render(sample_extensions_data)

        # Should contain ANSI escape codes
        assert "\033[" in result

    def test_color_not_applied_when_disabled(self, sample_extensions_data):
        """Test that ANSI codes are not included when color is disabled."""
        renderer = TerminalRenderer(use_color=False)
        result = renderer.render(sample_extensions_data)

        # Should not contain ANSI escape codes
        assert "\033[" not in result

    def test_tree_characters(self, sample_extensions_data):
        """Test tree drawing characters are present."""
        renderer = TerminalRenderer(use_color=False)
        result = renderer.render(sample_extensions_data)

        # Should contain tree characters
        assert "├" in result or "└" in result


class TestHTMLRenderer:
    """Tests for HTMLRenderer class."""

    def test_render_returns_html(self, sample_extensions_data):
        """Test render returns valid HTML structure."""
        renderer = HTMLRenderer()
        result = renderer.render(sample_extensions_data)

        assert result.startswith("<!DOCTYPE html>")
        assert "<html" in result
        assert "</html>" in result

    def test_render_includes_sections(self, sample_extensions_data):
        """Test render includes all sections."""
        renderer = HTMLRenderer()
        result = renderer.render(sample_extensions_data)

        assert "Skills" in result
        assert "Commands" in result
        assert "Hooks" in result

    def test_render_includes_css(self, sample_extensions_data):
        """Test render includes embedded CSS."""
        renderer = HTMLRenderer()
        result = renderer.render(sample_extensions_data)

        assert "<style>" in result
        assert "</style>" in result

    def test_render_includes_javascript(self, sample_extensions_data):
        """Test render includes JavaScript for collapsible sections."""
        renderer = HTMLRenderer()
        result = renderer.render(sample_extensions_data)

        assert "<script>" in result
        assert "toggleSection" in result

    def test_render_empty_data(self):
        """Test render with empty data."""
        renderer = HTMLRenderer()
        empty_data = ExtensionsData(skills=[], commands=[], hooks=[])
        result = renderer.render(empty_data)

        assert "No skills configured" in result
        assert "No commands configured" in result
        assert "No hooks configured" in result

    def test_render_escapes_html(self, tmp_path):
        """Test that HTML special characters are escaped."""
        skill = SkillInfo(
            name="<malicious>alert('xss')</malicious>",
            description="Test & <dangerous> \"quotes\"",
            triggers=["<tag>"],
            path=tmp_path / "skill.md"
        )
        renderer = HTMLRenderer()
        data = ExtensionsData(skills=[skill], commands=[], hooks=[])
        result = renderer.render(data)

        # Should escape dangerous characters in user content
        # Note: <script> appears in the JS code, so we use <malicious> to test
        assert "<malicious>" not in result  # Should be escaped
        assert "&lt;malicious&gt;" in result
        assert "&amp;" in result

    def test_render_hook_status_classes(self, tmp_path):
        """Test enabled/disabled hooks have correct CSS classes."""
        enabled_hook = HookInfo(
            name="enabled", event="PostToolUse", enabled=True,
            matcher="*", commands=[], raw={}
        )
        disabled_hook = HookInfo(
            name="disabled", event="PostToolUse", enabled=False,
            matcher="*", commands=[], raw={}
        )
        renderer = HTMLRenderer()
        data = ExtensionsData(skills=[], commands=[], hooks=[enabled_hook, disabled_hook])
        result = renderer.render(data)

        assert "status-enabled" in result
        assert "status-disabled" in result

    def test_render_dark_mode_support(self, sample_extensions_data):
        """Test CSS includes dark mode support."""
        renderer = HTMLRenderer()
        result = renderer.render(sample_extensions_data)

        assert "prefers-color-scheme" in result

    def test_render_collapsible_sections(self, sample_extensions_data):
        """Test sections are collapsible."""
        renderer = HTMLRenderer()
        result = renderer.render(sample_extensions_data)

        assert "collapsible" in result
        assert "aria-expanded" in result


class TestMarkdownRenderer:
    """Tests for MarkdownRenderer class."""

    def test_render_returns_markdown(self, sample_extensions_data):
        """Test render returns valid markdown."""
        renderer = MarkdownRenderer()
        result = renderer.render(sample_extensions_data)

        # Should start with header
        assert result.startswith("# Claude Code Extensions")

    def test_render_includes_sections(self, sample_extensions_data):
        """Test render includes all sections."""
        renderer = MarkdownRenderer()
        result = renderer.render(sample_extensions_data)

        assert "## Skills" in result
        assert "## Commands" in result
        assert "## Hooks" in result

    def test_render_includes_tables(self, sample_extensions_data):
        """Test render includes markdown tables."""
        renderer = MarkdownRenderer()
        result = renderer.render(sample_extensions_data)

        # Table header separators
        assert "|---" in result

    def test_render_empty_data(self):
        """Test render with empty data."""
        renderer = MarkdownRenderer()
        empty_data = ExtensionsData(skills=[], commands=[], hooks=[])
        result = renderer.render(empty_data)

        assert "*No skills found.*" in result
        assert "*No commands found.*" in result
        assert "*No hooks found.*" in result

    def test_render_escapes_markdown_pipes(self, tmp_path):
        """Test that pipe characters are escaped in tables."""
        skill = SkillInfo(
            name="test|skill",
            description="desc|with|pipes",
            triggers=["a|b"],
            path=tmp_path / "skill.md"
        )
        renderer = MarkdownRenderer()
        data = ExtensionsData(skills=[skill], commands=[], hooks=[])
        result = renderer.render(data)

        # Pipes should be escaped
        assert "\\|" in result

    def test_render_hook_status_emoji(self, tmp_path):
        """Test enabled/disabled hooks have status emoji."""
        enabled_hook = HookInfo(
            name="enabled", event="PostToolUse", enabled=True,
            matcher="*", commands=[], raw={}
        )
        disabled_hook = HookInfo(
            name="disabled", event="PostToolUse", enabled=False,
            matcher="*", commands=[], raw={}
        )
        renderer = MarkdownRenderer()
        data = ExtensionsData(skills=[], commands=[], hooks=[enabled_hook, disabled_hook])
        result = renderer.render(data)

        assert "✅" in result  # Enabled
        assert "⚠️" in result  # Disabled

    def test_render_command_slash_prefix(self, sample_command_info):
        """Test commands are prefixed with /."""
        renderer = MarkdownRenderer()
        data = ExtensionsData(skills=[], commands=[sample_command_info], hooks=[])
        result = renderer.render(data)

        assert f"`/{sample_command_info.name}`" in result

    def test_render_total_count(self, sample_extensions_data):
        """Test total extensions count is shown."""
        renderer = MarkdownRenderer()
        result = renderer.render(sample_extensions_data)

        assert "**Total Extensions:**" in result


class TestTUIRenderer:
    """Tests for TUIRenderer class (limited testing due to curses dependency)."""

    def test_init_default_values(self):
        """Test TUIRenderer initializes with default values."""
        from renderers import TUIRenderer

        renderer = TUIRenderer()

        assert renderer.current_section == 0
        assert renderer.current_item == 0
        assert renderer.scroll_offset == 0
        assert renderer.show_detail is False
        assert renderer.show_help is False

    def test_get_sections(self, sample_extensions_data):
        """Test _get_sections returns correct structure."""
        from renderers import TUIRenderer

        renderer = TUIRenderer()
        renderer.data = sample_extensions_data

        sections = renderer._get_sections()

        assert len(sections) == 3
        assert sections[0][0] == "Skills"
        assert sections[1][0] == "Commands"
        assert sections[2][0] == "Hooks"

    def test_get_sections_empty_data(self):
        """Test _get_sections with no data."""
        from renderers import TUIRenderer

        renderer = TUIRenderer()
        renderer.data = None

        sections = renderer._get_sections()
        assert sections == []

    def test_format_skill_detail(self, sample_skill_info):
        """Test _format_skill_detail returns correct lines."""
        from renderers import TUIRenderer

        renderer = TUIRenderer()
        lines = renderer._format_skill_detail(sample_skill_info, 80)

        assert any("Name:" in line for line in lines)
        assert any("Description:" in line for line in lines)
        assert any("Triggers:" in line for line in lines)
        assert any("Path:" in line for line in lines)

    def test_format_command_detail(self, sample_command_info):
        """Test _format_command_detail returns correct lines."""
        from renderers import TUIRenderer

        renderer = TUIRenderer()
        lines = renderer._format_command_detail(sample_command_info, 80)

        assert any("Command:" in line for line in lines)
        assert any("Description:" in line for line in lines)
        assert any("Path:" in line for line in lines)

    def test_format_hook_detail(self, sample_hook_info):
        """Test _format_hook_detail returns correct lines."""
        from renderers import TUIRenderer

        renderer = TUIRenderer()
        lines = renderer._format_hook_detail(sample_hook_info, 80)

        assert any("Name:" in line for line in lines)
        assert any("Status:" in line for line in lines)
        assert any("Event:" in line for line in lines)
        assert any("Matcher:" in line for line in lines)
        assert any("Commands" in line for line in lines)

    def test_render_returns_empty_string_on_error(self, sample_extensions_data):
        """Test render returns empty string when curses fails."""
        from renderers import TUIRenderer

        renderer = TUIRenderer()

        # Mock curses.wrapper to simulate curses.error
        import curses
        with patch('renderers.tui.curses.wrapper', side_effect=curses.error("curses error")):
            result = renderer.render(sample_extensions_data)

        # Should handle error gracefully
        assert result == "" or "error" in result.lower()


class TestRendererIntegration:
    """Integration tests across renderers."""

    def test_all_renderers_handle_empty_data(self):
        """Test all renderers handle empty data gracefully."""
        empty_data = ExtensionsData(skills=[], commands=[], hooks=[])

        renderers = [
            TerminalRenderer(use_color=False),
            HTMLRenderer(),
            MarkdownRenderer(),
        ]

        for renderer in renderers:
            result = renderer.render(empty_data)
            assert isinstance(result, str)
            assert len(result) > 0

    def test_all_renderers_handle_large_data(self, tmp_path):
        """Test all renderers handle large amounts of data."""
        # Create large dataset
        skills = [
            SkillInfo(name=f"skill-{i}", description=f"Description {i}",
                      triggers=[f"trigger-{i}"], path=tmp_path / f"skill-{i}.md")
            for i in range(50)
        ]
        commands = [
            CommandInfo(name=f"cmd-{i}", description=f"Command {i}",
                        path=tmp_path / f"cmd-{i}.md")
            for i in range(50)
        ]
        hooks = [
            HookInfo(name=f"hook-{i}", event="PostToolUse", enabled=i % 2 == 0,
                     matcher="*", commands=[], raw={})
            for i in range(50)
        ]

        data = ExtensionsData(skills=skills, commands=commands, hooks=hooks)

        renderers = [
            TerminalRenderer(use_color=False),
            HTMLRenderer(),
            MarkdownRenderer(),
        ]

        for renderer in renderers:
            result = renderer.render(data)
            assert isinstance(result, str)
            # Should contain some of the items
            assert "skill-0" in result
            assert "cmd-0" in result
            assert "hook-0" in result

    def test_render_to_file_all_formats(self, tmp_path, sample_extensions_data):
        """Test render_to_file works for all renderers."""
        renderers_and_files = [
            (TerminalRenderer(use_color=False), "output.txt"),
            (HTMLRenderer(), "output.html"),
            (MarkdownRenderer(), "output.md"),
        ]

        for renderer, filename in renderers_and_files:
            output_file = tmp_path / filename
            renderer.render_to_file(sample_extensions_data, output_file)

            assert output_file.exists()
            content = output_file.read_text()
            assert len(content) > 0
