"""
パーサーファクトリー

設定に基づいて適切なパーサーを生成
"""
from typing import Dict, Any, Optional
from .base import BaseParser
from .java_parser import JavaCassandraParser
from .ast_parser import ASTJavaParser


class ParserFactory:
    """
    パーサーファクトリー

    設定に基づいて適切なパーサーインスタンスを生成
    """

    # 利用可能なパーサータイプ
    PARSER_TYPES = {
        "regex": JavaCassandraParser,
        "ast": ASTJavaParser,
    }

    @staticmethod
    def create_parser(
        parser_type: str = "regex",
        config: Optional[Dict[str, Any]] = None,
    ) -> BaseParser:
        """
        パーサーを生成

        Args:
            parser_type: パーサータイプ（"regex" または "ast"）
            config: パーサー設定

        Returns:
            パーサーインスタンス

        Raises:
            ValueError: 無効なパーサータイプの場合
        """
        if parser_type not in ParserFactory.PARSER_TYPES:
            raise ValueError(
                f"Unknown parser type: {parser_type}. "
                f"Available types: {list(ParserFactory.PARSER_TYPES.keys())}"
            )

        parser_class = ParserFactory.PARSER_TYPES[parser_type]
        return parser_class(config=config)

    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> BaseParser:
        """
        設定辞書からパーサーを生成

        Args:
            config: 設定辞書
                {
                    "parser": {
                        "type": "regex" or "ast",
                        ...other parser configs...
                    }
                }

        Returns:
            パーサーインスタンス
        """
        parser_config = config.get("parser", {})
        parser_type = parser_config.get("type", "regex")
        parser_specific_config = parser_config.get("config", {})

        return ParserFactory.create_parser(
            parser_type=parser_type,
            config=parser_specific_config,
        )

    @staticmethod
    def get_available_parsers() -> Dict[str, str]:
        """
        利用可能なパーサーのリストを取得

        Returns:
            パーサータイプと説明の辞書
        """
        return {
            "regex": "Regular expression-based Java parser (fast, Phase 1)",
            "ast": "AST-based Java parser (accurate, Phase 2)",
        }
