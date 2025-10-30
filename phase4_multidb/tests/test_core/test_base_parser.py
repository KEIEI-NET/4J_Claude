"""
Tests for Base Parser

基底パーサーのテスト
"""

import pytest
from pathlib import Path
from multidb_analyzer.core.base_parser import (
    BaseParser,
    DatabaseType,
    QueryType,
    ParsedQuery,
    JavaParserMixin,
    PythonParserMixin
)


class DummyParser(BaseParser):
    """テスト用のダミーパーサー"""

    def get_db_type(self) -> DatabaseType:
        return DatabaseType.ELASTICSEARCH

    def parse_file(self, file_path: Path):
        # テスト用: ファイル名に "error" が含まれていたらエラー
        if "error" in file_path.name.lower():
            raise ValueError("Test error")

        return [
            ParsedQuery(
                query_type=QueryType.SEARCH,
                query_text="test query",
                file_path=str(file_path),
                line_number=1
            )
        ]

    def can_parse(self, file_path: Path) -> bool:
        # .txtファイルのみ解析可能とする
        return file_path.suffix == '.txt'


class TestParsedQuery:
    """ParsedQuery のテスト"""

    def test_create_parsed_query(self):
        """ParsedQueryの作成テスト"""
        query = ParsedQuery(
            query_type=QueryType.SEARCH,
            query_text="SELECT * FROM table",
            file_path="/path/to/file.sql",
            line_number=10
        )

        assert query.query_type == QueryType.SEARCH
        assert query.query_text == "SELECT * FROM table"
        assert query.file_path == "/path/to/file.sql"
        assert query.line_number == 10
        assert query.parameters == {}
        assert query.metadata == {}

    def test_parsed_query_with_optional_fields(self):
        """オプションフィールド付きParseQueryの作成"""
        query = ParsedQuery(
            query_type=QueryType.INSERT,
            query_text="INSERT INTO table VALUES (?)",
            file_path="/path/to/file.java",
            line_number=20,
            method_name="insertData",
            class_name="DataService",
            parameters={'arg0': 'value'},
            metadata={'db': 'test'}
        )

        assert query.method_name == "insertData"
        assert query.class_name == "DataService"
        assert query.parameters == {'arg0': 'value'}
        assert query.metadata == {'db': 'test'}


class TestBaseParser:
    """BaseParser のテスト"""

    @pytest.fixture
    def parser(self):
        """ダミーパーサーを作成"""
        return DummyParser()

    @pytest.fixture
    def test_directory(self, tmp_path):
        """テスト用ディレクトリを作成"""
        # 複数のファイルを作成
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        (tmp_path / "file3.java").write_text("java content")  # 解析対象外
        (tmp_path / "error.txt").write_text("error content")  # エラーを発生させる

        # サブディレクトリ
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file4.txt").write_text("content4")

        return tmp_path

    def test_parse_directory_non_recursive(self, parser, test_directory):
        """非再帰的ディレクトリ解析のテスト"""
        queries = parser.parse_directory(test_directory, recursive=False)

        # file1.txt, file2.txt, error.txt（エラーでスキップ）
        # error.txtはエラーになるがcatchされる
        assert len(queries) >= 2

    def test_parse_directory_recursive(self, parser, test_directory):
        """再帰的ディレクトリ解析のテスト"""
        queries = parser.parse_directory(test_directory, recursive=True)

        # サブディレクトリのファイルも含まれる
        assert len(queries) >= 3

    def test_parse_directory_with_file_extensions(self, parser, test_directory):
        """ファイル拡張子フィルタリングのテスト"""
        queries = parser.parse_directory(
            test_directory,
            recursive=True,
            file_extensions=['.txt']
        )

        # .txtファイルのみ
        assert len(queries) >= 2
        for query in queries:
            assert '.txt' in query.file_path

    def test_parse_directory_error_handling(self, parser, test_directory):
        """エラーハンドリングのテスト"""
        # error.txtでエラーが発生するが、他のファイルは処理される
        queries = parser.parse_directory(test_directory)

        # エラーファイルは除外されるが他は処理される
        assert len(queries) >= 2

    def test_get_statistics(self, parser):
        """統計情報取得のテスト"""
        # いくつかクエリを追加
        parser._queries = [
            ParsedQuery(QueryType.SEARCH, "query1", "file1.txt", 1),
            ParsedQuery(QueryType.SEARCH, "query2", "file1.txt", 2),
            ParsedQuery(QueryType.INSERT, "query3", "file2.txt", 1),
        ]

        stats = parser.get_statistics()

        assert stats['total_queries'] == 3
        assert stats['query_types']['search'] == 2
        assert stats['query_types']['insert'] == 1
        assert stats['db_type'] == DatabaseType.ELASTICSEARCH.value

    def test_clear_cache(self, parser):
        """キャッシュクリアのテスト"""
        parser._queries = [
            ParsedQuery(QueryType.SEARCH, "query1", "file1.txt", 1),
        ]

        assert len(parser._queries) == 1

        parser.clear_cache()

        assert len(parser._queries) == 0


class TestJavaParserMixin:
    """JavaParserMixin のテスト"""

    class DummyJavaParser(JavaParserMixin):
        """テスト用Javaパーサー"""
        pass

    @pytest.fixture
    def java_parser(self):
        """Javaパーサーミックスインを作成"""
        return self.DummyJavaParser()

    def test_is_java_file(self, java_parser, tmp_path):
        """Javaファイル判定のテスト"""
        java_file = tmp_path / "Test.java"
        python_file = tmp_path / "test.py"

        java_file.touch()
        python_file.touch()

        assert java_parser._is_java_file(java_file) is True
        assert java_parser._is_java_file(python_file) is False

    def test_read_java_file_utf8(self, java_parser, tmp_path):
        """UTF-8 Javaファイル読み込みのテスト"""
        java_file = tmp_path / "Test.java"
        content = "public class Test { /* 日本語コメント */ }"
        java_file.write_text(content, encoding='utf-8')

        read_content = java_parser._read_java_file(java_file)
        assert read_content == content

    def test_read_java_file_latin1_fallback(self, java_parser, tmp_path):
        """Latin-1フォールバック読み込みのテスト"""
        java_file = tmp_path / "Test.java"
        content = b"public class Test { }"  # Latin-1でエンコード
        java_file.write_bytes(content)

        read_content = java_parser._read_java_file(java_file)
        assert "public class Test" in read_content

    def test_extract_string_literal(self, java_parser):
        """文字列リテラル抽出のテスト"""
        class DummyNode:
            def __init__(self, value):
                self.value = value

        node = DummyNode("test string")
        result = java_parser._extract_string_literal(node)
        assert result == "test string"

    def test_extract_string_literal_no_value(self, java_parser):
        """値なしノードからの抽出テスト"""
        class DummyNode:
            pass

        node = DummyNode()
        result = java_parser._extract_string_literal(node)
        assert result is None


class TestPythonParserMixin:
    """PythonParserMixin のテスト"""

    class DummyPythonParser(PythonParserMixin):
        """テスト用Pythonパーサー"""
        pass

    @pytest.fixture
    def python_parser(self):
        """Pythonパーサーミックスインを作成"""
        return self.DummyPythonParser()

    def test_is_python_file(self, python_parser, tmp_path):
        """Pythonファイル判定のテスト"""
        python_file = tmp_path / "test.py"
        java_file = tmp_path / "Test.java"

        python_file.touch()
        java_file.touch()

        assert python_parser._is_python_file(python_file) is True
        assert python_parser._is_python_file(java_file) is False

    def test_read_python_file(self, python_parser, tmp_path):
        """Pythonファイル読み込みのテスト"""
        python_file = tmp_path / "test.py"
        content = "def hello():\n    print('Hello, World!')"
        python_file.write_text(content, encoding='utf-8')

        read_content = python_parser._read_python_file(python_file)
        assert read_content == content


# Additional tests for BaseParser coverage improvement (16-24)

class TestBaseParserAbstractMethods:
    """Test abstract method requirements"""

    def test_cannot_instantiate_without_implementing_abstract_methods(self):
        """Test that BaseParser cannot be instantiated without implementing abstract methods"""
        # Trying to instantiate a class that doesn't implement all abstract methods
        with pytest.raises(TypeError):
            class IncompleteParser(BaseParser):
                # Missing get_db_type, parse_file, can_parse
                pass

            IncompleteParser()

    def test_must_implement_get_db_type(self):
        """Test that get_db_type must be implemented"""
        with pytest.raises(TypeError):
            class NoGetDbTypeParser(BaseParser):
                # Missing get_db_type
                def parse_file(self, file_path: Path):
                    return []

                def can_parse(self, file_path: Path) -> bool:
                    return True

            NoGetDbTypeParser()

    def test_must_implement_parse_file(self):
        """Test that parse_file must be implemented"""
        with pytest.raises(TypeError):
            class NoParseFileParser(BaseParser):
                def get_db_type(self) -> DatabaseType:
                    return DatabaseType.ELASTICSEARCH
                # Missing parse_file

                def can_parse(self, file_path: Path) -> bool:
                    return True

            NoParseFileParser()

    def test_must_implement_can_parse(self):
        """Test that can_parse must be implemented"""
        with pytest.raises(TypeError):
            class NoCanParseParser(BaseParser):
                def get_db_type(self) -> DatabaseType:
                    return DatabaseType.ELASTICSEARCH

                def parse_file(self, file_path: Path):
                    return []
                # Missing can_parse

            NoCanParseParser()


class TestJavaParserMixinAdvanced:
    """Advanced tests for JavaParserMixin"""

    class DummyJavaParser(JavaParserMixin):
        """Test Java parser"""
        pass

    @pytest.fixture
    def java_parser(self):
        """Create Java parser mixin"""
        return self.DummyJavaParser()

    def test_read_java_file_unicode_decode_error_fallback(self, java_parser, tmp_path):
        """Test Latin-1 fallback when UnicodeDecodeError occurs"""
        java_file = tmp_path / "BadEncoding.java"
        # Write bytes that are invalid UTF-8 but valid Latin-1
        # 0xFF is invalid in UTF-8 but valid in Latin-1
        content = b"public class Test { // \xFF\xFE invalid UTF-8 }"
        java_file.write_bytes(content)

        # Should fall back to latin-1 and succeed
        read_content = java_parser._read_java_file(java_file)
        assert "public class Test" in read_content
        assert isinstance(read_content, str)

    def test_get_method_name_with_parent_attribute(self, java_parser):
        """Test _get_method_name with parent attribute (fallback logic)"""
        # Create mock nodes with parent attribute
        class MockMethodNode:
            def __init__(self, name):
                self.name = name
                self.parameters = []
                self.parent = None

        class MockNode:
            def __init__(self):
                self.parent = MockMethodNode("testMethod")

        node = MockNode()
        # Call without path (None) to trigger fallback logic
        result = java_parser._get_method_name(node, path=None)
        assert result == "testMethod"

    def test_get_method_name_no_parent(self, java_parser):
        """Test _get_method_name when no parent found"""
        class MockNode:
            def __init__(self):
                self.parent = None

        node = MockNode()
        result = java_parser._get_method_name(node, path=None)
        assert result is None

    def test_get_method_name_with_chain_of_parents(self, java_parser):
        """Test _get_method_name with multiple parent nodes"""
        class MockMethodNode:
            def __init__(self):
                self.name = "foundMethod"
                self.parameters = []
                self.parent = None

        class MockIntermediateNode:
            def __init__(self):
                self.parent = MockMethodNode()

        class MockNode:
            def __init__(self):
                self.parent = MockIntermediateNode()

        node = MockNode()
        result = java_parser._get_method_name(node, path=None)
        assert result == "foundMethod"

    def test_get_class_name_with_parent_attribute(self, java_parser):
        """Test _get_class_name with parent attribute (fallback logic)"""
        # Create mock nodes with parent attribute
        class MockClassNode:
            def __init__(self, name):
                self.name = name
                self.body = []
                self.parent = None

        class MockNode:
            def __init__(self):
                self.parent = MockClassNode("TestClass")

        node = MockNode()
        # Call without path (None) to trigger fallback logic
        result = java_parser._get_class_name(node, path=None)
        assert result == "TestClass"

    def test_get_class_name_no_parent(self, java_parser):
        """Test _get_class_name when no parent found"""
        class MockNode:
            def __init__(self):
                self.parent = None

        node = MockNode()
        result = java_parser._get_class_name(node, path=None)
        assert result is None

    def test_get_class_name_with_chain_of_parents(self, java_parser):
        """Test _get_class_name with multiple parent nodes"""
        class MockClassNode:
            def __init__(self):
                self.name = "FoundClass"
                self.body = []
                self.parent = None

        class MockIntermediateNode:
            def __init__(self):
                self.parent = MockClassNode()

        class MockNode:
            def __init__(self):
                self.parent = MockIntermediateNode()

        node = MockNode()
        result = java_parser._get_class_name(node, path=None)
        assert result == "FoundClass"

    def test_get_method_name_with_empty_path(self, java_parser):
        """Test _get_method_name with empty path (branch 228->233)"""
        class MockNode:
            def __init__(self):
                self.name = "fallbackMethod"
                self.parameters = []
                self.parent = None

        node = MockNode()
        # Pass empty list as path - should trigger fallback logic
        result = java_parser._get_method_name(node, path=[])
        assert result == "fallbackMethod"

    def test_get_method_name_with_non_method_path(self, java_parser):
        """Test _get_method_name with path containing no MethodDeclaration"""
        import javalang

        class MockNode:
            def __init__(self):
                self.name = "fallbackMethod"
                self.parameters = []
                self.parent = None

        # Create path with non-MethodDeclaration nodes
        class_node = javalang.tree.ClassDeclaration(name="TestClass")
        node = MockNode()

        # Path contains only ClassDeclaration, no MethodDeclaration
        result = java_parser._get_method_name(node, path=[class_node])
        assert result == "fallbackMethod"

    def test_get_class_name_with_empty_path(self, java_parser):
        """Test _get_class_name with empty path (branch 255->260)"""
        class MockNode:
            def __init__(self):
                self.name = "FallbackClass"
                self.body = []
                self.parent = None

        node = MockNode()
        # Pass empty list as path - should trigger fallback logic
        result = java_parser._get_class_name(node, path=[])
        assert result == "FallbackClass"

    def test_get_class_name_with_non_class_path(self, java_parser):
        """Test _get_class_name with path containing no ClassDeclaration"""
        import javalang

        class MockNode:
            def __init__(self):
                self.name = "FallbackClass"
                self.body = []
                self.parent = None

        # Create path with non-ClassDeclaration nodes
        method_node = javalang.tree.MethodDeclaration(name="testMethod")
        node = MockNode()

        # Path contains only MethodDeclaration, no ClassDeclaration
        result = java_parser._get_class_name(node, path=[method_node])
        assert result == "FallbackClass"
