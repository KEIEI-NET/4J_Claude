"""
Analysis Result Data Structure

統合分析結果のデータ構造
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import defaultdict

from multidb_analyzer.core.base_detector import Issue, Severity, IssueCategory


@dataclass
class AnalysisResult:
    """
    統合分析結果

    複数のDB分析エンジンからの結果を統合して保持します。

    Attributes:
        timestamp: 分析実行時刻
        total_files: 検出された総ファイル数
        analyzed_files: 実際に分析されたファイル数
        execution_time: 実行時間（秒）
        issues: 検出された全問題のリスト
        issues_by_severity: 重大度別の問題マップ
        issues_by_category: カテゴリ別の問題マップ
        issues_by_db_type: DBタイプ別の問題マップ
        total_issues: 総問題数
        critical_count: CRITICAL問題数
        high_count: HIGH問題数
        medium_count: MEDIUM問題数
        low_count: LOW問題数
        config: 分析設定
        warnings: 警告メッセージリスト
        errors: エラーメッセージリスト
    """

    # 基本情報
    timestamp: datetime
    total_files: int
    analyzed_files: int
    execution_time: float

    # 問題情報
    issues: List[Issue] = field(default_factory=list)
    issues_by_severity: Dict[Severity, List[Issue]] = field(default_factory=dict)
    issues_by_category: Dict[IssueCategory, List[Issue]] = field(default_factory=dict)
    issues_by_db_type: Dict[str, List[Issue]] = field(default_factory=dict)

    # 統計情報
    total_issues: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0

    # メタデータ
    config: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def __post_init__(self):
        """初期化後処理 - 統計を自動計算"""
        if self.issues:
            self._calculate_statistics()

    def _calculate_statistics(self):
        """統計情報を計算"""
        # 総問題数
        self.total_issues = len(self.issues)

        # 重大度別カウント
        self.critical_count = sum(1 for i in self.issues if i.severity == Severity.CRITICAL)
        self.high_count = sum(1 for i in self.issues if i.severity == Severity.HIGH)
        self.medium_count = sum(1 for i in self.issues if i.severity == Severity.MEDIUM)
        self.low_count = sum(1 for i in self.issues if i.severity == Severity.LOW)

        # 重大度別マップ
        self.issues_by_severity = defaultdict(list)
        for issue in self.issues:
            self.issues_by_severity[issue.severity].append(issue)

        # カテゴリ別マップ
        self.issues_by_category = defaultdict(list)
        for issue in self.issues:
            self.issues_by_category[issue.category].append(issue)

        # DBタイプ別マップ（detector名から推測）
        self.issues_by_db_type = defaultdict(list)
        for issue in self.issues:
            db_type = self._infer_db_type(issue.detector_name)
            self.issues_by_db_type[db_type].append(issue)

    def _infer_db_type(self, detector_name: str) -> str:
        """検出器名からDBタイプを推測"""
        detector_lower = detector_name.lower()

        if any(kw in detector_lower for kw in ['elastic', 'es', 'mapping', 'shard', 'wildcard', 'script']):
            return 'elasticsearch'
        elif any(kw in detector_lower for kw in ['mysql', 'nplus', 'scan', 'index', 'join']):
            return 'mysql'
        elif 'llm' in detector_lower:
            return 'llm'
        else:
            return 'unknown'

    def to_dict(self) -> Dict[str, Any]:
        """
        辞書形式に変換

        Returns:
            分析結果の辞書表現
        """
        return {
            'metadata': {
                'timestamp': self.timestamp.isoformat(),
                'execution_time': self.execution_time,
                'total_files': self.total_files,
                'analyzed_files': self.analyzed_files,
            },
            'summary': {
                'total_issues': self.total_issues,
                'critical_count': self.critical_count,
                'high_count': self.high_count,
                'medium_count': self.medium_count,
                'low_count': self.low_count,
            },
            'issues': [issue.to_dict() for issue in self.issues],
            'by_severity': {
                severity.value: len(issues)
                for severity, issues in self.issues_by_severity.items()
            },
            'by_category': {
                category.value: len(issues)
                for category, issues in self.issues_by_category.items()
            },
            'by_db_type': {
                db_type: len(issues)
                for db_type, issues in self.issues_by_db_type.items()
            },
            'config': self.config,
            'warnings': self.warnings,
            'errors': self.errors,
        }

    def get_summary(self) -> str:
        """
        サマリーテキストを取得

        Returns:
            人間可読なサマリー文字列
        """
        lines = [
            "=" * 80,
            "MultiDB Analyzer - Analysis Summary",
            "=" * 80,
            "",
            f"Timestamp: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Execution Time: {self.execution_time:.2f}s",
            f"Files: {self.analyzed_files}/{self.total_files} analyzed",
            "",
            "=" * 80,
            "Issues Summary",
            "=" * 80,
            f"Total Issues: {self.total_issues}",
            "",
            f"  CRITICAL: {self.critical_count:>4}",
            f"  HIGH:     {self.high_count:>4}",
            f"  MEDIUM:   {self.medium_count:>4}",
            f"  LOW:      {self.low_count:>4}",
            "",
        ]

        # DBタイプ別
        if self.issues_by_db_type:
            lines.append("=" * 80)
            lines.append("By Database Type")
            lines.append("=" * 80)
            for db_type, issues in sorted(self.issues_by_db_type.items()):
                lines.append(f"  {db_type.upper()}: {len(issues)} issues")
            lines.append("")

        # カテゴリ別
        if self.issues_by_category:
            lines.append("=" * 80)
            lines.append("By Category")
            lines.append("=" * 80)
            for category, issues in sorted(
                self.issues_by_category.items(),
                key=lambda x: len(x[1]),
                reverse=True
            ):
                lines.append(f"  {category.value}: {len(issues)} issues")
            lines.append("")

        # 警告とエラー
        if self.warnings:
            lines.append("=" * 80)
            lines.append("Warnings")
            lines.append("=" * 80)
            for warning in self.warnings:
                lines.append(f"  ⚠️  {warning}")
            lines.append("")

        if self.errors:
            lines.append("=" * 80)
            lines.append("Errors")
            lines.append("=" * 80)
            for error in self.errors:
                lines.append(f"  ❌ {error}")
            lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)

    def get_top_issues(self, limit: int = 10) -> List[Issue]:
        """
        重大度順にトップN問題を取得

        Args:
            limit: 取得する問題数

        Returns:
            重大度の高い順の問題リスト
        """
        # 重大度の順序定義
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
        }

        sorted_issues = sorted(
            self.issues,
            key=lambda i: (severity_order.get(i.severity, 999), i.file_path, i.line_number)
        )

        return sorted_issues[:limit]

    def get_issues_by_file(self) -> Dict[str, List[Issue]]:
        """
        ファイル別の問題マップを取得

        Returns:
            ファイルパスをキーとした問題リストの辞書
        """
        by_file: Dict[str, List[Issue]] = defaultdict(list)
        for issue in self.issues:
            by_file[issue.file_path].append(issue)

        return dict(by_file)

    def has_critical_issues(self) -> bool:
        """CRITICAL問題があるか確認"""
        return self.critical_count > 0

    def has_high_issues(self) -> bool:
        """HIGH以上の問題があるか確認"""
        return self.critical_count > 0 or self.high_count > 0

    def get_success_rate(self) -> float:
        """
        成功率を計算（問題なしファイルの割合）

        Returns:
            0.0-1.0の成功率
        """
        if self.analyzed_files == 0:
            return 1.0

        issues_by_file = self.get_issues_by_file()
        clean_files = self.analyzed_files - len(issues_by_file)

        return clean_files / self.analyzed_files

    def add_warning(self, message: str):
        """警告を追加"""
        self.warnings.append(message)

    def add_error(self, message: str):
        """エラーを追加"""
        self.errors.append(message)

    def merge(self, other: 'AnalysisResult'):
        """
        別の分析結果とマージ

        Args:
            other: マージする分析結果
        """
        self.issues.extend(other.issues)
        self.total_files += other.total_files
        self.analyzed_files += other.analyzed_files
        self.execution_time += other.execution_time
        self.warnings.extend(other.warnings)
        self.errors.extend(other.errors)

        # 統計を再計算
        self._calculate_statistics()
