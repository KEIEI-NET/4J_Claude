"""
Unified Analyzer

複数のDBタイプを統合分析するメインクラス
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from time import time

from multidb_analyzer.core.base_detector import Issue, Severity
from multidb_analyzer.unified.analysis_result import AnalysisResult

# Elasticsearchモジュール
from multidb_analyzer.elasticsearch.parsers.java_client_parser import ElasticsearchJavaParser
from multidb_analyzer.elasticsearch.detectors.mapping_detector import MappingDetector
from multidb_analyzer.elasticsearch.detectors.wildcard_detector import WildcardDetector
from multidb_analyzer.elasticsearch.detectors.shard_detector import ShardDetector
from multidb_analyzer.elasticsearch.detectors.script_query_detector import ScriptQueryDetector

# MySQLモジュール
from multidb_analyzer.mysql.parsers.mysql_parser import MySQLParser
from multidb_analyzer.mysql.detectors.nplus_one_detector import NPlusOneDetector
from multidb_analyzer.mysql.detectors.full_table_scan_detector import FullTableScanDetector
from multidb_analyzer.mysql.detectors.missing_index_detector import MissingIndexDetector
from multidb_analyzer.mysql.detectors.join_performance_detector import JoinPerformanceDetector

# LLMモジュール
from multidb_analyzer.llm.llm_enhancer import LLMEnhancer, LLMConfig

logger = logging.getLogger(__name__)


class UnifiedAnalyzer:
    """
    統合アナライザー

    複数のDBタイプ（Elasticsearch、MySQL）を一度に分析し、
    統一されたAnalysisResultを返します。

    Example:
        >>> analyzer = UnifiedAnalyzer(
        ...     enable_elasticsearch=True,
        ...     enable_mysql=True
        ... )
        >>> result = analyzer.analyze([Path('./src')])
        >>> print(result.get_summary())
    """

    def __init__(
        self,
        enable_elasticsearch: bool = True,
        enable_mysql: bool = True,
        enable_llm: bool = False,
        llm_api_key: Optional[str] = None,
        llm_model: str = "claude-sonnet-3.5",
        llm_min_severity: Severity = Severity.HIGH,
        llm_batch_size: int = 5,
        llm_rate_limit_rpm: int = 50,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        統合アナライザーの初期化

        Args:
            enable_elasticsearch: Elasticsearch分析を有効化
            enable_mysql: MySQL分析を有効化
            enable_llm: LLM最適化を有効化
            llm_api_key: Claude APIキー（LLM有効時必須）
            llm_model: 使用するLLMモデル
            llm_min_severity: LLM分析対象の最小重大度
            llm_batch_size: LLMバッチサイズ
            llm_rate_limit_rpm: LLMレート制限（RPM）
            config: カスタム設定辞書
        """
        self.enable_elasticsearch = enable_elasticsearch
        self.enable_mysql = enable_mysql
        self.enable_llm = enable_llm
        self.llm_api_key = llm_api_key
        self.config = config or {}

        # Elasticsearchコンポーネント
        if self.enable_elasticsearch:
            self.es_parser = ElasticsearchJavaParser()
            self.es_detectors = [
                MappingDetector(),
                WildcardDetector(),
                ShardDetector(),
                ScriptQueryDetector(),
            ]
            logger.info("Elasticsearch analysis enabled with 4 detectors")
        else:
            self.es_parser = None
            self.es_detectors = []

        # MySQLコンポーネント
        if self.enable_mysql:
            self.mysql_parser = MySQLParser()
            self.mysql_detectors = [
                NPlusOneDetector(),
                FullTableScanDetector(),
                MissingIndexDetector(),
                JoinPerformanceDetector(),
            ]
            logger.info("MySQL analysis enabled with 4 detectors")
        else:
            self.mysql_parser = None
            self.mysql_detectors = []

        # LLMコンポーネント
        self.llm_enhancer: Optional[LLMEnhancer] = None
        if self.enable_llm:
            if not llm_api_key:
                logger.warning("LLM enabled but no API key provided")
            else:
                llm_config = LLMConfig(
                    api_key=llm_api_key,
                    model=llm_model,
                    min_severity=llm_min_severity,
                    batch_size=llm_batch_size,
                    rate_limit_rpm=llm_rate_limit_rpm,
                )
                self.llm_enhancer = LLMEnhancer(llm_config)
                logger.info(
                    f"LLM optimization enabled: {llm_model}, "
                    f"min_severity={llm_min_severity.value}, "
                    f"batch_size={llm_batch_size}"
                )

    def analyze(
        self,
        source_paths: List[Path],
        output_dir: Optional[Path] = None,
        config: Optional[Dict] = None
    ) -> AnalysisResult:
        """
        統合分析を実行

        Args:
            source_paths: 分析対象のソースコードパス
            output_dir: 出力ディレクトリ（Noneの場合は./reports/）
            config: カスタム設定（Noneの場合はコンストラクタの設定を使用）

        Returns:
            AnalysisResult: 統合分析結果
        """
        start_time = time()
        timestamp = datetime.now()

        logger.info(f"Starting unified analysis on {len(source_paths)} path(s)")

        # 設定のマージ
        effective_config = {**self.config, **(config or {})}

        # ファイル収集
        all_files = self._collect_files(source_paths)
        total_files = len(all_files)

        logger.info(f"Found {total_files} files to analyze")

        # 分析実行
        all_issues: List[Issue] = []
        analyzed_files = 0
        warnings: List[str] = []
        errors: List[str] = []

        try:
            # Elasticsearch分析
            if self.enable_elasticsearch:
                logger.info("Running Elasticsearch analysis...")
                es_issues, es_analyzed = self._analyze_elasticsearch(all_files)
                all_issues.extend(es_issues)
                analyzed_files += es_analyzed
                logger.info(f"Elasticsearch: {len(es_issues)} issues in {es_analyzed} files")

            # MySQL分析
            if self.enable_mysql:
                logger.info("Running MySQL analysis...")
                mysql_issues, mysql_analyzed = self._analyze_mysql(all_files)
                all_issues.extend(mysql_issues)
                analyzed_files += mysql_analyzed
                logger.info(f"MySQL: {len(mysql_issues)} issues in {mysql_analyzed} files")

            # LLM最適化
            if self.enable_llm and self.llm_enhancer and all_issues:
                logger.info("Applying LLM optimization...")
                all_issues, llm_errors = self._apply_llm_optimization(all_issues)
                if llm_errors:
                    errors.extend(llm_errors)

        except Exception as e:
            error_msg = f"Analysis error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)

        # 実行時間計算
        execution_time = time() - start_time

        # AnalysisResult作成
        result = AnalysisResult(
            timestamp=timestamp,
            total_files=total_files,
            analyzed_files=analyzed_files,
            execution_time=execution_time,
            issues=all_issues,
            config=effective_config,
            warnings=warnings,
            errors=errors
        )

        logger.info(f"Analysis complete: {len(all_issues)} issues in {execution_time:.2f}s")

        return result

    def _collect_files(self, source_paths: List[Path]) -> List[Path]:
        """
        ソースファイルを収集

        Args:
            source_paths: ソースパスのリスト

        Returns:
            収集されたファイルのリスト
        """
        files: List[Path] = []

        for source_path in source_paths:
            if source_path.is_file():
                if self._should_analyze_file(source_path):
                    files.append(source_path)
            elif source_path.is_dir():
                for file_path in source_path.rglob('*.java'):
                    if self._should_analyze_file(file_path):
                        files.append(file_path)
                for file_path in source_path.rglob('*.py'):
                    if self._should_analyze_file(file_path):
                        files.append(file_path)
            else:
                logger.warning(f"Path not found: {source_path}")

        return files

    def _should_analyze_file(self, file_path: Path) -> bool:
        """
        ファイルを分析すべきか判定

        Args:
            file_path: ファイルパス

        Returns:
            分析対象の場合True
        """
        # 除外パターン
        exclude_patterns = [
            'node_modules',
            'target',
            '.git',
            '__pycache__',
            'venv',
            '.venv',
            'build',
            'dist',
        ]

        path_str = str(file_path)
        return not any(pattern in path_str for pattern in exclude_patterns)

    def _analyze_elasticsearch(self, files: List[Path]) -> tuple[List[Issue], int]:
        """
        Elasticsearch分析を実行

        Args:
            files: ファイルリスト

        Returns:
            (問題リスト, 分析ファイル数)
        """
        all_queries = []
        analyzed_count = 0

        for file_path in files:
            try:
                queries = self.es_parser.parse_file(file_path)
                if queries:
                    all_queries.extend(queries)
                    analyzed_count += 1
            except Exception as e:
                logger.warning(f"ES parse error in {file_path}: {e}")

        # 検出器実行
        all_issues = []
        for detector in self.es_detectors:
            try:
                issues = detector.detect(all_queries)
                all_issues.extend(issues)
            except Exception as e:
                logger.warning(f"ES detector {detector.get_name()} error: {e}")

        return all_issues, analyzed_count

    def _analyze_mysql(self, files: List[Path]) -> tuple[List[Issue], int]:
        """
        MySQL分析を実行

        Args:
            files: ファイルリスト

        Returns:
            (問題リスト, 分析ファイル数)
        """
        all_queries = []
        analyzed_count = 0

        for file_path in files:
            try:
                queries = self.mysql_parser.parse_file(file_path)
                if queries:
                    all_queries.extend(queries)
                    analyzed_count += 1
            except Exception as e:
                logger.warning(f"MySQL parse error in {file_path}: {e}")

        # 検出器実行
        all_issues = []
        for detector in self.mysql_detectors:
            try:
                issues = detector.detect(all_queries)
                all_issues.extend(issues)
            except Exception as e:
                logger.warning(f"MySQL detector {detector.get_name()} error: {e}")

        return all_issues, analyzed_count

    def _apply_llm_optimization(
        self,
        issues: List[Issue]
    ) -> tuple[List[Issue], List[str]]:
        """
        LLM最適化を適用

        Args:
            issues: 問題リスト

        Returns:
            (最適化された問題リスト, エラーリスト)
        """
        if not self.llm_enhancer:
            logger.warning("LLM enhancer not initialized, skipping optimization")
            return issues, []

        try:
            # 非同期コンテキストで実行
            loop = asyncio.get_event_loop()
            enhanced_issues, errors = loop.run_until_complete(
                self.llm_enhancer.enhance_issues(issues)
            )

            logger.info(
                f"LLM optimization complete: "
                f"{len(enhanced_issues)} issues enhanced"
            )

            return enhanced_issues, errors

        except Exception as e:
            error_msg = f"LLM optimization failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return issues, [error_msg]

    def get_supported_databases(self) -> List[str]:
        """サポートするDBタイプのリストを取得"""
        supported = []
        if self.enable_elasticsearch:
            supported.append('elasticsearch')
        if self.enable_mysql:
            supported.append('mysql')
        return supported

    def get_detector_count(self) -> int:
        """有効な検出器の総数を取得"""
        count = 0
        if self.enable_elasticsearch:
            count += len(self.es_detectors)
        if self.enable_mysql:
            count += len(self.mysql_detectors)
        return count
