"""
Base Detector for Multi-Database Analyzer

すべての問題検出器の基底クラス
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class Severity(Enum):
    """問題の重要度"""
    CRITICAL = "critical"  # 即座に修正が必要
    HIGH = "high"         # できるだけ早く修正
    MEDIUM = "medium"     # 計画的に修正
    LOW = "low"           # 余裕があれば修正
    INFO = "info"         # 情報提供のみ


class IssueCategory(Enum):
    """問題のカテゴリ"""
    PERFORMANCE = "performance"      # パフォーマンス問題
    SECURITY = "security"            # セキュリティ問題
    RELIABILITY = "reliability"      # 信頼性問題
    MAINTAINABILITY = "maintainability"  # 保守性問題
    SCALABILITY = "scalability"      # スケーラビリティ問題
    BEST_PRACTICE = "best_practice"  # ベストプラクティス違反


@dataclass
class Issue:
    """
    検出された問題

    すべての検出器が返す統一された問題形式
    """
    # 必須フィールド
    detector_name: str
    severity: Severity
    category: IssueCategory
    title: str
    description: str
    file_path: str
    line_number: int

    # オプションフィールド
    query_text: Optional[str] = None
    method_name: Optional[str] = None
    class_name: Optional[str] = None
    suggestion: Optional[str] = None
    auto_fix_available: bool = False
    auto_fix_code: Optional[str] = None
    documentation_url: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    detected_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "detector_name": self.detector_name,
            "severity": self.severity.value,
            "category": self.category.value,
            "title": self.title,
            "description": self.description,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "query_text": self.query_text,
            "method_name": self.method_name,
            "class_name": self.class_name,
            "suggestion": self.suggestion,
            "auto_fix_available": self.auto_fix_available,
            "auto_fix_code": self.auto_fix_code,
            "documentation_url": self.documentation_url,
            "tags": self.tags,
            "metadata": self.metadata,
            "detected_at": self.detected_at.isoformat()
        }

    def get_severity_score(self) -> int:
        """重要度をスコアで返す (高いほど重要)"""
        severity_scores = {
            Severity.CRITICAL: 100,
            Severity.HIGH: 75,
            Severity.MEDIUM: 50,
            Severity.LOW: 25,
            Severity.INFO: 0
        }
        return severity_scores.get(self.severity, 0)


class BaseDetector(ABC):
    """
    すべての問題検出器の基底クラス

    各DB用の検出器はこのクラスを継承して実装する
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        検出器の初期化

        Args:
            config: 検出器設定
        """
        self.config = config or {}
        self._issues: List[Issue] = []

    @abstractmethod
    def get_name(self) -> str:
        """
        検出器名を返す

        Returns:
            検出器名
        """
        pass

    @abstractmethod
    def get_severity(self) -> Severity:
        """
        この検出器が検出する問題のデフォルト重要度を返す

        Returns:
            重要度
        """
        pass

    @abstractmethod
    def get_category(self) -> IssueCategory:
        """
        この検出器が検出する問題のカテゴリを返す

        Returns:
            カテゴリ
        """
        pass

    @abstractmethod
    def detect(self, queries: List[Any]) -> List[Issue]:
        """
        問題を検出

        Args:
            queries: 解析されたクエリのリスト

        Returns:
            検出された問題のリスト
        """
        pass

    def get_description(self) -> str:
        """
        検出器の説明を返す

        Returns:
            説明文
        """
        return self.__doc__ or "No description available"

    def is_enabled(self) -> bool:
        """
        この検出器が有効かどうか

        Returns:
            有効な場合True
        """
        return self.config.get('enabled', True)

    def get_threshold(self, key: str, default: Any = None) -> Any:
        """
        設定から閾値を取得

        Args:
            key: 設定キー
            default: デフォルト値

        Returns:
            設定値
        """
        return self.config.get('thresholds', {}).get(key, default)

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        設定値を取得

        Args:
            key: 設定キー
            default: デフォルト値

        Returns:
            設定値
        """
        return self.config.get(key, default)

    def create_issue(
        self,
        title: str,
        description: str,
        file_path: str,
        line_number: int,
        **kwargs
    ) -> Issue:
        """
        Issueオブジェクトを作成

        Args:
            title: 問題のタイトル
            description: 詳細説明
            file_path: ファイルパス
            line_number: 行番号
            **kwargs: その他のフィールド

        Returns:
            Issueオブジェクト
        """
        issue = Issue(
            detector_name=self.get_name(),
            severity=kwargs.get('severity', self.get_severity()),
            category=kwargs.get('category', self.get_category()),
            title=title,
            description=description,
            file_path=file_path,
            line_number=line_number,
            **{k: v for k, v in kwargs.items() if k not in ['severity', 'category']}
        )
        self._issues.append(issue)
        return issue

    def get_statistics(self) -> Dict[str, Any]:
        """
        検出統計を取得

        Returns:
            統計情報
        """
        severity_counts = {}
        for issue in self._issues:
            severity = issue.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return {
            "detector_name": self.get_name(),
            "total_issues": len(self._issues),
            "severity_counts": severity_counts,
            "category": self.get_category().value
        }

    def clear_issues(self):
        """検出された問題をクリア"""
        self._issues.clear()


class DetectorRegistry:
    """
    検出器レジストリ

    すべての検出器を管理
    """

    def __init__(self):
        self._detectors: Dict[str, BaseDetector] = {}

    def register(self, detector: BaseDetector):
        """
        検出器を登録

        Args:
            detector: 登録する検出器
        """
        name = detector.get_name()
        if name in self._detectors:
            raise ValueError(f"Detector '{name}' is already registered")
        self._detectors[name] = detector

    def unregister(self, name: str):
        """
        検出器を登録解除

        Args:
            name: 検出器名
        """
        if name in self._detectors:
            del self._detectors[name]

    def get_detector(self, name: str) -> Optional[BaseDetector]:
        """
        検出器を取得

        Args:
            name: 検出器名

        Returns:
            検出器（見つからない場合None）
        """
        return self._detectors.get(name)

    def get_all_detectors(self) -> List[BaseDetector]:
        """
        すべての検出器を取得

        Returns:
            検出器のリスト
        """
        return list(self._detectors.values())

    def get_enabled_detectors(self) -> List[BaseDetector]:
        """
        有効な検出器のみを取得

        Returns:
            有効な検出器のリスト
        """
        return [d for d in self._detectors.values() if d.is_enabled()]

    def run_all(self, queries: List[Any]) -> List[Issue]:
        """
        すべての有効な検出器を実行

        Args:
            queries: 解析されたクエリ

        Returns:
            すべての検出された問題
        """
        all_issues = []
        for detector in self.get_enabled_detectors():
            try:
                issues = detector.detect(queries)
                all_issues.extend(issues)
            except Exception as e:
                print(f"Error running detector {detector.get_name()}: {e}")
                continue
        return all_issues
