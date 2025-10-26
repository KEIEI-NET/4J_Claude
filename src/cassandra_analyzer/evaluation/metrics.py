"""
評価メトリクス

Precision, Recall, F1 Score, False Positive Rateなどの計算
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any
import json


@dataclass
class ConfusionMatrix:
    """
    混同行列

    Attributes:
        true_positives: 真陽性（正しく検出）
        false_positives: 偽陽性（誤検出）
        true_negatives: 真陰性（正しく検出しない）
        false_negatives: 偽陰性（見逃し）
    """
    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0

    def to_dict(self) -> Dict[str, int]:
        """辞書形式に変換"""
        return {
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "true_negatives": self.true_negatives,
            "false_negatives": self.false_negatives,
        }


@dataclass
class EvaluationResult:
    """
    評価結果

    Attributes:
        precision: 適合率（検出したもののうち正しいものの割合）
        recall: 再現率（実際の問題のうち検出できたものの割合）
        f1_score: F1スコア（PrecisionとRecallの調和平均）
        false_positive_rate: 偽陽性率
        accuracy: 精度
        confusion_matrix: 混同行列
        per_issue_type: 問題タイプ別のメトリクス
    """
    precision: float
    recall: float
    f1_score: float
    false_positive_rate: float
    accuracy: float
    confusion_matrix: ConfusionMatrix
    per_issue_type: Dict[str, Dict[str, float]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "false_positive_rate": self.false_positive_rate,
            "accuracy": self.accuracy,
            "confusion_matrix": self.confusion_matrix.to_dict(),
            "per_issue_type": self.per_issue_type,
        }

    def to_json(self, indent: int = 2) -> str:
        """JSON文字列に変換"""
        return json.dumps(self.to_dict(), indent=indent)

    def summary(self) -> str:
        """サマリー文字列を生成"""
        lines = [
            "=== Evaluation Results ===",
            f"Precision:    {self.precision:.4f}",
            f"Recall:       {self.recall:.4f}",
            f"F1 Score:     {self.f1_score:.4f}",
            f"Accuracy:     {self.accuracy:.4f}",
            f"FP Rate:      {self.false_positive_rate:.4f}",
            "",
            "Confusion Matrix:",
            f"  TP: {self.confusion_matrix.true_positives:4d}  FN: {self.confusion_matrix.false_negatives:4d}",
            f"  FP: {self.confusion_matrix.false_positives:4d}  TN: {self.confusion_matrix.true_negatives:4d}",
        ]

        if self.per_issue_type:
            lines.append("")
            lines.append("Per Issue Type:")
            for issue_type, metrics in self.per_issue_type.items():
                lines.append(f"  {issue_type}:")
                lines.append(f"    Precision: {metrics.get('precision', 0):.4f}")
                lines.append(f"    Recall:    {metrics.get('recall', 0):.4f}")
                lines.append(f"    F1 Score:  {metrics.get('f1_score', 0):.4f}")

        return "\n".join(lines)


class EvaluationMetrics:
    """
    評価メトリクスの計算
    """

    @staticmethod
    def calculate_precision(tp: int, fp: int) -> float:
        """
        適合率を計算

        Precision = TP / (TP + FP)

        Args:
            tp: True Positives
            fp: False Positives

        Returns:
            適合率（0.0 ~ 1.0）
        """
        if tp + fp == 0:
            return 0.0
        return tp / (tp + fp)

    @staticmethod
    def calculate_recall(tp: int, fn: int) -> float:
        """
        再現率を計算

        Recall = TP / (TP + FN)

        Args:
            tp: True Positives
            fn: False Negatives

        Returns:
            再現率（0.0 ~ 1.0）
        """
        if tp + fn == 0:
            return 0.0
        return tp / (tp + fn)

    @staticmethod
    def calculate_f1_score(precision: float, recall: float) -> float:
        """
        F1スコアを計算

        F1 = 2 * (Precision * Recall) / (Precision + Recall)

        Args:
            precision: 適合率
            recall: 再現率

        Returns:
            F1スコア（0.0 ~ 1.0）
        """
        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)

    @staticmethod
    def calculate_false_positive_rate(fp: int, tn: int) -> float:
        """
        偽陽性率を計算

        FPR = FP / (FP + TN)

        Args:
            fp: False Positives
            tn: True Negatives

        Returns:
            偽陽性率（0.0 ~ 1.0）
        """
        if fp + tn == 0:
            return 0.0
        return fp / (fp + tn)

    @staticmethod
    def calculate_accuracy(tp: int, tn: int, fp: int, fn: int) -> float:
        """
        精度を計算

        Accuracy = (TP + TN) / (TP + TN + FP + FN)

        Args:
            tp: True Positives
            tn: True Negatives
            fp: False Positives
            fn: False Negatives

        Returns:
            精度（0.0 ~ 1.0）
        """
        total = tp + tn + fp + fn
        if total == 0:
            return 0.0
        return (tp + tn) / total

    @classmethod
    def calculate_all(
        cls,
        confusion_matrix: ConfusionMatrix,
        per_issue_type: Dict[str, ConfusionMatrix] = None
    ) -> EvaluationResult:
        """
        すべてのメトリクスを計算

        Args:
            confusion_matrix: 全体の混同行列
            per_issue_type: 問題タイプ別の混同行列

        Returns:
            評価結果
        """
        tp = confusion_matrix.true_positives
        fp = confusion_matrix.false_positives
        tn = confusion_matrix.true_negatives
        fn = confusion_matrix.false_negatives

        precision = cls.calculate_precision(tp, fp)
        recall = cls.calculate_recall(tp, fn)
        f1_score = cls.calculate_f1_score(precision, recall)
        fpr = cls.calculate_false_positive_rate(fp, tn)
        accuracy = cls.calculate_accuracy(tp, tn, fp, fn)

        # 問題タイプ別のメトリクス計算
        per_issue_metrics = {}
        if per_issue_type:
            for issue_type, cm in per_issue_type.items():
                type_precision = cls.calculate_precision(cm.true_positives, cm.false_positives)
                type_recall = cls.calculate_recall(cm.true_positives, cm.false_negatives)
                type_f1 = cls.calculate_f1_score(type_precision, type_recall)

                per_issue_metrics[issue_type] = {
                    "precision": type_precision,
                    "recall": type_recall,
                    "f1_score": type_f1,
                    "true_positives": cm.true_positives,
                    "false_positives": cm.false_positives,
                    "false_negatives": cm.false_negatives,
                }

        return EvaluationResult(
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            false_positive_rate=fpr,
            accuracy=accuracy,
            confusion_matrix=confusion_matrix,
            per_issue_type=per_issue_metrics,
        )
