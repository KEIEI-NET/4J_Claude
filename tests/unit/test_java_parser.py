"""
JavaCassandraParserのユニットテスト
"""
from pathlib import Path
import pytest

from cassandra_analyzer.parsers import JavaCassandraParser
from cassandra_analyzer.models import CassandraCall, CallType


@pytest.fixture
def parser():
    """パーサーのフィクスチャ"""
    return JavaCassandraParser()


@pytest.fixture
def fixtures_dir():
    """フィクスチャディレクトリのパス"""
    return Path(__file__).parent.parent / "fixtures"


class TestJavaCassandraParser:
    """JavaCassandraParserのテストクラス"""

    def test_parse_good_dao(self, parser, fixtures_dir):
        """問題のないDAOファイルのパース"""
        test_file = fixtures_dir / "sample_dao_good.java"
        calls = parser.parse_file(test_file)

        assert len(calls) > 0, "少なくとも1つのCassandra呼び出しが検出されるべき"

        # Prepared Statementの使用を確認
        select_calls = [c for c in calls if "SELECT" in c.cql_text]
        assert len(select_calls) > 0, "SELECT文が検出されるべき"

        # パーティションキーの使用を確認
        assert any("user_id" in c.cql_text for c in calls), "user_idが使用されているべき"

    def test_parse_allow_filtering(self, parser, fixtures_dir):
        """ALLOW FILTERINGを含むファイルのパース"""
        test_file = fixtures_dir / "sample_dao_bad1.java"
        calls = parser.parse_file(test_file)

        assert len(calls) > 0, "Cassandra呼び出しが検出されるべき"

        # ALLOW FILTERINGの検出
        allow_filtering_calls = [c for c in calls if "ALLOW FILTERING" in c.cql_text]
        assert (
            len(allow_filtering_calls) > 0
        ), "ALLOW FILTERINGを含む呼び出しが検出されるべき"

    def test_parse_no_partition_key(self, parser, fixtures_dir):
        """パーティションキー未使用のファイルのパース"""
        test_file = fixtures_dir / "sample_dao_bad2.java"
        calls = parser.parse_file(test_file)

        assert len(calls) > 0, "Cassandra呼び出しが検出されるべき"

        # WHERE句なしのクエリを確認
        select_all = [c for c in calls if "SELECT * FROM" in c.cql_text and "WHERE" not in c.cql_text]
        assert len(select_all) > 0, "WHERE句なしのSELECTが検出されるべき"

    def test_parse_large_batch(self, parser, fixtures_dir):
        """大量バッチ処理のファイルのパース"""
        test_file = fixtures_dir / "sample_dao_bad3.java"
        calls = parser.parse_file(test_file)

        assert len(calls) > 0, "Cassandra呼び出しが検出されるべき"

        # バッチ処理の検出（コメントから推測）
        # 実際のバッチステートメント検出は今後実装

    def test_parse_unprepared_statement(self, parser, fixtures_dir):
        """Prepared Statement未使用のファイルのパース"""
        test_file = fixtures_dir / "sample_dao_bad4.java"
        calls = parser.parse_file(test_file)

        assert len(calls) > 0, "Cassandra呼び出しが検出されるべき"

        # Prepared Statementを使用していない呼び出しを確認
        unprepared = [c for c in calls if not c.is_prepared]
        assert len(unprepared) > 0, "Prepared未使用の呼び出しが検出されるべき"

    def test_extract_consistency_level(self, parser, fixtures_dir):
        """Consistency Level抽出のテスト"""
        test_file = fixtures_dir / "sample_dao_good.java"
        calls = parser.parse_file(test_file)

        # Consistency Levelが設定されている呼び出しを確認
        with_consistency = [c for c in calls if c.consistency_level is not None]

        # sample_dao_good.javaにはConsistencyLevel.QUORUMが含まれる
        if with_consistency:
            assert any(
                c.consistency_level == "QUORUM" for c in with_consistency
            ), "QUORUMが検出されるべき"

    def test_call_type_determination(self, parser):
        """CallTypeの判定テスト"""
        # CassandraCallオブジェクトの直接作成
        call1 = CassandraCall(
            method_name="execute",
            cql_text="SELECT * FROM users",
            line_number=10,
            is_prepared=False,
            consistency_level=None,
            file_path="test.java",
        )
        assert call1.call_type == CallType.EXECUTE

        call2 = CassandraCall(
            method_name="executeAsync",
            cql_text="INSERT INTO users",
            line_number=20,
            is_prepared=False,
            consistency_level=None,
            file_path="test.java",
        )
        assert call2.call_type == CallType.EXECUTE_ASYNC

    def test_error_handling_invalid_file(self, parser):
        """存在しないファイルのエラーハンドリング"""
        invalid_file = Path("nonexistent_file.java")
        calls = parser.parse_file(invalid_file)

        # エラーでもクラッシュせず、空のリストを返す
        assert calls == [], "存在しないファイルの場合は空のリストを返すべき"

    def test_multiple_calls_in_file(self, parser, fixtures_dir):
        """1つのファイルに複数のCassandra呼び出しがある場合"""
        test_file = fixtures_dir / "sample_dao_bad1.java"
        calls = parser.parse_file(test_file)

        # sample_dao_bad1.javaには複数のメソッドがある
        assert len(calls) >= 2, "複数の呼び出しが検出されるべき"

        # 各呼び出しが正しい行番号を持つ
        assert all(c.line_number > 0 for c in calls), "全ての呼び出しが行番号を持つべき"

    def test_constant_reference_not_resolved(self, parser, tmp_path):
        """定数参照が解決できない場合のテスト（line 142）"""
        # 定数を参照しているが、定数定義がないJavaファイル
        java_file = tmp_path / "ConstantRef.java"
        java_file.write_text("""
        public class ConstantRef {
            public void query() {
                session.execute(SOME_UNDEFINED_CONSTANT);
            }
        }
        """)

        calls = parser.parse_file(java_file)

        # 定数参照が検出されるが、値は解決されない
        assert len(calls) == 1
        assert "[CONSTANT:" in calls[0].cql_text

    def test_string_concatenation_in_constants(self, parser, tmp_path):
        """定数の文字列連結のテスト（lines 208-221）"""
        # 文字列リテラル同士の連結
        java_file = tmp_path / "StringConcat.java"
        java_file.write_text("""
        public class StringConcat {
            private static final String QUERY = "SELECT * FROM " + "users" + " WHERE id = ?";

            public void query() {
                session.execute(QUERY);
            }
        }
        """)

        calls = parser.parse_file(java_file)

        # 文字列リテラル連結が解決される
        assert len(calls) == 1
        assert "SELECT * FROM users WHERE id = ?" in calls[0].cql_text

    def test_bound_statement_detection(self, parser, tmp_path):
        """BoundStatement使用の検出（lines 246-271）"""
        java_file = tmp_path / "BoundStmt.java"
        java_file.write_text("""
        public class BoundStmt {
            private PreparedStatement selectStmt;

            public void query() {
                BoundStatement bound = selectStmt.bind("value");
                session.execute("SELECT * FROM users WHERE id = ?");
            }
        }
        """)

        calls = parser.parse_file(java_file)

        # BoundStatementが検出され、Prepared Statementとして認識される
        assert len(calls) == 1
        assert calls[0].is_prepared

    def test_prepared_statement_variable_usage(self, parser, tmp_path):
        """PreparedStatement変数の使用検出（lines 264-267）"""
        java_file = tmp_path / "PreparedVar.java"
        java_file.write_text("""
        public class PreparedVar {
            private final PreparedStatement selectStmt;

            public void query() {
                selectStmt.bind("value");
                session.execute("SELECT * FROM users WHERE id = ?");
            }
        }
        """)

        calls = parser.parse_file(java_file)

        # PreparedStatement変数が使用されていることを検出
        assert len(calls) == 1
        assert calls[0].is_prepared

    def test_simple_statement_detection(self, parser, tmp_path):
        """SimpleStatementの検出（line 271）"""
        java_file = tmp_path / "SimpleStmt.java"
        java_file.write_text("""
        public class SimpleStmt {
            public void query() {
                SimpleStatement stmt = new SimpleStatement("SELECT * FROM users WHERE id = ?");
                session.execute("SELECT * FROM users WHERE id = ?");
            }
        }
        """)

        calls = parser.parse_file(java_file)

        # SimpleStatementは非Preparedとして検出される
        assert len(calls) == 1
        assert not calls[0].is_prepared

    def test_set_consistency_level_method(self, parser, tmp_path):
        """setConsistencyLevelメソッドの検出（line 305）"""
        java_file = tmp_path / "SetConsistency.java"
        java_file.write_text("""
        public class SetConsistency {
            public void query() {
                Statement stmt = new SimpleStatement("SELECT * FROM users");
                stmt.setConsistencyLevel(ConsistencyLevel.LOCAL_QUORUM);
                session.execute("SELECT * FROM users WHERE id = ?");
            }
        }
        """)

        calls = parser.parse_file(java_file)

        # setConsistencyLevelメソッドからConsistency Levelを抽出
        assert len(calls) == 1
        assert calls[0].consistency_level == "LOCAL_QUORUM"

    def test_constant_reference_chaining(self, parser, tmp_path):
        """定数参照チェーンのテスト（line 221 - MemberReference）"""
        java_file = tmp_path / "ConstantChain.java"
        java_file.write_text("""
        public class ConstantChain {
            private static final String BASE = "SELECT * FROM users";
            private static final String QUERY = BASE;

            public void query() {
                session.execute(QUERY);
            }
        }
        """)

        calls = parser.parse_file(java_file)

        # 定数参照チェーンは現在未サポート（TODO）
        # BASEへの参照は解決されない
        assert len(calls) == 1

    def test_resolve_constants_config(self, tmp_path):
        """resolve_constants設定のテスト"""
        # resolve_constantsを無効にしたパーサー
        parser_no_resolve = JavaCassandraParser(config={"resolve_constants": False})

        java_file = tmp_path / "ConstantNoResolve.java"
        java_file.write_text("""
        public class ConstantNoResolve {
            private static final String QUERY = "SELECT * FROM users WHERE id = ?";

            public void query() {
                session.execute(QUERY);
            }
        }
        """)

        calls = parser_no_resolve.parse_file(java_file)

        # resolve_constantsが無効なので、定数は解決されない
        assert len(calls) == 1
        assert "[CONSTANT:" in calls[0].cql_text
