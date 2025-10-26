"""
Base parserのユニットテスト
"""
import pytest
from typing import List

from cassandra_analyzer.parsers.base import BaseParser
from cassandra_analyzer.models import CassandraCall


class ConcreteParser(BaseParser):
    """テスト用の具象パーサー"""

    def parse_file(self, file_path: str) -> List[CassandraCall]:
        """
        parse_fileの実装

        Args:
            file_path: ファイルパス

        Returns:
            空のリスト
        """
        # ここで親クラスのpass文を通過させる
        super().parse_file(file_path)
        return []


class TestBaseParser:
    """BaseParserのテストクラス"""

    def test_initialization_without_config(self):
        """設定なしでの初期化"""
        parser = ConcreteParser()
        assert parser.config == {}

    def test_initialization_with_config(self):
        """設定ありでの初期化"""
        config = {"key": "value", "timeout": 30}
        parser = ConcreteParser(config=config)
        assert parser.config == config
        assert parser.config["key"] == "value"
        assert parser.config["timeout"] == 30

    def test_initialization_with_none_config(self):
        """Noneの設定での初期化"""
        parser = ConcreteParser(config=None)
        assert parser.config == {}

    def test_parse_file_abstract_method(self):
        """抽象メソッドの実装をテスト"""
        parser = ConcreteParser()
        result = parser.parse_file("test.java")

        # 抽象メソッドが実装されていることを確認
        assert isinstance(result, list)
        assert len(result) == 0

    def test_cannot_instantiate_base_parser_directly(self):
        """BaseParser自体はインスタンス化できないことを確認"""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseParser()
