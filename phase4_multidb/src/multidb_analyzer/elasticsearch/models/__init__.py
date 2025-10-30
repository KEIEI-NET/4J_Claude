"""
Elasticsearch Data Models

Elasticsearch解析に使用するデータモデル

モデル一覧:
- ElasticsearchQueryType: クエリタイプの列挙型
- AggregationType: Aggregationタイプの列挙型
- WildcardPattern: ワイルドカードパターン情報
- ScriptQuery: Script Query情報
- MappingIssue: マッピング問題情報
- ShardConfiguration: Shard設定情報

使用例:
```python
from multidb_analyzer.elasticsearch.models import (
    WildcardPattern,
    ScriptQuery,
    ShardConfiguration
)

# ワイルドカードパターン
pattern = WildcardPattern(
    pattern="*smith",
    field_name="name",
    starts_with_wildcard=True,
    ends_with_wildcard=False
)
print(f"Is problematic: {pattern.is_problematic()}")
print(f"Severity: {pattern.get_severity()}")

# Script Query
script = ScriptQuery(
    script_lang="painless",
    script_source="doc['price'].value * doc['quantity'].value > 1000",
    is_inline=True
)
print(f"Is complex: {script.is_complex()}")

# Shard設定
shard_config = ShardConfiguration(
    index_name="products",
    shard_count=100,
    replica_count=1,
    index_size_gb=100.0
)
print(f"Is over-sharded: {shard_config.is_over_sharded()}")
print(f"Recommended shards: {shard_config.get_recommended_shard_count()}")
```
"""

from multidb_analyzer.elasticsearch.models.es_models import (
    ElasticsearchQueryType,
    AggregationType,
    WildcardPattern,
    ScriptQuery,
    MappingIssue,
    ShardConfiguration,
)

__all__ = [
    'ElasticsearchQueryType',
    'AggregationType',
    'WildcardPattern',
    'ScriptQuery',
    'MappingIssue',
    'ShardConfiguration',
]
