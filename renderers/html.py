"""HTML renderer for standalone visualization with embedded CSS."""

from pathlib import Path
from typing import List
import html

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from hooks_manager import ExtensionsData, SkillInfo, CommandInfo, HookInfo
from .base import BaseRenderer


class HTMLRenderer(BaseRenderer):
    """Renders extensions as a standalone HTML document with embedded CSS."""

    def __init__(self, use_color: bool = True):
        super().__init__(use_color)

    def render(self, data: ExtensionsData) -> str:
        """Render extensions data as an HTML document."""
        skills_html = self._render_skills_section(data.skills)
        commands_html = self._render_commands_section(data.commands)
        hooks_html = self._render_hooks_section(data.hooks)

        return self._generate_document(skills_html, commands_html, hooks_html, data)

    def _escape(self, text: str) -> str:
        """Escape HTML special characters."""
        return html.escape(str(text))

    def _render_skills_section(self, skills: List[SkillInfo]) -> str:
        """Render the skills section."""
        if not skills:
            return '<p class="empty">No skills configured</p>'

        items = []
        for skill in skills:
            triggers_html = ""
            if skill.triggers:
                triggers = ", ".join(self._escape(t) for t in skill.triggers)
                triggers_html = f'<div class="item-meta"><span class="label">Triggers:</span> {triggers}</div>'

            desc_html = ""
            if skill.description:
                desc_html = f'<div class="item-desc">{self._escape(skill.description)}</div>'

            items.append(f'''
            <div class="item">
                <div class="item-header">
                    <span class="item-name">{self._escape(skill.name)}</span>
                </div>
                {desc_html}
                {triggers_html}
                <div class="item-meta"><span class="label">Path:</span> <code>{self._escape(str(skill.path))}</code></div>
            </div>
            ''')

        return "\n".join(items)

    def _render_commands_section(self, commands: List[CommandInfo]) -> str:
        """Render the commands section."""
        if not commands:
            return '<p class="empty">No commands configured</p>'

        items = []
        for cmd in commands:
            desc_html = ""
            if cmd.description:
                desc_html = f'<div class="item-desc">{self._escape(cmd.description)}</div>'

            items.append(f'''
            <div class="item">
                <div class="item-header">
                    <span class="item-name command-name">/{self._escape(cmd.name)}</span>
                </div>
                {desc_html}
                <div class="item-meta"><span class="label">Path:</span> <code>{self._escape(str(cmd.path))}</code></div>
            </div>
            ''')

        return "\n".join(items)

    def _render_hooks_section(self, hooks: List[HookInfo]) -> str:
        """Render the hooks section."""
        if not hooks:
            return '<p class="empty">No hooks configured</p>'

        items = []
        for hook in hooks:
            status_class = "status-enabled" if hook.enabled else "status-disabled"
            status_text = "enabled" if hook.enabled else "disabled"

            cmd_count = len(hook.commands) if hook.commands else 0
            cmd_text = f"{cmd_count} command{'s' if cmd_count != 1 else ''}"

            items.append(f'''
            <div class="item hook-item">
                <div class="item-header">
                    <span class="item-name">{self._escape(hook.name)}</span>
                    <span class="status-badge {status_class}">{status_text}</span>
                </div>
                <div class="item-meta"><span class="label">Event:</span> <span class="event-type">{self._escape(hook.event)}</span></div>
                <div class="item-meta"><span class="label">Matcher:</span> <code>{self._escape(hook.matcher)}</code></div>
                <div class="item-meta"><span class="label">Commands:</span> {cmd_text}</div>
            </div>
            ''')

        return "\n".join(items)

    def _generate_document(self, skills_html: str, commands_html: str,
                          hooks_html: str, data: ExtensionsData) -> str:
        """Generate the complete HTML document."""
        skills_count = len(data.skills)
        commands_count = len(data.commands)
        hooks_count = len(data.hooks)

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Claude Code Extensions</title>
    <style>
{self._get_css()}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Claude Code Extensions</h1>
            <p class="subtitle">Skills, Commands, and Hooks Overview</p>
        </header>

        <main>
            <section class="collapsible">
                <button class="section-header" onclick="toggleSection(this)" aria-expanded="true">
                    <span class="section-icon">▼</span>
                    <span class="section-title">Skills</span>
                    <span class="section-count">{skills_count}</span>
                </button>
                <div class="section-content">
                    {skills_html}
                </div>
            </section>

            <section class="collapsible">
                <button class="section-header" onclick="toggleSection(this)" aria-expanded="true">
                    <span class="section-icon">▼</span>
                    <span class="section-title">Commands</span>
                    <span class="section-count">{commands_count}</span>
                </button>
                <div class="section-content">
                    {commands_html}
                </div>
            </section>

            <section class="collapsible">
                <button class="section-header" onclick="toggleSection(this)" aria-expanded="true">
                    <span class="section-icon">▼</span>
                    <span class="section-title">Hooks</span>
                    <span class="section-count">{hooks_count}</span>
                </button>
                <div class="section-content">
                    {hooks_html}
                </div>
            </section>
        </main>

        <footer>
            <p>Generated by Claude Code Hooks Manager</p>
        </footer>
    </div>

    <script>
        function toggleSection(button) {{
            const section = button.parentElement;
            const content = section.querySelector('.section-content');
            const icon = button.querySelector('.section-icon');
            const isExpanded = button.getAttribute('aria-expanded') === 'true';

            button.setAttribute('aria-expanded', !isExpanded);
            content.style.display = isExpanded ? 'none' : 'block';
            icon.textContent = isExpanded ? '▶' : '▼';
        }}
    </script>
</body>
</html>'''

    def _get_css(self) -> str:
        """Return the embedded CSS styles."""
        return '''
        :root {
            --bg-primary: #1a1b26;
            --bg-secondary: #24283b;
            --bg-tertiary: #414868;
            --text-primary: #c0caf5;
            --text-secondary: #a9b1d6;
            --text-muted: #565f89;
            --accent-blue: #7aa2f7;
            --accent-green: #9ece6a;
            --accent-yellow: #e0af68;
            --accent-red: #f7768e;
            --accent-purple: #bb9af7;
            --border-color: #414868;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        }

        @media (prefers-color-scheme: light) {
            :root {
                --bg-primary: #f8f9fa;
                --bg-secondary: #ffffff;
                --bg-tertiary: #e9ecef;
                --text-primary: #212529;
                --text-secondary: #495057;
                --text-muted: #6c757d;
                --accent-blue: #0d6efd;
                --accent-green: #198754;
                --accent-yellow: #ffc107;
                --accent-red: #dc3545;
                --accent-purple: #6f42c1;
                --border-color: #dee2e6;
                --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            }
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem 1rem;
        }

        header {
            text-align: center;
            margin-bottom: 2rem;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--border-color);
        }

        h1 {
            font-size: 2rem;
            font-weight: 600;
            color: var(--accent-blue);
            margin-bottom: 0.5rem;
        }

        .subtitle {
            color: var(--text-muted);
            font-size: 1rem;
        }

        main {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .collapsible {
            background-color: var(--bg-secondary);
            border-radius: 8px;
            border: 1px solid var(--border-color);
            overflow: hidden;
            box-shadow: var(--shadow);
        }

        .section-header {
            width: 100%;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 1rem 1.25rem;
            background-color: var(--bg-secondary);
            border: none;
            cursor: pointer;
            text-align: left;
            color: var(--text-primary);
            font-size: 1rem;
            transition: background-color 0.2s ease;
        }

        .section-header:hover {
            background-color: var(--bg-tertiary);
        }

        .section-icon {
            font-size: 0.75rem;
            color: var(--text-muted);
            transition: transform 0.2s ease;
        }

        .section-title {
            font-weight: 600;
            flex-grow: 1;
        }

        .section-count {
            background-color: var(--bg-tertiary);
            color: var(--text-secondary);
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.875rem;
            font-weight: 500;
        }

        .section-content {
            padding: 0.5rem 1.25rem 1.25rem;
            border-top: 1px solid var(--border-color);
        }

        .item {
            padding: 1rem;
            margin-top: 0.75rem;
            background-color: var(--bg-primary);
            border-radius: 6px;
            border: 1px solid var(--border-color);
        }

        .item:first-child {
            margin-top: 0.5rem;
        }

        .item-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.5rem;
        }

        .item-name {
            font-weight: 600;
            color: var(--accent-green);
            font-size: 1.05rem;
        }

        .command-name {
            color: var(--accent-purple);
            font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
        }

        .item-desc {
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
            font-size: 0.925rem;
        }

        .item-meta {
            color: var(--text-muted);
            font-size: 0.875rem;
            margin-top: 0.25rem;
        }

        .item-meta .label {
            color: var(--text-secondary);
            font-weight: 500;
        }

        .item-meta code {
            background-color: var(--bg-tertiary);
            padding: 0.125rem 0.375rem;
            border-radius: 4px;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
            font-size: 0.8rem;
        }

        .status-badge {
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.025em;
        }

        .status-enabled {
            background-color: rgba(158, 206, 106, 0.2);
            color: var(--accent-green);
        }

        .status-disabled {
            background-color: rgba(224, 175, 104, 0.2);
            color: var(--accent-yellow);
        }

        .event-type {
            color: var(--accent-blue);
            font-weight: 500;
        }

        .empty {
            color: var(--text-muted);
            font-style: italic;
            padding: 1rem;
            text-align: center;
        }

        footer {
            margin-top: 2rem;
            padding-top: 1.5rem;
            border-top: 1px solid var(--border-color);
            text-align: center;
            color: var(--text-muted);
            font-size: 0.875rem;
        }

        @media (max-width: 640px) {
            .container {
                padding: 1rem 0.75rem;
            }

            h1 {
                font-size: 1.5rem;
            }

            .section-header {
                padding: 0.875rem 1rem;
            }

            .section-content {
                padding: 0.5rem 1rem 1rem;
            }

            .item {
                padding: 0.75rem;
            }
        }
'''
