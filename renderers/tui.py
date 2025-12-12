"""TUI renderer using curses for interactive visualization."""

import curses
from pathlib import Path
from typing import List, Optional, Tuple, Union

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from hooks_manager import Colors, ExtensionsData, SkillInfo, CommandInfo, HookInfo
from .base import BaseRenderer


class TUIRenderer(BaseRenderer):
    """Interactive TUI renderer using curses for terminal visualization."""

    # Key bindings
    KEY_QUIT = ord('q')
    KEY_HELP = ord('?')
    KEY_DETAIL = ord('\n')  # Enter
    KEY_BACK = ord('b')
    KEY_TAB = ord('\t')

    def __init__(self, use_color: bool = True):
        super().__init__(use_color)
        self.data: Optional[ExtensionsData] = None
        self.stdscr: Optional[curses.window] = None

        # Navigation state
        self.current_section = 0  # 0=Skills, 1=Commands, 2=Hooks
        self.current_item = 0
        self.scroll_offset = 0
        self.show_detail = False
        self.show_help = False

        # Color pairs
        self.COLOR_HEADER = 1
        self.COLOR_SELECTED = 2
        self.COLOR_ENABLED = 3
        self.COLOR_DISABLED = 4
        self.COLOR_DIM = 5
        self.COLOR_SECTION = 6
        self.COLOR_DETAIL = 7

    def render(self, data: ExtensionsData) -> str:
        """Render extensions data interactively using curses.

        Returns empty string since output is interactive.
        """
        self.data = data
        try:
            curses.wrapper(self._run)
        except curses.error:
            return "Error: Terminal too small or curses not supported"
        return ""

    def _run(self, stdscr: curses.window) -> None:
        """Main curses loop."""
        self.stdscr = stdscr
        self._init_curses()

        while True:
            self._draw()
            key = stdscr.getch()

            if key == self.KEY_QUIT:
                break
            elif self.show_help:
                # Any key closes help
                self.show_help = False
            elif self.show_detail:
                if key == self.KEY_BACK or key == curses.KEY_LEFT or key == 27:  # ESC
                    self.show_detail = False
            else:
                self._handle_input(key)

    def _init_curses(self) -> None:
        """Initialize curses settings and colors."""
        curses.curs_set(0)  # Hide cursor
        self.stdscr.timeout(100)  # Non-blocking input

        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()

            # Define color pairs
            curses.init_pair(self.COLOR_HEADER, curses.COLOR_WHITE, curses.COLOR_BLUE)
            curses.init_pair(self.COLOR_SELECTED, curses.COLOR_BLACK, curses.COLOR_CYAN)
            curses.init_pair(self.COLOR_ENABLED, curses.COLOR_GREEN, -1)
            curses.init_pair(self.COLOR_DISABLED, curses.COLOR_YELLOW, -1)
            curses.init_pair(self.COLOR_DIM, curses.COLOR_WHITE, -1)
            curses.init_pair(self.COLOR_SECTION, curses.COLOR_CYAN, -1)
            curses.init_pair(self.COLOR_DETAIL, curses.COLOR_WHITE, -1)

    def _handle_input(self, key: int) -> None:
        """Handle keyboard input for navigation."""
        sections = self._get_sections()
        current_items = sections[self.current_section][1] if sections else []

        if key == curses.KEY_UP or key == ord('k'):
            if self.current_item > 0:
                self.current_item -= 1
                self._adjust_scroll()
        elif key == curses.KEY_DOWN or key == ord('j'):
            if self.current_item < len(current_items) - 1:
                self.current_item += 1
                self._adjust_scroll()
        elif key == curses.KEY_LEFT or key == ord('h'):
            if self.current_section > 0:
                self.current_section -= 1
                self.current_item = 0
                self.scroll_offset = 0
        elif key == curses.KEY_RIGHT or key == ord('l'):
            if self.current_section < len(sections) - 1:
                self.current_section += 1
                self.current_item = 0
                self.scroll_offset = 0
        elif key == self.KEY_TAB:
            # Cycle through sections
            self.current_section = (self.current_section + 1) % len(sections)
            self.current_item = 0
            self.scroll_offset = 0
        elif key == self.KEY_DETAIL:
            if current_items:
                self.show_detail = True
        elif key == self.KEY_HELP:
            self.show_help = True
        elif key == ord('1'):
            self.current_section = 0
            self.current_item = 0
            self.scroll_offset = 0
        elif key == ord('2'):
            self.current_section = 1
            self.current_item = 0
            self.scroll_offset = 0
        elif key == ord('3'):
            self.current_section = 2
            self.current_item = 0
            self.scroll_offset = 0

    def _adjust_scroll(self) -> None:
        """Adjust scroll offset to keep current item visible."""
        max_height, _ = self.stdscr.getmaxyx()
        visible_area = max_height - 6  # Account for header/footer

        if self.current_item < self.scroll_offset:
            self.scroll_offset = self.current_item
        elif self.current_item >= self.scroll_offset + visible_area:
            self.scroll_offset = self.current_item - visible_area + 1

    def _get_sections(self) -> List[Tuple[str, List[Union[SkillInfo, CommandInfo, HookInfo]]]]:
        """Get section data as list of (title, items) tuples."""
        if not self.data:
            return []
        return [
            ("Skills", self.data.skills),
            ("Commands", self.data.commands),
            ("Hooks", self.data.hooks),
        ]

    def _draw(self) -> None:
        """Draw the main TUI interface."""
        self.stdscr.clear()
        max_height, max_width = self.stdscr.getmaxyx()

        if max_height < 10 or max_width < 40:
            self.stdscr.addstr(0, 0, "Terminal too small")
            self.stdscr.refresh()
            return

        if self.show_help:
            self._draw_help()
        elif self.show_detail:
            self._draw_detail()
        else:
            self._draw_main()

        self.stdscr.refresh()

    def _draw_main(self) -> None:
        """Draw the main list view."""
        max_height, max_width = self.stdscr.getmaxyx()
        sections = self._get_sections()

        # Header
        header = " Claude Code Extensions "
        self._draw_header(header, max_width)

        # Section tabs
        self._draw_section_tabs(sections, max_width)

        # Current section content
        if sections:
            title, items = sections[self.current_section]
            self._draw_items(items, 3, max_height - 3, max_width)

        # Footer with help
        self._draw_footer(max_height, max_width)

    def _draw_header(self, text: str, width: int) -> None:
        """Draw the header bar."""
        header = text.center(width - 1)
        try:
            self.stdscr.attron(curses.color_pair(self.COLOR_HEADER) | curses.A_BOLD)
            self.stdscr.addstr(0, 0, header[:width-1])
            self.stdscr.attroff(curses.color_pair(self.COLOR_HEADER) | curses.A_BOLD)
        except curses.error:
            pass

    def _draw_section_tabs(self, sections: List, width: int) -> None:
        """Draw section navigation tabs."""
        y = 1
        x = 0

        for i, (title, items) in enumerate(sections):
            tab_text = f" [{i+1}] {title} ({len(items)}) "

            try:
                if i == self.current_section:
                    self.stdscr.attron(curses.color_pair(self.COLOR_SELECTED) | curses.A_BOLD)
                    self.stdscr.addstr(y, x, tab_text)
                    self.stdscr.attroff(curses.color_pair(self.COLOR_SELECTED) | curses.A_BOLD)
                else:
                    self.stdscr.attron(curses.color_pair(self.COLOR_SECTION))
                    self.stdscr.addstr(y, x, tab_text)
                    self.stdscr.attroff(curses.color_pair(self.COLOR_SECTION))
            except curses.error:
                pass

            x += len(tab_text)

        # Separator line
        try:
            self.stdscr.addstr(2, 0, "-" * (width - 1))
        except curses.error:
            pass

    def _draw_items(self, items: List, start_y: int, end_y: int, width: int) -> None:
        """Draw list of items in current section."""
        if not items:
            try:
                self.stdscr.attron(curses.color_pair(self.COLOR_DIM))
                self.stdscr.addstr(start_y, 2, "(no items)")
                self.stdscr.attroff(curses.color_pair(self.COLOR_DIM))
            except curses.error:
                pass
            return

        visible_height = end_y - start_y - 2

        for idx, item in enumerate(items):
            if idx < self.scroll_offset:
                continue

            display_idx = idx - self.scroll_offset
            if display_idx >= visible_height:
                break

            y = start_y + display_idx
            self._draw_item(item, y, width, idx == self.current_item)

    def _draw_item(self, item: Union[SkillInfo, CommandInfo, HookInfo],
                   y: int, width: int, selected: bool) -> None:
        """Draw a single item line."""
        try:
            if isinstance(item, SkillInfo):
                text = f"  {item.name}"
                if item.description:
                    text += f" - {item.description[:width-len(text)-5]}"
            elif isinstance(item, CommandInfo):
                text = f"  /{item.name}"
                if item.description:
                    text += f" - {item.description[:width-len(text)-5]}"
            elif isinstance(item, HookInfo):
                status = "[ON] " if item.enabled else "[OFF]"
                text = f"  {status} {item.name} ({item.event})"
            else:
                text = f"  {item}"

            # Truncate to width
            text = text[:width-2].ljust(width-2)

            if selected:
                self.stdscr.attron(curses.color_pair(self.COLOR_SELECTED))
                self.stdscr.addstr(y, 0, text)
                self.stdscr.attroff(curses.color_pair(self.COLOR_SELECTED))
            else:
                if isinstance(item, HookInfo):
                    color = self.COLOR_ENABLED if item.enabled else self.COLOR_DISABLED
                    self.stdscr.attron(curses.color_pair(color))
                    self.stdscr.addstr(y, 0, text)
                    self.stdscr.attroff(curses.color_pair(color))
                else:
                    self.stdscr.addstr(y, 0, text)
        except curses.error:
            pass

    def _draw_footer(self, height: int, width: int) -> None:
        """Draw the footer with key hints."""
        footer = " q:Quit  ?:Help  Enter:Details  Tab:Next Section  Arrows:Navigate "
        try:
            self.stdscr.attron(curses.color_pair(self.COLOR_HEADER))
            self.stdscr.addstr(height - 1, 0, footer.center(width - 1)[:width-1])
            self.stdscr.attroff(curses.color_pair(self.COLOR_HEADER))
        except curses.error:
            pass

    def _draw_detail(self) -> None:
        """Draw detail view for selected item."""
        max_height, max_width = self.stdscr.getmaxyx()
        sections = self._get_sections()

        if not sections:
            return

        _, items = sections[self.current_section]
        if not items or self.current_item >= len(items):
            return

        item = items[self.current_item]

        # Header
        self._draw_header(" Item Details ", max_width)

        # Content
        y = 2

        if isinstance(item, SkillInfo):
            lines = self._format_skill_detail(item, max_width)
        elif isinstance(item, CommandInfo):
            lines = self._format_command_detail(item, max_width)
        elif isinstance(item, HookInfo):
            lines = self._format_hook_detail(item, max_width)
        else:
            lines = [str(item)]

        for line in lines:
            if y >= max_height - 1:
                break
            try:
                self.stdscr.addstr(y, 2, line[:max_width-4])
            except curses.error:
                pass
            y += 1

        # Footer
        footer = " b/Left/ESC:Back  q:Quit "
        try:
            self.stdscr.attron(curses.color_pair(self.COLOR_HEADER))
            self.stdscr.addstr(max_height - 1, 0, footer.center(max_width - 1)[:max_width-1])
            self.stdscr.attroff(curses.color_pair(self.COLOR_HEADER))
        except curses.error:
            pass

    def _format_skill_detail(self, skill: SkillInfo, width: int) -> List[str]:
        """Format skill details for display."""
        lines = [
            f"Name: {skill.name}",
            "",
            f"Description:",
            f"  {skill.description or '(none)'}",
            "",
            f"Triggers:",
        ]

        if skill.triggers:
            for trigger in skill.triggers:
                lines.append(f"  - {trigger}")
        else:
            lines.append("  (none)")

        lines.extend([
            "",
            f"Path:",
            f"  {skill.path}",
        ])

        return lines

    def _format_command_detail(self, cmd: CommandInfo, width: int) -> List[str]:
        """Format command details for display."""
        lines = [
            f"Command: /{cmd.name}",
            "",
            f"Description:",
            f"  {cmd.description or '(none)'}",
            "",
            f"Path:",
            f"  {cmd.path}",
        ]

        return lines

    def _format_hook_detail(self, hook: HookInfo, width: int) -> List[str]:
        """Format hook details for display."""
        status = "ENABLED" if hook.enabled else "DISABLED"

        lines = [
            f"Name: {hook.name}",
            f"Status: {status}",
            "",
            f"Event: {hook.event}",
            f"Matcher: {hook.matcher}",
            "",
            f"Commands ({len(hook.commands)}):",
        ]

        if hook.commands:
            for i, cmd in enumerate(hook.commands):
                cmd_type = cmd.get("type", "command")
                if cmd_type == "command":
                    command = cmd.get("command", "(none)")
                    timeout = cmd.get("timeout", 60)
                    lines.append(f"  {i+1}. {command}")
                    lines.append(f"     Timeout: {timeout}s")
                elif cmd_type == "prompt":
                    prompt = cmd.get("prompt", "(none)")
                    # Truncate long prompts
                    if len(prompt) > width - 10:
                        prompt = prompt[:width-13] + "..."
                    lines.append(f"  {i+1}. [prompt] {prompt}")
        else:
            lines.append("  (none)")

        return lines

    def _draw_help(self) -> None:
        """Draw help overlay."""
        max_height, max_width = self.stdscr.getmaxyx()

        help_lines = [
            "KEYBOARD SHORTCUTS",
            "",
            "Navigation:",
            "  Up/k       Move up",
            "  Down/j     Move down",
            "  Left/h     Previous section",
            "  Right/l    Next section",
            "  Tab        Cycle sections",
            "  1/2/3      Jump to section",
            "",
            "Actions:",
            "  Enter      Show details",
            "  b/ESC      Back from details",
            "  ?          Show this help",
            "  q          Quit",
            "",
            "Press any key to close help...",
        ]

        # Calculate box dimensions
        box_width = max(len(line) for line in help_lines) + 6
        box_height = len(help_lines) + 4
        start_x = (max_width - box_width) // 2
        start_y = (max_height - box_height) // 2

        # Draw box
        try:
            for y in range(box_height):
                for x in range(box_width):
                    char = " "
                    self.stdscr.addch(start_y + y, start_x + x, ord(char),
                                      curses.color_pair(self.COLOR_HEADER))

            # Draw content
            for i, line in enumerate(help_lines):
                self.stdscr.addstr(start_y + 2 + i, start_x + 3, line,
                                   curses.color_pair(self.COLOR_HEADER))
        except curses.error:
            pass
