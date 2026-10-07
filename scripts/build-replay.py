#!/usr/bin/env python3
"""
調查重播 — 把 cases/{目標}/replay-log.jsonl 注入重播範本，產出動畫 HTML。

Usage:
    python3 scripts/build-replay.py "cases/{目標名稱}"

輸入：cases/{目標名稱}/replay-log.jsonl
    第 1 行：{"meta": {"title", "subtitle", "date": "YYYY-MM-DD", "phases": [["A","開工"], ...],
              "cols"?: [[key, 欄名], ...], "counters"?: [[key, 標籤], ...]}}
    其餘每行一個步驟：{"ph", "k", "tools", "t", "did", "got", "why", "d"?, "add"?, "upd"?, "hl"?}
    欄位說明見 .claude/skills/company/SKILL.md「調查日誌」。

輸出：cases/{目標名稱}/{date}_{目標名稱}_replay.html
"""

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
TEMPLATE_PATH = PROJECT_ROOT / "references" / "templates" / "investigation-replay.html"
PLACEHOLDER = "/*__REPLAY_DATA__*/null"

KINDS = {"act", "judge", "infer", "persist", "quit"}
REQUIRED = ("ph", "k", "t", "did", "got", "why")


def load_log(log_path: Path):
    lines = [l for l in log_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not lines:
        sys.exit(f"空的日誌：{log_path}")
    first = json.loads(lines[0])
    if "meta" not in first:
        sys.exit("第 1 行必須是 {\"meta\": {...}}")
    meta = first["meta"]
    for key in ("title", "date", "phases"):
        if key not in meta:
            sys.exit(f"meta 缺少 {key}")
    steps = [json.loads(l) for l in lines[1:]]
    return meta, steps


def validate(meta, steps):
    phase_keys = {p[0] for p in meta["phases"]}
    card_ids = set()
    errors = []
    for i, s in enumerate(steps, 1):
        for key in REQUIRED:
            if not s.get(key):
                errors.append(f"第 {i} 步缺少 {key}")
        if s.get("k") not in KINDS:
            errors.append(f"第 {i} 步 k={s.get('k')!r} 不是 {sorted(KINDS)} 之一")
        if s.get("ph") not in phase_keys:
            errors.append(f"第 {i} 步 ph={s.get('ph')!r} 不在 meta.phases")
        for card in s.get("add", []):
            card_ids.add(card[0])
        for ref in [u[0] for u in s.get("upd", [])] + s.get("hl", []):
            if ref not in card_ids:
                errors.append(f"第 {i} 步引用了還沒出現的線索 {ref!r}")
    if errors:
        sys.exit("日誌驗證失敗：\n" + "\n".join(errors))


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    case_dir = Path(sys.argv[1]).resolve()
    log_path = case_dir / "replay-log.jsonl"
    if not log_path.exists():
        sys.exit(f"找不到 {log_path}")

    meta, steps = load_log(log_path)
    validate(meta, steps)

    payload = json.dumps({"meta": meta, "steps": steps}, ensure_ascii=False).replace("</", "<\\/")
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    if PLACEHOLDER not in template:
        sys.exit(f"範本中找不到注入點 {PLACEHOLDER}")
    html = template.replace(PLACEHOLDER, payload, 1)
    html = html.replace("<title>調查重播</title>", f"<title>{meta['title']}</title>", 1)

    out_path = case_dir / f"{meta['date']}_{case_dir.name}_replay.html"
    out_path.write_text(html, encoding="utf-8")

    totals = {}
    for s in steps:
        for k, v in s.get("d", {}).items():
            totals[k] = totals.get(k, 0) + v
    print(f"已產出 {out_path.relative_to(PROJECT_ROOT)}")
    print(f"步驟 {len(steps)}，計數 {totals}")


if __name__ == "__main__":
    main()
