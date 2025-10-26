"""
評価スクリプト

検出器の性能を評価し、レポートを生成します。

使用方法:
    python scripts/evaluate.py --annotations tests/evaluation_data --output evaluation_report.json

    # カスタム設定で実行
    python scripts/evaluate.py --annotations tests/evaluation_data --config config.yaml --output report.json
"""
import argparse
import sys
from pathlib import Path
import json
from typing import Dict, List

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cassandra_analyzer.analyzer import CassandraAnalyzer
from cassandra_analyzer.evaluation import (
    EvaluationDataset,
    Evaluator,
    EvaluationResult,
)
from cassandra_analyzer.models import Issue


def load_config(config_path: Path) -> Dict:
    """設定ファイルを読み込み"""
    if config_path.suffix in [".yaml", ".yml"]:
        try:
            import yaml
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except ImportError:
            print("Error: PyYAML is required for YAML config files. Install it with: pip install pyyaml")
            sys.exit(1)
    elif config_path.suffix == ".json":
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        print(f"Error: Unsupported config file format: {config_path.suffix}")
        sys.exit(1)


def run_analysis(
    dataset: EvaluationDataset,
    config: Dict = None
) -> Dict[str, List[Issue]]:
    """
    データセット内のすべてのファイルを分析

    Args:
        dataset: 評価用データセット
        config: アナライザーの設定

    Returns:
        ファイルパスをキーとした検出結果の辞書
    """
    analyzer = CassandraAnalyzer(config=config or {})
    results = {}

    print("Running analysis...")
    for i, annotated_file in enumerate(dataset.get_all_files(), 1):
        file_path = annotated_file.file_path
        print(f"  [{i}/{len(dataset.get_all_files())}] Analyzing {file_path}...")

        try:
            # ファイルを分析
            analysis_result = analyzer.analyze_file(file_path)
            results[file_path] = analysis_result.issues
        except Exception as e:
            print(f"    Error analyzing {file_path}: {e}")
            results[file_path] = []

    return results


def generate_report(
    result: EvaluationResult,
    output_path: Path,
    detailed: bool = False
) -> None:
    """
    評価レポートを生成

    Args:
        result: 評価結果
        output_path: 出力ファイルパス
        detailed: 詳細レポートを生成するか
    """
    report = result.to_dict()

    # 詳細情報を追加
    if detailed:
        report["detailed"] = {
            "summary": result.summary(),
            "recommendations": generate_recommendations(result),
        }

    # ファイルに保存
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nReport saved to: {output_path}")


def generate_recommendations(result: EvaluationResult) -> List[str]:
    """
    評価結果に基づいた改善提案を生成

    Args:
        result: 評価結果

    Returns:
        推奨事項のリスト
    """
    recommendations = []

    # 精度が低い場合
    if result.precision < 0.8:
        recommendations.append(
            f"Low precision ({result.precision:.2%}): Consider adjusting detection thresholds "
            "to reduce false positives."
        )

    # 再現率が低い場合
    if result.recall < 0.8:
        recommendations.append(
            f"Low recall ({result.recall:.2%}): Consider adding more detection patterns "
            "or improving pattern matching to catch more issues."
        )

    # 偽陽性率が高い場合
    if result.false_positive_rate > 0.1:
        recommendations.append(
            f"High false positive rate ({result.false_positive_rate:.2%}): "
            "Review and refine detection rules to reduce incorrect detections."
        )

    # 問題タイプ別の推奨
    for issue_type, metrics in result.per_issue_type.items():
        if metrics.get("precision", 1.0) < 0.7:
            recommendations.append(
                f"{issue_type}: Low precision ({metrics['precision']:.2%}) - "
                "Review detection logic for this issue type."
            )
        if metrics.get("recall", 1.0) < 0.7:
            recommendations.append(
                f"{issue_type}: Low recall ({metrics['recall']:.2%}) - "
                "Add more detection patterns for this issue type."
            )

    if not recommendations:
        recommendations.append(
            "Excellent performance! Consider expanding the test dataset "
            "to ensure consistent results across more scenarios."
        )

    return recommendations


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="Evaluate Cassandra analyzer performance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic evaluation
  python scripts/evaluate.py --annotations tests/evaluation_data

  # With custom config
  python scripts/evaluate.py --annotations tests/evaluation_data --config config.yaml

  # With detailed report
  python scripts/evaluate.py --annotations tests/evaluation_data --detailed --output report.json
        """
    )

    parser.add_argument(
        "--annotations",
        type=Path,
        required=True,
        help="Path to directory containing annotation files (JSON)"
    )

    parser.add_argument(
        "--config",
        type=Path,
        help="Path to analyzer configuration file (YAML or JSON)"
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evaluation_report.json"),
        help="Output path for evaluation report (default: evaluation_report.json)"
    )

    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Generate detailed report with recommendations"
    )

    parser.add_argument(
        "--tolerance",
        type=int,
        default=2,
        help="Line number tolerance for matching (default: 2)"
    )

    args = parser.parse_args()

    # アノテーションディレクトリを確認
    if not args.annotations.exists():
        print(f"Error: Annotations directory not found: {args.annotations}")
        sys.exit(1)

    # 設定ファイルを読み込み
    config = {}
    if args.config:
        if not args.config.exists():
            print(f"Error: Config file not found: {args.config}")
            sys.exit(1)
        config = load_config(args.config)

    print(f"Loading annotations from: {args.annotations}")

    # データセットを読み込み
    try:
        dataset = EvaluationDataset.load_from_directory(args.annotations)
        print(f"Loaded {len(dataset.get_all_files())} annotated files")
        print(f"Total ground truth issues: {dataset.get_total_issues()}")

        # 問題タイプ別の統計
        issues_by_type = dataset.get_issues_by_type()
        print("\nGround truth issues by type:")
        for issue_type, count in sorted(issues_by_type.items()):
            print(f"  {issue_type}: {count}")

    except Exception as e:
        print(f"Error loading dataset: {e}")
        sys.exit(1)

    # 分析を実行
    detected_issues = run_analysis(dataset, config)

    # 評価を実行
    print("\nEvaluating results...")
    evaluator = Evaluator(tolerance=args.tolerance)
    result = evaluator.evaluate_dataset(detected_issues, dataset)

    # 結果を表示
    print("\n" + "="*60)
    print(result.summary())
    print("="*60)

    # 推奨事項を表示
    if args.detailed:
        recommendations = generate_recommendations(result)
        print("\nRecommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")

    # レポートを生成
    generate_report(result, args.output, detailed=args.detailed)

    # 終了コード（F1スコアが0.8未満の場合は1）
    if result.f1_score < 0.8:
        print(f"\nWarning: F1 Score ({result.f1_score:.2%}) is below target (80%)")
        sys.exit(1)

    print("\nEvaluation completed successfully!")
    sys.exit(0)


if __name__ == "__main__":
    main()
