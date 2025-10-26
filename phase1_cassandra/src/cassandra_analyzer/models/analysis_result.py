"""
分析結果全体を表すモデル
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime

from .issue import Issue


@dataclass
class AnalysisResult:
    """
    分析結果

    Attributes:
        analyzed_files: 分析したファイルのリスト
        total_issues: 検出された問題の総数
        issues_by_severity: 重要度別の問題数
        issues: 検出された問題のリスト
        analysis_time: 分析にかかった時間（秒）
        timestamp: 分析実行時刻
    """

    analyzed_files: List[str]
    total_issues: int
    issues_by_severity: Dict[str, int]
    issues: List[Issue] = field(default_factory=list)
    analysis_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def total_files(self) -> int:
        """分析したファイルの総数"""
        return len(self.analyzed_files)

    @property
    def files_analyzed(self) -> List[str]:
        """分析したファイルのリスト（エイリアス）"""
        return self.analyzed_files

    @property
    def total_calls(self) -> int:
        """Cassandra呼び出しの総数（問題数と同じ）"""
        return self.total_issues

    @property
    def critical_count(self) -> int:
        """Critical問題の数"""
        return self.issues_by_severity.get("critical", 0)

    @property
    def high_count(self) -> int:
        """High問題の数"""
        return self.issues_by_severity.get("high", 0)

    @property
    def medium_count(self) -> int:
        """Medium問題の数"""
        return self.issues_by_severity.get("medium", 0)

    @property
    def low_count(self) -> int:
        """Low問題の数"""
        return self.issues_by_severity.get("low", 0)

    def to_dict(self) -> Dict[str, Any]:
        """
        辞書形式に変換

        Returns:
            分析結果の辞書
        """
        return {
            "analyzed_files": self.analyzed_files,
            "total_issues": self.total_issues,
            "issues_by_severity": self.issues_by_severity,
            "issues": [issue.to_dict() for issue in self.issues],
            "analysis_time_seconds": self.analysis_time,
            "timestamp": self.timestamp,
        }

    def get_critical_issues(self) -> List[Issue]:
        """
        Critical問題のみを取得

        Returns:
            Critical問題のリスト
        """
        return [issue for issue in self.issues if issue.severity == "critical"]

    def get_high_issues(self) -> List[Issue]:
        """
        High問題のみを取得

        Returns:
            High問題のリスト
        """
        return [issue for issue in self.issues if issue.severity == "high"]

    def get_issues_by_file(self) -> Dict[str, List[Issue]]:
        """
        ファイル別に問題をグループ化

        Returns:
            ファイルパスをキーとした問題のリスト
        """
        issues_by_file: Dict[str, List[Issue]] = {}
        for issue in self.issues:
            if issue.file_path not in issues_by_file:
                issues_by_file[issue.file_path] = []
            issues_by_file[issue.file_path].append(issue)
        return issues_by_file

    def get_issues_by_type(self) -> Dict[str, List[Issue]]:
        """
        問題タイプ別にグループ化

        Returns:
            問題タイプをキーとした問題のリスト
        """
        issues_by_type: Dict[str, List[Issue]] = {}
        for issue in self.issues:
            if issue.issue_type not in issues_by_type:
                issues_by_type[issue.issue_type] = []
            issues_by_type[issue.issue_type].append(issue)
        return issues_by_type
