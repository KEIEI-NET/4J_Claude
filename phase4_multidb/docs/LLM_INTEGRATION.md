# LLM統合ガイド

**バージョン**: v1.0.0
**最終更新**: 2025年01月27日

## 目次

1. [概要](#概要)
2. [セットアップ](#セットアップ)
3. [基本的な使い方](#基本的な使い方)
4. [プロンプトエンジニアリング](#プロンプトエンジニアリング)
5. [コスト管理](#コスト管理)
6. [高度な機能](#高度な機能)
7. [ベストプラクティス](#ベストプラクティス)
8. [トラブルシューティング](#トラブルシューティング)

---

## 概要

LLM統合モジュールは、Claude API（Anthropic）を使用して、静的解析では困難な以下の機能を提供します:

- **深い意味論的理解**: コードの文脈を理解した問題分析
- **最適化提案の生成**: ベストプラクティスに基づいた具体的な修正案
- **自動修正コード生成**: 実際に適用可能なコードの生成
- **問題の優先順位付け**: ビジネス影響を考慮した順序付け
- **説明の生成**: 技術的な根拠とトレードオフの説明

### なぜLLMが必要なのか？

従来の静的解析では:
- パターンマッチングに限定される
- コンテキストを理解できない
- 具体的な最適化案を提示できない
- トレードオフを説明できない

LLMを使用すると:
- コード全体の文脈を理解
- ドメイン知識を活用
- 実行可能な提案を生成
- 詳細な説明とトレードオフを提供

---

## セットアップ

### 1. 依存関係のインストール

```bash
cd phase4_multidb
pip install anthropic>=0.18.0
```

または、requirements.txtから:
```bash
pip install -r requirements.txt
```

### 2. APIキーの取得

1. [Anthropic Console](https://console.anthropic.com/)にアクセス
2. アカウントを作成（まだの場合）
3. APIキーを生成
4. クレジットカードを登録（使用量に応じて課金）

### 3. 環境変数の設定

**.env ファイル** (推奨):
```env
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx
```

**環境変数として直接設定** (Windows):
```cmd
setx ANTHROPIC_API_KEY "sk-ant-api03-xxxxxxxxxxxxx"
```

**環境変数として直接設定** (Linux/Mac):
```bash
export ANTHROPIC_API_KEY="sk-ant-api03-xxxxxxxxxxxxx"
```

### 4. 動作確認

```python
from multidb_analyzer.llm import ClaudeClient

try:
    client = ClaudeClient()
    response = client.generate("Say hello!")
    print(f"✅ LLM connection successful: {response}")
except Exception as e:
    print(f"❌ Error: {e}")
```

---

## 基本的な使い方

### ClaudeClient: 基本的なテキスト生成

```python
from multidb_analyzer.llm import ClaudeClient, ClaudeModel

# 初期化
client = ClaudeClient(
    api_key="sk-ant-xxxxx",  # または環境変数から自動取得
    model=ClaudeModel.SONNET,  # OPUS, SONNET, HAIKU
    max_retries=3,
    timeout=60
)

# テキスト生成
response = client.generate(
    prompt="Explain why leading wildcards are slow in Elasticsearch",
    system_prompt="You are an Elasticsearch expert",
    max_tokens=1024,
    temperature=0.3  # 0.0-1.0, 低いほど確定的
)

print(response)
```

### LLMOptimizer: コード最適化

```python
from multidb_analyzer.llm import LLMOptimizer
from multidb_analyzer.core.base_detector import Issue, Severity, IssueCategory

# 初期化
optimizer = LLMOptimizer(
    api_key="sk-ant-xxxxx",
    temperature=0.3  # 技術的な分析には低温度推奨
)

# 問題定義
issue = Issue(
    detector_name="WildcardDetector",
    severity=Severity.CRITICAL,
    category=IssueCategory.PERFORMANCE,
    title="Leading Wildcard Query",
    description="Query uses leading wildcard which causes full index scan",
    file_path="SearchService.java",
    line_number=42,
    query_text='wildcardQuery("name", "*smith")',
    suggestion="Use prefix query instead"
)

# 最適化
result = optimizer.optimize_issue(
    issue=issue,
    code='wildcardQuery("name", "*smith")',
    language="java",
    db_type="elasticsearch"
)

# 結果の利用
print(f"Root Cause: {result.root_cause}")
print(f"Performance Impact: {result.performance_impact}")
print(f"Optimized Code:\n{result.optimized_code}")
print(f"Confidence: {result.confidence_score}")
```

---

## プロンプトエンジニアリング

### プロンプトの構造

LLMに効果的に指示を出すには、適切なプロンプト設計が重要です。

#### システムプロンプト

システムプロンプトは、LLMの役割と専門性を定義します:

```python
from multidb_analyzer.llm import PromptTemplates

print(PromptTemplates.SYSTEM_PROMPT)
```

**デフォルトのシステムプロンプト**:
```
You are an expert database performance consultant specializing in Elasticsearch,
MySQL, Redis, and SQL Server. Your expertise includes:

- Query optimization and performance tuning
- Index design and management
- Database architecture best practices
- Trade-off analysis between different approaches
- Code review with a focus on database interactions

Provide detailed, actionable advice with concrete code examples.
Always explain the reasoning behind your recommendations.
```

#### タスク固有プロンプト

各タスクに最適化されたプロンプトテンプレートを使用:

```python
# Elasticsearch最適化プロンプト
prompt = PromptTemplates.format_elasticsearch_optimization(
    issue=detected_issue,
    code=original_code,
    language="java"
)

# 問題優先順位付けプロンプト
prompt = PromptTemplates.format_prioritize_issues(all_issues)

# 自動修正生成プロンプト
prompt = PromptTemplates.format_auto_fix(
    issue=issue,
    code=code,
    db_type="elasticsearch",
    framework="Spring Data"
)
```

### カスタムプロンプトの作成

プロジェクト固有の要件に合わせてカスタマイズ:

```python
custom_system_prompt = """
You are an expert in Elasticsearch optimization for e-commerce platforms.

Context:
- Our platform handles 10M+ products
- Search latency must be < 100ms (P99)
- Budget constraints: optimize for cost

Guidelines:
- Prioritize latency over features
- Consider AWS Elasticsearch pricing
- Provide cost estimates when relevant
"""

client = ClaudeClient()
response = client.generate(
    prompt="How can I optimize this product search query?",
    system_prompt=custom_system_prompt
)
```

---

## コスト管理

### 料金体系（2025年01月時点）

| モデル | 入力トークン | 出力トークン | 推奨用途 |
|--------|-------------|-------------|----------|
| Opus | $15/1M | $75/1M | 複雑な分析 |
| Sonnet | $3/1M | $15/1M | 標準的な用途（推奨） |
| Haiku | $0.25/1M | $1.25/1M | 大量処理 |

### コスト追跡

```python
from multidb_analyzer.llm import ClaudeClient

client = ClaudeClient(model=ClaudeModel.SONNET)

# 複数のリクエストを実行
for i in range(10):
    client.generate(f"Analyze query {i}")

# 使用統計を確認
stats = client.get_usage_stats()

print(f"Total Requests: {stats['total_requests']}")
print(f"Total Tokens: {stats['total_tokens']:,}")
print(f"  - Input: {stats['input_tokens']:,}")
print(f"  - Output: {stats['output_tokens']:,}")
print(f"Total Cost: ${stats['total_cost_usd']:.4f}")
print(f"Avg Cost/Request: ${stats['average_cost_per_request']:.4f}")

# リクエスト履歴
for req in stats['request_history']:
    print(f"  {req['timestamp']}: {req['input_tokens']} in, {req['output_tokens']} out")
```

### コスト最適化戦略

#### 1. 適切なモデル選択

```python
# 簡単なタスク（構造抽出、分類）: Haiku
client_haiku = ClaudeClient(model=ClaudeModel.HAIKU)

# 標準的なタスク（最適化提案）: Sonnet (推奨)
client_sonnet = ClaudeClient(model=ClaudeModel.SONNET)

# 複雑なタスク（アーキテクチャ設計）: Opus
client_opus = ClaudeClient(model=ClaudeModel.OPUS)
```

#### 2. バッチ処理

```python
# ❌ 非効率: 個別リクエスト
for issue in issues:
    optimizer.optimize_issue(issue, code)

# ✅ 効率的: バッチ処理
optimizer.optimize_batch(issues, code_snippets)
```

#### 3. プロンプト最適化

```python
# ❌ 冗長なプロンプト
prompt = f"""
Here is a very long explanation of the problem...
[1000 lines of context]
Now please analyze this query: {query}
"""

# ✅ 簡潔なプロンプト
prompt = f"""
Query: {query}
Issue: {issue.title}
Context: {relevant_context}

Analyze and optimize.
"""
```

#### 4. キャッシング

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_optimization(issue_hash: str, code: str):
    """同じ問題は再分析しない"""
    return optimizer.optimize_issue(issue, code)
```

#### 5. レート制限の設定

```python
# バッチ処理で遅延を設定（API制限対策）
responses = client.generate_batch(
    prompts,
    delay_between_requests=1.5  # 秒
)
```

---

## 高度な機能

### 1. バッチ最適化

複数の問題を効率的に処理:

```python
from multidb_analyzer.llm import LLMOptimizer

optimizer = LLMOptimizer()

# 問題リスト
issues = [issue1, issue2, issue3, ...]

# コードスニペット
code_snippets = {
    "SearchService.java:42": 'wildcardQuery("name", "*smith")',
    "SearchService.java:55": 'searchSourceBuilder.size(10000)',
    # ...
}

# バッチ最適化
results = optimizer.optimize_batch(
    issues=issues,
    code_snippets=code_snippets,
    language="java",
    db_type="elasticsearch"
)

# 結果を処理
for i, result in enumerate(results):
    print(f"\n=== Issue {i+1} ===")
    print(f"Title: {result.issue.title}")
    print(f"Optimized Code:\n{result.optimized_code}")
```

### 2. 問題の優先順位付け

LLMを使って最適な修正順序を決定:

```python
# 優先順位を決定
prioritization = optimizer.prioritize_issues(all_issues)

# Quick Wins（簡単で効果が高い）
print("\n=== Quick Wins ===")
for issue_id in prioritization['quick_wins']:
    issue = all_issues[int(issue_id)]
    print(f"- {issue.title}")

# High Risk, High Reward（難しいが重要）
print("\n=== High Risk, High Reward ===")
for issue_id in prioritization['high_risk_high_reward']:
    issue = all_issues[int(issue_id)]
    print(f"- {issue.title}")

# Technical Debt（後で対応）
print("\n=== Technical Debt ===")
for issue_id in prioritization['technical_debt']:
    issue = all_issues[int(issue_id)]
    print(f"- {issue.title}")
```

### 3. 自動修正の生成

実際に適用可能なコードを生成:

```python
fix = optimizer.generate_auto_fix(
    issue=wildcard_issue,
    code='wildcardQuery("name", "*smith")',
    db_type="elasticsearch",
    framework="Spring Data",
    language="java"
)

# 修正コード
print(f"Fixed Code:\n{fix['fixed_code']}")

# 信頼度チェック
if fix['confidence'] > 0.8:
    print("✅ High confidence - safe to apply")
else:
    print("⚠️ Low confidence - manual review required")

# Breaking changes警告
if fix['breaking_changes']:
    print(f"⚠️ Warning: {fix['migration_notes']}")
```

### 4. カスタムモデルパラメータ

```python
from multidb_analyzer.llm import LLMOptimizer, ClaudeModel

# 創造的な提案が必要な場合（高温度）
creative_optimizer = LLMOptimizer(
    model=ClaudeModel.OPUS,
    temperature=0.8,  # より創造的
    max_tokens=8192   # より長い応答
)

# 確定的な修正が必要な場合（低温度）
deterministic_optimizer = LLMOptimizer(
    model=ClaudeModel.SONNET,
    temperature=0.1,  # より確定的
    max_tokens=2048
)

# タスクに応じて使い分け
creative_result = creative_optimizer.optimize_issue(issue, code)
deterministic_fix = deterministic_optimizer.generate_auto_fix(issue, code)
```

---

## ベストプラクティス

### 1. エラーハンドリング

```python
from multidb_analyzer.exceptions import LLMError

try:
    result = optimizer.optimize_issue(issue, code)
except LLMError as e:
    # フォールバック: 静的解析結果のみ使用
    logger.warning(f"LLM analysis failed: {e}")
    result = create_basic_result(issue)
except Exception as e:
    # 予期しないエラー
    logger.error(f"Unexpected error: {e}")
    raise
```

### 2. タイムアウト管理

```python
# タイムアウトを設定
client = ClaudeClient(timeout=30)  # 30秒

# または、リトライ回数を調整
client = ClaudeClient(max_retries=5)
```

### 3. レスポンスの検証

```python
result = optimizer.optimize_issue(issue, code)

# 結果の妥当性チェック
if result.confidence_score < 0.7:
    logger.warning("Low confidence result")
    # 追加の検証やマニュアルレビュー

if not result.optimized_code:
    logger.error("No optimized code generated")
    # フォールバック処理
```

### 4. プログレス表示

```python
from tqdm import tqdm

issues = [...]  # 大量の問題

results = []
for issue in tqdm(issues, desc="Optimizing"):
    result = optimizer.optimize_issue(issue, code_snippets[issue])
    results.append(result)

    # 定期的にコスト確認
    if len(results) % 10 == 0:
        stats = optimizer.get_usage_stats()
        tqdm.write(f"Cost so far: ${stats['total_cost_usd']:.4f}")
```

### 5. 結果のキャッシング

```python
import json
from pathlib import Path

def cache_result(issue_id: str, result: OptimizationResult):
    """結果をキャッシュ"""
    cache_dir = Path('.cache/llm_results')
    cache_dir.mkdir(parents=True, exist_ok=True)

    cache_file = cache_dir / f"{issue_id}.json"
    with open(cache_file, 'w') as f:
        json.dump(result.to_dict(), f, indent=2)

def load_cached_result(issue_id: str) -> Optional[dict]:
    """キャッシュから読み込み"""
    cache_file = Path(f'.cache/llm_results/{issue_id}.json')
    if cache_file.exists():
        with open(cache_file, 'r') as f:
            return json.load(f)
    return None

# 使用例
issue_id = f"{issue.file_path}:{issue.line_number}"

cached = load_cached_result(issue_id)
if cached:
    print("Using cached result")
    result = OptimizationResult(**cached)
else:
    print("Generating new result")
    result = optimizer.optimize_issue(issue, code)
    cache_result(issue_id, result)
```

---

## トラブルシューティング

### 問題1: API キーエラー

**症状**:
```
ValueError: API key not provided. Set ANTHROPIC_API_KEY environment variable or pass api_key parameter.
```

**解決策**:
```bash
# 環境変数を設定
export ANTHROPIC_API_KEY="sk-ant-xxxxx"

# または.envファイルを作成
echo "ANTHROPIC_API_KEY=sk-ant-xxxxx" > .env
```

### 問題2: レート制限エラー

**症状**:
```
anthropic.RateLimitError: Rate limit exceeded
```

**解決策**:
```python
# 遅延を追加
client.generate_batch(
    prompts,
    delay_between_requests=2.0  # 秒
)

# または、リトライ回数を増やす
client = ClaudeClient(max_retries=5)
```

### 問題3: タイムアウト

**症状**:
```
TimeoutError: Request timed out after 60 seconds
```

**解決策**:
```python
# タイムアウトを延長
client = ClaudeClient(timeout=120)

# または、トークン数を削減
optimizer = LLMOptimizer(max_tokens=2048)
```

### 問題4: コストが高すぎる

**原因と解決策**:

1. **不要なリクエスト**
   ```python
   # ❌ 毎回LLMを呼び出す
   for issue in issues:
       result = optimizer.optimize_issue(issue, code)

   # ✅ キャッシュを使用
   cached_results = load_cache()
   for issue in issues:
       if issue.id not in cached_results:
           result = optimizer.optimize_issue(issue, code)
   ```

2. **高価なモデルを使用**
   ```python
   # ❌ すべてでOpusを使用
   optimizer = LLMOptimizer(model=ClaudeModel.OPUS)

   # ✅ 用途に応じて選択
   optimizer = LLMOptimizer(model=ClaudeModel.SONNET)  # 標準
   ```

3. **冗長なプロンプト**
   ```python
   # ❌ 長すぎるコンテキスト
   prompt = f"Here is the entire file:\n{entire_file_content}"

   # ✅ 必要な部分のみ
   prompt = f"Here is the problematic code:\n{code_snippet}"
   ```

### 問題5: 低品質な応答

**原因と解決策**:

1. **温度が高すぎる**
   ```python
   # ❌ 温度が高い
   optimizer = LLMOptimizer(temperature=0.9)

   # ✅ 技術的な分析には低温度
   optimizer = LLMOptimizer(temperature=0.3)
   ```

2. **不明確なプロンプト**
   ```python
   # ❌ 曖昧な指示
   prompt = "Make this code better"

   # ✅ 具体的な指示
   prompt = """
   Optimize this Elasticsearch query:
   - Reduce latency by 50%
   - Maintain current functionality
   - Use only official Elasticsearch APIs
   """
   ```

3. **システムプロンプトが不適切**
   ```python
   # ❌ 一般的すぎる
   system_prompt = "You are a helpful assistant"

   # ✅ 専門性を明確に
   system_prompt = "You are an Elasticsearch expert with 10 years of experience..."
   ```

---

## セキュリティとプライバシー

### データの取り扱い

Anthropicのデータ保持ポリシー（2025年01月時点）:
- APIリクエストは30日間保持される
- 機械学習モデルのトレーニングには使用されない（オプトインしない限り）
- エンタープライズプランではデータ保持期間をカスタマイズ可能

### ベストプラクティス

```python
# ❌ 機密情報を送信しない
prompt = f"Analyze this query with API key: {api_key}"

# ✅ 機密情報をサニタイズ
sanitized_code = sanitize_sensitive_data(code)
prompt = f"Analyze this query: {sanitized_code}"
```

---

## まとめ

このガイドでは、LLM統合モジュールの以下の側面をカバーしました:

1. **セットアップ**: APIキー取得と環境設定
2. **基本的な使い方**: ClaudeClientとLLMOptimizerの使用
3. **プロンプトエンジニアリング**: 効果的なプロンプト設計
4. **コスト管理**: 料金体系と最適化戦略
5. **高度な機能**: バッチ処理、優先順位付け、自動修正
6. **ベストプラクティス**: エラーハンドリング、キャッシング
7. **トラブルシューティング**: 一般的な問題と解決策

---

**参考リソース**:
- [Anthropic API ドキュメント](https://docs.anthropic.com/)
- [Claude モデルカード](https://www.anthropic.com/claude)
- [プロンプトエンジニアリングガイド](https://docs.anthropic.com/claude/docs/prompt-engineering)

---

**次のステップ**: ドキュメントを全て確認したら、Phase 6-4 (MySQL実装) に進みます。
