"""
Phase 2 Data Models
"""

import sys
from pathlib import Path

# Phase 1のパスを追加
phase1_src = Path(__file__).parent.parent.parent.parent.parent / "phase1_cassandra" / "src"
if phase1_src.exists() and str(phase1_src) not in sys.path:
    sys.path.insert(0, str(phase1_src))

from .confidence import AnalysisConfidence

# Phase 1からIssueをインポート（再エクスポート用）
try:
    from cassandra_analyzer.models.issue import Issue as Phase1Issue
except ImportError:
    # フォールバック: 直接パスからインポート
    import importlib.util
    issue_path = phase1_src / "cassandra_analyzer" / "models" / "issue.py"
    spec = importlib.util.spec_from_file_location("issue", issue_path)
    issue_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(issue_module)
    Phase1Issue = issue_module.Issue

# Phase 1のIssueをこのパッケージからも利用可能にする
Issue = Phase1Issue

__all__ = [
    "AnalysisConfidence",
    "Issue",  # Phase 1から再エクスポート
]
