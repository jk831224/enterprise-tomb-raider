"""
Extractor for person network search.

Primary source: findbiz.nat.gov.tw (official MOEA, "公司董事或監察人或經理人" mode).
Fallback: twincn.com company page (for director details on a known tax_id).

Note: twincn.com person SEARCH pages are empty even with Playwright (Cloudflare/anti-bot).
However, twincn.com company DETAIL pages (item.aspx?no=) work fine and are used
as supplementary source in tw_company_lookup.
"""

import asyncio
import re


async def extract_person_network(page, person_name: str) -> list[dict]:
    """
    Search findbiz.nat.gov.tw for all companies where a person is
    registered as representative, director, supervisor, or manager.
    """
    await page.goto("https://findbiz.nat.gov.tw/fts/query/QueryBar/queryInit.do")
    await page.wait_for_load_state("networkidle")

    # Switch to "公司董事或監察人或經理人" search mode
    label = await page.query_selector('label:has-text("公司董事或監察人")')
    if label:
        await label.click()
        await asyncio.sleep(0.5)

    await page.fill("#qryCond", person_name)
    await page.click("#qryBtn")
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(2)

    text = await page.inner_text("body")
    return _parse_person_results(text, person_name)


async def extract_company_directors(page, tax_id: str) -> dict:
    """
    Navigate to twincn.com company page and extract director/shareholder info.
    This complements findbiz by providing historical change data.

    Note: twincn company detail pages (item.aspx?no=) render fine with Playwright,
    unlike the person search pages which are blocked.
    """
    url = f"https://www.twincn.com/item.aspx?no={tax_id}"
    await page.goto(url)
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(2)

    text = await page.inner_text("body")

    if not text.strip() or "查無資料" in text:
        return {"error": f"No data found for tax_id: {tax_id}", "tax_id": tax_id}

    return _parse_company_page(text, tax_id)


def _parse_person_results(text: str, person_name: str) -> list[dict]:
    """Parse findbiz person search results (list page)."""
    results = []

    # Check for zero results
    if "共 0 筆" in text:
        return []

    # Pattern: company name block followed by metadata line
    # "雲端整合代理商 D\n統一編號：XXXXXXXX , 公司代表人：代表人 Y , ..."
    blocks = re.split(r"\n(?=\S+(?:有限公司|股份有限公司|商行|企業社|工作室))", text)

    for block in blocks:
        # Extract company name (first line)
        lines = block.strip().split("\n")
        if not lines:
            continue

        company_name = lines[0].strip()
        if not any(
            kw in company_name
            for kw in ("有限公司", "股份有限公司", "商行", "企業社", "工作室")
        ):
            continue

        # Extract tax_id
        tax_match = re.search(r"統一編號[：:]\s*(\d{8})", block)
        if not tax_match:
            continue

        tax_id = tax_match.group(1)

        # Extract role
        role = None
        role_match = re.search(r"公司代表人[：:]\s*(\S+)", block)
        if role_match and person_name in role_match.group(1):
            role = "代表人"

        # Extract status
        status = None
        status_match = re.search(r"登記現況[：:]\s*(\S+)", block)
        if status_match:
            status = status_match.group(1)

        # Extract address
        address = None
        addr_match = re.search(r"地址[：:]\s*(.+?)(?:\s*,|\s*$)", block)
        if addr_match:
            address = addr_match.group(1).strip()

        results.append(
            {
                "company_name": company_name,
                "tax_id": tax_id,
                "role": role,
                "status": status,
                "address": address,
                "person_name": person_name,
                "source": "findbiz.nat.gov.tw",
            }
        )

    return results


def _parse_company_page(text: str, tax_id: str) -> dict:
    """Parse twincn company page (for supplementary director data)."""
    result = {
        "source": "twincn.com",
        "tax_id": tax_id,
    }

    patterns = {
        "company_name": r"公司名稱[：:]\s*(.+?)(?:\n|$)",
        "representative": r"代表人[：:]\s*(\S+)",
        "capital": r"資本(?:總)?額[：:]\s*([\d,]+)",
        "address": r"公司地址[：:]\s*(.+?)(?:\n|$)",
        "phone": r"電話[：:]\s*(\S+)",
        "established_date": r"設立日期[：:]\s*(\S+)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            value = match.group(1).strip()
            if key == "capital":
                value = int(value.replace(",", ""))
            result[key] = value

    # Extract directors list
    directors = []
    dir_pattern = re.findall(
        r"(董事長|副董事長|董事|監察人)\s*[：:]\s*(\S+?)(?:\s|,|、|$)", text
    )
    for title, name in dir_pattern:
        directors.append({"title": title, "name": name})
    if directors:
        result["directors"] = directors

    return result
