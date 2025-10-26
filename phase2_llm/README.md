# Phase 2: LLM統合

**ステータス**: 🔵 計画中
**期間**: 2025年11月11日 - 11月22日

## 目標

Claude Sonnet 4.5 / GPT-5 Codexによる深い分析機能の実装

## 主要機能

### Week 3: LLM基盤実装

#### Task 10.1: LLMクライアント実装
- Claude Sonnet 4.5 APIクライアント
- レート制限管理
- リトライロジック
- コスト追跡

#### Task 10.2: ハイブリッド分析エンジン
- 静的解析とLLM分析の統合
- Tierベースのファイル分類（Tier 1-3）
- 信頼度計算アルゴリズム

#### Task 10.3: データモデル評価機能
- CQLスキーマ解析
- パーティションキー設計評価
- Materialized View提案

#### Task 10.4: Consistency Level詳細分析
- Consistency Level追跡
- Read/Write整合性チェック
- パフォーマンスとの trade-off 分析

### Week 4: 自動修正と統合

#### Task 11.1: 自動修正提案生成
- 問題パターンごとの修正テンプレート
- LLMによる修正コード生成
- 安全性検証

#### Task 11.2: コスト管理システム
- APIコール数追跡
- トークン使用量追跡
- 予算アラート
- 月次レポート生成

## 成功条件

- [ ] LLM統合が動作
- [ ] 自動修正提案が有用
- [ ] コスト管理が機能
- [ ] LLM精度 > 85%

## 予算

- LLMコスト: $315/月
- 開発環境: $100/月
- **月間合計**: $415

## ディレクトリ構造（予定）

```
phase2_llm/
├── src/
│   └── cassandra_analyzer/
│       ├── llm/
│       │   ├── client.py         # LLM APIクライアント
│       │   ├── prompt_builder.py # プロンプト管理
│       │   └── cost_manager.py   # コスト追跡
│       ├── analyzers/
│       │   ├── hybrid_analyzer.py       # ハイブリッド分析
│       │   ├── data_model_evaluator.py  # データモデル評価
│       │   └── consistency_analyzer.py  # Consistency分析
│       └── fixers/
│           └── auto_fixer.py     # 自動修正
├── tests/
│   ├── unit/
│   └── integration/
└── README.md                     # このファイル
```

## 詳細計画

詳細なタスクとタイムラインは [`../TODO.md`](../TODO.md) のPhase 2セクションを参照してください。

---

**開始日**: 2025年11月11日（予定）
