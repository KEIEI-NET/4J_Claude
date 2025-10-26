# LLM統合テスト実行手順

このドキュメントでは、実際のAnthropic APIを使用してLLM統合をテストする方法を説明します。

## 前提条件

- Python 3.11以上がインストールされていること
- Anthropic API キーを取得していること（https://console.anthropic.com/）
- Phase 1とPhase 2の依存関係がインストールされていること

## セットアップ手順

### 1. API キーの設定

`.env`ファイルにAnthropic API キーを設定します：

```bash
# .envファイルを編集
cd phase2_llm
notepad .env  # または任意のエディタ
```

`.env`ファイルの内容：
```
ANTHROPIC_API_KEY=sk-ant-あなたのAPIキーをここに入力
```

⚠️ **重要**: `.env`ファイルは`.gitignore`に登録されているため、Gitリポジトリにコミットされません。

### 2. 依存関係のインストール

```bash
# python-dotenvがインストールされていることを確認
pip install python-dotenv

# Phase 2の依存関係をインストール
pip install -e .
```

## テスト実行

### 基本的な実行方法

```bash
cd phase2_llm
python test_real_llm_integration.py
```

### 期待される動作

スクリプトは以下の3つのモードでテストを実行します：

1. **quickモード**: 静的解析のみ（LLM不使用）
2. **standardモード**: 静的解析 + 高重要度問題のLLM分析
3. **comprehensiveモード**: 静的解析 + 全問題のLLM分析 + LLM独自の意味解析

各モードで以下の情報が表示されます：
- 検出された問題の数
- 各問題の詳細（タイプ、重要度、信頼度）
- 検出元（静的解析/LLM/両方）
- LLM分析結果（該当する場合）
- 統計情報

### 実行例

```
✅ APIキーを読み込みました
   APIキー: sk-ant-api03-1234...

📝 テスト用Javaファイルを作成中...
✅ テストファイル作成完了

🔧 HybridAnalysisEngineを初期化中（LLM有効）...
✅ エンジン初期化完了

============================================================
🚀 モード: quick
============================================================
分析実行中...

📊 検出結果: 2件の問題

--- 問題 1 ---
タイプ: ALLOW_FILTERING_USAGE
重要度: high
信頼度: certain (1.00)
メッセージ: ALLOW FILTERING detected in query
CQL: SELECT * FROM users WHERE email = ? ALLOW FILTERING
検出元: 静的解析

...
```

## トラブルシューティング

### エラー: "ANTHROPIC_API_KEYを設定してください"

`.env`ファイルが正しく設定されていない可能性があります：
- `.env`ファイルが`phase2_llm`ディレクトリに存在するか確認
- APIキーが正しく入力されているか確認（`your-api-key-here`のままになっていないか）

### エラー: "No module named 'dotenv'"

`python-dotenv`がインストールされていません：
```bash
pip install python-dotenv
```

### エラー: "Failed to parse file"

Phase 1のパーサーが正しく動作していない可能性があります：
- Phase 1の依存関係がインストールされているか確認
- Phase 1のパスが正しく設定されているか確認

### APIエラーが発生する場合

- APIキーが有効か確認
- API利用制限に達していないか確認
- インターネット接続を確認

## コスト見積もり

このテストスクリプトは3つのモードで実行され、以下の程度のAPIコールを行います：

- **quickモード**: APIコールなし（無料）
- **standardモード**: 約2回のAPIコール（入力: ~1,000トークン、出力: ~500トークン/回）
- **comprehensiveモード**: 約4-5回のAPIコール（入力: ~1,500トークン、出力: ~1,000トークン/回）

概算コスト（Claude 3.5 Sonnet使用時）：
- 1回の実行: 約 **$0.05-0.10 USD**

## 次のステップ

テストが成功したら、以下を実施できます：

1. **より複雑なJavaコードでテスト**: `test_real_llm_integration.py`のJavaコードを編集
2. **カスタムプロンプトの調整**: `hybrid_analyzer.py`のプロンプトを調整
3. **統計情報の詳細分析**: `get_statistics()`メソッドの出力を確認

## 参考情報

- [Anthropic API Documentation](https://docs.anthropic.com/)
- [Phase 1 Documentation](../phase1_cassandra/README.md)
- [Phase 2 Architecture](./docs/ARCHITECTURE.md)
