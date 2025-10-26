"""
評価モジュールのユニットテスト
"""
import pytest
from pathlib import Path

from cassandra_analyzer.evaluation import (
    EvaluationMetrics,
    ConfusionMatrix,
    EvaluationResult,
    GroundTruthIssue,
    AnnotatedFile,
    EvaluationDataset,
    Evaluator,
)
from cassandra_analyzer.models import Issue


class TestConfusionMatrix:
    """ConfusionMatrixのテストクラス"""

    def test_initialization(self):
        """初期化"""
        cm = ConfusionMatrix()
        assert cm.true_positives == 0
        assert cm.false_positives == 0
        assert cm.true_negatives == 0
        assert cm.false_negatives == 0

    def test_to_dict(self):
        """辞書変換"""
        cm = ConfusionMatrix(
            true_positives=10,
            false_positives=5,
            true_negatives=20,
            false_negatives=3
        )
        result = cm.to_dict()
        assert result["true_positives"] == 10
        assert result["false_positives"] == 5
        assert result["true_negatives"] == 20
        assert result["false_negatives"] == 3


class TestEvaluationMetrics:
    """EvaluationMetricsのテストクラス"""

    def test_calculate_precision(self):
        """適合率の計算"""
        # TP=10, FP=5 の場合
        precision = EvaluationMetrics.calculate_precision(10, 5)
        assert precision == pytest.approx(0.6667, rel=1e-3)

        # TP=0, FP=0 の場合（ゼロ除算）
        precision = EvaluationMetrics.calculate_precision(0, 0)
        assert precision == 0.0

    def test_calculate_recall(self):
        """再現率の計算"""
        # TP=10, FN=2 の場合
        recall = EvaluationMetrics.calculate_recall(10, 2)
        assert recall == pytest.approx(0.8333, rel=1e-3)

        # TP=0, FN=0 の場合（ゼロ除算）
        recall = EvaluationMetrics.calculate_recall(0, 0)
        assert recall == 0.0

    def test_calculate_f1_score(self):
        """F1スコアの計算"""
        # Precision=0.8, Recall=0.9 の場合
        f1 = EvaluationMetrics.calculate_f1_score(0.8, 0.9)
        assert f1 == pytest.approx(0.8471, rel=1e-3)

        # Precision=0, Recall=0 の場合（ゼロ除算）
        f1 = EvaluationMetrics.calculate_f1_score(0.0, 0.0)
        assert f1 == 0.0

    def test_calculate_false_positive_rate(self):
        """偽陽性率の計算"""
        # FP=5, TN=95 の場合
        fpr = EvaluationMetrics.calculate_false_positive_rate(5, 95)
        assert fpr == 0.05

        # FP=0, TN=0 の場合（ゼロ除算）
        fpr = EvaluationMetrics.calculate_false_positive_rate(0, 0)
        assert fpr == 0.0

    def test_calculate_accuracy(self):
        """精度の計算"""
        # TP=90, TN=10, FP=5, FN=5 の場合
        accuracy = EvaluationMetrics.calculate_accuracy(90, 10, 5, 5)
        assert accuracy == pytest.approx(0.9091, rel=1e-3)

        # TP=0, TN=0, FP=0, FN=0 の場合（ゼロ除算）
        accuracy = EvaluationMetrics.calculate_accuracy(0, 0, 0, 0)
        assert accuracy == 0.0

    def test_calculate_all(self):
        """すべてのメトリクスの計算"""
        cm = ConfusionMatrix(
            true_positives=90,
            false_positives=10,
            true_negatives=85,
            false_negatives=15
        )

        result = EvaluationMetrics.calculate_all(cm)

        assert isinstance(result, EvaluationResult)
        assert result.precision == 0.9
        assert result.recall == pytest.approx(0.8571, rel=1e-3)
        assert result.f1_score > 0.8
        assert result.false_positive_rate < 0.2
        assert result.accuracy > 0.8


class TestEvaluationResult:
    """EvaluationResultのテストクラス"""

    @pytest.fixture
    def sample_result(self):
        """サンプルの評価結果"""
        cm = ConfusionMatrix(
            true_positives=10,
            false_positives=2,
            true_negatives=85,
            false_negatives=3
        )
        return EvaluationResult(
            precision=0.8333,
            recall=0.7692,
            f1_score=0.8000,
            false_positive_rate=0.0230,
            accuracy=0.95,
            confusion_matrix=cm,
        )

    def test_to_dict(self, sample_result):
        """辞書変換"""
        result_dict = sample_result.to_dict()
        assert result_dict["precision"] == pytest.approx(0.8333, rel=1e-3)
        assert result_dict["recall"] == pytest.approx(0.7692, rel=1e-3)
        assert "confusion_matrix" in result_dict

    def test_to_json(self, sample_result):
        """JSON変換"""
        json_str = sample_result.to_json()
        assert "precision" in json_str
        assert "recall" in json_str

    def test_summary(self, sample_result):
        """サマリー生成"""
        summary = sample_result.summary()
        assert "Precision" in summary
        assert "Recall" in summary
        assert "F1 Score" in summary
        assert "Confusion Matrix" in summary

    def test_summary_with_per_issue_type(self):
        """問題タイプ別メトリクス付きサマリー"""
        result = EvaluationResult(
            confusion_matrix=ConfusionMatrix(
                true_positives=15,
                false_positives=3,
                true_negatives=0,
                false_negatives=5
            ),
            precision=0.83,
            recall=0.75,
            f1_score=0.79,
            false_positive_rate=0.17,
            accuracy=0.65,
            per_issue_type={
                "ALLOW_FILTERING": {
                    "precision": 0.9,
                    "recall": 0.8,
                    "f1_score": 0.85
                },
                "BATCH_SIZE": {
                    "precision": 0.75,
                    "recall": 0.7,
                    "f1_score": 0.72
                }
            }
        )

        summary = result.summary()
        assert "Precision" in summary
        assert "Recall" in summary
        assert "Per Issue Type:" in summary
        assert "ALLOW_FILTERING" in summary
        assert "BATCH_SIZE" in summary


class TestGroundTruthIssue:
    """GroundTruthIssueのテストクラス"""

    def test_initialization(self):
        """初期化"""
        issue = GroundTruthIssue(
            issue_type="ALLOW_FILTERING",
            line_number=10,
            severity="high",
            description="Test issue"
        )
        assert issue.issue_type == "ALLOW_FILTERING"
        assert issue.line_number == 10
        assert issue.severity == "high"

    def test_to_dict_from_dict(self):
        """辞書変換と復元"""
        issue = GroundTruthIssue(
            issue_type="NO_PARTITION_KEY",
            line_number=20,
            severity="critical"
        )
        issue_dict = issue.to_dict()
        restored = GroundTruthIssue.from_dict(issue_dict)

        assert restored.issue_type == issue.issue_type
        assert restored.line_number == issue.line_number
        assert restored.severity == issue.severity


class TestAnnotatedFile:
    """AnnotatedFileのテストクラス"""

    @pytest.fixture
    def sample_annotated_file(self):
        """サンプルのアノテーション済みファイル"""
        issues = [
            GroundTruthIssue("ALLOW_FILTERING", 10, "high"),
            GroundTruthIssue("NO_PARTITION_KEY", 20, "critical"),
        ]
        return AnnotatedFile(
            file_path="test.java",
            ground_truth_issues=issues,
            metadata={"annotator": "test"}
        )

    def test_initialization(self, sample_annotated_file):
        """初期化"""
        assert sample_annotated_file.file_path == "test.java"
        assert len(sample_annotated_file.ground_truth_issues) == 2

    def test_to_dict_from_dict(self, sample_annotated_file):
        """辞書変換と復元"""
        file_dict = sample_annotated_file.to_dict()
        restored = AnnotatedFile.from_dict(file_dict)

        assert restored.file_path == sample_annotated_file.file_path
        assert len(restored.ground_truth_issues) == len(sample_annotated_file.ground_truth_issues)

    def test_to_json_from_json(self, sample_annotated_file):
        """JSON変換と復元"""
        json_str = sample_annotated_file.to_json()
        restored = AnnotatedFile.from_json(json_str)

        assert restored.file_path == sample_annotated_file.file_path
        assert len(restored.ground_truth_issues) == len(sample_annotated_file.ground_truth_issues)


class TestEvaluationDataset:
    """EvaluationDatasetのテストクラス"""

    @pytest.fixture
    def sample_dataset(self):
        """サンプルデータセット"""
        files = [
            AnnotatedFile(
                "file1.java",
                [GroundTruthIssue("ALLOW_FILTERING", 10, "high")]
            ),
            AnnotatedFile(
                "file2.java",
                [
                    GroundTruthIssue("NO_PARTITION_KEY", 20, "critical"),
                    GroundTruthIssue("UNPREPARED_STATEMENT", 30, "medium"),
                ]
            ),
        ]
        return EvaluationDataset(files)

    def test_initialization(self):
        """初期化"""
        dataset = EvaluationDataset()
        assert len(dataset.get_all_files()) == 0

    def test_add_file(self, sample_dataset):
        """ファイルの追加"""
        new_file = AnnotatedFile("file3.java", [])
        sample_dataset.add_file(new_file)
        assert len(sample_dataset.get_all_files()) == 3

    def test_get_file(self, sample_dataset):
        """ファイルの取得"""
        file = sample_dataset.get_file("file1.java")
        assert file is not None
        assert file.file_path == "file1.java"

        # 存在しないファイル
        file = sample_dataset.get_file("nonexistent.java")
        assert file is None

    def test_get_total_issues(self, sample_dataset):
        """総問題数の取得"""
        total = sample_dataset.get_total_issues()
        assert total == 3  # 1 + 2

    def test_get_issues_by_type(self, sample_dataset):
        """問題タイプ別のカウント"""
        counts = sample_dataset.get_issues_by_type()
        assert counts["ALLOW_FILTERING"] == 1
        assert counts["NO_PARTITION_KEY"] == 1
        assert counts["UNPREPARED_STATEMENT"] == 1

    def test_save_and_load_annotated_file(self, tmp_path):
        """AnnotatedFileの保存と読み込み"""
        annotated_file = AnnotatedFile(
            file_path="test.java",
            ground_truth_issues=[
                GroundTruthIssue("ALLOW_FILTERING", 10, "high", "Test issue")
            ],
            metadata={"author": "tester"}
        )

        # 保存
        output_path = tmp_path / "annotation.json"
        annotated_file.save(output_path)
        assert output_path.exists()

        # 読み込み
        loaded = AnnotatedFile.load(output_path)
        assert loaded.file_path == "test.java"
        assert len(loaded.ground_truth_issues) == 1
        assert loaded.ground_truth_issues[0].issue_type == "ALLOW_FILTERING"
        assert loaded.metadata["author"] == "tester"

    def test_load_from_directory(self, tmp_path):
        """ディレクトリからデータセットを読み込み"""
        # アノテーションファイルを作成
        file1 = AnnotatedFile(
            file_path="test1.java",
            ground_truth_issues=[GroundTruthIssue("ALLOW_FILTERING", 10, "high")]
        )
        file1.save(tmp_path / "annotation1.json")

        file2 = AnnotatedFile(
            file_path="test2.java",
            ground_truth_issues=[GroundTruthIssue("BATCH_SIZE", 20, "medium")]
        )
        file2.save(tmp_path / "annotation2.json")

        # ダミーファイル（無視されるべき）
        (tmp_path / "readme.txt").write_text("dummy")

        # ディレクトリから読み込み
        dataset = EvaluationDataset.load_from_directory(tmp_path)
        assert len(dataset.get_all_files()) == 2
        assert dataset.get_total_issues() == 2

    def test_dataset_to_dict_and_from_dict(self):
        """データセットの辞書変換"""
        dataset = EvaluationDataset()
        dataset.add_file(AnnotatedFile(
            file_path="test1.java",
            ground_truth_issues=[GroundTruthIssue("ALLOW_FILTERING", 10, "high")]
        ))
        dataset.add_file(AnnotatedFile(
            file_path="test2.java",
            ground_truth_issues=[GroundTruthIssue("BATCH_SIZE", 20, "medium")]
        ))

        # 辞書に変換
        data = dataset.to_dict()
        assert "annotated_files" in data
        assert "statistics" in data
        assert data["statistics"]["total_files"] == 2
        assert data["statistics"]["total_issues"] == 2

        # 辞書から復元
        restored = EvaluationDataset.from_dict(data)
        assert len(restored.get_all_files()) == 2
        assert restored.get_total_issues() == 2

    def test_dataset_to_json_and_from_json(self):
        """データセットのJSON変換"""
        dataset = EvaluationDataset()
        dataset.add_file(AnnotatedFile(
            file_path="test.java",
            ground_truth_issues=[GroundTruthIssue("ALLOW_FILTERING", 10, "high")]
        ))

        # JSONに変換
        json_str = dataset.to_json()
        assert isinstance(json_str, str)
        assert "annotated_files" in json_str

        # JSONから復元
        restored = EvaluationDataset.from_json(json_str)
        assert len(restored.get_all_files()) == 1
        assert restored.get_total_issues() == 1

    def test_dataset_save_and_load(self, tmp_path):
        """データセットの保存と読み込み"""
        dataset = EvaluationDataset()
        dataset.add_file(AnnotatedFile(
            file_path="test.java",
            ground_truth_issues=[
                GroundTruthIssue("ALLOW_FILTERING", 10, "high"),
                GroundTruthIssue("BATCH_SIZE", 20, "medium"),
            ]
        ))

        # 保存
        output_path = tmp_path / "dataset.json"
        dataset.save(output_path)
        assert output_path.exists()

        # 読み込み
        loaded = EvaluationDataset.load(output_path)
        assert len(loaded.get_all_files()) == 1
        assert loaded.get_total_issues() == 2

    def test_load_from_directory_with_errors(self, tmp_path):
        """エラーを含むファイルの読み込み"""
        # 正常なファイル
        file1 = AnnotatedFile(
            file_path="test1.java",
            ground_truth_issues=[GroundTruthIssue("ALLOW_FILTERING", 10, "high")]
        )
        file1.save(tmp_path / "annotation1.json")

        # 不正なJSONファイル
        (tmp_path / "invalid.json").write_text("{invalid json}")

        # ディレクトリから読み込み（エラーは警告のみで続行）
        dataset = EvaluationDataset.load_from_directory(tmp_path)
        assert len(dataset.get_all_files()) == 1


class TestEvaluator:
    """Evaluatorのテストクラス"""

    @pytest.fixture
    def evaluator(self):
        """評価器"""
        return Evaluator(tolerance=2)

    @pytest.fixture
    def sample_ground_truth(self):
        """サンプル正解データ"""
        issues = [
            GroundTruthIssue("ALLOW_FILTERING", 10, "high"),
            GroundTruthIssue("NO_PARTITION_KEY", 20, "critical"),
            GroundTruthIssue("UNPREPARED_STATEMENT", 30, "medium"),
        ]
        return AnnotatedFile("test.java", issues)

    def test_perfect_detection(self, evaluator, sample_ground_truth):
        """完璧な検出（すべて正しく検出）"""
        detected = [
            Issue(
                detector_name="test",
                issue_type="ALLOW_FILTERING",
                severity="high",
                file_path="test.java",
                line_number=10,
                message="Test",
                cql_text="",
                recommendation="",
                evidence=[],
                confidence=1.0,
            ),
            Issue(
                detector_name="test",
                issue_type="NO_PARTITION_KEY",
                severity="critical",
                file_path="test.java",
                line_number=20,
                message="Test",
                cql_text="",
                recommendation="",
                evidence=[],
                confidence=1.0,
            ),
            Issue(
                detector_name="test",
                issue_type="UNPREPARED_STATEMENT",
                severity="medium",
                file_path="test.java",
                line_number=30,
                message="Test",
                cql_text="",
                recommendation="",
                evidence=[],
                confidence=1.0,
            ),
        ]

        result = evaluator.evaluate(detected, sample_ground_truth)

        assert result.confusion_matrix.true_positives == 3
        assert result.confusion_matrix.false_positives == 0
        assert result.confusion_matrix.false_negatives == 0
        assert result.precision == 1.0
        assert result.recall == 1.0
        assert result.f1_score == 1.0

    def test_partial_detection_with_false_positive(self, evaluator, sample_ground_truth):
        """部分的な検出（見逃しと誤検出あり）"""
        detected = [
            # TP: 正しく検出
            Issue(
                detector_name="test",
                issue_type="ALLOW_FILTERING",
                severity="high",
                file_path="test.java",
                line_number=10,
                message="Test",
                cql_text="",
                recommendation="",
                evidence=[],
                confidence=1.0,
            ),
            # FP: 誤検出
            Issue(
                detector_name="test",
                issue_type="BATCH_SIZE",
                severity="medium",
                file_path="test.java",
                line_number=40,
                message="Test",
                cql_text="",
                recommendation="",
                evidence=[],
                confidence=1.0,
            ),
        ]
        # FN: NO_PARTITION_KEY と UNPREPARED_STATEMENT を見逃し

        result = evaluator.evaluate(detected, sample_ground_truth)

        assert result.confusion_matrix.true_positives == 1
        assert result.confusion_matrix.false_positives == 1
        assert result.confusion_matrix.false_negatives == 2
        assert result.precision == 0.5
        assert result.recall == pytest.approx(0.3333, rel=1e-3)

    def test_tolerance_matching(self, evaluator, sample_ground_truth):
        """許容誤差内のマッチング"""
        detected = [
            # 行番号が2行ずれているが、tolerance=2なので一致
            Issue(
                detector_name="test",
                issue_type="ALLOW_FILTERING",
                severity="high",
                file_path="test.java",
                line_number=12,  # 正解は10
                message="Test",
                cql_text="",
                recommendation="",
                evidence=[],
                confidence=1.0,
            ),
        ]

        result = evaluator.evaluate(detected, sample_ground_truth)

        # 許容誤差内なのでTPとしてカウント
        assert result.confusion_matrix.true_positives == 1
        assert result.confusion_matrix.false_positives == 0

    def test_per_issue_type_metrics(self, evaluator, sample_ground_truth):
        """問題タイプ別のメトリクス"""
        detected = [
            Issue(
                detector_name="test",
                issue_type="ALLOW_FILTERING",
                severity="high",
                file_path="test.java",
                line_number=10,
                message="Test",
                cql_text="",
                recommendation="",
                evidence=[],
                confidence=1.0,
            ),
            # NO_PARTITION_KEYは見逃し
            Issue(
                detector_name="test",
                issue_type="UNPREPARED_STATEMENT",
                severity="medium",
                file_path="test.java",
                line_number=30,
                message="Test",
                cql_text="",
                recommendation="",
                evidence=[],
                confidence=1.0,
            ),
        ]

        result = evaluator.evaluate(detected, sample_ground_truth)

        # 問題タイプ別のメトリクスがあることを確認
        assert "ALLOW_FILTERING" in result.per_issue_type
        assert "NO_PARTITION_KEY" in result.per_issue_type
        assert "UNPREPARED_STATEMENT" in result.per_issue_type

        # ALLOW_FILTERINGは完璧
        assert result.per_issue_type["ALLOW_FILTERING"]["precision"] == 1.0
        assert result.per_issue_type["ALLOW_FILTERING"]["recall"] == 1.0

        # NO_PARTITION_KEYは完全に見逃し
        assert result.per_issue_type["NO_PARTITION_KEY"]["precision"] == 0.0
        assert result.per_issue_type["NO_PARTITION_KEY"]["recall"] == 0.0

    def test_evaluate_dataset(self, evaluator):
        """データセット全体の評価"""
        # データセットを作成
        dataset = EvaluationDataset()
        dataset.add_file(AnnotatedFile(
            file_path="file1.java",
            ground_truth_issues=[
                GroundTruthIssue("ALLOW_FILTERING", 10, "high"),
                GroundTruthIssue("NO_PARTITION_KEY", 20, "critical"),
            ]
        ))
        dataset.add_file(AnnotatedFile(
            file_path="file2.java",
            ground_truth_issues=[
                GroundTruthIssue("BATCH_SIZE", 30, "medium"),
            ]
        ))

        # 検出結果
        all_detected = {
            "file1.java": [
                Issue(
                    detector_name="test",
                    issue_type="ALLOW_FILTERING",
                    severity="high",
                    file_path="file1.java",
                    line_number=10,
                    message="Test",
                    cql_text="",
                    recommendation="",
                    evidence=[],
                    confidence=1.0,
                ),
            ],
            "file2.java": [
                Issue(
                    detector_name="test",
                    issue_type="BATCH_SIZE",
                    severity="medium",
                    file_path="file2.java",
                    line_number=30,
                    message="Test",
                    cql_text="",
                    recommendation="",
                    evidence=[],
                    confidence=1.0,
                ),
            ],
        }

        result = evaluator.evaluate_dataset(all_detected, dataset)

        # 2 TP (ALLOW_FILTERING, BATCH_SIZE), 1 FN (NO_PARTITION_KEY)
        assert result.confusion_matrix.true_positives == 2
        assert result.confusion_matrix.false_positives == 0
        assert result.confusion_matrix.false_negatives == 1
        assert result.precision == 1.0
        assert result.recall == pytest.approx(0.6667, rel=1e-3)

    def test_evaluate_dataset_with_per_issue_type(self, evaluator):
        """データセット評価の問題タイプ別メトリクス"""
        dataset = EvaluationDataset()
        dataset.add_file(AnnotatedFile(
            file_path="file1.java",
            ground_truth_issues=[
                GroundTruthIssue("ALLOW_FILTERING", 10, "high"),
                GroundTruthIssue("ALLOW_FILTERING", 20, "high"),
            ]
        ))

        all_detected = {
            "file1.java": [
                Issue(
                    detector_name="test",
                    issue_type="ALLOW_FILTERING",
                    severity="high",
                    file_path="file1.java",
                    line_number=10,
                    message="Test",
                    cql_text="",
                    recommendation="",
                    evidence=[],
                    confidence=1.0,
                ),
                Issue(
                    detector_name="test",
                    issue_type="BATCH_SIZE",
                    severity="medium",
                    file_path="file1.java",
                    line_number=30,
                    message="Test",
                    cql_text="",
                    recommendation="",
                    evidence=[],
                    confidence=1.0,
                ),
            ],
        }

        result = evaluator.evaluate_dataset(all_detected, dataset)

        # 問題タイプ別にチェック
        assert "ALLOW_FILTERING" in result.per_issue_type
        assert "BATCH_SIZE" in result.per_issue_type

        # ALLOW_FILTERINGは1 TP, 1 FN
        assert result.per_issue_type["ALLOW_FILTERING"]["recall"] == 0.5

    def test_get_detailed_comparison(self, evaluator):
        """詳細な比較結果を取得"""
        # 正解データ
        ground_truth = AnnotatedFile(
            file_path="test.java",
            ground_truth_issues=[
                GroundTruthIssue("ALLOW_FILTERING", 10, "high"),
                GroundTruthIssue("NO_PARTITION_KEY", 20, "critical"),
                GroundTruthIssue("BATCH_SIZE", 30, "medium"),
            ]
        )

        # 検出結果（2つは正解、1つは誤検出、1つは見逃し）
        detected_issues = [
            Issue(
                detector_name="test",
                issue_type="ALLOW_FILTERING",
                severity="high",
                file_path="test.java",
                line_number=10,  # TP
                message="Test",
                cql_text="",
                recommendation="",
                evidence=[],
                confidence=1.0,
            ),
            Issue(
                detector_name="test",
                issue_type="NO_PARTITION_KEY",
                severity="critical",
                file_path="test.java",
                line_number=21,  # TP (tolerance=2なので20と一致)
                message="Test",
                cql_text="",
                recommendation="",
                evidence=[],
                confidence=1.0,
            ),
            Issue(
                detector_name="test",
                issue_type="PREPARED_STATEMENT",
                severity="low",
                file_path="test.java",
                line_number=40,  # FP（正解にない）
                message="Test",
                cql_text="",
                recommendation="",
                evidence=[],
                confidence=1.0,
            ),
            # BATCH_SIZEは検出されず（FN）
        ]

        result = evaluator.get_detailed_comparison(detected_issues, ground_truth)

        # True Positives
        assert len(result["true_positives"]) == 2
        assert result["true_positives"][0]["detected"].issue_type == "ALLOW_FILTERING"
        assert result["true_positives"][1]["detected"].issue_type == "NO_PARTITION_KEY"

        # False Positives
        assert len(result["false_positives"]) == 1
        assert result["false_positives"][0].issue_type == "PREPARED_STATEMENT"

        # False Negatives
        assert len(result["false_negatives"]) == 1
        assert result["false_negatives"][0].issue_type == "BATCH_SIZE"
