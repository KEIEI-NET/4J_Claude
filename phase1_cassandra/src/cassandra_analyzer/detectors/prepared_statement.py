"""
Prepared Statement検証検出器
"""
from typing import List, Dict, Any, Optional

from .base import BaseDetector
from ..models import Issue, CassandraCall
from ..parsers import CQLParser


class PreparedStatementDetector(BaseDetector):
    """
    Prepared Statementの未使用を検出

    繰り返し実行されるクエリでPrepared Statementを使用しないと、
    以下の問題が発生する：
    - パフォーマンス低下（毎回CQLをパースする必要がある）
    - セキュリティリスク（SQL/CQLインジェクションのリスク）
    - サーバー負荷の増加
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Args:
            config: 検出器の設定辞書（オプション）
                    - min_executions: 問題視する最小実行回数（デフォルト: 1）
                                     Phase 1では単純検出のため1を推奨
        """
        super().__init__(config)
        # デフォルト重要度は"low"（Phase 1では検出のみ）
        if "severity" not in self.config:
            self._severity = "low"

        # 最小実行回数（Phase 1では常に検出するため1）
        self.min_executions = self.config.get("min_executions", 1)

        self.cql_parser = CQLParser()

    @property
    def detector_name(self) -> str:
        """検出器の名前"""
        return "PreparedStatementDetector"

    def detect(self, call: CassandraCall) -> List[Issue]:
        """
        Prepared Statementの未使用を検出

        Args:
            call: 分析対象のCassandra呼び出し

        Returns:
            検出された問題のリスト
        """
        issues: List[Issue] = []

        # Prepared Statementが使用されていない場合のみ検出
        if call.is_prepared:
            return issues

        # CQL文字列を解析して追加情報を取得
        try:
            analysis = self.cql_parser.analyze(call.cql_text)
        except Exception as e:
            # 解析エラーの場合でも基本的な問題は報告
            analysis = None

        # 証拠の収集
        evidence = [
            f"Method: {call.method_name}",
            "Prepared Statement: NOT USED",
        ]

        if call.consistency_level:
            evidence.append(f"Consistency Level: {call.consistency_level}")

        if analysis:
            evidence.append(f"Query type: {analysis.query_type.value}")
            if analysis.tables:
                evidence.append(f"Target tables: {', '.join(analysis.tables)}")

        # 文字列リテラルまたは変数の使用を検出
        if '"' in call.cql_text or "'" in call.cql_text:
            evidence.append("String literals detected in CQL (potential injection risk)")

        # 推奨事項の生成
        recommendation = self._generate_recommendation(call, analysis)

        # 重要度の調整（セキュリティリスクがある場合はmediumに）
        severity = self._severity
        if self._has_security_risk(call):
            severity = "medium"

        issue = self._create_issue(
            issue_type="UNPREPARED_STATEMENT",
            call=call,
            message="Prepared Statement not used - performance and security risk",
            recommendation=recommendation,
            severity=severity,
            evidence=evidence,
            confidence=0.95,  # JavaParserの判定に基づくため高い信頼度
        )

        issues.append(issue)

        return issues

    def _has_security_risk(self, call: CassandraCall) -> bool:
        """
        セキュリティリスクがあるかチェック

        Args:
            call: Cassandra呼び出し

        Returns:
            リスクがある場合True
        """
        # 文字列の連結や変数置換の可能性がある場合
        risk_indicators = [
            "+",  # 文字列連結
            "String.format",  # 文字列フォーマット
            "StringBuilder",  # 文字列ビルダー
        ]

        for indicator in risk_indicators:
            if indicator in call.cql_text:
                return True

        return False

    def _generate_recommendation(self, call: CassandraCall, analysis) -> str:
        """
        分析結果に基づいて推奨事項を生成

        Args:
            call: Cassandra呼び出し
            analysis: CQL分析結果（オプション）

        Returns:
            推奨事項の文字列
        """
        recommendations = []

        # 基本的な推奨事項
        recommendations.append(
            "Use Prepared Statements for all parameterized queries to improve performance "
            "and prevent CQL injection attacks."
        )

        # 具体的な修正方法
        recommendations.append(
            "\nHow to fix:"
        )
        recommendations.append(
            "1. Change from:"
        )
        recommendations.append(
            '   session.execute("SELECT * FROM users WHERE id = \'" + userId + "\'");')
        recommendations.append(
            "\n2. To:"
        )
        recommendations.append(
            '   PreparedStatement ps = session.prepare("SELECT * FROM users WHERE id = ?");')
        recommendations.append(
            '   BoundStatement bs = ps.bind(userId);')
        recommendations.append(
            '   session.execute(bs);')

        # パフォーマンスの利点
        recommendations.append(
            "\nBenefits:"
        )
        recommendations.append(
            "- Better performance: Query is parsed only once")
        recommendations.append(
            "- Security: Prevents CQL injection attacks")
        recommendations.append(
            "- Type safety: Parameters are properly typed")
        recommendations.append(
            "- Reusability: Same PreparedStatement can be reused with different values")

        # セキュリティリスクがある場合
        if self._has_security_risk(call):
            recommendations.append(
                "\n⚠️  SECURITY WARNING:"
            )
            recommendations.append(
                "String concatenation detected in CQL - HIGH RISK of CQL injection!"
            )
            recommendations.append(
                "This is a critical security vulnerability that must be fixed immediately."
            )

        return "\n".join(recommendations)
