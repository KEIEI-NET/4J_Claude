# 4J_Claude プロジェクトドキュメント索引

*バージョン: v3.0.0*
*最終更新: 2025年01月27日 18:30 JST*

このドキュメントは、4J_Claudeプロジェクトの全てのドキュメントへのナビゲーションガイドです。

## 📚 プロジェクト全体ドキュメント

### 概要・仕様書
- **[README.md](./README.md)** - プロジェクト全体の概要とロードマップ
- **[CHANGELOG.md](./CHANGELOG.md)** - 変更履歴とリリースノート
- **[TODO.md](./TODO.md)** - 詳細タスクリスト（2,253行）

### アーキテクチャ・設計書
- **[integrated_architecture.md](./integrated_architecture.md)** - 統合アーキテクチャ設計
- **[DETAILED_DESIGN.md](./DETAILED_DESIGN.md)** - 詳細設計書
- **[IMPLEMENTATION_SPEC.md](./IMPLEMENTATION_SPEC.md)** - 実装仕様書
- **[CLAUDE.md](./CLAUDE.md)** - Claude AI統合仕様

### Phase別仕様書
- **[cassandra_analysis_spec.md](./cassandra_analysis_spec.md)** - Cassandra分析仕様
- **[llm_hybrid_analysis_spec.md](./llm_hybrid_analysis_spec.md)** - LLMハイブリッド分析仕様
- **[source_code_graph_analysis_spec.md](./source_code_graph_analysis_spec.md)** - グラフ分析仕様
- **[database_analysis_extension_spec.md](./database_analysis_extension_spec.md)** - DB拡張仕様

## 📁 Phase 1: Cassandra特化型分析（完了）

**ディレクトリ**: `phase1_cassandra/`

### 主要ドキュメント
- **[README_CASSANDRA.md](./phase1_cassandra/README_CASSANDRA.md)** - Phase 1詳細説明
- **[USAGE.md](./phase1_cassandra/USAGE.md)** - 使用方法ガイド
- **[DEVELOPMENT.md](./phase1_cassandra/DEVELOPMENT.md)** - 開発者ガイド

### 成果物
- ✅ Javaファイル静的解析
- ✅ CQL抽出と問題検出
- ✅ 4つの検出器実装
- ✅ HTML/JSON/Markdownレポート生成
- ✅ CLIツール実装
- ✅ テストカバレッジ95.34%

## 📁 Phase 2: LLM統合（完了）

**ディレクトリ**: `phase2_llm/`

### 主要ドキュメント
- **[README_LLM.md](./phase2_llm/README_LLM.md)** - Phase 2詳細説明とAPI仕様
- **[ARCHITECTURE.md](./phase2_llm/ARCHITECTURE.md)** - システムアーキテクチャ図（10種類のマーメイド図）
- **[IMPLEMENTATION_PLAN.md](./phase2_llm/IMPLEMENTATION_PLAN.md)** - 実装計画
- **[LLM_INTEGRATION_TEST.md](./phase2_llm/LLM_INTEGRATION_TEST.md)** - 統合テスト結果

### 成果物
- ✅ HybridAnalysisEngine実装
- ✅ 4つの分析モード（quick/standard/comprehensive/critical_only）
- ✅ Anthropic Claude API統合
- ✅ 信頼度計算システム
- ✅ コスト管理（$0.05-0.10/実行）
- ✅ テストカバレッジ90%

### 主要コンポーネント
1. **models.py** - データモデル定義
2. **llm_client.py** - AnthropicClient実装
3. **llm_analyzer.py** - LLM分析エンジン
4. **hybrid_engine.py** - ハイブリッド分析統合

## 📁 Phase 3: Neo4j統合（完了）

**ディレクトリ**: `phase3_neo4j/`

### 主要ドキュメント
- **[README.md](./phase3_neo4j/README.md)** - Phase 3詳細説明（Mermaid図付き）
- **[README_CELERY.md](./phase3_neo4j/README_CELERY.md)** - Celery並列処理詳細
- **[README_INTEGRATION_TESTS.md](./phase3_neo4j/README_INTEGRATION_TESTS.md)** - 統合テスト詳細
- **[TASK_12.2_COMPLETION_REPORT.md](./phase3_neo4j/TASK_12.2_COMPLETION_REPORT.md)** - Neo4jClient実装報告
- **[TASK_12.3_COMPLETION_REPORT.md](./phase3_neo4j/TASK_12.3_COMPLETION_REPORT.md)** - ImpactAnalyzer実装報告

### 成果物
- ✅ Neo4jグラフデータベース構築（100%完了）
- ✅ GraphBuilder実装（100%カバレッジ）
- ✅ Neo4jClient実装（98%カバレッジ）
- ✅ Celery並列処理タスク（97%カバレッジ）
- ✅ ImpactAnalyzer影響範囲分析（90%カバレッジ）
- ✅ 統合テスト43件全通過
- ✅ テストカバレッジ83%達成

### 主要コンポーネント
1. **neo4j_client.py** - Neo4j接続・操作
2. **graph_builder.py** - グラフ構造変換
3. **impact_analyzer.py** - 影響範囲分析
4. **tasks.py** - Celery並列処理タスク
5. **celery_app.py** - Celery設定管理

## 📁 Phase 4: マルチDB対応（計画中）

**ディレクトリ**: `phase4_multidb/`

### 対応予定データベース
1. MySQL - N+1問題、フルテーブルスキャン検出
2. Redis - キャッシュ整合性、TTL検証
3. Elasticsearch - クエリDSL解析、インデックス評価
4. SQL Server - T-SQL解析、ストアドプロシージャ分析

## 🔍 ドキュメント検索ガイド

### 目的別ドキュメント検索

| 目的 | 参照ドキュメント |
|------|------------------|
| プロジェクト全体を理解したい | [README.md](./README.md) |
| Phase 1の使い方を知りたい | [USAGE.md](./phase1_cassandra/USAGE.md) |
| Phase 2のアーキテクチャを理解したい | [ARCHITECTURE.md](./phase2_llm/ARCHITECTURE.md) |
| LLM統合の詳細を知りたい | [Phase 2 README.md](./phase2_llm/README_LLM.md) |
| Phase 3のグラフDB統合を知りたい | [Phase 3 README.md](./phase3_neo4j/README.md) |
| Celery並列処理の詳細を知りたい | [README_CELERY.md](./phase3_neo4j/README_CELERY.md) |
| 変更履歴を確認したい | [CHANGELOG.md](./CHANGELOG.md) |
| タスクの詳細を見たい | [TODO.md](./TODO.md) |
| 開発に参加したい | [DEVELOPMENT.md](./phase1_cassandra/DEVELOPMENT.md) |

### トピック別索引

#### 🏗️ アーキテクチャ
- [統合アーキテクチャ](./integrated_architecture.md)
- [Phase 2アーキテクチャ図](./phase2_llm/ARCHITECTURE.md)
- [詳細設計書](./DETAILED_DESIGN.md)

#### 🧪 テスト
- [Phase 1テスト結果](./phase1_cassandra/README_CASSANDRA.md#テスト)
- [Phase 2テスト結果](./phase2_llm/README_LLM.md#テスト結果)
- [LLM統合テスト](./phase2_llm/LLM_INTEGRATION_TEST.md)
- [Phase 3統合テスト](./phase3_neo4j/README_INTEGRATION_TESTS.md)

#### 🚀 使用方法
- [CLIツール使用法](./phase1_cassandra/USAGE.md)
- [HybridAnalysisEngine使用法](./phase2_llm/README_LLM.md#使用方法)

#### 📊 仕様
- [Cassandra分析仕様](./cassandra_analysis_spec.md)
- [LLMハイブリッド分析仕様](./llm_hybrid_analysis_spec.md)
- [グラフ分析仕様](./source_code_graph_analysis_spec.md)

## 📈 プロジェクト進捗サマリー

```
全体進捗: [███████████████░░░░░] 75%

✅ Phase 1: Cassandra分析    100% 完了 (カバレッジ 95.34%)
✅ Phase 2: LLM統合          100% 完了 (カバレッジ 90%)
✅ Phase 3: Neo4j統合        100% 完了 (カバレッジ 83%)
🔵 Phase 4: マルチDB対応       0% 計画中
```

## 🔄 更新方針

このインデックスは以下のタイミングで更新されます：
- 新しいPhaseの完了時
- 重要なドキュメントの追加時
- プロジェクト構造の大幅な変更時

## 📝 ドキュメント作成ガイドライン

新しいドキュメント作成時は以下を含めてください：

1. **ヘッダー情報**
   ```markdown
   *バージョン: vX.Y.Z*
   *最終更新: YYYY年MM月DD日 HH:mm JST*
   ```

2. **フッター情報**
   ```markdown
   ---
   *最終更新: YYYY年MM月DD日 HH:mm JST*
   *バージョン: vX.Y.Z*

   **更新履歴:**
   - vX.Y.Z (YYYY年MM月DD日): 更新内容
   ```

3. **AI再現性のための詳細**
   - 具体的なコマンド例
   - ファイルパスは絶対パスで記載
   - 環境変数と依存関係の明記
   - エラーハンドリングの説明

---

*最終更新: 2025年01月27日 18:30 JST*
*バージョン: v3.0.0*

**更新履歴:**
- v3.0.0 (2025年01月27日): Phase 3完了状態を反映、Neo4j統合ドキュメント追加、進捗75%に更新
- v2.0.0 (2025年01月27日): プロジェクト構造変更に伴う全パス修正（cassandra-analyzer削除、各フェーズをルート直下に配置）
- v1.0.0 (2025年01月27日): ドキュメント索引初版作成、Phase 1&2完了状態を反映