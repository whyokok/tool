"""
Index manager panel for monitoring and controlling indexing.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QGroupBox, QListWidget, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal

from storage.elasticsearch_client import es_client


class IndexManager(QWidget):
    """Panel for managing and monitoring the index."""

    clear_index_requested = pyqtSignal()
    refresh_stats_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Statistics group
        stats_group = QGroupBox("Index Statistics")
        stats_layout = QVBoxLayout(stats_group)

        self.doc_count_label = QLabel("Documents: 0")
        self.index_size_label = QLabel("Index Size: --")
        stats_layout.addWidget(self.doc_count_label)
        stats_layout.addWidget(self.index_size_label)

        refresh_btn = QPushButton("Refresh Statistics")
        refresh_btn.clicked.connect(self._on_refresh)
        stats_layout.addWidget(refresh_btn)

        layout.addWidget(stats_group)

        # Monitored directories group
        monitor_group = QGroupBox("Monitored Directories")
        monitor_layout = QVBoxLayout(monitor_group)

        self.monitored_list = QListWidget()
        monitor_layout.addWidget(self.monitored_list)

        layout.addWidget(monitor_group)

        # Actions group
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)

        clear_btn = QPushButton("Clear All Index Data")
        clear_btn.clicked.connect(self._on_clear_index)
        actions_layout.addWidget(clear_btn)

        clear_cache_btn = QPushButton("Clear Search Cache")
        clear_cache_btn.clicked.connect(self._on_clear_cache)
        actions_layout.addWidget(clear_cache_btn)

        layout.addWidget(actions_group)
        layout.addStretch()

    def update_statistics(self, doc_count: int = None):
        """Update displayed statistics."""
        if doc_count is None:
            doc_count = es_client.get_document_count()
        self.doc_count_label.setText(f"Documents: {doc_count:,}")

    def set_monitored_directories(self, paths: list):
        """Update the list of monitored directories."""
        self.monitored_list.clear()
        for path in paths:
            self.monitored_list.addItem(str(path))

    def _on_refresh(self):
        self.refresh_stats_requested.emit()

    def _on_clear_index(self):
        self.clear_index_requested.emit()

    def _on_clear_cache(self):
        from storage.redis_client import redis_client
        cleared = redis_client.clear_search_cache()
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self, "Cache Cleared",
            f"Cleared {cleared} cached search results."
        )
