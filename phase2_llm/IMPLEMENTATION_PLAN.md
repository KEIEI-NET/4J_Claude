# Phase 2: LLM統合 実装計画書

**バージョン**: v2.0
**最終更新**: 2025年10月26日 JST
**参照**: [`../llm_hybrid_analysis_spec.md`](../llm_hybrid_analysis_spec.md)

---

## 📊 Phase 1との差分分析

### ✅ Phase 1で実装済み

**基本LLM統合** (`phase1_cassandra/src/cassandra_analyzer/llm/`)
- ✅ `AnthropicClient`: Claude API通信クライアント
  - API呼び出し機能
  - レート制限対応
  - リトライ処理（指数バックオフ）
  - 基本的なコスト推定（`estimate_cost()`）
- ✅ `LLMAnalyzer`: 基本的なコード分析
  - コードファイル分析
  - 問題検出
  - 推奨事項生成
  - プロンプトテンプレート管理

**スマート検出器** (`phase1_cassandra/src/cassandra_analyzer/detectors/`)
- ✅ `SmartAllowFilteringDetector`: LLMを使った高度なALLOW FILTERING検出
- ✅ `SmartPartitionKeyDetector`: LLMを使ったパーティションキー分析

**成果**:
- テストカバレッジ: 95.34%
- 284テスト全成功
- Claude 3.5 Sonnet統合済み

---

## 🎯 Phase 2で実装する機能

### 1. ハイブリッド分析エンジン（Week 1-2）

#### 1.1 HybridAnalysisEngine

**目的**: 静的解析とLLM分析を統合し、最適な分析結果を生成

**実装場所**: `src/cassandra_analyzer/analyzers/hybrid_analyzer.py`

**主要機能**:
```python
class HybridAnalysisEngine:
    """
    静的解析とLLM分析を統合するエンジン
    """

    async def analyze_code(
        self,
        file_path: str,
        analysis_type: str = "standard"  # quick/standard/comprehensive/critical_only
    ) -> List[AnalysisResult]

    def _should_use_llm(
        self,
        static_result: AnalysisResult,
        analysis_type: str
    ) -> bool

    async def _llm_deep_analysis(
        self,
        file_path: str,
        static_result: AnalysisResult
    ) -> Dict[str, Any]

    def _integrate_results(
        self,
        static_result: AnalysisResult,
        llm_result: Dict[str, Any]
    ) -> AnalysisResult

    async def _llm_semantic_analysis(
        self,
        file_path: str
    ) -> List[AnalysisResult]
```

**信頼度計算ロジック**:
- CERTAIN (100%): 静的解析で確実
- HIGH (90-99%): 静的解析とLLMが一致
- MEDIUM (70-89%): LLM推定のみ
- LOW (50-69%): 推測
- UNCERTAIN (<50%): 人間判断が必要

**完了条件**:
- [ ] 4種類の分析モード実装
- [ ] 信頼度スコアリング実装
- [ ] 結果統合アルゴリズム実装
- [ ] ユニットテスト（カバレッジ > 80%）

---

### 2. Cassandra特化LLM分析（Week 3-4）

#### 2.1 CassandraLLMAnalyzer

**目的**: Cassandra特有の問題を深く分析

**実装場所**: `src/cassandra_analyzer/analyzers/cassandra_llm_analyzer.py`

**主要機能**:
```python
class CassandraLLMAnalyzer:
    """
    LLMを使ったCassandra特化分析
    """

    async def evaluate_data_model(
        self,
        table_name: str,
        keyspace: str
    ) -> Dict[str, Any]

    async def evaluate_consistency_level(
        self,
        query: str,
        consistency_level: str,
        business_context: Dict[str, Any]
    ) -> Dict[str, Any]

    async def analyze_query_performance(
        self,
        query: str,
        table_schema: str
    ) -> Dict[str, Any]
```

**評価観点**:
1. **データモデル評価**
   - Partition Key設計の妥当性
   - Clustering Key設計
   - アクセスパターンとの整合性
   - スケーラビリティ
   - ホットスポットリスク

2. **Consistency Level評価**
   - Replication Factorとの整合性
   - Read + Write > RF の原則
   - レイテンシ要件
   - データ重要度との整合性

3. **クエリパフォーマンス予測**
   - スキャンタイプ（single_partition/multi_partition/full_cluster）
   - 推定ノード数
   - ボトルネック特定
   - 最適化提案

**完了条件**:
- [ ] データモデル評価機能実装
- [ ] Consistency Level分析実装
- [ ] クエリパフォーマンス予測実装
- [ ] Neo4Jとの統合（スキーマ情報取得）
- [ ] ユニットテスト（カバレッジ > 80%）

---

### 3. 自動修正機能（Week 5-6）

#### 3.1 AutoFixer

**目的**: 検出された問題の自動修正コードを生成

**実装場所**: `src/cassandra_analyzer/fixers/auto_fixer.py`

**主要機能**:
```python
class AutoFixer:
    """
    LLMを使った自動修正機能
    """

    async def generate_fix_pr(
        self,
        issue: AnalysisResult,
        file_path: str
    ) -> Dict[str, Any]

    async def _generate_test_code(
        self,
        fixed_code: str,
        issue: AnalysisResult
    ) -> str

    async def _generate_pr_description(
        self,
        issue: AnalysisResult,
        original_code: str,
        fixed_code: str
    ) -> str
```

**修正可能な問題タイプ**:
1. ALLOW FILTERING → Materialized View作成
2. 未使用Partition Key → WHERE句追加
3. 大量Batch → 分割処理
4. Unprepared Statement → PreparedStatement化

**完了条件**:
- [ ] 4種類の問題に対する自動修正実装
- [ ] テストコード生成機能実装
- [ ] PR説明文生成機能実装
- [ ] GitHubとの統合（PR自動作成）
- [ ] ユニットテスト（カバレッジ > 80%）

---

### 4. 影響範囲説明（Week 7）

#### 4.1 ImpactExplainer

**目的**: 変更の影響範囲を自然言語で説明

**実装場所**: `src/cassandra_analyzer/explainers/impact_explainer.py`

**主要機能**:
```python
class ImpactExplainer:
    """
    LLMを使って影響範囲を自然言語で説明
    """

    async def explain_impact(
        self,
        change_description: str,
        affected_items: List[Dict[str, Any]],
        target_audience: str = "developer"  # developer/manager/executive
    ) -> str

    async def generate_executive_report(
        self,
        analysis_results: List[AnalysisResult],
        time_period: str = "今週"
    ) -> str
```

**対象読者**:
- **developer**: 技術的な詳細
- **manager**: ビジネスへの影響
- **executive**: 経営判断に必要な情報

**完了条件**:
- [ ] 3種類の読者向け説明生成実装
- [ ] 経営層向けレポート生成実装
- [ ] Markdown/HTML形式出力対応
- [ ] ユニットテスト（カバレッジ > 80%）

---

### 5. コスト最適化（Week 8）

#### 5.1 CostOptimizer

**目的**: LLM使用コストを管理・最適化

**実装場所**: `src/cassandra_analyzer/cost/cost_optimizer.py`

**主要機能**:
```python
class CostOptimizer:
    """
    LLM使用コストを最適化
    """

    async def analyze_with_budget(
        self,
        file_path: str,
        max_cost_usd: float = 0.10
    ) -> AnalysisResult

    def _estimate_cost(self, file_path: str) -> float

    def get_cost_report(self, time_period: str = "today") -> Dict[str, Any]
```

**コスト管理機能**:
- 結果キャッシュ（ファイルハッシュベース）
- コスト見積もり（事前計算）
- コスト上限管理
- コストレポート生成（日次/週次/月次）

**コスト目標**:
- 1ファイルあたり: < $0.05
- 月間予算: $315
- 35,000ファイル分析: < $1,750

**完了条件**:
- [ ] コスト見積もり機能実装
- [ ] キャッシュ機構実装
- [ ] コスト上限管理実装
- [ ] コストレポート生成実装
- [ ] ユニットテスト（カバレッジ > 80%）

---

### 6. 段階的分析戦略（Week 8）

#### 6.1 TieredAnalysisStrategy

**目的**: ファイルの重要度に応じて分析レベルを調整

**実装場所**: `src/cassandra_analyzer/strategies/tiered_analysis.py`

**主要機能**:
```python
class TieredAnalysisStrategy:
    """
    ファイルの重要度に応じてLLM使用を調整
    """

    def determine_analysis_tier(self, file_path: str) -> str
```

**分析レベル**:
- **Tier 1 (静的解析のみ)**: テストコード、設定ファイル
- **Tier 2 (条件付きLLM)**: 一般的なビジネスロジック
- **Tier 3 (フルLLM)**: 重要なデータアクセス層、決済処理等

**完了条件**:
- [ ] Tier判定ロジック実装
- [ ] ファイルパターンマッチング実装
- [ ] 設定ファイルでのカスタマイズ対応
- [ ] ユニットテスト（カバレッジ > 80%）

---

## 📋 実装ロードマップ

### Week 1-2: LLM統合基盤
- [ ] Task 10.1: HybridAnalysisEngine実装
- [ ] Task 10.2: 信頼度スコアリング実装
- [ ] Task 10.3: 結果統合アルゴリズム実装
- [ ] Task 10.4: ユニットテスト作成

### Week 3-4: Cassandra特化機能
- [ ] Task 11.1: CassandraLLMAnalyzer実装
- [ ] Task 11.2: データモデル評価機能
- [ ] Task 11.3: Consistency Level分析
- [ ] Task 11.4: クエリパフォーマンス予測
- [ ] Task 11.5: ユニットテスト作成

### Week 5-6: 自動修正機能
- [ ] Task 12.1: AutoFixer実装
- [ ] Task 12.2: 4種類の問題修正機能
- [ ] Task 12.3: テストコード生成機能
- [ ] Task 12.4: GitHub PR統合
- [ ] Task 12.5: ユニットテスト作成

### Week 7: 影響範囲説明
- [ ] Task 13.1: ImpactExplainer実装
- [ ] Task 13.2: 3種類の読者向け説明生成
- [ ] Task 13.3: 経営層向けレポート生成
- [ ] Task 13.4: ユニットテスト作成

### Week 8: コスト最適化
- [ ] Task 14.1: CostOptimizer実装
- [ ] Task 14.2: TieredAnalysisStrategy実装
- [ ] Task 14.3: キャッシュ機構実装
- [ ] Task 14.4: コストレポート生成
- [ ] Task 14.5: ユニットテスト作成

---

## 📊 成功指標

| 指標 | 目標 | 測定方法 |
|-----|------|---------|
| 検出精度 (Precision) | > 90% | 手動レビューとの比較 |
| 検出率 (Recall) | > 85% | 既知のバグ検出率 |
| 誤検出率 | < 10% | False Positive率 |
| LLM同意率 | > 80% | 静的解析とLLMの一致率 |
| 修正提案の採用率 | > 60% | 開発者が採用した割合 |
| コスト効率 | < $0.05/file | 1ファイルあたりの平均コスト |
| テストカバレッジ | > 80% | pytest --cov |
| API応答時間 | < 5秒/file | 平均分析時間 |

---

## 🧪 テスト戦略

### ユニットテスト
- 各クラスの主要メソッドをテスト
- モックを使ってLLM APIをシミュレーション
- エッジケースのカバー
- カバレッジ目標: > 80%

### 統合テスト
- Phase 1の静的解析との統合確認
- Neo4J連携の動作確認
- エンドツーエンドの分析フロー確認

### パフォーマンステスト
- 35,000ファイル分析の実行時間測定
- メモリ使用量の監視
- API呼び出し数の最適化確認

### コスト検証
- 実際のAPI使用コストの測定
- 予算内での運用可能性の確認
- キャッシュ効果の測定

---

## 💰 予算管理

### 月間予算: $315

**内訳**:
- Claude Sonnet 4.5 API: $300/月
- バッファ: $15/月

**コスト計算**:
- Input: $3 / 1M tokens
- Output: $15 / 1M tokens
- 平均ファイルサイズ: 500行 ≒ 1,500 tokens
- コンテキスト収集: 3,000 tokens (2倍)
- 出力: 1,000 tokens

**1ファイルあたり**:
- Input: 4,500 tokens = $0.0135
- Output: 1,000 tokens = $0.015
- **合計**: $0.0285/file

**月間分析可能ファイル数**:
- $300 ÷ $0.0285 ≒ **10,526ファイル/月**

**キャッシュ効果**:
- キャッシュヒット率80%を想定
- 実質コスト: $0.0285 × 0.2 = **$0.0057/file**
- 月間分析可能: **52,632ファイル/月**

---

## 🔄 Phase 1との統合

### 既存コンポーネントの活用

**パーサー** (`phase1_cassandra/src/cassandra_analyzer/parsers/`)
- ✅ JavaCassandraParser
- ✅ ASTJavaParser
- ✅ CQLParser

**検出器** (`phase1_cassandra/src/cassandra_analyzer/detectors/`)
- ✅ AllowFilteringDetector（静的）
- ✅ PartitionKeyDetector（静的）
- ✅ BatchSizeDetector（静的）
- ✅ PreparedStatementDetector（静的）
- ✅ SmartAllowFilteringDetector（LLM統合）
- ✅ SmartPartitionKeyDetector（LLM統合）

**モデル** (`phase1_cassandra/src/cassandra_analyzer/models/`)
- ✅ CassandraCall
- ✅ Issue
- ✅ AnalysisResult

**LLM基盤** (`phase1_cassandra/src/cassandra_analyzer/llm/`)
- ✅ AnthropicClient
- ✅ LLMAnalyzer

### 拡張ポイント

**新規データモデル**:
```python
@dataclass
class AnalysisConfidence(Enum):
    CERTAIN = "certain"      # 100% 確実
    HIGH = "high"            # 90-99%
    MEDIUM = "medium"        # 70-89%
    LOW = "low"              # 50-69%
    UNCERTAIN = "uncertain"  # <50%

@dataclass
class HybridAnalysisResult(AnalysisResult):
    """ハイブリッド分析結果"""
    static_analysis: Optional[Dict[str, Any]]
    llm_analysis: Optional[Dict[str, Any]]
    confidence: AnalysisConfidence
    fix_suggestions: List[str]
    impact_scope: Dict[str, Any]
```

---

## 📚 関連ドキュメント

- **詳細仕様**: [`../llm_hybrid_analysis_spec.md`](../llm_hybrid_analysis_spec.md)
- **Phase 1成果**: [`../phase1_cassandra/README_CASSANDRA.md`](../phase1_cassandra/README_CASSANDRA.md)
- **全体計画**: [`../TODO.md`](../TODO.md)
- **プロジェクト概要**: [`../README.md`](../README.md)

---

**次のアクション**: Week 1のTask 10.1（HybridAnalysisEngine実装）から開始
