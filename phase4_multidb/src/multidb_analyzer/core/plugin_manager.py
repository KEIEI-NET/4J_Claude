"""
Plugin Manager for Multi-Database Analyzer

DBプラグインを管理するマネージャー
"""

from typing import Dict, List, Optional, Type, Any
from pathlib import Path

from .base_parser import BaseParser, DatabaseType
from .base_detector import BaseDetector, Issue, DetectorRegistry


class DatabasePlugin:
    """
    データベースプラグイン

    各DBごとのパーサーと検出器をまとめる
    """

    def __init__(
        self,
        db_type: DatabaseType,
        parser: BaseParser,
        detectors: List[BaseDetector]
    ):
        """
        プラグインの初期化

        Args:
            db_type: データベースタイプ
            parser: パーサー
            detectors: 検出器のリスト
        """
        self.db_type = db_type
        self.parser = parser
        self.detector_registry = DetectorRegistry()

        # 検出器を登録
        for detector in detectors:
            self.detector_registry.register(detector)

    def analyze_file(self, file_path: Path) -> List[Issue]:
        """
        ファイルを解析して問題を検出

        Args:
            file_path: 解析するファイル

        Returns:
            検出された問題のリスト
        """
        # パース
        queries = self.parser.parse_file(file_path)

        # 問題検出
        issues = self.detector_registry.run_all(queries)

        return issues

    def analyze_directory(
        self,
        directory: Path,
        recursive: bool = True
    ) -> List[Issue]:
        """
        ディレクトリを解析して問題を検出

        Args:
            directory: 解析するディレクトリ
            recursive: 再帰的に解析するか

        Returns:
            検出された問題のリスト
        """
        # パース
        queries = self.parser.parse_directory(directory, recursive=recursive)

        # 問題検出
        issues = self.detector_registry.run_all(queries)

        return issues


class PluginManager:
    """
    プラグインマネージャー

    すべてのDBプラグインを管理し、統一されたインターフェースを提供
    """

    def __init__(self):
        self._plugins: Dict[DatabaseType, DatabasePlugin] = {}

    def register_plugin(
        self,
        db_type: DatabaseType,
        parser: BaseParser,
        detectors: List[BaseDetector]
    ):
        """
        プラグインを登録

        Args:
            db_type: データベースタイプ
            parser: パーサー
            detectors: 検出器のリスト
        """
        plugin = DatabasePlugin(db_type, parser, detectors)
        self._plugins[db_type] = plugin

    def get_plugin(self, db_type: DatabaseType) -> Optional[DatabasePlugin]:
        """
        プラグインを取得

        Args:
            db_type: データベースタイプ

        Returns:
            プラグイン（見つからない場合None）
        """
        return self._plugins.get(db_type)

    def get_all_plugins(self) -> List[DatabasePlugin]:
        """
        すべてのプラグインを取得

        Returns:
            プラグインのリスト
        """
        return list(self._plugins.values())

    def analyze_file(
        self,
        file_path: Path,
        db_type: Optional[DatabaseType] = None
    ) -> List[Issue]:
        """
        ファイルを解析

        Args:
            file_path: 解析するファイル
            db_type: データベースタイプ（Noneの場合は自動判定）

        Returns:
            検出された問題のリスト
        """
        if db_type is not None:
            # 指定されたDBタイプで解析
            plugin = self.get_plugin(db_type)
            if plugin is None:
                raise ValueError(f"No plugin registered for {db_type.value}")
            return plugin.analyze_file(file_path)

        # 自動判定: すべてのプラグインを試す
        all_issues = []
        for plugin in self.get_all_plugins():
            if plugin.parser.can_parse(file_path):
                issues = plugin.analyze_file(file_path)
                all_issues.extend(issues)

        return all_issues

    def analyze_directory(
        self,
        directory: Path,
        db_types: Optional[List[DatabaseType]] = None,
        recursive: bool = True
    ) -> Dict[DatabaseType, List[Issue]]:
        """
        ディレクトリを解析

        Args:
            directory: 解析するディレクトリ
            db_types: データベースタイプのリスト（Noneの場合はすべて）
            recursive: 再帰的に解析するか

        Returns:
            DB毎の検出された問題のマップ
        """
        results = {}

        if db_types is None:
            # すべてのプラグインで解析
            plugins = self.get_all_plugins()
        else:
            # 指定されたDBタイプのみ
            plugins = [self.get_plugin(dt) for dt in db_types]
            plugins = [p for p in plugins if p is not None]

        for plugin in plugins:
            issues = plugin.analyze_directory(directory, recursive=recursive)
            results[plugin.db_type] = issues

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """
        統計情報を取得

        Returns:
            統計情報
        """
        stats = {
            "total_plugins": len(self._plugins),
            "supported_databases": [dt.value for dt in self._plugins.keys()],
            "plugins": {}
        }

        for db_type, plugin in self._plugins.items():
            plugin_stats = {
                "parser": plugin.parser.__class__.__name__,
                "detectors": [d.get_name() for d in plugin.detector_registry.get_all_detectors()],
                "detector_count": len(plugin.detector_registry.get_all_detectors())
            }
            stats["plugins"][db_type.value] = plugin_stats

        return stats


# グローバルプラグインマネージャー
_global_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """
    グローバルプラグインマネージャーを取得

    Returns:
        プラグインマネージャー
    """
    global _global_plugin_manager
    if _global_plugin_manager is None:
        _global_plugin_manager = PluginManager()
    return _global_plugin_manager


def register_plugin(
    db_type: DatabaseType,
    parser: BaseParser,
    detectors: List[BaseDetector]
):
    """
    グローバルプラグインマネージャーにプラグインを登録

    Args:
        db_type: データベースタイプ
        parser: パーサー
        detectors: 検出器のリスト
    """
    manager = get_plugin_manager()
    manager.register_plugin(db_type, parser, detectors)
