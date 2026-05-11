from .base import BaseParser
from .txt_parser import TxtParser
from .pdf_parser import PdfParser
from .word_parser import WordParser
from .ppt_parser import PptParser


def get_parser(file_extension: str) -> BaseParser | None:
    """Get the appropriate parser for a file extension."""
    extension_map = {
        "txt": TxtParser,
        "pdf": PdfParser,
        "word": WordParser,
        "ppt": PptParser,
    }
    parser_class = extension_map.get(file_extension)
    return parser_class() if parser_class else None
