"""
Pytest configuration for Phase 2
"""

import sys
from pathlib import Path

# Phase 1のsrcディレクトリをsys.pathに追加
phase1_src = Path(__file__).parent.parent / "phase1_cassandra" / "src"
if phase1_src.exists() and str(phase1_src) not in sys.path:
    sys.path.insert(0, str(phase1_src))

# Phase 2のsrcディレクトリをsys.pathに追加
phase2_src = Path(__file__).parent / "src"
if phase2_src.exists() and str(phase2_src) not in sys.path:
    sys.path.insert(0, str(phase2_src))
