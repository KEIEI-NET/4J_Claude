"""
Real LLM Integration Test Script

このスクリプトは実際のAnthropic APIを使用してLLM統合をテストします。
.envファイルにANTHROPIC_API_KEYを設定してから実行してください。

使用方法:
    python test_real_llm_integration.py
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# Windows console encoding fix
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 環境変数を読み込み
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Phase 1とPhase 2のパスを追加
phase1_path = Path(__file__).parent.parent / "phase1_cassandra" / "src"
phase2_path = Path(__file__).parent / "src"

if phase1_path.exists():
    sys.path.insert(0, str(phase1_path.resolve()))
if phase2_path.exists():
    sys.path.insert(0, str(phase2_path.resolve()))

from cassandra_analyzer.analyzers.hybrid_analyzer import HybridAnalysisEngine
import tempfile


async def main():
    """メイン実行関数"""

    # APIキーのチェック
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your-api-key-here":
        print("❌ エラー: .envファイルにANTHROPIC_API_KEYを設定してください")
        print("   .envファイルの場所:", env_path.absolute())
        print("\n   .envファイルの内容例:")
        print("   ANTHROPIC_API_KEY=sk-ant-...")
        return 1

    print("✅ APIキーを読み込みました")
    print(f"   APIキー: {api_key[:20]}...")

    # テスト用のJavaコードを作成
    print("\n📝 テスト用Javaファイルを作成中...")
    with tempfile.TemporaryDirectory() as tmpdir:
        java_file = Path(tmpdir) / "TestDAO.java"
        java_content = """
package com.example;

import com.datastax.driver.core.Session;
import com.datastax.driver.core.ResultSet;

public class TestDAO {
    private final Session session;

    // 問題のあるCQLクエリ（ALLOW FILTERINGを使用）
    private static final String FIND_BY_EMAIL_CQL =
        "SELECT * FROM users WHERE email = ? ALLOW FILTERING";

    // パーティションキーなしのクエリ
    private static final String SCAN_ALL_CQL = "SELECT * FROM users";

    public TestDAO(Session session) {
        this.session = session;
    }

    public ResultSet findUserByEmail(String email) {
        // ALLOW FILTERINGは通常パフォーマンス問題の原因となる
        ResultSet rs = session.execute(FIND_BY_EMAIL_CQL, email);
        return rs;
    }

    public ResultSet scanAllUsers() {
        // フルテーブルスキャンは大規模データで問題になる
        session.execute(SCAN_ALL_CQL);
        return null;
    }
}
"""
        java_file.write_text(java_content, encoding="utf-8")
        print(f"✅ テストファイル作成完了: {java_file}")

        # HybridAnalysisEngineを初期化（LLM有効）
        print("\n🔧 HybridAnalysisEngineを初期化中（LLM有効）...")
        engine = HybridAnalysisEngine(
            api_key=api_key,
            enable_llm=True,
            llm_threshold_severity="high"
        )
        print("✅ エンジン初期化完了")

        # 3つのモードでテスト
        modes = ["quick", "standard", "comprehensive"]

        for mode in modes:
            print(f"\n{'='*60}")
            print(f"🚀 モード: {mode}")
            print(f"{'='*60}")

            try:
                print(f"分析実行中...")
                results = await engine.analyze_code(str(java_file), mode)

                print(f"\n📊 検出結果: {len(results)}件の問題")

                for i, result in enumerate(results, 1):
                    print(f"\n--- 問題 {i} ---")
                    print(f"タイプ: {result.issue.issue_type}")
                    print(f"重要度: {result.issue.severity}")
                    print(f"信頼度: {result.confidence_level.value} ({result.confidence_score:.2f})")
                    print(f"メッセージ: {result.issue.message}")
                    print(f"CQL: {result.issue.cql_text}")

                    # 検出ソース
                    sources = []
                    if result.has_static_detection:
                        sources.append("静的解析")
                    if result.has_llm_detection:
                        sources.append("LLM分析")
                    print(f"検出元: {', '.join(sources)}")

                    # LLM分析結果があれば表示
                    if result.llm_analysis:
                        print(f"\n💡 LLM分析:")
                        print(f"   {result.llm_analysis.get('analysis', 'N/A')[:200]}...")

                        fix_suggestions = result.fix_suggestions
                        if fix_suggestions:
                            print(f"\n🔧 修正提案:")
                            for j, suggestion in enumerate(fix_suggestions[:3], 1):
                                print(f"   {j}. {suggestion}")

                # 統計情報
                stats = engine.get_statistics(results)
                print(f"\n📈 統計情報:")
                print(f"   総問題数: {stats['total_issues']}")
                print(f"   静的のみ: {stats['detection_sources']['static_only']}")
                print(f"   LLMのみ: {stats['detection_sources']['llm_only']}")
                print(f"   ハイブリッド: {stats['detection_sources']['hybrid']}")
                print(f"   平均信頼度: {stats['average_confidence_score']:.2f}")

            except Exception as e:
                print(f"❌ エラーが発生しました: {e}")
                import traceback
                traceback.print_exc()
                return 1

    print(f"\n{'='*60}")
    print("✅ すべてのテスト完了")
    print(f"{'='*60}")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
