# Phase 2 実装計画

## 概要

Phase 1の成功（91.30%カバレッジ、92件テスト成功）を基盤として、LLM統合とスマート分析機能を追加します。

## Phase 2 の目標

### 主要目標

1. **LLM統合**: Claude APIを活用したスマート分析
2. **ASTベースパーサー**: より正確なコード解析
3. **誤検出率の測定**: 実データでの評価と改善
4. **高度な検出ロジック**: コンテキストを理解した検出

### 定量目標

| 項目 | Phase 1 | Phase 2 目標 |
|------|---------|-------------|
| 誤検出率 | 未測定 | < 10% |
| 検出精度 | 基本パターン | コンテキスト理解 |
| 対応ファイル数 | 制限なし | 100+ファイル |
| 実行時間 | 0.67秒 | < 60秒（LLM含む） |
| テストカバレッジ | 91.30% | > 90% 維持 |

## 実装タスク

### Day 6: LLM統合の基盤構築

#### 6.1 LLMクライアントの実装
- [ ] `src/cassandra_analyzer/llm/` パッケージ作成
- [ ] `anthropic_client.py` - Claude API統合
- [ ] `llm_analyzer.py` - LLMベース分析エンジン
- [ ] 環境変数管理（API Key）
- [ ] レート制限・リトライ処理

#### 6.2 プロンプト設計
- [ ] `prompts/` ディレクトリ作成
- [ ] コード分析用プロンプトテンプレート
- [ ] 問題検出用プロンプト
- [ ] 推奨事項生成プロンプト

#### 6.3 テスト
- [ ] LLMクライアントのユニットテスト（モック使用）
- [ ] プロンプト品質テスト

**期待される成果物**:
- LLM統合基盤
- 10件以上のテストケース

### Day 7: ASTベースパーサーの実装

#### 7.1 Javaパーサーライブラリの選定
- [ ] `javalang` または `tree-sitter` の評価
- [ ] 依存関係の追加（requirements.txt）

#### 7.2 ASTパーサーの実装
- [ ] `src/cassandra_analyzer/parsers/ast_parser.py`
- [ ] クラス・メソッド構造の解析
- [ ] 変数スコープの追跡
- [ ] データフロー分析（基本）

#### 7.3 既存パーサーとの統合
- [ ] パーサー切り替え機能（設定による選択）
- [ ] 後方互換性の維持

#### 7.4 テスト
- [ ] ASTパーサーのユニットテスト
- [ ] 既存の正規表現パーサーとの比較テスト
- [ ] パフォーマンステスト

**期待される成果物**:
- ASTベースパーサー
- 15件以上のテストケース

### Day 8: スマート検出器の実装

#### 8.1 LLM強化検出器
- [ ] `SmartAllowFilteringDetector` - コンテキスト理解
- [ ] `SmartPartitionKeyDetector` - データモデル理解
- [ ] LLMを使用した根拠の生成

#### 8.2 コンテキスト分析
- [ ] テーブルスキーマの推論
- [ ] クエリパターンの学習
- [ ] ベストプラクティスとの比較

#### 8.3 信頼度スコアリング
- [ ] 複数の証拠に基づくスコア計算
- [ ] LLMの信頼度との統合

#### 8.4 テスト
- [ ] スマート検出器のユニットテスト
- [ ] 精度評価テスト
- [ ] Phase 1検出器との比較

**期待される成果物**:
- 2つ以上のスマート検出器
- 20件以上のテストケース

### Day 9: 誤検出率の測定と改善

#### 9.1 評価データセットの作成
- [ ] 実際のCassandra DAOファイルの収集
- [ ] 正解データのアノテーション
- [ ] テストセットの分割（Train/Test）

#### 9.2 評価メトリクスの実装
- [ ] Precision（適合率）
- [ ] Recall（再現率）
- [ ] F1 Score
- [ ] False Positive Rate

#### 9.3 評価スクリプト
- [ ] `scripts/evaluate.py` - 自動評価
- [ ] レポート生成（混同行列、ROC曲線）

#### 9.4 改善サイクル
- [ ] 誤検出パターンの分析
- [ ] 検出ロジックの調整
- [ ] 再評価

**期待される成果物**:
- 評価データセット（20+ファイル）
- 評価レポート
- 誤検出率 < 10%

### Day 10: CLI・設定強化

#### 10.1 CLIツールの実装
- [ ] `src/cassandra_analyzer/cli.py`
- [ ] `cassandra-analyzer` コマンド
- [ ] サブコマンド（analyze, evaluate, config）
- [ ] 進捗表示（プログレスバー）

#### 10.2 設定ファイル対応
- [ ] YAML設定ファイルのサポート
- [ ] 設定バリデーション
- [ ] デフォルト設定の生成

#### 10.3 ドキュメント更新
- [ ] CLI使用方法の追加
- [ ] Phase 2機能のドキュメント化
- [ ] サンプル設定ファイル

#### 10.4 テスト
- [ ] CLIのE2Eテスト
- [ ] 設定ファイルのテスト

**期待される成果物**:
- CLIツール
- 更新されたドキュメント

## 技術スタック（追加）

### 新規依存パッケージ

```txt
# LLM統合
anthropic>=0.18.0

# ASTパーサー
javalang>=0.13.0
# または
tree-sitter>=0.20.0
tree-sitter-java>=0.20.0

# CLI
click>=8.1.0
rich>=13.0.0  # プログレスバー・整形出力

# 設定管理
pyyaml>=6.0.0
pydantic>=2.0.0  # 設定バリデーション

# 評価
scikit-learn>=1.3.0  # メトリクス計算
matplotlib>=3.7.0  # グラフ生成
```

## アーキテクチャ拡張

### 新規コンポーネント

```
src/cassandra_analyzer/
├── llm/                        # LLM統合 (NEW)
│   ├── __init__.py
│   ├── anthropic_client.py     # Claude APIクライアント
│   ├── llm_analyzer.py         # LLM分析エンジン
│   └── prompts/                # プロンプトテンプレート
│       ├── code_analysis.txt
│       ├── issue_detection.txt
│       └── recommendation.txt
├── parsers/
│   ├── ast_parser.py           # ASTパーサー (NEW)
│   └── parser_factory.py       # パーサー選択 (NEW)
├── detectors/
│   ├── smart/                  # スマート検出器 (NEW)
│   │   ├── __init__.py
│   │   ├── smart_allow_filtering.py
│   │   └── smart_partition_key.py
│   └── detector_factory.py     # 検出器選択 (NEW)
├── evaluation/                 # 評価フレームワーク (NEW)
│   ├── __init__.py
│   ├── metrics.py              # 評価メトリクス
│   ├── dataset.py              # データセット管理
│   └── evaluator.py            # 評価実行
└── cli.py                      # CLIエントリポイント (NEW)

scripts/                        # 評価・ユーティリティ (NEW)
├── evaluate.py                 # 評価スクリプト
├── generate_config.py          # 設定生成
└── benchmark.py                # ベンチマーク

config/                         # 設定例 (NEW)
├── default.yaml
├── llm_enabled.yaml
└── ast_parser.yaml

datasets/                       # 評価データ (NEW)
└── evaluation/
    ├── train/
    └── test/
```

## 設計方針

### 1. 後方互換性

Phase 1のAPIを維持し、既存ユーザーに影響を与えない：

```python
# Phase 1 API（引き続き動作）
analyzer = CassandraAnalyzer()
result = analyzer.analyze_file("dao.java")

# Phase 2 API（オプション機能）
analyzer = CassandraAnalyzer(config={
    "parser": "ast",           # AST parser使用
    "llm_enabled": True,       # LLM分析有効化
    "smart_detectors": True,   # スマート検出器使用
})
result = analyzer.analyze_file("dao.java")
```

### 2. 段階的な機能追加

各機能は独立して有効/無効にできる：

```yaml
# config.yaml
parser:
  type: "ast"  # or "regex"

llm:
  enabled: true
  provider: "anthropic"
  model: "claude-3-5-sonnet-20241022"
  api_key_env: "ANTHROPIC_API_KEY"

detectors:
  basic:
    - allow_filtering
    - partition_key
  smart:
    - smart_allow_filtering  # LLM強化版
```

### 3. テストカバレッジの維持

- 新規コード: > 90%
- 全体: > 90% 維持
- E2Eテスト: 重要なユースケースをカバー

## リスクと対策

### リスク1: LLM APIコスト

**対策**:
- キャッシング機能の実装
- バッチ処理の最適化
- ローカルモードのサポート（LLMなし）

### リスク2: パフォーマンス低下

**対策**:
- ASTパーサーの最適化
- 並列処理の導入
- 段階的な分析（基本→詳細）

### リスク3: 複雑性の増加

**対策**:
- 明確なインターフェース設計
- 豊富なドキュメント
- 設定のデフォルト値を適切に設定

## 成功基準

Phase 2の成功は以下で判断：

1. ✅ 誤検出率 < 10%
2. ✅ LLM統合の動作確認
3. ✅ ASTパーサーの実装
4. ✅ テストカバレッジ > 90% 維持
5. ✅ 実行時間 < 60秒（100ファイル）
6. ✅ CLIツールの完成
7. ✅ ドキュメント完備

## タイムライン

- **Day 6**: LLM統合基盤（2日間）
- **Day 7**: ASTパーサー（2日間）
- **Day 8**: スマート検出器（2日間）
- **Day 9**: 評価・改善（2日間）
- **Day 10**: CLI・ドキュメント（1日間）

**合計**: 約9日間

## 次のステップ

1. Phase 2計画の承認
2. 依存パッケージのインストール
3. Day 6タスクの開始

---

Phase 2の実装により、Cassandra Code Analyzerは本格的な実用ツールになります。
