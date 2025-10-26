"""
Pytest configuration for Phase 2
"""

import sys
from pathlib import Path

def pytest_configure(config):
    """pytest起動時の設定"""
    # Phase 1のsrcディレクトリをsys.pathに追加
    phase1_src = Path(__file__).parent.parent / "phase1_cassandra" / "src"
    phase1_src_resolved = phase1_src.resolve()
    if phase1_src_resolved.exists():
        sys.path.insert(0, str(phase1_src_resolved))
        print(f"[Phase 2 Test] Added to sys.path: {phase1_src_resolved}")

    # Phase 2のsrcディレクトリをsys.pathに追加
    phase2_src = Path(__file__).parent / "src"
    phase2_src_resolved = phase2_src.resolve()
    if phase2_src_resolved.exists():
        sys.path.insert(0, str(phase2_src_resolved))
        print(f"[Phase 2 Test] Added to sys.path: {phase2_src_resolved}")

    # デバッグ: sys.pathの最初の5エントリを表示
    print(f"[Phase 2 Test] sys.path (first 5): {sys.path[:5]}")

# モジュールレベルでも設定（テストインポート時に実行）
phase1_src = Path(__file__).parent.parent / "phase1_cassandra" / "src"
phase1_src_resolved = phase1_src.resolve()
if phase1_src_resolved.exists() and str(phase1_src_resolved) not in sys.path:
    sys.path.insert(0, str(phase1_src_resolved))

phase2_src = Path(__file__).parent / "src"
phase2_src_resolved = phase2_src.resolve()
if phase2_src_resolved.exists() and str(phase2_src_resolved) not in sys.path:
    sys.path.insert(0, str(phase2_src_resolved))
