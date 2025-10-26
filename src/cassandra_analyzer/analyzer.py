"""
Cassandra分析器のメインクラス

パーサー、検出器、レポーターを統合して分析を実行
"""
import time
from pathlib import Path
from typing import List, Optional, Dict, Any

from cassandra_analyzer.parsers import JavaCassandraParser, ParserFactory
from cassandra_analyzer.detectors import (
    AllowFilteringDetector,
    PartitionKeyDetector,
    BatchSizeDetector,
    PreparedStatementDetector,
)
from cassandra_analyzer.models import AnalysisResult, Issue


class CassandraAnalyzer:
    """
    Cassandra分析器

    Javaファイルを分析してCassandra使用パターンの問題を検出
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Args:
            config: 設定辞書
                - detectors: 有効にする検出器のリスト（デフォルト: 全て）
                - parser_config: パーサー設定
                - detector_configs: 検出器別の設定
        """
        self.config = config or {}

        # パーサーの初期化
        self.parser = self._initialize_parser()

        # 検出器の初期化
        self.detectors = self._initialize_detectors()

    def _initialize_parser(self):
        """パーサーを初期化"""
        # parser設定がある場合はParserFactoryを使用
        if "parser" in self.config:
            return ParserFactory.create_from_config(self.config)

        # 後方互換性のため、parser_configがある場合は正規表現パーサーを使用
        parser_config = self.config.get("parser_config", {})
        return JavaCassandraParser(config=parser_config)

    def _initialize_detectors(self) -> List:
        """検出器を初期化"""
        detector_configs = self.config.get("detector_configs", {})
        enabled_detectors = self.config.get(
            "detectors", ["allow_filtering", "partition_key", "batch_size", "prepared_statement"]
        )

        detectors = []

        if "allow_filtering" in enabled_detectors:
            config = detector_configs.get("allow_filtering", {})
            detectors.append(AllowFilteringDetector(config=config))

        if "partition_key" in enabled_detectors:
            config = detector_configs.get("partition_key", {})
            detectors.append(PartitionKeyDetector(config=config))

        if "batch_size" in enabled_detectors:
            config = detector_configs.get("batch_size", {})
            detectors.append(BatchSizeDetector(config=config))

        if "prepared_statement" in enabled_detectors:
            config = detector_configs.get("prepared_statement", {})
            detectors.append(PreparedStatementDetector(config=config))

        return detectors

    def analyze_file(self, file_path: str) -> AnalysisResult:
        """
        単一ファイルを分析

        Args:
            file_path: 分析するJavaファイルのパス

        Returns:
            分析結果
        """
        return self.analyze_files([file_path])

    def analyze_directory(self, directory: str, pattern: str = "**/*.java") -> AnalysisResult:
        """
        ディレクトリ内のJavaファイルを分析

        Args:
            directory: 分析するディレクトリのパス
            pattern: ファイルパターン（デフォルト: **/*.java）

        Returns:
            分析結果
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        if not dir_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")

        # Javaファイルを検索
        java_files = [str(f) for f in dir_path.glob(pattern)]

        if not java_files:
            # 空の結果を返す
            return AnalysisResult(
                analyzed_files=[],
                total_issues=0,
                issues_by_severity={},
                issues=[],
            )

        return self.analyze_files(java_files)

    def analyze_files(self, file_paths: List[str]) -> AnalysisResult:
        """
        複数ファイルを分析

        Args:
            file_paths: 分析するJavaファイルのパスのリスト

        Returns:
            分析結果
        """
        start_time = time.time()

        all_issues = []
        analyzed_files = []

        # 各ファイルを解析
        for file_path in file_paths:
            try:
                # パース
                calls = self.parser.parse_file(file_path)

                # 検出
                for call in calls:
                    for detector in self.detectors:
                        if detector.is_enabled():
                            issues = detector.detect(call)
                            all_issues.extend(issues)

                analyzed_files.append(file_path)

            except Exception as e:
                # エラーは無視して続行（ログ出力は将来の実装）
                pass

        # 重要度別カウント
        issues_by_severity = self._count_by_severity(all_issues)

        # 分析時間
        analysis_time = time.time() - start_time

        return AnalysisResult(
            analyzed_files=analyzed_files,
            total_issues=len(all_issues),
            issues_by_severity=issues_by_severity,
            issues=all_issues,
            analysis_time=analysis_time,
        )

    def _count_by_severity(self, issues: List[Issue]) -> Dict[str, int]:
        """重要度別に問題をカウント"""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for issue in issues:
            if issue.severity in counts:
                counts[issue.severity] += 1

        return counts
