# 4J_Claude: 汎用ソースコード解析システム

*バージョン: v3.0.0*
*最終更新: 2025年01月27日 18:30 JST*

<p align="center">
  <img src="https://img.shields.io/badge/Status-Phase%201%20Completed-success" alt="Phase 1 Completed"/>
  <img src="https://img.shields.io/badge/Phase%202-Completed-success" alt="Phase 2 Completed"/>
  <img src="https://img.shields.io/badge/Phase%203-Completed-success" alt="Phase 3 Completed"/>
  <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License"/>
  <img src="https://img.shields.io/badge/Python-3.11+-blue" alt="Python 3.11+"/>
  <img src="https://img.shields.io/badge/Coverage-83%25-brightgreen" alt="Test Coverage 83%"/>
</p>

## 📋 プロジェクト概要

**4J_Claude** は、ソースコードファイル群を解析し、**Neo4Jグラフデータベース**で視覚化し、バグ内容から関連ソースファイルを自動検出するための汎用ソースコード解析システムです。

### 核心機能

1. **静的コード解析** - データベース関連のアンチパターンと問題を検出
2. **LLM統合** - Claude APIを使用した高度な意味論的分析
3. **Neo4Jグラフ可視化** - コード構造と依存関係の視覚的表現（Phase 3）
4. **影響範囲分析** - 変更の影響をトレースして可視化（Phase 3）
5. **マルチDB対応** - Cassandra, MySQL, Redis, Elasticsearch, SQL Server（Phase 4）

---

## 🎯 プロジェクト構成（4フェーズ）

### ✅ Phase 1: Cassandra特化型コード分析システム（完了）
Javaコード内のCassandraクエリを静的解析し、パフォーマンス問題を早期検出するシステム。284のテストで95.34%のカバレッジを達成。

**詳細ドキュメント**: 📖 [`phase1_cassandra/README_CASSANDRA.md`](./phase1_cassandra/README_CASSANDRA.md)

### ✅ Phase 2: LLM統合（完了）
Anthropic Claude APIを統合し、静的解析では検出困難な問題を発見。4つの分析モード（quick, standard, comprehensive, critical_only）を提供。

**詳細ドキュメント**: 📖 [`phase2_llm/README.md`](./phase2_llm/README.md)

### ✅ Phase 3: Neo4Jグラフデータベース統合（完了）
コード構造をグラフDBで可視化し、影響範囲分析を実現。GraphBuilder、Neo4jClient、Celery並列処理タスクを実装し、統合テスト43件全通過。

**詳細ドキュメント**: 📖 [`phase3_neo4j/README.md`](./phase3_neo4j/README.md)
**主要成果**:
- GraphBuilderによる分析結果のグラフ変換（100%カバレッジ）
- Neo4jClientによるデータベース操作（98%カバレッジ）
- Celery並列処理タスク実装（97%カバレッジ）
- 統合テスト43件全通過
- テストカバレッジ: 66% → 83% (+17%向上)

### 🔵 Phase 4: マルチデータベース展開（計画中）
MySQL、Redis、Elasticsearch、SQL Serverへの対応を追加し、クロスDB整合性チェック機能を実装予定。

**計画ドキュメント**: 📖 [`phase4_multidb/README.md`](./phase4_multidb/README.md)

---

## 🚀 クイックスタート

```bash
# リポジトリのクローン
git clone https://github.com/your-org/4j-claude.git
cd 4j-claude

# Phase 1 & 2の基本使用
cd phase1_cassandra/
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e .

# Cassandra分析実行（静的解析のみ）
cassandra-analyzer analyze /path/to/java/project --output report.html

# LLM統合分析（Phase 2機能）
cassandra-analyzer analyze /path/to/java/project \
    --enable-llm \
    --api-key $ANTHROPIC_API_KEY \
    --mode comprehensive
```

**詳細な使用方法**:
- Phase 1機能: [`phase1_cassandra/README_CASSANDRA.md`](./phase1_cassandra/README_CASSANDRA.md)
- Phase 2機能: [`phase2_llm/README.md`](./phase2_llm/README.md)

---

## 📊 プロジェクト進捗

```
全体進捗: [███████████████░░░░░] 75% (Phase 1-3完了)

Phase 1: [████████████████████] 100% ✅ 静的解析
Phase 2: [████████████████████] 100% ✅ LLM統合
Phase 3: [████████████████████] 100% ✅ Neo4j/Celery
Phase 4: [░░░░░░░░░░░░░░░░░░░░]   0% 🔵 計画中
```

---

## 🏗️ プロジェクト構造

```
4j-claude/
├── phase1_cassandra/         ✅ Cassandra特化型分析（完了）
├── phase2_llm/               ✅ LLM統合（完了）
├── phase3_neo4j/             ✅ グラフDB統合（完了）
│   ├── src/graph_analyzer/
│   │   ├── graph/           # Neo4j接続とグラフ構築
│   │   ├── impact/          # 影響範囲分析
│   │   └── tasks/           # Celery並列処理
│   └── tests/               # 43統合テスト
├── phase4_multidb/           🔵 マルチDB対応（計画中）
├── README.md                 # プロジェクト概要（このファイル）
└── TODO.md                   # タスク管理
```

**詳細な構造は各フェーズのREADMEを参照**:
- [`phase1_cassandra/README_CASSANDRA.md`](./phase1_cassandra/README_CASSANDRA.md#ディレクトリ構造)
- [`phase2_llm/README.md`](./phase2_llm/README.md#ディレクトリ構造)
- [`phase3_neo4j/README.md`](./phase3_neo4j/README.md#ディレクトリ構造予定)
- [`phase4_multidb/README.md`](./phase4_multidb/README.md#ディレクトリ構造予定)

---

## 📈 成功指標

| Phase | ステータス | 主要指標 |
|-------|-----------|----------|
| **Phase 1** | ✅ 完了 | テストカバレッジ 95.34%、284テスト成功 |
| **Phase 2** | ✅ 完了 | LLM精度 92-97%、コスト $0.05-0.10/実行 |
| **Phase 3** | ✅ 完了 | カバレッジ 83%、統合テスト43件、GraphBuilder 100%、Neo4jClient 98%、Celeryタスク 97% |
| **Phase 4** | 🔵 計画中 | 5種DB対応、検出率 >80%（目標） |

---

## 📚 ドキュメント構造

### プロジェクト全体
- **このREADME** - プロジェクト概要とナビゲーション
- [`TODO.md`](./TODO.md) - 全フェーズの詳細タスク管理
- [`DETAILED_DESIGN.md`](./DETAILED_DESIGN.md) - 技術アーキテクチャ詳細
- [`IMPLEMENTATION_SPEC.md`](./IMPLEMENTATION_SPEC.md) - 実装仕様

### 各フェーズ詳細
- **Phase 1**: [`phase1_cassandra/README_CASSANDRA.md`](./phase1_cassandra/README_CASSANDRA.md)
  - Cassandra分析の詳細仕様、使用方法、テスト結果
- **Phase 2**: [`phase2_llm/README.md`](./phase2_llm/README.md)
  - LLM統合の実装詳細、4つの分析モード、コスト管理
- **Phase 3**: [`phase3_neo4j/README.md`](./phase3_neo4j/README.md)
  - Neo4J統合計画、スキーマ設計、並列処理アーキテクチャ
- **Phase 4**: [`phase4_multidb/README.md`](./phase4_multidb/README.md)
  - マルチDB対応計画、各DB固有の検出パターン

---

## 🎯 次のステップ

**Phase 4開始予定**: 2025年2月1日 JST

1. MySQL/PostgreSQL検出パターン実装
2. Redis/Elasticsearch対応追加
3. クロスDB整合性チェック機能
4. 統合ダッシュボード拡張

詳細は[`phase4_multidb/README.md`](./phase4_multidb/README.md)を参照

---

## 🤝 開発ガイド

### 環境セットアップ
```bash
# 基本セットアップ
git clone https://github.com/your-org/4j-claude.git
cd 4j-claude
```

### 各フェーズでの作業
- **Phase 1/2の改善**: 該当ディレクトリ内で作業
- **Phase 3/4の開発**: 計画ドキュメントを参照して開始

### テスト実行
各フェーズのディレクトリで `pytest tests/ -v --cov` を実行

---

## 📄 ライセンス

MIT License

---

## 📧 お問い合わせ

プロジェクトに関する質問や提案は、GitHubのIssuesでお願いします。

---

*最終更新: 2025年01月27日 18:30 JST*
*バージョン: v3.0.0*

**更新履歴:**
- v3.0.0 (2025年01月27日): Phase 3 Neo4j統合完了、テストカバレッジ83%達成
- v2.0.0 (2025年01月27日): ドキュメント構造の整理と重複削除
