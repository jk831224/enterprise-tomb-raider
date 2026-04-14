"""
Extractor for findbiz.nat.gov.tw (經濟部商工登記公示資料查詢).

Returns structured company data from the official MOEA registry.
"""

import asyncio
import re


async def extract_company(page, tax_id: str) -> dict:
    """
    Navigate to findbiz.nat.gov.tw search for a tax_id,
    click into detail page, and extract structured data.
    """
    await page.goto("https://findbiz.nat.gov.tw/fts/query/QueryBar/queryInit.do")
    await page.wait_for_load_state("networkidle")

    await page.fill("#qryCond", tax_id)
    await page.click("#qryBtn")
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(2)

    # Check if results found
    body_text = await page.inner_text("body")
    if "共 0 筆" in body_text:
        return {"error": f"No company found for tax_id: {tax_id}", "tax_id": tax_id}

    # Click detail link
    detail_link = await page.query_selector("text=詳細資料")
    if not detail_link:
        return {"error": "Detail link not found", "tax_id": tax_id}

    await detail_link.click()
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(1)

    # Extract basic info from detail page
    text = await page.inner_text("body")
    result = _parse_basic_info(text, tax_id)

    # Click directors tab
    dir_tab = await page.query_selector('a:has-text("董監事資料")')
    if dir_tab:
        await dir_tab.click()
        await asyncio.sleep(2)
        dir_text = await page.inner_text("body")
        result["directors"] = _parse_directors(dir_text)
        result["board_term"] = _parse_board_term(dir_text)

    return result


def _parse_basic_info(text: str, tax_id: str) -> dict:
    """Parse the basic info page text into structured fields."""
    result = {
        "source": "findbiz.nat.gov.tw",
        "tax_id": tax_id,
    }

    patterns = {
        "company_name": r"公司名稱\s*[：:]\s*(.+?)(?:\s*Google|$)",
        "previous_name": r"前名稱[：:]\s*(.+?)[）)]",
        "name_change_date": r"(\d+年\d+月\d+日)\s*發文號.*?變更名稱",
        "english_name": r"出進口廠商英文名稱[：:]\s*(.+?)[)）]",
        "capital_total": r"資本總額\(元\)\s*[：:]?\s*([\d,]+)",
        "capital_paid": r"實收資本額\(元\)\s*[：:]?\s*([\d,]+)",
        "shares_per_unit": r"每股金額\(元\)\s*[：:]?\s*([\d,]+)",
        "total_shares": r"已發行股份總數\(股\)\s*[：:]?\s*([\d,]+)",
        "representative": r"代表人姓名\s*[：:]?\s*(\S+)",
        "address": r"公司所在地\s*[：:]?\s*(.+?)(?:\s*電子地圖|\s*同地址)",
        "status": r"登記現況\s*[：:]?\s*(\S+)",
        "established_date": r"核准設立日期\s*[：:]?\s*(\S+)",
        "last_change_date": r"最後核准變更日期\s*[：:]?\s*(\S+)",
        "registration_authority": r"登記機關\s*[：:]?\s*(\S+)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            value = match.group(1).strip()
            if key in ("capital_total", "capital_paid", "total_shares"):
                value = int(value.replace(",", ""))
            result[key] = value

    # Extract business scope
    scope_match = re.findall(r"([A-Z]\d{6})\s+(.+?)(?:\n|$)", text)
    if scope_match:
        result["business_scope"] = [
            {"code": code, "name": name.strip()} for code, name in scope_match
        ]

    # Convert ROC dates to AD
    for date_key in ("established_date", "last_change_date"):
        if date_key in result:
            result[date_key] = _roc_to_ad(result[date_key])

    return result


def _parse_directors(text: str) -> list[dict]:
    """Parse director/supervisor table from the directors tab."""
    directors = []
    # Pattern: sequence number, title, name, representative corp, shares
    lines = text.split("\n")
    for line in lines:
        line = line.strip()
        match = re.match(
            r"(\d{4})\s+(董事長|副董事長|董事|監察人|獨立董事)\s+(\S+)\s*(.*?)\s*([\d,]+)\s*$",
            line,
        )
        if match:
            directors.append(
                {
                    "sequence": match.group(1),
                    "title": match.group(2),
                    "name": match.group(3),
                    "representative_of": match.group(4).strip() or None,
                    "shares": int(match.group(5).replace(",", "")),
                }
            )
    return directors


def _parse_board_term(text: str) -> str | None:
    """Extract board term period."""
    match = re.search(
        r"最近一次登記當屆董監事任期[：:]\s*(.+?至.+?)(?:\s*\(|$)", text
    )
    return match.group(1).strip() if match else None


def _roc_to_ad(roc_str: str) -> str:
    """Convert ROC date string to AD date string.
    e.g. '109年06月12日' -> '2020-06-12'
         '1090612' -> '2020-06-12'
    """
    # Format: 109年06月12日
    match = re.match(r"(\d+)年(\d+)月(\d+)日", roc_str)
    if match:
        year = int(match.group(1)) + 1911
        return f"{year}-{match.group(2)}-{match.group(3)}"

    # Format: 1090612
    match = re.match(r"(\d{3})(\d{2})(\d{2})", roc_str)
    if match:
        year = int(match.group(1)) + 1911
        return f"{year}-{match.group(2)}-{match.group(3)}"

    return roc_str
