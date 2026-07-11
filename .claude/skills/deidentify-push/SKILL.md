---
name: deidentify-push
description: >
  推 public repo 前的去識別化 SOP。使用者說「去識別化」「把公司名換成代號」
  「git history 要清乾淨」「推上 GitHub 前先掃一遍」「release notes 有真實公司名」
  「repo 要公開、敏感資料清掉」時觸發。
  提供從盤點、代號映射、history 改寫、force push 到 protection 還原的完整流程，
  避免多輪 tool call 反覆試錯。
allowed-tools: Bash Read Edit Write Grep Glob
---

# De-identify & Push — 公開 Repo 前去識別化 SOP

## 目的

把敏感識別資訊（真實公司名、人名、統編、地址等）從 repo 裡清乾淨——包含**工作區檔案、commit message、release notes、git history**——再推上 public GitHub。

設計原則：**一次盤點、一次代號定案、一次改寫、一次驗證**。避免像初次處理時的多輪追加與 tool call 浪費。

## 什麼時候用這個 skill

- 把私有/混用 repo 改公開前
- 已公開但發現漏掉敏感資料要補救
- 每次發 release 前的例行檢查（可以只跑步驟 1 + 5）

## 什麼時候**不**該用

- repo 本來就從零公開、沒有敏感資料累積 → 直接 push
- 只想改最新 commit 的敏感字串 → 用一般 Edit + amend 即可（除非 tag/release 已建立）

---

## 核心流程（6 步）

### Step 1 — 一次性盤點

**一個 grep 把所有洩漏點抓出來**（檔案內容 + git history + commit messages + release notes）：

```bash
# 1a. 工作區 + git history 檔案內容
git log --all -p | grep -oE "<pattern1>|<pattern2>|..." | sort -u

# 1b. commit messages（--replace-text 不會動到這裡）
git log --all --pretty="%s%n%b" | grep -oE "<patterns>" | sort -u

# 1c. release notes
for tag in $(gh release list --json tagName -q '.[].tagName'); do
  gh release view "$tag" --json body -q '.body'
done | grep -oE "<patterns>" | sort -u

# 1d. 同步掃被 release notes 連結到的文件（CHANGELOG.md、RFC、docs/）
grep -rE "<patterns>" . --exclude-dir=.git --exclude-dir=node_modules
```

**注意盤點範圍**——不要只看 release notes。release notes 往往連結到 `CHANGELOG.md` / `RFC-*.md`，這些也是公開可見面。被 `.gitignore` 的目錄（例如 `cases/`、`output/`）可以豁免，但要**驗證 gitignore 規則從第一個 commit 就在**——否則歷史 commit 可能還留有舊檔。

### Step 2 — 一次性定案代號表

**不要做完一個再加一個**。列出所有實體，一次決定代號：

| 類型 | 代號模式 | 範例 |
|------|---------|------|
| 公司（有產業特徵） | `{領域} {字母}` | 雲端整合代理商 D / 上市遊戲營運商 C |
| 公司（產業不重要） | `微型公司 {字母}` | 微型公司 F |
| 人名 | `代表人 {字母}` 或 `前代表人 X` | 代表人 Y |
| 關聯法人 | `關聯法人 {字母}{數字}` | 關聯法人 X1 / X2 |
| 統編 / ID | `XXXXXXXX` | — |
| 地址 | `某縣市某區` | — |

**字母配置原則**：延續專案既有代號體系（例如本 repo v1.3/v1.4 已有 A/B/C），新代號從 D 接下去，避免混淆。

**避免的命名陷阱**：
- `X` 和 `X1` 容易混淆（前者是人、後者是關聯法人）→ 改用 `代表人 Y`、`法人 Y1`
- 代號裡出現真實部分字（例：「範例」→「範 D」）→ 要完全替換

把代號表存成 `replacements.txt`，格式符合 `git filter-repo --replace-text`：

```text
範例科技==>雲端整合代理商 D
12345678==>XXXXXXXX
王小明==>代表人 X
...
```

**長字串放前面**：`範例科技股份有限公司` 要在 `範例` 之前，否則會先被短 pattern 替換掉後綴。

### Step 3 — 環境前檢

動手前**先確認**以下三件，避免中途卡住：

```bash
# 3a. filter-repo 存在
which git-filter-repo || brew install git-filter-repo

# 3b. branch protection 狀態
gh api repos/{owner}/{repo}/branches/main/protection > /tmp/branch-protection-backup.json

# 3c. remote 狀態 + 備份
git remote -v
cp -r . /tmp/$(basename $PWD)-backup-$(date +%s)
```

若 `lock_branch: true` 或 `allow_force_pushes: false`，記下完整 JSON——稍後 push 前暫時解除、push 後還原。

### Step 4 — 單次 filter-repo 改寫

**兩個 flag 一起跑**（分兩次會浪費一遍 parse history）：

```bash
echo "Y" | git filter-repo \
  --replace-text /tmp/replacements.txt \
  --replace-message /tmp/replacements.txt \
  --force
```

- `--replace-text` 改檔案內容
- `--replace-message` 改 commit message
- `echo "Y" |` 跳過「是否延續上次」互動 prompt
- `--force` 必要（filter-repo 預設保守拒絕跑第二次）

filter-repo 會**移除 remote**（safety feature），跑完後要手動 re-add：

```bash
git remote add origin https://github.com/{owner}/{repo}.git
```

### Step 5 — 先修 release notes（仍在 GitHub 上）+ 現存檔案

release notes 是 GitHub 端資料，**filter-repo 動不到**。用 `gh release edit` 改：

```bash
gh release edit v1.8 --notes "$(cat <<'EOF'
...新版內容...
EOF
)"
```

檔案層面的 commit（就是「現在的 working tree 也要乾淨」）應該在 Step 4 之前就 commit 一次——這樣 filter-repo 既改歷史、也保留最新 commit 為已修正狀態。

### Step 6 — Push + 驗證

```bash
# 6a. 暫時解除 branch protection（若有）
gh api -X DELETE repos/{owner}/{repo}/branches/main/protection

# 6b. Force push main + tags
git push origin main --force
git push origin --tags --force

# 6c. 還原 protection（把 Step 3 的 backup 還原）
gh api -X PUT repos/{owner}/{repo}/branches/main/protection --input /tmp/restore-protection.json

# 6d. 最終驗證（一次就好）
git log --all -p | grep -oE "<patterns>" | sort -u && echo "should be empty"
gh release view vX.Y --json body -q '.body' | grep -E "<patterns>"
```

`--force-with-lease` 在剛 re-add remote 時會因為 stale info 被拒，用 `--force` 即可（前面已手動備份 + 盤點過，此處 force 是安全的）。

---

## 重要提醒

### filter-repo 的副作用

- **移除 origin remote**——必須手動 re-add
- **重寫所有 commit hash**——合作者必須重新 clone（本人專案沒差）
- **重寫 tag**——release 會指向新 SHA，GitHub release notes 本體不變但 source code zip 會重產

### GitHub 快取

force push 後舊 commits 仍在 GitHub 內部約 **90 天**可透過 `git fetch <old-sha>` 取得。要徹底清除需聯絡 GitHub Support。若敏感度極高，考慮：

1. 刪除 repo 重建（連 fork 一起被 orphan）
2. 改 private 一段時間後再公開

### `.gitignore` 的盲點

被 gitignore 的目錄**只有從加入 gitignore 後的 commit** 會豁免。如果檔案曾經被 commit 過才改 gitignore，git history 裡還有。要一併清。

### Release notes 的連結效應

release notes 裡的相對連結（`[RFC-004](product/rfcs/RFC-004.md)`）指向的檔案也是公開面，盤點時別漏。

---

## Anti-patterns（初次處理時踩過的坑）

1. **切批掃 release**：`gh release view` 一個一個看 → 改成 `for tag in $(gh release list ...)` 批次
2. **Edit 前 Read 過量**：grep 已定位好的字串不需要再 Read 上下文，直接 Edit
3. **代號追加**：先決一個再加一個 → 後面映射表內部不一致，要一次定完
4. **filter-repo 跑兩遍**：`--replace-text` 跑完才發現 commit message 沒清 → 兩個 flag 一起跑
5. **Push 才發現 protection**：動手前就該 `gh api .../protection` 看

---

## 快速啟動模板

使用者說「幫我清乾淨再 push」時，按這個順序問：

1. **要清什麼**？（列敏感字串或指向代號表）
2. **代號怎麼配**？（領域代號 / 數字匿名 / 直接刪除）
3. **是否 force push**？（history 改寫是破壞性動作，需明確授權）
4. **branch protection 狀態**？（先查 + 備份）

確認後一次跑完 Step 1–6，最後把備份路徑告訴使用者以便 rollback。
