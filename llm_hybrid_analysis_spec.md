# LLM統合型ハイブリッドコード分析システム 詳細仕様書

## 1. エグゼクティブサマリー

### 1.1 ハイブリッドアプローチの必然性

従来の静的解析には以下の限界があります:

| 静的解析の限界 | 具体例 | LLMによる解決 |
|--------------|--------|--------------|
| コンテキスト理解不足 | ビジネスロジックの妥当性判定不可 | ビジネス要件との整合性を推論 |
| 動的コードの追跡困難 | リフレクション、動的SQL生成 | コードパターンから動作を推定 |
| 複雑なロジックの評価 | 分散トランザクションの正当性 | 複数ファイルを横断して意図を理解 |
| 修正提案の限界 | 問題検出のみ、修正案なし | 具体的な修正コードを生成 |
| ドメイン知識不足 | Cassandra最適解の判断不可 | ベストプラクティスに基づく推奨 |

### 1.2 ハイブリッドシステムの設計思想

```
┌────────────────────────────────────────────────────┐
│           入力: ソースコード (35,000ファイル)       │
└────────────────┬───────────────────────────────────┘
                 │
        ┌────────┴────────┐
        ▼                  ▼
┌──────────────┐    ┌──────────────┐
│ 静的解析層    │    │ LLM分析層     │
│              │    │              │
│ ✓ 高速        │    │ ✓ 深い理解    │
│ ✓ 確実        │    │ ✓ 柔軟        │
│ ✓ 構造的      │    │ ✓ 意味的      │
└──────┬───────┘    └──────┬───────┘
       │                   │
       └────────┬──────────┘
                ▼
     ┌────────────────────┐
     │  統合判定レイヤー    │
     │  - 信頼度スコア計算  │
     │  - 結果の融合        │
     │  - 優先度付け        │
     └────────┬───────────┘
              ▼
     ┌────────────────────┐
     │  人間レビュー        │
     │  (低信頼度のみ)      │
     └────────────────────┘
```

### 1.3 LLM活用の主要ユースケース

#### ✅ **レベル1: 静的解析の補完**
- リフレクション、動的SQLの解析
- 間接的な依存関係の推定
- 複雑な制御フローの理解

#### ✅ **レベル2: 意味的な問題検出**
- ビジネスロジックの矛盾検出
- データモデル設計の妥当性評価
- 整合性レベル選択の妥当性判断

#### ✅ **レベル3: 修正提案の生成**
- 問題コードの具体的な修正案
- 複数の代替案と長短の説明
- マイグレーション手順の自動生成

#### ✅ **レベル4: 説明の自動生成**
- 技術的な問題を平易に説明
- 影響範囲を自然言語で記述
- 経営層向けレポートの生成

---

## 2. ハイブリッドアーキテクチャ詳細設計

### 2.1 システムアーキテクチャ

```python
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

class AnalysisConfidence(Enum):
    """分析結果の信頼度"""
    CERTAIN = "certain"          # 100% 確実（静的解析）
    HIGH = "high"                # 90-99% （静的+LLM一致）
    MEDIUM = "medium"            # 70-89% （LLM推定）
    LOW = "low"                  # 50-69% （推測）
    UNCERTAIN = "uncertain"      # <50% （要人間判断）

@dataclass
class AnalysisResult:
    """分析結果の統一フォーマット"""
    issue_type: str
    severity: str  # critical, high, medium, low
    confidence: AnalysisConfidence
    
    # 静的解析の結果
    static_analysis: Optional[Dict[str, Any]]
    
    # LLMの分析結果
    llm_analysis: Optional[Dict[str, Any]]
    
    # 統合判定
    final_verdict: str
    
    # 証拠
    evidence: List[str]
    
    # 修正提案
    fix_suggestions: List[str]
    
    # 説明（自然言語）
    explanation: str
    
    # 影響範囲
    impact_scope: Dict[str, Any]

class HybridAnalysisEngine:
    """
    静的解析とLLM分析を統合するエンジン
    """
    
    def __init__(
        self,
        static_analyzer,
        llm_client,  # GPT-5 Codex または Claude Sonnet 4.5
        neo4j_driver,
        confidence_threshold: float = 0.7
    ):
        self.static_analyzer = static_analyzer
        self.llm_client = llm_client
        self.neo4j = neo4j_driver
        self.confidence_threshold = confidence_threshold
        
    async def analyze_code(
        self, 
        file_path: str, 
        analysis_type: str = "comprehensive"
    ) -> List[AnalysisResult]:
        """
        ファイルを包括的に分析
        
        分析タイプ:
        - quick: 静的解析のみ（高速）
        - standard: 静的解析 + 重要箇所のLLM分析
        - comprehensive: 全面的なLLM分析
        - critical_only: 致命的な問題のみLLM確認
        """
        results = []
        
        # Step 1: 静的解析を実行（常に実行）
        static_results = await self.static_analyzer.analyze(file_path)
        
        if analysis_type == "quick":
            # 静的解析のみで終了
            return static_results
        
        # Step 2: 信頼度が低い、または重要度が高い問題をLLMで分析
        for static_result in static_results:
            if self._should_use_llm(static_result, analysis_type):
                # LLM分析を実行
                llm_result = await self._llm_deep_analysis(
                    file_path, 
                    static_result
                )
                
                # 結果を統合
                integrated = self._integrate_results(static_result, llm_result)
                results.append(integrated)
            else:
                # 静的解析結果をそのまま使用
                results.append(static_result)
        
        # Step 3: LLM独自の分析（静的解析で検出できない問題）
        if analysis_type in ["comprehensive", "standard"]:
            llm_only_issues = await self._llm_semantic_analysis(file_path)
            results.extend(llm_only_issues)
        
        return results
    
    def _should_use_llm(
        self, 
        static_result: AnalysisResult, 
        analysis_type: str
    ) -> bool:
        """
        LLM分析が必要か判定
        """
        # 致命的な問題は必ずLLMで確認
        if static_result.severity == "critical":
            return True
        
        # 信頼度が低い場合
        if static_result.confidence in [AnalysisConfidence.LOW, AnalysisConfidence.UNCERTAIN]:
            return True
        
        # 包括的分析モード
        if analysis_type == "comprehensive":
            return True
        
        # データベース関連は必ずLLMで確認
        if "database" in static_result.issue_type.lower():
            return True
        
        return False
    
    async def _llm_deep_analysis(
        self, 
        file_path: str, 
        static_result: AnalysisResult
    ) -> Dict[str, Any]:
        """
        LLMによる深い分析
        """
        # ファイルのコンテキストを収集
        code_context = await self._gather_code_context(file_path)
        
        # LLMプロンプトを構築
        prompt = self._build_analysis_prompt(code_context, static_result)
        
        # LLMに分析を依頼
        llm_response = await self.llm_client.analyze(prompt)
        
        return llm_response
    
    async def _gather_code_context(self, file_path: str) -> Dict[str, Any]:
        """
        分析に必要なコンテキストを収集
        
        - ファイルの内容
        - 依存するファイルの内容
        - 呼び出されるメソッドの実装
        - データモデル定義
        - 関連するコメント、ドキュメント
        """
        context = {
            'target_file': await self._read_file(file_path),
            'dependencies': [],
            'callers': [],
            'data_models': [],
            'comments': []
        }
        
        # Neo4jから依存関係を取得
        deps_query = """
        MATCH (f:File {path: $path})-[:DEPENDS_ON]->(dep:File)
        RETURN dep.path as depPath, dep.content as depContent
        LIMIT 5
        """
        
        dependencies = self.neo4j.execute_query(deps_query, path=file_path)
        
        for dep in dependencies:
            context['dependencies'].append({
                'path': dep['depPath'],
                'content': dep['depContent'][:2000]  # 最初の2000文字
            })
        
        # Cassandraテーブル定義を取得
        if 'cassandra' in file_path.lower():
            context['data_models'] = await self._get_cassandra_schema_context(file_path)
        
        return context
    
    def _build_analysis_prompt(
        self, 
        context: Dict[str, Any], 
        static_result: AnalysisResult
    ) -> str:
        """
        LLM分析用のプロンプトを構築
        """
        prompt = f"""
あなたは熟練したソフトウェアアーキテクトです。以下のコードを分析してください。

## 静的解析の結果
問題タイプ: {static_result.issue_type}
重要度: {static_result.severity}
信頼度: {static_result.confidence}

{static_result.static_analysis}

## 分析対象のコード
```
{context['target_file']}
```

## 依存ファイル
{self._format_dependencies(context['dependencies'])}

## データモデル定義
{self._format_data_models(context['data_models'])}

## 分析タスク
以下の観点から詳細に分析してください:

1. **問題の妥当性**: 静的解析が指摘した問題は本当に問題か?
2. **ビジネスロジックの妥当性**: コードの意図は何か? 設計として正しいか?
3. **データベース設計**: Cassandraの使い方として適切か?
4. **整合性レベル**: 選択されているConsistency Levelは要件に合っているか?
5. **パフォーマンス**: ボトルネックになる可能性は?
6. **保守性**: コードは理解しやすく変更しやすいか?

## 出力フォーマット
必ず以下のJSON形式で回答してください:

{{
  "is_real_issue": true/false,
  "confidence": 0.0-1.0,
  "issue_explanation": "問題の詳細な説明",
  "business_context": "ビジネス要件との整合性",
  "severity_assessment": "critical/high/medium/low",
  "root_cause": "根本原因の説明",
  "impact_analysis": {{
    "performance": "パフォーマンスへの影響",
    "data_integrity": "データ整合性への影響",
    "maintainability": "保守性への影響"
  }},
  "fix_suggestions": [
    {{
      "approach": "修正アプローチ1",
      "code_example": "具体的なコード例",
      "pros": ["メリット1", "メリット2"],
      "cons": ["デメリット1"],
      "effort": "low/medium/high"
    }}
  ],
  "alternative_designs": [
    "代替設計案1",
    "代替設計案2"
  ],
  "references": [
    "参考となるベストプラクティス"
  ]
}}
"""
        return prompt
    
    def _integrate_results(
        self, 
        static_result: AnalysisResult, 
        llm_result: Dict[str, Any]
    ) -> AnalysisResult:
        """
        静的解析とLLM分析の結果を統合
        """
        # LLMが問題ではないと判断した場合
        if not llm_result.get('is_real_issue', True):
            # 誤検出として除外
            if llm_result.get('confidence', 0) > 0.8:
                return None  # 結果から除外
        
        # 信頼度の計算
        static_confidence = self._confidence_to_float(static_result.confidence)
        llm_confidence = llm_result.get('confidence', 0.5)
        
        # 両方が一致する場合は信頼度が高い
        if static_result.severity == llm_result.get('severity_assessment'):
            final_confidence = (static_confidence + llm_confidence) / 2 * 1.2  # ブースト
        else:
            final_confidence = min(static_confidence, llm_confidence)
        
        # 統合結果を作成
        integrated = AnalysisResult(
            issue_type=static_result.issue_type,
            severity=llm_result.get('severity_assessment', static_result.severity),
            confidence=self._float_to_confidence(final_confidence),
            static_analysis=static_result.static_analysis,
            llm_analysis=llm_result,
            final_verdict=llm_result.get('issue_explanation', ''),
            evidence=[
                *static_result.evidence,
                llm_result.get('root_cause', '')
            ],
            fix_suggestions=llm_result.get('fix_suggestions', []),
            explanation=self._generate_explanation(static_result, llm_result),
            impact_scope=llm_result.get('impact_analysis', {})
        )
        
        return integrated
    
    async def _llm_semantic_analysis(self, file_path: str) -> List[AnalysisResult]:
        """
        LLM独自の意味的分析
        
        静的解析では検出できない問題を検出:
        - ビジネスロジックの矛盾
        - データモデル設計の問題
        - アーキテクチャの問題
        - セキュリティの問題
        """
        context = await self._gather_code_context(file_path)
        
        prompt = f"""
以下のコードを包括的にレビューしてください。
静的解析ツールでは検出できない、深い設計上の問題を探してください。

## コード
```
{context['target_file']}
```

## 依存ファイル
{self._format_dependencies(context['dependencies'])}

## チェック観点
1. ビジネスロジックの一貫性
2. データモデル設計の妥当性
3. トランザクション境界の正しさ
4. エラーハンドリングの妥当性
5. セキュリティリスク
6. スケーラビリティの問題
7. テスタビリティ

特にCassandraを使用している場合:
- Partition Keyの設計は適切か
- Consistency Levelの選択は要件に合っているか
- データ分散は適切か
- ホットスポットのリスクは?

見つかった問題を前述のJSON形式で返してください。
問題がない場合は空配列を返してください。
"""
        
        llm_response = await self.llm_client.analyze(prompt)
        
        # LLM独自の問題をAnalysisResultに変換
        issues = []
        for llm_issue in llm_response.get('issues', []):
            result = AnalysisResult(
                issue_type=llm_issue.get('type', 'semantic_issue'),
                severity=llm_issue.get('severity', 'medium'),
                confidence=AnalysisConfidence.MEDIUM,
                static_analysis=None,
                llm_analysis=llm_issue,
                final_verdict=llm_issue.get('description', ''),
                evidence=llm_issue.get('evidence', []),
                fix_suggestions=llm_issue.get('fix_suggestions', []),
                explanation=llm_issue.get('explanation', ''),
                impact_scope=llm_issue.get('impact', {})
            )
            issues.append(result)
        
        return issues
```

### 2.2 LLMクライアント実装

```python
from abc import ABC, abstractmethod
import anthropic
import openai
from typing import Dict, Any

class LLMClient(ABC):
    """LLMクライアントの基底クラス"""
    
    @abstractmethod
    async def analyze(self, prompt: str) -> Dict[str, Any]:
        """コード分析を実行"""
        pass
    
    @abstractmethod
    async def generate_fix(self, issue: Dict[str, Any]) -> str:
        """修正コードを生成"""
        pass

class ClaudeSonnetClient(LLMClient):
    """Claude Sonnet 4.5クライアント"""
    
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-5-20250514"
        
    async def analyze(self, prompt: str) -> Dict[str, Any]:
        """
        Claudeでコード分析
        
        Claude Sonnetの特徴:
        - 長いコンテキストウィンドウ (200K tokens)
        - 優れたコード理解能力
        - JSON出力の正確性
        """
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=0.0,  # 決定論的な出力
            system="""あなたは熟練したソフトウェアアーキテクトです。
コードレビューと問題検出において世界最高レベルの専門知識を持っています。
特にCassandraのようなNoSQLデータベースの設計に精通しています。
必ず有効なJSON形式で回答してください。""",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # JSON応答をパース
        content = response.content[0].text
        
        # JSONを抽出（マークダウンのコードブロックを除去）
        json_str = self._extract_json(content)
        
        return json.loads(json_str)
    
    async def generate_fix(self, issue: Dict[str, Any]) -> str:
        """修正コードを生成"""
        prompt = f"""
以下の問題に対する修正コードを生成してください。

## 問題
{issue['description']}

## 元のコード
```
{issue['original_code']}
```

## 要件
- 問題を完全に解決すること
- コードの可読性を維持すること
- 既存のコードスタイルに合わせること
- コメントで変更理由を説明すること

修正後のコード全体を出力してください。
"""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    def _extract_json(self, text: str) -> str:
        """テキストからJSON部分を抽出"""
        # ```json ... ``` を除去
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        # {} で囲まれた部分を探す
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json_match.group(0)
        
        return text

class GPT5CodexClient(LLMClient):
    """GPT-5 Codexクライアント (将来対応)"""
    
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = "gpt-5-turbo"  # 実際のモデル名は異なる可能性
        
    async def analyze(self, prompt: str) -> Dict[str, Any]:
        """GPT-5でコード分析"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert software architect specializing in code review and bug detection."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},  # JSON出力を強制
            temperature=0.0
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def generate_fix(self, issue: Dict[str, Any]) -> str:
        """修正コードを生成"""
        # Claude実装と同様
        pass
```

---

## 3. Cassandra特化LLM分析

### 3.1 Cassandraデータモデル評価

```python
class CassandraLLMAnalyzer:
    """
    LLMを使ったCassandra特化分析
    """
    
    def __init__(self, llm_client: LLMClient, neo4j_driver):
        self.llm = llm_client
        self.neo4j = neo4j_driver
    
    async def evaluate_data_model(
        self, 
        table_name: str, 
        keyspace: str
    ) -> Dict[str, Any]:
        """
        Cassandraテーブル設計をLLMで評価
        
        評価観点:
        - Partition Key設計の妥当性
        - Clustering Key設計
        - アクセスパターンとの整合性
        - スケーラビリティ
        - ホットスポットリスク
        """
        # テーブル定義を取得
        table_schema = await self._get_table_schema(table_name, keyspace)
        
        # このテーブルへのアクセスパターンを取得
        access_patterns = await self._get_access_patterns(table_name, keyspace)
        
        # クエリ例を取得
        query_examples = await self._get_query_examples(table_name, keyspace)
        
        # LLMに評価を依頼
        prompt = f"""
Cassandraのテーブル設計を評価してください。

## テーブル定義
```cql
{table_schema}
```

## アクセスパターン
{self._format_access_patterns(access_patterns)}

## 実際のクエリ例
{self._format_queries(query_examples)}

## 評価タスク
以下の観点から設計を評価してください:

1. **Partition Key設計**
   - カーディナリティは適切か
   - データ分散は均等か
   - ホットスポットのリスクは?

2. **Clustering Key設計**
   - ソート順序は要件に合っているか
   - 範囲クエリは効率的か

3. **アクセスパターンとの整合性**
   - クエリパターンに最適化されているか
   - ALLOW FILTERINGが必要になっていないか

4. **スケーラビリティ**
   - データ増加に対応できるか
   - パーティションサイズは適切か

5. **改善案**
   - より良い設計案はあるか
   - Materialized Viewの活用は?

## 出力フォーマット
{{
  "overall_score": 0-100,
  "partition_key_assessment": {{
    "score": 0-100,
    "issues": ["問題1", "問題2"],
    "recommendations": ["推奨1", "推奨2"]
  }},
  "clustering_key_assessment": {{
    "score": 0-100,
    "issues": [],
    "recommendations": []
  }},
  "access_pattern_alignment": {{
    "score": 0-100,
    "mismatches": ["不整合1"],
    "recommendations": []
  }},
  "scalability_assessment": {{
    "score": 0-100,
    "concerns": ["懸念1"],
    "max_scale_estimate": "推定最大スケール"
  }},
  "hot_partition_risk": {{
    "risk_level": "low/medium/high",
    "reasons": ["理由1"],
    "mitigation": ["対策1"]
  }},
  "alternative_designs": [
    {{
      "approach": "代替案1",
      "schema": "CQLスキーマ",
      "pros": ["メリット1"],
      "cons": ["デメリット1"],
      "migration_effort": "low/medium/high"
    }}
  ]
}}
"""
        
        evaluation = await self.llm.analyze(prompt)
        
        return evaluation
    
    async def evaluate_consistency_level(
        self,
        query: str,
        consistency_level: str,
        business_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Consistency Levelの選択が妥当か評価
        """
        prompt = f"""
CassandraのConsistency Level設定を評価してください。

## クエリ
```cql
{query}
```

## 現在の設定
Consistency Level: {consistency_level}

## ビジネスコンテキスト
{json.dumps(business_context, indent=2, ensure_ascii=False)}

## 評価タスク
1. このConsistency Levelは要件に適しているか?
2. データ整合性のリスクは?
3. パフォーマンスとのトレードオフは適切か?
4. より良い選択肢はあるか?

特に以下を考慮してください:
- Replication Factor (通常3)
- Read + Write > RF の原則
- レイテンシ要件
- データの重要度

## 出力フォーマット
{{
  "is_appropriate": true/false,
  "confidence": 0.0-1.0,
  "risk_assessment": {{
    "data_loss_risk": "none/low/medium/high",
    "inconsistency_risk": "none/low/medium/high",
    "performance_impact": "説明"
  }},
  "reasoning": "判断理由の詳細な説明",
  "recommended_cl": {{
    "read": "ONE/QUORUM/ALL/...",
    "write": "ONE/QUORUM/ALL/...",
    "rationale": "推奨理由"
  }},
  "tradeoffs": {{
    "current": {{"pros": [], "cons": []}},
    "recommended": {{"pros": [], "cons": []}}
  }}
}}
"""
        
        evaluation = await self.llm.analyze(prompt)
        
        return evaluation
    
    async def analyze_query_performance(
        self,
        query: str,
        table_schema: str
    ) -> Dict[str, Any]:
        """
        クエリのパフォーマンスを予測
        """
        prompt = f"""
Cassandraクエリのパフォーマンスを分析してください。

## クエリ
```cql
{query}
```

## テーブルスキーマ
```cql
{table_schema}
```

## 分析タスク
1. このクエリは効率的か?
2. どのくらいのノードがスキャンされるか?
3. ボトルネックは何か?
4. 最適化できるか?

## 出力フォーマット
{{
  "performance_score": 0-100,
  "scan_type": "single_partition/multi_partition/full_cluster",
  "estimated_nodes_scanned": 推定数,
  "bottlenecks": ["ボトルネック1"],
  "optimization_suggestions": [
    {{
      "suggestion": "最適化案1",
      "expected_improvement": "改善見込み",
      "implementation": "実装方法"
    }}
  ],
  "estimated_latency": {{
    "best_case_ms": 数値,
    "typical_ms": 数値,
    "worst_case_ms": 数値
  }}
}}
"""
        
        analysis = await self.llm.analyze(prompt)
        
        return analysis
```

### 3.2 影響範囲説明の自動生成

```python
class ImpactExplainer:
    """
    LLMを使って影響範囲を自然言語で説明
    """
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    async def explain_impact(
        self,
        change_description: str,
        affected_items: List[Dict[str, Any]],
        target_audience: str = "developer"  # developer, manager, executive
    ) -> str:
        """
        変更の影響を説明
        
        target_audience:
        - developer: 技術的な詳細
        - manager: ビジネスへの影響
        - executive: 経営判断に必要な情報
        """
        prompt = f"""
以下のコード変更の影響範囲を{target_audience}向けに説明してください。

## 変更内容
{change_description}

## 影響を受ける箇所
{json.dumps(affected_items, indent=2, ensure_ascii=False)}

## 説明の要件
対象読者: {target_audience}

{"技術的な詳細を含めてください。" if target_audience == "developer" else ""}
{"ビジネスへの影響を中心に説明してください。専門用語は最小限に。" if target_audience == "manager" else ""}
{"経営判断に必要な情報のみを簡潔に。リスクと対応コストを明確に。" if target_audience == "executive" else ""}

## 出力フォーマット
以下の構成で説明してください:

1. 概要 (2-3文)
2. 影響範囲
   - 影響を受けるコンポーネント数
   - 影響を受けるユーザー機能
3. リスク評価
   - データ損失のリスク
   - ダウンタイムのリスク
   - パフォーマンス影響
4. 対応方針
   - 推奨される対応手順
   - 必要な工数見積もり
5. 代替案 (あれば)
"""
        
        explanation = await self.llm.analyze(prompt)
        
        # Markdown形式で整形
        return self._format_explanation(explanation, target_audience)
    
    async def generate_executive_report(
        self,
        analysis_results: List[AnalysisResult],
        time_period: str = "今週"
    ) -> str:
        """
        経営層向けレポートを生成
        """
        # 重要な問題のみを抽出
        critical_issues = [r for r in analysis_results if r.severity == "critical"]
        high_issues = [r for r in analysis_results if r.severity == "high"]
        
        prompt = f"""
コード品質分析の結果を経営層向けにレポートしてください。

## 分析期間
{time_period}

## 検出された問題
### 致命的 (Critical): {len(critical_issues)}件
{self._summarize_issues(critical_issues)}

### 深刻 (High): {len(high_issues)}件
{self._summarize_issues(high_issues)}

## レポート要件
- 専門用語を避け、ビジネスへの影響を明確に
- 数値で示せる指標を使用
- 対応の優先度と必要なリソースを明記
- 1ページ以内に収める

## 出力フォーマット
# コード品質レポート - {time_period}

## エグゼクティブサマリー
[3-4文で全体を要約]

## 主要な発見事項
[ビジネスインパクトの大きい順に3-5項目]

## リスク評価
- データ損失のリスク: [評価]
- システムダウンのリスク: [評価]
- セキュリティリスク: [評価]

## 推奨アクション
1. [最優先事項]
2. [次の優先事項]

## 必要なリソース
- 工数: [見積もり]
- 予算: [必要に応じて]

## 今後の見通し
[対応しない場合のリスク、対応した場合の効果]
"""
        
        report = await self.llm.analyze(prompt)
        
        return report['content']
```

---

## 4. 実装例: Cassandra問題の自動修正

```python
class AutoFixer:
    """
    LLMを使った自動修正機能
    """
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    async def generate_fix_pr(
        self,
        issue: AnalysisResult,
        file_path: str
    ) -> Dict[str, Any]:
        """
        問題を修正するPull Requestを自動生成
        """
        # 元のコードを取得
        original_code = await self._read_file(file_path)
        
        # 修正コードを生成
        fixed_code = await self.llm.generate_fix({
            'description': issue.explanation,
            'original_code': original_code,
            'suggestions': issue.fix_suggestions
        })
        
        # テストコードも生成
        test_code = await self._generate_test_code(fixed_code, issue)
        
        # PR説明文を生成
        pr_description = await self._generate_pr_description(
            issue,
            original_code,
            fixed_code
        )
        
        return {
            'title': f"Fix: {issue.issue_type} in {file_path}",
            'description': pr_description,
            'changes': {
                file_path: fixed_code,
                f"test/{file_path}": test_code
            },
            'labels': [issue.severity, 'auto-generated'],
            'reviewers': self._suggest_reviewers(file_path)
        }
    
    async def _generate_test_code(
        self,
        fixed_code: str,
        issue: AnalysisResult
    ) -> str:
        """
        修正に対応するテストコードを生成
        """
        prompt = f"""
以下の修正に対するテストコードを生成してください。

## 修正後のコード
```
{fixed_code}
```

## 修正内容
{issue.explanation}

## 要件
- 修正前の問題が再発しないことを確認するテスト
- エッジケースもカバー
- JUnit 5を使用
- モック使用時はMockitoを使用

完全なテストクラスを出力してください。
"""
        
        response = await self.llm.analyze(prompt)
        
        return response.get('test_code', '')
    
    async def _generate_pr_description(
        self,
        issue: AnalysisResult,
        original_code: str,
        fixed_code: str
    ) -> str:
        """
        PR説明文を生成
        """
        prompt = f"""
以下のコード修正に対するPull Request説明文を生成してください。

## 問題
{issue.explanation}

## 修正内容
[diffを表示]

## 要件
- 問題の説明
- 修正方針
- テスト方法
- レビューポイント
- 関連Issue

Markdown形式で出力してください。
"""
        
        response = await self.llm.analyze(prompt)
        
        return response.get('pr_description', '')
```

---

## 5. コスト最適化戦略

### 5.1 LLM使用のコスト管理

```python
class CostOptimizer:
    """
    LLM使用コストを最適化
    """
    
    def __init__(self):
        self.cache = {}  # 結果キャッシュ
        self.cost_tracker = {}
        
    async def analyze_with_budget(
        self,
        file_path: str,
        max_cost_usd: float = 0.10
    ) -> AnalysisResult:
        """
        コスト上限内で分析
        """
        # キャッシュチェック
        file_hash = self._compute_file_hash(file_path)
        if file_hash in self.cache:
            return self.cache[file_hash]
        
        # コスト見積もり
        estimated_cost = self._estimate_cost(file_path)
        
        if estimated_cost > max_cost_usd:
            # コストが高すぎる場合は静的解析のみ
            return await self._static_analysis_only(file_path)
        
        # LLM分析を実行
        result = await self._full_analysis(file_path)
        
        # 結果をキャッシュ
        self.cache[file_hash] = result
        
        # コストを記録
        self._track_cost(file_path, estimated_cost)
        
        return result
    
    def _estimate_cost(self, file_path: str) -> float:
        """
        分析コストを見積もり
        
        Claude Sonnet 4.5の料金 (2025年推定):
        - Input: $3 per million tokens
        - Output: $15 per million tokens
        """
        file_size = os.path.getsize(file_path)
        
        # トークン数を推定 (1文字 ≒ 0.5トークン)
        estimated_tokens = file_size * 0.5
        
        # コンテキスト収集で追加のトークン
        context_tokens = estimated_tokens * 2  # 依存ファイルなど
        
        # 入力トークン
        input_tokens = estimated_tokens + context_tokens
        input_cost = (input_tokens / 1_000_000) * 3
        
        # 出力トークン (通常は入力の1/4程度)
        output_tokens = input_tokens / 4
        output_cost = (output_tokens / 1_000_000) * 15
        
        total_cost = input_cost + output_cost
        
        return total_cost
    
    def get_cost_report(self, time_period: str = "today") -> Dict[str, Any]:
        """
        コストレポートを生成
        """
        return {
            'total_cost': sum(self.cost_tracker.values()),
            'analyses_count': len(self.cost_tracker),
            'average_cost_per_analysis': sum(self.cost_tracker.values()) / len(self.cost_tracker),
            'breakdown': self.cost_tracker
        }
```

### 5.2 段階的LLM使用戦略

```python
class TieredAnalysisStrategy:
    """
    ファイルの重要度に応じてLLM使用を調整
    """
    
    def determine_analysis_tier(self, file_path: str) -> str:
        """
        分析レベルを決定
        
        Tier 1 (静的解析のみ): テストコード、設定ファイル
        Tier 2 (条件付きLLM): 一般的なビジネスロジック
        Tier 3 (フルLLM): 重要なデータアクセス層、決済処理等
        """
        # DAO/Repositoryレイヤー
        if any(pattern in file_path for pattern in ['dao', 'repository', 'cassandra']):
            return 'tier3'
        
        # テストコード
        if 'test' in file_path.lower():
            return 'tier1'
        
        # 設定ファイル
        if file_path.endswith(('.yml', '.xml', '.properties')):
            return 'tier1'
        
        # コアビジネスロジック
        if any(pattern in file_path for pattern in ['service', 'controller', 'processor']):
            return 'tier2'
        
        return 'tier2'
```

---

## 6. 実装ロードマップ

### Week 1-2: LLM統合基盤
- [ ] LLMクライアント実装 (Claude Sonnet 4.5)
- [ ] プロンプトテンプレート作成
- [ ] JSON応答パーサー
- [ ] エラーハンドリング

### Week 3-4: ハイブリッド分析エンジン
- [ ] 静的解析との統合
- [ ] 信頼度計算ロジック
- [ ] 結果統合アルゴリズム
- [ ] キャッシュ機構

### Week 5-6: Cassandra特化機能
- [ ] データモデル評価
- [ ] Consistency Level分析
- [ ] クエリパフォーマンス予測
- [ ] 修正案生成

### Week 7-8: 自動修正・レポート
- [ ] 自動修正機能
- [ ] テストコード生成
- [ ] 経営層レポート生成
- [ ] PR自動作成

### Week 9-10: UI統合・最適化
- [ ] ダッシュボードへのLLM分析統合
- [ ] コスト最適化
- [ ] パフォーマンスチューニング
- [ ] ユーザーフィードバック収集

---

## 7. 成功指標

| 指標 | 目標 | 測定方法 |
|-----|------|---------|
| 検出精度 (Precision) | > 90% | 手動レビューとの比較 |
| 検出率 (Recall) | > 85% | 既知のバグ検出率 |
| 誤検出率 | < 10% | False Positive率 |
| LLM同意率 | > 80% | 静的解析とLLMの一致率 |
| 修正提案の採用率 | > 60% | 開発者が採用した割合 |
| コスト効率 | < $0.05/file | 1ファイルあたりの平均コスト |

---

## 8. 次のステップ

### 即座に必要な情報

1. **LLMの選択**
   - Claude Sonnet 4.5を第一候補としますか?
   - GPT-5 Codexも併用しますか?
   - APIキーの準備状況は?

2. **予算**
   - LLM使用の月間予算は?
   - 1ファイルあたりいくらまで許容できますか?

3. **優先順位**
   - まずCassandra特化から始めますか?
   - それとも汎用的な機能から?

4. **人間レビューのワークフロー**
   - 低信頼度の結果をどのように人間がレビューしますか?
   - レビュー担当者は誰ですか?

### プロトタイプ提案

**2週間プロトタイプ**:
- Claude Sonnet 4.5統合
- 10-20ファイルのCassandraコード分析
- 問題検出 + 修正提案生成
- コスト計測

このアプローチでよろしいでしょうか?

---

**本仕様書のバージョン**: v2.0 (LLM Integrated Hybrid System)  
**最終更新日**: 2025年10月26日
