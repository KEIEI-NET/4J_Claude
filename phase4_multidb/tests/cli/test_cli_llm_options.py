"""
Tests for CLI LLM Options

CLI LLMオプションの包括的テストスイート
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
import tempfile

from multidb_analyzer.core.base_detector import Severity
from multidb_analyzer.cli.main import cli, analyze


@pytest.fixture
def runner():
    """CliRunner インスタンス"""
    return CliRunner()


@pytest.fixture
def temp_source():
    """一時ソースディレクトリ"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # サンプルファイル作成
        test_file = Path(tmpdir) / "test.java"
        test_file.write_text("public class Test {}")
        yield tmpdir


@pytest.fixture(autouse=True)
def mock_generate_reports():
    """_generate_reports関数をmock - レポート生成をスキップ"""
    with patch('multidb_analyzer.cli.main._generate_reports', return_value=[]):
        yield


class TestCLILLMOptions:
    """CLI LLMオプションのテスト"""

    def test_llm_flag_basic(self, runner, temp_source):
        """基本的な--llmフラグのテスト"""
        with patch('multidb_analyzer.cli.main.UnifiedAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.analyze.return_value = Mock(

                total_files=1,

                analyzed_files=1,

                execution_time=1.0,

                total_issues=0,

                critical_count=0,

                high_count=0,

                medium_count=0,

                low_count=0,

                issues=[],

                errors=[],

                warnings=[]

            )
            mock_analyzer_class.return_value = mock_analyzer

            result = runner.invoke(analyze, [
                temp_source,
                '--llm',
                '--llm-api-key', 'test-key',
                            ])

            # CLIが成功したか
            assert result.exit_code == 0

            # UnifiedAnalyzerがLLM有効で呼ばれたか
            mock_analyzer_class.assert_called_once()
            call_kwargs = mock_analyzer_class.call_args[1]
            assert call_kwargs['enable_llm'] is True
            assert call_kwargs['llm_api_key'] == 'test-key'

    def test_llm_model_option(self, runner, temp_source):
        """--llm-modelオプションのテスト"""
        with patch('multidb_analyzer.cli.main.UnifiedAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.analyze.return_value = Mock(

                total_files=1,

                analyzed_files=1,

                execution_time=1.0,

                total_issues=0,

                critical_count=0,

                high_count=0,

                medium_count=0,

                low_count=0,

                issues=[],

                errors=[],

                warnings=[]

            )
            mock_analyzer_class.return_value = mock_analyzer

            # Sonnet
            result = runner.invoke(analyze, [
                temp_source,
                '--llm',
                '--llm-api-key', 'test-key',
                '--llm-model', 'claude-sonnet-3.5',
                            ])

            assert result.exit_code == 0
            call_kwargs = mock_analyzer_class.call_args[1]
            assert call_kwargs['llm_model'] == 'claude-sonnet-3.5'

    def test_llm_model_opus(self, runner, temp_source):
        """Opusモデルのテスト"""
        with patch('multidb_analyzer.cli.main.UnifiedAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.analyze.return_value = Mock(

                total_files=1,

                analyzed_files=1,

                execution_time=1.0,

                total_issues=0,

                critical_count=0,

                high_count=0,

                medium_count=0,

                low_count=0,

                issues=[],

                errors=[],

                warnings=[]

            )
            mock_analyzer_class.return_value = mock_analyzer

            result = runner.invoke(analyze, [
                temp_source,
                '--llm',
                '--llm-api-key', 'test-key',
                '--llm-model', 'claude-opus',
                            ])

            assert result.exit_code == 0
            call_kwargs = mock_analyzer_class.call_args[1]
            assert call_kwargs['llm_model'] == 'claude-opus'

    def test_llm_model_haiku(self, runner, temp_source):
        """Haikuモデルのテスト"""
        with patch('multidb_analyzer.cli.main.UnifiedAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.analyze.return_value = Mock(

                total_files=1,

                analyzed_files=1,

                execution_time=1.0,

                total_issues=0,

                critical_count=0,

                high_count=0,

                medium_count=0,

                low_count=0,

                issues=[],

                errors=[],

                warnings=[]

            )
            mock_analyzer_class.return_value = mock_analyzer

            result = runner.invoke(analyze, [
                temp_source,
                '--llm',
                '--llm-api-key', 'test-key',
                '--llm-model', 'claude-haiku',
                            ])

            assert result.exit_code == 0
            call_kwargs = mock_analyzer_class.call_args[1]
            assert call_kwargs['llm_model'] == 'claude-haiku'

    def test_llm_severity_critical(self, runner, temp_source):
        """--llm-severity criticalのテスト"""
        with patch('multidb_analyzer.cli.main.UnifiedAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.analyze.return_value = Mock(

                total_files=1,

                analyzed_files=1,

                execution_time=1.0,

                total_issues=0,

                critical_count=0,

                high_count=0,

                medium_count=0,

                low_count=0,

                issues=[],

                errors=[],

                warnings=[]

            )
            mock_analyzer_class.return_value = mock_analyzer

            result = runner.invoke(analyze, [
                temp_source,
                '--llm',
                '--llm-api-key', 'test-key',
                '--llm-severity', 'critical',
                            ])

            assert result.exit_code == 0
            call_kwargs = mock_analyzer_class.call_args[1]
            assert call_kwargs['llm_min_severity'] == Severity.CRITICAL

    def test_llm_severity_high(self, runner, temp_source):
        """--llm-severity highのテスト"""
        with patch('multidb_analyzer.cli.main.UnifiedAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.analyze.return_value = Mock(

                total_files=1,

                analyzed_files=1,

                execution_time=1.0,

                total_issues=0,

                critical_count=0,

                high_count=0,

                medium_count=0,

                low_count=0,

                issues=[],

                errors=[],

                warnings=[]

            )
            mock_analyzer_class.return_value = mock_analyzer

            result = runner.invoke(analyze, [
                temp_source,
                '--llm',
                '--llm-api-key', 'test-key',
                '--llm-severity', 'high',
                            ])

            assert result.exit_code == 0
            call_kwargs = mock_analyzer_class.call_args[1]
            assert call_kwargs['llm_min_severity'] == Severity.HIGH

    def test_llm_severity_medium(self, runner, temp_source):
        """--llm-severity mediumのテスト"""
        with patch('multidb_analyzer.cli.main.UnifiedAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.analyze.return_value = Mock(

                total_files=1,

                analyzed_files=1,

                execution_time=1.0,

                total_issues=0,

                critical_count=0,

                high_count=0,

                medium_count=0,

                low_count=0,

                issues=[],

                errors=[],

                warnings=[]

            )
            mock_analyzer_class.return_value = mock_analyzer

            result = runner.invoke(analyze, [
                temp_source,
                '--llm',
                '--llm-api-key', 'test-key',
                '--llm-severity', 'medium',
                            ])

            assert result.exit_code == 0
            call_kwargs = mock_analyzer_class.call_args[1]
            assert call_kwargs['llm_min_severity'] == Severity.MEDIUM

    def test_llm_severity_low(self, runner, temp_source):
        """--llm-severity lowのテスト"""
        with patch('multidb_analyzer.cli.main.UnifiedAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.analyze.return_value = Mock(

                total_files=1,

                analyzed_files=1,

                execution_time=1.0,

                total_issues=0,

                critical_count=0,

                high_count=0,

                medium_count=0,

                low_count=0,

                issues=[],

                errors=[],

                warnings=[]

            )
            mock_analyzer_class.return_value = mock_analyzer

            result = runner.invoke(analyze, [
                temp_source,
                '--llm',
                '--llm-api-key', 'test-key',
                '--llm-severity', 'low',
                            ])

            assert result.exit_code == 0
            call_kwargs = mock_analyzer_class.call_args[1]
            assert call_kwargs['llm_min_severity'] == Severity.LOW

    def test_llm_batch_size(self, runner, temp_source):
        """--llm-batch-sizeオプションのテスト"""
        with patch('multidb_analyzer.cli.main.UnifiedAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.analyze.return_value = Mock(

                total_files=1,

                analyzed_files=1,

                execution_time=1.0,

                total_issues=0,

                critical_count=0,

                high_count=0,

                medium_count=0,

                low_count=0,

                issues=[],

                errors=[],

                warnings=[]

            )
            mock_analyzer_class.return_value = mock_analyzer

            result = runner.invoke(analyze, [
                temp_source,
                '--llm',
                '--llm-api-key', 'test-key',
                '--llm-batch-size', '10',
                            ])

            assert result.exit_code == 0
            call_kwargs = mock_analyzer_class.call_args[1]
            assert call_kwargs['llm_batch_size'] == 10

    def test_llm_rate_limit(self, runner, temp_source):
        """--llm-rate-limitオプションのテスト"""
        with patch('multidb_analyzer.cli.main.UnifiedAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.analyze.return_value = Mock(

                total_files=1,

                analyzed_files=1,

                execution_time=1.0,

                total_issues=0,

                critical_count=0,

                high_count=0,

                medium_count=0,

                low_count=0,

                issues=[],

                errors=[],

                warnings=[]

            )
            mock_analyzer_class.return_value = mock_analyzer

            result = runner.invoke(analyze, [
                temp_source,
                '--llm',
                '--llm-api-key', 'test-key',
                '--llm-rate-limit', '30',
                            ])

            assert result.exit_code == 0
            call_kwargs = mock_analyzer_class.call_args[1]
            assert call_kwargs['llm_rate_limit_rpm'] == 30

    def test_llm_all_options_combined(self, runner, temp_source):
        """全LLMオプション組み合わせのテスト"""
        with patch('multidb_analyzer.cli.main.UnifiedAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.analyze.return_value = Mock(

                total_files=1,

                analyzed_files=1,

                execution_time=1.0,

                total_issues=0,

                critical_count=0,

                high_count=0,

                medium_count=0,

                low_count=0,

                issues=[],

                errors=[],

                warnings=[]

            )
            mock_analyzer_class.return_value = mock_analyzer

            result = runner.invoke(analyze, [
                temp_source,
                '--llm',
                '--llm-api-key', 'test-api-key',
                '--llm-model', 'claude-opus',
                '--llm-severity', 'critical',
                '--llm-batch-size', '8',
                '--llm-rate-limit', '25',
                            ])

            assert result.exit_code == 0
            call_kwargs = mock_analyzer_class.call_args[1]
            assert call_kwargs['enable_llm'] is True
            assert call_kwargs['llm_api_key'] == 'test-api-key'
            assert call_kwargs['llm_model'] == 'claude-opus'
            assert call_kwargs['llm_min_severity'] == Severity.CRITICAL
            assert call_kwargs['llm_batch_size'] == 8
            assert call_kwargs['llm_rate_limit_rpm'] == 25

    def test_llm_disabled_by_default(self, runner, temp_source):
        """LLMがデフォルトで無効のテスト"""
        with patch('multidb_analyzer.cli.main.UnifiedAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.analyze.return_value = Mock(

                total_files=1,

                analyzed_files=1,

                execution_time=1.0,

                total_issues=0,

                critical_count=0,

                high_count=0,

                medium_count=0,

                low_count=0,

                issues=[],

                errors=[],

                warnings=[]

            )
            mock_analyzer_class.return_value = mock_analyzer

            # --llmフラグなし
            result = runner.invoke(analyze, [
                temp_source,
                            ])

            assert result.exit_code == 0
            call_kwargs = mock_analyzer_class.call_args[1]
            assert call_kwargs.get('enable_llm', False) is False

    def test_llm_api_key_from_env(self, runner, temp_source):
        """環境変数からのAPIキー取得のテスト"""
        with patch('multidb_analyzer.cli.main.UnifiedAnalyzer') as mock_analyzer_class:
            with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'env-api-key'}):
                mock_analyzer = Mock()
                mock_analyzer.analyze.return_value = Mock(

                    total_files=1,

                    analyzed_files=1,

                    execution_time=1.0,

                    total_issues=0,

                    critical_count=0,

                    high_count=0,

                    medium_count=0,

                    low_count=0,

                    issues=[],

                    errors=[],

                    warnings=[]

                )
                mock_analyzer_class.return_value = mock_analyzer

                result = runner.invoke(analyze, [
                    temp_source,
                    '--llm',
                                    ])

                assert result.exit_code == 0
                call_kwargs = mock_analyzer_class.call_args[1]
                # 環境変数から取得されたキー
                assert call_kwargs['llm_api_key'] == 'env-api-key'

    def test_llm_without_api_key(self, runner, temp_source):
        """APIキーなしでのLLM有効化（警告のみ）"""
        with patch('multidb_analyzer.cli.main.UnifiedAnalyzer') as mock_analyzer_class:
            with patch.dict('os.environ', {}, clear=True):
                mock_analyzer = Mock()
                mock_analyzer.analyze.return_value = Mock(

                    total_files=1,

                    analyzed_files=1,

                    execution_time=1.0,

                    total_issues=0,

                    critical_count=0,

                    high_count=0,

                    medium_count=0,

                    low_count=0,

                    issues=[],

                    errors=[],

                    warnings=[]

                )
                mock_analyzer_class.return_value = mock_analyzer

                # APIキーなしで--llm
                result = runner.invoke(analyze, [
                    temp_source,
                    '--llm',
                                    ])

                # APIキーがないのでエラーで終了
                assert result.exit_code == 1
                assert 'API key' in result.output or 'api-key' in result.output

    def test_llm_default_values(self, runner, temp_source):
        """LLMオプションのデフォルト値テスト"""
        with patch('multidb_analyzer.cli.main.UnifiedAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.analyze.return_value = Mock(

                total_files=1,

                analyzed_files=1,

                execution_time=1.0,

                total_issues=0,

                critical_count=0,

                high_count=0,

                medium_count=0,

                low_count=0,

                issues=[],

                errors=[],

                warnings=[]

            )
            mock_analyzer_class.return_value = mock_analyzer

            result = runner.invoke(analyze, [
                temp_source,
                '--llm',
                '--llm-api-key', 'test-key',
                            ])

            assert result.exit_code == 0
            call_kwargs = mock_analyzer_class.call_args[1]

            # デフォルト値確認
            assert call_kwargs['llm_model'] == 'claude-sonnet-3.5'
            assert call_kwargs['llm_min_severity'] == Severity.HIGH
            assert call_kwargs['llm_batch_size'] == 5
            assert call_kwargs['llm_rate_limit_rpm'] == 50


class TestCLIIntegrationWithOtherOptions:
    """他のオプションとの統合テスト"""

    def test_llm_with_elasticsearch(self, runner, temp_source):
        """Elasticsearch + LLMの組み合わせ"""
        with patch('multidb_analyzer.cli.main.UnifiedAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.analyze.return_value = Mock(

                total_files=1,

                analyzed_files=1,

                execution_time=1.0,

                total_issues=0,

                critical_count=0,

                high_count=0,

                medium_count=0,

                low_count=0,

                issues=[],

                errors=[],

                warnings=[]

            )
            mock_analyzer_class.return_value = mock_analyzer

            result = runner.invoke(analyze, [
                temp_source,
                '--db', 'elasticsearch',
                '--llm',
                '--llm-api-key', 'test-key'
            ])

            assert result.exit_code == 0
            call_kwargs = mock_analyzer_class.call_args[1]
            assert call_kwargs['enable_elasticsearch'] is True
            assert call_kwargs['enable_mysql'] is False
            assert call_kwargs['enable_llm'] is True

    def test_llm_with_mysql(self, runner, temp_source):
        """MySQL + LLMの組み合わせ"""
        with patch('multidb_analyzer.cli.main.UnifiedAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.analyze.return_value = Mock(

                total_files=1,

                analyzed_files=1,

                execution_time=1.0,

                total_issues=0,

                critical_count=0,

                high_count=0,

                medium_count=0,

                low_count=0,

                issues=[],

                errors=[],

                warnings=[]

            )
            mock_analyzer_class.return_value = mock_analyzer

            result = runner.invoke(analyze, [
                temp_source,
                '--db', 'mysql',
                '--llm',
                '--llm-api-key', 'test-key'
            ])

            assert result.exit_code == 0
            call_kwargs = mock_analyzer_class.call_args[1]
            assert call_kwargs['enable_elasticsearch'] is False
            assert call_kwargs['enable_mysql'] is True
            assert call_kwargs['enable_llm'] is True

    def test_llm_with_all_databases(self, runner, temp_source):
        """全DB + LLMの組み合わせ"""
        with patch('multidb_analyzer.cli.main.UnifiedAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.analyze.return_value = Mock(

                total_files=1,

                analyzed_files=1,

                execution_time=1.0,

                total_issues=0,

                critical_count=0,

                high_count=0,

                medium_count=0,

                low_count=0,

                issues=[],

                errors=[],

                warnings=[]

            )
            mock_analyzer_class.return_value = mock_analyzer

            result = runner.invoke(analyze, [
                temp_source,
                '--db', 'all',
                '--llm',
                '--llm-api-key', 'test-key',
                '--llm-model', 'claude-sonnet-3.5',
                '--llm-severity', 'high'
            ])

            assert result.exit_code == 0
            call_kwargs = mock_analyzer_class.call_args[1]
            assert call_kwargs['enable_elasticsearch'] is True
            assert call_kwargs['enable_mysql'] is True
            assert call_kwargs['enable_llm'] is True
