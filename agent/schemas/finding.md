# Finding Schema — Explorer 回傳格式

> 對抗式深挖輪（v2.0）中，每個 explorer subagent 回傳的結構化發現格式。
> 設計目的：subagent 隔離執行但**證據鏈不斷**——每個結論都帶原始 URL 與原文截句回主 context（RFC-007 G4）。

## JSON Schema

每個 explorer 的最終訊息必須是一個 JSON array，元素結構如下：

```json
{
  "claim": "一句話結論陳述（具體、可驗證）",
  "dimension": "entity | stakeholder | industry | finance | legal | operations | reputation | network",
  "source_url": "來源連結（必填；無 URL 的發現會被棄用）",
  "source_title": "來源標題或頁面名稱",
  "source_date": "來源發布日期 YYYY-MM-DD；不明則填 \"unknown\"",
  "source_quote": "原文截句（≤200 字，保留證據鏈可追溯性）",
  "evidence_level": "充分 | 部分 | 推測 | 缺失",
  "cross_refs": ["交叉驗證的其他來源 URL，可為空 array"],
  "novelty": "new | corroborates | conflicts",
  "conflict_with": "若 novelty=conflicts，填主報告中矛盾的結論原文；否則填 null"
}
```

## 欄位規則

| 欄位 | 規則 |
|------|------|
| `claim` | 一個 finding 一個結論。複合發現拆成多個 finding |
| `source_url` | **必填**。沒有可引用來源的「發現」不是發現，是猜測——不要回傳 |
| `source_quote` | 從來源原文擷取，不可改寫。snippet 也算原文 |
| `evidence_level` | 依 `.claude/rules/output-quality.md` 四級標準自評：單一來源最高只能標「部分」；有 `cross_refs` 至少一個獨立來源才可標「充分」 |
| `novelty` | `new`=主報告未覆蓋；`corroborates`=佐證既有結論（會觸發證據升級評估）；`conflicts`=與主報告矛盾（會進衝突表） |

## Negative finding（重要）

「查無結果」本身是有價值的發現。例如司法院裁判書查無公開訴訟＝負面資訊排除訊號。此時：

```json
{
  "claim": "司法院裁判書系統查無 [公司名] 相關公開判決（搜尋詞：...）",
  "source_url": "搜尋結果頁或系統 URL",
  "source_quote": "（無結果）",
  "evidence_level": "部分",
  "novelty": "new"
}
```

## Orchestrator 端驗證規則

主 context 收到 Finding[] 後逐筆檢查：

1. 缺 `claim` / `source_url` / `evidence_level` 任一 → 棄用該筆，記入深挖輪紀錄「棄用 N 筆（缺必填欄位）」
2. `evidence_level` 標「充分」但 `cross_refs` 為空 → 降為「部分」
3. JSON 解析失敗 → 要求該 explorer 重試一次；再失敗則放棄該 explorer，報告標註該來源類未完成
