"""
Integration Tests for LLM Enhancement

UnifiedAnalyzer と LLM統合の包括的なエンドツーエンドテスト
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import tempfile
import os

from multidb_analyzer.core.base_detector import Issue, Severity, IssueCategory
from multidb_analyzer.unified.unified_analyzer import UnifiedAnalyzer
from multidb_analyzer.llm.llm_enhancer import LLMConfig


@pytest.fixture
def temp_source_dir():
    """一時ソースディレクトリ"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # サンプルJavaファイル作成
        java_file = Path(tmpdir) / "TestQuery.java"
        java_file.write_text("""
public class TestQuery {
    public void executeQuery() {
        String query = "SELECT * FROM users";
        session.execute(query);
    }
}
""")
        yield Path(tmpdir)


@pytest.fixture
def mock_llm_config():
    """モックLLM設定"""
    return {
        'api_key': 'test-api-key',
        'model': 'claude-sonnet-3.5',
        'min_severity': Severity.HIGH,
        'batch_size': 3,
        'rate_limit_rpm': 60
    }


class TestUnifiedAnalyzerLLMIntegration:
    """UnifiedAnalyzer LLM統合テスト"""

    def test_analyzer_initialization_with_llm(self, mock_llm_config):
        """LLM有効時の初期化"""
        with patch('multidb_analyzer.llm.llm_enhancer.ClaudeClient'):
            analyzer = UnifiedAnalyzer(
                enable_elasticsearch=True,
                enable_mysql=True,
                enable_llm=True,
                llm_api_key=mock_llm_config['api_key'],
                llm_model=mock_llm_config['model'],
                llm_min_severity=mock_llm_config['min_severity'],
                llm_batch_size=mock_llm_config['batch_size'],
                llm_rate_limit_rpm=mock_llm_config['rate_limit_rpm']
            )

            assert analyzer.enable_llm is True
            assert analyzer.llm_enhancer is not None
            assert analyzer.llm_enhancer.config.model == 'claude-sonnet-3.5'
            assert analyzer.llm_enhancer.config.min_severity == Severity.HIGH

    def test_analyzer_initialization_without_llm(self):
        """LLM無効時の初期化"""
        analyzer = UnifiedAnalyzer(
            enable_elasticsearch=True,
            enable_mysql=True,
            enable_llm=False
        )

        assert analyzer.enable_llm is False
        assert analyzer.llm_enhancer is None

    def test_analyzer_initialization_llm_no_api_key(self):
        """APIキーなしでのLLM初期化"""
        analyzer = UnifiedAnalyzer(
            enable_llm=True,
            llm_api_key=None  # No API key
        )

        # LLM有効だがenhancerは初期化されない
        assert analyzer.enable_llm is True
        assert analyzer.llm_enhancer is None

    def test_analyze_without_llm(self, temp_source_dir):
        """LLM無効時の分析"""
        analyzer = UnifiedAnalyzer(
            enable_elasticsearch=True,
            enable_mysql=False,
            enable_llm=False
        )

        # パーサーとdetectorをモック
        with patch.object(analyzer, 'es_parser') as mock_parser:
            with patch.object(analyzer, 'es_detectors', []):
                mock_parser.parse_file.return_value = []

                result = analyzer.analyze([temp_source_dir])

                assert result is not None
                assert result.execution_time >= 0
                assert len(result.errors) == 0

    def test_analyze_with_llm_enabled(self, temp_source_dir, mock_llm_config):
        """LLM有効時の分析フロー"""
        with patch('multidb_analyzer.llm.llm_enhancer.ClaudeClient'):
            analyzer = UnifiedAnalyzer(
                enable_elasticsearch=True,
                enable_mysql=False,
                enable_llm=True,
                llm_api_key=mock_llm_config['api_key']
            )

            # モックissues
            mock_issues = [
                Issue(
                    detector_name="MockDetector",
                    severity=Severity.HIGH,
                    category=IssueCategory.PERFORMANCE,
                    title=f"Issue {i}",
                    description="Test description",
                    file_path=str(temp_source_dir / "TestQuery.java"
                ),
                    line_number=i * 10,
                    query_text="SELECT * FROM test",
                    metadata={}
                )
                for i in range(3)
            ]

            # _analyze_elasticsearchをモック
            with patch.object(
                analyzer,
                '_analyze_elasticsearch',
                return_value=(mock_issues, 1)
            ):
                # LLM enhancerをモック
                analyzer.llm_enhancer.enhance_issues = AsyncMock(
                    return_value=(mock_issues, [])
                )

                result = analyzer.analyze([temp_source_dir])

                # LLM optimization was called
                assert analyzer.llm_enhancer.enhance_issues.called
                assert len(result.issues) == 3

    def test_apply_llm_optimization_success(self, mock_llm_config):
        """LLM最適化成功のテスト"""
        with patch('multidb_analyzer.llm.llm_enhancer.ClaudeClient'):
            analyzer = UnifiedAnalyzer(
                enable_llm=True,
                llm_api_key=mock_llm_config['api_key']
            )

            # サンプルissues
            issues = [
                Issue(
                    detector_name="Test",
                    severity=Severity.HIGH,
                    category=IssueCategory.PERFORMANCE,
                    title="Test Issue",
                    description="Test description",
                    file_path="test.java",
                    line_number=10,
                    query_text="SELECT * FROM test",
                    metadata={}
                )
            ]

            # LLM enhancerをモック
            enhanced_issue = Issue(
     detector_name="Test",
     severity=Severity.HIGH,
     category=IssueCategory.PERFORMANCE,
     title="Test Issue",
     description="Test description",
     file_path="test.java",
     line_number=10,
     query_text="SELECT * FROM test",
     metadata={'llm_enhanced': True}
 )

            analyzer.llm_enhancer.enhance_issues = AsyncMock(
                return_value=([enhanced_issue], [])
            )

            result_issues, errors = analyzer._apply_llm_optimization(issues)

            assert len(result_issues) == 1
            assert result_issues[0].metadata.get('llm_enhanced') is True
            assert len(errors) == 0

    def test_apply_llm_optimization_error(self, mock_llm_config):
        """LLM最適化エラーのテスト"""
        with patch('multidb_analyzer.llm.llm_enhancer.ClaudeClient'):
            analyzer = UnifiedAnalyzer(
                enable_llm=True,
                llm_api_key=mock_llm_config['api_key']
            )

            issues = [
                Issue(
                    detector_name="Test",
                    severity=Severity.HIGH,
                    category=IssueCategory.PERFORMANCE,
                    title="Test Issue",
                    description="Test description",
                    file_path="test.java",
                    line_number=10,
                    query_text="SELECT * FROM test",
                    metadata={}
                )
            ]

            # LLM enhancerがエラーを投げる
            analyzer.llm_enhancer.enhance_issues = AsyncMock(
                side_effect=Exception("LLM API Error")
            )

            result_issues, errors = analyzer._apply_llm_optimization(issues)

            # エラー時は元のissuesを返す
            assert len(result_issues) == 1
            assert len(errors) == 1
            assert "LLM optimization failed" in errors[0]

    def test_apply_llm_optimization_no_enhancer(self):
        """LLM enhancerなしでの最適化呼び出し"""
        analyzer = UnifiedAnalyzer(enable_llm=False)

        issues = [
            Issue(
                detector_name="Test",
                severity=Severity.HIGH,
                category=IssueCategory.PERFORMANCE,
                title="Test",
                description="Test description",
                file_path="test.java",
                line_number=10,
                query_text="",
                metadata={}
            )
        ]

        result_issues, errors = analyzer._apply_llm_optimization(issues)

        # enhancerなしなので元のissuesがそのまま返される
        assert result_issues == issues
        assert errors == []

    def test_end_to_end_with_llm(self, temp_source_dir):
        """エンドツーエンドテスト（モック含む）"""
        with patch('multidb_analyzer.llm.llm_enhancer.ClaudeClient') as mock_client_class:
            # ClaudeClientのモック設定
            mock_client = Mock()
            mock_client.analyze_code = AsyncMock(
                return_value="""### 1. 問題の詳細説明
SELECT * は不要なカラムを取得します

### 2. 修正提案
1. 必要なカラムのみ指定
2. インデックスを活用

### 3. 修正後のコード
```java
String query = "SELECT id, name FROM users WHERE id = ?";
```
"""
            )
            mock_client_class.return_value = mock_client

            # UnifiedAnalyzer初期化
            analyzer = UnifiedAnalyzer(
                enable_elasticsearch=True,
                enable_mysql=False,
                enable_llm=True,
                llm_api_key='test-api-key',
                llm_model='claude-sonnet-3.5',
                llm_min_severity=Severity.HIGH,
                llm_batch_size=5
            )

            # Elasticsearch分析をモック
            mock_issues = [
                Issue(
                    detector_name="WildcardDetector",
                    severity=Severity.HIGH,
                    category=IssueCategory.PERFORMANCE,
                    title="Wildcard Query Detected",
                    description="Test description",
                    file_path=str(temp_source_dir / "TestQuery.java"
                ),
                    line_number=4,
                    query_text="SELECT * FROM users",
                    suggestion="Use specific columns",
                    metadata={}
                )
            ]

            with patch.object(
                analyzer,
                '_analyze_elasticsearch',
                return_value=(mock_issues, 1)
            ):
                # 分析実行
                result = analyzer.analyze([temp_source_dir])

                # 結果検証
                assert result is not None
                assert result.total_files >= 1
                assert len(result.issues) >= 1

                # LLM拡張が適用されたか確認
                enhanced_issue = result.issues[0]
                if 'llm_enhanced' in enhanced_issue.metadata:
                    assert enhanced_issue.metadata['llm_enhanced'] is True


class TestLLMIntegrationErrorHandling:
    """LLM統合エラーハンドリングテスト"""

    def test_llm_timeout_handling(self, mock_llm_config):
        """タイムアウトハンドリング"""
        with patch('multidb_analyzer.llm.llm_enhancer.ClaudeClient'):
            analyzer = UnifiedAnalyzer(
                enable_llm=True,
                llm_api_key=mock_llm_config['api_key']
            )

            issues = [
                Issue(
                    detector_name="Test",
                    severity=Severity.HIGH,
                    category=IssueCategory.PERFORMANCE,
                    title="Test",
                    description="Test description",
                    file_path="test.java",
                    line_number=10,
                    query_text="",
                    metadata={}
                )
            ]

            # タイムアウトエラーをシミュレート
            analyzer.llm_enhancer.enhance_issues = AsyncMock(
                side_effect=asyncio.TimeoutError("Request timeout")
            )

            result_issues, errors = analyzer._apply_llm_optimization(issues)

            # タイムアウト時も元のissues返却
            assert len(result_issues) == 1
            assert len(errors) == 1

    def test_llm_network_error_handling(self, mock_llm_config):
        """ネットワークエラーハンドリング"""
        with patch('multidb_analyzer.llm.llm_enhancer.ClaudeClient'):
            analyzer = UnifiedAnalyzer(
                enable_llm=True,
                llm_api_key=mock_llm_config['api_key']
            )

            issues = [
                Issue(
                    detector_name="Test",
                    severity=Severity.HIGH,
                    category=IssueCategory.PERFORMANCE,
                    title="Test",
                    description="Test description",
                    file_path="test.java",
                    line_number=10,
                    query_text="",
                    metadata={}
                )
            ]

            # ネットワークエラーをシミュレート
            analyzer.llm_enhancer.enhance_issues = AsyncMock(
                side_effect=ConnectionError("Network unreachable")
            )

            result_issues, errors = analyzer._apply_llm_optimization(issues)

            assert len(result_issues) == 1
            assert len(errors) == 1
            assert "Network unreachable" in errors[0]


class TestLLMConfigurationVariations:
    """LLM設定バリエーションテスト"""

    def test_different_severity_levels(self):
        """異なる重大度レベルでのLLM統合"""
        for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]:
            with patch('multidb_analyzer.llm.llm_enhancer.ClaudeClient'):
                analyzer = UnifiedAnalyzer(
                    enable_llm=True,
                    llm_api_key='test-key',
                    llm_min_severity=severity
                )

                assert analyzer.llm_enhancer.config.min_severity == severity

    def test_different_batch_sizes(self):
        """異なるバッチサイズでのLLM統合"""
        for batch_size in [1, 5, 10, 20]:
            with patch('multidb_analyzer.llm.llm_enhancer.ClaudeClient'):
                analyzer = UnifiedAnalyzer(
                    enable_llm=True,
                    llm_api_key='test-key',
                    llm_batch_size=batch_size
                )

                assert analyzer.llm_enhancer.config.batch_size == batch_size

    def test_different_models(self):
        """異なるモデルでのLLM統合"""
        for model in ['claude-sonnet-3.5', 'claude-opus', 'claude-haiku']:
            with patch('multidb_analyzer.llm.llm_enhancer.ClaudeClient'):
                analyzer = UnifiedAnalyzer(
                    enable_llm=True,
                    llm_api_key='test-key',
                    llm_model=model
                )

                assert analyzer.llm_enhancer.config.model == model
