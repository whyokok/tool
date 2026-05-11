"""
File monitoring using watchdog for real-time index updates.
"""
import logging
from pathlib import Path
from threading import Thread
from typing import Callable, Optional

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

import config
from core.indexer import FileIndexer


class FileMonitorHandler(FileSystemEventHandler):
    """Handler for file system events."""

    def __init__(self, indexer: FileIndexer, callback: Optional[Callable] = None):
        self.indexer = indexer
        self.callback = callback
        super().__init__()

    def on_created(self, event: FileSystemEvent):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() in config.SUPPORTED_EXTENSIONS:
            self._log_action("Created", path)
            self.indexer.index_single_file(path)

    def on_modified(self, event: FileSystemEvent):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() in config.SUPPORTED_EXTENSIONS:
            self._log_action("Modified", path)
            self.indexer.index_single_file(path)

    def on_deleted(self, event: FileSystemEvent):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() in config.SUPPORTED_EXTENSIONS:
            self._log_action("Deleted", path)
            self.indexer.remove_file(path)

    def on_moved(self, event: FileSystemEvent):
        if event.is_directory:
            return
        old_path = Path(event.src_path)
        new_path = Path(event.dest_path)

        if old_path.suffix.lower() in config.SUPPORTED_EXTENSIONS:
            self._log_action("Moved (removed)", old_path)
            self.indexer.remove_file(old_path)

        if new_path.suffix.lower() in config.SUPPORTED_EXTENSIONS:
            self._log_action("Moved (added)", new_path)
            self.indexer.index_single_file(new_path)

    def _log_action(self, action: str, path: Path):
        msg = f"[Monitor] {action}: {path}"
        logging.info(msg)
        if self.callback:
            self.callback(action, path)


class FileMonitor:
    """Monitor directories for file changes and update the index."""

    def __init__(self, indexer: FileIndexer):
        self.indexer = indexer
        self._observer: Optional[Observer] = None
        self._handler: Optional[FileMonitorHandler] = None
        self._watched_paths: list[Path] = []
        self._event_callback: Optional[Callable] = None

    def set_event_callback(self, callback: Callable):
        """Set callback for file events: callback(action, path)."""
        self._event_callback = callback

    def start(self, paths: list[Path]):
        """Start monitoring the given directories."""
        self.stop()
        self._watched_paths = paths

        if not paths:
            return

        self._handler = FileMonitorHandler(self.indexer, self._event_callback)
        self._observer = Observer()

        for path in paths:
            if path.exists() and path.is_dir():
                self._observer.schedule(self._handler, str(path), recursive=True)
                logging.info(f"[Monitor] Watching: {path}")

        self._observer.start()

    def stop(self):
        """Stop monitoring."""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            logging.info("[Monitor] Stopped")

    def add_path(self, path: Path):
        """Add a path to monitor."""
        if not self._observer or not path.exists() or not path.is_dir():
            return

        if path not in self._watched_paths:
            self._watched_paths.append(path)
            self._observer.schedule(self._handler, str(path), recursive=True)
            logging.info(f"[Monitor] Added watch: {path}")

    def remove_path(self, path: Path):
        """Remove a path from monitoring (requires restart)."""
        if path in self._watched_paths:
            self._watched_paths.remove(path)
            # Note: watchdog doesn't support unscheduling individual watches
            # We need to restart the observer
            self.start(self._watched_paths)

    @property
    def is_running(self) -> bool:
        return self._observer is not None and self._observer.is_alive()

    @property
    def watched_paths(self) -> list[Path]:
        return self._watched_paths.copy()
