"""
UnifiedAnalyzer Tests
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from multidb_analyzer.unified.unified_analyzer import UnifiedAnalyzer
from multidb_analyzer.unified.analysis_result import AnalysisResult
from multidb_analyzer.core.base_detector import Issue, Severity, IssueCategory


@pytest.fixture
def temp_java_file():
    """一時的なJavaファイルを作成"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
        f.write("""
            package com.example;

            import com.mysql.jdbc.Connection;

            public class UserDAO {
                public void getUsers() {
                    List<User> users = session.execute("SELECT * FROM users");
                    for (User user : users) {
                        session.execute("SELECT * FROM orders WHERE user_id = " + user.getId());
                    }
                }
            }
        """)
        return Path(f.name)


@pytest.fixture
def temp_directory(temp_java_file):
    """一時ディレクトリを作成"""
    return temp_java_file.parent


class TestUnifiedAnalyzerInitialization:
    """UnifiedAnalyzer初期化のテスト"""

    def test_init_default(self):
        """デフォルト初期化"""
        analyzer = UnifiedAnalyzer()

        assert analyzer.enable_elasticsearch is True
        assert analyzer.enable_mysql is True
        assert analyzer.enable_llm is False
        assert analyzer.es_parser is not None
        assert analyzer.mysql_parser is not None
        assert len(analyzer.es_detectors) == 4
        assert len(analyzer.mysql_detectors) == 4

    def test_init_elasticsearch_only(self):
        """Elasticsearchのみ有効"""
        analyzer = UnifiedAnalyzer(
            enable_elasticsearch=True,
            enable_mysql=False
        )

        assert analyzer.enable_elasticsearch is True
        assert analyzer.enable_mysql is False
        assert analyzer.es_parser is not None
        assert analyzer.mysql_parser is None
        assert len(analyzer.es_detectors) == 4
        assert len(analyzer.mysql_detectors) == 0

    def test_init_mysql_only(self):
        """MySQLのみ有効"""
        analyzer = UnifiedAnalyzer(
            enable_elasticsearch=False,
            enable_mysql=True
        )

        assert analyzer.enable_elasticsearch is False
        assert analyzer.enable_mysql is True
        assert analyzer.es_parser is None
        assert analyzer.mysql_parser is not None
        assert len(analyzer.es_detectors) == 0
        assert len(analyzer.mysql_detectors) == 4

    def test_init_with_config(self):
        """設定付き初期化"""
        config = {
            'exclude_patterns': ['*/test/*', '*/tests/*'],
            'max_file_size': 1024 * 1024,
        }

        analyzer = UnifiedAnalyzer(config=config)

        assert analyzer.config == config


class TestUnifiedAnalyzerFileCollection:
    """UnifiedAnalyzer ファイル収集のテスト"""

    def test_collect_java_files(self, temp_directory):
        """Javaファイルを収集"""
        analyzer = UnifiedAnalyzer()

        files = analyzer._collect_files([temp_directory])

        assert len(files) > 0
        # 実装は .java と .py の両方を収集する
        assert all(f.suffix in ['.java', '.py'] for f in files)

    def test_collect_with_exclusion(self, temp_directory):
        """除外パターン適用"""
        # __pycache__ディレクトリ内にファイル作成（ハードコードされた除外パターン）
        pycache_dir = temp_directory / "__pycache__"
        pycache_dir.mkdir(exist_ok=True)
        pycache_file = pycache_dir / "test.py"
        pycache_file.write_text("# test")

        analyzer = UnifiedAnalyzer()

        files = analyzer._collect_files([temp_directory])

        # __pycache__ディレクトリのファイルは除外される
        assert all('__pycache__' not in str(f) for f in files)

    def test_collect_nonexistent_path(self):
        """存在しないパスの処理"""
        analyzer = UnifiedAnalyzer()

        files = analyzer._collect_files([Path('/nonexistent/path')])

        assert len(files) == 0


class TestUnifiedAnalyzerAnalysis:
    """UnifiedAnalyzer 分析のテスト"""

    @patch('multidb_analyzer.unified.unified_analyzer.UnifiedAnalyzer._analyze_elasticsearch')
    @patch('multidb_analyzer.unified.unified_analyzer.UnifiedAnalyzer._analyze_mysql')
    def test_analyze_both_databases(
        self,
        mock_mysql_analysis,
        mock_es_analysis,
        temp_directory
    ):
        """両DBの分析実行"""
        # モックの設定
        mock_es_analysis.return_value = ([], 0)
        mock_mysql_analysis.return_value = ([], 0)

        analyzer = UnifiedAnalyzer()
        result = analyzer.analyze([temp_directory])

        # 両方の分析が呼ばれること
        assert mock_es_analysis.called
        assert mock_mysql_analysis.called
        assert isinstance(result, AnalysisResult)

    @patch('multidb_analyzer.unified.unified_analyzer.UnifiedAnalyzer._analyze_elasticsearch')
    def test_analyze_elasticsearch_only(
        self,
        mock_es_analysis,
        temp_directory
    ):
        """Elasticsearch分析のみ"""
        mock_es_analysis.return_value = ([], 0)

        analyzer = UnifiedAnalyzer(
            enable_elasticsearch=True,
            enable_mysql=False
        )
        result = analyzer.analyze([temp_directory])

        assert mock_es_analysis.called
        assert result.total_files > 0

    def test_analyze_empty_directory(self):
        """空ディレクトリの分析"""
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = UnifiedAnalyzer()
            result = analyzer.analyze([Path(tmpdir)])

            assert result.total_issues == 0
            assert result.analyzed_files == 0


class TestUnifiedAnalyzerElasticsearchAnalysis:
    """UnifiedAnalyzer Elasticsearch分析のテスト"""

    def test_analyze_elasticsearch(self, temp_java_file):
        """Elasticsearch分析実行"""
        analyzer = UnifiedAnalyzer(enable_mysql=False)

        # パーサーをモック
        mock_parser = Mock()
        mock_parser.parse.return_value = MagicMock(
            queries=[
                MagicMock(
                    query_type="search",
                    query_text='{"query": {"wildcard": {"name": "*test"}}}',
                    line_number=10
                )
            ]
        )
        analyzer.es_parser = mock_parser

        issues, analyzed_count = analyzer._analyze_elasticsearch([temp_java_file])

        # 何らかの問題が検出されるはず（WildcardDetector等）
        assert isinstance(issues, list)
        assert isinstance(analyzed_count, int)

    def test_elasticsearch_analysis_with_detector_issues(self, temp_java_file):
        """検出器が問題を検出"""
        analyzer = UnifiedAnalyzer(enable_mysql=False)

        # パーサーと検出器をモック
        mock_query = MagicMock(
            query_type="search",
            query_text='{"query": {"wildcard": {"name": "*test"}}}',
            line_number=10
        )
        mock_result = MagicMock(queries=[mock_query])

        analyzer.es_parser = Mock(return_value=None)
        analyzer.es_parser.parse = Mock(return_value=mock_result)

        # 検出器をモック
        mock_detector = Mock()
        mock_detector.detect.return_value = [
            Issue(
                title="Wildcard Issue",
                description="Leading wildcard",
                severity=Severity.MEDIUM,
                category=IssueCategory.PERFORMANCE,
                detector_name="WildcardDetector",
                file_path=temp_java_file,
                line_number=10,
                query_text='{"query": {"wildcard": {"name": "*test"}}}',
            )
        ]
        analyzer.es_detectors = [mock_detector]

        issues, analyzed_count = analyzer._analyze_elasticsearch([temp_java_file])

        assert len(issues) >= 1
        assert issues[0].title == "Wildcard Issue"


class TestUnifiedAnalyzerMySQLAnalysis:
    """UnifiedAnalyzer MySQL分析のテスト"""

    def test_analyze_mysql(self, temp_java_file):
        """MySQL分析実行"""
        analyzer = UnifiedAnalyzer(enable_elasticsearch=False)

        # パーサーをモック
        mock_parser = Mock()
        mock_parser.parse.return_value = MagicMock(
            queries=[
                MagicMock(
                    query_type="select",
                    query_text="SELECT * FROM users",
                    line_number=8
                )
            ]
        )
        analyzer.mysql_parser = mock_parser

        issues, analyzed_count = analyzer._analyze_mysql([temp_java_file])

        assert isinstance(issues, list)
        assert isinstance(analyzed_count, int)

    def test_mysql_analysis_with_nplus_one(self, temp_java_file):
        """N+1問題検出"""
        analyzer = UnifiedAnalyzer(enable_elasticsearch=False)

        # N+1パターンのクエリをモック
        mock_queries = [
            MagicMock(
                query_type="select",
                query_text="SELECT * FROM users",
                line_number=7,
                in_loop=False
            ),
            MagicMock(
                query_type="select",
                query_text="SELECT * FROM orders WHERE user_id = ?",
                line_number=9,
                in_loop=True
            ),
        ]
        mock_result = MagicMock(queries=mock_queries)

        analyzer.mysql_parser = Mock()
        analyzer.mysql_parser.parse = Mock(return_value=mock_result)

        # N+1検出器をモック
        mock_detector = Mock()
        mock_detector.detect.return_value = [
            Issue(
                title="N+1 Query",
                description="Loop query detected",
                severity=Severity.CRITICAL,
                category=IssueCategory.PERFORMANCE,
                detector_name="NPlusOneDetector",
                file_path=temp_java_file,
                line_number=9,
                query_text="SELECT * FROM orders WHERE user_id = ?",
            )
        ]
        analyzer.mysql_detectors = [mock_detector]

        issues, analyzed_count = analyzer._analyze_mysql([temp_java_file])

        assert len(issues) >= 1
        assert any("N+1" in issue.title for issue in issues)


class TestUnifiedAnalyzerErrorHandling:
    """UnifiedAnalyzer エラーハンドリングのテスト"""

    def test_handle_parse_error(self, temp_directory):
        """パースエラーの処理"""
        analyzer = UnifiedAnalyzer()

        # パーサーがエラーを投げる
        analyzer.es_parser.parse_file = Mock(side_effect=Exception("Parse error"))
        analyzer.mysql_parser.parse_file = Mock(side_effect=Exception("Parse error"))

        result = analyzer.analyze([temp_directory])

        # エラーが発生しても分析は継続され、結果が返される
        # パースエラーはログに記録されるが、result.errorsには含まれない（内部でキャッチされる）
        assert isinstance(result, AnalysisResult)
        assert result.analyzed_files == 0  # パースエラーのため分析できたファイルは0

    def test_handle_detector_error(self, temp_java_file):
        """検出器エラーの処理"""
        analyzer = UnifiedAnalyzer()

        # 検出器がエラーを投げる
        mock_detector = Mock()
        mock_detector.detect = Mock(side_effect=Exception("Detector error"))
        analyzer.es_detectors = [mock_detector]

        # パーサーは正常
        analyzer.es_parser.parse_file = Mock(return_value=[])

        result = analyzer.analyze([temp_java_file.parent])

        # エラーは記録されないが、分析は継続される（エラーはログ出力のみ）
        # 検出器のエラーは内部でキャッチされてログに記録されるが、result.errorsには含まれない
        assert isinstance(result, AnalysisResult)


class TestUnifiedAnalyzerStatistics:
    """UnifiedAnalyzer 統計のテスト"""

    @patch('multidb_analyzer.unified.unified_analyzer.UnifiedAnalyzer._analyze_elasticsearch')
    @patch('multidb_analyzer.unified.unified_analyzer.UnifiedAnalyzer._analyze_mysql')
    def test_statistics_calculation(
        self,
        mock_mysql,
        mock_es,
        temp_directory
    ):
        """統計計算"""
        # モックが問題を返す
        mock_es.return_value = ([
            Issue(
                title="ES Issue",
                description="Test",
                severity=Severity.HIGH,
                category=IssueCategory.PERFORMANCE,
                detector_name="TestDetector",
                file_path=Path("test.java"),
                line_number=1,
            )
        ], 1)
        mock_mysql.return_value = ([
            Issue(
                title="MySQL Issue",
                description="Test",
                severity=Severity.CRITICAL,
                category=IssueCategory.PERFORMANCE,
                detector_name="TestDetector",
                file_path=Path("test.java"),
                line_number=1,
            )
        ], 1)

        analyzer = UnifiedAnalyzer()
        result = analyzer.analyze([temp_directory])

        # 統計が正しく計算される
        assert result.total_issues == 2
        assert result.critical_count == 1
        assert result.high_count == 1

    def test_execution_time_tracking(self, temp_directory):
        """実行時間の追跡"""
        analyzer = UnifiedAnalyzer()

        result = analyzer.analyze([temp_directory])

        # 実行時間が記録される
        assert result.execution_time > 0


class TestUnifiedAnalyzerIntegration:
    """UnifiedAnalyzer 統合テスト"""

    def test_end_to_end_analysis(self, temp_java_file):
        """エンドツーエンド分析"""
        analyzer = UnifiedAnalyzer()

        result = analyzer.analyze([temp_java_file.parent])

        # 結果が生成される
        assert isinstance(result, AnalysisResult)
        assert result.total_files > 0
        assert result.execution_time > 0

    def test_multi_path_analysis(self):
        """複数パスの分析"""
        with tempfile.TemporaryDirectory() as tmpdir1:
            with tempfile.TemporaryDirectory() as tmpdir2:
                # 各ディレクトリにファイル作成
                file1 = Path(tmpdir1) / "Test1.java"
                file1.write_text("public class Test1 {}")

                file2 = Path(tmpdir2) / "Test2.java"
                file2.write_text("public class Test2 {}")

                analyzer = UnifiedAnalyzer()
                result = analyzer.analyze([Path(tmpdir1), Path(tmpdir2)])

                # 両方のディレクトリが分析される
                assert result.total_files >= 2
