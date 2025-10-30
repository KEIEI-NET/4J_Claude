"""
Claude API Client

Claude APIとの通信を管理するクライアントクラス。
レート制限、リトライ、エラーハンドリングを提供します。
"""

import os
import time
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ClaudeModel(Enum):
    """Claude APIモデル"""
    OPUS = "claude-3-opus-20240229"
    SONNET = "claude-3-5-sonnet-20241022"
    HAIKU = "claude-3-5-haiku-20241022"


@dataclass
class APIUsage:
    """API使用状況"""
    total_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    request_history: List[Dict[str, Any]] = field(default_factory=list)

    def add_request(
        self,
        input_tokens: int,
        output_tokens: int,
        model: ClaudeModel
    ) -> None:
        """リクエスト情報を記録"""
        self.total_requests += 1
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens += input_tokens + output_tokens

        # コスト計算（2024年1月時点の料金）
        cost_per_million = {
            ClaudeModel.OPUS: (15.00, 75.00),    # (input, output)
            ClaudeModel.SONNET: (3.00, 15.00),
            ClaudeModel.HAIKU: (0.25, 1.25),
        }

        input_cost, output_cost = cost_per_million.get(
            model,
            (3.00, 15.00)  # デフォルト: Sonnet
        )

        request_cost = (
            (input_tokens / 1_000_000) * input_cost +
            (output_tokens / 1_000_000) * output_cost
        )
        self.total_cost += request_cost

        self.request_history.append({
            'timestamp': time.time(),
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'cost': request_cost,
            'model': model.value
        })


class ClaudeClient:
    """
    Claude API クライアント

    機能:
    - Claude APIへの接続
    - レート制限対応
    - 指数バックオフリトライ
    - コスト追跡
    - エラーハンドリング
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: ClaudeModel = ClaudeModel.SONNET,
        max_retries: int = 3,
        timeout: int = 60
    ):
        """
        Claude APIクライアントを初期化

        Args:
            api_key: AnthropicのAPIキー（Noneの場合は環境変数から取得）
            model: 使用するClaudeモデル
            max_retries: 最大リトライ回数
            timeout: リクエストタイムアウト（秒）
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError(
                "API key not provided. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        self.usage = APIUsage()

        # Anthropic clientの初期化（遅延インポート）
        self._client: Optional[Any] = None

    @property
    def client(self) -> Any:
        """Anthropic clientの遅延初期化"""
        if self._client is None:
            try:
                from anthropic import Anthropic
                self._client = Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "anthropic package is required. "
                    "Install it with: pip install anthropic"
                )
        return self._client

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        model: Optional[ClaudeModel] = None
    ) -> str:
        """
        テキスト生成

        Args:
            prompt: ユーザープロンプト
            system_prompt: システムプロンプト
            max_tokens: 最大生成トークン数
            temperature: 温度パラメータ（0.0-1.0）
            model: 使用するモデル（Noneの場合はインスタンスのデフォルト）

        Returns:
            生成されたテキスト
        """
        use_model = model or self.model

        for attempt in range(self.max_retries):
            try:
                messages = [{"role": "user", "content": prompt}]

                kwargs: Dict[str, Any] = {
                    "model": use_model.value,
                    "max_tokens": max_tokens,
                    "messages": messages,
                    "temperature": temperature,
                }

                if system_prompt:
                    kwargs["system"] = system_prompt

                response = self.client.messages.create(**kwargs)

                # 使用状況を記録
                self.usage.add_request(
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                    model=use_model
                )

                # レスポンスからテキストを抽出
                if response.content and len(response.content) > 0:
                    return response.content[0].text

                raise ValueError("Empty response from Claude API")

            except Exception as e:
                logger.warning(
                    f"API request failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                )

                if attempt < self.max_retries - 1:
                    # 指数バックオフ
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error("Max retries reached. Request failed.")
                    raise

        raise RuntimeError("Failed to generate text after max retries")

    def generate_batch(
        self,
        prompts: List[str],
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        delay_between_requests: float = 1.0
    ) -> List[str]:
        """
        バッチでテキスト生成

        Args:
            prompts: プロンプトのリスト
            system_prompt: システムプロンプト
            max_tokens: 最大生成トークン数
            temperature: 温度パラメータ
            delay_between_requests: リクエスト間の遅延（秒）

        Returns:
            生成されたテキストのリスト
        """
        results = []

        for i, prompt in enumerate(prompts):
            logger.info(f"Processing prompt {i + 1}/{len(prompts)}")

            result = self.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            results.append(result)

            # レート制限を避けるための遅延
            if i < len(prompts) - 1:
                time.sleep(delay_between_requests)

        return results

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        使用統計を取得

        Returns:
            使用統計の辞書
        """
        return {
            'total_requests': self.usage.total_requests,
            'total_tokens': self.usage.total_tokens,
            'input_tokens': self.usage.input_tokens,
            'output_tokens': self.usage.output_tokens,
            'total_cost_usd': round(self.usage.total_cost, 4),
            'average_cost_per_request': (
                round(self.usage.total_cost / self.usage.total_requests, 4)
                if self.usage.total_requests > 0 else 0
            )
        }

    def reset_usage_stats(self) -> None:
        """使用統計をリセット"""
        self.usage = APIUsage()
