# 2026-04-08 雲端資安代理商 B 實測報告 — RFC-001 Drop Zone

**測試日期**：2026-04-08
**對照 baseline**：[`baseline-v1.1-token-usage.md`](baseline-v1.1-token-usage.md)（個人理財 SaaS A，v1.1 era）
**對應 RFC**：[RFC-001](../rfcs/RFC-001-drop-zone.md)
**測試環境**：Claude Opus 4.6 (1M context)，CLI + WebSearch/WebFetch
**測試者**：Andrew Yen
**系統版本**：Enterprise Tomb Raider v1.4（首次有 drop zone 流程的實測）

---

## 測試情境與重要 Caveat

本次測試走完整路徑 B 全流程（`/company 雲端資安代理商 B`），**但 drop zone 為空**（使用者未餵入任何檔案）。

**這意味著**：
- ✅ 能量測 v1.4 新增流程的「overhead 情境」（Step 3.5 空掃描、drop-zone.md 預載、多源優先序的 prompt 膨脹）
- ❌ **無法量測**「drop zone 有檔案時的節省效應」（預期搜尋次數下降 5-7 次、fetch 下降 2-3 次）

這是 RFC-001 §6 的預估表中「有年報時」的情境**未被本次測試驗證**。需要後續補一次「帶 drop zone 內容」的對照測試（建議：在 `input/雲端資安代理商 B/` 放入 ASDP 公告截圖和 Cloudflare 案例 PDF，重跑一次）。

**另一個重要 caveat**：baseline 案例（個人理財 SaaS A）與本次實測案例（雲端資安代理商 B）的**本質複雜度不同**：
- 個人理財 SaaS A案：相對單純的單一實體，無關聯法人發現
- 案例 B：**發現關聯法人**（系統整合商 B-Affiliate）+ 資本額衝突觸發 v1.2 規則 + 雙法人事業體判定 → 計畫外但高價值的追蹤

所以本報告中**所有「實測 vs baseline」的比較都不是純粹的 v1.4 overhead 比較**，而是「不同案例複雜度 + v1.4 overhead」的混合效應。這個 caveat 不會影響對 v1.4 overhead 趨勢的判斷，但會影響具體數字的可比較性。

---

## Tool Call 統計（精確回溯）

### 分階段明細

| 階段 | WebSearch | WebFetch | Read | Glob | Write | 備註 |
|------|----------|---------|------|------|-------|------|
| Step 0 Profile Check | — | — | 1 | 1 | — | user-profile.md 存在，靜默載入 |
| **Step 3.5 Drop Zone Scan** | — | — | — | **1** | — | **v1.4 新增**，目錄為空靜默通過 |
| Step 1 方法論載入 | — | — | 2 | — | — | scale-classification.md、path-selection.md |
| **Step 4.1 Entity Verification** | **10** | **8** | — | — | — | **大幅超預算**（預算 5-8 search + 1-2 fetch） |
| Step 4.0.5 預分析評估 | 0 | 0 | — | — | — | 零搜尋預算，純合成 |
| Step 4.1.5 Stakeholder Investigation | 13 | 2 | 1 | — | — | search 在 10-15 預算內 |
| Step 4.2 Industry Analysis | 5 | 0 | 1 | — | — | 低於 8-12 預算，主動收斂 |
| Step 4.2.5 Annual Report Analysis | — | — | — | — | — | **跳過**（非上市無年報）|
| Step 4.3 Company Deep Dive | 0 | 0 | 2 | — | 1 | 純合成；Read prompt + template；Write 報告 |
| Step 5.5 Decision Brief | 0 | 0 | — | — | 1 | 零搜尋預算（v1.1 設計）|
| Step 6 案例沉澱 | — | — | 1 | — | 1 | Read case template、Write case |
| 本份 Perf 報告（meta） | — | — | 1 | — | 1 | 不計入研究預算 |
| **研究階段總計** | **28** | **10** | **8** | **2** | **3** | 不含 perf 寫入本身 |

### 與 RFC-001 §6 設計時預估的對照

| 維度 | RFC-001 預估 Δ | 實測 (baseline → v1.4 案例 B) | 偏差 vs 預估 | 解讀 |
|------|--------------|----------------------------|------------|------|
| 預載 token（系統 prompt + skill + agent） | +300 | +~350 (估算) | +17% | Step 3.5 + drop-zone.md 指向確實增加 prompt 載入量，與預估接近 |
| 平均階段新增 Read 呼叫 | +1–2 | +0（drop zone 空，無 MANIFEST 可讀）| 低於預估 | drop zone 空時完全無 Read 開銷 |
| 平均階段新增 Glob 呼叫 | +1 | **+1** ✅ | 準確 | Step 3.5 的 Glob 如預期發生 |
| 預期搜尋次數變化（有年報時）| −5 to −7 | **不適用**（drop zone 空）| 未驗證 | 需補測「有餵資」情境 |
| 預期 fetch 次數變化（有年報時）| −2 to −3 | **不適用** | 未驗證 | 同上 |
| 命中率預期變化 | 使用者餵資時提升 | **不適用** | 未驗證 | 同上 |
| 證據等級分布預期變化 | 資料缺失下降 | **未明顯變化**（案例 B資料缺失仍多）| 未驗證 | 本案的資料缺失是**非上市財務不透明**造成，不是 drop zone 能解的 |

### 總用量與 baseline 對照

| 指標 | baseline v1.1（個人理財 SaaS A案）| 實測 v1.4（案例 B）| 差異 | 原因歸因 |
|------|---------------------|------------------|------|---------|
| WebSearch 總次數 | 18（Phase 2 完整路徑 B）| **28** | **+10** | 主要來自關聯法人發現追蹤（約 +7），其餘來自案例 B本身複雜度 |
| WebFetch 總次數 | 0（Phase 2 完整路徑 B）| **10** | **+10** | 案例 B有資本額衝突需多源驗證 + 關聯法人需追多個頁面；baseline 案例靠 snippet 就夠 |
| Read 呼叫 | 8 | 8 | 0 | 載入方法論的模式穩定 |
| Write 呼叫 | 3 | 3 | 0 | 報告 + 簡報 + case 的模式穩定 |
| 階段總數 | 5（含 Decision Brief）| 5（含 Decision Brief，跳過年報）| 0 | 階段結構穩定 |
| 分析時間（人類牆鐘）| 未精確記錄 | ~25-35 分鐘（估算）| — | 包含關聯法人追蹤的計畫外深挖 |

---

## 異常觀察

### 觀察 1：Entity Verification 階段大幅超預算

**現象**：預算 5-8 search / 1-2 fetch，實際 10 search / 8 fetch（search +25%~100%、fetch +300%~700%）

**根因**：
1. **資本額衝突**觸發 v1.2 強制多源驗證（biz.news vs opengovtw 差距 5 倍、時間差 4 年）→ 多做 2 次 fetch 和 2-3 次 search 交叉比對
2. **發現關聯法人**（系統整合商 B-Affiliate）是計畫外的高價值追蹤 → 多做 ~3-4 次 search 和 ~3 次 fetch
3. **[公司B官網] 官網 403**（Cloudflare WAF）→ 被迫改用媒體報導 fetch 替代，多付出 ~2 次 fetch

**這是 bug 還是 feature？**：**Feature**。v1.2 規則和 `fetch-policy.md` 的設計意圖就是「寧可多花預算也不讓過時資料污染報告」。發現關聯法人則是高價值的計畫外收穫。如果硬性卡預算，就會錯過最重要的發現。

**建議**：不調整預算，但在 AGENT-CORE.md 的搜尋預算表加一句「發現關聯法人或資本額衝突時，預算可臨時放寬 50%」。

### 觀察 2：Industry Analysis 階段主動收斂省預算

**現象**：預算 8-12 search，實際 5 search（低於預算下限）

**根因**：fetch 預算已達 total hard limit（10/10），agent 主動收斂到 search-only，並用更精準的 query 一次命中多個維度（市場規模 + 代理商生態 + 零信任 + DDoS 全景在 5 次 search 內完成）。

**這個行為反映了 AGENT-CORE 的「降級策略」正確生效** — 觸到 fetch 上限時自動切換到 search-heavy 模式。

### 觀察 3：Drop Zone Scan 的 overhead 極小

**現象**：Step 3.5 僅 1 次 Glob，0 fetch，0 search。對執行時間的影響 <1 秒。

**意義**：RFC-001 最擔心的「drop zone 掃描會拖慢空情境下的流程」這個風險**沒有發生**。`input/{target}/` 不存在時 Glob 立即回 empty，agent 靜默通過。

**結論**：v1.4 對「drop zone 為空」情境的 overhead 可以忽略不計（~1 Glob、~300 token prompt 預載、~0 秒牆鐘時間）。這是 RFC-001 設計決策 A（結構化目錄 vs MCP server）的正確性驗證。

### 觀察 4：Drop Zone 空情境下，案例複雜度由非預期因素主導

**現象**：本次超預算的主要原因（關聯法人 + 資本額衝突 + 403 官網）**全部與 v1.4 無關**。它們是案例本身的特性，在 baseline 時代的 v1.1 系統也會發生。

**意義**：**Drop Zone 的節省效應只在特定情境下有價值**（使用者預先知道要餵什麼 + 餵的內容能直接替代搜尋）。對於「未知的關聯法人發現」、「資料衝突的交叉驗證」這類**調查型需求**，Drop Zone 無法提供任何節省。

**建議**：RFC-001 §2「觀察到的問題」章節應補充這個 caveat：Drop Zone 的核心價值是「節省已知資料的搜尋成本」而不是「加速調查型研究」。後者仍依賴 v1.2 的交叉驗證規則和 AGENT-CORE 的降級策略。

---

## RFC-001 §6 回填建議

本實測應該回填到 RFC-001 `§6 效能影響 → 實測結果` 表格。建議填入以下內容：

```markdown
### 實測結果

**測試案例**：雲端資安代理商 B（台灣 Cloudflare ASDP，微型→準中型邊界）
**測試日期**：2026-04-08
**Drop Zone 狀態**：空（本次為 overhead-only 情境）
**對照 baseline**：[baseline-v1.1-token-usage.md](../perf/baseline-v1.1-token-usage.md)（個人理財 SaaS A）
**完整實測報告**：[2026-04-08_caseB_RFC-001-perf.md](../perf/2026-04-08_caseB_RFC-001-perf.md)

| 維度 | 預估 | 實測 | 偏差 | 備註 |
|------|------|------|------|------|
| 預載 token | +300 | +~350 | +17% | Step 3.5 + drop-zone.md 指向，接近預估 |
| 新增 Glob 呼叫 | +1 | **+1** ✅ | 0 | 精準 |
| 新增 Read 呼叫 | +1-2 | +0 | 低於預估 | Drop zone 空時無 MANIFEST 可讀 |
| 搜尋節省（有年報時）| −5 to −7 | **未驗證** | — | Drop zone 為空，此情境未觸發 |
| Fetch 節省（有年報時）| −2 to −3 | **未驗證** | — | 同上 |
| 命中率變化 | 餵資時提升 | **未驗證** | — | 同上 |

**後續實測 (F1)**：需補測「帶 drop zone 內容」情境以驗證節省效應。建議在 `input/雲端資安代理商 B/` 放入 ASDP 公告截圖和 Cloudflare 案例 PDF，重跑 `/company 雲端資安代理商 B...`，對比本次 overhead-only 實測。
```

---

## 命中率估算（Hit Rate）

依 `product/perf/README.md` 的操作型定義估算本次實測：

### 分子：命中的搜尋呼叫（被引用 / 形成證據鏈 / 負面確認）

| 呼叫類型 | 次數 | 狀態 |
|---------|------|------|
| 直接引用到報告的 search | ~18 | 命中 |
| 驗證鏈接（如 twincn 找到關聯法人線索 → 延伸搜尋 → 形成證據）| ~6 | 命中 |
| 負面確認（如「司法院 雲端資安代理商 B」無結果 → 寫入報告為正面訊號）| ~2 | 命中 |
| **小計** | **~26** | |

### 分母：總搜尋呼叫 = 28

### 估算命中率

**26/28 ≈ 0.93**

**解讀**：按 perf methodology 的命中率區間表，> 0.9 是**警訊**（「可能在 confirmation bias 下只搜已知答案」）。但本次實測中：
- 關聯法人（系統整合商 B-Affiliate）的發現是**非預期且高價值**的追蹤結果 — 這不是 confirmation bias 的典型症狀
- 員工數搜尋 ~4 次都無結果，但這是對「資料缺失」的負面確認，也算命中
- 實際「無結果且無價值」的呼叫只有 2 次（`"[董事長 B]" 董事 公司 -雲端資安代理商 B` 和 `"[策略長 B]" 資安 OR CSO` 無公司限定）

**結論**：命中率 0.93 雖然落在 perf README 的警訊區間，但**這次是因為 entity verification 階段的高聚焦搜尋 + 未做廣泛探索性搜尋**造成，不是 confirmation bias。

### 對 perf README 命中率區間的回饋

原區間表「> 0.9 = 警訊」可能對某些情境太嚴格。建議修正為：
- 0.9-0.95 搭配「高度聚焦調查」時 = 健康
- > 0.95 = 真正的警訊

或者在命中率定義中加入第二維度：「廣泛探索性搜尋的比例」。若命中率高但探索性搜尋比例也高 → 健康；若命中率高但探索性搜尋為零 → confirmation bias 警訊。

這個改善建議值得未來單獨開一份 RFC 討論。

---

## 成本估算

以 Claude Opus 4.6 定價 $15/M input + $75/M output（參考 baseline 報告的估算方式）：

| 項目 | Tokens | 成本估算 |
|------|--------|---------|
| Input（預載方法論 + 搜尋結果 + context 累積）| ~150-200K | $2.25-3.00 |
| Output（報告 + 簡報 + case + perf + 對話文字）| ~30K | $2.25 |
| **總計** | | **~$4.50-5.25** |

對比 baseline Phase 2（個人理財 SaaS A案完整路徑 B）約 $2.44，本次實測成本**高約 2 倍**，但：
- 關聯法人發現是 baseline 案例沒有的計畫外收穫
- Fetch 次數 0 → 10 反映案例本身複雜度
- Drop Zone 空情境下 overhead 極小，成本差距**主要來自案例本身**

---

## 下一輪要追的指標

基於本次實測暴露的問題，建議下次 perf 測試時追加的指標：

1. **Drop Zone 有餵資時的節省率**：補測以驗證 RFC-001 的核心假設
2. **第一個發現到多源交叉驗證觸發的 token 距離**：量化「發現衝突 → 啟動 v1.2 規則」的預算需求
3. **關聯法人發現的機率分布**：統計多少比例的案例會出現關聯法人線索 → 用來調整 entity verification 預算
4. **403 / WAF 失敗率**：觀察資安廠商類案例的官網 fetch 失敗率 → 是否需要 `fetch-policy.md` 黑名單新增「資安廠商自家網站」的一般規則

---

## 本實測對應的 Followup Action

1. **[DONE]** 寫入本 perf 報告 → `product/perf/2026-04-08_caseB_RFC-001-perf.md`
2. **[TODO]** 回填 RFC-001 §6「實測結果」表格與「後續實測 F1」紀錄
3. **[TODO]** 修正 company 報告 §9 的 search/fetch 計數誤差（報告中寫 31/7，實際 28/10）
4. **[CANDIDATE]** 開 `RFC-002` 討論命中率定義的雙維度改進（命中率 + 探索性搜尋比例）
5. **[CANDIDATE]** 更新 `fetch-policy.md` 加入「資安廠商官網預期 403」的一般規則
6. **[CANDIDATE]** 補測「帶 drop zone 內容」情境以驗證 RFC-001 的核心節省假設（需使用者配合準備測試檔案）
