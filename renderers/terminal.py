"""Terminal renderer for tree-style visualization."""

from pathlib import Path
from typing import List

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from hooks_manager import Colors, ExtensionsData, SkillInfo, CommandInfo, HookInfo
from .base import BaseRenderer


class TerminalRenderer(BaseRenderer):
    """Renders extensions as a tree structure for terminal output."""

    # Tree drawing characters
    BRANCH = "├── "
    LAST_BRANCH = "└── "
    VERTICAL = "│   "
    SPACE = "    "

    def __init__(self, use_color: bool = True):
        super().__init__(use_color)

    def _color(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled."""
        if self.use_color:
            return f"{color}{text}{Colors.RESET}"
        return text

    def render(self, data: ExtensionsData) -> str:
        """Render extensions data as a tree structure."""
        lines: List[str] = []

        lines.append(self._color("Claude Code Extensions", Colors.BOLD))
        lines.append("")

        sections = [
            ("Skills", data.skills, self._render_skill),
            ("Commands", data.commands, self._render_command),
            ("Hooks", data.hooks, self._render_hook),
        ]

        for i, (title, items, renderer) in enumerate(sections):
            is_last_section = i == len(sections) - 1
            branch = self.LAST_BRANCH if is_last_section else self.BRANCH
            prefix = self.SPACE if is_last_section else self.VERTICAL

            # Section header with count
            count = len(items)
            header = f"{title} ({count})"
            lines.append(f"{branch}{self._color(header, Colors.BLUE)}")

            if not items:
                lines.append(f"{prefix}{self.LAST_BRANCH}{self._color('(none)', Colors.DIM)}")
            else:
                for j, item in enumerate(items):
                    is_last_item = j == len(items) - 1
                    item_branch = self.LAST_BRANCH if is_last_item else self.BRANCH
                    item_prefix = self.SPACE if is_last_item else self.VERTICAL

                    item_lines = renderer(item)
                    lines.append(f"{prefix}{item_branch}{item_lines[0]}")

                    for detail in item_lines[1:]:
                        lines.append(f"{prefix}{item_prefix}{detail}")

            if not is_last_section:
                lines.append(f"{self.VERTICAL}")

        return "\n".join(lines)

    def _render_skill(self, skill: SkillInfo) -> List[str]:
        """Render a single skill entry."""
        lines = [self._color(skill.name, Colors.GREEN)]

        if skill.description:
            lines.append(f"{self.BRANCH}{self._color('Description:', Colors.DIM)} {skill.description}")

        if skill.triggers:
            triggers_str = ", ".join(skill.triggers)
            lines.append(f"{self.BRANCH}{self._color('Triggers:', Colors.DIM)} {triggers_str}")

        lines.append(f"{self.LAST_BRANCH}{self._color('Path:', Colors.DIM)} {skill.path}")

        return lines

    def _render_command(self, cmd: CommandInfo) -> List[str]:
        """Render a single command entry."""
        lines = [self._color(f"/{cmd.name}", Colors.GREEN)]

        if cmd.description:
            lines.append(f"{self.BRANCH}{self._color('Description:', Colors.DIM)} {cmd.description}")

        lines.append(f"{self.LAST_BRANCH}{self._color('Path:', Colors.DIM)} {cmd.path}")

        return lines

    def _render_hook(self, hook: HookInfo) -> List[str]:
        """Render a single hook entry."""
        status_color = Colors.GREEN if hook.enabled else Colors.YELLOW
        status_text = "enabled" if hook.enabled else "disabled"

        name_display = f"{hook.name} [{self._color(status_text, status_color)}]"
        lines = [name_display]

        lines.append(f"{self.BRANCH}{self._color('Event:', Colors.DIM)} {hook.event}")
        lines.append(f"{self.BRANCH}{self._color('Matcher:', Colors.DIM)} {hook.matcher}")

        if hook.commands:
            cmd_count = len(hook.commands)
            lines.append(f"{self.LAST_BRANCH}{self._color('Commands:', Colors.DIM)} {cmd_count}")
        else:
            lines.append(f"{self.LAST_BRANCH}{self._color('Commands:', Colors.DIM)} (none)")

        return lines
