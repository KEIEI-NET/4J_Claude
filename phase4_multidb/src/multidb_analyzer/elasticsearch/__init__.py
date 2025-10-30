"""
Elasticsearch Analyzer Module

Elasticsearchコードの静的解析モジュール

このモジュールは以下を提供します:
- Javaクライアントコードのパーサー
- クエリパターンの検出器
- Elasticsearch特有のデータモデル

使用例:
```python
from multidb_analyzer.elasticsearch.parsers import ElasticsearchJavaParser
from multidb_analyzer.elasticsearch.detectors import (
    WildcardDetector,
    ScriptQueryDetector,
    MappingDetector,
    ShardDetector
)

# パーサーの初期化
parser = ElasticsearchJavaParser()

# ファイルの解析
queries = parser.parse_file(Path("SearchService.java"))

# 問題検出
detectors = [
    WildcardDetector(),
    ScriptQueryDetector(),
    MappingDetector(),
    ShardDetector()
]

all_issues = []
for detector in detectors:
    issues = detector.detect(queries)
    all_issues.extend(issues)

# 結果の表示
for issue in all_issues:
    print(f"{issue.severity}: {issue.title}")
    print(f"  {issue.suggestion}")
```
"""

from multidb_analyzer.elasticsearch.parsers import ElasticsearchJavaParser
from multidb_analyzer.elasticsearch.detectors import (
    WildcardDetector,
    ScriptQueryDetector,
    MappingDetector,
    ShardDetector
)

__all__ = [
    'ElasticsearchJavaParser',
    'WildcardDetector',
    'ScriptQueryDetector',
    'MappingDetector',
    'ShardDetector',
]
