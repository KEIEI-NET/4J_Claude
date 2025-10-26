"""
End-to-End分析テスト

完全な分析パイプラインのテスト
"""
import json
import pytest
from pathlib import Path

from cassandra_analyzer.analyzer import CassandraAnalyzer
from cassandra_analyzer.reporters import JSONReporter, MarkdownReporter, HTMLReporter


@pytest.fixture
def fixtures_dir():
    """フィクスチャディレクトリのパス"""
    return Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def analyzer():
    """アナライザーのフィクスチャ"""
    return CassandraAnalyzer()


class TestSingleFileAnalysis:
    """単一ファイル分析のテスト"""

    def test_analyze_bad_dao1(self, analyzer, fixtures_dir):
        """ALLOW FILTERING問題を持つファイルの分析"""
        test_file = fixtures_dir / "sample_dao_bad1.java"
        result = analyzer.analyze_file(str(test_file))

        # ファイルが分析されたことを確認
        assert result.total_files == 1
        assert str(test_file) in result.analyzed_files

        # 問題が検出されたことを確認
        assert result.total_issues > 0

        # ALLOW FILTERING問題が検出されたことを確認
        assert result.high_count >= 3  # 3つのALLOW FILTERING

        # 分析時間が記録されたことを確認
        assert result.analysis_time > 0

    def test_analyze_bad_dao2(self, analyzer, fixtures_dir):
        """Partition Key未使用問題を持つファイルの分析"""
        test_file = fixtures_dir / "sample_dao_bad2.java"
        result = analyzer.analyze_file(str(test_file))

        # 問題が検出されたことを確認
        assert result.total_issues > 0

        # Partition Key問題が検出されたことを確認
        assert result.critical_count >= 1

    def test_analyze_good_dao(self, analyzer, fixtures_dir):
        """問題のないファイルの分析"""
        test_file = fixtures_dir / "sample_dao_good.java"
        result = analyzer.analyze_file(str(test_file))

        # ファイルは分析されるが、問題は検出されない
        assert result.total_files == 1
        assert result.total_issues == 0


class TestDirectoryAnalysis:
    """ディレクトリ分析のテスト"""

    def test_analyze_fixtures_directory(self, analyzer, fixtures_dir):
        """フィクスチャディレクトリ全体の分析"""
        result = analyzer.analyze_directory(str(fixtures_dir))

        # 複数ファイルが分析されたことを確認
        assert result.total_files >= 3

        # 問題が検出されたことを確認（bad1, bad2, bad3から）
        assert result.total_issues > 0

        # 各重要度の問題が存在することを確認
        assert result.critical_count > 0  # Partition Key問題
        assert result.high_count > 0  # ALLOW FILTERING問題

    def test_analyze_empty_directory(self, analyzer, tmp_path):
        """空のディレクトリの分析"""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = analyzer.analyze_directory(str(empty_dir))

        # ファイルがないので問題も検出されない
        assert result.total_files == 0
        assert result.total_issues == 0

    def test_analyze_nonexistent_directory(self, analyzer, tmp_path):
        """存在しないディレクトリの分析"""
        nonexistent = tmp_path / "nonexistent"

        with pytest.raises(FileNotFoundError):
            analyzer.analyze_directory(str(nonexistent))


class TestReportGeneration:
    """レポート生成のテスト"""

    def test_json_report_generation(self, analyzer, fixtures_dir, tmp_path):
        """JSONレポート生成"""
        # 分析実行
        result = analyzer.analyze_file(str(fixtures_dir / "sample_dao_bad1.java"))

        # JSONレポート生成
        reporter = JSONReporter()
        report = reporter.generate(result)

        # 有効なJSONであることを確認
        data = json.loads(report)
        assert "summary" in data
        assert "issues" in data

        # ファイルに保存
        output_file = tmp_path / "report.json"
        reporter.save(report, str(output_file))

        # ファイルが存在することを確認
        assert output_file.exists()

        # ファイル内容が正しいことを確認
        with open(output_file, encoding="utf-8") as f:
            saved_data = json.load(f)
        assert saved_data["summary"]["total_issues"] == result.total_issues

    def test_markdown_report_generation(self, analyzer, fixtures_dir, tmp_path):
        """Markdownレポート生成"""
        # 分析実行
        result = analyzer.analyze_file(str(fixtures_dir / "sample_dao_bad1.java"))

        # Markdownレポート生成
        reporter = MarkdownReporter()
        report = reporter.generate(result)

        # Markdown要素を確認
        assert "# Cassandra Code Analysis Report" in report
        assert "## Summary" in report

        # ファイルに保存
        output_file = tmp_path / "report.md"
        reporter.save(report, str(output_file))

        # ファイルが存在することを確認
        assert output_file.exists()

    def test_html_report_generation(self, analyzer, fixtures_dir, tmp_path):
        """HTMLレポート生成"""
        # 分析実行
        result = analyzer.analyze_file(str(fixtures_dir / "sample_dao_bad1.java"))

        # HTMLレポート生成
        reporter = HTMLReporter()
        report = reporter.generate(result)

        # HTML要素を確認
        assert "<!DOCTYPE html>" in report
        assert "<html" in report
        assert "</html>" in report

        # ファイルに保存
        output_file = tmp_path / "report.html"
        reporter.save(report, str(output_file))

        # ファイルが存在することを確認
        assert output_file.exists()

    def test_all_reports_generation(self, analyzer, fixtures_dir, tmp_path):
        """全形式のレポート生成"""
        # 分析実行
        result = analyzer.analyze_directory(str(fixtures_dir))

        # 3形式全てのレポートを生成
        reports = {
            "json": (JSONReporter(), "report.json"),
            "markdown": (MarkdownReporter(), "report.md"),
            "html": (HTMLReporter(), "report.html"),
        }

        for format_name, (reporter, filename) in reports.items():
            output_file = tmp_path / filename
            report = reporter.generate_and_save(result, str(output_file))

            # ファイルが存在することを確認
            assert output_file.exists(), f"{format_name} report not found"

            # 内容が空でないことを確認
            assert len(report) > 0, f"{format_name} report is empty"


class TestConfigurationOptions:
    """設定オプションのテスト"""

    def test_custom_detector_config(self, fixtures_dir):
        """カスタム検出器設定"""
        # カスタム閾値でアナライザーを作成
        config = {
            "detector_configs": {
                "batch_size": {"threshold": 50}
            }
        }
        analyzer = CassandraAnalyzer(config=config)

        result = analyzer.analyze_file(str(fixtures_dir / "sample_dao_bad3.java"))

        # カスタム設定が適用されたことを（間接的に）確認
        # Phase 1ではBatchStatementオブジェクトは検出できないので、
        # 設定が正しく読み込まれたことを確認
        assert analyzer.detectors[2].config.get("threshold") == 50

    def test_selective_detectors(self, fixtures_dir):
        """選択的な検出器の有効化"""
        # ALLOW FILTERINGのみ有効
        config = {
            "detectors": ["allow_filtering"]
        }
        analyzer = CassandraAnalyzer(config=config)

        result = analyzer.analyze_file(str(fixtures_dir / "sample_dao_bad1.java"))

        # ALLOW FILTERING問題のみが検出されることを確認
        # （Prepared Statement問題は検出されない）
        assert len(analyzer.detectors) == 1

    def test_all_detectors_disabled(self, fixtures_dir):
        """全検出器無効化"""
        config = {
            "detectors": []
        }
        analyzer = CassandraAnalyzer(config=config)

        result = analyzer.analyze_file(str(fixtures_dir / "sample_dao_bad1.java"))

        # 検出器がないので問題も検出されない
        assert len(analyzer.detectors) == 0
        assert result.total_issues == 0


class TestErrorHandling:
    """エラーハンドリングのテスト"""

    def test_invalid_file_path(self, analyzer):
        """無効なファイルパスの処理"""
        # 存在しないファイルを分析
        result = analyzer.analyze_file("nonexistent_file.java")

        # エラーは例外にならず、ファイルはリストに追加されるが問題は検出されない
        assert result.total_files == 1
        assert result.total_issues == 0

    def test_non_java_file(self, analyzer, tmp_path):
        """Java以外のファイルの処理"""
        # テキストファイルを作成
        text_file = tmp_path / "test.txt"
        text_file.write_text("This is not a Java file")

        # 分析を試みる
        result = analyzer.analyze_file(str(text_file))

        # エラーは発生しないが、問題も検出されない
        # （パーサーがJavaコードを見つけられない）
        assert result.total_files == 1
        assert result.total_issues == 0

    def test_malformed_java_file(self, analyzer, tmp_path):
        """構文エラーを含むJavaファイルの処理"""
        # 不正なJavaファイルを作成
        bad_java = tmp_path / "bad.java"
        bad_java.write_text("public class Bad { this is not valid Java }")

        # 分析を試みる
        result = analyzer.analyze_file(str(bad_java))

        # パーサーエラーが発生しても継続
        # ファイルはリストに追加されるが、問題は検出されない
        assert result.total_files == 1
        assert result.total_issues == 0


class TestAnalysisMetrics:
    """分析メトリクスのテスト"""

    def test_analysis_time_recorded(self, analyzer, fixtures_dir):
        """分析時間が記録されることを確認"""
        result = analyzer.analyze_file(str(fixtures_dir / "sample_dao_good.java"))

        # 分析時間が記録されている
        assert result.analysis_time > 0
        assert result.analysis_time < 10.0  # 10秒以内で完了するはず

    def test_file_count_accurate(self, analyzer, fixtures_dir):
        """ファイル数が正確にカウントされることを確認"""
        result = analyzer.analyze_directory(str(fixtures_dir))

        # analyzed_filesの長さとtotal_filesが一致
        assert result.total_files == len(result.analyzed_files)

    def test_issue_count_accurate(self, analyzer, fixtures_dir):
        """問題数が正確にカウントされることを確認"""
        result = analyzer.analyze_directory(str(fixtures_dir))

        # total_issuesとissuesリストの長さが一致
        assert result.total_issues == len(result.issues)

        # 重要度別カウントの合計がtotal_issuesと一致
        severity_total = (
            result.critical_count
            + result.high_count
            + result.medium_count
            + result.low_count
        )
        assert severity_total == result.total_issues


class TestIntegrationScenarios:
    """統合シナリオのテスト"""

    def test_complete_analysis_workflow(self, analyzer, fixtures_dir, tmp_path):
        """完全な分析ワークフロー"""
        # 1. ディレクトリ分析
        result = analyzer.analyze_directory(str(fixtures_dir))

        # 2. 結果の検証
        assert result.total_files > 0
        assert result.total_issues > 0

        # 3. 全形式でレポート生成
        json_reporter = JSONReporter()
        md_reporter = MarkdownReporter()
        html_reporter = HTMLReporter()

        json_file = tmp_path / "analysis_report.json"
        md_file = tmp_path / "analysis_report.md"
        html_file = tmp_path / "analysis_report.html"

        json_reporter.generate_and_save(result, str(json_file))
        md_reporter.generate_and_save(result, str(md_file))
        html_reporter.generate_and_save(result, str(html_file))

        # 4. 全ファイルが生成されたことを確認
        assert json_file.exists()
        assert md_file.exists()
        assert html_file.exists()

        # 5. ファイルサイズが妥当であることを確認
        assert json_file.stat().st_size > 100
        assert md_file.stat().st_size > 100
        assert html_file.stat().st_size > 1000  # HTMLはCSSを含むので大きい
