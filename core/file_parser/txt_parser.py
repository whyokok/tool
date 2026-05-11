"""
Text file parser.
"""
import chardet
from pathlib import Path

from .base import BaseParser, ParseResult


class TxtParser(BaseParser):
    """Parser for plain text files (.txt, .md, .log)."""

    @property
    def file_type(self) -> str:
        return "txt"

    def parse(self, file_path: Path) -> ParseResult:
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read()

            # Detect encoding
            detected = chardet.detect(raw_data)
            encoding = detected.get('encoding', 'utf-8') or 'utf-8'

            # Try to decode with detected encoding
            try:
                content = raw_data.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                # Fallback to utf-8 with error handling
                content = raw_data.decode('utf-8', errors='replace')

            return self._create_result(file_path, content.strip())

        except Exception as e:
            return self._create_result(file_path, "", str(e))
