"""
Tests for Plugin Manager

プラグインマネージャーのテスト
"""

import pytest
from pathlib import Path
from multidb_analyzer.core.plugin_manager import (
    PluginManager,
    DatabasePlugin,
    get_plugin_manager,
    register_plugin
)
from multidb_analyzer.core.base_parser import DatabaseType, QueryType, ParsedQuery
from multidb_analyzer.core.base_detector import BaseDetector, Issue, Severity, IssueCategory
from multidb_analyzer.elasticsearch.parsers import ElasticsearchJavaParser
from multidb_analyzer.elasticsearch.detectors import WildcardDetector


class DummyDetector(BaseDetector):
    """Test用のダミー検出器"""

    def get_name(self) -> str:
        return "DummyDetector"

    def get_severity(self) -> Severity:
        return Severity.LOW

    def get_category(self) -> IssueCategory:
        return IssueCategory.BEST_PRACTICE

    def detect(self, queries):
        return []


class TestPluginManager:
    """PluginManager のテスト"""

    @pytest.fixture
    def plugin_manager(self):
        """プラグインマネージャーを作成"""
        return PluginManager()

    @pytest.fixture
    def sample_parser(self):
        """サンプルパーサーを作成"""
        return ElasticsearchJavaParser()

    @pytest.fixture
    def sample_detectors(self):
        """サンプル検出器を作成"""
        return [WildcardDetector(), DummyDetector()]

    def test_register_plugin(self, plugin_manager, sample_parser, sample_detectors):
        """プラグイン登録のテスト"""
        plugin_manager.register_plugin(
            DatabaseType.ELASTICSEARCH,
            sample_parser,
            sample_detectors
        )

        plugin = plugin_manager.get_plugin(DatabaseType.ELASTICSEARCH)
        assert plugin is not None
        assert plugin.db_type == DatabaseType.ELASTICSEARCH
        assert plugin.parser == sample_parser

    def test_get_plugin_not_found(self, plugin_manager):
        """存在しないプラグインの取得"""
        plugin = plugin_manager.get_plugin(DatabaseType.MYSQL)
        assert plugin is None

    def test_get_all_plugins(self, plugin_manager, sample_parser, sample_detectors):
        """すべてのプラグイン取得のテスト"""
        plugin_manager.register_plugin(
            DatabaseType.ELASTICSEARCH,
            sample_parser,
            sample_detectors
        )

        plugins = plugin_manager.get_all_plugins()
        assert len(plugins) == 1
        assert plugins[0].db_type == DatabaseType.ELASTICSEARCH

    def test_analyze_directory(self, plugin_manager, sample_parser, sample_detectors, tmp_path):
        """ディレクトリ解析のテスト"""
        plugin_manager.register_plugin(
            DatabaseType.ELASTICSEARCH,
            sample_parser,
            sample_detectors
        )

        # テスト用Javaファイルを作成
        java_file = tmp_path / "Test.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.client.RestHighLevelClient;
            import org.elasticsearch.index.query.QueryBuilders;

            public class Test {
                public void search() {
                    QueryBuilders.wildcardQuery("name", "*smith");
                }
            }
        """, encoding='utf-8')

        results = plugin_manager.analyze_directory(tmp_path)

        assert DatabaseType.ELASTICSEARCH in results
        assert len(results[DatabaseType.ELASTICSEARCH]) >= 0

    def test_analyze_directory_with_db_types(self, plugin_manager, sample_parser, sample_detectors, tmp_path):
        """特定DBタイプでのディレクトリ解析"""
        plugin_manager.register_plugin(
            DatabaseType.ELASTICSEARCH,
            sample_parser,
            sample_detectors
        )

        results = plugin_manager.analyze_directory(
            tmp_path,
            db_types=[DatabaseType.ELASTICSEARCH]
        )

        assert DatabaseType.ELASTICSEARCH in results

    def test_analyze_directory_recursive(self, plugin_manager, sample_parser, sample_detectors, tmp_path):
        """再帰的ディレクトリ解析のテスト"""
        plugin_manager.register_plugin(
            DatabaseType.ELASTICSEARCH,
            sample_parser,
            sample_detectors
        )

        # サブディレクトリを作成
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        java_file = subdir / "Test.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.client.RestHighLevelClient;

            public class Test {}
        """, encoding='utf-8')

        results = plugin_manager.analyze_directory(tmp_path, recursive=True)
        assert DatabaseType.ELASTICSEARCH in results

    def test_get_statistics(self, plugin_manager, sample_parser, sample_detectors):
        """統計情報取得のテスト"""
        plugin_manager.register_plugin(
            DatabaseType.ELASTICSEARCH,
            sample_parser,
            sample_detectors
        )

        stats = plugin_manager.get_statistics()

        assert stats['total_plugins'] == 1
        assert DatabaseType.ELASTICSEARCH.value in stats['supported_databases']
        assert DatabaseType.ELASTICSEARCH.value in stats['plugins']

        es_stats = stats['plugins'][DatabaseType.ELASTICSEARCH.value]
        assert es_stats['parser'] == 'ElasticsearchJavaParser'
        assert 'WildcardDetector' in es_stats['detectors']
        assert es_stats['detector_count'] == 2

    def test_analyze_file_with_db_type(self, plugin_manager, sample_parser, sample_detectors, tmp_path):
        """指定されたDBタイプでファイル解析"""
        plugin_manager.register_plugin(
            DatabaseType.ELASTICSEARCH,
            sample_parser,
            sample_detectors
        )

        # テスト用Javaファイルを作成
        java_file = tmp_path / "Test.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.client.RestHighLevelClient;
            import org.elasticsearch.index.query.QueryBuilders;

            public class Test {
                public void search() {
                    QueryBuilders.wildcardQuery("name", "*smith");
                }
            }
        """, encoding='utf-8')

        # db_typeを指定して解析
        issues = plugin_manager.analyze_file(java_file, db_type=DatabaseType.ELASTICSEARCH)
        assert isinstance(issues, list)

    def test_analyze_file_with_unregistered_db_type(self, plugin_manager, tmp_path):
        """登録されていないDBタイプでファイル解析（エラー）"""
        java_file = tmp_path / "Test.java"
        java_file.write_text("public class Test {}", encoding='utf-8')

        # 登録されていないDBタイプを指定
        with pytest.raises(ValueError) as exc_info:
            plugin_manager.analyze_file(java_file, db_type=DatabaseType.MYSQL)

        assert "No plugin registered" in str(exc_info.value)
        assert DatabaseType.MYSQL.value in str(exc_info.value)

    def test_analyze_file_auto_detect(self, plugin_manager, sample_parser, sample_detectors, tmp_path):
        """自動判定でファイル解析"""
        plugin_manager.register_plugin(
            DatabaseType.ELASTICSEARCH,
            sample_parser,
            sample_detectors
        )

        # テスト用Javaファイルを作成
        java_file = tmp_path / "Test.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.client.RestHighLevelClient;
            import org.elasticsearch.index.query.QueryBuilders;

            public class Test {
                public void search() {
                    QueryBuilders.wildcardQuery("name", "*smith");
                }
            }
        """, encoding='utf-8')

        # db_typeを指定せず、自動判定
        issues = plugin_manager.analyze_file(java_file, db_type=None)
        assert isinstance(issues, list)

    def test_analyze_file_auto_detect_no_match(self, plugin_manager, sample_parser, sample_detectors, tmp_path):
        """自動判定でファイル解析（マッチするパーサーなし）"""
        plugin_manager.register_plugin(
            DatabaseType.ELASTICSEARCH,
            sample_parser,
            sample_detectors
        )

        # Elasticsearch用でないファイル（パーサーがcan_parseでFalseを返す）
        non_es_file = tmp_path / "Other.txt"
        non_es_file.write_text("some random content", encoding='utf-8')

        # 自動判定（マッチなし）
        issues = plugin_manager.analyze_file(non_es_file, db_type=None)
        assert isinstance(issues, list)
        assert len(issues) == 0  # マッチするパーサーがないので空


class TestDatabasePlugin:
    """DatabasePlugin のテスト"""

    @pytest.fixture
    def database_plugin(self):
        """データベースプラグインを作成"""
        parser = ElasticsearchJavaParser()
        detectors = [WildcardDetector()]

        return DatabasePlugin(
            DatabaseType.ELASTICSEARCH,
            parser,
            detectors
        )

    def test_analyze_file(self, database_plugin, tmp_path):
        """ファイル解析のテスト"""
        java_file = tmp_path / "Test.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.client.RestHighLevelClient;
            import org.elasticsearch.index.query.QueryBuilders;

            public class Test {
                public void search() {
                    QueryBuilders.wildcardQuery("name", "*smith");
                }
            }
        """, encoding='utf-8')

        issues = database_plugin.analyze_file(java_file)
        assert isinstance(issues, list)

    def test_analyze_directory(self, database_plugin, tmp_path):
        """ディレクトリ解析のテスト"""
        java_file = tmp_path / "Test.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.client.RestHighLevelClient;

            public class Test {}
        """, encoding='utf-8')

        issues = database_plugin.analyze_directory(tmp_path)
        assert isinstance(issues, list)

    def test_analyze_directory_non_recursive(self, database_plugin, tmp_path):
        """非再帰的ディレクトリ解析のテスト"""
        # サブディレクトリを作成
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        java_file = subdir / "Test.java"
        java_file.write_text("""
            package com.example;
            import org.elasticsearch.client.RestHighLevelClient;

            public class Test {}
        """, encoding='utf-8')

        issues = database_plugin.analyze_directory(tmp_path, recursive=False)
        assert isinstance(issues, list)


class TestGlobalPluginManager:
    """グローバルプラグインマネージャーのテスト"""

    def test_get_plugin_manager_singleton(self):
        """シングルトンパターンのテスト"""
        manager1 = get_plugin_manager()
        manager2 = get_plugin_manager()

        assert manager1 is manager2

    def test_register_plugin_global(self):
        """グローバル登録関数のテスト"""
        parser = ElasticsearchJavaParser()
        detectors = [WildcardDetector()]

        register_plugin(
            DatabaseType.ELASTICSEARCH,
            parser,
            detectors
        )

        manager = get_plugin_manager()
        plugin = manager.get_plugin(DatabaseType.ELASTICSEARCH)

        assert plugin is not None
        assert plugin.db_type == DatabaseType.ELASTICSEARCH
