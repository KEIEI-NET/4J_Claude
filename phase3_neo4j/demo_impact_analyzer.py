"""
Impact Analyzer Demo Script

ImpactAnalyzerの使用例を示します。
"""

import sys
import io

# Windows console encoding fix
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from unittest.mock import Mock
from src.graph_analyzer.analyzers.impact_analyzer import ImpactAnalyzer, RiskLevel


def main():
    """デモメイン関数"""
    print("=" * 70)
    print("Phase 3 Impact Analyzer Demo")
    print("=" * 70)

    # モックNeo4jクライアント（デモ用）
    mock_client = Mock()

    # ImpactAnalyzerを初期化
    print("\n📊 ImpactAnalyzer初期化中...")
    analyzer = ImpactAnalyzer(mock_client)
    print("✅ ImpactAnalyzer初期化完了")

    # ===== デモ 1: テーブル変更の影響分析 =====
    print("\n" + "=" * 70)
    print("🔍 デモ 1: テーブル変更の影響分析")
    print("=" * 70)
    print("テーブル: 'users'")

    # モックデータを設定
    mock_client.execute_query.side_effect = [
        # テーブルを使用しているファイル
        [
            {
                "file_path": "/src/main/java/com/example/dao/UserDAO.java",
                "class_name": "UserDAO",
                "method_name": "findByEmail",
                "query_count": 3,
            },
            {
                "file_path": "/src/main/java/com/example/service/UserService.java",
                "class_name": "UserService",
                "method_name": "getUser",
                "query_count": 2,
            },
            {
                "file_path": "/src/main/java/com/example/service/AuthService.java",
                "class_name": "AuthService",
                "method_name": "authenticate",
                "query_count": 1,
            },
        ],
        # アクセスパターン
        [
            {"query_type": "SELECT", "count": 5},
            {"query_type": "INSERT", "count": 1},
            {"query_type": "UPDATE", "count": 2},
        ],
        # 問題
        [
            {"issue_type": "ALLOW_FILTERING", "severity": "high", "issue_count": 1},
            {"issue_type": "NO_PARTITION_KEY", "severity": "medium", "issue_count": 1},
        ],
    ]

    result = analyzer.analyze_table_change_impact("users", include_issues=True)

    print(f"\n✅ 分析完了")
    print(f"\n📈 影響範囲:")
    print(f"   影響を受けるファイル: {len(result.affected_files)}個")
    print(f"   影響を受けるクラス: {len(result.affected_classes)}個")
    print(f"   影響を受けるメソッド: {len(result.affected_methods)}個")

    print(f"\n⚠️  リスク評価:")
    print(f"   リスクレベル: {result.risk_level.value.upper()}")
    print(f"   リスクスコア: {result.risk_score:.2f}")

    print(f"\n📄 影響を受けるファイル:")
    for file_path in result.affected_files[:5]:
        print(f"   - {file_path}")

    print(f"\n📊 アクセスパターン:")
    for pattern in result.details.get("access_patterns", []):
        print(f"   {pattern['type']}: {pattern['count']}回")

    if "issues" in result.details:
        print(f"\n🐛 関連する問題:")
        for issue in result.details["issues"]:
            print(f"   [{issue['severity'].upper()}] {issue['type']}: {issue['count']}件")

    # ===== デモ 2: ファイル変更の影響分析 =====
    print("\n" + "=" * 70)
    print("🔍 デモ 2: ファイル変更の影響分析")
    print("=" * 70)
    print("ファイル: '/src/UserDAO.java'")

    mock_client.execute_query.side_effect = [
        [
            {"dependent_file": "/src/UserService.java", "depth": 1},
            {"dependent_file": "/src/OrderService.java", "depth": 1},
            {"dependent_file": "/src/UserController.java", "depth": 2},
            {"dependent_file": "/src/OrderController.java", "depth": 2},
            {"dependent_file": "/src/ReportService.java", "depth": 3},
        ]
    ]

    result = analyzer.analyze_file_change_impact("/src/UserDAO.java", recursive=True)

    print(f"\n✅ 分析完了")
    print(f"\n📈 依存関係:")
    print(f"   依存ファイル数: {len(result.affected_files)}個")
    print(f"   リスクレベル: {result.risk_level.value.upper()}")

    print(f"\n🌲 依存ツリー:")
    for dep in result.details.get("dependencies", [])[:5]:
        indent = "  " * dep["depth"]
        print(f"{indent}└─ Depth {dep['depth']}: {dep['file']}")

    # ===== デモ 3: クラスの依存関係分析 =====
    print("\n" + "=" * 70)
    print("🔍 デモ 3: クラスの依存関係分析")
    print("=" * 70)
    print("クラス: 'UserDAO'")

    mock_client.execute_query.side_effect = [
        [
            {"table_name": "users", "query_count": 10},
            {"table_name": "user_sessions", "query_count": 5},
            {"table_name": "user_preferences", "query_count": 2},
        ]
    ]

    result = analyzer.analyze_class_dependencies("UserDAO")

    print(f"\n✅ 分析完了")
    print(f"\n📊 使用しているテーブル:")
    for table_info in result.details.get("tables_used", []):
        print(f"   - {table_info['table']}: {table_info['query_count']}クエリ")

    # ===== デモ 4: 高リスクファイルの検出 =====
    print("\n" + "=" * 70)
    print("🔍 デモ 4: 高リスクファイルの検出")
    print("=" * 70)

    mock_client.execute_query.side_effect = [
        [
            {
                "file_path": "/src/CriticalDAO.java",
                "issue_count": 15,
                "severities": ["critical", "high"],
            },
            {
                "file_path": "/src/ProblematicService.java",
                "issue_count": 8,
                "severities": ["high", "medium"],
            },
            {
                "file_path": "/src/OldLegacyDAO.java",
                "issue_count": 12,
                "severities": ["critical", "high", "medium"],
            },
        ]
    ]

    high_risk_files = analyzer.get_high_risk_files(severities=["critical", "high"], limit=10)

    print(f"\n✅ 高リスクファイルを検出")
    print(f"\n⚠️  問題が多いファイル（上位3件）:")
    for i, file_info in enumerate(high_risk_files[:3], 1):
        print(f"\n   {i}. {file_info['file_path']}")
        print(f"      問題数: {file_info['issue_count']}件")
        print(f"      重要度: {', '.join(file_info['severities'])}")

    # ===== デモ 5: 依存関係チェーンの追跡 =====
    print("\n" + "=" * 70)
    print("🔍 デモ 5: 依存関係チェーンの追跡")
    print("=" * 70)
    print("開始ファイル: '/src/UserDAO.java'")
    print("目標ファイル: '/src/UserController.java'")

    mock_client.execute_query.side_effect = [
        [
            {
                "dependency_chain": [
                    "/src/UserDAO.java",
                    "/src/UserService.java",
                    "/src/UserController.java",
                ]
            }
        ]
    ]

    chain = analyzer.trace_dependency_chain(
        "/src/UserDAO.java", "/src/UserController.java", max_depth=5
    )

    if chain:
        print(f"\n✅ 依存関係チェーンを発見")
        print(f"\n🔗 チェーン ({len(chain)}ステップ):")
        for i, file_path in enumerate(chain):
            if i == 0:
                print(f"   📁 {file_path}")
            elif i == len(chain) - 1:
                print(f"   {'   ' * i}└─> 🎯 {file_path}")
            else:
                print(f"   {'   ' * i}└─> 📄 {file_path}")
    else:
        print(f"\n❌ 依存関係チェーンが見つかりませんでした")

    # ===== リスクレベルの例 =====
    print("\n" + "=" * 70)
    print("📊 リスクレベルの計算例")
    print("=" * 70)

    examples = [
        (60, 15, 30, "CRITICAL", "大規模なコアユーティリティ"),
        (30, 10, 15, "HIGH", "重要なサービスクラス"),
        (12, 5, 8, "MEDIUM", "一般的なDAOクラス"),
        (3, 2, 3, "LOW", "小規模なユーティリティ"),
        (0, 0, 0, "MINIMAL", "影響なし"),
    ]

    for files, classes, methods, expected_level, description in examples:
        level, score = analyzer._calculate_risk(files, classes, methods)
        print(f"\n   {description}:")
        print(f"      ファイル: {files}, クラス: {classes}, メソッド: {methods}")
        print(f"      → {level.value.upper()} (スコア: {score:.2f})")

    # ===== サマリー =====
    print("\n" + "=" * 70)
    print("✅ デモ完了")
    print("=" * 70)

    print("\n💡 ImpactAnalyzerの主な機能:")
    print("   1. テーブル変更の影響分析 - テーブル変更がどのファイルに影響するか")
    print("   2. ファイル変更の影響分析 - ファイル変更の依存関係を追跡")
    print("   3. クラスの依存関係分析 - クラスが使用しているテーブルを特定")
    print("   4. 高リスクファイル検出 - 問題が多いファイルを優先度順に取得")
    print("   5. 依存関係チェーン追跡 - 2つのファイル間の最短パスを発見")
    print("   6. リスク評価 - 影響範囲からリスクレベルを自動計算")

    print("\n📊 Cypherクエリライブラリ:")
    print("   - テーブル使用ファイル取得")
    print("   - ファイル依存関係取得（再帰対応）")
    print("   - クラス・テーブル依存関係")
    print("   - 問題が多いファイル取得")
    print("   - アクセスパターン分析")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
