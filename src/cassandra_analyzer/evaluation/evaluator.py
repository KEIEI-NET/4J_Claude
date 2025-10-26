"""
評価器

検出結果と正解データを比較して評価メトリクスを計算
"""
from typing import List, Dict, Set, Tuple
from collections import defaultdict

from ..models import Issue
from .dataset import AnnotatedFile, EvaluationDataset, GroundTruthIssue
from .metrics import ConfusionMatrix, EvaluationMetrics, EvaluationResult


class Evaluator:
    """
    検出器の評価を実行

    検出結果と正解データを比較してメトリクスを計算
    """

    def __init__(self, tolerance: int = 2):
        """
        Args:
            tolerance: 行番号の許容誤差（デフォルト: 2行）
        """
        self.tolerance = tolerance

    def evaluate(
        self,
        detected_issues: List[Issue],
        ground_truth: AnnotatedFile
    ) -> EvaluationResult:
        """
        単一ファイルの評価

        Args:
            detected_issues: 検出された問題のリスト
            ground_truth: 正解データ

        Returns:
            評価結果
        """
        # 全体の混同行列
        overall_cm = self._calculate_confusion_matrix(detected_issues, ground_truth)

        # 問題タイプ別の混同行列
        per_issue_cm = self._calculate_per_issue_confusion_matrix(
            detected_issues, ground_truth
        )

        # メトリクスを計算
        return EvaluationMetrics.calculate_all(overall_cm, per_issue_cm)

    def evaluate_dataset(
        self,
        all_detected_issues: Dict[str, List[Issue]],
        dataset: EvaluationDataset
    ) -> EvaluationResult:
        """
        データセット全体の評価

        Args:
            all_detected_issues: ファイルパスをキーとした検出結果の辞書
            dataset: 評価用データセット

        Returns:
            評価結果
        """
        # 全体の混同行列を初期化
        overall_cm = ConfusionMatrix()
        per_issue_cm: Dict[str, ConfusionMatrix] = defaultdict(ConfusionMatrix)

        # 各ファイルごとに評価
        for annotated_file in dataset.get_all_files():
            file_path = annotated_file.file_path
            detected = all_detected_issues.get(file_path, [])

            # ファイルごとの混同行列を計算
            file_cm = self._calculate_confusion_matrix(detected, annotated_file)
            file_per_issue_cm = self._calculate_per_issue_confusion_matrix(
                detected, annotated_file
            )

            # 累積
            overall_cm.true_positives += file_cm.true_positives
            overall_cm.false_positives += file_cm.false_positives
            overall_cm.true_negatives += file_cm.true_negatives
            overall_cm.false_negatives += file_cm.false_negatives

            # 問題タイプ別に累積
            for issue_type, cm in file_per_issue_cm.items():
                per_issue_cm[issue_type].true_positives += cm.true_positives
                per_issue_cm[issue_type].false_positives += cm.false_positives
                per_issue_cm[issue_type].true_negatives += cm.true_negatives
                per_issue_cm[issue_type].false_negatives += cm.false_negatives

        # メトリクスを計算
        return EvaluationMetrics.calculate_all(overall_cm, dict(per_issue_cm))

    def _calculate_confusion_matrix(
        self,
        detected_issues: List[Issue],
        ground_truth: AnnotatedFile
    ) -> ConfusionMatrix:
        """
        混同行列を計算

        Args:
            detected_issues: 検出された問題
            ground_truth: 正解データ

        Returns:
            混同行列
        """
        cm = ConfusionMatrix()

        # 正解データをセットに変換（マッチング用）
        gt_set = set((gt.issue_type, gt.line_number) for gt in ground_truth.ground_truth_issues)

        # マッチング済みの正解データを記録
        matched_gt = set()

        # 検出結果をチェック
        for detected in detected_issues:
            matched = False
            for gt in ground_truth.ground_truth_issues:
                # 問題タイプが一致し、行番号が許容範囲内
                if (detected.issue_type == gt.issue_type and
                    abs(detected.line_number - gt.line_number) <= self.tolerance):
                    # True Positive
                    if (gt.issue_type, gt.line_number) not in matched_gt:
                        cm.true_positives += 1
                        matched_gt.add((gt.issue_type, gt.line_number))
                        matched = True
                        break

            if not matched:
                # False Positive（誤検出）
                cm.false_positives += 1

        # False Negative（見逃し）
        cm.false_negatives = len(gt_set) - len(matched_gt)

        # True Negative（正しく検出しない）
        # ※ 実際の実装では、ファイル内の潜在的な問題箇所の総数から計算する必要がある
        # ここでは簡易的に、検出も正解もない箇所を0とする
        cm.true_negatives = 0

        return cm

    def _calculate_per_issue_confusion_matrix(
        self,
        detected_issues: List[Issue],
        ground_truth: AnnotatedFile
    ) -> Dict[str, ConfusionMatrix]:
        """
        問題タイプ別の混同行列を計算

        Args:
            detected_issues: 検出された問題
            ground_truth: 正解データ

        Returns:
            問題タイプをキーとした混同行列の辞書
        """
        per_issue_cm: Dict[str, ConfusionMatrix] = defaultdict(ConfusionMatrix)

        # 問題タイプごとにグループ化
        detected_by_type = defaultdict(list)
        for issue in detected_issues:
            detected_by_type[issue.issue_type].append(issue)

        gt_by_type = defaultdict(list)
        for gt in ground_truth.ground_truth_issues:
            gt_by_type[gt.issue_type].append(gt)

        # すべての問題タイプを取得
        all_issue_types = set(detected_by_type.keys()) | set(gt_by_type.keys())

        # タイプごとに評価
        for issue_type in all_issue_types:
            detected = detected_by_type.get(issue_type, [])
            gt_list = gt_by_type.get(issue_type, [])

            # マッチング済みの正解データ
            matched_gt = set()

            # 検出結果をチェック
            for det in detected:
                matched = False
                for gt in gt_list:
                    if abs(det.line_number - gt.line_number) <= self.tolerance:
                        if gt.line_number not in matched_gt:
                            per_issue_cm[issue_type].true_positives += 1
                            matched_gt.add(gt.line_number)
                            matched = True
                            break

                if not matched:
                    per_issue_cm[issue_type].false_positives += 1

            # False Negative
            per_issue_cm[issue_type].false_negatives = len(gt_list) - len(matched_gt)

        return dict(per_issue_cm)

    def get_detailed_comparison(
        self,
        detected_issues: List[Issue],
        ground_truth: AnnotatedFile
    ) -> Dict[str, List]:
        """
        詳細な比較結果を取得

        Args:
            detected_issues: 検出された問題
            ground_truth: 正解データ

        Returns:
            true_positives, false_positives, false_negativesのリスト
        """
        result = {
            "true_positives": [],
            "false_positives": [],
            "false_negatives": [],
        }

        # 正解データをセットに変換
        gt_dict = {(gt.issue_type, gt.line_number): gt for gt in ground_truth.ground_truth_issues}
        matched_gt = set()

        # 検出結果をチェック
        for detected in detected_issues:
            matched = False
            for (gt_type, gt_line), gt in gt_dict.items():
                if (detected.issue_type == gt_type and
                    abs(detected.line_number - gt_line) <= self.tolerance):
                    if (gt_type, gt_line) not in matched_gt:
                        result["true_positives"].append({
                            "detected": detected,
                            "ground_truth": gt,
                        })
                        matched_gt.add((gt_type, gt_line))
                        matched = True
                        break

            if not matched:
                result["false_positives"].append(detected)

        # False Negative（見逃し）
        for (gt_type, gt_line), gt in gt_dict.items():
            if (gt_type, gt_line) not in matched_gt:
                result["false_negatives"].append(gt)

        return result
