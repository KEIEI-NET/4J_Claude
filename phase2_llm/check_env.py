"""
環境変数設定確認スクリプト

.envファイルが正しく設定されているか確認します。
APIを実際に呼び出すことはありません。
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# Windows console encoding fix
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# .envファイルを読み込み（ルートディレクトリから）
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

print("🔍 環境変数設定確認")
print(f"   .envファイルパス: {env_path.absolute()}")

# .envファイルの存在確認
if not env_path.exists():
    print("❌ エラー: .envファイルが見つかりません")
    print(f"   期待される場所: {env_path.absolute()}")
    exit(1)

print("✅ .envファイルが見つかりました")

# APIキーの確認
api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    print("❌ エラー: ANTHROPIC_API_KEYが設定されていません")
    print("\n   .envファイルに以下の形式で追加してください:")
    print("   ANTHROPIC_API_KEY=sk-ant-...")
    exit(1)

if api_key == "your-api-key-here":
    print("❌ エラー: ANTHROPIC_API_KEYがデフォルト値のままです")
    print("\n   .envファイルを編集して、実際のAPIキーに置き換えてください:")
    print("   ANTHROPIC_API_KEY=sk-ant-...")
    exit(1)

if not api_key.startswith("sk-ant-"):
    print("⚠️  警告: APIキーの形式が正しくない可能性があります")
    print(f"   取得した値: {api_key[:20]}...")
    print("   Anthropic APIキーは通常 'sk-ant-' で始まります")

# 成功
print("✅ ANTHROPIC_API_KEYが設定されています")
print(f"   APIキー: {api_key[:20]}...{api_key[-4:]}")
print("\n🎉 設定完了！以下のコマンドでLLM統合テストを実行できます:")
print("   python test_real_llm_integration.py")
