"""
レポーター基底クラス

分析結果を様々な形式で出力するレポーターの基底クラス
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from cassandra_analyzer.models import AnalysisResult


class BaseReporter(ABC):
    """
    レポーター基底クラス

    全てのレポーターはこのクラスを継承する必要がある
    """

    def __init__(self, config: Optional[dict] = None):
        """
        Args:
            config: レポーター設定（オプション）
        """
        self.config = config or {}

    @property
    @abstractmethod
    def format_name(self) -> str:
        """
        レポート形式の名前

        Returns:
            形式名（例: "JSON", "Markdown", "HTML"）
        """
        pass

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """
        デフォルトのファイル拡張子

        Returns:
            拡張子（例: ".json", ".md", ".html"）
        """
        pass

    @abstractmethod
    def generate(self, result: AnalysisResult) -> str:
        """
        分析結果からレポートを生成

        Args:
            result: 分析結果

        Returns:
            生成されたレポート文字列
        """
        pass

    def save(self, content: str, file_path: str) -> None:
        """
        レポートをファイルに保存

        Args:
            content: レポート内容
            file_path: 保存先パス
        """
        path = Path(file_path)

        # ディレクトリが存在しない場合は作成
        path.parent.mkdir(parents=True, exist_ok=True)

        # ファイルに書き込み
        path.write_text(content, encoding="utf-8")

    def generate_and_save(self, result: AnalysisResult, file_path: str) -> str:
        """
        レポートを生成してファイルに保存

        Args:
            result: 分析結果
            file_path: 保存先パス

        Returns:
            生成されたレポート文字列
        """
        content = self.generate(result)
        self.save(content, file_path)
        return content
