"""
Tests for MySQL Models
"""

import pytest
from multidb_analyzer.mysql.models import (
    MySQLQuery,
    SQLOperation,
    JoinType,
    JoinInfo,
    IndexHint,
    TableReference
)


class TestTableReference:
    """TableReferenceクラスのテスト"""

    def test_table_reference_basic(self):
        """基本的なテーブル参照"""
        table = TableReference(name="users")
        assert table.name == "users"
        assert table.alias is None
        assert table.schema is None
        assert str(table) == "users"

    def test_table_reference_with_alias(self):
        """エイリアス付きテーブル参照"""
        table = TableReference(name="users", alias="u")
        assert str(table) == "users AS u"

    def test_table_reference_with_schema(self):
        """スキーマ付きテーブル参照"""
        table = TableReference(name="users", schema="public")
        assert str(table) == "public.users"

    def test_table_reference_full(self):
        """スキーマとエイリアス両方"""
        table = TableReference(name="users", schema="public", alias="u")
        assert str(table) == "public.users AS u"


class TestJoinInfo:
    """JoinInfoクラスのテスト"""

    def test_join_info_creation(self):
        """JOIN情報の作成"""
        table = TableReference(name="orders", alias="o")
        join = JoinInfo(
            join_type=JoinType.INNER,
            table=table,
            condition="o.user_id = u.id",
            line_number=10
        )

        assert join.join_type == JoinType.INNER
        assert join.table.name == "orders"
        assert join.condition == "o.user_id = u.id"
        assert join.line_number == 10


class TestIndexHint:
    """IndexHintクラスのテスト"""

    def test_index_hint_use(self):
        """USEインデックスヒント"""
        hint = IndexHint(hint_type="USE", index_names=["idx_user_id"])
        assert hint.hint_type == "USE"
        assert "idx_user_id" in hint.index_names

    def test_index_hint_multiple(self):
        """複数インデックス"""
        hint = IndexHint(
            hint_type="FORCE",
            index_names=["idx_user_id", "idx_created_at"]
        )
        assert len(hint.index_names) == 2


class TestMySQLQuery:
    """MySQLQueryクラスのテスト"""

    def test_simple_select_query(self):
        """シンプルなSELECTクエリ"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[table],
            query_text="SELECT * FROM users",
            file_path="UserDao.java",
            line_number=42
        )

        assert query.operation == SQLOperation.SELECT
        assert len(query.tables) == 1
        assert query.file_path == "UserDao.java"
        assert query.line_number == 42
        assert not query.is_in_loop
        assert not query.has_joins()
        assert query.is_simple_query()

    def test_query_with_where_conditions(self):
        """WHERE条件付きクエリ"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[table],
            query_text="SELECT * FROM users WHERE status = 'active'",
            file_path="UserDao.java",
            line_number=42,
            where_conditions=["status = 'active'"]
        )

        assert len(query.where_conditions) == 1
        assert "status = 'active'" in query.where_conditions

    def test_query_in_loop(self):
        """ループ内のクエリ"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[table],
            query_text="SELECT * FROM users WHERE id = ?",
            file_path="UserDao.java",
            line_number=42,
            is_in_loop=True,
            loop_type="for"
        )

        assert query.is_in_loop
        assert query.loop_type == "for"
        assert not query.is_simple_query()

    def test_query_with_joins(self):
        """JOIN付きクエリ"""
        users_table = TableReference(name="users", alias="u")
        orders_table = TableReference(name="orders", alias="o")

        join = JoinInfo(
            join_type=JoinType.INNER,
            table=orders_table,
            condition="o.user_id = u.id",
            line_number=42
        )

        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[users_table],
            query_text="SELECT * FROM users u INNER JOIN orders o ON o.user_id = u.id",
            file_path="UserDao.java",
            line_number=42,
            joins=[join]
        )

        assert query.has_joins()
        assert len(query.joins) == 1
        assert query.joins[0].join_type == JoinType.INNER
        assert not query.is_simple_query()

    def test_get_main_table(self):
        """メインテーブルの取得"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[table],
            query_text="SELECT * FROM users",
            file_path="UserDao.java",
            line_number=42
        )

        main_table = query.get_main_table()
        assert main_table is not None
        assert main_table.name == "users"

    def test_get_main_table_empty(self):
        """テーブルなしの場合"""
        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[],
            query_text="SELECT 1",
            file_path="UserDao.java",
            line_number=42
        )

        assert query.get_main_table() is None

    def test_get_all_tables(self):
        """全テーブルの取得（JOIN含む）"""
        users_table = TableReference(name="users", alias="u")
        orders_table = TableReference(name="orders", alias="o")
        items_table = TableReference(name="order_items", alias="oi")

        join1 = JoinInfo(
            join_type=JoinType.INNER,
            table=orders_table,
            condition="o.user_id = u.id",
            line_number=42
        )

        join2 = JoinInfo(
            join_type=JoinType.LEFT,
            table=items_table,
            condition="oi.order_id = o.id",
            line_number=43
        )

        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[users_table],
            query_text="SELECT * FROM users u INNER JOIN orders o...",
            file_path="UserDao.java",
            line_number=42,
            joins=[join1, join2]
        )

        all_tables = query.get_all_tables()
        assert len(all_tables) == 3
        assert all_tables[0].name == "users"
        assert all_tables[1].name == "orders"
        assert all_tables[2].name == "order_items"

    def test_query_with_limit(self):
        """LIMIT付きクエリ"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[table],
            query_text="SELECT * FROM users LIMIT 10",
            file_path="UserDao.java",
            line_number=42,
            has_limit=True,
            limit_value=10
        )

        assert query.has_limit
        assert query.limit_value == 10

    def test_query_with_order_by(self):
        """ORDER BY付きクエリ"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[table],
            query_text="SELECT * FROM users ORDER BY created_at DESC",
            file_path="UserDao.java",
            line_number=42,
            has_order_by=True,
            order_by_columns=["created_at DESC"]
        )

        assert query.has_order_by
        assert len(query.order_by_columns) == 1
        assert "created_at DESC" in query.order_by_columns

    def test_query_with_select_star(self):
        """SELECT *のクエリ"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[table],
            query_text="SELECT * FROM users",
            file_path="UserDao.java",
            line_number=42,
            uses_select_star=True
        )

        assert query.uses_select_star
        assert query.column_count is None

    def test_query_with_specific_columns(self):
        """特定カラム選択のクエリ"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[table],
            query_text="SELECT id, name, email FROM users",
            file_path="UserDao.java",
            line_number=42,
            uses_select_star=False,
            column_count=3
        )

        assert not query.uses_select_star
        assert query.column_count == 3

    def test_query_with_subquery(self):
        """サブクエリ付きクエリ"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[table],
            query_text="SELECT * FROM users WHERE id IN (SELECT user_id FROM orders)",
            file_path="UserDao.java",
            line_number=42,
            has_subquery=True
        )

        assert query.has_subquery
        assert not query.is_simple_query()

    def test_query_with_index_hint(self):
        """インデックスヒント付きクエリ"""
        table = TableReference(name="users")
        hint = IndexHint(hint_type="USE", index_names=["idx_status"])

        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[table],
            query_text="SELECT * FROM users USE INDEX (idx_status) WHERE status = 'active'",
            file_path="UserDao.java",
            line_number=42,
            has_index_hint=True,
            index_hints=[hint]
        )

        assert query.has_index_hint
        assert len(query.index_hints) == 1
        assert query.index_hints[0].hint_type == "USE"

    def test_query_to_dict(self):
        """辞書変換"""
        table = TableReference(name="users", alias="u")
        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[table],
            query_text="SELECT * FROM users u",
            file_path="UserDao.java",
            line_number=42,
            method_name="findAll",
            class_name="UserDao"
        )

        query_dict = query.to_dict()

        assert query_dict['operation'] == "SELECT"
        assert query_dict['file_path'] == "UserDao.java"
        assert query_dict['line_number'] == 42
        assert query_dict['method_name'] == "findAll"
        assert query_dict['class_name'] == "UserDao"
        assert query_dict['has_joins'] is False
        assert query_dict['join_count'] == 0

    def test_query_str_representation(self):
        """文字列表現"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[table],
            query_text="SELECT * FROM users",
            file_path="UserDao.java",
            line_number=42
        )

        str_repr = str(query)
        assert "SELECT" in str_repr
        assert "users" in str_repr
        assert "UserDao.java:42" in str_repr

    def test_insert_query(self):
        """INSERTクエリ"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.INSERT,
            tables=[table],
            query_text="INSERT INTO users (name, email) VALUES (?, ?)",
            file_path="UserDao.java",
            line_number=42
        )

        assert query.operation == SQLOperation.INSERT
        assert query.get_main_table().name == "users"

    def test_update_query(self):
        """UPDATEクエリ"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.UPDATE,
            tables=[table],
            query_text="UPDATE users SET status = 'inactive' WHERE id = ?",
            file_path="UserDao.java",
            line_number=42
        )

        assert query.operation == SQLOperation.UPDATE

    def test_delete_query(self):
        """DELETEクエリ"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.DELETE,
            tables=[table],
            query_text="DELETE FROM users WHERE id = ?",
            file_path="UserDao.java",
            line_number=42
        )

        assert query.operation == SQLOperation.DELETE

    def test_query_with_metadata(self):
        """メタデータ付きクエリ"""
        table = TableReference(name="users")
        query = MySQLQuery(
            operation=SQLOperation.SELECT,
            tables=[table],
            query_text="SELECT * FROM users",
            file_path="UserDao.java",
            line_number=42,
            metadata={
                'framework': 'MyBatis',
                'annotation': '@Select'
            }
        )

        assert 'framework' in query.metadata
        assert query.metadata['framework'] == 'MyBatis'
