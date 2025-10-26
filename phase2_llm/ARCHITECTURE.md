# Phase 2: LLM統合アーキテクチャ

*バージョン: v1.0.0*
*最終更新: 2025年01月27日 15:40 JST*

## 📐 システムアーキテクチャ概要

Phase 2では、Phase 1の静的解析システムにLLM（Large Language Model）分析機能を統合し、より高度な問題検出と修正提案を実現しています。

## 🏗️ Phase 2 システムアーキテクチャ図

```mermaid
graph TB
    %% 入力層
    subgraph Input["入力層"]
        JavaCode["Java Source Code<br/>(.java files)"]
        Config["Configuration<br/>(mode, api_key)"]
    end

    %% Phase 1 静的解析層
    subgraph Phase1["Phase 1: 静的解析層"]
        Parser["JavaCassandraParser<br/>AST解析・CQL抽出"]

        subgraph Detectors["検出器群"]
            D1["AllowFilteringDetector"]
            D2["PartitionKeyDetector"]
            D3["BatchSizeDetector"]
            D4["PreparedStatementDetector"]
        end

        Parser --> Detectors
    end

    %% Phase 2 LLM統合層
    subgraph Phase2["Phase 2: LLM統合層"]
        HybridEngine["HybridAnalysisEngine<br/>統合エンジン"]

        subgraph LLMComponents["LLMコンポーネント"]
            LLMClient["AnthropicClient<br/>Claude API"]
            LLMAnalyzer["LLMAnalyzer<br/>分析エンジン"]
            PromptBuilder["Prompt Builder<br/>プロンプト生成"]
        end

        subgraph Models["データモデル"]
            Confidence["AnalysisConfidence<br/>信頼度計算"]
            HybridResult["HybridAnalysisResult<br/>結果統合"]
        end

        HybridEngine --> LLMClient
        LLMClient --> LLMAnalyzer
        LLMAnalyzer --> PromptBuilder
    end

    %% データフロー
    JavaCode --> Parser
    Config --> HybridEngine
    Detectors --> HybridEngine
    LLMAnalyzer --> Confidence
    Confidence --> HybridResult

    %% 出力層
    subgraph Output["出力層"]
        Issues["統合問題リスト<br/>(static + LLM)"]
        Suggestions["修正提案"]
        Metrics["分析メトリクス<br/>(信頼度・コスト)"]
    end

    HybridResult --> Issues
    HybridResult --> Suggestions
    HybridResult --> Metrics

    %% スタイリング
    classDef inputClass fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef phase1Class fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef phase2Class fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef outputClass fill:#fff3e0,stroke:#e65100,stroke-width:2px

    class JavaCode,Config inputClass
    class Parser,D1,D2,D3,D4 phase1Class
    class HybridEngine,LLMClient,LLMAnalyzer,PromptBuilder,Confidence,HybridResult phase2Class
    class Issues,Suggestions,Metrics outputClass
```

## 🔄 ハイブリッド分析フロー図

```mermaid
flowchart LR
    %% 開始
    Start([分析開始]) --> Mode{分析モード?}

    %% モード分岐
    Mode -->|quick| QuickFlow["静的解析のみ実行"]
    Mode -->|standard| StandardFlow["静的解析実行"]
    Mode -->|comprehensive| CompFlow["静的解析実行"]
    Mode -->|critical_only| CriticalFlow["Critical問題のみ<br/>静的解析"]

    %% Quick モード
    QuickFlow --> QuickResult["静的解析結果"]
    QuickResult --> End([結果返却])

    %% Standard モード
    StandardFlow --> StandardFilter{Critical<br/>問題あり?}
    StandardFilter -->|Yes| StandardLLM["LLM分析実行<br/>(Critical問題のみ)"]
    StandardFilter -->|No| StandardStatic["静的結果のみ"]
    StandardLLM --> StandardMerge["結果マージ"]
    StandardStatic --> StandardMerge
    StandardMerge --> End

    %% Comprehensive モード
    CompFlow --> CompLLM["LLM完全分析<br/>(全問題対象)"]
    CompLLM --> CompMerge["結果マージ<br/>重複除去"]
    CompMerge --> CompConfidence["信頼度計算"]
    CompConfidence --> End

    %% Critical Only モード
    CriticalFlow --> CriticalLLM["LLM分析<br/>(Critical問題)"]
    CriticalLLM --> End

    %% スタイリング
    style Start fill:#bbdefb
    style End fill:#c8e6c9
    style Mode fill:#fff9c4
    style StandardFilter fill:#fff9c4
```

## 📊 信頼度計算フロー図

```mermaid
graph TD
    %% 入力
    StaticResult["静的解析結果<br/>問題リスト"] --> CalcStatic
    LLMResult["LLM分析結果<br/>問題リスト"] --> CalcLLM

    %% 静的解析信頼度計算
    subgraph StaticConfidence["静的解析信頼度計算"]
        CalcStatic["基礎信頼度: 0.8"]
        CalcStatic --> StaticFactors["調整要因"]
        StaticFactors --> SF1["明確なパターン: +0.1"]
        StaticFactors --> SF2["行番号特定: +0.1"]
        StaticFactors --> SF3["複数検出器: +0.05"]
    end

    %% LLM信頼度計算
    subgraph LLMConfidence["LLM信頼度計算"]
        CalcLLM["基礎信頼度: 0.7"]
        CalcLLM --> LLMFactors["調整要因"]
        LLMFactors --> LF1["具体的な指摘: +0.15"]
        LLMFactors --> LF2["修正提案あり: +0.1"]
        LLMFactors --> LF3["コンテキスト理解: +0.05"]
    end

    %% 統合計算
    SF1 --> Merge["信頼度マージ"]
    SF2 --> Merge
    SF3 --> Merge
    LF1 --> Merge
    LF2 --> Merge
    LF3 --> Merge

    Merge --> Formula["総合信頼度計算<br/>overall = (static × 0.6) + (llm × 0.4)"]
    Formula --> Validation["検証"]

    %% 検証ルール
    Validation --> V1{"両方で検出?"}
    V1 -->|Yes| Boost["信頼度ブースト<br/>+0.1"]
    V1 -->|No| NoBoost["そのまま"]

    Boost --> Final["最終信頼度<br/>(0.0 - 1.0)"]
    NoBoost --> Final

    %% スタイリング
    style Final fill:#a5d6a7
    style Formula fill:#fff59d
```

## 🗂️ データモデル関係図

```mermaid
classDiagram
    %% Phase 1モデル
    class Issue {
        +String type
        +String severity
        +String message
        +String file_path
        +int line_number
        +String suggestion
    }

    class AnalysisResult {
        +List~Issue~ issues
        +int total_files
        +int files_with_issues
        +datetime timestamp
    }

    %% Phase 2モデル
    class AnalysisConfidence {
        +float static_confidence
        +float llm_confidence
        +float overall_confidence
        +calculate_overall()
    }

    class HybridAnalysisResult {
        +AnalysisResult static_result
        +AnalysisResult llm_result
        +List~Issue~ all_issues
        +AnalysisConfidence confidence
        +dict cost_metrics
        +String analysis_mode
        +merge_results()
        +remove_duplicates()
    }

    %% LLMコンポーネント
    class AnthropicClient {
        -String api_key
        -int max_retries
        -float rate_limit
        +analyze(prompt, code)
        +handle_retry()
    }

    class LLMAnalyzer {
        -AnthropicClient client
        +analyze_code(java_code)
        +build_prompt(code)
        +parse_response(response)
    }

    class HybridAnalysisEngine {
        -List~Detector~ detectors
        -LLMAnalyzer llm_analyzer
        -String api_key
        +analyze(java_code, mode)
        -run_static_analysis()
        -run_llm_analysis()
        -determine_analysis_strategy()
    }

    %% 関係
    AnalysisResult "1" --> "*" Issue : contains
    HybridAnalysisResult "1" --> "1" AnalysisResult : static_result
    HybridAnalysisResult "1" --> "1" AnalysisResult : llm_result
    HybridAnalysisResult "1" --> "1" AnalysisConfidence : confidence
    HybridAnalysisResult "1" --> "*" Issue : all_issues

    HybridAnalysisEngine "1" --> "1" LLMAnalyzer : uses
    LLMAnalyzer "1" --> "1" AnthropicClient : uses
    HybridAnalysisEngine "1" --> "*" HybridAnalysisResult : produces
```

## 🔀 分析モード決定フロー

```mermaid
stateDiagram-v2
    [*] --> ModeSelection: analyze(mode)

    state ModeSelection {
        [*] --> CheckMode
        CheckMode --> Quick: mode="quick"
        CheckMode --> Standard: mode="standard"
        CheckMode --> Comprehensive: mode="comprehensive"
        CheckMode --> CriticalOnly: mode="critical_only"
    }

    state Quick {
        [*] --> RunStatic
        RunStatic --> ReturnStatic
        ReturnStatic --> [*]
    }

    state Standard {
        [*] --> RunStaticStd
        RunStaticStd --> FilterCritical
        FilterCritical --> RunLLMCritical: has_critical
        FilterCritical --> SkipLLM: no_critical
        RunLLMCritical --> MergeResults
        SkipLLM --> MergeResults
        MergeResults --> [*]
    }

    state Comprehensive {
        [*] --> RunStaticComp
        RunStaticComp --> RunLLMFull
        RunLLMFull --> MergeCompResults
        MergeCompResults --> CalculateConfidence
        CalculateConfidence --> [*]
    }

    state CriticalOnly {
        [*] --> FilterStaticCritical
        FilterStaticCritical --> RunLLMCriticalOnly
        RunLLMCriticalOnly --> [*]
    }

    Quick --> [*]: HybridAnalysisResult
    Standard --> [*]: HybridAnalysisResult
    Comprehensive --> [*]: HybridAnalysisResult
    CriticalOnly --> [*]: HybridAnalysisResult
```

## 📈 コスト計算モデル

```mermaid
graph LR
    %% 入力パラメータ
    subgraph Inputs["入力パラメータ"]
        CodeSize["コードサイズ<br/>(行数)"]
        Mode["分析モード"]
        Issues["問題数"]
    end

    %% トークン計算
    subgraph TokenCalc["トークン計算"]
        InputTokens["入力トークン<br/>= code_lines × 2"]
        OutputTokens["出力トークン<br/>= issues × 100"]
    end

    %% 料金計算
    subgraph CostCalc["コスト計算"]
        InputCost["入力コスト<br/>$15/1M tokens"]
        OutputCost["出力コスト<br/>$75/1M tokens"]
        TotalCost["総コスト<br/>= input + output"]
    end

    %% フロー
    CodeSize --> InputTokens
    Issues --> OutputTokens
    Mode --> Multiplier["モード係数<br/>quick: 0<br/>standard: 0.3<br/>comprehensive: 1.0<br/>critical: 0.2"]

    InputTokens --> InputCost
    OutputTokens --> OutputCost
    Multiplier --> TotalCost
    InputCost --> TotalCost
    OutputCost --> TotalCost

    TotalCost --> Result["最終コスト<br/>$0.00 - $0.10"]

    %% スタイリング
    style Result fill:#c8e6c9
    style TotalCost fill:#fff59d
```

## 🔐 エラーハンドリングフロー

```mermaid
flowchart TD
    Start([API呼び出し]) --> Try{成功?}

    Try -->|Yes| Success[結果返却]
    Try -->|No| ErrorType{エラータイプ}

    ErrorType -->|Rate Limit| RateLimit[待機<br/>60秒]
    ErrorType -->|Timeout| Timeout[タイムアウト<br/>処理]
    ErrorType -->|API Error| APIError[APIエラー<br/>処理]
    ErrorType -->|Network| Network[ネットワーク<br/>エラー]

    RateLimit --> Retry{リトライ<br/>回数確認}
    Timeout --> Retry
    APIError --> Retry
    Network --> Retry

    Retry -->|< 3| Wait[指数バックオフ<br/>2^n秒待機]
    Retry -->|>= 3| Fallback[フォールバック<br/>静的解析のみ]

    Wait --> Start
    Fallback --> StaticOnly[静的解析結果<br/>のみ返却]

    Success --> End([完了])
    StaticOnly --> End

    %% スタイリング
    style Success fill:#c8e6c9
    style Fallback fill:#ffcdd2
    style End fill:#e1f5fe
```

## 🚀 パフォーマンス最適化

### キャッシング戦略

```mermaid
graph TD
    Request["分析リクエスト"] --> CacheCheck{キャッシュ<br/>チェック}

    CacheCheck -->|Hit| CacheHit["キャッシュ<br/>結果返却"]
    CacheCheck -->|Miss| Analysis["分析実行"]

    Analysis --> StaticAnalysis["静的解析"]
    StaticAnalysis --> StaticCache["静的結果<br/>キャッシュ"]

    Analysis --> LLMCheck{同一コード<br/>LLM結果?}
    LLMCheck -->|Yes| LLMCache["LLMキャッシュ<br/>利用"]
    LLMCheck -->|No| LLMAnalysis["LLM分析実行"]

    LLMAnalysis --> LLMCacheStore["LLM結果<br/>キャッシュ保存"]

    StaticCache --> Merge["結果マージ"]
    LLMCache --> Merge
    LLMCacheStore --> Merge

    Merge --> Result["最終結果"]
    Result --> ResultCache["結果キャッシュ<br/>TTL: 1時間"]

    CacheHit --> End([返却])
    ResultCache --> End
```

## 📊 メトリクス収集

```mermaid
graph LR
    %% メトリクス収集ポイント
    subgraph Collection["収集ポイント"]
        A1["分析開始時刻"]
        A2["静的解析時間"]
        A3["LLM応答時間"]
        A4["トークン使用量"]
        A5["検出問題数"]
        A6["信頼度スコア"]
    end

    %% 集計
    subgraph Aggregation["集計"]
        B1["平均分析時間"]
        B2["累計コスト"]
        B3["精度指標"]
        B4["エラー率"]
    end

    %% レポート
    subgraph Reporting["レポート"]
        C1["リアルタイムダッシュボード"]
        C2["日次レポート"]
        C3["月次コストレポート"]
    end

    A1 --> B1
    A2 --> B1
    A3 --> B1
    A4 --> B2
    A5 --> B3
    A6 --> B3

    B1 --> C1
    B2 --> C2
    B3 --> C2
    B4 --> C3
```

## 🔗 Phase 1との統合ポイント

1. **検出器の再利用**
   - AllowFilteringDetector
   - PartitionKeyDetector
   - BatchSizeDetector
   - PreparedStatementDetector

2. **モデルの拡張**
   - Issue → HybridIssue（信頼度追加）
   - AnalysisResult → HybridAnalysisResult

3. **パーサーの共有**
   - JavaCassandraParser
   - ASTParser
   - CQLExtractor

4. **レポート生成の強化**
   - HTML/JSON/Markdownフォーマット維持
   - LLM分析結果の統合表示
   - 信頼度スコアの可視化

## 📝 設計原則

1. **モジュラー設計**
   - 各コンポーネントは独立して動作可能
   - インターフェース経由での疎結合

2. **フェイルセーフ**
   - LLM失敗時は静的解析結果を返却
   - 部分的な失敗を許容

3. **コスト効率**
   - モード選択による最適化
   - キャッシング活用

4. **拡張性**
   - 新しいLLMプロバイダーの追加容易
   - 新しい分析モードの追加可能

---

*最終更新: 2025年01月27日 15:40 JST*
*バージョン: v1.0.0*

**更新履歴:**
- v1.0.0 (2025年01月27日): Phase 2アーキテクチャ図初版作成、全図表完成