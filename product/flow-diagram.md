# Enterprise Tomb Raider — 系統流程圖

> 最後更新：2026-04-10（v1.5）
> 本文件使用 Mermaid 格式。在 GitHub 上可直接渲染，或使用 [Mermaid Live Editor](https://mermaid.live/) 檢視。

---

## 1. 系統總覽：三層架構 + 檔案調用關係

```mermaid
graph TB
    subgraph USER["使用者"]
        CMD["/recon · /industry · /company"]
    end

    subgraph SKILL["入口層 — .claude/skills/"]
        S_RECON["recon/SKILL.md<br/>統一入口 · 完整流程"]
        S_IND["industry/SKILL.md<br/>路徑 A 快捷"]
        S_COM["company/SKILL.md<br/>路徑 B 快捷"]
    end

    subgraph AGENT["執行層 — agent/"]
        CORE["AGENT-CORE.md<br/>角色 · 迴圈 · 預算 · 降級"]
        ROUTES["AGENT-ROUTES.md<br/>路徑 · 階段順序"]
        subgraph PROMPTS["prompts/ — 動態載入"]
            P_EV["entity-verification.md"]
            P_SI["stakeholder-investigation.md"]
            P_IA["industry-analysis.md"]
            P_AR["annual-report-analysis.md"]
            P_CD["company-deep-dive.md"]
            P_DB["decision-brief.md"]
        end
    end

    subgraph REF["知識層 — references/"]
        subgraph METH["methodology/"]
            M_PS["path-selection.md"]
            M_SC["scale-classification.md"]
            M_QC["quality-checklist.md"]
            M_FP["fetch-policy.md"]
            M_IS["industry-specific-sources.md"]
            M_AR["annual-report-sources.md"]
        end
        subgraph TMPL["templates/"]
            T_IR["industry-report.md"]
            T_CR["company-report.md"]
            T_DB["decision-brief.md"]
        end
    end

    subgraph CASES_LAYER["案例層 — cases/"]
        CASE_TMPL["_case-template.md"]
        CASE_DIR["{target}/<br/>input/ · report · brief<br/>supplements/ · case-log"]
    end

    subgraph OUTPUT["品質層"]
        RULES[".claude/rules/<br/>output-quality.md"]
    end

    CMD --> S_RECON
    CMD --> S_IND
    CMD --> S_COM
    S_RECON --> CORE
    S_IND --> CORE
    S_COM --> CORE
    S_RECON -.->|"讀取"| M_PS
    S_RECON -.->|"讀取"| M_SC
    CORE --> ROUTES
    ROUTES -->|"動態載入"| PROMPTS
    P_EV -.->|"引用"| M_FP
    P_SI -.->|"引用"| M_FP
    P_IA -.->|"引用"| M_IS
    P_AR -.->|"引用"| M_AR
    P_CD -.->|"引用"| T_CR
    P_DB -.->|"引用"| T_DB
    P_IA -.->|"引用"| T_IR
    CORE -.->|"引用"| CASE_DIR
    PROMPTS -->|"產出"| CASE_DIR
    CASE_DIR -.->|"受約束"| RULES
    PROMPTS -->|"沉澱"| CASE_DIR
    S_RECON -.->|"Review"| M_QC
```

---

## 2. 路徑 B 完整流程：公司 → 產業（主要路徑）

```mermaid
flowchart TD
    START(["使用者輸入<br/>/company XX 或 /recon XX公司"]) --> PROFILE{"user-profile.md<br/>存在？"}

    PROFILE -->|"不存在"| ONBOARD["Onboarding<br/>建立使用者 Profile"]
    PROFILE -->|"存在"| SCOPING
    ONBOARD --> SCOPING

    SCOPING["Step 3: Scoping<br/>路徑判斷 → B<br/>讀取 path-selection.md<br/>讀取 scale-classification.md"] --> EV

    EV["Step 1: Entity Verification<br/>載入 entity-verification.md<br/>🔍 5-8 search · 1-2 fetch<br/>引用 fetch-policy.md"] --> EV_OUT["產出：快速輪廓<br/>規模分類確認"]

    EV_OUT --> ASSESS["Step 4.0.5: 預分析評估<br/>📊 零搜尋預算<br/>· 資料豐富度評估<br/>· 年報計畫（強制/建議/跳過）<br/>· 搜尋預算預估<br/>· 模型建議<br/>· 時間預估"]

    ASSESS --> USER_CONFIRM{"使用者確認？"}
    USER_CONFIRM -->|"繼續"| SI
    USER_CONFIRM -->|"提供 PDF 路徑"| SI
    USER_CONFIRM -->|"跳過年報"| SI

    SI["Step 1.5: Stakeholder Investigation<br/>載入 stakeholder-investigation.md<br/>🔍 10-15 search · 3-5 fetch<br/>引用 fetch-policy.md"] --> SI_OUT["產出：三項判斷<br/>權力結構 · 關係資本 · 人事穩定性"]

    SI_OUT --> IA["Step 2: Industry Analysis<br/>載入 industry-analysis.md（錨點模式）<br/>🔍 8-12 search · 2-3 fetch<br/>引用 industry-specific-sources.md"]

    IA --> AR_CHECK{"規模分類？"}

    AR_CHECK -->|"大型/上市<br/>（強制）"| AR
    AR_CHECK -->|"中型且公開<br/>（建議）"| AR
    AR_CHECK -->|"微型<br/>或已跳過"| CD

    AR["Step 2.5: Annual Report Analysis<br/>載入 annual-report-analysis.md<br/>🔍 5 search · 3 fetch<br/>引用 annual-report-sources.md<br/>📄 Read PDF（如使用者提供）"] --> AR_OUT["產出：年報數據摘要<br/>+ 衝突清單"]

    AR_OUT --> CD

    CD["Step 3: Company Deep Dive<br/>載入 company-deep-dive.md<br/>🔍 5-8 search · 2-3 fetch<br/>輸入：前序所有階段結果<br/>+ 年報數據（如有）<br/>引用 company-report.md 模板"] --> CD_CHECK{"有年報數據？<br/>（大型/上市）"}

    CD_CHECK -->|"有"| CD_FULL["正常分析<br/>年報為主要數據源"]
    CD_CHECK -->|"無"| CD_DEGRADE["降級分析<br/>6 維度標註<br/>⚠️ 報告 metadata 警告"]
    CD_CHECK -->|"不適用<br/>（微型/中型）"| CD_NORMAL["正常分析<br/>無年報前置檢查"]

    CD_FULL --> QR
    CD_DEGRADE --> QR
    CD_NORMAL --> QR

    QR["Step 5: Quality Review<br/>載入 quality-checklist.md<br/>24 項逐項檢查"] --> DB_CHECK{"user-profile.md<br/>存在？"}

    DB_CHECK -->|"存在"| DB["Step 5.5: Decision Brief<br/>載入 decision-brief.md<br/>🚫 零搜尋預算<br/>引用 decision-brief.md 模板<br/>角色化重新解讀"]
    DB_CHECK -->|"不存在"| SAVE

    DB --> SAVE["Step 6: 存檔 + 案例沉澱<br/>→ cases/{name}/company-report.md（含 Version History）<br/>→ cases/{name}/decision-brief.md<br/>→ cases/{name}/case-log.md"]

    SAVE --> SUPP_HINT(["完成<br/>★ 後續有新資料 →<br/>/supplement {name}"])

    style ASSESS fill:#e1f5fe,stroke:#0288d1,stroke-width:2px
    style AR fill:#e1f5fe,stroke:#0288d1,stroke-width:2px
    style CD_DEGRADE fill:#fff3e0,stroke:#f57c00,stroke-width:2px
```

---

## 3. 路徑 A 完整流程：產業 → 公司

```mermaid
flowchart TD
    START_A(["使用者輸入<br/>/industry XX 或 /recon XX產業"]) --> PROFILE_A{"user-profile.md<br/>存在？"}

    PROFILE_A -->|"不存在"| ONBOARD_A["Onboarding"]
    PROFILE_A -->|"存在"| SCOPING_A
    ONBOARD_A --> SCOPING_A

    SCOPING_A["Scoping<br/>路徑判斷 → A<br/>確認：產業細分 + 地理範圍 + 分析目的"] --> IA_A

    IA_A["Industry Analysis<br/>載入 industry-analysis.md（無錨點）<br/>🔍 8-12 search · 2-3 fetch<br/>三維度：趨勢 · 結構 · 玩家"] --> IA_OUT_A["產出：產業報告"]

    IA_OUT_A --> DEEP{"要深入<br/>某家公司？"}

    DEEP -->|"否"| DB_A_CHECK{"user-profile.md<br/>存在？"}
    DEEP -->|"是"| ENTER_B["進入路徑 B<br/>從 Step 1 開始"]

    DB_A_CHECK -->|"存在"| DB_A["Decision Brief<br/>（產業版）"]
    DB_A_CHECK -->|"不存在"| SAVE_A

    DB_A --> SAVE_A["存檔<br/>cases/{name}/industry-report.md"]
    SAVE_A --> DONE_A(["完成"])
```

---

## 4. 搜尋迴圈（每個 Agent 階段內部）

```mermaid
flowchart TD
    ENTER(["進入階段<br/>載入對應 prompt"]) --> SEARCH["執行搜尋<br/>web_search / web_fetch"]

    SEARCH --> EVAL{"資訊<br/>足夠？"}

    EVAL -->|"足夠"| PRODUCE["產出結構化結果"]
    EVAL -->|"不足"| BUDGET{"搜尋預算<br/>剩餘？"}

    BUDGET -->|"有餘額"| ADJUST["識別缺口<br/>調整搜尋策略"] --> SEARCH
    BUDGET -->|"已用完"| DEGRADE["降級產出<br/>標註證據等級<br/>[部分證據] / [推測，待驗證] / [資料缺失]"]

    PRODUCE --> EXIT(["EXIT 階段"])
    DEGRADE --> EXIT

    style DEGRADE fill:#fff3e0,stroke:#f57c00
```

---

## 5. 規模自適應：不同規模走不同深度

```mermaid
graph LR
    subgraph MICRO["微型 — <50人 · 非上市"]
        M1["商業登記 + 求職平台"]
        M2["現金流結構推論"]
        M3["創辦人能力評估"]
        M4["簡化五力"]
        M5["關鍵人物風險"]
        M6["❌ 年報不適用"]
    end

    subgraph MID["中型 — 50-500人"]
        D1["商業登記 + 求職平台"]
        D2["融資輪次分析"]
        D3["標準三層調查"]
        D4["標準五力"]
        D5["標準 DD"]
        D6["📄 年報建議取得"]
    end

    subgraph LARGE["大型/上市 — >500人 · 已上市"]
        L1["商業登記 + 年報（強制）+ 財經平台"]
        L2["完整三大報表（以年報為準）"]
        L3["完整三層 + 董事會"]
        L4["完整五力 + 數據"]
        L5["完整 DD"]
        L6["📄 年報強制取得"]
    end

    style MICRO fill:#e8f5e9
    style MID fill:#fff8e1
    style LARGE fill:#fce4ec
```

---

## 6. 年報解析降級鏈

```mermaid
flowchart TD
    START_AR(["年報解析階段開始"]) --> USER_PDF{"使用者<br/>提供 PDF？"}

    USER_PDF -->|"是"| READ_LOCAL["直接 Read PDF<br/>最快 · 最可靠"]
    USER_PDF -->|"否"| SEARCH_IR["搜尋公司 IR 網站<br/>web_search + web_fetch"]

    SEARCH_IR --> IR_OK{"fetch<br/>成功？"}
    IR_OK -->|"是"| READ_LOCAL
    IR_OK -->|"否"| SEARCH_REG["搜尋監管平台<br/>（MOPS / EDGAR 等）"]

    SEARCH_REG --> REG_OK{"fetch<br/>成功？"}
    REG_OK -->|"是"| READ_LOCAL
    REG_OK -->|"否"| SEARCH_HTML["搜尋 HTML 版年報"]

    SEARCH_HTML --> HTML_OK{"取得？"}
    HTML_OK -->|"是"| PARSE["解析並提取<br/>12 項數據點"]
    HTML_OK -->|"否"| FAIL["全部失敗<br/>標註 [年報未取得]<br/>列出已嘗試來源"]

    READ_LOCAL --> PARSE
    PARSE --> SUMMARY["產出：年報數據摘要<br/>+ 衝突清單"]
    FAIL --> NOTIFY["通知 Skill 層<br/>company-deep-dive 將降級"]

    SUMMARY --> NEXT(["進入 company-deep-dive<br/>年報數據作為輸入"])
    NOTIFY --> NEXT

    style FAIL fill:#ffcdd2,stroke:#c62828
    style SUMMARY fill:#c8e6c9,stroke:#2e7d32
```
