"""
Elasticsearch Models

Elasticsearch解析用のデータモデル
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


class ElasticsearchQueryType(Enum):
    """Elasticsearchクエリタイプ"""
    MATCH = "match"
    TERM = "term"
    RANGE = "range"
    WILDCARD = "wildcard"
    SCRIPT = "script"
    BOOL = "bool"
    MULTI_MATCH = "multi_match"
    FUZZY = "fuzzy"
    PREFIX = "prefix"
    QUERY_STRING = "query_string"


class AggregationType(Enum):
    """Aggregationタイプ"""
    TERMS = "terms"
    SUM = "sum"
    AVG = "avg"
    MAX = "max"
    MIN = "min"
    CARDINALITY = "cardinality"
    DATE_HISTOGRAM = "date_histogram"
    HISTOGRAM = "histogram"


@dataclass
class ElasticsearchQuery:
    """
    Elasticsearchクエリ情報

    ParsedQueryのElasticsearch特化版
    """
    query_type: ElasticsearchQueryType
    field_name: Optional[str] = None
    query_value: Optional[str] = None
    is_wildcard: bool = False
    is_script: bool = False
    script_content: Optional[str] = None
    boost: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ElasticsearchAggregation:
    """Elasticsearch Aggregation情報"""
    aggregation_type: AggregationType
    name: str
    field_name: Optional[str] = None
    sub_aggregations: List['ElasticsearchAggregation'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ElasticsearchIndex:
    """Elasticsearchインデックス情報"""
    index_name: str
    shard_count: Optional[int] = None
    replica_count: Optional[int] = None
    mapping: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None


@dataclass
class WildcardPattern:
    """
    ワイルドカードパターン

    問題のあるワイルドカードパターンを表現
    """
    pattern: str
    field_name: str
    starts_with_wildcard: bool = False
    ends_with_wildcard: bool = False
    contains_wildcard: bool = False

    def is_problematic(self) -> bool:
        """問題のあるパターンか判定"""
        # 先頭にワイルドカードがある場合は問題
        return self.starts_with_wildcard

    def get_severity(self) -> str:
        """重要度を取得"""
        if self.starts_with_wildcard:
            return "HIGH"
        if self.contains_wildcard:
            return "MEDIUM"
        return "LOW"


@dataclass
class ScriptQuery:
    """Script Query情報"""
    script_lang: str = "painless"
    script_source: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)
    is_inline: bool = True

    def is_complex(self) -> bool:
        """複雑なスクリプトか判定"""
        if not self.script_source:
            return False

        # 長いスクリプト
        if len(self.script_source) > 100:
            return True

        # ループや条件分岐を含む
        complex_keywords = ['for', 'while', 'if', 'else', 'def']
        return any(keyword in self.script_source for keyword in complex_keywords)


@dataclass
class MappingIssue:
    """マッピング問題"""
    index_name: str
    field_name: str
    issue_type: str  # 'dynamic_mapping', 'wrong_type', 'missing_analyzer'
    expected_type: Optional[str] = None
    actual_type: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class ShardConfiguration:
    """Shard設定情報"""
    index_name: str
    shard_count: int
    replica_count: int
    index_size_gb: Optional[float] = None
    document_count: Optional[int] = None

    def is_over_sharded(self) -> bool:
        """過度なシャーディングか判定"""
        # 推奨: 1シャードあたり20-50GB
        if self.index_size_gb and self.shard_count > 0:
            shard_size_gb = self.index_size_gb / self.shard_count
            if shard_size_gb < 10:  # 10GB未満は細かすぎる
                return True

        # ドキュメント数ベース
        if self.document_count and self.shard_count > 0:
            docs_per_shard = self.document_count / self.shard_count
            if docs_per_shard < 1_000_000:  # 100万件未満は細かすぎる
                return True

        return False

    def is_under_sharded(self) -> bool:
        """シャード数が少なすぎるか判定"""
        # 1シャードあたり50GB超過
        if self.index_size_gb and self.shard_count > 0:
            shard_size_gb = self.index_size_gb / self.shard_count
            if shard_size_gb > 50:
                return True

        return False

    def get_recommended_shard_count(self) -> Optional[int]:
        """推奨シャード数を計算"""
        if not self.index_size_gb:
            return None

        # 1シャードあたり30GBを目標
        target_shard_size_gb = 30
        recommended = max(1, int(self.index_size_gb / target_shard_size_gb))

        return recommended
