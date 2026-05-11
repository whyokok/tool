"""
Base class for file parsers.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ParseResult:
    """Result of parsing a file."""
    file_path: str
    file_name: str
    content: str
    file_type: str
    file_size: int
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None


class BaseParser(ABC):
    """Abstract base class for file parsers."""

    @property
    @abstractmethod
    def file_type(self) -> str:
        """Return the file type this parser handles."""
        pass

    @abstractmethod
    def parse(self, file_path: Path) -> ParseResult:
        """Parse the file and extract text content."""
        pass

    def _create_result(self, file_path: Path, content: str, error: str = None) -> ParseResult:
        """Helper to create a ParseResult."""
        return ParseResult(
            file_path=str(file_path),
            file_name=file_path.name,
            content=content,
            file_type=self.file_type,
            file_size=file_path.stat().st_size if file_path.exists() else 0,
            error=error
        )
