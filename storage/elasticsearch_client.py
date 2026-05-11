"""
Elasticsearch client for file content indexing and searching.
"""
from datetime import datetime
from typing import Optional

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

import config


class ESClient:
    """Elasticsearch client for managing file content index."""

    def __init__(self):
        self._client: Optional[Elasticsearch] = None

    @property
    def client(self) -> Elasticsearch:
        if self._client is None:
            self._client = Elasticsearch(
                hosts=[{"host": config.ES_HOST, "port": config.ES_PORT}],
                headers={"Accept": "application/json", "Content-Type": "application/json"}
            )
        return self._client

    def ping(self) -> bool:
        """Check if Elasticsearch is reachable."""
        try:
            return self.client.ping()
        except Exception:
            return False

    def create_index(self) -> bool:
        """Create the file contents index if it doesn't exist."""
        try:
            if not self.client.indices.exists(index=config.ES_INDEX_NAME):
                self.client.indices.create(
                    index=config.ES_INDEX_NAME,
                    body=config.ES_MAPPING
                )
            return True
        except Exception as e:
            print(f"Error creating index: {e}")
            return False

    def delete_index(self) -> bool:
        """Delete the file contents index."""
        try:
            if self.client.indices.exists(index=config.ES_INDEX_NAME):
                self.client.indices.delete(index=config.ES_INDEX_NAME)
            return True
        except Exception as e:
            print(f"Error deleting index: {e}")
            return False

    def index_document(self, doc: dict) -> bool:
        """Index a single document."""
        try:
            doc["indexed_time"] = datetime.utcnow().isoformat()
            self.client.index(index=config.ES_INDEX_NAME, document=doc)
            return True
        except Exception as e:
            print(f"Error indexing document: {e}")
            return False

    def bulk_index(self, documents: list[dict]) -> tuple[int, list]:
        """Bulk index multiple documents."""
        actions = []
        for doc in documents:
            doc["indexed_time"] = datetime.utcnow().isoformat()
            actions.append({
                "_index": config.ES_INDEX_NAME,
                "_source": doc
            })

        try:
            success, errors = bulk(self.client, actions, raise_on_error=False)
            return success, errors
        except Exception as e:
            return 0, [str(e)]

    def delete_document(self, file_path: str) -> bool:
        """Delete a document by file path."""
        try:
            self.client.delete_by_query(
                index=config.ES_INDEX_NAME,
                query={"term": {"file_path": file_path}}
            )
            return True
        except Exception as e:
            print(f"Error deleting document: {e}")
            return False

    def search(self, query: str, file_types: list[str] = None,
               from_: int = 0, size: int = 50) -> dict:
        """Search for documents matching the query."""
        must = [
            {
                "multi_match": {
                    "query": query,
                    "fields": ["content", "file_name"],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            }
        ]

        if file_types:
            must.append({"terms": {"file_type": file_types}})

        body = {
            "query": {"bool": {"must": must}},
            "highlight": {
                "fields": {
                    "content": {
                        "fragment_size": 200,
                        "number_of_fragments": 3
                    }
                }
            },
            "from": from_,
            "size": size,
            "sort": ["_score"]
        }

        try:
            return self.client.search(index=config.ES_INDEX_NAME, body=body)
        except Exception as e:
            print(f"Search error: {e}")
            return {"hits": {"hits": [], "total": {"value": 0}}}

    def get_document_count(self) -> int:
        """Get total number of indexed documents."""
        try:
            result = self.client.count(index=config.ES_INDEX_NAME)
            return result["count"]
        except Exception:
            return 0

    def document_exists(self, file_path: str) -> bool:
        """Check if a document exists by file path."""
        try:
            result = self.client.search(
                index=config.ES_INDEX_NAME,
                query={"term": {"file_path": file_path}},
                size=1
            )
            return result["hits"]["total"]["value"] > 0
        except Exception:
            return False

    def close(self):
        """Close the Elasticsearch connection."""
        if self._client:
            self._client.close()
            self._client = None


# Singleton instance
es_client = ESClient()
