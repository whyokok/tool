"""
Search panel widget.
"""
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QComboBox, QCheckBox,
    QFileDialog, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal


class SearchPanel(QWidget):
    """Panel for search input and options."""

    search_requested = pyqtSignal(str, list)  # query, file_types
    index_requested = pyqtSignal(str, bool)  # path, is_full_disk
    stop_indexing_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Search input section
        search_group = QGroupBox("Search")
        search_layout = QVBoxLayout(search_group)

        # Search input row
        input_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search keywords...")
        self.search_input.returnPressed.connect(self._on_search)

        self.search_btn = QPushButton("Search")
        self.search_btn.setFixedWidth(100)
        self.search_btn.clicked.connect(self._on_search)

        input_row.addWidget(self.search_input)
        input_row.addWidget(self.search_btn)
        search_layout.addLayout(input_row)

        # File type filters
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("File types:"))

        self.pdf_cb = QCheckBox("PDF")
        self.pdf_cb.setChecked(True)
        self.word_cb = QCheckBox("Word")
        self.word_cb.setChecked(True)
        self.ppt_cb = QCheckBox("PowerPoint")
        self.ppt_cb.setChecked(True)
        self.txt_cb = QCheckBox("Text")
        self.txt_cb.setChecked(True)

        filter_row.addWidget(self.pdf_cb)
        filter_row.addWidget(self.word_cb)
        filter_row.addWidget(self.ppt_cb)
        filter_row.addWidget(self.txt_cb)
        filter_row.addStretch()
        search_layout.addLayout(filter_row)

        layout.addWidget(search_group)

        # Index section
        index_group = QGroupBox("Index Management")
        index_layout = QVBoxLayout(index_group)

        # Directory selection
        dir_row = QHBoxLayout()
        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText("Select directory to index...")
        self.dir_input.setReadOnly(True)

        self.browse_btn = QPushButton("Browse")
        self.browse_btn.setFixedWidth(80)
        self.browse_btn.clicked.connect(self._on_browse)

        dir_row.addWidget(self.dir_input)
        dir_row.addWidget(self.browse_btn)
        index_layout.addLayout(dir_row)

        # Index buttons
        btn_row = QHBoxLayout()
        self.index_btn = QPushButton("Index Selected Directory")
        self.index_btn.clicked.connect(self._on_index)

        self.full_disk_btn = QPushButton("Index All Drives")
        self.full_disk_btn.clicked.connect(self._on_full_disk_index)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._on_stop)

        btn_row.addWidget(self.index_btn)
        btn_row.addWidget(self.full_disk_btn)
        btn_row.addWidget(self.stop_btn)
        index_layout.addLayout(btn_row)

        # Progress
        progress_row = QHBoxLayout()
        self.progress_label = QLabel("Ready")
        progress_row.addWidget(self.progress_label)
        progress_row.addStretch()
        index_layout.addLayout(progress_row)

        layout.addWidget(index_group)
        layout.addStretch()

    def _on_search(self):
        query = self.search_input.text().strip()
        if not query:
            return

        file_types = []
        if self.pdf_cb.isChecked():
            file_types.append("pdf")
        if self.word_cb.isChecked():
            file_types.append("word")
        if self.ppt_cb.isChecked():
            file_types.append("ppt")
        if self.txt_cb.isChecked():
            file_types.append("txt")

        self.search_requested.emit(query, file_types)

    def _on_browse(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Directory to Index"
        )
        if dir_path:
            self.dir_input.setText(dir_path)

    def _on_index(self):
        path = self.dir_input.text().strip()
        if not path:
            self.progress_label.setText("Please select a directory first")
            return
        self.index_requested.emit(path, False)

    def _on_full_disk_index(self):
        self.index_requested.emit("", True)

    def _on_stop(self):
        self.stop_indexing_requested.emit()

    def set_indexing(self, indexing: bool):
        """Enable/disable indexing state."""
        self.index_btn.setEnabled(not indexing)
        self.full_disk_btn.setEnabled(not indexing)
        self.stop_btn.setEnabled(indexing)

    def set_progress(self, current: int, total: int, file_path: str):
        """Update progress display."""
        from pathlib import Path
        file_name = Path(file_path).name
        self.progress_label.setText(
            f"Indexing {current}/{total}: {file_name}"
        )

    def set_status(self, message: str):
        """Set status message."""
        self.progress_label.setText(message)

    def get_selected_directory(self) -> Optional[Path]:
        """Get the currently selected directory path."""
        path = self.dir_input.text().strip()
        return Path(path) if path else None
