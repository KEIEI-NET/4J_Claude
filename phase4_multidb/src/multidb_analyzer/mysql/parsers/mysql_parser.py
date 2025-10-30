"""
MySQL Parser

JavaコードからMySQL/JDBCクエリを抽出するパーサー
"""

import re
import logging
from typing import List, Optional, Set
from pathlib import Path

import javalang

from multidb_analyzer.mysql.models import (
    MySQLQuery,
    SQLOperation,
    TableReference,
    JoinType,
    JoinInfo
)

logger = logging.getLogger(__name__)


class MySQLParser:
    """
    MySQL/JDBCクエリパーサー

    以下のパターンをサポート:
    - JDBC: Statement, PreparedStatement, CallableStatement
    - MyBatis: @Select, @Insert, @Update, @Delete annotations
    - Spring Data JPA: @Query annotations
    - JPA Criteria API
    """

    def __init__(self):
        # JDBC関連のクラス名
        self.jdbc_classes = {
            'Statement', 'PreparedStatement', 'CallableStatement',
            'Connection', 'DataSource'
        }

        # SQL実行メソッド
        self.sql_execution_methods = {
            'executeQuery', 'executeUpdate', 'execute',
            'createQuery', 'createNativeQuery'
        }

        # MyBatisアノテーション
        self.mybatis_annotations = {
            '@Select', '@Insert', '@Update', '@Delete',
            '@SelectProvider', '@InsertProvider', '@UpdateProvider', '@DeleteProvider'
        }

        # Spring Data JPAアノテーション
        self.jpa_annotations = {
            '@Query', '@Modifying'
        }

    def parse_file(self, file_path: Path, code: Optional[str] = None) -> List[MySQLQuery]:
        """
        Javaファイルを解析してMySQLクエリを抽出

        Args:
            file_path: Javaファイルのパス
            code: Javaコード（Noneの場合はファイルから読み込み）

        Returns:
            抽出されたMySQLクエリのリスト
        """
        if code is None:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()

        try:
            tree = javalang.parse.parse(code)
            queries = []

            # JDBCクエリを抽出
            queries.extend(self._extract_jdbc_queries(tree, code, str(file_path)))

            # MyBatisクエリを抽出
            queries.extend(self._extract_mybatis_queries(tree, code, str(file_path)))

            # Spring Data JPAクエリを抽出
            queries.extend(self._extract_jpa_queries(tree, code, str(file_path)))

            logger.info(f"Extracted {len(queries)} MySQL queries from {file_path}")
            return queries

        except javalang.parser.JavaSyntaxError as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return []

    def _extract_jdbc_queries(
        self,
        tree: javalang.tree.CompilationUnit,
        code: str,
        file_path: str
    ) -> List[MySQLQuery]:
        """JDBCクエリを抽出"""
        queries = []
        lines = code.split('\n')

        for path, node in tree.filter(javalang.tree.MethodInvocation):
            # SQL実行メソッドかチェック
            if node.member not in self.sql_execution_methods:
                continue

            # クエリ文字列を抽出
            query_text = None
            if node.arguments:
                first_arg = node.arguments[0]

                # 文字列リテラル
                if isinstance(first_arg, javalang.tree.Literal):
                    query_text = first_arg.value.strip('"')

                # 変数参照
                elif isinstance(first_arg, javalang.tree.MemberReference):
                    query_text = self._find_variable_value(
                        tree, first_arg.member, code
                    )

            if not query_text or not self._is_sql_query(query_text):
                continue

            # 行番号を取得
            line_number = self._get_line_number(node, lines)

            # メソッド名とクラス名を取得
            method_name, class_name = self._get_context_info(path)

            # ループ内かチェック
            is_in_loop, loop_type = self._check_if_in_loop(path)

            # クエリを解析
            mysql_query = self._parse_sql_query(
                query_text=query_text,
                file_path=file_path,
                line_number=line_number,
                method_name=method_name,
                class_name=class_name,
                is_in_loop=is_in_loop,
                loop_type=loop_type
            )

            if mysql_query:
                queries.append(mysql_query)

        return queries

    def _extract_mybatis_queries(
        self,
        tree: javalang.tree.CompilationUnit,
        code: str,
        file_path: str
    ) -> List[MySQLQuery]:
        """MyBatisアノテーションからクエリを抽出"""
        queries = []
        lines = code.split('\n')

        for path, node in tree.filter(javalang.tree.MethodDeclaration):
            if not node.annotations:
                continue

            for annotation in node.annotations:
                if f"@{annotation.name}" not in self.mybatis_annotations:
                    continue

                # アノテーション値からクエリ抽出
                query_text = self._extract_annotation_value(annotation, code)

                if not query_text or not self._is_sql_query(query_text):
                    continue

                line_number = self._get_line_number(node, lines)
                method_name = node.name
                class_name = self._get_class_name(path)

                # クエリを解析
                mysql_query = self._parse_sql_query(
                    query_text=query_text,
                    file_path=file_path,
                    line_number=line_number,
                    method_name=method_name,
                    class_name=class_name
                )

                if mysql_query:
                    queries.append(mysql_query)

        return queries

    def _extract_jpa_queries(
        self,
        tree: javalang.tree.CompilationUnit,
        code: str,
        file_path: str
    ) -> List[MySQLQuery]:
        """Spring Data JPA @Queryアノテーションからクエリを抽出"""
        queries = []
        lines = code.split('\n')

        for path, node in tree.filter(javalang.tree.MethodDeclaration):
            if not node.annotations:
                continue

            for annotation in node.annotations:
                if f"@{annotation.name}" not in self.jpa_annotations:
                    continue

                # @Queryの値を抽出
                query_text = self._extract_annotation_value(annotation, code)

                if not query_text or not self._is_sql_query(query_text):
                    continue

                line_number = self._get_line_number(node, lines)
                method_name = node.name
                class_name = self._get_class_name(path)

                # クエリを解析
                mysql_query = self._parse_sql_query(
                    query_text=query_text,
                    file_path=file_path,
                    line_number=line_number,
                    method_name=method_name,
                    class_name=class_name
                )

                if mysql_query:
                    queries.append(mysql_query)

        return queries

    def _parse_sql_query(
        self,
        query_text: str,
        file_path: str,
        line_number: int,
        method_name: Optional[str] = None,
        class_name: Optional[str] = None,
        is_in_loop: bool = False,
        loop_type: Optional[str] = None
    ) -> Optional[MySQLQuery]:
        """SQL文字列を解析してMySQLQueryオブジェクトを作成"""

        # 正規化
        query_normalized = ' '.join(query_text.split()).upper()

        # 操作タイプを判定
        operation = self._determine_operation(query_normalized)
        if not operation:
            return None

        # テーブルを抽出
        tables = self._extract_tables(query_text, operation)

        # JOIN情報を抽出
        joins = self._extract_joins(query_text, line_number)

        # WHERE条件を抽出
        where_conditions = self._extract_where_conditions(query_text)

        # SELECT特有の情報
        uses_select_star = False
        column_count = None
        if operation == SQLOperation.SELECT:
            uses_select_star = self._uses_select_star(query_text)
            if not uses_select_star:
                column_count = self._count_selected_columns(query_text)

        # LIMIT/ORDER BY
        has_limit, limit_value = self._extract_limit(query_text)
        has_order_by, order_by_columns = self._extract_order_by(query_text)

        # インデックスヒント
        has_index_hint = self._has_index_hint(query_text)

        # サブクエリ
        has_subquery = self._has_subquery(query_text)

        return MySQLQuery(
            operation=operation,
            tables=tables,
            query_text=query_text,
            file_path=file_path,
            line_number=line_number,
            method_name=method_name,
            class_name=class_name,
            joins=joins,
            where_conditions=where_conditions,
            has_index_hint=has_index_hint,
            has_limit=has_limit,
            limit_value=limit_value,
            has_order_by=has_order_by,
            order_by_columns=order_by_columns,
            is_in_loop=is_in_loop,
            loop_type=loop_type,
            uses_select_star=uses_select_star,
            column_count=column_count,
            has_subquery=has_subquery
        )

    def _determine_operation(self, query: str) -> Optional[SQLOperation]:
        """SQL操作タイプを判定"""
        query = query.strip().upper()

        for op in SQLOperation:
            if query.startswith(op.value):
                return op

        return None

    def _extract_tables(self, query: str, operation: SQLOperation) -> List[TableReference]:
        """クエリからテーブルを抽出"""
        tables = []

        if operation == SQLOperation.SELECT:
            # FROM句からテーブル抽出
            from_match = re.search(
                r'\bFROM\s+([^\s,()]+(?:\s+AS\s+\w+)?(?:\s*,\s*[^\s,()]+(?:\s+AS\s+\w+)?)*)',
                query,
                re.IGNORECASE
            )
            if from_match:
                table_list = from_match.group(1)
                for table_str in re.split(r',\s*', table_list):
                    table = self._parse_table_reference(table_str.strip())
                    if table:
                        tables.append(table)

        elif operation in (SQLOperation.INSERT, SQLOperation.UPDATE, SQLOperation.DELETE):
            # INTO/FROM句からテーブル抽出
            pattern = r'\b(?:INTO|UPDATE|FROM)\s+([^\s,()]+(?:\s+AS\s+\w+)?)'
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                table = self._parse_table_reference(match.group(1).strip())
                if table:
                    tables.append(table)

        return tables

    def _parse_table_reference(self, table_str: str) -> Optional[TableReference]:
        """テーブル参照文字列を解析"""
        # schema.table AS alias パターン
        match = re.match(
            r'(?:(\w+)\.)?(\w+)(?:\s+(?:AS\s+)?(\w+))?',
            table_str,
            re.IGNORECASE
        )

        if match:
            schema, name, alias = match.groups()
            return TableReference(name=name, alias=alias, schema=schema)

        return None

    def _extract_joins(self, query: str, line_number: int) -> List[JoinInfo]:
        """JOIN情報を抽出"""
        joins = []

        # JOINパターン - よりシンプルに
        # (JOIN_TYPE?) JOIN table_name (alias?) ON condition
        join_pattern = r'\b((?:INNER|LEFT|RIGHT|FULL|CROSS)\s+)?JOIN\s+(\w+(?:\s+\w+)?)\s+ON\s+(.+?)(?=\s+(?:INNER|LEFT|RIGHT|FULL|CROSS)\s+JOIN|\s+WHERE|\s+GROUP|\s+ORDER|\s+LIMIT|;|$)'

        for match in re.finditer(join_pattern, query, re.IGNORECASE | re.DOTALL):
            join_type_str = (match.group(1) or 'INNER').strip().upper()
            table_str = match.group(2).strip()
            condition = match.group(3).strip()

            # JoinType enumに変換
            join_type = None
            for jt in JoinType:
                if jt.value.startswith(join_type_str):
                    join_type = jt
                    break

            if not join_type:
                join_type = JoinType.INNER

            table = self._parse_table_reference(table_str)
            if table:
                joins.append(JoinInfo(
                    join_type=join_type,
                    table=table,
                    condition=condition,
                    line_number=line_number
                ))

        return joins

    def _extract_where_conditions(self, query: str) -> List[str]:
        """WHERE条件を抽出"""
        where_match = re.search(
            r'\bWHERE\s+(.+?)(?:\s+(?:GROUP|HAVING|ORDER|LIMIT)|$)',
            query,
            re.IGNORECASE | re.DOTALL
        )

        if where_match:
            conditions_str = where_match.group(1).strip()
            # ANDで分割
            conditions = re.split(r'\s+AND\s+', conditions_str, flags=re.IGNORECASE)
            return [c.strip() for c in conditions if c.strip()]

        return []

    def _extract_limit(self, query: str) -> tuple[bool, Optional[int]]:
        """LIMIT句を抽出"""
        limit_match = re.search(r'\bLIMIT\s+(\d+)', query, re.IGNORECASE)
        if limit_match:
            return True, int(limit_match.group(1))
        return False, None

    def _extract_order_by(self, query: str) -> tuple[bool, List[str]]:
        """ORDER BY句を抽出"""
        order_match = re.search(
            r'\bORDER\s+BY\s+(.+?)(?=\s+LIMIT|$)',
            query,
            re.IGNORECASE
        )

        if order_match:
            columns = [c.strip() for c in order_match.group(1).split(',')]
            return True, columns

        return False, []

    def _uses_select_star(self, query: str) -> bool:
        """SELECT *の使用を確認"""
        return bool(re.search(r'\bSELECT\s+\*', query, re.IGNORECASE))

    def _count_selected_columns(self, query: str) -> Optional[int]:
        """選択カラム数をカウント"""
        select_match = re.search(
            r'\bSELECT\s+(.+?)\s+FROM',
            query,
            re.IGNORECASE
        )

        if select_match:
            columns_str = select_match.group(1)
            # 簡易的なカウント（関数内のカンマは無視できない）
            columns = [c.strip() for c in columns_str.split(',')]
            return len(columns)

        return None

    def _has_index_hint(self, query: str) -> bool:
        """インデックスヒントの有無を確認"""
        return bool(re.search(
            r'\b(USE|FORCE|IGNORE)\s+INDEX',
            query,
            re.IGNORECASE
        ))

    def _has_subquery(self, query: str) -> bool:
        """サブクエリの有無を確認"""
        # SELECT が2回以上出現
        return len(re.findall(r'\bSELECT\b', query, re.IGNORECASE)) > 1

    def _is_sql_query(self, text: str) -> bool:
        """SQL クエリかどうかを判定"""
        sql_keywords = {
            'SELECT', 'INSERT', 'UPDATE', 'DELETE',
            'CREATE', 'ALTER', 'DROP', 'TRUNCATE'
        }

        text_upper = text.strip().upper()
        return any(text_upper.startswith(keyword) for keyword in sql_keywords)

    def _find_variable_value(
        self,
        tree: javalang.tree.CompilationUnit,
        variable_name: str,
        code: str
    ) -> Optional[str]:
        """変数の値を検索"""
        for path, node in tree.filter(javalang.tree.VariableDeclarator):
            if node.name == variable_name and node.initializer:
                return self._extract_string_value(node.initializer)

        return None

    def _extract_string_value(self, node) -> Optional[str]:
        """ノードから文字列値を抽出（連結対応）"""
        if isinstance(node, javalang.tree.Literal):
            # 単一のリテラル文字列
            return node.value.strip('"')
        elif isinstance(node, javalang.tree.BinaryOperation) and node.operator == '+':
            # 文字列連結を処理
            left = self._extract_string_value(node.operandl)
            right = self._extract_string_value(node.operandr)
            if left is not None and right is not None:
                return left + right
        return None

    def _get_line_number(self, node, lines: List[str]) -> int:
        """ノードの行番号を取得"""
        if hasattr(node, 'position') and node.position:
            return node.position.line
        return 1

    def _get_context_info(self, path) -> tuple[Optional[str], Optional[str]]:
        """メソッド名とクラス名を取得"""
        method_name = None
        class_name = None

        for node in path:
            if isinstance(node, javalang.tree.MethodDeclaration):
                method_name = node.name
            elif isinstance(node, javalang.tree.ClassDeclaration):
                class_name = node.name

        return method_name, class_name

    def _get_class_name(self, path) -> Optional[str]:
        """クラス名を取得"""
        for node in path:
            if isinstance(node, javalang.tree.ClassDeclaration):
                return node.name
        return None

    def _check_if_in_loop(self, path) -> tuple[bool, Optional[str]]:
        """ループ内かどうかをチェック"""
        for node in path:
            if isinstance(node, javalang.tree.ForStatement):
                return True, 'for'
            elif isinstance(node, javalang.tree.WhileStatement):
                return True, 'while'
            elif isinstance(node, javalang.tree.DoStatement):
                return True, 'do-while'

        return False, None

    def _extract_annotation_value(
        self,
        annotation: javalang.tree.Annotation,
        code: str
    ) -> Optional[str]:
        """アノテーションから値を抽出"""
        if not annotation.element:
            return None

        # 単一値
        if isinstance(annotation.element, javalang.tree.Literal):
            return annotation.element.value.strip('"')

        # 名前付きパラメータ
        elif isinstance(annotation.element, list):
            for elem in annotation.element:
                if isinstance(elem, tuple) and elem[0] == 'value':
                    if isinstance(elem[1], javalang.tree.Literal):
                        return elem[1].value.strip('"')

        return None
