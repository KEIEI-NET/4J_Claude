"""
Tests for LLM Response Parser

LLMResponseParserクラスの包括的テストスイート
"""

import pytest
from unittest.mock import Mock

from multidb_analyzer.core.base_detector import Issue, Severity, IssueCategory
from multidb_analyzer.llm.response_parser import (
    LLMResponseParser,
    LLMResponseValidator
)


@pytest.fixture
def parser():
    """パーサーインスタンス"""
    return LLMResponseParser()


@pytest.fixture
def sample_issue():
    """サンプルIssue"""
    return Issue(
        detector_name="TestDetector",
        severity=Severity.HIGH,
        category=IssueCategory.PERFORMANCE,
        title="Test Issue",
        description="Test description",
        file_path="test.java",
        line_number=10,
        query_text="SELECT * FROM test",
        suggestion="Use specific columns",
        metadata={'original_key': 'original_value'}
    )


@pytest.fixture
def sample_response():
    """サンプルLLMレスポンス"""
    return """### 1. 問題の詳細説明

このクエリはSELECT *を使用しており、不要なカラムまで取得しています。
これにより、ネットワーク転送量が増加し、パフォーマンスが低下します。

### 2. 修正提案

1. 必要なカラムのみを明示的に指定する
2. インデックスを活用できるようクエリを最適化する
3. LIMIT句を追加してデータ量を制限する

### 3. 修正後のコード

```java
// 修正後: 必要なカラムのみ取得
String query = "SELECT id, name, email FROM test WHERE id = ?";
PreparedStatement stmt = conn.prepareStatement(query);
stmt.setInt(1, userId);
```

### 4. ベストプラクティス

- 常に必要なカラムのみを SELECT する
- PreparedStatement を使用してSQLインジェクションを防ぐ
- インデックスを活用できるWHERE句を記述する

### 5. 参考資料

- https://docs.oracle.com/javase/tutorial/jdbc/
- https://www.postgresql.org/docs/current/sql-select.html
"""


@pytest.fixture
def batch_response():
    """バッチレスポンス"""
    return """## 問題 #1

### 1. 問題の詳細説明
Issue 1 description

### 2. 修正提案
1. Fix step 1
2. Fix step 2

---

## 問題 #2

### 1. 問題の詳細説明
Issue 2 description

### 2. 修正提案
- Fix step A
- Fix step B
"""


class TestLLMResponseParser:
    """LLMResponseParser tests"""

    def test_extract_section_with_triple_hash(self, parser):
        """### ヘッダーの抽出"""
        response = "### 問題の詳細説明\nThis is the description\n### Next Section"

        result = parser._extract_section(response, "問題の詳細説明")

        assert result == "This is the description"

    def test_extract_section_with_double_hash(self, parser):
        """## ヘッダーの抽出"""
        response = "## 問題の詳細説明\nThis is the description\n## Next Section"

        result = parser._extract_section(response, "問題の詳細説明")

        assert result == "This is the description"

    def test_extract_section_with_bold(self, parser):
        """太字ヘッダーの抽出"""
        response = "**問題の詳細説明**\nThis is the description\n**Next Section**"

        result = parser._extract_section(response, "問題の詳細説明")

        assert result == "This is the description"

    def test_extract_section_with_numbers(self, parser):
        """番号付きヘッダーの抽出"""
        response = "### 1. 問題の詳細説明\nThis is the description\n### 2. Next"

        result = parser._extract_section(response, "問題の詳細説明")

        assert result == "This is the description"

    def test_extract_section_with_alternative_header(self, parser):
        """代替ヘッダーでの抽出"""
        response = "### 詳細説明\nThis is the description"

        result = parser._extract_section(response, "問題の詳細説明", "詳細説明")

        assert result == "This is the description"

    def test_extract_section_removes_code_blocks(self, parser):
        """コードブロック除去のテスト"""
        response = """### 問題の詳細説明
Text before code
```java
Code here
```
Text after code
### Next Section"""

        result = parser._extract_section(response, "問題の詳細説明")

        assert "Text before code" in result
        assert "Text after code" in result
        assert "Code here" not in result

    def test_extract_section_not_found(self, parser):
        """セクションが見つからない場合"""
        response = "### Other Section\nContent"

        result = parser._extract_section(response, "Non-existent Section")

        assert result == ""

    def test_extract_fix_steps_numbered(self, parser):
        """番号付きリストの抽出"""
        response = """### 修正提案
1. First step
2. Second step
3. Third step
"""

        result = parser._extract_fix_steps(response)

        assert len(result) == 3
        assert result[0] == "First step"
        assert result[1] == "Second step"
        assert result[2] == "Third step"

    def test_extract_fix_steps_bulleted(self, parser):
        """箇条書きリストの抽出"""
        response = """### 修正提案
- First step
- Second step
* Third step
"""

        result = parser._extract_fix_steps(response)

        assert len(result) == 3
        assert "First step" in result
        assert "Second step" in result
        assert "Third step" in result

    def test_extract_fix_steps_alternative_header(self, parser):
        """代替ヘッダーでの抽出"""
        response = """### 修正手順
1. Step one
2. Step two
"""

        result = parser._extract_fix_steps(response)

        assert len(result) == 2
        assert result[0] == "Step one"

    def test_extract_fix_steps_empty(self, parser):
        """ステップがない場合"""
        response = "### Other Section\nNo steps here"

        result = parser._extract_fix_steps(response)

        assert result == []

    def test_extract_code_snippet_with_language(self, parser):
        """言語指定付きコードブロックの抽出"""
        response = """### 修正後のコード
```java
String query = "SELECT id FROM test";
PreparedStatement stmt = conn.prepareStatement(query);
```
"""

        result = parser._extract_code_snippet(response, "修正後のコード")

        assert "SELECT id FROM test" in result
        assert "PreparedStatement" in result

    def test_extract_code_snippet_without_language(self, parser):
        """言語指定なしコードブロックの抽出"""
        response = """### 修正後のコード
```
code line 1
code line 2
```
"""

        result = parser._extract_code_snippet(response, "修正後のコード")

        assert "code line 1" in result
        assert "code line 2" in result

    def test_extract_code_snippet_multiple_blocks(self, parser):
        """複数コードブロックから最長を抽出"""
        response = """
```
short
```

### 修正後のコード
```java
This is a much longer
code block that should
be extracted as the result
```

```
also short
```
"""

        result = parser._extract_code_snippet(response, "修正後のコード")

        assert "much longer" in result
        assert "extracted as the result" in result

    def test_extract_code_snippet_not_found(self, parser):
        """コードブロックがない場合"""
        response = "### 修正後のコード\nNo code block here"

        result = parser._extract_code_snippet(response, "修正後のコード")

        assert result is None

    def test_extract_references_from_section(self, parser):
        """セクションからURL抽出"""
        response = """### 参考資料
- https://docs.oracle.com/javase/tutorial/
- https://www.postgresql.org/docs/
- https://github.com/example/repo
"""

        result = parser._extract_references(response)

        assert len(result) == 3
        assert "https://docs.oracle.com/javase/tutorial/" in result
        assert "https://www.postgresql.org/docs/" in result
        assert "https://github.com/example/repo" in result

    def test_extract_references_duplicates_removed(self, parser):
        """重複URL削除のテスト"""
        response = """
https://example.com/doc1
https://example.com/doc2
https://example.com/doc1
"""

        result = parser._extract_references(response)

        assert len(result) == 2
        assert result.count("https://example.com/doc1") == 1

    def test_extract_references_from_full_response(self, parser):
        """レスポンス全体からURL抽出"""
        response = """
Some text with a URL: https://example.com/resource
More content
"""

        result = parser._extract_references(response)

        assert "https://example.com/resource" in result

    def test_extract_references_empty(self, parser):
        """URLがない場合"""
        response = "No URLs in this response"

        result = parser._extract_references(response)

        assert result == []

    def test_split_batch_response_with_dashes(self, parser):
        """--- 区切りでの分割"""
        response = """Issue 1 content
---
Issue 2 content
---
Issue 3 content"""

        result = parser._split_batch_response(response)

        assert len(result) == 3
        assert "Issue 1 content" in result[0]
        assert "Issue 2 content" in result[1]
        assert "Issue 3 content" in result[2]

    def test_split_batch_response_with_headers(self, parser):
        """## 問題 #N での分割"""
        response = """## 問題 #1
Content 1
## 問題 #2
Content 2"""

        result = parser._split_batch_response(response)

        assert len(result) == 2
        assert "Content 1" in result[0]
        assert "Content 2" in result[1]

    def test_format_suggestion_single_step(self, parser):
        """単一ステップのフォーマット"""
        steps = ["Single fix step"]

        result = parser._format_suggestion(steps)

        assert result == "Single fix step"

    def test_format_suggestion_multiple_steps(self, parser):
        """複数ステップのフォーマット"""
        steps = ["Step 1", "Step 2", "Step 3"]

        result = parser._format_suggestion(steps)

        assert "1. Step 1" in result
        assert "2. Step 2" in result
        assert "3. Step 3" in result

    def test_format_suggestion_empty(self, parser):
        """空ステップのフォーマット"""
        steps = []

        result = parser._format_suggestion(steps)

        assert result == ""

    def test_parse_analysis_full_response(self, parser, sample_issue, sample_response):
        """完全なレスポンス解析"""
        result = parser.parse_analysis(sample_response, sample_issue)

        # 元のIssue情報保持
        assert result.title == sample_issue.title
        assert result.severity == sample_issue.severity
        assert result.file_path == sample_issue.file_path
        assert result.line_number == sample_issue.line_number

        # LLM拡張情報追加
        assert 'llm_detailed_description' in result.metadata
        assert 'llm_fix_steps' in result.metadata
        assert 'llm_best_practices' in result.metadata
        assert 'llm_references' in result.metadata

        # 詳細説明
        assert "SELECT *を使用" in result.metadata['llm_detailed_description']

        # 修正ステップ
        assert len(result.metadata['llm_fix_steps']) == 3
        assert "必要なカラムのみ" in result.metadata['llm_fix_steps'][0]

        # 修正コード
        assert result.auto_fix_available is True
        assert "SELECT id, name, email" in result.auto_fix_code

        # 参考資料
        assert len(result.metadata['llm_references']) == 2
        assert any('oracle.com' in url for url in result.metadata['llm_references'])

        # ベストプラクティス
        assert "PreparedStatement" in result.metadata['llm_best_practices']

        # 元のメタデータ保持
        assert result.metadata['original_key'] == 'original_value'

    def test_parse_analysis_partial_response(self, parser, sample_issue):
        """部分的なレスポンス解析"""
        partial_response = """### 1. 問題の詳細説明
Partial description

### 2. 修正提案
1. Only one step
"""

        result = parser.parse_analysis(partial_response, sample_issue)

        assert result.metadata['llm_detailed_description'] == "Partial description"
        assert len(result.metadata['llm_fix_steps']) == 1
        assert result.auto_fix_available is False  # No code
        assert result.metadata['llm_references'] == []

    def test_parse_batch_response(self, parser, batch_response):
        """バッチレスポンス解析"""
        issues = [
            Issue(
                detector_name="Test",
                severity=Severity.HIGH,
                category=IssueCategory.PERFORMANCE,
                title=f"Issue {i}",
                description=f"Description {i}",
                file_path=f"test{i}.java",
                line_number=i * 10,
                query_text="",
                metadata={}
            )
            for i in range(1, 3)
        ]

        result = parser.parse_batch_response(batch_response, issues)

        assert len(result) == 2
        assert all(isinstance(issue, Issue) for issue in result)

    def test_parse_batch_response_error_handling(self, parser, sample_issue):
        """バッチ解析エラーハンドリング"""
        # 不正なレスポンス
        bad_response = "Malformed response"

        issues = [sample_issue]

        result = parser.parse_batch_response(bad_response, issues)

        # エラー時は元のIssueを返却（メタデータにLLMフィールドが追加されることは許容）
        assert len(result) == 1

        # 主要属性が同じことを確認（detected_atとmetadataの詳細は除く）
        assert result[0].detector_name == sample_issue.detector_name
        assert result[0].severity == sample_issue.severity
        assert result[0].category == sample_issue.category
        assert result[0].title == sample_issue.title
        assert result[0].description == sample_issue.description
        assert result[0].file_path == sample_issue.file_path
        assert result[0].line_number == sample_issue.line_number
        assert result[0].query_text == sample_issue.query_text

        # 元のメタデータキーが保持されていることを確認
        assert 'original_key' in result[0].metadata
        assert result[0].metadata['original_key'] == sample_issue.metadata['original_key']


class TestLLMResponseValidator:
    """LLMResponseValidator tests"""

    def test_validate_response_valid(self):
        """有効なレスポンスの検証"""
        response = """### 1. 問題の詳細説明
Description here

### 2. 修正提案
Fix steps here
"""

        result = LLMResponseValidator.validate_response(response)

        assert result is True

    def test_validate_response_too_short(self):
        """短すぎるレスポンス"""
        response = "Too short"

        result = LLMResponseValidator.validate_response(response)

        assert result is False

    def test_validate_response_empty(self):
        """空レスポンス"""
        result = LLMResponseValidator.validate_response("")

        assert result is False

    def test_validate_response_missing_sections(self):
        """必須セクション欠如"""
        response = """### 1. 問題の詳細説明
Only description, no fix section
""" + "x" * 50  # 最小長を満たすために追加

        result = LLMResponseValidator.validate_response(response)

        assert result is False

    def test_extract_confidence_explicit(self):
        """明示的な信頼度抽出"""
        response = "信頼度: 95%"

        result = LLMResponseValidator.extract_confidence(response)

        assert result == 0.95

    def test_extract_confidence_with_colon(self):
        """全角コロンでの信頼度抽出"""
        response = "信頼度:80%"

        result = LLMResponseValidator.extract_confidence(response)

        assert result == 0.80

    def test_extract_confidence_default(self):
        """デフォルト信頼度"""
        response = "No confidence mentioned"

        result = LLMResponseValidator.extract_confidence(response)

        assert result == 0.85
