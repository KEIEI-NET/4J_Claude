"""
パーサーの基底クラス
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from cassandra_analyzer.models import CassandraCall


class BaseParser(ABC):
    """
    パーサーの基底クラス

    すべてのパーサーはこのクラスを継承して実装
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Args:
            config: パーサー設定
        """
        self.config = config or {}

    @abstractmethod
    def parse_file(self, file_path: str) -> List[CassandraCall]:
        """
        ファイルを解析してCassandra呼び出しを抽出

        Args:
            file_path: 解析するファイルのパス

        Returns:
            CassandraCall のリスト
        """
        pass
