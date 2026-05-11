"""
File indexer for crawling and indexing documents.
"""
import os
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

import config
from core.file_parser import get_parser
from storage.elasticsearch_client import es_client


class FileIndexer:
    """Indexer for crawling files and adding them to Elasticsearch."""

    def __init__(self):
        self._stop_flag = False
        self._progress_callback: Optional[Callable] = None

    def set_progress_callback(self, callback: Callable):
        """Set callback for progress updates: callback(current, total, file_path)."""
        self._progress_callback = callback

    def stop(self):
        """Stop the indexing process."""
        self._stop_flag = True

    def index_directory(self, directory: Path, incremental: bool = True) -> dict:
        """
        Index all supported files in a directory.

        Returns:
            dict with 'indexed', 'skipped', 'errors', 'total' counts
        """
        self._stop_flag = False
        results = {"indexed": 0, "skipped": 0, "errors": 0, "total": 0}

        # Collect all files first
        files_to_index = list(self._collect_files(directory))
        results["total"] = len(files_to_index)

        # Ensure index exists
        es_client.create_index()

        # Process files in batches
        batch = []
        for i, file_path in enumerate(files_to_index):
            if self._stop_flag:
                break

            if self._progress_callback:
                self._progress_callback(i + 1, results["total"], str(file_path))

            # Check if already indexed (incremental mode)
            if incremental and es_client.document_exists(str(file_path)):
                results["skipped"] += 1
                continue

            # Parse and index
            doc = self._process_file(file_path)
            if doc:
                batch.append(doc)
                if len(batch) >= config.BATCH_SIZE:
                    success, errors = es_client.bulk_index(batch)
                    results["indexed"] += success
                    results["errors"] += len(errors)
                    batch = []
            else:
                results["errors"] += 1

        # Index remaining documents
        if batch:
            success, errors = es_client.bulk_index(batch)
            results["indexed"] += success
            results["errors"] += len(errors)

        return results

    def index_drives(self, incremental: bool = True) -> dict:
        """
        Index all drives on Windows system.

        Returns combined results from all drives.
        """
        results = {"indexed": 0, "skipped": 0, "errors": 0, "total": 0}

        # Get all drives on Windows
        drives = [f"{chr(d)}:\\" for d in range(65, 91) if os.path.exists(f"{chr(d)}:\\")]

        for drive in drives:
            if self._stop_flag:
                break
            drive_results = self.index_directory(Path(drive), incremental)
            for key in results:
                results[key] += drive_results.get(key, 0)

        return results

    def index_single_file(self, file_path: Path) -> bool:
        """Index a single file."""
        doc = self._process_file(file_path)
        if doc:
            return es_client.index_document(doc)
        return False

    def remove_file(self, file_path: Path) -> bool:
        """Remove a file from the index."""
        return es_client.delete_document(str(file_path))

    def _collect_files(self, directory: Path):
        """Recursively collect all supported files."""
        try:
            for entry in directory.rglob("*"):
                if self._stop_flag:
                    break
                if entry.is_file() and entry.suffix.lower() in config.SUPPORTED_EXTENSIONS:
                    if entry.stat().st_size <= config.MAX_FILE_SIZE:
                        yield entry
        except PermissionError:
            pass
        except Exception as e:
            print(f"Error scanning directory {directory}: {e}")

    def _process_file(self, file_path: Path) -> Optional[dict]:
        """Parse a file and return a document for indexing."""
        try:
            extension = file_path.suffix.lower()
            file_type = config.SUPPORTED_EXTENSIONS.get(extension)
            if not file_type:
                return None

            parser = get_parser(file_type)
            if not parser:
                return None

            result = parser.parse(file_path)
            if not result.success:
                print(f"Parse error for {file_path}: {result.error}")
                return None

            stat = file_path.stat()
            return {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "content": result.content,
                "file_type": file_type,
                "file_size": stat.st_size,
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }

        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            return None
