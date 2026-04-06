# 年報來源登記表（Annual Report Source Registry）

Agent 進入年報解析階段前，查此表取得目標公司所在市場的年報來源。

## 各市場年報來源

### 台灣

| 來源 | URL 格式 | 取得方式 | 備註 |
|------|---------|---------|------|
| 公司 IR 網站 | `ir.[公司域名]` 或 `[公司官網]/investors` | web_search `"[公司名] 投資人關係 年報"` → web_fetch PDF | **優先使用**；通常有歷年年報 PDF 下載 |
| MOPS 公開資訊觀測站 | `mops.twse.com.tw` | web_search `"[公司名] site:mops.twse.com.tw 年報"` | 官方法定申報平台；部分需 JS 渲染，fetch 可能失敗 |

**台灣年報結構（標準格式）**：
- 壹、致股東報告書（業績摘要+展望）
- 貳、公司治理報告（董監事+薪酬+治理）
- 參、募資情形（股本+股東名單+配息）
- 肆、營運概況（營收拆分+產業概況+研發+進銷貨客戶+員工+重大合約）
- 伍、財務狀況（損益表+資產負債表+現金流+風險）
- 陸、特別記載事項

**關鍵頁面定位提示**：
- 營收拆分 → 肆、營運概況 → 業務內容 → 所營業務之營業比重
- 進銷貨集中度 → 肆、營運概況 → 市場及產銷概況 → 主要進銷貨客戶名單
- 員工數 → 肆、營運概況 → 從業員工
- 重大合約 → 肆、營運概況最末 → 重要契約
- 股東名單 → 參、募資情形 → 主要股東名單
- 損益表 → 伍、財務狀況 → 財務績效比較分析表

### 美國

| 來源 | URL 格式 | 取得方式 | 備註 |
|------|---------|---------|------|
| SEC EDGAR | `sec.gov/cgi-bin/browse-edgar?action=getcompany&company=[name]&type=10-K` | web_search `"[company] 10-K SEC filing"` → web_fetch | 法定申報；10-K 為年報，10-Q 為季報 |
| 公司 IR 網站 | `[公司官網]/investors` 或 `/sec-filings` | web_search `"[company] investor relations annual report"` | 通常提供 PDF 格式下載 |

### 日本

| 來源 | URL 格式 | 取得方式 | 備註 |
|------|---------|---------|------|
| EDINET | `disclosure.edinet-fsa.go.jp` | web_search `"[会社名] 有価証券報告書 EDINET"` | 法定申報；日文 |
| 公司 IR 網站 | — | web_search `"[company] IR 有価証券報告書"` | 日本上市公司通常有完整 IR 專區 |

### 韓國

| 來源 | URL 格式 | 取得方式 | 備註 |
|------|---------|---------|------|
| DART | `dart.fss.or.kr` | web_search `"[회사명] 사업보고서 DART"` | 法定申報；韓文 |
| 公司 IR 網站 | — | web_search `"[company] investor relations annual report"` | 大型韓企通常有英文版 |

### 香港

| 來源 | URL 格式 | 取得方式 | 備註 |
|------|---------|---------|------|
| HKEXnews 披露易 | `hkexnews.hk` | web_search `"[公司名] annual report site:hkexnews.hk"` | 法定申報 |
| 公司 IR 網站 | — | web_search `"[company] investor relations 年報"` | — |

### 中國

| 來源 | URL 格式 | 取得方式 | 備註 |
|------|---------|---------|------|
| 巨潮資訊 | `cninfo.com.cn` | web_search `"[公司名] 年度报告 site:cninfo.com.cn"` | A 股法定申報平台 |
| 公司 IR 網站 | — | — | — |

## 通用搜尋模式

如果上述市場來源均未命中，使用以下通用搜尋：

```
"[公司名] annual report [年份] filetype:pdf"
"[公司名] investor relations"
"[公司名] 年報 [年份]"
"[公司名] [年份] 年度報告"
```

## 已知限制

- MOPS（台灣）部分頁面需 JS 渲染，web_fetch 可能只取得空白框架
- EDGAR（美國）10-K 為大型 HTML 檔案，fetch 可能截斷；優先找 PDF 版本
- EDINET/DART 為非英語平台，需對應語言搜尋
- 部分公司 IR 網站的 PDF 連結需經 redirect，web_fetch 需 follow redirect

## 維護規則

同 `fetch-policy.md`：每次分析中遇到新的年報來源或 fetch 失敗，在案例沉澱（`references/cases/`）中記錄，定期更新此表。
