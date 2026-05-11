"""
Main application window.
"""
import logging
import os
import subprocess
from pathlib import Path
from threading import Thread

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTabWidget, QMessageBox, QStatusBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject

from core.indexer import FileIndexer
from core.searcher import Searcher
from core.file_monitor import FileMonitor
from storage.elasticsearch_client import es_client
from storage.redis_client import redis_client

from gui.styles import MAIN_STYLE
from gui.search_panel import SearchPanel
from gui.result_view import ResultView
from gui.index_manager import IndexManager


class IndexingSignals(QObject):
    """Signals for indexing thread communication."""
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self._init_logging()
        self._init_components()
        self._init_ui()
        self._connect_signals()
        self._check_services()

    def _init_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def _init_components(self):
        self.indexer = FileIndexer()
        self.searcher = Searcher()
        self.monitor = FileMonitor(self.indexer)
        self._indexing_thread = None
        self._indexing_signals = IndexingSignals()
        self._is_indexing = False

    def _init_ui(self):
        self.setWindowTitle("File Search Tool")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        self.setStyleSheet(MAIN_STYLE)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel (Search and Index)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.search_panel = SearchPanel()
        left_layout.addWidget(self.search_panel)

        self.index_manager = IndexManager()
        left_layout.addWidget(self.index_manager)

        splitter.addWidget(left_widget)

        # Right panel (Results)
        self.result_view = ResultView()
        splitter.addWidget(self.result_view)

        splitter.setSizes([350, 650])
        layout.addWidget(splitter)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _connect_signals(self):
        # Search panel signals
        self.search_panel.search_requested.connect(self._on_search)
        self.search_panel.index_requested.connect(self._on_index)
        self.search_panel.stop_indexing_requested.connect(self._on_stop_indexing)

        # Index manager signals
        self.index_manager.clear_index_requested.connect(self._on_clear_index)
        self.index_manager.refresh_stats_requested.connect(self._refresh_stats)

        # Result view signals
        self.result_view.file_open_requested.connect(self._on_open_file)

        # Indexing thread signals
        self._indexing_signals.progress.connect(self._on_indexing_progress)
        self._indexing_signals.finished.connect(self._on_indexing_finished)
        self._indexing_signals.error.connect(self._on_indexing_error)

        # Monitor events
        self.monitor.set_event_callback(self._on_file_event)

    def _check_services(self):
        """Check if Elasticsearch and Redis are running."""
        if not es_client.ping():
            QMessageBox.warning(
                self, "Service Unavailable",
                "Cannot connect to Elasticsearch.\n"
                "Please start Docker containers:\n"
                "  docker-compose up -d"
            )
        elif not redis_client.ping():
            QMessageBox.warning(
                self, "Service Unavailable",
                "Cannot connect to Redis.\n"
                "Please start Docker containers:\n"
                "  docker-compose up -d"
            )
        else:
            self._refresh_stats()

    def _on_search(self, query: str, file_types: list):
        """Handle search request."""
        self.status_bar.showMessage(f"Searching: {query}")
        results = self.searcher.search(query, file_types)
        self.result_view.set_results(results)
        self.status_bar.showMessage(
            f"Found {results.total} result(s)"
            + (" (cached)" if results.cached else "")
        )

    def _on_index(self, path: str, is_full_disk: bool):
        """Start indexing process."""
        if self._is_indexing:
            return

        self._is_indexing = True
        self.search_panel.set_indexing(True)
        self.search_panel.set_status("Starting indexing...")

        def run_index():
            try:
                if is_full_disk:
                    results = self.indexer.index_drives(incremental=True)
                else:
                    results = self.indexer.index_directory(Path(path), incremental=True)
                self._indexing_signals.finished.emit(results)
            except Exception as e:
                self._indexing_signals.error.emit(str(e))

        self.indexer.set_progress_callback(
            lambda c, t, f: self._indexing_signals.progress.emit(c, t, f)
        )

        self._indexing_thread = Thread(target=run_index, daemon=True)
        self._indexing_thread.start()

        # Start monitoring the indexed directory
        if not is_full_disk and path:
            self.monitor.start([Path(path)])

    def _on_stop_indexing(self):
        """Stop the indexing process."""
        self.indexer.stop()
        self.search_panel.set_status("Stopping...")

    def _on_indexing_progress(self, current: int, total: int, file_path: str):
        """Update indexing progress."""
        self.search_panel.set_progress(current, total, file_path)

    def _on_indexing_finished(self, results: dict):
        """Handle indexing completion."""
        self._is_indexing = False
        self.search_panel.set_indexing(False)
        self.search_panel.set_status(
            f"Indexed: {results['indexed']}, "
            f"Skipped: {results['skipped']}, "
            f"Errors: {results['errors']}"
        )
        self._refresh_stats()

    def _on_indexing_error(self, error: str):
        """Handle indexing error."""
        self._is_indexing = False
        self.search_panel.set_indexing(False)
        self.search_panel.set_status(f"Error: {error}")
        QMessageBox.critical(self, "Indexing Error", error)

    def _on_clear_index(self):
        """Clear the entire index."""
        reply = QMessageBox.question(
            self, "Clear Index",
            "Are you sure you want to delete all indexed data?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if es_client.delete_index():
                es_client.create_index()
                self._refresh_stats()
                QMessageBox.information(
                    self, "Index Cleared",
                    "All indexed data has been removed."
                )

    def _refresh_stats(self):
        """Refresh index statistics."""
        self.index_manager.update_statistics()
        self.index_manager.set_monitored_directories(
            self.monitor.watched_paths
        )

    def _on_open_file(self, file_path: str):
        """Open a file with the default application."""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            else:  # macOS and Linux
                subprocess.run(['xdg-open', file_path], check=False)
        except Exception as e:
            QMessageBox.warning(
                self, "Cannot Open File",
                f"Failed to open file:\n{str(e)}"
            )

    def _on_file_event(self, action: str, path: Path):
        """Handle file monitor events."""
        self.status_bar.showMessage(f"[Monitor] {action}: {path.name}")

    def closeEvent(self, event):
        """Handle window close event."""
        self.monitor.stop()
        es_client.close()
        redis_client.close()
        event.accept()
