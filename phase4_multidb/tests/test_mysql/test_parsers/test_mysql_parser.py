"""
Tests for MySQL Parser
"""

import pytest
from pathlib import Path
from multidb_analyzer.mysql.parsers import MySQLParser
from multidb_analyzer.mysql.models import SQLOperation, JoinType


class TestMySQLParserBasics:
    """MySQL Parserの基本機能テスト"""

    @pytest.fixture
    def parser(self):
        """パーサーインスタンス"""
        return MySQLParser()

    def test_parser_initialization(self, parser):
        """パーサーの初期化"""
        assert parser is not None
        assert 'Statement' in parser.jdbc_classes
        assert 'executeQuery' in parser.sql_execution_methods

    def test_parse_empty_file(self, parser, tmp_path):
        """空のファイルの解析"""
        file_path = tmp_path / "Empty.java"
        file_path.write_text("public class Empty {}")

        queries = parser.parse_file(file_path)
        assert queries == []

    def test_parse_syntax_error(self, parser, tmp_path):
        """構文エラーのあるファイル"""
        file_path = tmp_path / "Invalid.java"
        file_path.write_text("public class Invalid { this is not valid java }")

        queries = parser.parse_file(file_path)
        assert queries == []  # エラーでも空リスト返却


class TestJDBCQueryExtraction:
    """JDBCクエリ抽出のテスト"""

    @pytest.fixture
    def parser(self):
        return MySQLParser()

    def test_simple_select_query(self, parser, tmp_path):
        """シンプルなSELECTクエリ"""
        code = '''
        public class UserDao {
            public List<User> findAll() {
                String sql = "SELECT * FROM users";
                return statement.executeQuery(sql);
            }
        }
        '''
        file_path = tmp_path / "UserDao.java"
        file_path.write_text(code)

        queries = parser.parse_file(file_path, code)

        assert len(queries) == 1
        assert queries[0].operation == SQLOperation.SELECT
        assert queries[0].query_text == "SELECT * FROM users"
        assert len(queries[0].tables) >= 1
        assert queries[0].method_name == "findAll"

    def test_select_with_where(self, parser, tmp_path):
        """WHERE句付きSELECT"""
        code = '''
        public class UserDao {
            public User findById(Long id) {
                String sql = "SELECT * FROM users WHERE id = ?";
                return statement.executeQuery(sql);
            }
        }
        '''
        file_path = tmp_path / "UserDao.java"
        file_path.write_text(code)

        queries = parser.parse_file(file_path, code)

        assert len(queries) == 1
        query = queries[0]
        assert query.operation == SQLOperation.SELECT
        assert len(query.where_conditions) > 0

    def test_insert_query(self, parser, tmp_path):
        """INSERTクエリ"""
        code = '''
        public class UserDao {
            public void insert(User user) {
                String sql = "INSERT INTO users (name, email) VALUES (?, ?)";
                statement.executeUpdate(sql);
            }
        }
        '''
        file_path = tmp_path / "UserDao.java"
        file_path.write_text(code)

        queries = parser.parse_file(file_path, code)

        assert len(queries) == 1
        assert queries[0].operation == SQLOperation.INSERT

    def test_update_query(self, parser, tmp_path):
        """UPDATEクエリ"""
        code = '''
        public class UserDao {
            public void update(User user) {
                String sql = "UPDATE users SET name = ?, email = ? WHERE id = ?";
                statement.executeUpdate(sql);
            }
        }
        '''
        file_path = tmp_path / "UserDao.java"
        file_path.write_text(code)

        queries = parser.parse_file(file_path, code)

        assert len(queries) == 1
        assert queries[0].operation == SQLOperation.UPDATE

    def test_delete_query(self, parser, tmp_path):
        """DELETEクエリ"""
        code = '''
        public class UserDao {
            public void delete(Long id) {
                String sql = "DELETE FROM users WHERE id = ?";
                statement.executeUpdate(sql);
            }
        }
        '''
        file_path = tmp_path / "UserDao.java"
        file_path.write_text(code)

        queries = parser.parse_file(file_path, code)

        assert len(queries) == 1
        assert queries[0].operation == SQLOperation.DELETE


class TestJoinExtraction:
    """JOIN抽出のテスト"""

    @pytest.fixture
    def parser(self):
        return MySQLParser()

    def test_inner_join(self, parser, tmp_path):
        """INNER JOIN"""
        code = '''
        public class OrderDao {
            public List<Order> findWithUser() {
                String sql = "SELECT * FROM orders o INNER JOIN users u ON o.user_id = u.id";
                return statement.executeQuery(sql);
            }
        }
        '''
        file_path = tmp_path / "OrderDao.java"
        file_path.write_text(code)

        queries = parser.parse_file(file_path, code)

        assert len(queries) == 1
        query = queries[0]
        assert query.has_joins()
        assert len(query.joins) == 1
        assert query.joins[0].join_type == JoinType.INNER

    def test_left_join(self, parser, tmp_path):
        """LEFT JOIN"""
        code = '''
        public class OrderDao {
            public List<Order> findAll() {
                String sql = "SELECT * FROM orders o LEFT JOIN users u ON o.user_id = u.id";
                return statement.executeQuery(sql);
            }
        }
        '''
        file_path = tmp_path / "OrderDao.java"
        file_path.write_text(code)

        queries = parser.parse_file(file_path, code)

        assert len(queries) == 1
        assert queries[0].joins[0].join_type == JoinType.LEFT

    def test_multiple_joins(self, parser, tmp_path):
        """複数のJOIN"""
        code = '''
        public class OrderDao {
            public List<Order> findComplete() {
                String sql = "SELECT * FROM orders o " +
                    "INNER JOIN users u ON o.user_id = u.id " +
                    "LEFT JOIN order_items oi ON oi.order_id = o.id";
                return statement.executeQuery(sql);
            }
        }
        '''
        file_path = tmp_path / "OrderDao.java"
        file_path.write_text(code)

        queries = parser.parse_file(file_path, code)

        assert len(queries) == 1
        query = queries[0]
        assert len(query.joins) == 2


class TestLoopDetection:
    """ループ検出のテスト"""

    @pytest.fixture
    def parser(self):
        return MySQLParser()

    def test_query_in_for_loop(self, parser, tmp_path):
        """forループ内のクエリ"""
        code = '''
        public class UserDao {
            public void processUsers(List<Long> ids) {
                for (Long id : ids) {
                    String sql = "SELECT * FROM users WHERE id = ?";
                    statement.executeQuery(sql);
                }
            }
        }
        '''
        file_path = tmp_path / "UserDao.java"
        file_path.write_text(code)

        queries = parser.parse_file(file_path, code)

        assert len(queries) == 1
        query = queries[0]
        assert query.is_in_loop
        assert query.loop_type == "for"

    def test_query_in_while_loop(self, parser, tmp_path):
        """whileループ内のクエリ"""
        code = '''
        public class UserDao {
            public void processUsers() {
                while (iterator.hasNext()) {
                    String sql = "SELECT * FROM users WHERE id = ?";
                    statement.executeQuery(sql);
                }
            }
        }
        '''
        file_path = tmp_path / "UserDao.java"
        file_path.write_text(code)

        queries = parser.parse_file(file_path, code)

        assert len(queries) == 1
        assert queries[0].is_in_loop
        assert queries[0].loop_type == "while"

    def test_query_outside_loop(self, parser, tmp_path):
        """ループ外のクエリ"""
        code = '''
        public class UserDao {
            public List<User> findAll() {
                String sql = "SELECT * FROM users";
                return statement.executeQuery(sql);
            }
        }
        '''
        file_path = tmp_path / "UserDao.java"
        file_path.write_text(code)

        queries = parser.parse_file(file_path, code)

        assert len(queries) == 1
        assert not queries[0].is_in_loop


class TestMyBatisAnnotations:
    """MyBatisアノテーションのテスト"""

    @pytest.fixture
    def parser(self):
        return MySQLParser()

    def test_select_annotation(self, parser, tmp_path):
        """@Selectアノテーション"""
        code = '''
        public interface UserMapper {
            @Select("SELECT * FROM users WHERE id = #{id}")
            User findById(Long id);
        }
        '''
        file_path = tmp_path / "UserMapper.java"
        file_path.write_text(code)

        queries = parser.parse_file(file_path, code)

        assert len(queries) == 1
        assert queries[0].operation == SQLOperation.SELECT
        assert queries[0].method_name == "findById"

    def test_insert_annotation(self, parser, tmp_path):
        """@Insertアノテーション"""
        code = '''
        public interface UserMapper {
            @Insert("INSERT INTO users (name, email) VALUES (#{name}, #{email})")
            void insert(User user);
        }
        '''
        file_path = tmp_path / "UserMapper.java"
        file_path.write_text(code)

        queries = parser.parse_file(file_path, code)

        assert len(queries) == 1
        assert queries[0].operation == SQLOperation.INSERT


class TestSpringDataJPA:
    """Spring Data JPAのテスト"""

    @pytest.fixture
    def parser(self):
        return MySQLParser()

    def test_query_annotation(self, parser, tmp_path):
        """@Queryアノテーション"""
        code = '''
        public interface UserRepository extends JpaRepository<User, Long> {
            @Query("SELECT u FROM User u WHERE u.status = ?1")
            List<User> findByStatus(String status);
        }
        '''
        file_path = tmp_path / "UserRepository.java"
        file_path.write_text(code)

        queries = parser.parse_file(file_path, code)

        assert len(queries) == 1
        assert queries[0].method_name == "findByStatus"


class TestQueryAnalysis:
    """クエリ解析のテスト"""

    @pytest.fixture
    def parser(self):
        return MySQLParser()

    def test_select_star_detection(self, parser, tmp_path):
        """SELECT *の検出"""
        code = '''
        public class UserDao {
            public List<User> findAll() {
                String sql = "SELECT * FROM users";
                return statement.executeQuery(sql);
            }
        }
        '''
        file_path = tmp_path / "UserDao.java"
        file_path.write_text(code)

        queries = parser.parse_file(file_path, code)

        assert len(queries) == 1
        assert queries[0].uses_select_star

    def test_specific_columns(self, parser, tmp_path):
        """特定カラム選択の検出"""
        code = '''
        public class UserDao {
            public List<User> findAll() {
                String sql = "SELECT id, name, email FROM users";
                return statement.executeQuery(sql);
            }
        }
        '''
        file_path = tmp_path / "UserDao.java"
        file_path.write_text(code)

        queries = parser.parse_file(file_path, code)

        assert len(queries) == 1
        query = queries[0]
        assert not query.uses_select_star
        assert query.column_count == 3

    def test_limit_detection(self, parser, tmp_path):
        """LIMIT句の検出"""
        code = '''
        public class UserDao {
            public List<User> findTop10() {
                String sql = "SELECT * FROM users LIMIT 10";
                return statement.executeQuery(sql);
            }
        }
        '''
        file_path = tmp_path / "UserDao.java"
        file_path.write_text(code)

        queries = parser.parse_file(file_path, code)

        assert len(queries) == 1
        query = queries[0]
        assert query.has_limit
        assert query.limit_value == 10

    def test_order_by_detection(self, parser, tmp_path):
        """ORDER BY句の検出"""
        code = '''
        public class UserDao {
            public List<User> findAllOrdered() {
                String sql = "SELECT * FROM users ORDER BY created_at DESC";
                return statement.executeQuery(sql);
            }
        }
        '''
        file_path = tmp_path / "UserDao.java"
        file_path.write_text(code)

        queries = parser.parse_file(file_path, code)

        assert len(queries) == 1
        query = queries[0]
        assert query.has_order_by
        assert len(query.order_by_columns) > 0

    def test_subquery_detection(self, parser, tmp_path):
        """サブクエリの検出"""
        code = '''
        public class UserDao {
            public List<User> findActive() {
                String sql = "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders)";
                return statement.executeQuery(sql);
            }
        }
        '''
        file_path = tmp_path / "UserDao.java"
        file_path.write_text(code)

        queries = parser.parse_file(file_path, code)

        assert len(queries) == 1
        assert queries[0].has_subquery

    def test_index_hint_detection(self, parser, tmp_path):
        """インデックスヒントの検出"""
        code = '''
        public class UserDao {
            public List<User> findWithHint() {
                String sql = "SELECT * FROM users USE INDEX (idx_status) WHERE status = 'active'";
                return statement.executeQuery(sql);
            }
        }
        '''
        file_path = tmp_path / "UserDao.java"
        file_path.write_text(code)

        queries = parser.parse_file(file_path, code)

        assert len(queries) == 1
        assert queries[0].has_index_hint


class TestTableExtraction:
    """テーブル抽出のテスト"""

    @pytest.fixture
    def parser(self):
        return MySQLParser()

    def test_single_table(self, parser, tmp_path):
        """単一テーブル"""
        code = '''
        public class UserDao {
            public List<User> findAll() {
                String sql = "SELECT * FROM users";
                return statement.executeQuery(sql);
            }
        }
        '''
        file_path = tmp_path / "UserDao.java"
        file_path.write_text(code)

        queries = parser.parse_file(file_path, code)

        assert len(queries) == 1
        query = queries[0]
        assert len(query.tables) == 1
        assert query.tables[0].name == "users"

    def test_table_with_alias(self, parser, tmp_path):
        """エイリアス付きテーブル"""
        code = '''
        public class UserDao {
            public List<User> findAll() {
                String sql = "SELECT * FROM users u WHERE u.status = 'active'";
                return statement.executeQuery(sql);
            }
        }
        '''
        file_path = tmp_path / "UserDao.java"
        file_path.write_text(code)

        queries = parser.parse_file(file_path, code)

        assert len(queries) == 1
        query = queries[0]
        assert query.tables[0].name == "users"
        # エイリアスの検出は実装依存

    def test_schema_qualified_table(self, parser, tmp_path):
        """スキーマ付きテーブル"""
        code = '''
        public class UserDao {
            public List<User> findAll() {
                String sql = "SELECT * FROM public.users";
                return statement.executeQuery(sql);
            }
        }
        '''
        file_path = tmp_path / "UserDao.java"
        file_path.write_text(code)

        queries = parser.parse_file(file_path, code)

        assert len(queries) == 1
        # スキーマ付きテーブルの解析


class TestComplexQueries:
    """複雑なクエリのテスト"""

    @pytest.fixture
    def parser(self):
        return MySQLParser()

    def test_complex_join_query(self, parser, tmp_path):
        """複雑なJOINクエリ"""
        code = '''
        public class OrderDao {
            public List<Order> findCompleteOrders() {
                String sql = "SELECT o.*, u.name, oi.quantity " +
                    "FROM orders o " +
                    "INNER JOIN users u ON o.user_id = u.id " +
                    "LEFT JOIN order_items oi ON oi.order_id = o.id " +
                    "WHERE o.status = 'completed' " +
                    "ORDER BY o.created_at DESC " +
                    "LIMIT 100";
                return statement.executeQuery(sql);
            }
        }
        '''
        file_path = tmp_path / "OrderDao.java"
        file_path.write_text(code)

        queries = parser.parse_file(file_path, code)

        assert len(queries) == 1
        query = queries[0]
        assert query.has_joins()
        assert len(query.joins) == 2
        assert len(query.where_conditions) > 0
        assert query.has_order_by
        assert query.has_limit
        assert query.limit_value == 100
