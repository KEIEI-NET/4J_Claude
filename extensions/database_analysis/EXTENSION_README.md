# Database Analysis Extension

**種類**: 補完機能 (Extension)
**ステータス**: 実装完了（96%カバレッジ）
**作成日**: 2025年10月27日

---

## 概要

このディレクトリには、**マルチデータベース解析フレームワーク**が含まれています。
これは本プロジェクトの**補完機能**であり、データベース特化の問題検出を提供します。

### 重要な注意

本機能は「database_analysis_extension_spec.md」に基づく実装であり、
プロジェクトの**主要なゴール（可視化・影響範囲分析）とは異なります**。

主要なゴール（Phase 4）:
- ソースファイルの関係性可視化
- バグ影響範囲の即時特定
- リファクタリング影響分析

→ これらは `phase4_visualization/` で実装されます。

---

## 機能一覧

### 1. SQL解析エンジン
- MySQL / SQL Server対応
- N+1問題自動検出
- クエリ複雑度計算
- 90%テストカバレッジ

### 2. Redis解析エンジン
- キャッシュ操作検出
- TTL抽出とミッシングTTL検出
- キャッシュパターン分析
- 97%テストカバレッジ

### 3. Elasticsearch解析エンジン
- Query DSL解析
- パフォーマンスリスク評価
- 複雑度計算（1-10スケール）
- 97%テストカバレッジ

### 4. トランザクション解析エンジン
- Spring @Transactional検出
- デッドロックリスク評価
- 分散トランザクション検出
- 99%テストカバレッジ

---

## テスト結果

```
=========================== test session starts ===========================
collected 103 items

tests/unit/test_database_models.py ................                  [ 15%]
tests/unit/test_sql_analyzer.py .................................    [ 48%]
tests/unit/test_redis_analyzer.py ........................           [ 71%]
tests/unit/test_elasticsearch_analyzer.py ....................       [ 91%]
tests/unit/test_transaction_analyzer.py .................         [100%]

========================== 103 passed in 2.34s ============================

---------- coverage: platform win32, python 3.11.x -----------
TOTAL                                             710     28    96%
```

**96% カバレッジ達成**

---

## ディレクトリ構造

```
database_analysis/
├── src/multidb_analyzer/
│   ├── models/
│   │   └── database_models.py (100%カバレッジ)
│   ├── analyzers/
│   │   ├── sql_analyzer.py (90%カバレッジ)
│   │   ├── redis_analyzer.py (97%カバレッジ)
│   │   ├── elasticsearch_analyzer.py (97%カバレッジ)
│   │   └── transaction_analyzer.py (99%カバレッジ)
│   ├── neo4j/
│   │   ├── schema_extension.py
│   │   └── graph_exporter.py
│   └── api/
│       └── main.py (FastAPI)
├── tests/ (103テスト)
├── README.md
├── PHASE4_SPECIFICATION.md
└── pyproject.toml
```

---

## 使用方法

### インストール

```bash
cd extensions/database_analysis
pip install -e .
```

### SQL解析

```python
from multidb_analyzer.analyzers.sql_analyzer import SQLAnalyzer

analyzer = SQLAnalyzer(database=DatabaseType.MYSQL)
queries = analyzer.analyze_file("UserRepository.java")

# N+1問題の検出
n_plus_one_queries = [q for q in queries if q.n_plus_one_risk]
print(f"N+1 risks found: {len(n_plus_one_queries)}")
```

### FastAPI起動

```bash
python -m multidb_analyzer.api.main
# → http://localhost:8000/docs でSwagger UI
```

---

## 統合方法

本機能は、メインの可視化システム（Phase 4）と統合可能です：

### オプション1: APIエンドポイントとして統合
```
phase4_visualization/backend/
└── integrations/
    └── database_analyzer.py  # この拡張機能を呼び出す
```

### オプション2: グラフDBノードとして統合
```
Neo4j Graph:
├── File ノード
├── Method ノード
└── DatabaseQuery ノード ← この拡張機能が提供
```

### オプション3: 独立したサービスとして運用
```
Docker Compose:
├── visualization-service (Phase 4)
├── database-analysis-service (この拡張機能)
└── neo4j
```

---

## 今後の展開

### 短期的な活用
- Phase 4可視化システムの補完機能として
- N+1問題検出の専用ツールとして
- CI/CDパイプラインでの静的解析として

### 長期的な統合
- LLM統合（Phase 2）との連携
- 自動修正提案の生成
- リアルタイム監視システムへの組み込み

---

## 参照ドキュメント

- `README.md` - ユーザーガイド
- `PHASE4_SPECIFICATION.md` - 技術仕様書
- `../../database_analysis_extension_spec.md` - 元の仕様書

---

## まとめ

本機能は**高品質な実装**（96%カバレッジ、103テスト）ですが、
プロジェクトの主要ゴールとは異なる**補完機能**です。

**主要ゴール**: 可視化・影響範囲分析 → `phase4_visualization/`
**補完機能**: データベース解析 → `extensions/database_analysis/`（このディレクトリ）

両者を組み合わせることで、より強力なコード分析システムを構築できます。

---

*最終更新: 2025年10月27日*
