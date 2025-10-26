"""
Anthropic Claude APIクライアント

Claude APIとの通信を管理し、レート制限やリトライ処理を実装
"""
import os
import time
from typing import Dict, Any, Optional, List
from anthropic import Anthropic, APIError, RateLimitError, APIConnectionError


class AnthropicClient:
    """
    Anthropic Claude APIクライアント

    環境変数ANTHROPIC_API_KEYからAPIキーを読み込み、
    レート制限とリトライ処理を実装
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Args:
            api_key: APIキー（Noneの場合は環境変数から取得）
            model: 使用するClaudeモデル
            max_retries: 最大リトライ回数
            retry_delay: リトライ間の待機時間（秒）
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is not set. "
                "Please set it or pass api_key parameter."
            )

        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Anthropicクライアントの初期化
        self.client = Anthropic(api_key=self.api_key)

    def analyze_code(
        self,
        code: str,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> str:
        """
        コードを分析してレスポンスを取得

        Args:
            code: 分析対象のコード
            prompt: 分析指示のプロンプト
            max_tokens: 最大トークン数
            temperature: 生成の温度（0.0 = 決定的, 1.0 = ランダム）

        Returns:
            Claude APIのレスポンステキスト

        Raises:
            APIError: API呼び出しエラー
            ValueError: 無効な入力
        """
        if not code or not code.strip():
            raise ValueError("Code cannot be empty")

        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        # プロンプトの構築
        full_prompt = f"{prompt}\n\n```java\n{code}\n```"

        # リトライ付きでAPI呼び出し
        for attempt in range(self.max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[
                        {
                            "role": "user",
                            "content": full_prompt,
                        }
                    ],
                )

                # レスポンスからテキストを抽出
                if response.content and len(response.content) > 0:
                    return response.content[0].text

                raise APIError("Empty response from API")

            except RateLimitError as e:
                # レート制限エラー: 指数バックオフで再試行
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    time.sleep(wait_time)
                    continue
                raise

            except APIConnectionError as e:
                # 接続エラー: 再試行
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                raise

            except APIError as e:
                # その他のAPIエラー
                raise

        raise APIError(f"Failed after {self.max_retries} retries")

    def analyze_code_batch(
        self,
        code_snippets: List[Dict[str, str]],
        prompt: str,
        max_tokens: int = 4096,
    ) -> List[str]:
        """
        複数のコードスニペットをバッチ分析

        Args:
            code_snippets: コードスニペットのリスト
                           各要素は {"id": "識別子", "code": "コード"} の辞書
            prompt: 分析指示のプロンプト
            max_tokens: 最大トークン数

        Returns:
            各スニペットの分析結果のリスト

        Raises:
            APIError: API呼び出しエラー
        """
        results = []

        for snippet in code_snippets:
            snippet_id = snippet.get("id", "unknown")
            code = snippet.get("code", "")

            if not code:
                results.append("")
                continue

            try:
                result = self.analyze_code(
                    code=code,
                    prompt=prompt,
                    max_tokens=max_tokens,
                )
                results.append(result)

            except APIError as e:
                # エラーの場合は空文字列を返す
                # （バッチ処理全体を停止しない）
                results.append("")

        return results

    def generate_recommendation(
        self,
        issue_description: str,
        code_context: str,
        max_tokens: int = 1024,
    ) -> str:
        """
        問題に対する推奨事項を生成

        Args:
            issue_description: 問題の説明
            code_context: コードのコンテキスト
            max_tokens: 最大トークン数

        Returns:
            推奨事項のテキスト

        Raises:
            APIError: API呼び出しエラー
        """
        prompt = f"""You are an expert in Apache Cassandra and Java development.

Given the following issue and code context, provide a detailed recommendation on how to fix it.

Issue:
{issue_description}

Code Context:
```java
{code_context}
```

Please provide:
1. A clear explanation of why this is a problem
2. Step-by-step instructions to fix it
3. Best practices to avoid this issue in the future

Keep your response concise and actionable."""

        return self.analyze_code(
            code=code_context,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=0.0,
        )

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        API呼び出しのコストを概算

        Args:
            input_tokens: 入力トークン数
            output_tokens: 出力トークン数

        Returns:
            概算コスト（USD）

        Note:
            Claude 3.5 Sonnetの料金:
            - Input: $3 / 1M tokens
            - Output: $15 / 1M tokens
        """
        # Claude 3.5 Sonnetの料金（2025年1月時点）
        input_cost_per_token = 3.0 / 1_000_000
        output_cost_per_token = 15.0 / 1_000_000

        total_cost = (
            input_tokens * input_cost_per_token +
            output_tokens * output_cost_per_token
        )

        return total_cost

    def get_model_info(self) -> Dict[str, Any]:
        """
        使用中のモデル情報を取得

        Returns:
            モデル情報の辞書
        """
        return {
            "model": self.model,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
        }
