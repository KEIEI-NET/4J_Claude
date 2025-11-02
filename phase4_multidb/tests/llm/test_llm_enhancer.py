"""
Tests for LLM Enhancer

LLMEnhancerクラスの包括的テストスイート
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from multidb_analyzer.core.base_detector import Issue, Severity, IssueCategory
from multidb_analyzer.llm.llm_enhancer import (
    LLMEnhancer,
    LLMConfig,
    RateLimiter
)


@pytest.fixture
def mock_config():
    """モックLLM設定"""
    return LLMConfig(
        api_key="test-api-key",
        model="claude-sonnet-3.5",
        min_severity=Severity.HIGH,
        max_issues=10,
        batch_size=3,
        rate_limit_rpm=60,  # 1req/sec for faster tests
        max_retries=2,
        timeout=10.0,
        cache_enabled=True,
        cache_ttl=3600
    )


@pytest.fixture
def sample_issue():
    """サンプルIssue"""
    return Issue(
        detector_name="TestDetector",
        severity=Severity.HIGH,
        category=IssueCategory.PERFORMANCE,
        title="Test Issue",
        description="Test description",
        file_path="test.java",
        line_number=10,
        query_text="SELECT * FROM test",
        suggestion="Use specific columns",
        metadata={}
    )


@pytest.fixture
def sample_issues():
    """複数のサンプルIssue"""
    return [
        Issue(
            detector_name="TestDetector",
            severity=Severity.HIGH if i < 3 else Severity.MEDIUM,
            category=IssueCategory.PERFORMANCE,
            title=f"Issue {i}",
            description=f"Description {i}",
            file_path=f"test{i}.java",
            line_number=i * 10,
            query_text=f"SELECT * FROM table{i}",
            suggestion=f"Fix issue {i}",
            metadata={}
        )
        for i in range(5)
    ]


@pytest.fixture
def mock_enhancer(mock_config):
    """モックLLMEnhancer"""
    with patch('multidb_analyzer.llm.llm_enhancer.ClaudeClient'):
        enhancer = LLMEnhancer(mock_config)
        enhancer.client.analyze_code = AsyncMock(
            return_value="### 1. 問題の詳細説明\nTest description\n\n### 2. 修正提案\n1. Step 1\n2. Step 2"
        )
        return enhancer


class TestLLMConfig:
    """LLMConfig tests"""

    def test_default_config(self):
        """デフォルト設定のテスト"""
        config = LLMConfig(api_key="test-key")

        assert config.api_key == "test-key"
        assert config.model == "claude-sonnet-3.5"
        assert config.min_severity == Severity.HIGH
        assert config.max_issues == 50
        assert config.batch_size == 5
        assert config.rate_limit_rpm == 50
        assert config.max_retries == 3
        assert config.timeout == 30.0
        assert config.max_concurrent == 10
        assert config.cache_enabled is True
        assert config.cache_ttl == 3600

    def test_custom_config(self):
        """カスタム設定のテスト"""
        config = LLMConfig(
            api_key="custom-key",
            model="claude-opus",
            min_severity=Severity.CRITICAL,
            batch_size=10,
            rate_limit_rpm=100
        )

        assert config.api_key == "custom-key"
        assert config.model == "claude-opus"
        assert config.min_severity == Severity.CRITICAL
        assert config.batch_size == 10
        assert config.rate_limit_rpm == 100


class TestRateLimiter:
    """RateLimiter tests"""

    def test_rate_limiter_initialization(self):
        """初期化のテスト"""
        limiter = RateLimiter(rpm=60)

        assert limiter.rpm == 60
        assert limiter.interval == 1.0  # 60req/60sec = 1req/sec
        assert limiter.last_request == 0.0

    @pytest.mark.asyncio
    async def test_rate_limiter_wait(self):
        """待機機能のテスト"""
        limiter = RateLimiter(rpm=120)  # 0.5sec interval

        start_time = asyncio.get_event_loop().time()

        # 最初の呼び出しは即座に完了
        await limiter.wait()
        first_call_time = asyncio.get_event_loop().time() - start_time
        assert first_call_time < 0.1

        # 2回目の呼び出しは待機
        await limiter.wait()
        second_call_time = asyncio.get_event_loop().time() - start_time
        assert second_call_time >= 0.4  # ~0.5sec wait

    @pytest.mark.asyncio
    async def test_rate_limiter_multiple_calls(self):
        """複数回呼び出しのテスト"""
        limiter = RateLimiter(rpm=120)

        start_time = asyncio.get_event_loop().time()

        # 3回連続呼び出し
        for _ in range(3):
            await limiter.wait()

        elapsed = asyncio.get_event_loop().time() - start_time
        # 3 calls = 2 intervals = ~1.0sec
        assert 0.8 <= elapsed <= 1.2


class TestLLMEnhancer:
    """LLMEnhancer tests"""

    def test_initialization(self, mock_config):
        """初期化のテスト"""
        with patch('multidb_analyzer.llm.llm_enhancer.ClaudeClient'):
            enhancer = LLMEnhancer(mock_config)

            assert enhancer.config == mock_config
            assert enhancer.client is not None
            assert enhancer.parser is not None
            assert enhancer.prompt_builder is not None
            assert enhancer.rate_limiter is not None
            assert isinstance(enhancer._cache, dict)
            assert len(enhancer._cache) == 0

    def test_filter_by_severity(self, mock_enhancer, sample_issues):
        """重大度フィルタのテスト"""
        # HIGH以上（HIGH, CRITICAL）
        filtered = mock_enhancer._filter_by_severity(sample_issues, Severity.HIGH)
        assert len(filtered) == 3  # Only HIGH severity issues
        assert all(i.severity == Severity.HIGH for i in filtered)

        # MEDIUM以上（MEDIUM, HIGH, CRITICAL）
        filtered = mock_enhancer._filter_by_severity(sample_issues, Severity.MEDIUM)
        assert len(filtered) == 5  # All issues

        # CRITICAL以上
        critical_issue = Issue(
            detector_name="Test",
            severity=Severity.CRITICAL,
            category=IssueCategory.SECURITY,
            title="Critical",
            description="Critical issue",
            file_path="test.java",
            line_number=1,
            query_text="",
            metadata={}
        )
        test_issues = [critical_issue] + sample_issues
        filtered = mock_enhancer._filter_by_severity(test_issues, Severity.CRITICAL)
        assert len(filtered) == 1
        assert filtered[0].severity == Severity.CRITICAL

    def test_batch_issues(self, mock_enhancer, sample_issues):
        """バッチ分割のテスト"""
        batches = mock_enhancer._batch_issues(sample_issues)

        # batch_size=3 → 5 issues = [3, 2]
        assert len(batches) == 2
        assert len(batches[0]) == 3
        assert len(batches[1]) == 2

        # 全Issue含まれているか確認
        all_batched = [issue for batch in batches for issue in batch]
        assert len(all_batched) == len(sample_issues)

    def test_get_cache_key(self, mock_enhancer, sample_issue):
        """キャッシュキー生成のテスト"""
        key = mock_enhancer._get_cache_key(sample_issue)

        assert key == "test.java:10:TestDetector"
        assert isinstance(key, str)

    def test_get_context_code_file_not_found(self, mock_enhancer, sample_issue):
        """ファイルが存在しない場合のコンテキスト取得"""
        sample_issue.file_path = "nonexistent_file.java"

        context = mock_enhancer._get_context_code(sample_issue)
        assert context == ""

    @pytest.mark.asyncio
    async def test_enhance_issue_with_cache(self, mock_enhancer, sample_issue):
        """キャッシュ機能のテスト"""
        # モックレスポンス設定
        mock_enhancer.parser.parse_analysis = Mock(return_value=sample_issue)

        # 1回目の呼び出し
        result1 = await mock_enhancer.enhance_issue(sample_issue)
        assert mock_enhancer.client.analyze_code.call_count == 1

        # 2回目の呼び出し（キャッシュヒット）
        result2 = await mock_enhancer.enhance_issue(sample_issue)
        assert mock_enhancer.client.analyze_code.call_count == 1  # No additional call

        # 結果が同じ
        assert result1 == result2

    @pytest.mark.asyncio
    async def test_enhance_issue_cache_disabled(self, mock_config, sample_issue):
        """キャッシュ無効時のテスト"""
        mock_config.cache_enabled = False

        with patch('multidb_analyzer.llm.llm_enhancer.ClaudeClient'):
            enhancer = LLMEnhancer(mock_config)
            enhancer.client.analyze_code = AsyncMock(return_value="Response")
            enhancer.parser.parse_analysis = Mock(return_value=sample_issue)

            # 2回呼び出し
            await enhancer.enhance_issue(sample_issue)
            await enhancer.enhance_issue(sample_issue)

            # 両方とも実行
            assert enhancer.client.analyze_code.call_count == 2

    @pytest.mark.asyncio
    async def test_enhance_issue_with_error(self, mock_enhancer, sample_issue):
        """エラー時のフォールバック"""
        mock_enhancer.client.analyze_code = AsyncMock(side_effect=Exception("API Error"))

        result = await mock_enhancer.enhance_issue(sample_issue)

        # 元のIssueが返される
        assert result.file_path == sample_issue.file_path
        assert result.line_number == sample_issue.line_number

        # エラーメタデータ追加
        assert 'llm_error' in result.metadata
        assert "API Error" in result.metadata['llm_error']

    @pytest.mark.asyncio
    async def test_enhance_batch(self, mock_enhancer, sample_issues):
        """バッチ拡張のテスト"""
        batch = sample_issues[:3]

        mock_enhancer.parser.parse_batch_response = Mock(return_value=batch)

        result = await mock_enhancer._enhance_batch(batch)

        assert len(result) == 3
        assert mock_enhancer.client.analyze_code.call_count == 1

    @pytest.mark.asyncio
    async def test_enhance_batch_with_error(self, mock_enhancer, sample_issues):
        """バッチエラー時のフォールバック"""
        batch = sample_issues[:3]
        mock_enhancer.client.analyze_code = AsyncMock(side_effect=Exception("Batch Error"))

        result = await mock_enhancer._enhance_batch(batch)

        # 元のバッチが返される
        assert len(result) == 3

        # 各IssueにエラーメタデータLLM_error added
        for issue in result:
            assert 'llm_error' in issue.metadata

    @pytest.mark.asyncio
    async def test_enhance_issues_filtering(self, mock_enhancer, sample_issues):
        """enhance_issuesのフィルタリング"""
        mock_enhancer.parser.parse_batch_response = Mock(side_effect=lambda r, b: b)

        # HIGH以上のみ処理（最初の3つ）
        enhanced, errors = await mock_enhancer.enhance_issues(
            sample_issues,
            filter_severity=Severity.HIGH
        )

        # 3つがHIGH、2つがMEDIUM → 全て返されるが、HIGH only enhanced
        assert len(enhanced) == 5

    @pytest.mark.asyncio
    async def test_enhance_issues_max_limit(self, mock_config, sample_issues):
        """最大Issue数制限のテスト"""
        mock_config.max_issues = 2

        with patch('multidb_analyzer.llm.llm_enhancer.ClaudeClient'):
            enhancer = LLMEnhancer(mock_config)
            enhancer.client.analyze_code = AsyncMock(return_value="Response")
            enhancer.parser.parse_batch_response = Mock(side_effect=lambda r, b: b)

            enhanced, errors = await enhancer.enhance_issues(sample_issues)

            # max_issues=2制限 + 残り3つ = 5つ全て返される
            assert len(enhanced) == 5

    @pytest.mark.asyncio
    async def test_enhance_with_retry_success(self, mock_enhancer, sample_issue):
        """リトライ成功のテスト"""
        enhanced_issue = Issue(
            detector_name="Test",
            severity=Severity.HIGH,
            category=IssueCategory.PERFORMANCE,
            title="Enhanced",
            description="Enhanced issue",
            file_path="test.java",
            line_number=10,
            query_text="",
            metadata={'llm_enhanced': True}
        )

        mock_enhancer.parser.parse_analysis = Mock(return_value=enhanced_issue)

        result = await mock_enhancer._enhance_with_retry(sample_issue, "Test prompt")

        assert result.metadata['llm_enhanced'] is True
        assert result.metadata['llm_model'] == "claude-sonnet-3.5"
        assert result.metadata['llm_attempts'] == 1

    @pytest.mark.asyncio
    async def test_enhance_with_retry_failure(self, mock_enhancer, sample_issue):
        """リトライ失敗のテスト"""
        mock_enhancer.client.analyze_code = AsyncMock(side_effect=Exception("Retry Error"))

        result = await mock_enhancer._enhance_with_retry(sample_issue, "Test prompt")

        # 元のIssue返却
        assert result.file_path == sample_issue.file_path
        assert 'llm_error' in result.metadata
        assert result.metadata['llm_attempts'] == 2  # max_retries=2

    def test_clear_cache(self, mock_enhancer):
        """キャッシュクリアのテスト"""
        mock_enhancer._cache = {'key1': 'value1', 'key2': 'value2'}

        mock_enhancer.clear_cache()

        assert len(mock_enhancer._cache) == 0

    def test_get_stats(self, mock_enhancer):
        """統計情報取得のテスト"""
        mock_enhancer._cache = {'key1': 'value1'}

        stats = mock_enhancer.get_stats()

        assert stats['cache_size'] == 1
        assert stats['rate_limit_rpm'] == 60
        assert stats['max_batch_size'] == 3
        assert stats['model'] == "claude-sonnet-3.5"
