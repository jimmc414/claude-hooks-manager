"""Markdown renderer for documentation-style visualization."""

from pathlib import Path
from typing import List

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from hooks_manager import ExtensionsData, SkillInfo, CommandInfo, HookInfo
from .base import BaseRenderer


class MarkdownRenderer(BaseRenderer):
    """Renders extensions as clean markdown with tables."""

    def __init__(self, use_color: bool = True):
        # Markdown doesn't use terminal colors, but we keep the interface
        super().__init__(use_color)

    def render(self, data: ExtensionsData) -> str:
        """Render extensions data as markdown documentation."""
        lines: List[str] = []

        # Main header
        lines.append("# Claude Code Extensions")
        lines.append("")

        # Summary
        total = len(data.skills) + len(data.commands) + len(data.hooks)
        lines.append(f"**Total Extensions:** {total}")
        lines.append("")

        # Render each section
        lines.extend(self._render_skills_section(data.skills))
        lines.extend(self._render_commands_section(data.commands))
        lines.extend(self._render_hooks_section(data.hooks))

        return "\n".join(lines)

    def _escape_markdown(self, text: str) -> str:
        """Escape special markdown characters in table cells."""
        if not text:
            return ""
        # Escape pipe characters which break tables
        text = text.replace("|", "\\|")
        # Escape newlines
        text = text.replace("\n", " ")
        return text

    def _render_skills_section(self, skills: List[SkillInfo]) -> List[str]:
        """Render the skills section as a markdown table."""
        lines: List[str] = []

        lines.append("## Skills")
        lines.append("")

        if not skills:
            lines.append("*No skills found.*")
            lines.append("")
            return lines

        # Table header
        lines.append("| Name | Description | Triggers | Path |")
        lines.append("|------|-------------|----------|------|")

        # Table rows
        for skill in skills:
            name = self._escape_markdown(skill.name)
            desc = self._escape_markdown(skill.description or "-")
            triggers = self._escape_markdown(", ".join(skill.triggers) if skill.triggers else "-")
            path = self._escape_markdown(str(skill.path))

            lines.append(f"| {name} | {desc} | {triggers} | `{path}` |")

        lines.append("")
        return lines

    def _render_commands_section(self, commands: List[CommandInfo]) -> List[str]:
        """Render the commands section as a markdown table."""
        lines: List[str] = []

        lines.append("## Commands")
        lines.append("")

        if not commands:
            lines.append("*No commands found.*")
            lines.append("")
            return lines

        # Table header
        lines.append("| Command | Description | Path |")
        lines.append("|---------|-------------|------|")

        # Table rows
        for cmd in commands:
            name = f"`/{self._escape_markdown(cmd.name)}`"
            desc = self._escape_markdown(cmd.description or "-")
            path = self._escape_markdown(str(cmd.path))

            lines.append(f"| {name} | {desc} | `{path}` |")

        lines.append("")
        return lines

    def _render_hooks_section(self, hooks: List[HookInfo]) -> List[str]:
        """Render the hooks section as a markdown table."""
        lines: List[str] = []

        lines.append("## Hooks")
        lines.append("")

        if not hooks:
            lines.append("*No hooks found.*")
            lines.append("")
            return lines

        # Table header
        lines.append("| Name | Event | Status | Matcher | Commands |")
        lines.append("|------|-------|--------|---------|----------|")

        # Table rows
        for hook in hooks:
            name = self._escape_markdown(hook.name)
            event = self._escape_markdown(hook.event)
            status = "✅ Enabled" if hook.enabled else "⚠️ Disabled"
            matcher = self._escape_markdown(hook.matcher or "*")
            cmd_count = len(hook.commands) if hook.commands else 0

            lines.append(f"| {name} | `{event}` | {status} | `{matcher}` | {cmd_count} |")

        lines.append("")
        return lines
