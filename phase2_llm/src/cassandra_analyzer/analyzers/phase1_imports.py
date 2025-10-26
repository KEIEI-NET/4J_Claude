"""
Phase 1 コンポーネントのインポートヘルパー

Phase 1とPhase 2の名前空間衝突を解決するための専用モジュール
"""

import sys
from pathlib import Path

# Phase 1のパスを設定
_current_file = Path(__file__)
phase1_path = _current_file.parent.parent.parent.parent.parent / "phase1_cassandra" / "src"
phase1_path_resolved = phase1_path.resolve()

# Phase 2のパスを一時的に退避し、Phase 1のパスを最優先にする
_phase2_paths = [p for p in sys.path if "phase2_llm" in p]
_cached_phase2_modules = {}

# sys.pathからPhase 2を一時削除
for p in _phase2_paths:
    if p in sys.path:
        sys.path.remove(p)

# sys.modulesからPhase 2のcassandra_analyzerモジュールを一時退避
# これによりPhase 1のモジュールが優先的にロードされる
for key in list(sys.modules.keys()):
    if key.startswith('cassandra_analyzer'):
        module = sys.modules[key]
        if hasattr(module, '__file__') and module.__file__ and 'phase2_llm' in module.__file__:
            _cached_phase2_modules[key] = sys.modules.pop(key)

# Phase 1のパスを最優先に追加
if phase1_path_resolved.exists() and str(phase1_path_resolved) not in sys.path:
    sys.path.insert(0, str(phase1_path_resolved))

# Phase 1からインポート（Phase 1のモジュールがsys.modulesにロードされる）
from cassandra_analyzer.parsers.java_parser import JavaCassandraParser
from cassandra_analyzer.detectors import (
    AllowFilteringDetector,
    PartitionKeyDetector,
    BatchSizeDetector,
    PreparedStatementDetector,
)
from cassandra_analyzer.llm.anthropic_client import AnthropicClient
from cassandra_analyzer.llm.llm_analyzer import LLMAnalyzer

# Phase 1のパーサー/検出器/LLMモジュールをsys.modulesから退避
# (これらは上記のローカル変数に保持されている)
_phase1_modules_to_keep = {}
for key in ['cassandra_analyzer.parsers.java_parser',
            'cassandra_analyzer.parsers',
            'cassandra_analyzer.detectors',
            'cassandra_analyzer.detectors.allow_filtering',
            'cassandra_analyzer.detectors.partition_key',
            'cassandra_analyzer.detectors.batch_size',
            'cassandra_analyzer.detectors.prepared_statement',
            'cassandra_analyzer.detectors.base',
            'cassandra_analyzer.llm',
            'cassandra_analyzer.llm.anthropic_client',
            'cassandra_analyzer.llm.llm_analyzer']:
    if key in sys.modules:
        _phase1_modules_to_keep[key] = sys.modules[key]

# Phase 2のパスを復元
for p in _phase2_paths:
    if p not in sys.path:
        sys.path.insert(0, p)

# Phase 2のモジュールを復元
for key, module in _cached_phase2_modules.items():
    sys.modules[key] = module

# Phase 1のモジュールを sys.modules に保持
# (Phase 2が同名モジュールをロードしても、Phase 1の方が使われるようにする)
for key, module in _phase1_modules_to_keep.items():
    sys.modules[key] = module

# エクスポート
__all__ = [
    "JavaCassandraParser",
    "AllowFilteringDetector",
    "PartitionKeyDetector",
    "BatchSizeDetector",
    "PreparedStatementDetector",
    "AnthropicClient",
    "LLMAnalyzer",
]
