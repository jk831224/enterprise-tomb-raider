# 產業特殊資料源矩陣

Agent 進入產業分析前，查此表取得對應產業的高價值資料源。

| 產業 | 特殊資料源 | 搜尋方式 |
|------|-----------|---------|
| **AdTech** | ads.txt（媒體授權賣方） | `web_fetch https://[媒體域名]/ads.txt` 搜目標公司名 |
| | BuiltWith / SimilarTech | `[公司] site:builtwith.com` |
| | SDK 偵測 | `[公司SDK名] site:github.com OR npm` |
| **SaaS** | G2 / Capterra 評價 | `[公司] site:g2.com OR site:capterra.com` |
| | Product Hunt | `[公司] site:producthunt.com` |
| | GitHub 開源活躍度 | `[公司] site:github.com` |
| **製造業** | 海關進出口資料 | `[公司] 進出口 OR 海關` |
| | 政府標案 | `[公司] site:web.pcc.gov.tw` `[公司] 決標` |
| | ISO / 品質認證 | `[公司] ISO OR 認證` |
| **金融** | 金管會公告 | `[公司] site:fsc.gov.tw` |
| | 保險局/銀行局裁罰 | `[公司] 裁罰 OR 罰鍰` |
| **餐飲零售** | Google Maps 評價 | `[公司] site:google.com/maps` |
| | 食藥署稽核 | `[公司] site:fda.gov.tw` |
| | 展店數 | `[公司] 門市數 OR 分店` |

## 通用高價值資料源（所有產業）

| 資料源 | 搜尋方式 | 補什麼 |
|--------|---------|--------|
| 求職平台 | `[公司] site:cake.me OR yourator.co OR 104.com.tw` | 員工數、部門、技術棧、薪資帶 |
| SimilarWeb | `[公司官網] site:similarweb.com` | 流量趨勢 |
| Wayback Machine | `web.archive.org/web/*/[公司官網]` | 官網歷史快照 |
| 政府電子採購網 | `[公司] site:web.pcc.gov.tw` | B2G 營收來源 |
| TIPO 專利商標 | `[公司] 專利 site:twpat.tipo.gov.tw` `[公司] 商標` | 技術壁壘 |
