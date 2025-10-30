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
