"""
Cassandra Analyzer CLI

コマンドラインインターフェース
"""
import argparse
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import json

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from .analyzer import CassandraAnalyzer
from .reporters import JSONReporter, MarkdownReporter, HTMLReporter


def load_config(config_path: Path) -> Dict[str, Any]:
    """
    設定ファイルを読み込み

    Args:
        config_path: 設定ファイルのパス

    Returns:
        設定辞書
    """
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)

    if config_path.suffix in [".yaml", ".yml"]:
        if not HAS_YAML:
            print("Error: PyYAML is required for YAML config files.")
            print("Install it with: pip install pyyaml")
            sys.exit(1)
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    elif config_path.suffix == ".json":
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        print(f"Error: Unsupported config format: {config_path.suffix}")
        print("Supported formats: .yaml, .yml, .json")
        sys.exit(1)


def save_config(config: Dict[str, Any], output_path: Path) -> None:
    """
    設定ファイルを保存

    Args:
        config: 設定辞書
        output_path: 出力パス
    """
    if output_path.suffix in [".yaml", ".yml"]:
        if not HAS_YAML:
            print("Error: PyYAML is required for YAML output.")
            print("Install it with: pip install pyyaml")
            sys.exit(1)
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    elif output_path.suffix == ".json":
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    else:
        print(f"Error: Unsupported output format: {output_path.suffix}")
        sys.exit(1)

    print(f"Config saved to: {output_path}")


def get_default_config() -> Dict[str, Any]:
    """
    デフォルト設定を取得

    Returns:
        デフォルト設定辞書
    """
    return {
        "parser": {
            "type": "regex",  # "regex" or "ast"
            "resolve_constants": True,
        },
        "detectors": [
            "allow_filtering",
            "partition_key",
            "batch_size",
            "prepared_statement"
        ],
        "detector_configs": {
            "allow_filtering": {
                "severity": "high",
                "enabled": True,
            },
            "partition_key": {
                "severity": "critical",
                "enabled": True,
            },
            "batch_size": {
                "severity": "medium",
                "enabled": True,
                "max_batch_size": 100,
            },
            "prepared_statement": {
                "severity": "medium",
                "enabled": True,
            }
        },
        "output": {
            "formats": ["json", "markdown"],
            "directory": "reports",
        }
    }


def cmd_analyze(args) -> int:
    """
    分析コマンド

    Args:
        args: コマンドライン引数

    Returns:
        終了コード
    """
    # 設定を読み込み
    config = {}
    if args.config:
        config = load_config(args.config)

    # アナライザーを初期化
    analyzer = CassandraAnalyzer(config=config)

    # 入力の検証
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input path not found: {input_path}")
        return 1

    # 分析を実行
    print(f"Analyzing: {input_path}")
    try:
        if input_path.is_file():
            result = analyzer.analyze_file(str(input_path))
        elif input_path.is_dir():
            pattern = args.pattern or "**/*.java"
            result = analyzer.analyze_directory(str(input_path), pattern)
        else:
            print(f"Error: Invalid input path: {input_path}")
            return 1

        print(f"\nAnalysis completed in {result.analysis_time:.2f}s")
        print(f"Files analyzed: {result.total_files}")
        print(f"Total issues found: {result.total_issues}")

        # 重要度別の統計
        if result.issues_by_severity:
            print("\nIssues by severity:")
            for severity, count in sorted(result.issues_by_severity.items()):
                print(f"  {severity}: {count}")

        # レポートを生成
        output_dir = Path(args.output) if args.output else Path("reports")
        output_dir.mkdir(parents=True, exist_ok=True)

        formats = args.format if args.format else ["json"]

        for fmt in formats:
            if fmt == "json":
                reporter = JSONReporter()
                output_file = output_dir / "report.json"
            elif fmt == "markdown":
                reporter = MarkdownReporter()
                output_file = output_dir / "report.md"
            elif fmt == "html":
                reporter = HTMLReporter()
                output_file = output_dir / "report.html"
            else:
                print(f"Warning: Unknown format '{fmt}', skipping")
                continue

            reporter.generate_and_save(result, str(output_file))
            print(f"Report saved: {output_file}")

        return 0 if result.total_issues == 0 else 1

    except Exception as e:
        print(f"Error during analysis: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_config(args) -> int:
    """
    設定コマンド

    Args:
        args: コマンドライン引数

    Returns:
        終了コード
    """
    if args.init:
        # デフォルト設定を生成
        output_path = Path(args.output) if args.output else Path("cassandra-analyzer.yaml")

        if output_path.exists() and not args.force:
            print(f"Error: Config file already exists: {output_path}")
            print("Use --force to overwrite")
            return 1

        config = get_default_config()
        save_config(config, output_path)
        print("Default configuration created successfully")
        return 0

    elif args.validate:
        # 設定ファイルを検証
        if not args.config:
            print("Error: --config is required with --validate")
            return 1

        try:
            config = load_config(Path(args.config))
            print("Configuration is valid")

            # 簡易検証
            if "parser" in config:
                parser_type = config["parser"].get("type", "regex")
                if parser_type not in ["regex", "ast"]:
                    print(f"Warning: Unknown parser type: {parser_type}")

            if "detectors" in config:
                print(f"Enabled detectors: {', '.join(config['detectors'])}")

            return 0
        except Exception as e:
            print(f"Error: Invalid configuration: {e}")
            return 1

    elif args.show:
        # 現在の設定を表示
        if args.config:
            config = load_config(Path(args.config))
        else:
            config = get_default_config()

        print(json.dumps(config, indent=2, ensure_ascii=False))
        return 0

    else:
        print("Error: No action specified. Use --init, --validate, or --show")
        return 1


def create_parser() -> argparse.ArgumentParser:
    """
    ArgumentParserを作成

    Returns:
        ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog="cassandra-analyzer",
        description="Cassandra Query Analyzer - Detect anti-patterns in Cassandra usage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a single file
  cassandra-analyzer analyze UserDao.java

  # Analyze a directory
  cassandra-analyzer analyze src/main/java/dao

  # Use custom config
  cassandra-analyzer analyze --config config.yaml src/

  # Generate reports in multiple formats
  cassandra-analyzer analyze --format json markdown html src/

  # Initialize default config
  cassandra-analyzer config --init

  # Validate config
  cassandra-analyzer config --validate --config my-config.yaml
        """
    )

    parser.add_argument(
        "--version",
        action="version",
        version="cassandra-analyzer 2.0.0 (Phase 2)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Analyze コマンド
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze Java files for Cassandra anti-patterns"
    )
    analyze_parser.add_argument(
        "input",
        type=str,
        help="Input file or directory to analyze"
    )
    analyze_parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (YAML or JSON)"
    )
    analyze_parser.add_argument(
        "--output",
        type=str,
        help="Output directory for reports (default: reports/)"
    )
    analyze_parser.add_argument(
        "--format",
        nargs="+",
        choices=["json", "markdown", "html"],
        help="Report format(s) (default: json)"
    )
    analyze_parser.add_argument(
        "--pattern",
        type=str,
        help="File pattern for directory analysis (default: **/*.java)"
    )
    analyze_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )

    # Config コマンド
    config_parser = subparsers.add_parser(
        "config",
        help="Manage configuration"
    )
    config_parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize default configuration file"
    )
    config_parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate configuration file"
    )
    config_parser.add_argument(
        "--show",
        action="store_true",
        help="Show current configuration"
    )
    config_parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file"
    )
    config_parser.add_argument(
        "--output",
        type=str,
        help="Output path for config file (with --init)"
    )
    config_parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite existing config (with --init)"
    )

    return parser


def main() -> int:
    """
    メインエントリーポイント

    Returns:
        終了コード
    """
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "analyze":
        return cmd_analyze(args)
    elif args.command == "config":
        return cmd_config(args)
    else:
        print(f"Error: Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
