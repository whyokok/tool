"""
Searcher for querying the file index.
"""
import hashlib
from dataclasses import dataclass
from typing import Optional

from storage.elasticsearch_client import es_client
from storage.redis_client import redis_client


@dataclass
class SearchResult:
    """A single search result."""
    file_path: str
    file_name: str
    file_type: str
    file_size: int
    score: float
    highlights: list[str]
    modified_time: Optional[str] = None

    @property
    def file_size_display(self) -> str:
        """Human readable file size."""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


@dataclass
class SearchResults:
    """Container for search results."""
    results: list[SearchResult]
    total: int
    query: str
    from_: int
    size: int
    cached: bool = False


class Searcher:
    """Searcher for querying indexed files."""

    def __init__(self):
        self._use_cache = True

    def enable_cache(self, enable: bool = True):
        """Enable or disable result caching."""
        self._use_cache = enable

    def search(self, query: str, file_types: list[str] = None,
               page: int = 1, page_size: int = 50) -> SearchResults:
        """
        Search for files matching the query.

        Args:
            query: Search query string
            file_types: Optional list of file types to filter (pdf, word, ppt, txt)
            page: Page number (1-indexed)
            page_size: Results per page

        Returns:
            SearchResults object
        """
        # Check cache
        cache_key = self._make_cache_key(query, file_types, page, page_size)
        if self._use_cache:
            cached = redis_client.get_json(cache_key)
            if cached:
                return self._deserialize_results(cached, cached=True)

        # Search Elasticsearch
        from_ = (page - 1) * page_size
        response = es_client.search(query, file_types, from_, page_size)

        # Parse results
        results = self._parse_response(response, query)
        results.from_ = from_
        results.size = page_size

        # Cache results
        if self._use_cache:
            redis_client.set_json(cache_key, self._serialize_results(results))

        return results

    def quick_search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Quick search returning just top results."""
        results = self.search(query, page_size=limit)
        return results.results

    def clear_cache(self):
        """Clear all cached search results."""
        redis_client.clear_search_cache()

    def _parse_response(self, response: dict, query: str) -> SearchResults:
        """Parse Elasticsearch response into SearchResults."""
        hits = response.get("hits", {})
        total = hits.get("total", {}).get("value", 0)
        results = []

        for hit in hits.get("hits", []):
            source = hit.get("_source", {})
            highlight = hit.get("highlight", {}).get("content", [])

            result = SearchResult(
                file_path=source.get("file_path", ""),
                file_name=source.get("file_name", ""),
                file_type=source.get("file_type", ""),
                file_size=source.get("file_size", 0),
                score=hit.get("_score", 0),
                highlights=highlight,
                modified_time=source.get("modified_time")
            )
            results.append(result)

        return SearchResults(
            results=results,
            total=total,
            query=query,
            from_=0,
            size=len(results)
        )

    def _make_cache_key(self, query: str, file_types: list[str],
                        page: int, page_size: int) -> str:
        """Generate cache key for search parameters."""
        types_str = ",".join(sorted(file_types)) if file_types else "all"
        key_data = f"{query}:{types_str}:{page}:{page_size}"
        hash_key = hashlib.md5(key_data.encode()).hexdigest()
        return f"search:{hash_key}"

    def _serialize_results(self, results: SearchResults) -> dict:
        """Serialize SearchResults to dict."""
        return {
            "results": [
                {
                    "file_path": r.file_path,
                    "file_name": r.file_name,
                    "file_type": r.file_type,
                    "file_size": r.file_size,
                    "score": r.score,
                    "highlights": r.highlights,
                    "modified_time": r.modified_time
                }
                for r in results.results
            ],
            "total": results.total,
            "query": results.query,
            "from_": results.from_,
            "size": results.size
        }

    def _deserialize_results(self, data: dict, cached: bool = False) -> SearchResults:
        """Deserialize dict to SearchResults."""
        return SearchResults(
            results=[
                SearchResult(**r) for r in data.get("results", [])
            ],
            total=data.get("total", 0),
            query=data.get("query", ""),
            from_=data.get("from_", 0),
            size=data.get("size", 0),
            cached=cached
        )
