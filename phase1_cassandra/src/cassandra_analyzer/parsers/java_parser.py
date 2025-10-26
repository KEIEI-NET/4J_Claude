"""
Javaファイルを解析し、Cassandra関連の呼び出しを抽出
"""
import re
from pathlib import Path
from typing import List, Optional, Dict, Any
import javalang

from ..models import CassandraCall, CallType
from .base import BaseParser


class JavaCassandraParser(BaseParser):
    """
    JavaファイルからCassandra操作を抽出

    検出対象:
    - session.execute()
    - session.executeAsync()
    - session.prepare()
    - BatchStatement
    """

    # Cassandra関連のメソッド
    CASSANDRA_METHODS = ["execute", "executeAsync", "prepare", "batch"]

    def __init__(self, config: Optional[Dict] = None):
        """
        Args:
            config: 設定辞書（オプション）
        """
        super().__init__(config)
        self.resolve_constants = self.config.get("resolve_constants", True)  # デフォルトで有効化
        self._constants_cache: Dict[str, str] = {}
        self._file_cache: Dict[str, Dict[str, str]] = {}  # ファイルごとの定数キャッシュ

    def parse_file(self, file_path: Path) -> List[CassandraCall]:
        """
        Javaファイルを解析してCassandra呼び出しを抽出

        Args:
            file_path: 解析対象のJavaファイルパス

        Returns:
            CassandraCallのリスト
        """
        file_path_str = str(file_path)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return []

        # AST解析
        try:
            tree = javalang.parse.parse(content)
        except javalang.parser.JavaSyntaxError as e:
            print(f"Syntax error in {file_path}: {e}")
            return []

        calls: List[CassandraCall] = []

        # 定数の抽出（ファイルキャッシュ活用）
        if self.resolve_constants:
            if file_path_str not in self._file_cache:
                self._file_cache[file_path_str] = self._extract_constants(tree, content)
            self._constants_cache = self._file_cache[file_path_str]

        # MethodInvocationノードを探索
        for path, node in tree.filter(javalang.tree.MethodInvocation):
            if self._is_cassandra_call(node):
                call = self._extract_call_info(node, content, str(file_path))
                if call:
                    calls.append(call)

        return calls

    def _is_cassandra_call(self, node: javalang.tree.MethodInvocation) -> bool:
        """
        Cassandra関連の呼び出しか判定

        Args:
            node: メソッド呼び出しノード

        Returns:
            Cassandra関連の場合True
        """
        return node.member in self.CASSANDRA_METHODS

    def _extract_call_info(
        self, node: javalang.tree.MethodInvocation, content: str, file_path: str
    ) -> Optional[CassandraCall]:
        """
        呼び出し情報を詳細に抽出

        Args:
            node: メソッド呼び出しノード
            content: ファイル全体のコンテンツ
            file_path: ファイルパス

        Returns:
            CassandraCall または None
        """
        # CQL文字列の抽出
        cql_text = self._extract_cql_string(node)
        if not cql_text:
            return None

        # 行番号の取得
        line_number = node.position.line if hasattr(node, "position") else 0

        # Prepared Statement判定
        is_prepared = node.member == "prepare" or self._check_prepared_statement_usage(
            content, line_number
        )

        # Consistency Level抽出
        consistency_level = self._extract_consistency_level(content, line_number)

        return CassandraCall(
            method_name=node.member,
            cql_text=cql_text,
            line_number=line_number,
            is_prepared=is_prepared,
            consistency_level=consistency_level,
            file_path=file_path,
        )

    def _extract_cql_string(self, node: javalang.tree.MethodInvocation) -> Optional[str]:
        """
        メソッド引数からCQL文字列を抽出

        Args:
            node: メソッド呼び出しノード

        Returns:
            CQL文字列 または None
        """
        if not node.arguments:
            return None

        for arg in node.arguments:
            # 文字列リテラル
            if isinstance(arg, javalang.tree.Literal):
                return arg.value.strip('"\'')

            # 定数参照
            elif isinstance(arg, javalang.tree.MemberReference):
                constant_name = arg.member
                if self.resolve_constants and constant_name in self._constants_cache:
                    return self._constants_cache[constant_name]
                return f"[CONSTANT: {constant_name}]"

        return None

    def _extract_constants(
        self, tree: javalang.tree.CompilationUnit, content: str
    ) -> Dict[str, str]:
        """
        static final String定数を抽出（強化版）

        Args:
            tree: ASTツリー
            content: ファイルコンテンツ

        Returns:
            定数名と値のマッピング
        """
        constants: Dict[str, str] = {}

        # フィールド宣言を探索
        for path, node in tree.filter(javalang.tree.FieldDeclaration):
            # static finalチェック（public/private問わず）
            if "static" in node.modifiers and "final" in node.modifiers:
                # String型のみ対象
                if isinstance(node.type, javalang.tree.ReferenceType):
                    if node.type.name == "String":
                        for declarator in node.declarators:
                            if declarator.initializer:
                                constant_value = self._extract_constant_value(
                                    declarator.initializer, content
                                )
                                if constant_value:
                                    constants[declarator.name] = constant_value

        return constants

    def _extract_constant_value(
        self, initializer: Any, content: str
    ) -> Optional[str]:
        """
        初期化式から定数値を抽出

        Args:
            initializer: 初期化式のASTノード
            content: ファイルコンテンツ

        Returns:
            定数値 または None
        """
        # 文字列リテラル
        if isinstance(initializer, javalang.tree.Literal):
            return initializer.value.strip('"\'')

        # 文字列連結（BinaryOperation）
        elif isinstance(initializer, javalang.tree.BinaryOperation):
            if initializer.operator == "+":
                left = self._extract_constant_value(initializer.operandl, content)
                right = self._extract_constant_value(initializer.operandr, content)
                if left and right:
                    return left + right

        # 定数参照（他の定数を参照している場合）
        elif isinstance(initializer, javalang.tree.MemberReference):
            # 同じファイル内の定数を参照している可能性
            # TODO: 定数参照チェーンの解決（将来の拡張）
            pass

        return None

    def _check_prepared_statement_usage(self, content: str, line_number: int) -> bool:
        """
        Prepared Statementが使用されているか確認（強化版）

        Args:
            content: ファイルコンテンツ
            line_number: 検査対象の行番号

        Returns:
            Prepared Statement使用の場合True
        """
        lines = content.split("\n")

        # より広いコンテキストを確認（前後10行）
        start = max(0, line_number - 10)
        end = min(len(lines), line_number + 10)
        context = "\n".join(lines[start:end])

        # 現在の行を取得
        current_line = lines[line_number - 1] if line_number > 0 else ""

        # パターン1: PreparedStatementの直接使用
        if re.search(r"PreparedStatement\s+\w+", context):
            return True

        # パターン2: BoundStatementの使用
        if re.search(r"BoundStatement\s+\w+", context):
            return True

        # パターン3: prepare()メソッドの呼び出し
        if re.search(r"\.prepare\s*\(", context):
            return True

        # パターン4: bind()メソッドの使用
        if re.search(r"\.bind\s*\(", context):
            return True

        # パターン5: 変数がprepareステートメントとして宣言されている
        # 例: private final PreparedStatement selectStmt;
        if re.search(r"PreparedStatement\s+\w+Stmt", content):
            # メソッド内でそのステートメントを使用しているかチェック
            stmt_names = re.findall(r"PreparedStatement\s+(\w+)", content)
            for stmt_name in stmt_names:
                if stmt_name in current_line:
                    return True

        # パターン6: SimpleStatementでないことを確認
        if "SimpleStatement" in current_line:
            return False

        # パターン7: session.execute()に文字列を直接渡していない
        if re.search(r'execute\s*\(\s*["\']', current_line):
            return False

        return False

    def _extract_consistency_level(self, content: str, line_number: int) -> Optional[str]:
        """
        Consistency Levelの設定を抽出（強化版）

        Args:
            content: ファイルコンテンツ
            line_number: 検査対象の行番号

        Returns:
            Consistency Level または None
        """
        lines = content.split("\n")

        # より広いコンテキストを確認（前後10行）
        start = max(0, line_number - 10)
        end = min(len(lines), line_number + 10)
        context = "\n".join(lines[start:end])

        # パターン1: ConsistencyLevel.XXX の直接使用
        match = re.search(r"ConsistencyLevel\.(\w+)", context)
        if match:
            return match.group(1)

        # パターン2: setConsistencyLevel() メソッド呼び出し
        match = re.search(r"setConsistencyLevel\s*\(\s*ConsistencyLevel\.(\w+)", context)
        if match:
            return match.group(1)

        return None

    def _extract_retry_policy(self, content: str, line_number: int) -> Optional[str]:
        """
        Retry Policyの抽出

        Args:
            content: ファイルコンテンツ
            line_number: 検査対象の行番号

        Returns:
            Retry Policy または None
        """
        lines = content.split("\n")
        start = max(0, line_number - 10)
        end = min(len(lines), line_number + 10)
        context = "\n".join(lines[start:end])

        # RetryPolicy の各種パターン
        retry_patterns = [
            (r"DefaultRetryPolicy\(\)", "DEFAULT"),
            (r"DowngradingConsistencyRetryPolicy\(\)", "DOWNGRADING"),
            (r"FallthroughRetryPolicy\(\)", "FALLTHROUGH"),
            (r"LoggingRetryPolicy\(", "LOGGING"),
        ]

        for pattern, policy_name in retry_patterns:
            if re.search(pattern, context):
                return policy_name

        return None

    def _extract_timeout(self, content: str, line_number: int) -> Optional[int]:
        """
        Timeoutの抽出（ミリ秒）

        Args:
            content: ファイルコンテンツ
            line_number: 検査対象の行番号

        Returns:
            Timeout（ミリ秒） または None
        """
        lines = content.split("\n")
        start = max(0, line_number - 10)
        end = min(len(lines), line_number + 10)
        context = "\n".join(lines[start:end])

        # setTimeout() または setReadTimeoutMillis() のパターン
        timeout_patterns = [
            r"setTimeout\s*\(\s*(\d+)",
            r"setReadTimeoutMillis\s*\(\s*(\d+)",
            r"setReadTimeout\s*\(\s*(\d+)",
        ]

        for pattern in timeout_patterns:
            match = re.search(pattern, context)
            if match:
                return int(match.group(1))

        return None
