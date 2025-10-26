"""
CLIモジュールのユニットテスト
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json
import sys

from cassandra_analyzer.cli import (
    load_config,
    save_config,
    get_default_config,
    cmd_analyze,
    cmd_config,
    create_parser,
    main,
)


class TestLoadConfig:
    """load_config関数のテスト"""

    def test_load_json_config(self, tmp_path):
        """JSON設定ファイルの読み込み"""
        config_file = tmp_path / "config.json"
        config_data = {"parser": {"type": "ast"}, "detectors": ["allow_filtering"]}

        with open(config_file, "w") as f:
            json.dump(config_data, f)

        result = load_config(config_file)
        assert result["parser"]["type"] == "ast"
        assert "allow_filtering" in result["detectors"]

    def test_load_nonexistent_config(self, tmp_path):
        """存在しない設定ファイル"""
        config_file = tmp_path / "nonexistent.json"

        with pytest.raises(SystemExit):
            load_config(config_file)

    @pytest.mark.skipif(not pytest.importorskip("yaml", reason="PyYAML not installed"),
                        reason="PyYAML not installed")
    def test_load_yaml_config(self, tmp_path):
        """YAML設定ファイルの読み込み"""
        import yaml

        config_file = tmp_path / "config.yaml"
        config_data = {"parser": {"type": "regex"}, "detectors": ["partition_key"]}

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        result = load_config(config_file)
        assert result["parser"]["type"] == "regex"
        assert "partition_key" in result["detectors"]


class TestSaveConfig:
    """save_config関数のテスト"""

    def test_save_json_config(self, tmp_path):
        """JSON設定ファイルの保存"""
        config_file = tmp_path / "config.json"
        config_data = {"parser": {"type": "ast"}}

        save_config(config_data, config_file)

        assert config_file.exists()
        with open(config_file, "r") as f:
            loaded = json.load(f)
        assert loaded["parser"]["type"] == "ast"

    @pytest.mark.skipif(not pytest.importorskip("yaml", reason="PyYAML not installed"),
                        reason="PyYAML not installed")
    def test_save_yaml_config(self, tmp_path):
        """YAML設定ファイルの保存"""
        import yaml

        config_file = tmp_path / "config.yaml"
        config_data = {"parser": {"type": "regex"}}

        save_config(config_data, config_file)

        assert config_file.exists()
        with open(config_file, "r") as f:
            loaded = yaml.safe_load(f)
        assert loaded["parser"]["type"] == "regex"


class TestGetDefaultConfig:
    """get_default_config関数のテスト"""

    def test_default_config_structure(self):
        """デフォルト設定の構造"""
        config = get_default_config()

        assert "parser" in config
        assert "detectors" in config
        assert "detector_configs" in config
        assert "output" in config

    def test_default_parser_config(self):
        """デフォルトパーサー設定"""
        config = get_default_config()

        assert config["parser"]["type"] == "regex"
        assert config["parser"]["resolve_constants"] is True

    def test_default_detectors(self):
        """デフォルト検出器"""
        config = get_default_config()

        assert "allow_filtering" in config["detectors"]
        assert "partition_key" in config["detectors"]
        assert "batch_size" in config["detectors"]
        assert "prepared_statement" in config["detectors"]


class TestCmdAnalyze:
    """cmd_analyze関数のテスト"""

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

    def test_analyze_single_file(self, sample_java_file):
        """単一ファイルの分析"""
        args = Mock()
        args.input = str(sample_java_file)
        args.config = None
        args.output = None
        args.format = ["json"]
        args.pattern = None
        args.verbose = False

        with patch("cassandra_analyzer.cli.CassandraAnalyzer") as mock_analyzer_class:
            with patch("cassandra_analyzer.cli.JSONReporter") as mock_reporter_class:
                mock_analyzer = Mock()
                mock_result = Mock()
                mock_result.total_files = 1
                mock_result.total_issues = 0
                mock_result.analysis_time = 0.5
                mock_result.issues_by_severity = {}

                mock_analyzer.analyze_file.return_value = mock_result
                mock_analyzer_class.return_value = mock_analyzer

                mock_reporter = Mock()
                mock_reporter_class.return_value = mock_reporter

                result = cmd_analyze(args)

                # 分析が実行された
                mock_analyzer.analyze_file.assert_called_once()
                # レポーターが呼ばれた
                mock_reporter.generate_and_save.assert_called_once()
                assert result == 0  # 問題なし

    def test_analyze_nonexistent_file(self):
        """存在しないファイルの分析"""
        args = Mock()
        args.input = "nonexistent.java"
        args.config = None
        args.output = None
        args.format = ["json"]
        args.pattern = None
        args.verbose = False

        result = cmd_analyze(args)
        assert result == 1  # エラー


class TestCmdConfig:
    """cmd_config関数のテスト"""

    def test_config_init(self, tmp_path):
        """設定ファイルの初期化"""
        output_file = tmp_path / "config.yaml"

        args = Mock()
        args.init = True
        args.validate = False
        args.show = False
        args.config = None
        args.output = str(output_file)
        args.force = False

        result = cmd_config(args)

        assert result == 0
        assert output_file.exists()

    def test_config_init_force_overwrite(self, tmp_path):
        """既存の設定ファイルを強制上書き"""
        output_file = tmp_path / "config.yaml"
        output_file.write_text("old content")

        args = Mock()
        args.init = True
        args.validate = False
        args.show = False
        args.config = None
        args.output = str(output_file)
        args.force = True

        result = cmd_config(args)

        assert result == 0
        # 新しい内容が書き込まれている
        assert "old content" not in output_file.read_text()

    def test_config_show_default(self):
        """デフォルト設定の表示"""
        args = Mock()
        args.init = False
        args.validate = False
        args.show = True
        args.config = None

        result = cmd_config(args)
        assert result == 0

    def test_config_validate_valid(self, tmp_path):
        """有効な設定ファイルの検証"""
        config_file = tmp_path / "config.json"
        config_data = get_default_config()

        with open(config_file, "w") as f:
            json.dump(config_data, f)

        args = Mock()
        args.init = False
        args.validate = True
        args.show = False
        args.config = str(config_file)

        result = cmd_config(args)
        assert result == 0


class TestCreateParser:
    """create_parser関数のテスト"""

    def test_parser_creation(self):
        """パーサーの作成"""
        parser = create_parser()

        assert parser.prog == "cassandra-analyzer"
        assert parser.description is not None

    def test_analyze_subcommand(self):
        """analyzeサブコマンド"""
        parser = create_parser()

        args = parser.parse_args(["analyze", "test.java"])
        assert args.command == "analyze"
        assert args.input == "test.java"

    def test_config_subcommand(self):
        """configサブコマンド"""
        parser = create_parser()

        args = parser.parse_args(["config", "--init"])
        assert args.command == "config"
        assert args.init is True

    def test_analyze_with_options(self):
        """オプション付きanalyzeコマンド"""
        parser = create_parser()

        args = parser.parse_args([
            "analyze",
            "src/",
            "--config", "config.yaml",
            "--format", "json", "markdown",
            "--output", "reports/",
            "--pattern", "**/*.java",
            "--verbose"
        ])

        assert args.command == "analyze"
        assert args.input == "src/"
        assert args.config == Path("config.yaml")
        assert args.format == ["json", "markdown"]
        assert args.output == "reports/"
        assert args.pattern == "**/*.java"
        assert args.verbose is True


class TestMain:
    """main関数のテスト"""

    def test_main_no_command(self):
        """コマンドなし"""
        with patch("sys.argv", ["cassandra-analyzer"]):
            with patch("cassandra_analyzer.cli.create_parser") as mock_parser:
                mock_parser_instance = Mock()
                mock_parser_instance.parse_args.return_value = Mock(command=None)
                mock_parser.return_value = mock_parser_instance

                result = main()
                assert result == 1

    def test_main_analyze_command(self, tmp_path):
        """analyzeコマンド"""
        test_file = tmp_path / "test.java"
        test_file.write_text("public class Test {}")

        with patch("sys.argv", ["cassandra-analyzer", "analyze", str(test_file)]):
            with patch("cassandra_analyzer.cli.cmd_analyze") as mock_analyze:
                mock_analyze.return_value = 0

                result = main()
                mock_analyze.assert_called_once()

    def test_main_config_command(self):
        """configコマンド"""
        with patch("sys.argv", ["cassandra-analyzer", "config", "--show"]):
            with patch("cassandra_analyzer.cli.cmd_config") as mock_config:
                mock_config.return_value = 0

                result = main()
                mock_config.assert_called_once()


    def test_analyze_with_exception(self):
        """分析中の例外処理"""
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".java", delete=False) as f:
            f.write("public class Test {}")
            test_file = f.name

        args = Mock()
        args.input = test_file
        args.config = None
        args.output = None
        args.format = ["json"]
        args.pattern = None
        args.verbose = True

        with patch("cassandra_analyzer.cli.CassandraAnalyzer") as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.analyze_file.side_effect = Exception("Test error")
            mock_analyzer_class.return_value = mock_analyzer

            result = cmd_analyze(args)
            assert result == 1

    def test_analyze_directory(self, tmp_path):
        """ディレクトリの分析"""
        java_dir = tmp_path / "src"
        java_dir.mkdir()
        (java_dir / "Test.java").write_text("public class Test {}")

        args = Mock()
        args.input = str(java_dir)
        args.config = None
        args.output = None
        args.format = ["json"]
        args.pattern = "**/*.java"
        args.verbose = False

        with patch("cassandra_analyzer.cli.CassandraAnalyzer") as mock_analyzer_class:
            with patch("cassandra_analyzer.cli.JSONReporter") as mock_reporter_class:
                mock_analyzer = Mock()
                mock_result = Mock()
                mock_result.total_files = 1
                mock_result.total_issues = 0
                mock_result.analysis_time = 0.5
                mock_result.issues_by_severity = {}

                mock_analyzer.analyze_directory.return_value = mock_result
                mock_analyzer_class.return_value = mock_analyzer

                mock_reporter = Mock()
                mock_reporter_class.return_value = mock_reporter

                result = cmd_analyze(args)
                mock_analyzer.analyze_directory.assert_called_once()
                assert result == 0

    def test_analyze_with_issues(self, tmp_path):
        """問題が検出された場合"""
        test_file = tmp_path / "Test.java"
        test_file.write_text("public class Test {}")

        args = Mock()
        args.input = str(test_file)
        args.config = None
        args.output = None
        args.format = ["json"]
        args.pattern = None
        args.verbose = False

        with patch("cassandra_analyzer.cli.CassandraAnalyzer") as mock_analyzer_class:
            with patch("cassandra_analyzer.cli.JSONReporter") as mock_reporter_class:
                mock_analyzer = Mock()
                mock_result = Mock()
                mock_result.total_files = 1
                mock_result.total_issues = 3
                mock_result.analysis_time = 0.5
                mock_result.issues_by_severity = {"high": 3}

                mock_analyzer.analyze_file.return_value = mock_result
                mock_analyzer_class.return_value = mock_analyzer

                mock_reporter = Mock()
                mock_reporter_class.return_value = mock_reporter

                result = cmd_analyze(args)
                assert result == 1

    def test_config_show_with_file(self, tmp_path):
        """既存設定ファイルの表示"""
        config_file = tmp_path / "config.json"
        config_data = get_default_config()

        with open(config_file, "w") as f:
            json.dump(config_data, f)

        args = Mock()
        args.init = False
        args.validate = False
        args.show = True
        args.config = str(config_file)

        result = cmd_config(args)
        assert result == 0

    def test_config_init_without_force(self, tmp_path):
        """既存ファイルをforce なしで上書きしない"""
        output_file = tmp_path / "config.yaml"
        output_file.write_text("existing content")

        args = Mock()
        args.init = True
        args.validate = False
        args.show = False
        args.config = None
        args.output = str(output_file)
        args.force = False

        result = cmd_config(args)
        assert result == 1

