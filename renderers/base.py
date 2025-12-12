"""Base renderer interface for visualization."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from hooks_manager import ExtensionsData


class BaseRenderer(ABC):
    """Abstract base class for extension renderers."""

    def __init__(self, use_color: bool = True):
        self.use_color = use_color

    @abstractmethod
    def render(self, data: ExtensionsData) -> str:
        """Render extensions data to a string.

        Args:
            data: ExtensionsData containing skills, commands, and hooks.

        Returns:
            Rendered string representation.
        """
        pass

    def render_to_file(self, data: ExtensionsData, output_path: Path) -> None:
        """Render extensions data to a file.

        Args:
            data: ExtensionsData containing skills, commands, and hooks.
            output_path: Path to write the output.
        """
        content = self.render(data)
        output_path.write_text(content, encoding='utf-8')
