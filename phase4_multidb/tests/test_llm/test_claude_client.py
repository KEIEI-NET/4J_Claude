"""
Tests for Claude API Client
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from multidb_analyzer.llm.claude_client import (
    ClaudeClient,
    ClaudeModel,
    APIUsage
)


class TestAPIUsage:
    """APIUsageクラスのテスト"""

    def test_api_usage_initialization(self):
        """APIUsageの初期化テスト"""
        usage = APIUsage()
        assert usage.total_requests == 0
        assert usage.total_tokens == 0
        assert usage.total_cost == 0.0
        assert usage.input_tokens == 0
        assert usage.output_tokens == 0
        assert len(usage.request_history) == 0

    def test_add_request_sonnet(self):
        """Sonnetモデルのリクエスト追加テスト"""
        usage = APIUsage()
        usage.add_request(
            input_tokens=1000,
            output_tokens=500,
            model=ClaudeModel.SONNET
        )

        assert usage.total_requests == 1
        assert usage.input_tokens == 1000
        assert usage.output_tokens == 500
        assert usage.total_tokens == 1500

        # コスト計算: (1000/1M * $3) + (500/1M * $15) = $0.0105
        assert abs(usage.total_cost - 0.0105) < 0.0001

    def test_add_request_haiku(self):
        """Haikuモデルのリクエスト追加テスト"""
        usage = APIUsage()
        usage.add_request(
            input_tokens=1000,
            output_tokens=500,
            model=ClaudeModel.HAIKU
        )

        # コスト計算: (1000/1M * $0.25) + (500/1M * $1.25) = $0.000875
        assert abs(usage.total_cost - 0.000875) < 0.0001

    def test_add_multiple_requests(self):
        """複数リクエストの追加テスト"""
        usage = APIUsage()

        usage.add_request(1000, 500, ClaudeModel.SONNET)
        usage.add_request(2000, 1000, ClaudeModel.SONNET)

        assert usage.total_requests == 2
        assert usage.input_tokens == 3000
        assert usage.output_tokens == 1500
        assert len(usage.request_history) == 2


class TestClaudeClient:
    """ClaudeClientクラスのテスト"""

    def test_initialization_with_api_key(self):
        """APIキー指定での初期化テスト"""
        client = ClaudeClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.model == ClaudeModel.SONNET
        assert client.max_retries == 3

    def test_initialization_without_api_key_raises_error(self):
        """APIキーなしの初期化でエラーテスト"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="API key not provided"):
                ClaudeClient()

    def test_initialization_with_env_variable(self):
        """環境変数からのAPIキー取得テスト"""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'env-key'}):
            client = ClaudeClient()
            assert client.api_key == 'env-key'

    @patch('anthropic.Anthropic')
    def test_client_lazy_initialization(self, mock_anthropic):
        """clientプロパティの遅延初期化テスト"""
        client_instance = ClaudeClient(api_key="test-key")

        # まだclientは初期化されていない
        assert client_instance._client is None

        # clientプロパティにアクセスして初期化
        _ = client_instance.client

        # Anthropicが呼ばれたことを確認
        mock_anthropic.assert_called_once_with(api_key="test-key")

    @patch('anthropic.Anthropic')
    def test_generate_success(self, mock_anthropic):
        """正常なテキスト生成テスト"""
        # モックレスポンスを設定
        mock_response = Mock()
        mock_response.content = [Mock(text="Generated response")]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        client = ClaudeClient(api_key="test-key")
        result = client.generate(prompt="Test prompt")

        assert result == "Generated response"
        assert client.usage.total_requests == 1
        assert client.usage.input_tokens == 100
        assert client.usage.output_tokens == 50

    @patch('anthropic.Anthropic')
    def test_generate_with_system_prompt(self, mock_anthropic):
        """システムプロンプト付きの生成テスト"""
        mock_response = Mock()
        mock_response.content = [Mock(text="Response")]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        client = ClaudeClient(api_key="test-key")
        result = client.generate(
            prompt="User prompt",
            system_prompt="System instructions"
        )

        assert result == "Response"

        # システムプロンプトが渡されたことを確認
        call_kwargs = mock_client.messages.create.call_args[1]
        assert 'system' in call_kwargs
        assert call_kwargs['system'] == "System instructions"

    @patch('anthropic.Anthropic')
    @patch('time.sleep')  # sleepをモック
    def test_generate_with_retry(self, mock_sleep, mock_anthropic):
        """リトライ機能のテスト"""
        mock_client = Mock()

        # 最初の2回は失敗、3回目は成功
        mock_response = Mock()
        mock_response.content = [Mock(text="Success")]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        mock_client.messages.create.side_effect = [
            Exception("API Error 1"),
            Exception("API Error 2"),
            mock_response
        ]
        mock_anthropic.return_value = mock_client

        client = ClaudeClient(api_key="test-key", max_retries=3)
        result = client.generate(prompt="Test")

        assert result == "Success"
        assert mock_client.messages.create.call_count == 3
        assert mock_sleep.call_count == 2  # 2回のリトライ間の待機

    @patch('anthropic.Anthropic')
    def test_generate_batch(self, mock_anthropic):
        """バッチ生成のテスト"""
        mock_response = Mock()
        mock_response.content = [Mock(text="Response")]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        client = ClaudeClient(api_key="test-key")
        prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]

        with patch('time.sleep'):  # 待機時間をスキップ
            results = client.generate_batch(prompts, delay_between_requests=0.1)

        assert len(results) == 3
        assert all(r == "Response" for r in results)
        assert client.usage.total_requests == 3

    def test_get_usage_stats(self):
        """使用統計取得のテスト"""
        client = ClaudeClient(api_key="test-key")
        client.usage.add_request(1000, 500, ClaudeModel.SONNET)
        client.usage.add_request(2000, 1000, ClaudeModel.SONNET)

        stats = client.get_usage_stats()

        assert stats['total_requests'] == 2
        assert stats['total_tokens'] == 4500
        assert stats['input_tokens'] == 3000
        assert stats['output_tokens'] == 1500
        assert 'total_cost_usd' in stats
        assert 'average_cost_per_request' in stats

    def test_reset_usage_stats(self):
        """使用統計リセットのテスト"""
        client = ClaudeClient(api_key="test-key")
        client.usage.add_request(1000, 500, ClaudeModel.SONNET)

        assert client.usage.total_requests == 1

        client.reset_usage_stats()

        assert client.usage.total_requests == 0
        assert client.usage.total_tokens == 0
        assert client.usage.total_cost == 0.0
