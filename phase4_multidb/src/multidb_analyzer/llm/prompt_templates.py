"""
Prompt Templates for LLM Optimization

LLM最適化のためのプロンプトテンプレート集。
データベース特化の最適化提案を生成します。
"""

from typing import Dict, Any, List
from multidb_analyzer.core.base_detector import Issue, Severity


class PromptTemplates:
    """LLM最適化用プロンプトテンプレート"""

    # システムプロンプト
    SYSTEM_PROMPT = """You are an expert database performance consultant specializing in code optimization.

Your role is to:
1. Analyze database query patterns and identify performance issues
2. Provide specific, actionable optimization recommendations
3. Explain the technical rationale behind each suggestion
4. Generate production-ready code examples when possible

Guidelines:
- Be concise and technical
- Focus on measurable performance improvements
- Consider scalability and maintainability
- Provide code examples in the same language as the original
- Explain trade-offs when applicable"""

    # Elasticsearch最適化プロンプト
    ELASTICSEARCH_OPTIMIZATION = """Analyze this Elasticsearch query issue and provide optimization recommendations.

## Issue Details
**Severity**: {severity}
**Category**: {category}
**Title**: {title}
**Description**: {description}

## Original Code
```{language}
{code}
```

**File**: {file_path}:{line_number}
**Method**: {method_name}
**Class**: {class_name}

## Current Suggestion
{current_suggestion}

## Request
Provide a detailed optimization plan including:

1. **Root Cause Analysis**: Explain WHY this is a problem
2. **Performance Impact**: Quantify the expected impact (e.g., query time reduction)
3. **Optimized Code**: Provide production-ready replacement code
4. **Implementation Steps**: Step-by-step migration guide
5. **Testing Strategy**: How to verify the optimization
6. **Trade-offs**: Any considerations or limitations

Format your response as structured JSON:
```json
{{
  "root_cause": "...",
  "performance_impact": "...",
  "optimized_code": "...",
  "implementation_steps": ["...", "..."],
  "testing_strategy": "...",
  "trade_offs": "...",
  "confidence_score": 0.0-1.0
}}
```"""

    # 複数問題の優先度付けプロンプト
    PRIORITIZE_ISSUES = """Analyze these {count} database performance issues and provide prioritization recommendations.

## Issues

{issues_summary}

## Request
Prioritize these issues based on:
1. Performance impact (estimated query time improvement)
2. Implementation difficulty (LOW/MEDIUM/HIGH)
3. Risk level (potential for breaking changes)
4. Business value (user-facing vs internal)

Provide your analysis as JSON:
```json
{{
  "prioritized_issues": [
    {{
      "issue_id": 1,
      "priority_score": 0.0-10.0,
      "estimated_impact": "...",
      "implementation_difficulty": "LOW|MEDIUM|HIGH",
      "risk_level": "LOW|MEDIUM|HIGH",
      "recommended_order": 1,
      "rationale": "..."
    }}
  ],
  "quick_wins": ["...", "..."],
  "high_risk_high_reward": ["...", "..."],
  "technical_debt": ["...", "..."]
}}
```"""

    # コード品質レビュープロンプト
    CODE_REVIEW = """Review this database access code for best practices and potential issues.

## Code
```{language}
{code}
```

## Context
- **Database**: {db_type}
- **File**: {file_path}
- **Purpose**: {purpose}

## Request
Provide a comprehensive code review covering:

1. **Performance**: Query optimization opportunities
2. **Security**: SQL injection risks, data exposure
3. **Reliability**: Error handling, connection management
4. **Maintainability**: Code clarity, documentation
5. **Best Practices**: Framework-specific recommendations

Format as JSON:
```json
{{
  "overall_score": 0-100,
  "issues": [
    {{
      "category": "performance|security|reliability|maintainability",
      "severity": "critical|high|medium|low",
      "description": "...",
      "recommendation": "...",
      "code_example": "..."
    }}
  ],
  "positive_aspects": ["...", "..."],
  "summary": "..."
}}
```"""

    # 自動修正コード生成プロンプト
    AUTO_FIX_GENERATION = """Generate production-ready code to fix this database query issue.

## Issue
**Problem**: {title}
**Description**: {description}

## Original Code
```{language}
{code}
```

## Context
- **Database**: {db_type}
- **Framework**: {framework}
- **Language**: {language}

## Requirements
1. Maintain exact functionality
2. Preserve variable names and structure
3. Add inline comments explaining changes
4. Follow {language} best practices
5. Ensure backward compatibility

## Request
Generate the optimized code with:
- Clear inline comments
- Error handling if needed
- Performance improvements
- Same indentation style

```{language}
// Your optimized code here
```

Also provide:
- **Confidence**: 0.0-1.0 (how confident you are this fix is safe)
- **Breaking Changes**: Yes/No and explanation
- **Migration Notes**: Any special considerations"""

    @staticmethod
    def format_elasticsearch_optimization(
        issue: Issue,
        code: str,
        language: str = "java"
    ) -> str:
        """
        Elasticsearch最適化プロンプトをフォーマット

        Args:
            issue: 問題情報
            code: 元のコード
            language: プログラミング言語

        Returns:
            フォーマット済みプロンプト
        """
        return PromptTemplates.ELASTICSEARCH_OPTIMIZATION.format(
            severity=issue.severity.value,
            category=issue.category.value if issue.category else "PERFORMANCE",
            title=issue.title,
            description=issue.description,
            language=language,
            code=code,
            file_path=issue.file_path,
            line_number=issue.line_number,
            method_name=issue.method_name or "unknown",
            class_name=issue.class_name or "unknown",
            current_suggestion=issue.suggestion
        )

    @staticmethod
    def format_prioritize_issues(issues: List[Issue]) -> str:
        """
        問題優先度付けプロンプトをフォーマット

        Args:
            issues: 問題のリスト

        Returns:
            フォーマット済みプロンプト
        """
        issues_summary = "\n\n".join([
            f"### Issue {i + 1}\n"
            f"**Severity**: {issue.severity.value}\n"
            f"**Title**: {issue.title}\n"
            f"**File**: {issue.file_path}:{issue.line_number}\n"
            f"**Description**: {issue.description}\n"
            f"**Suggestion**: {issue.suggestion}"
            for i, issue in enumerate(issues)
        ])

        return PromptTemplates.PRIORITIZE_ISSUES.format(
            count=len(issues),
            issues_summary=issues_summary
        )

    @staticmethod
    def format_code_review(
        code: str,
        db_type: str,
        file_path: str,
        language: str = "java",
        purpose: str = "Database query execution"
    ) -> str:
        """
        コードレビュープロンプトをフォーマット

        Args:
            code: レビュー対象のコード
            db_type: データベースタイプ
            file_path: ファイルパス
            language: プログラミング言語
            purpose: コードの目的

        Returns:
            フォーマット済みプロンプト
        """
        return PromptTemplates.CODE_REVIEW.format(
            language=language,
            code=code,
            db_type=db_type,
            file_path=file_path,
            purpose=purpose
        )

    @staticmethod
    def format_auto_fix(
        issue: Issue,
        code: str,
        db_type: str,
        framework: str = "Spring Data",
        language: str = "java"
    ) -> str:
        """
        自動修正コード生成プロンプトをフォーマット

        Args:
            issue: 問題情報
            code: 元のコード
            db_type: データベースタイプ
            framework: 使用フレームワーク
            language: プログラミング言語

        Returns:
            フォーマット済みプロンプト
        """
        return PromptTemplates.AUTO_FIX_GENERATION.format(
            title=issue.title,
            description=issue.description,
            language=language,
            code=code,
            db_type=db_type,
            framework=framework
        )
<<<<<<< HEAD
=======


class PromptBuilder:
    """
    LLM分析用プロンプトビルダー

    Phase 6-6で使用する統合プロンプト生成クラス
    """

    ISSUE_ANALYSIS_TEMPLATE = """あなたはデータベース最適化の専門家です。以下の問題を分析してください。

## 問題情報
- **タイトル**: {title}
- **重大度**: {severity}
- **カテゴリ**: {category}
- **検出器**: {detector_name}
- **ファイル**: {file_path}:{line_number}

## 検出されたクエリ
```sql
{query_text}
```

## 周辺コード
```{language}
{context_code}
```

## 現在の提案
{current_suggestion}

---

## 分析依頼

以下の形式で詳細な分析結果を返してください：

### 1. 問題の詳細説明
（なぜこれが問題なのか、どのような影響があるか、技術的な背景）

### 2. 修正提案
1. （具体的な修正ステップ1）
2. （具体的な修正ステップ2）
3. （具体的な修正ステップ3）

### 3. 修正後のコード
```{language}
// 修正されたコード（コメント付き）
```

### 4. ベストプラクティス
（関連する業界標準、推奨事項、注意点）

### 5. 参考資料
- （公式ドキュメントURL）
- （参考記事URL）

---

**重要**: 具体的で実装可能な提案をお願いします。
"""

    BATCH_ANALYSIS_TEMPLATE = """以下の{count}件のデータベース問題を分析してください。

{issues_list}

---

各問題について、以下の形式で分析結果を返してください：

---
## 問題 #{{issue_number}}

### 1. 詳細説明
...

### 2. 修正提案
1. ...
2. ...

### 3. 修正コード
```{{language}}
...
```

### 4. ベストプラクティス
...

### 5. 参考資料
...

---

**重要**:
- 各問題の分析を明確に分離してください
- 具体的で実装可能な提案を優先してください
"""

    def build_issue_analysis_prompt(
        self,
        issue: Issue,
        context_code: str = "",
        language: str = "java"
    ) -> str:
        """
        単一問題分析プロンプトを生成

        Args:
            issue: 問題
            context_code: 周辺コード
            language: プログラミング言語

        Returns:
            プロンプト文字列
        """
        return self.ISSUE_ANALYSIS_TEMPLATE.format(
            title=issue.title,
            severity=issue.severity.value,
            category=issue.category.value if issue.category else "PERFORMANCE",
            detector_name=issue.detector_name,
            file_path=issue.file_path,
            line_number=issue.line_number,
            query_text=issue.query_text or "(クエリテキストなし)",
            context_code=context_code or "(コンテキストなし)",
            current_suggestion=issue.suggestion or "(提案なし)",
            language=language
        )

    def build_batch_analysis_prompt(
        self,
        issues: List[Issue],
        language: str = "java"
    ) -> str:
        """
        バッチ分析プロンプトを生成

        Args:
            issues: 問題リスト
            language: プログラミング言語

        Returns:
            プロンプト文字列
        """
        issues_list = "\n\n".join([
            self._format_issue_for_batch(i + 1, issue, language)
            for i, issue in enumerate(issues)
        ])

        return self.BATCH_ANALYSIS_TEMPLATE.format(
            count=len(issues),
            issues_list=issues_list,
            language=language
        )

    def _format_issue_for_batch(
        self,
        issue_number: int,
        issue: Issue,
        language: str = "java"
    ) -> str:
        """
        バッチ用に問題を整形

        Args:
            issue_number: 問題番号
            issue: 問題
            language: プログラミング言語

        Returns:
            整形された問題情報
        """
        return f"""## 問題 #{issue_number}
- **タイトル**: {issue.title}
- **重大度**: {issue.severity.value}
- **ファイル**: {issue.file_path}:{issue.line_number}
- **検出器**: {issue.detector_name}

**クエリ**:
```sql
{issue.query_text or "(なし)"}
```

**説明**: {issue.description}
"""
>>>>>>> 7f5798be (fix(phase6-6): Complete LLM integration test fixes (506/506 tests pass))
