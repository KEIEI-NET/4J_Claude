"""
Elasticsearch Parsers

Elasticsearchクライアントコードのパーサーモジュール

パーサー一覧:
- ElasticsearchJavaParser: Java Elasticsearchクライアントコードの解析

対応クライアント:
- RestHighLevelClient (Elasticsearch 7.x)
- RestClient (Low-level)
- TransportClient (非推奨、Elasticsearch 8.xで削除)
- ElasticsearchClient (Elasticsearch 8.x+)

使用例:
```python
from multidb_analyzer.elasticsearch.parsers import ElasticsearchJavaParser
from pathlib import Path

parser = ElasticsearchJavaParser()

# 単一ファイルの解析
queries = parser.parse_file(Path("src/main/java/SearchService.java"))

for query in queries:
    print(f"{query.query_type}: {query.query_text}")
    print(f"  File: {query.file_path}:{query.line_number}")
    print(f"  Method: {query.class_name}.{query.method_name}")

# ディレクトリの解析
all_queries = parser.parse_directory(Path("src/main/java"))
print(f"Total queries found: {len(all_queries)}")

# 統計情報
stats = parser.get_statistics()
print(f"Files analyzed: {stats['files_analyzed']}")
print(f"Queries found: {stats['queries_found']}")
```
"""

from multidb_analyzer.elasticsearch.parsers.java_client_parser import ElasticsearchJavaParser

__all__ = [
    'ElasticsearchJavaParser',
]
