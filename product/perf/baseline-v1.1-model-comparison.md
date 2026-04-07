# 模型選擇 + 訂閱方案指南：以個人理財 SaaS A分析為實戰基準

**撰寫日期**：2026-04-06
**資料來源**：[Anthropic Models Overview](https://platform.claude.com/docs/en/about-claude/models/overview)、[Pricing](https://platform.claude.com/docs/en/about-claude/pricing)、[Claude Plans & Pricing](https://claude.com/pricing)、[Claude Code Pro/Max 使用說明](https://support.claude.com/en/articles/11145838-using-claude-code-with-your-pro-or-max-plan)、[Claude Code Token Limits](https://www.faros.ai/blog/claude-code-token-limits)

---

## 一、四個選項的規格對照

| 規格 | Opus 4.6 | Opus 4.6 (1M) | Sonnet 4.6 | Haiku 4.5 |
|------|----------|---------------|------------|-----------|
| **本質** | 同一模型 | 同一模型 | 不同模型 | 不同模型 |
| **差異** | Claude Code 預設 context 管理 | 明確啟用完整 1M context | 速度 + 智力的平衡點 | 最快、最便宜 |
| **Context Window** | 1M（但 CLI 可能限縮使用量） | 1M（完整使用） | 1M | 200K |
| **Max Output** | 128K tokens | 128K tokens | 64K tokens | 64K tokens |
| **Input 定價** | $5 / MTok | $5 / MTok | $3 / MTok | $1 / MTok |
| **Output 定價** | $25 / MTok | $25 / MTok | $15 / MTok | $5 / MTok |
| **SWE-bench** | 80.8% | 80.8% | 79.6% | — |
| **延遲** | 中等 | 中等 | 快 | 最快 |
| **知識截止** | 2025-05（可靠）/ 2025-08（訓練） | 同左 | 2025-08（可靠）/ 2026-01（訓練） | 2025-02 / 2025-07 |

### Opus 4.6 vs Opus 4.6 (1M) 的差別

這兩個是**同一個模型**。差別在 Claude Code 的 context 管理策略：
- **Opus 4.6**：Claude Code 會更積極地壓縮 context history（摘要舊對話、丟棄早期 tool results），優化延遲和成本
- **Opus 4.6 (1M)**：明確告訴 Claude Code「保留完整 context，不要壓縮」，確保能使用完整的 1M token 窗口

對 Recon 系統而言，這個差異是**致命的**——如果 context 被壓縮，後序階段就無法引用前序階段的原始搜尋結果。

---

## 二、用個人理財 SaaS A數據分析算實際成本

### 基準數據（來自 token-usage-report）

| 指標 | 數值 |
|------|------|
| Phase 1+2 Input tokens（峰值） | ~168K |
| Phase 1+2 Output tokens | ~26K |
| WebSearch 次數 | 26 |
| WebFetch 次數 | 3 |
| 檔案 Read 次數 | 15 |
| 檔案 Write 次數 | 4 |
| Context 峰值 | ~116K tokens |

### 四種模型的成本估算

| 模型 | Input 成本 | Output 成本 | 合計 | vs Opus 1M |
|------|-----------|-----------|------|-----------|
| **Opus 4.6 (1M)** | $0.84 | $0.65 | **$1.49** | 基準 |
| **Opus 4.6** | $0.84 | $0.65 | **$1.49** | 同價，但有 context 壓縮風險 |
| **Sonnet 4.6** | $0.50 | $0.39 | **$0.89** | **-40%** |
| **Haiku 4.5** | $0.17 | $0.13 | **$0.30** | **-80%** |

> 注意：上一份 token-usage-report 使用了舊版 Opus 3 的定價（$15/$75），實際 Opus 4.6 定價為 $5/$25，已在此修正。

---

## 三、能不能跑 Recon 全流程？逐模型分析

### Opus 4.6 (1M) ✅ 完整支援

**這是目前唯一能保證完整 Recon 流程的配置。**

- Context 峰值 116K / 上限 1M = 11.6%，極度寬裕
- 128K max output 足以寫完整報告（company-report ~8K tokens + decision-brief ~5.5K）
- 結論繼承鏈完整：實體驗證 → 利害關係人 → 產業 → 公司 → Decision Brief
- 唯一問題：延遲較高，完整流程可能需要 3-5 分鐘

### Opus 4.6（標準 context 管理） ⚠️ 有風險

**模型能力相同，但 context 壓縮可能破壞分析品質。**

具體風險場景：
```
Phase 1 實體驗證：「opengovtw 顯示董事包含[董事 A-2]代表[創投 A-Investor]」
        ↓ context 壓縮，原始 search snippet 被丟棄
Phase 2 利害關係人：只剩壓縮摘要，無法回查原始數據
        ↓
Phase 4 公司深度：「[創投 A-Investor]持股 ~14.9%」← 無法驗證這個數字的來源
```

**實測建議**：如果你的對話只做到實體驗證就結束（Phase 1），Opus 標準模式完全夠用。但要跑全流程（Phase 1→Phase 2 一路到 Decision Brief），用 1M 模式更安全。

### Sonnet 4.6 ✅ 可行，品質略降

**90% 場景下的最佳性價比選擇。**

- Context window 同為 1M，結論繼承鏈可以保持完整
- SWE-bench 79.6% vs Opus 80.8%——對 Recon 的影響更多在「推論品質」而非「能不能做」
- Max output 64K vs 128K——對單次報告寫入夠用（company-report ~8K tokens）
- **成本只有 Opus 的 60%**

**Sonnet 會在哪裡表現較差？**

| 場景 | 影響程度 | 原因 |
|------|---------|------|
| 利害關係人的「關係資本歸屬」判斷 | 🟡 中 | 這需要從碎片化線索推導結論（「[創辦人 A]在[天使投資組織 A-Network]學了方法論後思維大改觀」→ 推論出關係資本綁個人），Opus 在這類 nuanced reasoning 上有優勢 |
| 營收間接推估（三種方法交叉） | 🟡 中 | 需要從不完整資訊做量化推估，Opus 的數學推理更穩 |
| Decision Brief 的「一句話判斷」 | 🟡 中 | 從 4 階段結果壓縮成一句精準判斷，Opus 的概括能力更好 |
| 實體驗證（搜尋 + 比對） | 🟢 低 | 結構化任務，Sonnet 完全勝任 |
| 產業分析（五力、趨勢） | 🟢 低 | 框架明確，Sonnet 完全勝任 |
| 搜尋策略選擇 | 🟢 低 | prompt 已定義搜尋樣式，差異極小 |

**結論**：如果你每月做 10+ 次公司分析，Sonnet 省下的 40% 成本是實質的。品質差異主要在「判斷的精準度」，而非「能不能完成」。

### Haiku 4.5 ❌ 無法單獨完成全流程

**Context window 只有 200K，無法在單一 context 中跑完全流程。**

但 Haiku **極適合作為 sub-agent**：

```
                        ┌→ Haiku sub-agent：實體驗證（~30K context）→ JSON
主 Agent（Opus/Sonnet）─┼→ Haiku sub-agent：人物搜尋 x N（~20K each）→ JSON
                        └→ Haiku sub-agent：產業搜尋（~25K context）→ JSON
                        ↓
            主 Agent 整合所有 JSON → 公司報告 + Decision Brief
```

此架構：
- Haiku 做搜尋密集的「資料收集」→ 每個 sub-agent 成本 ~$0.03-0.05
- Opus/Sonnet 做「整合 + 判斷 + 寫報告」→ 只需處理壓縮後的結構化資料
- 總成本可能降至 **$0.50-0.80**（vs 純 Opus $1.49）

**但有代價**：前面分析過的「壓縮過程會丟失 nuance」問題。

---

## 四、推薦配置

### 配置 A：品質最大化（現行）
```
全流程 Opus 4.6 (1M) → ~$1.49/次
```
- 適合：重大投資決策、高風險合作評估、需要完整證據鏈
- 優勢：品質最高、context 完整、結論繼承鏈無損
- 劣勢：成本最高、延遲最長

### 配置 B：性價比最佳（推薦日常使用）
```
全流程 Sonnet 4.6 (1M) → ~$0.89/次
```
- 適合：日常公司研究、求職評估、競品追蹤
- 優勢：成本降 40%、速度更快、品質差異在可接受範圍
- 劣勢：nuanced reasoning 略弱

### 配置 C：成本最小化（未來可探索）
```
Haiku 4.5 (sub-agents 做搜尋) + Sonnet 4.6 (主 Agent 做整合) → ~$0.50-0.80/次
```
- 適合：批量分析（一次研究 5-10 家公司）、初步篩選
- 優勢：成本降 50-65%、搜尋階段可平行加速
- 劣勢：需要開發 sub-agent 編排邏輯、nuance 丟失風險
- 狀態：需修改 AGENT-CORE 和 SKILL.md 架構才能支援

### 配置 D：混合模式（進階）
```
Phase 1 實體驗證：Haiku（結構化搜尋，不需要深度判斷）
Phase 2 利害關係人：Opus（需要 nuanced reasoning）
Phase 3 產業分析：Sonnet（框架明確，Sonnet 夠用）
Phase 4 公司深度 + Brief：Opus（整合判斷）
```
- 適合：願意投入架構開發成本的團隊
- 優勢：每個階段用最適合的模型
- 劣勢：跨模型 context 傳遞是工程挑戰
- 狀態：概念可行，但 Recon 系統目前不支援

---

## 五、模型選擇決策樹

```
你要分析的公司是？
├── 重大決策（投資 >1000 萬、高風險合作）
│   └→ 配置 A：Opus 4.6 (1M)，不省這個錢
├── 日常研究（求職、競品、一般了解）
│   └→ 配置 B：Sonnet 4.6，品質夠用省 40%
├── 批量篩選（一次看 5+ 家）
│   └→ 配置 C：Haiku + Sonnet 混合（需開發）
└── 只做實體驗證（快速確認公司是誰）
    └→ Haiku 4.5 就夠，~$0.05/次
```

---

## 六、訂閱方案 vs Recon 系統的適配分析

### 方案總覽

| 方案 | 月費 | Claude Code | Token 預算（5hr 窗口） | Claude.ai 共用 | 模型選擇 |
|------|------|-------------|----------------------|----------------|---------|
| **Free** | $0 | ❌ 不可用 | — | — | Sonnet 限量 |
| **Pro** | $20 | ✅ | ~44K tokens | ⚠️ 共用額度 | Opus + Sonnet |
| **Max 5x** | $100 | ✅ | ~88K tokens | ⚠️ 共用額度 | Opus + Sonnet |
| **Max 20x** | $200 | ✅ | ~220K tokens | ⚠️ 共用額度 | Opus + Sonnet |
| **Team Standard** | $20/seat | ❌ 不可用 | — | — | Opus + Sonnet |
| **Team Premium** | $100/seat | ✅ | ~88K（≈Max 5x） | ⚠️ 共用額度 | Opus + Sonnet |
| **Enterprise** | 洽談 | ✅ | 客製 | 獨立 | 全模型 + 500K context |
| **API（BYOK）** | pay-as-you-go | ✅ | **無上限** | 不適用 | 全模型 + 1M context |

> **來源**：[Claude Code Token Limits](https://www.faros.ai/blog/claude-code-token-limits)、[SSD Nodes 方案解析](https://www.ssdnodes.com/blog/claude-code-pricing-in-2026-every-plan-explained-pro-max-api-teams/)
> **注意**：Token 預算為社群估算值，Anthropic 未公開精確數字且會動態調整。`[部分證據]`

### 關鍵機制：5 小時滾動窗口

```
你發第一條訊息 → 計時開始 → 5 小時內所有 Claude Code + Claude.ai 的用量從同一池扣
                                                                    ↓
                                                        5 小時後下一條訊息 → 重新計時
```

**致命細節**：Claude Code 和 Claude.ai **共用額度**。如果你在 Claude.ai 上聊了一小時，再開 Claude Code 跑 Recon，剩餘額度已被吃掉一部分。

### 個人理財 SaaS A數據分析的實際消耗 vs 各方案額度

我們的 Recon 全流程消耗（Output tokens 為主要限制因素）：

| 模型 | Output tokens | Opus 加權（×1.7） | 說明 |
|------|--------------|-------------------|------|
| Sonnet 4.6 | ~26K | — | 直接消耗 |
| Opus 4.6 | ~26K | ~44K | Opus 每 token 從預算池扣 ~1.7 倍 |

### 逐方案可行性

#### Free ❌ 完全不可用
無 Claude Code 存取權。

#### Pro（$20/月）⚠️ 勉強可行，有很大限制

**Sonnet 模式**：
- 預算 ~44K tokens / 5hr
- Recon output ~26K tokens → 消耗約 **59%** 預算
- 但 system prompt + tool results 的 input 也消耗預算
- **結論**：可能剛好完成一次完整分析，但幾乎用完整個 5 小時窗口
- **風險**：如果同時段有用 Claude.ai，會擠壓預算

**Opus 模式**：
- Opus 加權後 ~44K → 消耗約 **100%** 預算
- **結論**：大概率跑不完全流程就撞牆
- **不推薦在 Pro 上用 Opus 跑完整 Recon**

**Pro 的最佳策略**：
```
1. 專開一個乾淨的 5hr 窗口（不要同時用 Claude.ai）
2. 用 Sonnet 跑全流程
3. 如果中途被限速 → 等下一個窗口繼續（對話 context 會保留）
4. 每月可做 ~3-5 次完整分析（假設每天用一個窗口）
```

#### Max 5x（$100/月）✅ 推薦的訂閱方案

**Sonnet 模式**：
- 預算 ~88K tokens / 5hr
- Recon 消耗 ~26K → 約 **30%** 預算
- **一個窗口內可做 2-3 次完整分析**

**Opus 模式**：
- Opus 加權後 ~44K → 約 **50%** 預算
- **一個窗口內可做 1-2 次完整分析**
- 有空間在分析中途糾錯（像我們修正董監事名單那樣）

**Max 5x 的最佳策略**：
```
1. 日常用 Sonnet 跑全流程（一個窗口做 2-3 家）
2. 重要決策切 Opus（一個窗口做 1 家 + 修正空間）
3. 每月可做 ~15-25 次完整分析
```

#### Max 20x（$200/月）✅ 重度使用者

**Sonnet 模式**：
- 預算 ~220K tokens / 5hr
- 一個窗口可做 **5-7 次完整分析**

**Opus 模式**：
- 一個窗口可做 **3-4 次完整分析**

**Max 20x 的最佳策略**：
```
1. 全部用 Opus 也無壓力
2. 適合每天研究多家公司的投資人或分析師
3. 每月可做 ~60-100 次完整分析
```

#### Team Premium（$100/seat/月）✅ 等同 Max 5x

同 Max 5x 的策略。額外優勢：多人共用同一個 Recon 方法論庫。

#### Enterprise（洽談）✅ 最完整

- 500K context window（比訂閱版的 200K 大 2.5 倍）
- 客製 token 限額
- 適合把 Recon 系統作為團隊標準工具的組織

#### API BYOK（自帶 Key）✅ 最大彈性

**成本完全透明，無窗口限制**：
- Opus 全流程 ~$1.49/次
- Sonnet 全流程 ~$0.89/次
- 完整 1M context window
- 適合：知道自己用量的開發者 / 把 Recon 包成產品的團隊

**損益兩平點**（vs 訂閱方案）：

| 比較 | API 成本 | 等同方案 | 損益兩平次數/月 |
|------|---------|---------|--------------|
| Opus $1.49/次 vs Max 5x $100/月 | $1.49 × N | $100 | **~67 次** |
| Sonnet $0.89/次 vs Max 5x $100/月 | $0.89 × N | $100 | **~112 次** |
| Opus $1.49/次 vs Pro $20/月 | $1.49 × N | $20 | **~13 次** |
| Sonnet $0.89/次 vs Pro $20/月 | $0.89 × N | $20 | **~22 次** |

> ⚠️ Pro 的窗口限制可能讓你每月實際只能做 3-5 次，遠低於損益兩平的 13-22 次。
> 所以對 Recon 系統而言，**Pro 的 $20 幾乎等於 3-5 次 Opus 分析的預付**。

---

## 七、終極推薦矩陣

| 你是誰 | 推薦方案 | 推薦模型 | 月預算 | 月分析量 |
|--------|---------|---------|--------|---------|
| **偶爾研究（<5 次/月）** | Pro $20 | Sonnet | $20 | 3-5 次 |
| **固定使用（5-20 次/月）** | Max 5x $100 | Sonnet 為主 / Opus 重要場合 | $100 | 15-25 次 |
| **重度使用（>20 次/月）** | Max 20x $200 | Opus 為主 | $200 | 60-100 次 |
| **團隊共用** | Team Premium $100/seat | Sonnet 為主 | $100/人 | 15-25 次/人 |
| **開發者 / 產品化** | API BYOK | 混合配置 | 按量 | 無限 |
| **組織級部署** | Enterprise | 全模型 | 洽談 | 客製 |

### 如果你只能記住一件事

> **Max 5x（$100/月）+ Sonnet 4.6** 是 Recon 系統的甜蜜點：
> 一個 5 小時窗口做 2-3 家公司分析，重要的切 Opus，每月 15-25 次。
> 比 Pro 寬裕很多，比 Max 20x 划算（除非你真的每天都在研究公司）。
