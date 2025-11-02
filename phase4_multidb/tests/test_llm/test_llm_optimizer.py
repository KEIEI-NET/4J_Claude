"""
Tests for LLM Optimizer
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from multidb_analyzer.llm.llm_optimizer import LLMOptimizer, OptimizationResult
from multidb_analyzer.core.base_detector import Issue, Severity, IssueCategory


class TestOptimizationResult:
    """OptimizationResultクラスのテスト"""

    def test_optimization_result_creation(self):
        """OptimizationResultの作成テスト"""
        issue = Mock(
            title="Test Issue",
            severity=Severity.HIGH,
            file_path="test.java",
            line_number=10
        )

        result = OptimizationResult(
            issue=issue,
            root_cause="Root cause explanation",
            performance_impact="50% improvement",
            optimized_code="optimized code",
            implementation_steps=["Step 1", "Step 2"],
            testing_strategy="Unit tests",
            trade_offs="None",
            confidence_score=0.9
        )

        assert result.issue == issue
        assert result.root_cause == "Root cause explanation"
        assert result.confidence_score == 0.9

    def test_optimization_result_to_dict(self):
        """to_dict()メソッドのテスト"""
        issue = Mock(
            title="Test Issue",
            severity=Severity.HIGH,
            file_path="test.java",
            line_number=10
        )

        result = OptimizationResult(
            issue=issue,
            root_cause="Root cause",
            performance_impact="Impact",
            optimized_code="code",
            implementation_steps=["Step 1"],
            testing_strategy="Testing",
            trade_offs="Trade-offs",
            confidence_score=0.8
        )

        result_dict = result.to_dict()

        assert 'issue' in result_dict
        assert result_dict['root_cause'] == "Root cause"
        assert result_dict['confidence_score'] == 0.8


class TestLLMOptimizer:
    """LLMOptimizerクラスのテスト"""

    @pytest.fixture
    def optimizer(self):
        """Optimizerインスタンスを作成"""
        with patch('multidb_analyzer.llm.llm_optimizer.ClaudeClient'):
            return LLMOptimizer(api_key="test-key")

    @pytest.fixture
    def sample_issue(self):
        """サンプルIssueを作成"""
        return Issue(
            detector_name="WildcardDetector",
            severity=Severity.CRITICAL,
            category=IssueCategory.PERFORMANCE,
            title="Leading Wildcard Query",
            description="Query uses leading wildcard",
            file_path="SearchService.java",
            line_number=10,
            query_text='wildcardQuery("name", "*smith")',
            suggestion="Use prefix query instead"
        )

    def test_optimizer_initialization(self, optimizer):
        """Optimizerの初期化テスト"""
        assert optimizer.temperature == 0.3
        assert optimizer.max_tokens == 4096

    def test_parse_optimization_response_valid_json(self, optimizer):
        """JSONレスポンス解析テスト（正常系）"""
        response = '''
Some text before
```json
{
  "root_cause": "Leading wildcard forces full index scan",
  "performance_impact": "Query time reduced by 80%",
  "optimized_code": "prefixQuery(\\"name\\", \\"smith\\")",
  "implementation_steps": ["Replace wildcardQuery", "Test performance"],
  "testing_strategy": "Run performance tests",
  "trade_offs": "Limited to prefix matching",
  "confidence_score": 0.95
}
```
Some text after
'''
        result = optimizer._parse_optimization_response(response)

        assert result['root_cause'] == "Leading wildcard forces full index scan"
        assert result['confidence_score'] == 0.95
        assert len(result['implementation_steps']) == 2

    def test_parse_optimization_response_invalid_json(self, optimizer):
        """JSONレスポンス解析テスト（不正なJSON）"""
        response = "This is not a valid JSON response"
        result = optimizer._parse_optimization_response(response)

        assert 'raw_response' in result
        assert result['raw_response'] == response

    def test_extract_code_block(self, optimizer):
        """コードブロック抽出テスト"""
        response = '''
Here is the optimized code:

```java
QueryBuilders.prefixQuery("name", "smith")
```

That's the solution.
'''
        code = optimizer._extract_code_block(response, "java")

        assert code == 'QueryBuilders.prefixQuery("name", "smith")'

    def test_extract_code_block_no_marker(self, optimizer):
        """コードブロックマーカーがない場合のテスト"""
        response = "Just plain text without code blocks"
        code = optimizer._extract_code_block(response, "java")

        assert code == response.strip()

    def test_calculate_simple_priority(self, optimizer):
        """シンプルな優先度計算テスト"""
        critical_issue = Mock(severity=Mock(value="CRITICAL"))
        high_issue = Mock(severity=Mock(value="HIGH"))
        low_issue = Mock(severity=Mock(value="LOW"))

        assert optimizer._calculate_simple_priority(critical_issue) == 10.0
        assert optimizer._calculate_simple_priority(high_issue) == 7.5
        assert optimizer._calculate_simple_priority(low_issue) == 2.5

    @patch('multidb_analyzer.llm.llm_optimizer.ClaudeClient')
    def test_optimize_issue_success(self, mock_client_class, sample_issue):
        """問題最適化の成功テスト"""
        # モックレスポンスを設定
        mock_response = json.dumps({
            "root_cause": "Leading wildcard issue",
            "performance_impact": "80% improvement",
            "optimized_code": "prefixQuery code",
            "implementation_steps": ["Step 1", "Step 2"],
            "testing_strategy": "Unit tests",
            "trade_offs": "None",
            "confidence_score": 0.9
        })

        mock_client = Mock()
        mock_client.generate.return_value = mock_response
        mock_client_class.return_value = mock_client

        optimizer = LLMOptimizer(api_key="test-key")
        result = optimizer.optimize_issue(
            issue=sample_issue,
            code='wildcardQuery("name", "*smith")',
            language="java"
        )

        assert isinstance(result, OptimizationResult)
        assert result.root_cause == "Leading wildcard issue"
        assert result.confidence_score == 0.9

    @patch('multidb_analyzer.llm.llm_optimizer.ClaudeClient')
    def test_optimize_issue_api_failure(self, mock_client_class, sample_issue):
        """API失敗時のフォールバックテスト"""
        mock_client = Mock()
        mock_client.generate.side_effect = Exception("API Error")
        mock_client_class.return_value = mock_client

        optimizer = LLMOptimizer(api_key="test-key")
        result = optimizer.optimize_issue(
            issue=sample_issue,
            code='wildcardQuery("name", "*smith")',
            language="java"
        )

        # フォールバック結果を返すことを確認
        assert isinstance(result, OptimizationResult)
        assert result.root_cause == "LLM analysis failed"
        assert result.confidence_score == 0.0

    @patch('multidb_analyzer.llm.llm_optimizer.ClaudeClient')
    def test_optimize_batch(self, mock_client_class, sample_issue):
        """バッチ最適化のテスト"""
        mock_response = json.dumps({
            "root_cause": "Issue",
            "performance_impact": "Good",
            "optimized_code": "code",
            "implementation_steps": [],
            "testing_strategy": "tests",
            "trade_offs": "none",
            "confidence_score": 0.8
        })

        mock_client = Mock()
        mock_client.generate.return_value = mock_response
        mock_client_class.return_value = mock_client

        optimizer = LLMOptimizer(api_key="test-key")
        issues = [sample_issue, sample_issue]
        code_snippets = {
            "SearchService.java:10": 'wildcardQuery("name", "*smith")'
        }

        results = optimizer.optimize_batch(
            issues=issues,
            code_snippets=code_snippets
        )

        assert len(results) == 2
        assert all(isinstance(r, OptimizationResult) for r in results)

    @patch('multidb_analyzer.llm.llm_optimizer.ClaudeClient')
    def test_prioritize_issues_success(self, mock_client_class, sample_issue):
        """問題優先度付けの成功テスト"""
        mock_response = json.dumps({
            "prioritized_issues": [
                {
                    "issue_id": 0,
                    "priority_score": 9.5,
                    "recommended_order": 1
                }
            ],
            "quick_wins": ["Issue 0"],
            "high_risk_high_reward": [],
            "technical_debt": []
        })

        mock_client = Mock()
        mock_client.generate.return_value = mock_response
        mock_client_class.return_value = mock_client

        optimizer = LLMOptimizer(api_key="test-key")
        result = optimizer.prioritize_issues([sample_issue])

        assert 'prioritized_issues' in result
        assert len(result['prioritized_issues']) == 1

    @patch('multidb_analyzer.llm.llm_optimizer.ClaudeClient')
    def test_prioritize_issues_fallback(self, mock_client_class, sample_issue):
        """優先度付け失敗時のフォールバックテスト"""
        mock_client = Mock()
        mock_client.generate.side_effect = Exception("API Error")
        mock_client_class.return_value = mock_client

        optimizer = LLMOptimizer(api_key="test-key")
        result = optimizer.prioritize_issues([sample_issue, sample_issue])

        # フォールバックの優先度付けが行われることを確認
        assert 'prioritized_issues' in result
        assert len(result['prioritized_issues']) == 2

    @patch('multidb_analyzer.llm.llm_optimizer.ClaudeClient')
    def test_generate_auto_fix_success(self, mock_client_class, sample_issue):
        """自動修正生成の成功テスト"""
        mock_response = '''
```java
QueryBuilders.prefixQuery("name", "smith")
```
'''
        mock_client = Mock()
        mock_client.generate.return_value = mock_response
        mock_client_class.return_value = mock_client

        optimizer = LLMOptimizer(api_key="test-key")
        result = optimizer.generate_auto_fix(
            issue=sample_issue,
            code='wildcardQuery("name", "*smith")'
        )

        assert 'fixed_code' in result
        assert 'prefixQuery' in result['fixed_code']
        assert result['confidence'] > 0

    @patch('multidb_analyzer.llm.llm_optimizer.ClaudeClient')
    def test_get_usage_stats(self, mock_client_class):
        """使用統計取得のテスト"""
        mock_client = Mock()
        mock_client.get_usage_stats.return_value = {
            'total_requests': 5,
            'total_cost_usd': 0.05
        }
        mock_client_class.return_value = mock_client

        optimizer = LLMOptimizer(api_key="test-key")
        stats = optimizer.get_usage_stats()

        assert stats['total_requests'] == 5
        assert 'total_cost_usd' in stats
