"""
評価用データセット

アノテーション済みファイルの管理
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
import json


@dataclass
class GroundTruthIssue:
    """
    正解データの問題

    Attributes:
        issue_type: 問題タイプ (ALLOW_FILTERING, NO_PARTITION_KEY, etc.)
        line_number: 行番号
        severity: 重要度
        description: 説明（オプション）
    """
    issue_type: str
    line_number: int
    severity: str
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "issue_type": self.issue_type,
            "line_number": self.line_number,
            "severity": self.severity,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GroundTruthIssue":
        """辞書から生成"""
        return cls(
            issue_type=data["issue_type"],
            line_number=data["line_number"],
            severity=data["severity"],
            description=data.get("description", ""),
        )


@dataclass
class AnnotatedFile:
    """
    アノテーション済みファイル

    Attributes:
        file_path: ファイルパス
        ground_truth_issues: 正解データの問題リスト
        metadata: メタデータ（作成者、作成日など）
    """
    file_path: str
    ground_truth_issues: List[GroundTruthIssue] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "file_path": self.file_path,
            "ground_truth_issues": [issue.to_dict() for issue in self.ground_truth_issues],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnnotatedFile":
        """辞書から生成"""
        return cls(
            file_path=data["file_path"],
            ground_truth_issues=[
                GroundTruthIssue.from_dict(issue) for issue in data.get("ground_truth_issues", [])
            ],
            metadata=data.get("metadata", {}),
        )

    def to_json(self, indent: int = 2) -> str:
        """JSON文字列に変換"""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> "AnnotatedFile":
        """JSON文字列から生成"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def save(self, output_path: Path) -> None:
        """ファイルに保存"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, file_path: Path) -> "AnnotatedFile":
        """ファイルから読み込み"""
        with open(file_path, "r", encoding="utf-8") as f:
            return cls.from_json(f.read())


class EvaluationDataset:
    """
    評価用データセット

    複数のアノテーション済みファイルを管理
    """

    def __init__(self, annotated_files: Optional[List[AnnotatedFile]] = None):
        """
        Args:
            annotated_files: アノテーション済みファイルのリスト
        """
        self.annotated_files = annotated_files or []

    def add_file(self, annotated_file: AnnotatedFile) -> None:
        """ファイルを追加"""
        self.annotated_files.append(annotated_file)

    def get_file(self, file_path: str) -> Optional[AnnotatedFile]:
        """ファイルパスで検索"""
        for annotated_file in self.annotated_files:
            if annotated_file.file_path == file_path:
                return annotated_file
        return None

    def get_all_files(self) -> List[AnnotatedFile]:
        """すべてのファイルを取得"""
        return self.annotated_files

    def get_total_issues(self) -> int:
        """総問題数を取得"""
        return sum(len(f.ground_truth_issues) for f in self.annotated_files)

    def get_issues_by_type(self) -> Dict[str, int]:
        """問題タイプ別のカウント"""
        counts: Dict[str, int] = {}
        for annotated_file in self.annotated_files:
            for issue in annotated_file.ground_truth_issues:
                counts[issue.issue_type] = counts.get(issue.issue_type, 0) + 1
        return counts

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "annotated_files": [f.to_dict() for f in self.annotated_files],
            "statistics": {
                "total_files": len(self.annotated_files),
                "total_issues": self.get_total_issues(),
                "issues_by_type": self.get_issues_by_type(),
            }
        }

    def to_json(self, indent: int = 2) -> str:
        """JSON文字列に変換"""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvaluationDataset":
        """辞書から生成"""
        annotated_files = [
            AnnotatedFile.from_dict(f) for f in data.get("annotated_files", [])
        ]
        return cls(annotated_files=annotated_files)

    @classmethod
    def from_json(cls, json_str: str) -> "EvaluationDataset":
        """JSON文字列から生成"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def save(self, output_path: Path) -> None:
        """データセットをファイルに保存"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, file_path: Path) -> "EvaluationDataset":
        """データセットをファイルから読み込み"""
        with open(file_path, "r", encoding="utf-8") as f:
            return cls.from_json(f.read())

    @classmethod
    def load_from_directory(cls, directory: Path, pattern: str = "*.json") -> "EvaluationDataset":
        """
        ディレクトリから複数のアノテーションファイルを読み込み

        Args:
            directory: アノテーションファイルが格納されたディレクトリ
            pattern: ファイルパターン

        Returns:
            評価用データセット
        """
        dataset = cls()
        for file_path in directory.glob(pattern):
            try:
                annotated_file = AnnotatedFile.load(file_path)
                dataset.add_file(annotated_file)
            except Exception as e:
                print(f"Warning: Failed to load {file_path}: {e}")
        return dataset
