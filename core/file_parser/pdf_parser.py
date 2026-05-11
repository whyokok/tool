"""
PDF file parser using PyMuPDF.
"""
from pathlib import Path

import fitz  # PyMuPDF

from .base import BaseParser, ParseResult


class PdfParser(BaseParser):
    """Parser for PDF files."""

    @property
    def file_type(self) -> str:
        return "pdf"

    def parse(self, file_path: Path) -> ParseResult:
        try:
            doc = fitz.open(file_path)
            text_parts = []

            for page_num, page in enumerate(doc):
                text = page.get_text()
                if text.strip():
                    text_parts.append(f"[Page {page_num + 1}]\n{text}")

            doc.close()
            content = "\n\n".join(text_parts)
            return self._create_result(file_path, content.strip())

        except Exception as e:
            return self._create_result(file_path, "", str(e))
