#!/usr/bin/env python3
"""
Cases Registry — 掃描 case reports，維護 CRM 式企業分類 DB。

Usage:
    python scripts/sync-registry.py sync                  # 掃描 → 更新 registry + 生成 index
    python scripts/sync-registry.py show                  # 印出全部企業摘要表
    python scripts/sync-registry.py show --sector 科技     # 篩選 sector
    python scripts/sync-registry.py show --size micro      # 篩選 size
    python scripts/sync-registry.py show --risk critical   # 篩選 risk
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
CASES_DIR = PROJECT_ROOT / "cases"
REGISTRY_PATH = CASES_DIR / "_registry.json"
INDEX_PATH = CASES_DIR / "_index.md"

SCHEMA_VERSION = "1.0"

VALID_SIZES = {"micro", "small", "medium", "large"}
VALID_LISTINGS = {"private", "public", "otc"}
VALID_RISKS = {"critical", "high", "medium", "low"}

RISK_EMOJI = {
    "critical": "\U0001f534",  # 🔴
    "high": "\U0001f7e0",      # 🟠
    "medium": "\U0001f7e1",    # 🟡
    "low": "\U0001f7e2",       # 🟢
}

SIZE_ORDER = {"micro": 0, "small": 1, "medium": 2, "large": 3}

# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def find_report(case_dir: Path) -> Path | None:
    """Find the primary company-report or industry-report in a case dir."""
    candidates = []
    for f in case_dir.iterdir():
        if f.is_file() and f.suffix == ".md":
            name_lower = f.name.lower()
            if "company-report" in name_lower or "industry-report" in name_lower:
                candidates.append(f)
    if not candidates:
        return None
    # prefer the one with a date prefix (newest first)
    candidates.sort(key=lambda p: p.name, reverse=True)
    return candidates[0]


def find_brief(case_dir: Path) -> Path | None:
    """Find the decision-brief in a case dir."""
    for f in case_dir.iterdir():
        if f.is_file() and f.suffix == ".md" and "decision-brief" in f.name.lower():
            return f
    return None


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_metadata_field(text: str, field: str) -> str | None:
    """Extract a metadata field value from report text (handles 3 formats)."""
    # Format 1: markdown table  | **field** | value |
    m = re.search(
        rf"\|\s*\**{re.escape(field)}\**\s*\|\s*(.+?)\s*\|", text
    )
    if m:
        return m.group(1).strip()
    # Format 2: bullet  - **field**：value
    m = re.search(
        rf"[-*]\s*\**{re.escape(field)}\**\s*[：:]\s*(.+)", text
    )
    if m:
        return m.group(1).strip()
    # Format 3: inline  **field**：value
    m = re.search(
        rf"\*\*{re.escape(field)}\*\*\s*[：:]\s*(.+)", text
    )
    if m:
        return m.group(1).strip()
    return None


def extract_summary(text: str) -> str | None:
    """Extract the 摘要 section (first paragraph after heading)."""
    m = re.search(r"##\s*\d*\.?\s*摘要\s*\n+(.+?)(?:\n\n|\n---|\n##)", text, re.DOTALL)
    if m:
        raw = m.group(1).strip()
        # take first 3 sentences (split by 。)
        sentences = raw.split("。")
        if len(sentences) > 3:
            return "。".join(sentences[:3]) + "。"
        return raw
    return None


def extract_table_field(text: str, field_pattern: str) -> str | None:
    """Extract a value from a 2-column markdown table row."""
    m = re.search(
        rf"\|\s*(?:{field_pattern})\s*\|\s*(.+?)\s*\|", text
    )
    if m:
        val = m.group(1).strip()
        # strip bold markers
        val = re.sub(r"\*\*(.+?)\*\*", r"\1", val)
        return val if val and val != "[資料缺失]" else None
    return None


def extract_tax_ids(text: str) -> list[str]:
    """Extract 統一編號 values from the report."""
    ids = set()
    for m in re.finditer(r"(?:統一編號|統編)[^\d]*(\d{8})", text):
        ids.add(m.group(1))
    # also from table rows with 8-digit numbers labeled as 統一編號
    for m in re.finditer(r"\|\s*統一編號\s*\|\s*(\d{8})", text):
        ids.add(m.group(1))
    return sorted(ids)


def extract_capital(text: str) -> int | None:
    """Extract 資本額 in NTD integer."""
    for pattern in [
        r"資本額[^\d]*?([\d,]+)\s*(?:NTD|元|新台幣)",
        r"資本額[^\d]*?(?:NTD|NT\$)\s*([\d,]+)",
        r"資本額\s*\|\s*([\d,]+)",
    ]:
        m = re.search(pattern, text)
        if m:
            return int(m.group(1).replace(",", ""))
    # try "N 萬 NTD" or "N 億 NTD"
    m = re.search(r"資本額[^\d]*?([\d.]+)\s*萬", text)
    if m:
        return int(float(m.group(1)) * 10000)
    m = re.search(r"資本額[^\d]*?([\d.]+)\s*億", text)
    if m:
        return int(float(m.group(1)) * 100000000)
    return None


def parse_size(raw: str | None) -> str | None:
    """Normalize size classification."""
    if not raw:
        return None
    raw_lower = raw.lower()
    if "微型" in raw or "micro" in raw_lower:
        return "micro"
    if "大型" in raw or "large" in raw_lower or "上市" in raw:
        return "large"
    if "中型" in raw or "medium" in raw_lower:
        return "medium"
    if "small" in raw_lower:
        return "small"
    return None


def parse_listing(text: str) -> str:
    """Determine listing status from report text."""
    if re.search(r"上市|上櫃|public|listed", text, re.IGNORECASE):
        if re.search(r"非上市|未上市|private", text, re.IGNORECASE):
            return "private"
        return "public"
    return "private"


def slugify(name: str) -> str:
    """Generate a URL-safe slug from a company name."""
    # try to use English name if available
    ascii_part = re.sub(r"[^a-zA-Z0-9\s]", "", name)
    if len(ascii_part.strip()) > 2:
        return re.sub(r"\s+", "-", ascii_part.strip().lower())
    # fallback: use pinyin-ish or just hash
    return re.sub(r"\s+", "-", name.strip().replace("/", "-"))


def extract_version(text: str) -> str | None:
    """Extract latest version from Version History table."""
    versions = re.findall(r"\|\s*(v[\d.]+)\s*\|", text)
    if versions:
        return versions[-1]
    return None


# ---------------------------------------------------------------------------
# Core: scan a single case
# ---------------------------------------------------------------------------

def scan_case(case_dir: Path) -> dict | None:
    """Parse a case directory and return a registry entry dict."""
    report_path = find_report(case_dir)
    if not report_path:
        return None

    text = read_text(report_path)
    brief_path = find_brief(case_dir)

    dir_name = case_dir.name

    # --- Metadata fields ---
    date_raw = extract_metadata_field(text, "分析日期")
    analysis_date = None
    if date_raw:
        # extract YYYY-MM-DD
        m = re.search(r"(\d{4}-\d{2}-\d{2})", date_raw)
        if m:
            analysis_date = m.group(1)

    size_raw = extract_metadata_field(text, "規模分類")
    route_raw = extract_metadata_field(text, "分析路徑")
    route = None
    if route_raw:
        m = re.match(r"([AB])", route_raw)
        if m:
            route = m.group(1)

    # --- Basic info ---
    name_zh = extract_table_field(text, r"登記名稱|法定名稱|公司名稱")
    if not name_zh:
        name_zh = dir_name

    name_en = extract_table_field(text, r"英文名[稱]?")
    tax_ids = extract_tax_ids(text)
    capital = extract_capital(text)

    employee_raw = extract_table_field(text, r"規模|員工")
    employee_range = None
    if employee_raw:
        m = re.search(r"(\d+[-–]\d+)", employee_raw)
        if m:
            employee_range = m.group(1).replace("–", "-")

    hq_raw = extract_table_field(text, r"總部|地址|營業地址")
    hq_city = None
    if hq_raw:
        for city in ["台北", "台中", "高雄", "新竹", "桃園", "台南"]:
            if city in hq_raw:
                hq_city = city
                break

    # --- Summary ---
    summary = extract_summary(text)
    version = extract_version(text)

    # --- Build entry ---
    entry = {
        "id": slugify(name_en or name_zh or dir_name),
        "dir_name": dir_name,
        "name_zh": name_zh,
        "name_en": name_en,
        "aliases": [],
        "tax_ids": tax_ids,
        "sector": None,
        "industry": None,
        "tags": [],
        "size": parse_size(size_raw),
        "listing": parse_listing(text),
        "employee_range": employee_range,
        "capital_ntd": capital,
        "hq_city": hq_city,
        "hq_country": "TW",
        "target_markets": [],
        "first_analyzed": analysis_date,
        "last_updated": analysis_date,
        "report_version": version or "v1.0",
        "route": route,
        "report_path": report_path.name,
        "brief_path": brief_path.name if brief_path else None,
        "risk_level": None,
        "verdict": summary[:120] + "..." if summary and len(summary) > 120 else summary,
        "red_flags": [],
        "opportunities": [],
        "revenue_estimate": None,
        "revenue_confidence": "unknown",
        "funding_stage": None,
    }

    return entry


# ---------------------------------------------------------------------------
# Registry I/O
# ---------------------------------------------------------------------------

def load_registry() -> dict:
    if REGISTRY_PATH.exists():
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return {"schema_version": SCHEMA_VERSION, "last_synced": None, "companies": []}


def save_registry(registry: dict) -> None:
    registry["last_synced"] = datetime.now().isoformat(timespec="seconds")
    REGISTRY_PATH.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def merge_entry(existing: dict, scanned: dict) -> dict:
    """Merge scanned data into existing entry, preserving manual enrichments.

    Strategy:
    - ALWAYS update from scan: tracking fields (timestamps, paths, version)
    - ADDITIVE merge: tax_ids (union)
    - ONLY fill if empty: everything else (manual enrichment wins)
    """
    merged = dict(existing)

    # Fields the scan should always update (reflect latest report state)
    ALWAYS_UPDATE = {"last_updated", "report_version", "report_path", "brief_path"}
    for key in ALWAYS_UPDATE:
        if scanned.get(key):
            merged[key] = scanned[key]

    # Additive: merge tax_ids as union
    existing_ids = set(existing.get("tax_ids") or [])
    scanned_ids = set(scanned.get("tax_ids") or [])
    merged["tax_ids"] = sorted(existing_ids | scanned_ids)

    # Everything else: only fill if existing value is empty/null
    for key, val in scanned.items():
        if key in ALWAYS_UPDATE or key == "tax_ids":
            continue
        if val is None or val == [] or val == "":
            continue
        existing_val = existing.get(key)
        if existing_val in (None, [], "", "unknown", 0):
            merged[key] = val

    return merged


# ---------------------------------------------------------------------------
# Sync command
# ---------------------------------------------------------------------------

def cmd_sync() -> None:
    registry = load_registry()
    existing_map = {e["dir_name"]: e for e in registry["companies"]}

    scanned_dirs = set()
    for entry_path in sorted(CASES_DIR.iterdir()):
        if not entry_path.is_dir():
            continue
        if entry_path.name.startswith("_") or entry_path.name.startswith("."):
            continue

        scanned = scan_case(entry_path)
        if scanned is None:
            print(f"  SKIP  {entry_path.name} (no report found)")
            continue

        dir_name = entry_path.name
        scanned_dirs.add(dir_name)

        if dir_name in existing_map:
            merged = merge_entry(existing_map[dir_name], scanned)
            existing_map[dir_name] = merged
            print(f"  UPDATE  {dir_name}")
        else:
            existing_map[dir_name] = scanned
            print(f"  NEW     {dir_name}")

    registry["companies"] = list(existing_map.values())
    save_registry(registry)
    print(f"\nRegistry saved: {REGISTRY_PATH}")
    print(f"  {len(registry['companies'])} companies total")

    generate_index(registry)
    print(f"Index saved: {INDEX_PATH}")


# ---------------------------------------------------------------------------
# Index generation
# ---------------------------------------------------------------------------

def generate_index(registry: dict) -> None:
    lines = [
        "# Cases Index",
        "",
        f"> Auto-generated by `scripts/sync-registry.py` — {registry['last_synced']}",
        "> 手動編輯無效，請修改 `_registry.json` 後重新 `python scripts/sync-registry.py sync`。",
        "",
    ]

    companies = registry["companies"]

    # --- Overview table ---
    lines.append("## 總覽")
    lines.append("")
    lines.append("| 公司 | 產業 | 規模 | 上市 | 風險 | 分析日期 | 版本 |")
    lines.append("|------|------|------|------|------|---------|------|")

    for c in sorted(companies, key=lambda x: x.get("first_analyzed") or "0000"):
        risk = c.get("risk_level") or "—"
        emoji = RISK_EMOJI.get(risk, "")
        risk_display = f"{emoji} {risk}" if emoji else risk
        lines.append(
            f"| {c.get('name_zh', '?')} "
            f"| {c.get('industry') or c.get('sector') or '—'} "
            f"| {c.get('size') or '—'} "
            f"| {c.get('listing') or '—'} "
            f"| {risk_display} "
            f"| {c.get('first_analyzed') or '—'} "
            f"| {c.get('report_version') or '—'} |"
        )

    # --- By sector ---
    lines.append("")
    lines.append("## 按產業分類")

    sectors: dict[str, list] = {}
    for c in companies:
        s = c.get("sector") or "未分類"
        sectors.setdefault(s, []).append(c)

    for sector in sorted(sectors.keys()):
        lines.append("")
        lines.append(f"### {sector}")
        lines.append("")
        for c in sectors[sector]:
            risk = c.get("risk_level") or "—"
            emoji = RISK_EMOJI.get(risk, "")
            verdict = c.get("verdict") or ""
            if len(verdict) > 80:
                verdict = verdict[:80] + "..."
            lines.append(
                f"- **{c.get('name_zh', '?')}** "
                f"({c.get('size', '?')}/{c.get('listing', '?')}) "
                f"— {verdict} [{emoji} {risk}]"
            )

    # --- By size ---
    lines.append("")
    lines.append("## 按規模分類")

    sizes: dict[str, list] = {}
    for c in companies:
        s = c.get("size") or "unknown"
        sizes.setdefault(s, []).append(c)

    for size in sorted(sizes.keys(), key=lambda s: SIZE_ORDER.get(s, 99)):
        lines.append("")
        lines.append(f"### {size}")
        lines.append("")
        for c in sizes[size]:
            lines.append(
                f"- **{c.get('name_zh', '?')}** — "
                f"{c.get('industry') or '—'} "
                f"({c.get('first_analyzed') or '—'})"
            )

    INDEX_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Show command
# ---------------------------------------------------------------------------

def cmd_show(args: argparse.Namespace) -> None:
    registry = load_registry()
    if not registry["companies"]:
        print("Registry is empty. Run 'sync' first.")
        return

    filtered = registry["companies"]

    if args.sector:
        filtered = [c for c in filtered if c.get("sector") == args.sector]
    if args.size:
        filtered = [c for c in filtered if c.get("size") == args.size]
    if args.risk:
        filtered = [c for c in filtered if c.get("risk_level") == args.risk]

    if not filtered:
        print("No companies match the filter.")
        return

    # header
    print(f"{'公司':<20} {'產業':<16} {'規模':<8} {'上市':<8} {'風險':<10} {'日期':<12} {'版本':<6}")
    print("-" * 82)

    for c in sorted(filtered, key=lambda x: x.get("first_analyzed") or "0000"):
        risk = c.get("risk_level") or "—"
        emoji = RISK_EMOJI.get(risk, "")
        name = c.get("name_zh", "?")
        if len(name) > 18:
            name = name[:17] + "…"
        print(
            f"{name:<20} "
            f"{(c.get('industry') or '—'):<16} "
            f"{(c.get('size') or '—'):<8} "
            f"{(c.get('listing') or '—'):<8} "
            f"{emoji + ' ' + risk:<10} "
            f"{(c.get('first_analyzed') or '—'):<12} "
            f"{(c.get('report_version') or '—'):<6}"
        )

    print(f"\n{len(filtered)} / {len(registry['companies'])} companies shown")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cases Registry — CRM 式企業分類管理"
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("sync", help="掃描 case reports → 更新 registry + 生成 index")

    show_parser = sub.add_parser("show", help="顯示企業摘要表")
    show_parser.add_argument("--sector", help="篩選 sector（科技/金融/娛樂/...）")
    show_parser.add_argument("--size", choices=sorted(VALID_SIZES), help="篩選規模")
    show_parser.add_argument("--risk", choices=sorted(VALID_RISKS), help="篩選風險等級")

    args = parser.parse_args()

    if args.command == "sync":
        cmd_sync()
    elif args.command == "show":
        cmd_show(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
