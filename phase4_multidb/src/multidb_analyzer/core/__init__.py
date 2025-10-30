"""
Core Framework for Multi-Database Analyzer

すべてのDBアナライザーの基底となるフレームワーク

このモジュールは以下を提供します:
- BaseParser: すべてのDBパーサーの抽象基底クラス
- BaseDetector: すべての検出器の抽象基底クラス
- PluginManager: プラグインアーキテクチャの管理
- 共通データ型とEnum

使用例:
```python
from multidb_analyzer.core import (
    BaseParser,
    BaseDetector,
    DatabaseType,
    QueryType,
    ParsedQuery,
    Issue,
    Severity,
    IssueCategory,
    PluginManager,
    get_plugin_manager
)

# プラグインマネージャーの取得
manager = get_plugin_manager()

# プラグインの登録
from multidb_analyzer.elasticsearch.parsers import ElasticsearchJavaParser
from multidb_analyzer.elasticsearch.detectors import (
    WildcardDetector,
    ScriptQueryDetector
)

manager.register_plugin(
    db_type=DatabaseType.ELASTICSEARCH,
    parser=ElasticsearchJavaParser(),
    detectors=[WildcardDetector(), ScriptQueryDetector()]
)

# ファイルの解析
issues = manager.analyze_file(
    Path("SearchService.java"),
    db_type=DatabaseType.ELASTICSEARCH
)

# 結果の表示
for issue in issues:
    print(f"{issue.severity}: {issue.title}")
```
"""

from multidb_analyzer.core.base_parser import (
    BaseParser,
    DatabaseType,
    QueryType,
    ParsedQuery,
    JavaParserMixin,
    PythonParserMixin,
)
from multidb_analyzer.core.base_detector import (
    BaseDetector,
    Issue,
    Severity,
    IssueCategory,
    DetectorRegistry,
)
from multidb_analyzer.core.plugin_manager import (
    DatabasePlugin,
    PluginManager,
    get_plugin_manager,
)

__all__ = [
    # Parser
    'BaseParser',
    'DatabaseType',
    'QueryType',
    'ParsedQuery',
    'JavaParserMixin',
    'PythonParserMixin',
    # Detector
    'BaseDetector',
    'Issue',
    'Severity',
    'IssueCategory',
    'DetectorRegistry',
    # Plugin Manager
    'DatabasePlugin',
    'PluginManager',
    'get_plugin_manager',
]
