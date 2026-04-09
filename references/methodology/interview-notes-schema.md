# 訪談筆記結構化 Schema

> 供使用者在 `cases/{target}/input/` 丟入訪談筆記時使用的建議格式。
> 也可配合 `/meeting` skill 把逐字稿結構化後再丟入。

## YAML Frontmatter

```yaml
---
type: interview-notes
date: YYYY-MM-DD
source: headhunter | internal-contact | interview | conference | other
counterpart: "[人物代稱，非全名——避免機敏資料外洩]"
topics: [薪資, 團隊規模, 產品方向, 離職率, 管理風格, ...]
confidence: low | medium | high
related-report: "[對應的 cases/{target}/ 報告檔名]"
---
```

### confidence 欄位說明

| 等級 | 意義 | Agent 處理方式 |
|------|------|---------------|
| `low` | 道聽途說、二手轉述、對方可能有利益衝突 | 所有事實標 `[推測，待驗證]`，不消耗搜尋預算驗證 |
| `medium` | 直接對話、對方為當事人或接近當事人 | 事實標 `[部分證據]`，關鍵項消耗搜尋預算交叉驗證 |
| `high` | 對方有直接利害關係且無明顯隱瞞動機（如公司 HR 官方 offer） | 事實標 `[部分證據]`，搜尋驗證若一致可升為充分 |

## 正文建議結構

```markdown
## 關鍵資訊點

- [條列具體事實]
- [每項標明是對方直接陳述還是你的推論]

## 直接引述

- "..." — [對方說的原話，儘量保留原文語氣]
- "..." — [標註上下文]

## 我的觀察 / 推論

- [你自己的判斷和推論]
- [標明哪些是事實、哪些是推論]
```

## 檔名建議

```
{source}-{date}.md
```

範例：
- `headhunter-2026-04-09.md`
- `interview-round1-2026-04-15.md`
- `conference-notes-2026-05-01.md`

## 與 `/supplement` 的整合

1. 把訪談筆記存入 `cases/{target}/input/`
2. 執行 `/supplement {target}`
3. Agent 會：
   - 自動辨識 `type: interview-notes` 的 frontmatter
   - 根據 `confidence` 等級決定證據處理方式
   - 將新資訊與既有報告比對，產出 Supplement Memo
