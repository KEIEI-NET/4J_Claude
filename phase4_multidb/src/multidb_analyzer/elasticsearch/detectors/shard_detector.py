"""
Shard Detector for Elasticsearch

Shard設定の最適化を検出
過度なシャーディング（Over-sharding）や不十分なシャーディング（Under-sharding）は
リソースの無駄遣いやパフォーマンス低下を引き起こす
"""

from typing import List, Optional, Dict, Any
import re

from multidb_analyzer.core.base_detector import (
    BaseDetector,
    Issue,
    Severity,
    IssueCategory
)
from multidb_analyzer.core.base_parser import ParsedQuery
from multidb_analyzer.elasticsearch.models.es_models import ShardConfiguration


class ShardDetector(BaseDetector):
    """
    Shard設定検出器

    検出パターン:
    1. 過度なシャーディング (HIGH) - シャードが小さすぎる（< 10GB）
    2. 不十分なシャーディング (MEDIUM) - シャードが大きすぎる（> 50GB）
    3. レプリカ数の最適化 (MEDIUM)
    4. 固定シャード数の使用 (INFO)

    ベストプラクティス:
    - 1シャードあたり20-50GBを目安とする
    - ノード数を考慮したシャード数設定
    - プライマリシャード数は後から変更不可
    - レプリカ数は動的に変更可能

    例:
    ```java
    // ❌ HIGH - 過度なシャーディング（1000シャード、各100MB = 100GB）
    CreateIndexRequest request = new CreateIndexRequest("logs")
        .settings(Settings.builder()
            .put("index.number_of_shards", 1000)  // 多すぎる！
            .put("index.number_of_replicas", 1)
        );
    // 推奨: 3-5シャード（各20-30GB）

    // ❌ MEDIUM - 不十分なシャーディング（1シャード、500GB）
    CreateIndexRequest request = new CreateIndexRequest("products")
        .settings(Settings.builder()
            .put("index.number_of_shards", 1)  // 少なすぎる！
            .put("index.number_of_replicas", 2)
        );
    // 推奨: 15-20シャード（各25-33GB）

    // ⚠️ INFO - 固定シャード数（将来の拡張性に注意）
    Settings.builder()
        .put("index.number_of_shards", 5);  // ハードコード
    // 推奨: 設定ファイルや環境変数から読み込む

    // ✅ Good - 適切なシャード数
    // 想定インデックスサイズ: 100GB
    // 3ノードクラスター
    CreateIndexRequest request = new CreateIndexRequest("events")
        .settings(Settings.builder()
            .put("index.number_of_shards", 4)      // 各25GB
            .put("index.number_of_replicas", 1)    // 可用性確保
        );
    ```

    参考:
    - Elasticsearch公式ガイド: Size your shards
    - 推奨シャードサイズ: 20GB - 50GB
    - 最大シャードサイズ: 50GB (検索パフォーマンス維持)
    - ノードあたりシャード数: < 20個が理想
    """

    # シャードサイズの閾値（GB）
    MIN_RECOMMENDED_SHARD_SIZE_GB = 10
    OPTIMAL_SHARD_SIZE_GB_MIN = 20
    OPTIMAL_SHARD_SIZE_GB_MAX = 50
    MAX_RECOMMENDED_SHARD_SIZE_GB = 50

    # ノードあたりの推奨最大シャード数
    MAX_SHARDS_PER_NODE = 20

    # シャード数の閾値
    VERY_HIGH_SHARD_COUNT = 100
    HIGH_SHARD_COUNT = 50

    def __init__(self, config=None):
        super().__init__(config)
        self._shard_configs: Dict[str, ShardConfiguration] = {}
        self._min_shard_size_gb = self.get_config_value(
            'min_shard_size_gb',
            self.MIN_RECOMMENDED_SHARD_SIZE_GB
        )
        self._max_shard_size_gb = self.get_config_value(
            'max_shard_size_gb',
            self.MAX_RECOMMENDED_SHARD_SIZE_GB
        )

    def get_name(self) -> str:
        return "ShardDetector"

    def get_severity(self) -> Severity:
        return Severity.HIGH

    def get_category(self) -> IssueCategory:
        return IssueCategory.SCALABILITY

    def detect(self, queries: List[ParsedQuery]) -> List[Issue]:
        """
        Shard設定の問題を検出

        Args:
            queries: 解析されたクエリのリスト

        Returns:
            検出された問題のリスト
        """
        issues = []

        for query in queries:
            # CreateIndexRequest のチェック
            if self._is_create_index(query):
                shard_config = self._extract_shard_config(query)
                if shard_config:
                    # 過度なシャーディングのチェック
                    overshard_issue = self._check_over_sharding(query, shard_config)
                    if overshard_issue:
                        issues.append(overshard_issue)

                    # 不十分なシャーディングのチェック
                    undershard_issue = self._check_under_sharding(query, shard_config)
                    if undershard_issue:
                        issues.append(undershard_issue)

                    # レプリカ数のチェック
                    replica_issue = self._check_replica_count(query, shard_config)
                    if replica_issue:
                        issues.append(replica_issue)

                    # 固定シャード数のチェック
                    hardcoded_issue = self._check_hardcoded_shards(query, shard_config)
                    if hardcoded_issue:
                        issues.append(hardcoded_issue)

        self._issues.extend(issues)
        return issues

    def _is_create_index(self, query: ParsedQuery) -> bool:
        """
        CreateIndexRequestか判定

        Args:
            query: 解析されたクエリ

        Returns:
            CreateIndexRequestの場合True
        """
        return (
            'CreateIndexRequest' in query.query_text or
            'createIndex' in query.query_text or
            'number_of_shards' in query.query_text
        )

    def _extract_shard_config(self, query: ParsedQuery) -> Optional[ShardConfiguration]:
        """
        Shard設定を抽出

        Args:
            query: 解析されたクエリ

        Returns:
            ShardConfiguration（見つからない場合None）
        """
        # インデックス名を抽出
        index_name = self._extract_index_name(query)
        if not index_name:
            index_name = "unknown"

        # シャード数を抽出
        shard_count = self._extract_shard_count(query)
        if shard_count is None:
            return None

        # レプリカ数を抽出
        replica_count = self._extract_replica_count(query)
        if replica_count is None:
            replica_count = 1  # デフォルト

        # インデックスサイズを抽出（コメントやメタデータから）
        index_size_gb = self._extract_index_size(query)

        return ShardConfiguration(
            index_name=index_name,
            shard_count=shard_count,
            replica_count=replica_count,
            index_size_gb=index_size_gb
        )

    def _extract_index_name(self, query: ParsedQuery) -> Optional[str]:
        """インデックス名を抽出"""
        # CreateIndexRequest("index_name") パターン
        match = re.search(r'CreateIndexRequest\s*\(\s*["\']([^"\']+)["\']', query.query_text)
        if match:
            return match.group(1)

        # パラメータから取得
        if query.parameters:
            return query.parameters.get('index_name', query.parameters.get('arg0'))

        return None

    def _extract_shard_count(self, query: ParsedQuery) -> Optional[int]:
        """シャード数を抽出"""
        # number_of_shards パターン
        patterns = [
            r'number_of_shards["\']?\s*,\s*(\d+)',
            r'numberOfShards\s*\(\s*(\d+)',
            r'setNumberOfShards\s*\(\s*(\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, query.query_text)
            if match:
                return int(match.group(1))

        return None

    def _extract_replica_count(self, query: ParsedQuery) -> Optional[int]:
        """レプリカ数を抽出"""
        # number_of_replicas パターン
        patterns = [
            r'number_of_replicas["\']?\s*,\s*(\d+)',
            r'numberOfReplicas\s*\(\s*(\d+)',
            r'setNumberOfReplicas\s*\(\s*(\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, query.query_text)
            if match:
                return int(match.group(1))

        return None

    def _extract_index_size(self, query: ParsedQuery) -> Optional[float]:
        """
        インデックスサイズを抽出（コメントやメタデータから推測）

        Args:
            query: 解析されたクエリ

        Returns:
            インデックスサイズ（GB）
        """
        # コメントから抽出: // Expected size: 100GB
        size_patterns = [
            r'expected\s+size:\s*(\d+\.?\d*)\s*GB',
            r'index\s+size:\s*(\d+\.?\d*)\s*GB',
            r'total:\s*(\d+\.?\d*)\s*GB',
        ]

        for pattern in size_patterns:
            match = re.search(pattern, query.query_text, re.IGNORECASE)
            if match:
                return float(match.group(1))

        # メタデータから取得
        if query.metadata and 'index_size_gb' in query.metadata:
            return float(query.metadata['index_size_gb'])

        return None

    def _check_over_sharding(
        self,
        query: ParsedQuery,
        config: ShardConfiguration
    ) -> Optional[Issue]:
        """
        過度なシャーディングをチェック

        Args:
            query: 解析されたクエリ
            config: Shard設定

        Returns:
            過度なシャーディングの場合Issue
        """
        # シャード数が非常に多い場合
        if config.shard_count >= self.VERY_HIGH_SHARD_COUNT:
            return self._create_over_sharding_issue(
                query, config, "very_high_count"
            )

        # インデックスサイズが既知で、シャードが小さすぎる場合
        if config.index_size_gb and config.is_over_sharded():
            return self._create_over_sharding_issue(
                query, config, "small_shard_size"
            )

        return None

    def _check_under_sharding(
        self,
        query: ParsedQuery,
        config: ShardConfiguration
    ) -> Optional[Issue]:
        """
        不十分なシャーディングをチェック

        Args:
            query: 解析されたクエリ
            config: Shard設定

        Returns:
            不十分なシャーディングの場合Issue
        """
        if not config.index_size_gb:
            return None

        # シャードあたりのサイズを計算
        shard_size_gb = config.index_size_gb / config.shard_count

        # シャードが大きすぎる
        if shard_size_gb > self._max_shard_size_gb:
            return self._create_under_sharding_issue(query, config, shard_size_gb)

        return None

    def _check_replica_count(
        self,
        query: ParsedQuery,
        config: ShardConfiguration
    ) -> Optional[Issue]:
        """
        レプリカ数をチェック

        Args:
            query: 解析されたクエリ
            config: Shard設定

        Returns:
            レプリカ数の問題がある場合Issue
        """
        # レプリカが0の場合（プロダクションでは推奨されない）
        if config.replica_count == 0:
            return self._create_replica_issue(query, config)

        # レプリカが多すぎる（通常1-2で十分）
        if config.replica_count > 2:
            return self._create_high_replica_issue(query, config)

        return None

    def _check_hardcoded_shards(
        self,
        query: ParsedQuery,
        config: ShardConfiguration
    ) -> Optional[Issue]:
        """
        固定シャード数をチェック

        Args:
            query: 解析されたクエリ
            config: Shard設定

        Returns:
            固定シャード数の場合Issue（INFO）
        """
        # 数値がハードコードされているかチェック
        # （設定ファイルや変数から読み込んでいない）
        if re.search(r'number_of_shards["\']?\s*,\s*\d+', query.query_text):
            return self._create_hardcoded_issue(query, config)

        return None

    def _create_over_sharding_issue(
        self,
        query: ParsedQuery,
        config: ShardConfiguration,
        reason: str
    ) -> Issue:
        """過度なシャーディング問題のIssueを作成"""
        if reason == "very_high_count":
            title = f"Excessive shard count ({config.shard_count}) for index '{config.index_name}'"
            description = (
                f"The index '{config.index_name}' is configured with {config.shard_count} shards. "
                f"This is an extremely high number and will create significant overhead. "
                f"Each shard consumes memory and file handles, and too many shards can "
                f"degrade cluster performance and stability."
            )
        else:  # small_shard_size
            shard_size = config.index_size_gb / config.shard_count if config.index_size_gb else 0
            recommended = config.get_recommended_shard_count()
            title = f"Over-sharding detected for index '{config.index_name}' - shards too small"
            description = (
                f"The index '{config.index_name}' is configured with {config.shard_count} shards "
                f"for an estimated {config.index_size_gb}GB of data. "
                f"This results in approximately {shard_size:.1f}GB per shard, "
                f"which is below the recommended minimum of {self._min_shard_size_gb}GB. "
                f"Small shards create unnecessary overhead and reduce performance."
            )

        suggestion = self._generate_shard_suggestion(config)

        return self.create_issue(
            title=title,
            description=description,
            file_path=query.file_path,
            line_number=query.line_number,
            severity=Severity.HIGH,
            query_text=query.query_text,
            method_name=query.method_name,
            class_name=query.class_name,
            suggestion=suggestion,
            auto_fix_available=False,
            documentation_url="https://www.elastic.co/guide/en/elasticsearch/reference/current/size-your-shards.html",
            tags=['elasticsearch', 'sharding', 'over-sharding', 'scalability'],
            metadata={
                'index_name': config.index_name,
                'shard_count': config.shard_count,
                'index_size_gb': config.index_size_gb,
                'recommended_shard_count': config.get_recommended_shard_count()
            }
        )

    def _create_under_sharding_issue(
        self,
        query: ParsedQuery,
        config: ShardConfiguration,
        shard_size_gb: float
    ) -> Issue:
        """不十分なシャーディング問題のIssueを作成"""
        recommended = config.get_recommended_shard_count()

        title = f"Under-sharding detected for index '{config.index_name}' - shards too large"

        description = (
            f"The index '{config.index_name}' is configured with {config.shard_count} shards "
            f"for an estimated {config.index_size_gb}GB of data. "
            f"This results in approximately {shard_size_gb:.1f}GB per shard, "
            f"which exceeds the recommended maximum of {self._max_shard_size_gb}GB. "
            f"Large shards can cause slow recovery times, memory pressure, and degraded search performance."
        )

        suggestion = self._generate_shard_suggestion(config)

        return self.create_issue(
            title=title,
            description=description,
            file_path=query.file_path,
            line_number=query.line_number,
            severity=Severity.MEDIUM,
            query_text=query.query_text,
            method_name=query.method_name,
            class_name=query.class_name,
            suggestion=suggestion,
            auto_fix_available=False,
            documentation_url="https://www.elastic.co/guide/en/elasticsearch/reference/current/size-your-shards.html",
            tags=['elasticsearch', 'sharding', 'under-sharding', 'scalability'],
            metadata={
                'index_name': config.index_name,
                'shard_count': config.shard_count,
                'shard_size_gb': shard_size_gb,
                'recommended_shard_count': recommended
            }
        )

    def _create_replica_issue(
        self,
        query: ParsedQuery,
        config: ShardConfiguration
    ) -> Issue:
        """レプリカ0の問題のIssueを作成"""
        title = f"No replicas configured for index '{config.index_name}'"

        description = (
            f"The index '{config.index_name}' is configured with 0 replicas. "
            f"This means there is no redundancy, and data will be lost if a node fails. "
            f"In production environments, at least 1 replica is strongly recommended for data durability."
        )

        suggestion = (
            f"Set 'number_of_replicas' to at least 1 for production environments. "
            f"With 1 replica, your data can survive a single node failure. "
            f"For critical data or high availability requirements, consider 2 replicas. "
            f"Note that replicas can be adjusted dynamically without reindexing."
        )

        return self.create_issue(
            title=title,
            description=description,
            file_path=query.file_path,
            line_number=query.line_number,
            severity=Severity.MEDIUM,
            query_text=query.query_text,
            method_name=query.method_name,
            class_name=query.class_name,
            suggestion=suggestion,
            auto_fix_available=False,
            documentation_url="https://www.elastic.co/guide/en/elasticsearch/reference/current/index-modules.html#dynamic-index-settings",
            tags=['elasticsearch', 'replica', 'reliability', 'best-practice'],
            metadata={
                'index_name': config.index_name,
                'replica_count': config.replica_count
            }
        )

    def _create_high_replica_issue(
        self,
        query: ParsedQuery,
        config: ShardConfiguration
    ) -> Issue:
        """レプリカが多すぎる問題のIssueを作成"""
        title = f"High replica count ({config.replica_count}) for index '{config.index_name}'"

        description = (
            f"The index '{config.index_name}' is configured with {config.replica_count} replicas. "
            f"While replicas provide redundancy, each replica consumes storage and resources. "
            f"For most use cases, 1-2 replicas are sufficient."
        )

        suggestion = (
            f"Review whether {config.replica_count} replicas are necessary. "
            f"Typically, 1 replica is sufficient for most production workloads, "
            f"and 2 replicas provide high availability. "
            f"More than 2 replicas are rarely needed unless you have specific requirements."
        )

        return self.create_issue(
            title=title,
            description=description,
            file_path=query.file_path,
            line_number=query.line_number,
            severity=Severity.LOW,
            query_text=query.query_text,
            method_name=query.method_name,
            class_name=query.class_name,
            suggestion=suggestion,
            auto_fix_available=False,
            documentation_url="https://www.elastic.co/guide/en/elasticsearch/reference/current/index-modules.html#dynamic-index-settings",
            tags=['elasticsearch', 'replica', 'optimization'],
            metadata={
                'index_name': config.index_name,
                'replica_count': config.replica_count
            }
        )

    def _create_hardcoded_issue(
        self,
        query: ParsedQuery,
        config: ShardConfiguration
    ) -> Issue:
        """固定シャード数の問題のIssueを作成"""
        title = f"Hardcoded shard count for index '{config.index_name}'"

        description = (
            f"The shard count ({config.shard_count}) appears to be hardcoded. "
            f"Hardcoding shard counts makes it difficult to adjust for different environments "
            f"(development, staging, production) or to optimize for changing data volumes."
        )

        suggestion = (
            f"Consider reading the shard count from a configuration file, "
            f"environment variable, or application properties. "
            f"This allows you to adjust shard counts based on the environment and data volume "
            f"without modifying code. Remember that primary shard count cannot be changed "
            f"after index creation (requires reindexing)."
        )

        return self.create_issue(
            title=title,
            description=description,
            file_path=query.file_path,
            line_number=query.line_number,
            severity=Severity.INFO,
            query_text=query.query_text,
            method_name=query.method_name,
            class_name=query.class_name,
            suggestion=suggestion,
            auto_fix_available=False,
            documentation_url="https://www.elastic.co/guide/en/elasticsearch/reference/current/index-modules.html",
            tags=['elasticsearch', 'configuration', 'best-practice'],
            metadata={
                'index_name': config.index_name,
                'shard_count': config.shard_count
            }
        )

    def _generate_shard_suggestion(self, config: ShardConfiguration) -> str:
        """シャード数の最適化提案を生成"""
        suggestions = []

        recommended = config.get_recommended_shard_count()
        if recommended:
            suggestions.append(
                f"Based on the estimated index size of {config.index_size_gb}GB, "
                f"a recommended shard count would be {recommended} shards "
                f"(targeting {self.OPTIMAL_SHARD_SIZE_GB_MIN}-{self.OPTIMAL_SHARD_SIZE_GB_MAX}GB per shard)."
            )

        suggestions.append(
            "Follow these guidelines: "
            f"(1) Aim for {self.OPTIMAL_SHARD_SIZE_GB_MIN}-{self.OPTIMAL_SHARD_SIZE_GB_MAX}GB per shard. "
            "(2) Keep the number of shards per node under 20 for optimal performance. "
            "(3) Consider using Index Lifecycle Management (ILM) for time-series data. "
            "(4) Remember that primary shard count cannot be changed after creation."
        )

        return " ".join(suggestions)
