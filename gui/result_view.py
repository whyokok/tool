"""
Result view widget for displaying search results.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QLabel, QAbstractItemView,
    QHeaderView, QPushButton, QTextEdit, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from core.searcher import SearchResult, SearchResults
from gui.styles import FILE_TYPE_ICONS, FILE_TYPE_NAMES


class ResultView(QWidget):
    """Widget for displaying and interacting with search results."""

    file_open_requested = pyqtSignal(str)  # file_path

    def __init__(self, parent=None):
        super().__init__(parent)
        self._results: list[SearchResult] = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header with result count
        header_layout = QHBoxLayout()
        self.result_count_label = QLabel("No results")
        header_layout.addWidget(self.result_count_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Splitter for table and preview
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Results table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "File Name", "Type", "Size", "Score", "Path"
        ])
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.doubleClicked.connect(self._on_double_click)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        splitter.addWidget(self.table)

        # Preview pane
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        preview_header = QLabel("Content Preview")
        preview_header.setStyleSheet("font-weight: bold; padding: 4px;")
        preview_layout.addWidget(preview_header)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        preview_layout.addWidget(self.preview_text)

        splitter.addWidget(preview_widget)
        splitter.setSizes([300, 150])

        layout.addWidget(splitter)

    def set_results(self, results: SearchResults):
        """Display search results."""
        self._results = results.results
        self.table.setRowCount(len(self._results))

        for row, result in enumerate(self._results):
            # File name
            name_item = QTableWidgetItem(result.file_name)
            name_item.setData(Qt.ItemDataRole.UserRole, result.file_path)
            self.table.setItem(row, 0, name_item)

            # File type with color
            type_name = FILE_TYPE_NAMES.get(result.file_type, result.file_type)
            type_item = QTableWidgetItem(type_name)
            color = QColor(FILE_TYPE_ICONS.get(result.file_type, "#999999"))
            type_item.setForeground(color)
            self.table.setItem(row, 1, type_item)

            # Size
            size_item = QTableWidgetItem(result.file_size_display)
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 2, size_item)

            # Score
            score_item = QTableWidgetItem(f"{result.score:.2f}")
            score_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 3, score_item)

            # Path
            path_item = QTableWidgetItem(result.file_path)
            self.table.setItem(row, 4, path_item)

        # Update count label
        total = results.total
        count = len(self._results)
        if total > count:
            self.result_count_label.setText(
                f"Showing {count} of {total} results"
            )
        else:
            self.result_count_label.setText(
                f"{total} result{'s' if total != 1 else ''}"
            )
            if results.cached:
                self.result_count_label.setText(
                    self.result_count_label.text() + " (cached)"
                )

        # Clear preview
        self.preview_text.clear()

    def clear_results(self):
        """Clear all results."""
        self._results = []
        self.table.setRowCount(0)
        self.result_count_label.setText("No results")
        self.preview_text.clear()

    def _on_double_click(self, index):
        """Handle double-click to open file."""
        result = self._results[index.row()]
        self.file_open_requested.emit(result.file_path)

    def _on_selection_changed(self):
        """Update preview when selection changes."""
        selected = self.table.selectedItems()
        if not selected:
            self.preview_text.clear()
            return

        row = selected[0].row()
        if 0 <= row < len(self._results):
            result = self._results[row]
            preview = self._format_preview(result)
            self.preview_text.setHtml(preview)

    def _format_preview(self, result: SearchResult) -> str:
        """Format result for preview display."""
        html = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif;">
            <p style="font-size: 14px; font-weight: bold;">{result.file_name}</p>
            <p style="color: #666; font-size: 12px;">{result.file_path}</p>
        """

        if result.highlights:
            html += "<hr><p style='font-weight: bold;'>Matches:</p>"
            for highlight in result.highlights:
                # Convert <em> tags to styled spans
                styled = highlight.replace(
                    "<em>", "<span style='background-color: #ffeb3b; font-weight: bold;'>"
                ).replace("</em>", "</span>")
                html += f"<p style='margin: 4px 0;'>{styled}</p>"

        html += "</div>"
        return html
