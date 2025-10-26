"""
CassandraAnalyzerのユニットテスト
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from cassandra_analyzer.analyzer import CassandraAnalyzer
from cassandra_analyzer.models import AnalysisResult, Issue


class TestCassandraAnalyzer:
    """CassandraAnalyzerのテストクラス"""

    @pytest.fixture
    def analyzer(self):
        """テスト用Analyzer"""
        return CassandraAnalyzer()

    @pytest.fixture
    def sample_java_file(self, tmp_path):
        """サンプルJavaファイル"""
        java_file = tmp_path / "Test.java"
        java_file.write_text("""
        public class Test {
            public void test() {
                session.execute("SELECT * FROM users WHERE id = ?");
            }
        }
        """)
        return java_file

    def test_analyze_directory_not_found(self, analyzer):
        """存在しないディレクトリの分析"""
        with pytest.raises(FileNotFoundError, match="Directory not found"):
            analyzer.analyze_directory("/nonexistent/directory")

    def test_analyze_directory_not_a_directory(self, analyzer, sample_java_file):
        """ファイルをディレクトリとして分析しようとする"""
        with pytest.raises(NotADirectoryError, match="Not a directory"):
            analyzer.analyze_directory(str(sample_java_file))

    def test_analyze_directory_no_matching_files(self, analyzer, tmp_path):
        """マッチするファイルがない場合"""
        # 空のディレクトリ
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = analyzer.analyze_directory(str(empty_dir), pattern="**/*.java")

        assert result.total_files == 0
        assert result.total_issues == 0
        assert len(result.analyzed_files) == 0
        assert len(result.issues) == 0

    def test_analyze_directory_with_pattern(self, analyzer, tmp_path):
        """パターンを指定してディレクトリを分析"""
        # サブディレクトリにJavaファイルを作成
        subdir = tmp_path / "src"
        subdir.mkdir()
        java_file = subdir / "Test.java"
        java_file.write_text("""
        public class Test {
            public void test() {
                session.execute("SELECT * FROM users WHERE id = ?");
            }
        }
        """)

        result = analyzer.analyze_directory(str(tmp_path), pattern="**/*.java")

        assert result.total_files >= 1

    def test_analyze_files_with_error(self, analyzer, tmp_path):
        """ファイル分析中のエラー処理"""
        # 正常なファイル
        good_file = tmp_path / "Good.java"
        good_file.write_text("""
        public class Good {
            public void test() {
                session.execute("SELECT * FROM users WHERE id = ?");
            }
        }
        """)

        # 不正なファイル（存在しない）
        bad_file = tmp_path / "Bad.java"

        # パーサーがエラーを投げるようにモック
        with patch.object(analyzer.parser, 'parse_file') as mock_parse:
            # 最初の呼び出しは成功、2回目はエラー
            mock_parse.side_effect = [
                [],  # 正常なファイル（Cassandra呼び出しなし）
                Exception("Parse error")  # エラー
            ]

            # 例外が発生しても分析は続行される
            result = analyzer.analyze_files([str(good_file), str(bad_file)])

            # 正常に処理されたファイルのみカウント
            assert result.total_files == 1

    def test_analyze_file_success(self, analyzer, sample_java_file):
        """単一ファイルの正常な分析"""
        result = analyzer.analyze_file(str(sample_java_file))

        assert result.total_files == 1
        assert len(result.analyzed_files) == 1
        assert result.analysis_time >= 0

    def test_analyze_files_empty_list(self, analyzer):
        """空のファイルリストの分析"""
        result = analyzer.analyze_files([])

        assert result.total_files == 0
        assert result.total_issues == 0
        assert len(result.issues) == 0
