"""
ASTベースのJavaパーサー

javalanglibを使用してJavaコードを抽象構文木(AST)として解析し、
より正確なCassandra呼び出しの抽出を行う
"""
import re
from typing import List, Optional, Set
from pathlib import Path
import javalang

from cassandra_analyzer.models import CassandraCall, CallType
from .base import BaseParser


class ASTJavaParser(BaseParser):
    """
    ASTベースのJavaパーサー

    javalanglibを使用してJavaコードをASTとして解析し、
    Cassandra関連のメソッド呼び出しを正確に抽出
    """

    # Cassandra関連のクラス名
    CASSANDRA_CLASSES = {
        "Session",
        "CqlSession",
        "SimpleStatement",
        "PreparedStatement",
        "BoundStatement",
        "BatchStatement",
    }

    # Cassandra関連のメソッド名
    CASSANDRA_METHODS = {
        "execute",
        "executeAsync",
        "prepare",
        "add",  # BatchStatement.add()
    }

    def __init__(self, config: Optional[dict] = None):
        """
        Args:
            config: パーサー設定
        """
        super().__init__(config)

    def parse_file(self, file_path: str) -> List[CassandraCall]:
        """
        Javaファイルを解析してCassandra呼び出しを抽出

        Args:
            file_path: 解析するJavaファイルのパス

        Returns:
            CassandraCall のリスト
        """
        try:
            # ファイルを読み込み
            with open(file_path, "r", encoding="utf-8") as f:
                java_code = f.read()

            # ASTに変換
            tree = javalang.parse.parse(java_code)

            # Cassandra呼び出しを抽出
            calls = self._extract_cassandra_calls(tree, java_code, file_path)

            return calls

        except javalang.parser.JavaSyntaxError as e:
            # 構文エラーは空リストを返す
            return []
        except Exception as e:
            # その他のエラーも空リストを返す
            return []

    def _extract_cassandra_calls(
        self,
        tree: javalang.tree.CompilationUnit,
        source_code: str,
        file_path: str,
    ) -> List[CassandraCall]:
        """
        ASTからCassandra呼び出しを抽出

        Args:
            tree: JavaのAST
            source_code: ソースコード（行番号計算用）
            file_path: ファイルパス

        Returns:
            CassandraCall のリスト
        """
        calls = []

        # メソッド呼び出しをすべて走査
        for path, node in tree.filter(javalang.tree.MethodInvocation):
            # Cassandraメソッド呼び出しかチェック
            if self._is_cassandra_method(node):
                call = self._create_cassandra_call(
                    node, path, source_code, file_path
                )
                if call:
                    calls.append(call)

        return calls

    def _is_cassandra_method(self, node: javalang.tree.MethodInvocation) -> bool:
        """
        メソッド呼び出しがCassandra関連かどうかを判定

        Args:
            node: メソッド呼び出しノード

        Returns:
            Cassandra関連の場合True
        """
        # メソッド名をチェック
        if node.member not in self.CASSANDRA_METHODS:
            return False

        # qualifierがある場合（session.execute()など）
        if node.qualifier:
            # 型情報は取得困難なため、変数名ベースで判定
            # session, cqlSession などの命名規則を検出
            qualifier_name = self._get_qualifier_name(node.qualifier)
            if qualifier_name:
                qualifier_lower = qualifier_name.lower()
                if "session" in qualifier_lower or "statement" in qualifier_lower:
                    return True

        return True  # メソッド名が一致すればCassandra関連とみなす

    def _get_qualifier_name(self, qualifier) -> Optional[str]:
        """
        qualifierから名前を取得

        Args:
            qualifier: qualifierノード

        Returns:
            名前（取得できない場合はNone）
        """
        if isinstance(qualifier, javalang.tree.MemberReference):
            return qualifier.member
        elif hasattr(qualifier, "value"):
            return qualifier.value
        return None

    def _create_cassandra_call(
        self,
        node: javalang.tree.MethodInvocation,
        path: List,
        source_code: str,
        file_path: str,
    ) -> Optional[CassandraCall]:
        """
        メソッド呼び出しノードからCassandraCallを生成

        Args:
            node: メソッド呼び出しノード
            path: ASTパス
            source_code: ソースコード
            file_path: ファイルパス

        Returns:
            CassandraCall（生成できない場合はNone）
        """
        try:
            # 行番号を取得
            line_number = self._get_line_number(node, source_code)

            # CQLテキストを抽出
            cql_text = self._extract_cql_from_arguments(node)

            # Prepared Statementかどうかを判定
            is_prepared = self._is_prepared_statement(node, path)

            # 整合性レベルを抽出
            consistency_level = self._extract_consistency_level(node)

            # クラス名とメソッドコンテキストを取得
            class_name = self._find_enclosing_class(path)
            method_context = self._find_enclosing_method(path)

            # CallTypeを判定
            call_type = self._determine_call_type(node.member)

            return CassandraCall(
                method_name=node.member,
                cql_text=cql_text,
                line_number=line_number,
                is_prepared=is_prepared,
                consistency_level=consistency_level,
                file_path=file_path,
                call_type=call_type,
                class_name=class_name,
                method_context=method_context,
            )

        except Exception as e:
            # エラーの場合はNone
            return None

    def _get_line_number(
        self,
        node: javalang.tree.MethodInvocation,
        source_code: str,
    ) -> int:
        """
        ノードの行番号を取得

        Args:
            node: ASTノード
            source_code: ソースコード

        Returns:
            行番号（1-indexed、取得できない場合は0）
        """
        # javalanglibはposition情報を提供しないため、
        # メソッド名を使って検索
        if hasattr(node, "position") and node.position:
            return node.position.line

        # position情報がない場合は、ソースコードから検索
        # （完全ではないが、おおよその位置を特定）
        lines = source_code.split("\n")
        method_name = node.member
        for i, line in enumerate(lines, 1):
            if method_name in line:
                return i

        return 0

    def _extract_cql_from_arguments(
        self,
        node: javalang.tree.MethodInvocation,
    ) -> str:
        """
        メソッド引数からCQLクエリを抽出

        Args:
            node: メソッド呼び出しノード

        Returns:
            CQLクエリ文字列
        """
        if not node.arguments:
            return ""

        # 最初の引数がCQLクエリの可能性が高い
        first_arg = node.arguments[0]

        # 文字列リテラルの場合
        if isinstance(first_arg, javalang.tree.Literal):
            if first_arg.value:
                # クォートを削除
                return first_arg.value.strip('"').strip("'")

        # BinaryOperationの場合（文字列連結）
        if isinstance(first_arg, javalang.tree.BinaryOperation):
            return self._extract_from_binary_operation(first_arg)

        # MemberReferenceの場合（定数参照）
        if isinstance(first_arg, javalang.tree.MemberReference):
            return f"[CONSTANT: {first_arg.member}]"

        return ""

    def _extract_from_binary_operation(
        self,
        node: javalang.tree.BinaryOperation,
    ) -> str:
        """
        BinaryOperationから文字列を抽出（文字列連結など）

        Args:
            node: BinaryOperationノード

        Returns:
            抽出された文字列
        """
        parts = []

        def collect_parts(n):
            if isinstance(n, javalang.tree.Literal):
                if n.value:
                    parts.append(n.value.strip('"').strip("'"))
            elif isinstance(n, javalang.tree.BinaryOperation):
                collect_parts(n.operandl)
                collect_parts(n.operandr)

        collect_parts(node)
        return " ".join(parts) if parts else "[STRING_CONCAT]"

    def _is_prepared_statement(
        self,
        node: javalang.tree.MethodInvocation,
        path: List,
    ) -> bool:
        """
        Prepared Statementを使用しているかを判定

        Args:
            node: メソッド呼び出しノード
            path: ASTパス

        Returns:
            Prepared Statementの場合True
        """
        # メソッド名が "prepare" の場合
        if node.member == "prepare":
            return True

        # PreparedStatement型の変数から呼び出されている場合
        if node.qualifier:
            qualifier_name = self._get_qualifier_name(node.qualifier)
            if qualifier_name and "prepared" in qualifier_name.lower():
                return True

        # 引数にPreparedStatementが含まれているか
        if node.arguments:
            for arg in node.arguments:
                if isinstance(arg, javalang.tree.MemberReference):
                    if "prepared" in arg.member.lower():
                        return True

        return False

    def _extract_consistency_level(
        self,
        node: javalang.tree.MethodInvocation,
    ) -> Optional[str]:
        """
        整合性レベルを抽出

        Args:
            node: メソッド呼び出しノード

        Returns:
            整合性レベル（見つからない場合はNone）
        """
        # 引数から整合性レベルを探す
        if node.arguments:
            for arg in node.arguments:
                if isinstance(arg, javalang.tree.MemberReference):
                    member = arg.member
                    # ConsistencyLevel.XXX のパターン
                    if member in ["ONE", "QUORUM", "ALL", "LOCAL_QUORUM", "EACH_QUORUM"]:
                        return member

        return None

    def _find_enclosing_class(self, path: List) -> Optional[str]:
        """
        パスから囲むクラス名を取得

        Args:
            path: ASTパス

        Returns:
            クラス名（見つからない場合はNone）
        """
        for node in reversed(path):
            if isinstance(node, javalang.tree.ClassDeclaration):
                return node.name
        return None

    def _find_enclosing_method(self, path: List) -> Optional[str]:
        """
        パスから囲むメソッド名を取得

        Args:
            path: ASTパス

        Returns:
            メソッド名（見つからない場合はNone）
        """
        for node in reversed(path):
            if isinstance(node, javalang.tree.MethodDeclaration):
                return node.name
        return None

    def _determine_call_type(self, method_name: str) -> CallType:
        """
        メソッド名からCallTypeを判定

        Args:
            method_name: メソッド名

        Returns:
            CallType
        """
        method_lower = method_name.lower()
        if method_lower == "execute":
            return CallType.EXECUTE
        elif method_lower == "executeasync":
            return CallType.EXECUTE_ASYNC
        elif method_lower == "prepare":
            return CallType.PREPARE
        elif method_lower == "add":
            return CallType.BATCH
        return CallType.UNKNOWN
