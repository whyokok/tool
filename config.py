"""
Configuration settings for the file search tool.
"""
import os
from pathlib import Path

# Elasticsearch settings
ES_HOST = os.getenv("ES_HOST", "localhost")
ES_PORT = int(os.getenv("ES_PORT", "9200"))
ES_INDEX_NAME = "file_contents"

# Redis settings
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Cache settings
CACHE_TTL = 3600  # 1 hour

# Supported file extensions
SUPPORTED_EXTENSIONS = {
    ".pdf": "pdf",
    ".docx": "word",
    ".doc": "word",
    ".pptx": "ppt",
    ".ppt": "ppt",
    ".txt": "txt",
    ".md": "txt",
    ".log": "txt",
}

# Index settings
BATCH_SIZE = 100
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Elasticsearch index mapping
ES_MAPPING = {
    "mappings": {
        "properties": {
            "file_path": {"type": "keyword"},
            "file_name": {
                "type": "text",
                "analyzer": "ik_max_word",
                "search_analyzer": "ik_smart",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            "content": {
                "type": "text",
                "analyzer": "ik_max_word",
                "search_analyzer": "ik_smart"
            },
            "file_type": {"type": "keyword"},
            "file_size": {"type": "long"},
            "modified_time": {"type": "date"},
            "indexed_time": {"type": "date"},
        }
    },
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "default": {
                    "type": "standard"
                }
            }
        }
    }
}
