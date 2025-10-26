"""
Graph Builder Demo Script

GraphBuilderとNeo4jClientの使用例を示します。
"""

import sys
import io

# Windows console encoding fix
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from src.graph_analyzer.graph.graph_builder import GraphBuilder
from src.graph_analyzer.models.schema import NodeType, RelationType


def main():
    """デモメイン関数"""
    print("=" * 60)
    print("Phase 3 Graph Builder Demo")
    print("=" * 60)

    # サンプル分析結果（Phase 1のフォーマット）
    sample_analysis_result = {
        "analyzed_files": [
            "/src/main/java/com/example/dao/UserDAO.java",
            "/src/main/java/com/example/dao/OrderDAO.java",
        ],
        "total_issues": 3,
        "issues_by_severity": {"high": 2, "medium": 1},
        "issues": [
            {
                "detector": "AllowFilteringDetector",
                "type": "ALLOW_FILTERING",
                "severity": "high",
                "file": "/src/main/java/com/example/dao/UserDAO.java",
                "line": 42,
                "message": "ALLOW FILTERING detected in query",
                "cql": "SELECT * FROM users WHERE email = ? ALLOW FILTERING",
                "recommendation": "Add email to the partition key or use a secondary index",
                "evidence": ["ALLOW FILTERING clause found"],
                "confidence": 1.0,
            },
            {
                "detector": "PartitionKeyDetector",
                "type": "NO_PARTITION_KEY",
                "severity": "high",
                "file": "/src/main/java/com/example/dao/UserDAO.java",
                "line": 55,
                "message": "Query missing partition key",
                "cql": "SELECT * FROM users WHERE status = ?",
                "recommendation": "Include user_id in WHERE clause",
                "evidence": ["No partition key in WHERE clause"],
                "confidence": 0.9,
            },
            {
                "detector": "BatchSizeDetector",
                "type": "LARGE_BATCH",
                "severity": "medium",
                "file": "/src/main/java/com/example/dao/OrderDAO.java",
                "line": 78,
                "message": "Batch operation with 150 statements",
                "cql": "BEGIN BATCH ... END BATCH",
                "recommendation": "Reduce batch size to < 100 statements",
                "evidence": ["150 statements in batch"],
                "confidence": 1.0,
            },
        ],
        "analysis_time": 2.5,
        "timestamp": "2025-01-27T10:00:00",
    }

    # GraphBuilderを初期化
    print("\n📊 GraphBuilder初期化中...")
    builder = GraphBuilder()

    # 分析結果からグラフを構築
    print("🔨 分析結果からグラフを構築中...")
    nodes, relationships = builder.build_from_analysis_result(sample_analysis_result)

    # 結果を表示
    print(f"\n✅ グラフ構築完了!")
    print(f"   ノード数: {len(nodes)}")
    print(f"   リレーションシップ数: {len(relationships)}")

    # ノードタイプ別の集計
    print("\n📈 ノードタイプ別集計:")
    node_type_counts = {}
    for node in nodes:
        node_type_counts[node.node_type] = node_type_counts.get(node.node_type, 0) + 1

    for node_type, count in sorted(node_type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {node_type.value:15s}: {count:3d} 個")

    # リレーションシップタイプ別の集計
    print("\n🔗 リレーションシップタイプ別集計:")
    rel_type_counts = {}
    for rel in relationships:
        rel_type_counts[rel.relation_type] = rel_type_counts.get(rel.relation_type, 0) + 1

    for rel_type, count in sorted(rel_type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {rel_type.value:15s}: {count:3d} 個")

    # 具体的なノード例を表示
    print("\n📝 ノード例:")

    # ファイルノード
    file_nodes = [n for n in nodes if n.node_type == NodeType.FILE]
    if file_nodes:
        print(f"\n   FileNode: {file_nodes[0].properties.get('path')}")

    # クラスノード
    class_nodes = [n for n in nodes if n.node_type == NodeType.CLASS]
    if class_nodes:
        print(f"   ClassNode: {class_nodes[0].properties.get('name')}")

    # クエリノード
    query_nodes = [n for n in nodes if n.node_type == NodeType.QUERY]
    if query_nodes:
        cql = query_nodes[0].properties.get('cql', '')
        print(f"   CQLQueryNode: {cql[:60]}...")

    # テーブルノード
    table_nodes = [n for n in nodes if n.node_type == NodeType.TABLE]
    if table_nodes:
        tables = [n.properties.get('name') for n in table_nodes]
        print(f"   TableNodes: {', '.join(tables)}")

    # 問題ノード
    issue_nodes = [n for n in nodes if n.node_type == NodeType.ISSUE]
    if issue_nodes:
        issue = issue_nodes[0]
        print(
            f"   IssueNode: {issue.properties.get('issue_type')} "
            f"({issue.properties.get('severity')})"
        )

    # グラフ階層の例
    print("\n🌲 グラフ階層の例:")
    print("   File → Class → Method → CQLQuery → Table")
    print("                              ↓")
    print("                           Issue")

    # Neo4jへのインポート準備ができていることを示す
    print("\n💾 Neo4jへのインポート準備:")
    print(f"   client.batch_create_nodes(nodes)  # {len(nodes)}個のノードを作成")
    print(
        f"   client.batch_create_relationships(relationships)  # {len(relationships)}個のリレーションシップを作成"
    )

    print("\n" + "=" * 60)
    print("✅ デモ完了")
    print("=" * 60)


if __name__ == "__main__":
    main()
