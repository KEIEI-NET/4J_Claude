"""
LLMコンポーネントのユニットテスト
"""
import json
import pytest
from unittest.mock import Mock, MagicMock, patch
from anthropic import APIError, RateLimitError

from cassandra_analyzer.llm import AnthropicClient, LLMAnalyzer
from cassandra_analyzer.models import CassandraCall, Issue


class TestAnthropicClient:
    """AnthropicClientのテストクラス"""

    @pytest.fixture
    def mock_anthropic(self):
        """AnthropicクライアントのMock"""
        with patch("cassandra_analyzer.llm.anthropic_client.Anthropic") as mock:
            yield mock

    @pytest.fixture
    def client(self, mock_anthropic):
        """テスト用クライアント（環境変数不要）"""
        return AnthropicClient(api_key="test_api_key")

    def test_initialization_with_api_key(self, mock_anthropic):
        """APIキーを指定して初期化"""
        client = AnthropicClient(api_key="test_key_123")
        assert client.api_key == "test_key_123"
        assert client.model == "claude-3-5-sonnet-20241022"

    def test_initialization_without_api_key_raises_error(self, mock_anthropic):
        """APIキーなしで初期化するとエラー"""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                AnthropicClient()

    def test_analyze_code_success(self, client, mock_anthropic):
        """正常にコード分析が実行される"""
        # Mockレスポンスの設定
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Analysis result")]
        client.client.messages.create = Mock(return_value=mock_response)

        # 実行
        result = client.analyze_code(
            code="SELECT * FROM users",
            prompt="Analyze this code"
        )

        # 検証
        assert result == "Analysis result"
        client.client.messages.create.assert_called_once()

    def test_analyze_code_empty_code_raises_error(self, client):
        """空のコードでエラー"""
        with pytest.raises(ValueError, match="Code cannot be empty"):
            client.analyze_code(code="", prompt="Test")

    def test_analyze_code_empty_prompt_raises_error(self, client):
        """空のプロンプトでエラー"""
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            client.analyze_code(code="SELECT * FROM users", prompt="")

    def test_analyze_code_rate_limit_retry(self, client, mock_anthropic):
        """レート制限エラーで再試行"""
        # 1回目: RateLimitError、2回目: 成功
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Success")]

        # RateLimitErrorのモック作成
        mock_rate_limit_error = RateLimitError(
            message="Rate limited",
            response=MagicMock(status_code=429),
            body={"error": {"message": "Rate limited"}}
        )

        client.client.messages.create = Mock(
            side_effect=[
                mock_rate_limit_error,
                mock_response,
            ]
        )

        # 実行（リトライ成功）
        result = client.analyze_code(
            code="SELECT * FROM users",
            prompt="Test",
        )

        assert result == "Success"
        assert client.client.messages.create.call_count == 2

    def test_analyze_code_max_retries_exceeded(self, client):
        """最大リトライ回数を超えたらエラー"""
        mock_rate_limit_error = RateLimitError(
            message="Rate limited",
            response=MagicMock(status_code=429),
            body={"error": {"message": "Rate limited"}}
        )

        client.client.messages.create = Mock(
            side_effect=mock_rate_limit_error
        )

        with pytest.raises(RateLimitError):
            client.analyze_code(
                code="SELECT * FROM users",
                prompt="Test",
            )

        assert client.client.messages.create.call_count == client.max_retries

    def test_generate_recommendation(self, client, mock_anthropic):
        """推奨事項の生成"""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Fix by doing X, Y, Z")]
        client.client.messages.create = Mock(return_value=mock_response)

        result = client.generate_recommendation(
            issue_description="ALLOW FILTERING detected",
            code_context="SELECT * FROM users WHERE email = ? ALLOW FILTERING",
        )

        assert "Fix by doing X, Y, Z" in result

    def test_estimate_cost(self, client):
        """コスト概算"""
        # Claude 3.5 Sonnet: Input $3/1M, Output $15/1M
        cost = client.estimate_cost(input_tokens=1000, output_tokens=500)

        expected_cost = (1000 * 3.0 / 1_000_000) + (500 * 15.0 / 1_000_000)
        assert abs(cost - expected_cost) < 0.0001

    def test_get_model_info(self, client):
        """モデル情報の取得"""
        info = client.get_model_info()

        assert info["model"] == "claude-3-5-sonnet-20241022"
        assert info["max_retries"] == 3
        assert "retry_delay" in info

    def test_analyze_code_api_connection_error_retry(self, client):
        """接続エラーで再試行"""
        from anthropic import APIConnectionError
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Success after connection error")]

        mock_connection_error = APIConnectionError(
            message="Connection failed",
            request=MagicMock()
        )

        client.client.messages.create = Mock(
            side_effect=[
                mock_connection_error,
                mock_response,
            ]
        )

        result = client.analyze_code(
            code="SELECT * FROM users",
            prompt="Test",
        )

        assert result == "Success after connection error"
        assert client.client.messages.create.call_count == 2

    def test_analyze_code_batch_success(self, client):
        """バッチ分析が成功"""
        mock_response1 = MagicMock()
        mock_response1.content = [MagicMock(text="Analysis 1")]
        mock_response2 = MagicMock()
        mock_response2.content = [MagicMock(text="Analysis 2")]

        client.client.messages.create = Mock(
            side_effect=[mock_response1, mock_response2]
        )

        snippets = [
            {"id": "snippet1", "code": "SELECT * FROM users"},
            {"id": "snippet2", "code": "SELECT * FROM orders"},
        ]

        results = client.analyze_code_batch(
            code_snippets=snippets,
            prompt="Analyze these queries"
        )

        assert len(results) == 2
        assert results[0] == "Analysis 1"
        assert results[1] == "Analysis 2"

    def test_analyze_code_batch_empty_code(self, client):
        """バッチ分析で空のコード"""
        snippets = [
            {"id": "snippet1", "code": "SELECT * FROM users"},
            {"id": "snippet2", "code": ""},  # Empty code
        ]

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Analysis 1")]
        client.client.messages.create = Mock(return_value=mock_response)

        results = client.analyze_code_batch(
            code_snippets=snippets,
            prompt="Analyze"
        )

        assert len(results) == 2
        assert results[0] == "Analysis 1"
        assert results[1] == ""  # Empty result for empty code

    def test_analyze_code_connection_error_max_retries(self, client):
        """接続エラーで最大リトライ回数を超える"""
        from anthropic import APIConnectionError

        mock_connection_error = APIConnectionError(
            message="Connection failed",
            request=MagicMock()
        )

        client.client.messages.create = Mock(side_effect=mock_connection_error)

        with pytest.raises(APIConnectionError):
            client.analyze_code(
                code="SELECT * FROM users",
                prompt="Test",
            )

        # max_retries = 3回試行される
        assert client.client.messages.create.call_count == 3

    def test_analyze_code_generic_api_error(self, client):
        """一般的なAPIError（リトライなし）"""
        from anthropic import APIError

        mock_api_error = APIError(
            message="API Error",
            request=MagicMock(),
            body={"error": {"message": "Generic error"}}
        )

        client.client.messages.create = Mock(side_effect=mock_api_error)

        with pytest.raises(APIError):
            client.analyze_code(
                code="SELECT * FROM users",
                prompt="Test",
            )

        # 一般的なAPIErrorは即座に再スローされるので1回のみ
        assert client.client.messages.create.call_count == 1

    def test_analyze_code_batch_with_api_error(self, client):
        """バッチ分析中のAPIError処理"""
        from anthropic import APIError

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Analysis 1")]

        mock_api_error = APIError(
            message="API Error",
            request=MagicMock(),
            body={"error": {"message": "Error"}}
        )

        client.client.messages.create = Mock(
            side_effect=[mock_response, mock_api_error, mock_response]
        )

        snippets = [
            {"id": "snippet1", "code": "SELECT * FROM users"},
            {"id": "snippet2", "code": "SELECT * FROM orders"},
            {"id": "snippet3", "code": "SELECT * FROM products"},
        ]

        results = client.analyze_code_batch(
            code_snippets=snippets,
            prompt="Analyze"
        )

        # エラーが発生したスニペットは空文字列
        assert len(results) == 3
        assert results[0] == "Analysis 1"
        assert results[1] == ""  # Error case
        assert results[2] == "Analysis 1"


class TestLLMAnalyzer:
    """LLMAnalyzerのテストクラス"""

    @pytest.fixture
    def mock_client(self):
        """AnthropicClientのMock"""
        client = Mock(spec=AnthropicClient)
        return client

    @pytest.fixture
    def analyzer(self, mock_client):
        """テスト用Analyzer"""
        return LLMAnalyzer(client=mock_client)

    def test_initialization_with_custom_prompts_dir(self, mock_client, tmp_path):
        """カスタムプロンプトディレクトリでの初期化"""
        prompts_dir = tmp_path / "custom_prompts"
        prompts_dir.mkdir()

        analyzer = LLMAnalyzer(client=mock_client, prompts_dir=prompts_dir)

        assert analyzer.prompts_dir == prompts_dir
        assert "code_analysis" in analyzer.prompts

    def test_initialization(self, analyzer):
        """初期化"""
        assert analyzer.client is not None
        assert "code_analysis" in analyzer.prompts
        assert "issue_detection" in analyzer.prompts
        assert "recommendation" in analyzer.prompts

    def test_analyze_code_file_success(self, analyzer, mock_client):
        """ファイル分析が成功"""
        # JSONレスポンスのMock
        json_response = json.dumps({
            "issues": [
                {
                    "type": "ALLOW_FILTERING",
                    "severity": "high",
                    "line": 10,
                    "explanation": "ALLOW FILTERING causes full table scan",
                    "cql": "SELECT * FROM users WHERE email = ? ALLOW FILTERING",
                    "recommendation": "Create a materialized view"
                }
            ]
        })

        mock_client.analyze_code.return_value = json_response

        # 実行
        issues = analyzer.analyze_code_file(
            file_path="test.java",
            code="public class Test { ... }"
        )

        # 検証
        assert len(issues) == 1
        assert issues[0].issue_type == "ALLOW_FILTERING"
        assert issues[0].severity == "high"
        assert issues[0].line_number == 10
        assert issues[0].detector_name == "LLMAnalyzer"

    def test_analyze_code_file_with_markdown_json(self, analyzer, mock_client):
        """マークダウン形式のJSONレスポンス"""
        markdown_response = """Here's the analysis:

```json
{
  "issues": [
    {
      "type": "NO_PARTITION_KEY",
      "severity": "critical",
      "line": 20,
      "explanation": "Missing partition key",
      "cql": "SELECT * FROM orders WHERE date > ?",
      "recommendation": "Add partition key to WHERE clause"
    }
  ]
}
```

That's all!"""

        mock_client.analyze_code.return_value = markdown_response

        issues = analyzer.analyze_code_file(
            file_path="test.java",
            code="public class Test { ... }"
        )

        assert len(issues) == 1
        assert issues[0].issue_type == "NO_PARTITION_KEY"
        assert issues[0].severity == "critical"

    def test_analyze_code_file_with_plain_markdown(self, analyzer, mock_client):
        """プレーンマークダウン形式（```のみ）のJSONレスポンス"""
        markdown_response = """```
{
  "issues": [
    {
      "type": "ALLOW_FILTERING",
      "severity": "high",
      "line": 15,
      "explanation": "ALLOW FILTERING detected",
      "cql": "SELECT * FROM users WHERE email = ? ALLOW FILTERING",
      "recommendation": "Create secondary index"
    }
  ]
}
```"""

        mock_client.analyze_code.return_value = markdown_response

        issues = analyzer.analyze_code_file(
            file_path="test.java",
            code="public class Test { ... }"
        )

        assert len(issues) == 1
        assert issues[0].issue_type == "ALLOW_FILTERING"
        assert issues[0].severity == "high"

    def test_analyze_code_file_json_decode_error(self, analyzer, mock_client):
        """JSONパースエラー時の処理"""
        # 不正なJSON
        mock_client.analyze_code.return_value = """```json
{
  "issues": [
    {
      "type": "TEST"
      "missing_comma": true
    }
  ]
}
```"""

        issues = analyzer.analyze_code_file(
            file_path="test.java",
            code="public class Test { ... }"
        )

        # JSONパースエラーの場合は空のリストを返す
        assert len(issues) == 0

    def test_analyze_code_file_with_exception(self, analyzer, mock_client):
        """予期しない例外発生時の処理"""
        # analyze_code内で例外が発生するように設定
        mock_client.analyze_code.return_value = """```json
{
  "issues": [
    {
      "type": "TEST",
      "severity": "invalid_severity",
      "line": 10,
      "explanation": "Test",
      "cql": "SELECT * FROM test",
      "recommendation": "Fix it"
    }
  ]
}
```"""

        # Issueのバリデーションエラーを発生させるため、
        # severityを不正な値にしています
        issues = analyzer.analyze_code_file(
            file_path="test.java",
            code="public class Test { ... }"
        )

        # 例外が発生しても空のリストを返す
        assert len(issues) == 0

    def test_analyze_code_file_empty_response(self, analyzer, mock_client):
        """空のレスポンス"""
        mock_client.analyze_code.return_value = '{"issues": []}'

        issues = analyzer.analyze_code_file(
            file_path="test.java",
            code="public class Test { ... }"
        )

        assert len(issues) == 0

    def test_analyze_code_file_api_error(self, analyzer, mock_client):
        """APIエラー時は空リストを返す"""
        mock_client.analyze_code.side_effect = Exception("API Error")

        issues = analyzer.analyze_code_file(
            file_path="test.java",
            code="public class Test { ... }"
        )

        assert len(issues) == 0

    def test_analyze_cassandra_call(self, analyzer, mock_client):
        """Cassandra呼び出しの分析"""
        mock_client.analyze_code.return_value = "This query has performance issues"

        call = CassandraCall(
            method_name="execute",
            cql_text="SELECT * FROM users WHERE email = ? ALLOW FILTERING",
            line_number=10,
            is_prepared=False,
            consistency_level=None,
            file_path="test.java",
        )

        result = analyzer.analyze_cassandra_call(call)

        assert result is not None
        assert "performance issues" in result

    def test_analyze_cassandra_call_with_exception(self, analyzer, mock_client):
        """Cassandra呼び出し分析での例外処理"""
        # analyze_codeが例外を投げる
        mock_client.analyze_code.side_effect = Exception("API Error")

        call = CassandraCall(
            method_name="execute",
            cql_text="SELECT * FROM users",
            line_number=10,
            is_prepared=False,
            consistency_level=None,
            file_path="test.java",
        )

        result = analyzer.analyze_cassandra_call(call)

        # 例外が発生した場合はNoneを返す
        assert result is None

    def test_enhance_issue(self, analyzer, mock_client):
        """問題の強化（推奨事項の詳細化）"""
        mock_client.generate_recommendation.return_value = "Detailed recommendation: 1. Do X, 2. Do Y"

        issue = Issue(
            detector_name="TestDetector",
            issue_type="ALLOW_FILTERING",
            severity="high",
            file_path="test.java",
            line_number=10,
            message="ALLOW FILTERING detected",
            cql_text="SELECT * FROM users WHERE email = ? ALLOW FILTERING",
            recommendation="Fix it",
            evidence=[],
            confidence=0.8,
        )

        enhanced = analyzer.enhance_issue(issue)

        assert enhanced.recommendation == "Detailed recommendation: 1. Do X, 2. Do Y"
        assert enhanced.issue_type == issue.issue_type
        assert enhanced.severity == issue.severity

    def test_enhance_issue_api_error(self, analyzer, mock_client):
        """強化中のAPIエラーは元の問題を返す"""
        mock_client.generate_recommendation.side_effect = Exception("API Error")

        issue = Issue(
            detector_name="TestDetector",
            issue_type="TEST",
            severity="low",
            file_path="test.java",
            line_number=1,
            message="Test",
            cql_text="SELECT * FROM test",
            recommendation="Original",
            evidence=[],
            confidence=0.9,
        )

        enhanced = analyzer.enhance_issue(issue)

        # エラー時は元の問題がそのまま返される
        assert enhanced.recommendation == "Original"

    def test_batch_enhance_issues(self, analyzer, mock_client):
        """複数問題の一括強化"""
        mock_client.generate_recommendation.side_effect = [
            "Recommendation 1",
            "Recommendation 2",
        ]

        issues = [
            Issue(
                detector_name="TestDetector",
                issue_type="ISSUE1",
                severity="high",
                file_path="test.java",
                line_number=10,
                message="Issue 1",
                cql_text="SELECT * FROM table1",
                recommendation="Fix 1",
                evidence=[],
                confidence=0.9,
            ),
            Issue(
                detector_name="TestDetector",
                issue_type="ISSUE2",
                severity="medium",
                file_path="test.java",
                line_number=20,
                message="Issue 2",
                cql_text="SELECT * FROM table2",
                recommendation="Fix 2",
                evidence=[],
                confidence=0.8,
            ),
        ]

        enhanced_issues = analyzer.batch_enhance_issues(issues)

        assert len(enhanced_issues) == 2
        assert enhanced_issues[0].recommendation == "Recommendation 1"
        assert enhanced_issues[1].recommendation == "Recommendation 2"

    def test_get_context_aware_analysis(self, analyzer, mock_client):
        """コンテキストを考慮した分析"""
        mock_client.analyze_code.return_value = "Analysis with context"

        result = analyzer.get_context_aware_analysis(
            code="SELECT * FROM users",
            table_schema="CREATE TABLE users (id uuid PRIMARY KEY, email text)"
        )

        assert result["success"] is True
        assert "Analysis with context" in result["analysis"]

    def test_get_context_aware_analysis_error(self, analyzer, mock_client):
        """コンテキスト分析でのエラー"""
        mock_client.analyze_code.side_effect = Exception("API Error")

        result = analyzer.get_context_aware_analysis(
            code="SELECT * FROM users"
        )

        assert result["success"] is False
        assert "error" in result
