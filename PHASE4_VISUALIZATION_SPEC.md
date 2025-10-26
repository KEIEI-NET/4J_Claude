# Phase 4: 可視化・影響範囲分析レイヤー 詳細仕様書

**バージョン**: v1.0.0
**作成日**: 2025年10月27日
**対象**: Phase 4実装担当者

---

## 📋 目次

1. [概要](#1-概要)
2. [アーキテクチャ設計](#2-アーキテクチャ設計)
3. [バックエンドAPI設計](#3-バックエンドapi設計)
4. [フロントエンド設計](#4-フロントエンド設計)
5. [グラフ可視化設計](#5-グラフ可視化設計)
6. [影響範囲分析アルゴリズム](#6-影響範囲分析アルゴリズム)
7. [実装計画](#7-実装計画)
8. [テスト戦略](#8-テスト戦略)

---

## 1. 概要

### 1.1 Phase 4の目的

Phase 3で構築したNeo4jグラフDBを活用し、開発者に直接的な価値を提供する**可視化・分析レイヤー**を実装する。

### 1.2 主要機能

| 機能 | 説明 | 優先度 |
|-----|------|--------|
| **グラフ可視化** | D3.jsによるインタラクティブな依存関係グラフ | 🔴 Critical |
| **影響範囲分析** | ファイル変更時の影響を受けるファイル/メソッドの特定 | 🔴 Critical |
| **バグ特定支援** | エラーログから関連コードを追跡 | 🟡 High |
| **リファクタリングリスク評価** | 変更の影響範囲とリスクレベルを定量化 | 🟡 High |
| **循環依存検出** | 循環参照の可視化と警告 | 🟢 Medium |
| **パスファインダー** | 2つのノード間の依存パスを検索 | 🟢 Medium |

### 1.3 ユーザーストーリー

#### ストーリー1: バグ影響範囲の特定
```
As a 開発者
I want ファイル名を入力すると依存関係グラフが表示される
So that バグの影響範囲を素早く把握できる

受け入れ基準:
- [ ] ファイル名で検索できる
- [ ] 10秒以内にグラフが表示される
- [ ] 依存先/依存元が色分けされている
- [ ] ノードをクリックすると詳細情報が表示される
```

#### ストーリー2: リファクタリング影響分析
```
As a アーキテクト
I want リファクタリング対象のクラスを選択
So that 影響を受けるファイル数とリスクレベルを確認できる

受け入れ基準:
- [ ] 影響を受けるファイル数が表示される
- [ ] リスクレベル (High/Medium/Low) が評価される
- [ ] 影響範囲が定量化される (例: 47ファイル, 183メソッド)
- [ ] 推奨テスト箇所が提示される
```

#### ストーリー3: エラーログからの追跡
```
As a サポートエンジニア
I want エラーログのスタックトレースを貼り付け
So that 関連するソースファイルと依存関係を表示できる

受け入れ基準:
- [ ] スタックトレースからファイル名を抽出
- [ ] 関連ファイルの依存関係グラフを表示
- [ ] 根本原因の可能性があるファイルをハイライト
```

---

## 2. アーキテクチャ設計

### 2.1 全体構成

```
┌─────────────────────────────────────────────────────────┐
│                    フロントエンド                         │
│                 (React + TypeScript)                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ Dashboard   │  │ Graph View  │  │ Analysis    │   │
│  │ Component   │  │ (D3.js)     │  │ Panel       │   │
│  └─────────────┘  └─────────────┘  └─────────────┘   │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ File        │  │ Impact      │  │ Risk        │   │
│  │ Explorer    │  │ Visualizer  │  │ Assessor    │   │
│  └─────────────┘  └─────────────┘  └─────────────┘   │
│                                                          │
└────────────────────────┬────────────────────────────────┘
                         │ REST API
                         │
┌────────────────────────┴────────────────────────────────┐
│                  バックエンドAPI                          │
│                    (FastAPI)                             │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌───────────────────────────────────────────────┐     │
│  │  POST /api/impact-analysis                    │     │
│  │  POST /api/refactoring-risk                   │     │
│  │  GET  /api/dependencies/{file_path}           │     │
│  │  GET  /api/graph/neighbors/{node_id}          │     │
│  │  POST /api/path-finder                        │     │
│  │  GET  /api/circular-dependencies              │     │
│  └───────────────────────────────────────────────┘     │
│                                                          │
└────────────────────────┬────────────────────────────────┘
                         │ Cypher Queries
                         │
┌────────────────────────┴────────────────────────────────┐
│                    Neo4j GraphDB                         │
│                  (Phase 3で構築済み)                     │
└─────────────────────────────────────────────────────────┘
```

### 2.2 技術スタック

| レイヤー | 技術 | バージョン | 理由 |
|---------|------|-----------|------|
| **フロントエンド** | React | 18.2+ | 標準的なUIライブラリ |
| **言語** | TypeScript | 5.0+ | 型安全性 |
| **状態管理** | Zustand | 4.5+ | シンプルな状態管理 |
| **グラフ可視化** | D3.js | 7.8+ | 最も強力なグラフ描画ライブラリ |
| **UIコンポーネント** | Ant Design | 5.12+ | 豊富なコンポーネント |
| **HTTPクライアント** | Axios | 1.6+ | Promise-based |
| **バックエンド** | FastAPI | 0.109+ | 高速・非同期対応 |
| **Neo4jドライバー** | neo4j-driver | 5.15+ | 公式Python driver |
| **API検証** | Pydantic | 2.5+ | 型安全なAPI |
| **テスト (FE)** | Vitest + React Testing Library | latest | 高速テスト |
| **テスト (BE)** | pytest | 7.4+ | 標準的なPythonテスト |

---

## 3. バックエンドAPI設計

### 3.1 エンドポイント一覧

#### 3.1.1 POST /api/impact-analysis

**目的**: 指定されたファイルまたはメソッドの変更が及ぼす影響範囲を分析

**リクエスト**:
```json
{
  "target_type": "file|class|method",
  "target_path": "src/main/java/com/example/UserService.java",
  "depth": 3,
  "include_indirect": true
}
```

**レスポンス**:
```json
{
  "target": {
    "type": "file",
    "path": "src/main/java/com/example/UserService.java",
    "name": "UserService.java"
  },
  "impact_summary": {
    "total_affected_files": 47,
    "total_affected_methods": 183,
    "total_affected_classes": 28,
    "risk_level": "high",
    "confidence": 0.92
  },
  "affected_files": [
    {
      "path": "src/main/java/com/example/OrderService.java",
      "distance": 1,
      "dependency_type": "direct",
      "affected_methods": ["createOrder", "updateOrder"],
      "risk_contribution": 0.15
    },
    {
      "path": "src/main/java/com/example/PaymentService.java",
      "distance": 2,
      "dependency_type": "indirect",
      "affected_methods": ["processPayment"],
      "risk_contribution": 0.08
    }
  ],
  "dependency_graph": {
    "nodes": [...],
    "edges": [...]
  }
}
```

**Neo4jクエリ例**:
```cypher
// 影響範囲の取得 (depth 3まで)
MATCH path = (target:File {path: $target_path})<-[:DEPENDS_ON*1..3]-(dependent:File)
RETURN DISTINCT dependent.path AS affected_file,
       length(path) AS distance,
       collect(DISTINCT [(dependent)-[:CONTAINS]->(m:Method) | m.name]) AS affected_methods
ORDER BY distance ASC
```

#### 3.1.2 POST /api/refactoring-risk

**目的**: リファクタリング時のリスク評価

**リクエスト**:
```json
{
  "target_files": [
    "src/main/java/com/example/UserService.java",
    "src/main/java/com/example/AuthService.java"
  ],
  "refactoring_type": "rename|move|extract|inline"
}
```

**レスポンス**:
```json
{
  "risk_assessment": {
    "overall_risk": "high",
    "risk_score": 7.8,
    "factors": {
      "affected_file_count": 47,
      "circular_dependencies": true,
      "test_coverage": 0.65,
      "complexity_increase": 1.2
    }
  },
  "recommendations": [
    "テストカバレッジを80%以上に向上させてください",
    "循環依存を解消してからリファクタリングしてください",
    "影響範囲が大きいため、段階的なリファクタリングを推奨します"
  ],
  "testing_checklist": [
    {
      "file": "OrderService.java",
      "methods": ["createOrder", "updateOrder"],
      "priority": "high"
    }
  ]
}
```

#### 3.1.3 GET /api/dependencies/{file_path}

**目的**: 指定されたファイルの依存関係を取得

**レスポンス**:
```json
{
  "file": {
    "path": "src/main/java/com/example/UserService.java",
    "language": "java",
    "size": 2048,
    "complexity": 45.2
  },
  "dependencies": {
    "imports": [
      "com.example.DatabaseService",
      "com.example.CacheService",
      "com.example.ValidationService"
    ],
    "dependents": [
      "com.example.OrderService",
      "com.example.AccountService"
    ],
    "dependency_count": 12,
    "dependent_count": 8
  },
  "methods": [
    {
      "name": "getUser",
      "calls": ["DatabaseService.query", "CacheService.get"],
      "called_by": ["OrderService.createOrder"]
    }
  ]
}
```

#### 3.1.4 GET /api/graph/neighbors/{node_id}

**目的**: 指定されたノードの隣接ノードを取得（グラフ表示用）

**クエリパラメータ**:
- `depth`: 深さ (デフォルト: 1)
- `direction`: `in|out|both` (デフォルト: both)
- `node_type`: フィルタするノードタイプ

**レスポンス**:
```json
{
  "center_node": {
    "id": "file:user-service",
    "type": "File",
    "label": "UserService.java",
    "properties": {...}
  },
  "neighbors": [
    {
      "node": {
        "id": "file:order-service",
        "type": "File",
        "label": "OrderService.java"
      },
      "relationship": {
        "type": "DEPENDS_ON",
        "direction": "outgoing",
        "properties": {"strength": 0.8}
      }
    }
  ]
}
```

#### 3.1.5 POST /api/path-finder

**目的**: 2つのノード間の依存パスを検索

**リクエスト**:
```json
{
  "source": "src/main/java/com/example/UserService.java",
  "target": "src/main/java/com/example/PaymentService.java",
  "max_depth": 5,
  "relationship_types": ["DEPENDS_ON", "CALLS"]
}
```

**レスポンス**:
```json
{
  "paths": [
    {
      "length": 2,
      "nodes": [
        {"type": "File", "name": "UserService.java"},
        {"type": "File", "name": "OrderService.java"},
        {"type": "File", "name": "PaymentService.java"}
      ],
      "relationships": [
        {"type": "DEPENDS_ON", "strength": 0.9},
        {"type": "CALLS", "strength": 0.7}
      ]
    }
  ],
  "shortest_path_length": 2,
  "total_paths_found": 3
}
```

#### 3.1.6 GET /api/circular-dependencies

**目的**: 循環依存の検出

**レスポンス**:
```json
{
  "circular_dependencies": [
    {
      "cycle_id": "cycle-1",
      "cycle_length": 3,
      "nodes": [
        "UserService.java",
        "OrderService.java",
        "PaymentService.java"
      ],
      "severity": "high"
    }
  ],
  "total_cycles": 5,
  "recommendation": "循環依存を解消してください"
}
```

**Neo4jクエリ**:
```cypher
// 循環依存の検出
MATCH path = (n:File)-[:DEPENDS_ON*2..10]->(n)
WHERE ALL(node in nodes(path) WHERE node:File)
RETURN DISTINCT [node in nodes(path) | node.name] AS cycle,
       length(path) AS cycle_length
ORDER BY cycle_length ASC
LIMIT 20
```

---

## 4. フロントエンド設計

### 4.1 コンポーネント構成

```
src/
├── components/
│   ├── Dashboard/
│   │   ├── Dashboard.tsx          # メインダッシュボード
│   │   ├── StatsPanel.tsx         # 統計情報パネル
│   │   └── QuickActions.tsx       # クイックアクション
│   ├── GraphView/
│   │   ├── GraphView.tsx          # D3.jsグラフコンポーネント
│   │   ├── GraphControls.tsx      # ズーム/フィルタコントロール
│   │   └── NodeDetails.tsx        # ノード詳細表示
│   ├── FileExplorer/
│   │   ├── FileTree.tsx           # ファイルツリー
│   │   ├── FileSearch.tsx         # ファイル検索
│   │   └── FileInfo.tsx           # ファイル情報表示
│   ├── ImpactAnalysis/
│   │   ├── ImpactPanel.tsx        # 影響範囲分析パネル
│   │   ├── AffectedFilesList.tsx  # 影響を受けるファイル一覧
│   │   └── RiskIndicator.tsx      # リスク指標表示
│   └── RefactoringRisk/
│       ├── RiskAssessment.tsx     # リスク評価表示
│       └── RecommendationsList.tsx # 推奨事項一覧
├── hooks/
│   ├── useGraph.ts                # グラフデータ取得
│   ├── useImpactAnalysis.ts       # 影響範囲分析
│   └── useDependencies.ts         # 依存関係取得
├── api/
│   ├── client.ts                  # Axiosクライアント
│   ├── impactAnalysisApi.ts       # 影響範囲分析API
│   └── graphApi.ts                # グラフAPI
├── stores/
│   ├── graphStore.ts              # グラフ状態管理 (Zustand)
│   └── uiStore.ts                 # UI状態管理
└── types/
    ├── graph.ts                   # グラフ型定義
    └── api.ts                     # API型定義
```

### 4.2 主要コンポーネント設計

#### 4.2.1 GraphView.tsx (D3.jsグラフ表示)

**責務**: インタラクティブなグラフ可視化

**Props**:
```typescript
interface GraphViewProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onNodeClick?: (node: GraphNode) => void;
  onEdgeClick?: (edge: GraphEdge) => void;
  highlightedNodes?: string[];
  width?: number;
  height?: number;
}
```

**主要機能**:
- ノード/エッジの描画
- ズーム/パン操作
- Force-directed layout
- ノード/エッジのツールチップ
- ハイライト表示

**実装例**:
```typescript
import * as d3 from 'd3';

export const GraphView: React.FC<GraphViewProps> = ({
  nodes,
  edges,
  onNodeClick,
  highlightedNodes = []
}) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);

    // Force simulation
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(edges).id(d => d.id))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2));

    // ノードの描画
    const node = svg.selectAll('.node')
      .data(nodes)
      .join('circle')
      .attr('class', 'node')
      .attr('r', 10)
      .attr('fill', d => highlightedNodes.includes(d.id) ? 'red' : 'blue')
      .on('click', (event, d) => onNodeClick?.(d));

    // エッジの描画
    const link = svg.selectAll('.link')
      .data(edges)
      .join('line')
      .attr('class', 'link')
      .attr('stroke', '#999');

    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      node
        .attr('cx', d => d.x)
        .attr('cy', d => d.y);
    });
  }, [nodes, edges, highlightedNodes]);

  return <svg ref={svgRef} width={width} height={height} />;
};
```

#### 4.2.2 ImpactPanel.tsx (影響範囲分析)

**責務**: 影響範囲の表示と分析

**機能**:
- ファイル選択
- 影響範囲の取得
- 影響を受けるファイル一覧
- リスクレベル表示
- グラフのハイライト

```typescript
export const ImpactPanel: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<string>('');
  const { data: impactData, isLoading } = useImpactAnalysis(selectedFile);

  return (
    <div className="impact-panel">
      <FileSearch onSelect={setSelectedFile} />

      {isLoading && <Spinner />}

      {impactData && (
        <>
          <RiskIndicator
            riskLevel={impactData.impact_summary.risk_level}
            affectedFiles={impactData.impact_summary.total_affected_files}
          />

          <AffectedFilesList files={impactData.affected_files} />

          <GraphView
            nodes={impactData.dependency_graph.nodes}
            edges={impactData.dependency_graph.edges}
            highlightedNodes={impactData.affected_files.map(f => f.path)}
          />
        </>
      )}
    </div>
  );
};
```

---

## 5. グラフ可視化設計

### 5.1 グラフレイアウトアルゴリズム

#### オプション1: Force-Directed Layout (推奨)
```typescript
const simulation = d3.forceSimulation(nodes)
  .force('link', d3.forceLink(edges).id(d => d.id).distance(100))
  .force('charge', d3.forceManyBody().strength(-300))
  .force('center', d3.forceCenter(width / 2, height / 2))
  .force('collision', d3.forceCollide().radius(30));
```

**利点**:
- 自然な配置
- インタラクティブ
- 大規模グラフに対応

**欠点**:
- 初期配置が不安定
- パフォーマンスに注意

#### オプション2: Hierarchical Layout
```typescript
const tree = d3.tree()
  .size([width, height])
  .separation((a, b) => (a.parent == b.parent ? 1 : 2) / a.depth);
```

**利点**:
- 階層構造が明確
- 依存関係の方向が分かりやすい

**欠点**:
- 循環依存に弱い
- 横幅が大きくなる

### 5.2 ノードスタイリング

```typescript
interface NodeStyle {
  // サイズ: ファイルサイズまたは複雑度に基づく
  radius: (node: GraphNode) => number;

  // 色: ノードタイプや影響度に基づく
  fill: (node: GraphNode) => string;

  // 枠線: 選択状態やハイライト
  stroke: (node: GraphNode) => string;
  strokeWidth: (node: GraphNode) => number;
}

const nodeStyle: NodeStyle = {
  radius: (node) => Math.sqrt(node.complexity) * 2 + 5,
  fill: (node) => {
    if (node.highlighted) return '#ff4d4f';
    if (node.type === 'File') return '#1890ff';
    if (node.type === 'Class') return '#52c41a';
    return '#d9d9d9';
  },
  stroke: (node) => node.selected ? '#000' : '#fff',
  strokeWidth: (node) => node.selected ? 3 : 1
};
```

### 5.3 エッジスタイリング

```typescript
const edgeStyle = {
  stroke: (edge: GraphEdge) => {
    if (edge.type === 'DEPENDS_ON') return '#1890ff';
    if (edge.type === 'CALLS') return '#52c41a';
    return '#d9d9d9';
  },
  strokeWidth: (edge: GraphEdge) => edge.strength * 3 + 1,
  strokeDasharray: (edge: GraphEdge) => {
    return edge.dependency_type === 'indirect' ? '5,5' : 'none';
  }
};
```

### 5.4 インタラクション

```typescript
// ズーム
const zoom = d3.zoom()
  .scaleExtent([0.1, 10])
  .on('zoom', (event) => {
    svg.select('.graph-container').attr('transform', event.transform);
  });

svg.call(zoom);

// ドラッグ
const drag = d3.drag()
  .on('start', (event, d) => {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  })
  .on('drag', (event, d) => {
    d.fx = event.x;
    d.fy = event.y;
  })
  .on('end', (event, d) => {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  });

node.call(drag);
```

---

## 6. 影響範囲分析アルゴリズム

### 6.1 影響範囲の計算

#### アルゴリズム: 幅優先探索 (BFS) + 重み付け

```python
from typing import List, Dict, Set
from collections import deque

def calculate_impact_range(
    neo4j_driver,
    target_file: str,
    max_depth: int = 3,
    include_indirect: bool = True
) -> Dict:
    """
    影響範囲を計算

    Returns:
        {
            'affected_files': List[{
                'path': str,
                'distance': int,
                'risk_contribution': float
            }],
            'total_risk_score': float
        }
    """
    affected = {}
    queue = deque([(target_file, 0, 1.0)])  # (file, depth, weight)
    visited = set()

    while queue:
        current_file, depth, weight = queue.popleft()

        if current_file in visited or depth > max_depth:
            continue

        visited.add(current_file)

        # Neo4jから依存ファイルを取得
        dependents = get_dependents(neo4j_driver, current_file)

        for dependent in dependents:
            dep_file = dependent['file']
            dep_strength = dependent['strength']  # 0.0 - 1.0

            # 重みの減衰 (深さに応じて影響が弱くなる)
            new_weight = weight * dep_strength * (0.7 ** depth)

            if dep_file not in affected or affected[dep_file]['weight'] < new_weight:
                affected[dep_file] = {
                    'path': dep_file,
                    'distance': depth + 1,
                    'weight': new_weight,
                    'risk_contribution': new_weight
                }

            if include_indirect:
                queue.append((dep_file, depth + 1, new_weight))

    # リスクスコアの計算
    total_risk = sum(f['risk_contribution'] for f in affected.values())

    return {
        'affected_files': sorted(
            affected.values(),
            key=lambda x: x['risk_contribution'],
            reverse=True
        ),
        'total_risk_score': total_risk
    }

def get_dependents(driver, file_path: str) -> List[Dict]:
    """Neo4jから依存ファイルを取得"""
    with driver.session() as session:
        result = session.run("""
            MATCH (target:File {path: $path})<-[dep:DEPENDS_ON]-(dependent:File)
            RETURN dependent.path AS file,
                   dep.strength AS strength
        """, path=file_path)

        return [
            {'file': record['file'], 'strength': record['strength']}
            for record in result
        ]
```

### 6.2 リスクレベルの評価

```python
def assess_risk_level(impact_data: Dict) -> str:
    """
    リスクレベルを評価: high|medium|low

    考慮要素:
    - 影響を受けるファイル数
    - 影響の深さ
    - 循環依存の有無
    - テストカバレッジ
    """
    affected_count = len(impact_data['affected_files'])
    total_risk = impact_data['total_risk_score']

    # ファイル数による判定
    if affected_count > 30:
        file_risk = 'high'
    elif affected_count > 10:
        file_risk = 'medium'
    else:
        file_risk = 'low'

    # リスクスコアによる判定
    if total_risk > 10.0:
        score_risk = 'high'
    elif total_risk > 5.0:
        score_risk = 'medium'
    else:
        score_risk = 'low'

    # 最大値を採用
    risk_levels = {'low': 1, 'medium': 2, 'high': 3}
    final_risk = max(file_risk, score_risk, key=lambda r: risk_levels[r])

    return final_risk
```

---

## 7. 実装計画

### 7.1 Week 1-2: バックエンドAPI

#### Day 1-2: 基盤セットアップ
- [ ] FastAPIプロジェクト初期化
- [ ] Neo4jドライバーセットアップ
- [ ] Pydanticモデル定義
- [ ] CORS設定

#### Day 3-5: コアAPI実装
- [ ] POST /api/impact-analysis
- [ ] GET /api/dependencies/{file_path}
- [ ] GET /api/graph/neighbors/{node_id}

#### Day 6-7: 高度な機能
- [ ] POST /api/refactoring-risk
- [ ] POST /api/path-finder
- [ ] GET /api/circular-dependencies

#### Day 8-10: テスト・最適化
- [ ] ユニットテスト
- [ ] Cypherクエリ最適化
- [ ] APIドキュメント (Swagger)

### 7.2 Week 3-4: フロントエンド基盤

#### Day 11-12: プロジェクトセットアップ
- [ ] React + TypeScript プロジェクト初期化 (Vite)
- [ ] Ant Design セットアップ
- [ ] Zustand状態管理
- [ ] Axios API クライアント

#### Day 13-15: D3.jsグラフコンポーネント
- [ ] GraphView基本実装
- [ ] Force-directed layout
- [ ] ノード/エッジのスタイリング
- [ ] ズーム/パン操作

#### Day 16-18: コアコンポーネント
- [ ] FileExplorer (ファイル検索)
- [ ] Dashboard (メイン画面)
- [ ] NodeDetails (ノード詳細表示)

#### Day 19-20: API統合・テスト
- [ ] バックエンドAPI統合
- [ ] エラーハンドリング
- [ ] コンポーネントテスト

### 7.3 Week 5-6: コア機能実装

#### Day 21-23: 影響範囲分析
- [ ] ImpactPanel実装
- [ ] 影響範囲の可視化
- [ ] AffectedFilesList
- [ ] RiskIndicator

#### Day 24-26: バグ特定支援
- [ ] エラーログ解析
- [ ] スタックトレースからの追跡
- [ ] 根本原因の推定

#### Day 27-30: リファクタリングリスク
- [ ] RiskAssessment表示
- [ ] 推奨事項の生成
- [ ] テストチェックリスト

### 7.4 Week 7-8: UX改善・テスト

#### Day 31-33: パフォーマンス最適化
- [ ] 大規模グラフの表示最適化
- [ ] レンダリング高速化
- [ ] メモリ使用量削減

#### Day 34-36: UX改善
- [ ] アニメーション追加
- [ ] ツールチップ改善
- [ ] キーボードショートカット

#### Day 37-40: テスト・ドキュメント
- [ ] E2Eテスト (Playwright)
- [ ] ユーザビリティテスト
- [ ] ユーザーマニュアル作成
- [ ] デプロイ準備

---

## 8. テスト戦略

### 8.1 バックエンドテスト

#### ユニットテスト (pytest)
```python
def test_impact_analysis():
    """影響範囲分析のテスト"""
    result = calculate_impact_range(
        neo4j_driver,
        target_file='UserService.java',
        max_depth=3
    )

    assert len(result['affected_files']) > 0
    assert result['total_risk_score'] > 0
    assert all(f['distance'] <= 3 for f in result['affected_files'])

def test_risk_assessment():
    """リスク評価のテスト"""
    impact_data = {
        'affected_files': [{'path': f'file{i}.java'} for i in range(50)],
        'total_risk_score': 15.0
    }

    risk = assess_risk_level(impact_data)
    assert risk == 'high'
```

### 8.2 フロントエンドテスト

#### コンポーネントテスト (Vitest + React Testing Library)
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { GraphView } from './GraphView';

describe('GraphView', () => {
  it('renders nodes and edges', () => {
    const nodes = [
      { id: '1', label: 'File1' },
      { id: '2', label: 'File2' }
    ];
    const edges = [
      { source: '1', target: '2' }
    ];

    render(<GraphView nodes={nodes} edges={edges} />);

    expect(screen.getAllByClass('node')).toHaveLength(2);
    expect(screen.getAllByClass('link')).toHaveLength(1);
  });

  it('calls onNodeClick when node is clicked', () => {
    const onNodeClick = vi.fn();
    const nodes = [{ id: '1', label: 'File1' }];

    render(<GraphView nodes={nodes} edges={[]} onNodeClick={onNodeClick} />);

    fireEvent.click(screen.getByClass('node'));
    expect(onNodeClick).toHaveBeenCalledWith(nodes[0]);
  });
});
```

#### E2Eテスト (Playwright)
```typescript
import { test, expect } from '@playwright/test';

test('impact analysis flow', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // ファイルを検索
  await page.fill('[data-testid="file-search"]', 'UserService.java');
  await page.click('[data-testid="search-button"]');

  // グラフが表示されることを確認
  await expect(page.locator('.graph-view')).toBeVisible();

  // 影響範囲が表示されることを確認
  await expect(page.locator('.impact-summary')).toContainText('47 files');

  // リスクレベルが表示されることを確認
  await expect(page.locator('.risk-indicator')).toContainText('High');
});
```

---

## 9. パフォーマンス要件

| 指標 | 目標値 | 測定方法 |
|-----|--------|---------|
| API応答時間 (影響範囲分析) | < 2秒 | Lighthouse, APM |
| グラフ初回表示時間 | < 3秒 | Web Vitals (LCP) |
| グラフ操作のフレームレート | 60fps | Chrome DevTools |
| 最大ノード数 (滑らかな操作) | 1,000ノード | パフォーマンステスト |
| メモリ使用量 (フロントエンド) | < 200MB | Chrome Task Manager |

---

## 10. 成功の定義

### 10.1 技術指標
- [ ] 35,000ファイルのグラフを10秒以内に表示
- [ ] 影響範囲分析APIのレスポンス < 2秒
- [ ] グラフ操作が60fpsで滑らか
- [ ] テストカバレッジ > 80%

### 10.2 ユーザー体験指標
- [ ] バグ調査時間: 90%短縮 (1時間 → 6分)
- [ ] リファクタリング計画時間: 80%短縮
- [ ] ユーザビリティスコア: > 8.0/10
- [ ] タスク完了率: > 95%

---

*最終更新: 2025年10月27日*
*バージョン: v1.0.0*
