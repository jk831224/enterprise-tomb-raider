"""
Extractor for twincn.com (台灣公司網).

Returns director history and associated companies for a person.
Note: twincn.com is JS-rendered, which is exactly why we need Playwright.
"""

import asyncio
import re


async def extract_person_network(page, person_name: str) -> list[dict]:
    """
    Search twincn.com for a person name and extract all associated companies.
    """
    url = f"https://www.twincn.com/Lq.aspx?q={person_name}"
    await page.goto(url)
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(2)

    text = await page.inner_text("body")

    if "查無資料" in text or "找不到" in text:
        return []

    return _parse_person_results(text, person_name)


async def extract_company_directors(page, tax_id: str) -> dict:
    """
    Navigate to twincn.com company page and extract director/shareholder info.
    This complements findbiz by providing historical change data that findbiz lacks.
    """
    url = f"https://www.twincn.com/item.aspx?no={tax_id}"
    await page.goto(url)
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(2)

    text = await page.inner_text("body")

    if "查無資料" in text:
        return {"error": f"No data found for tax_id: {tax_id}", "tax_id": tax_id}

    return _parse_company_page(text, tax_id)


def _parse_person_results(text: str, person_name: str) -> list[dict]:
    """Parse person search results from twincn."""
    results = []
    lines = text.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Pattern: company name + tax_id + role info
        # twincn shows results like: "雲端整合代理商 D XXXXXXXX 董事長"
        match = re.search(
            r"(.+?(?:有限公司|股份有限公司|商行|企業社))\s*[·×]?\s*(\d{8})",
            line,
        )
        if match:
            company_name = match.group(1).strip()
            tax_id = match.group(2)

            # Try to find role
            role = None
            for r in ("董事長", "副董事長", "董事", "監察人", "負責人", "股東"):
                if r in line:
                    role = r
                    break

            results.append(
                {
                    "company_name": company_name,
                    "tax_id": tax_id,
                    "role": role,
                    "person_name": person_name,
                    "source": "twincn.com",
                }
            )

    return results


def _parse_company_page(text: str, tax_id: str) -> dict:
    """Parse company page from twincn."""
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
