# product/ — PM 工件層

> Enterprise Tomb Raider 的產品/工程文件中心。Agent **不應載入此目錄的任何檔案**——這裡的內容是給人類讀者（產品迭代決策者、作品集評估者）看的。

## 為什麼有這個目錄

這個資料夾在 v1.4 引入，目的是把散落各處的設計、架構、效能、變更紀錄集中到一個有結構的位置，讓專案的迭代過程本身**可審視、可學習、可作為作品集呈現**。

完整動機與設計原則見 [`PRD.md`](PRD.md)。

## 目錄地圖

```
product/
├── README.md              # 本檔，導讀
├── PRD.md                 # 主 PRD：產品定位、目標、原則、路線圖
├── architecture.md        # 系統架構文件（v1.0 起維護）
├── flow-diagram.md        # 系統流程圖（Mermaid）
├── design-rationale.md    # 設計意圖與方法論解釋（簡短靜態筆記）
├── rfcs/                  # 設計變更紀錄（每次迭代一份）
│   ├── README.md          # RFC 索引
│   ├── _RFC-template.md   # 模板（複製後填寫）
│   └── RFC-XXX-*.md       # 各份 RFC
└── perf/                  # 效能追蹤
    ├── README.md          # 效能追蹤方法論、命中率定義
    ├── baseline-v1.1-*.md # v1.1 baseline 報告
    └── {date}_*_perf.md   # 後續實測報告
```

## 誰應該讀哪一個

| 你的目的 | 從哪開始讀 |
|---------|----------|
| **第一次認識這個專案** | 從根目錄 `README.md` 開始，再讀本檔 → `PRD.md` → `architecture.md` |
| **想了解某個具體設計為什麼這樣做** | 找對應的 [`rfcs/`](rfcs/) |
| **想知道一次變更花了多少效能代價** | 找對應 RFC 的 §6 → 看 [`perf/`](perf/) 的實測報告 |
| **想理解產品定位、不關心實作細節** | 只讀 [`PRD.md`](PRD.md) |
| **要寫新的設計變更** | 複製 [`rfcs/_RFC-template.md`](rfcs/_RFC-template.md)，編號接續 |
| **要更新架構** | 改 [`architecture.md`](architecture.md) 和（如需要）[`flow-diagram.md`](flow-diagram.md)，並在對應 RFC 註記 |

## 與 CHANGELOG.md 的分工

| 文件 | 視角 | 粒度 | 維護頻率 |
|------|------|------|---------|
| `CHANGELOG.md`（根目錄） | 使用者視角的 release notes | 每個版本一段 | 每次 release |
| `product/rfcs/` | 工程/PM 視角的決策過程 | 每個有意義的設計變更一份 | 每次有意義的迭代 |
| `product/perf/` | 量化視角的效能影響 | 每個重要 RFC 一份實測 | 重要 RFC 實作後 |

三者互相連結：CHANGELOG 的 entry 連到對應 RFC，RFC 連到對應的 perf 報告。

## 維護規則

- **PRD 是 living document**。每次大版本（v1.x）更新時同步「迭代路線圖」「成功指標」段落。
- **RFC 編號只增不減**。即使被 superseded 也保留原檔，只更新 status 並在新的 RFC 標註「Supersedes RFC-XXX」。
- **architecture.md 隨架構變動更新**。流程圖（flow-diagram.md）只在實際資料流改變時更新，避免太頻繁。
- **perf 報告不要每個 RFC 都寫**。挑值得的（觸及搜尋迴圈、預算、新階段的變更），避免測試成本壓過設計成本。完整原則見 [`perf/README.md`](perf/README.md)。
