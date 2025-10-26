"""
Cassandra呼び出し情報を表すモデル
"""
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class CallType(Enum):
    """Cassandra呼び出しのタイプ"""

    EXECUTE = "execute"
    EXECUTE_ASYNC = "executeAsync"
    PREPARE = "prepare"
    BATCH = "batch"
    UNKNOWN = "unknown"


@dataclass
class CassandraCall:
    """
    Cassandraの呼び出し情報

    Attributes:
        method_name: メソッド名（execute、executeAsync等）
        cql_text: CQLクエリ文字列
        line_number: ソースコード上の行番号
        is_prepared: Prepared Statementを使用しているか
        consistency_level: 整合性レベル（QUORUM、ONE等）
        file_path: ファイルパス
        call_type: 呼び出しタイプ
        class_name: クラス名（オプション）
        method_context: メソッドコンテキスト（オプション）
    """

    method_name: str
    cql_text: str
    line_number: int
    is_prepared: bool
    consistency_level: Optional[str]
    file_path: str
    call_type: CallType = CallType.UNKNOWN
    class_name: Optional[str] = None
    method_context: Optional[str] = None

    def __post_init__(self) -> None:
        """初期化後の処理"""
        # メソッド名からCallTypeを自動設定
        if self.call_type == CallType.UNKNOWN:
            self.call_type = self._determine_call_type()

    def _determine_call_type(self) -> CallType:
        """
        メソッド名からCallTypeを判定

        Returns:
            判定されたCallType
        """
        method_lower = self.method_name.lower()
        if method_lower == "execute":
            return CallType.EXECUTE
        elif method_lower == "executeasync":
            return CallType.EXECUTE_ASYNC
        elif method_lower == "prepare":
            return CallType.PREPARE
        elif method_lower == "batch":
            return CallType.BATCH
        return CallType.UNKNOWN

    def is_constant_reference(self) -> bool:
        """
        CQLが定数参照かどうかを判定

        Returns:
            定数参照の場合True
        """
        return self.cql_text.startswith("[CONSTANT:")

    def get_short_location(self) -> str:
        """
        短縮された位置情報を取得

        Returns:
            ファイル名:行番号の形式
        """
        import os

        filename = os.path.basename(self.file_path)
        return f"{filename}:{self.line_number}"

    def __str__(self) -> str:
        """文字列表現"""
        return f"CassandraCall({self.method_name} at {self.get_short_location()})"
