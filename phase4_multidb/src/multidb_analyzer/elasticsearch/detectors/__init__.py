"""
Elasticsearch Detectors

このモジュールは、Elasticsearchコードの問題検出器を提供します。

検出器一覧:
- WildcardDetector: ワイルドカードクエリの問題検出（先頭ワイルドカード等）
- ScriptQueryDetector: Script Queryの不適切な使用検出
- MappingDetector: Dynamic Mappingへの依存や型の不一致検出
- ShardDetector: Shard設定の最適化検出（過度/不十分なシャーディング）

使用例:
```python
from multidb_analyzer.elasticsearch.detectors import (
    WildcardDetector,
    ScriptQueryDetector,
    MappingDetector,
    ShardDetector
)

# 検出器の初期化
detectors = [
    WildcardDetector(),
    ScriptQueryDetector(),
    MappingDetector(),
    ShardDetector()
]

# クエリの検出
for detector in detectors:
    issues = detector.detect(parsed_queries)
    for issue in issues:
        print(f"{issue.severity}: {issue.title}")
```
"""

from multidb_analyzer.elasticsearch.detectors.wildcard_detector import WildcardDetector
from multidb_analyzer.elasticsearch.detectors.script_query_detector import ScriptQueryDetector
from multidb_analyzer.elasticsearch.detectors.mapping_detector import MappingDetector
from multidb_analyzer.elasticsearch.detectors.shard_detector import ShardDetector

__all__ = [
    'WildcardDetector',
    'ScriptQueryDetector',
    'MappingDetector',
    'ShardDetector',
]
