"""
Extractor for 104.com.tw (104 人力銀行).

Returns company profile including employee count.
Note: 104.com.tw is a Vite SPA, which is why web_fetch fails.
"""

import asyncio
import re


async def extract_company_profile(page, company_name: str) -> dict:
    """
    Search 104.com.tw for a company and extract profile info.
    """
    # 104 company search URL
    search_url = f"https://www.104.com.tw/company/search?keyword={company_name}"
    await page.goto(search_url)
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(3)

    text = await page.inner_text("body")

    # Try to find the company link and click into it
    company_link = await page.query_selector(f'a:has-text("{company_name}")')
    if not company_link:
        # Try partial match
        company_link = await page.query_selector(".company-name a")

    if company_link:
        await company_link.click()
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)
        text = await page.inner_text("body")
        return _parse_company_page(text, company_name, page.url)

    return {
        "error": f"Company not found on 104: {company_name}",
        "source": "104.com.tw",
    }


async def extract_company_by_id(page, company_id: str) -> dict:
    """
    Directly navigate to a known 104 company page.
    company_id is the 104 internal ID like '1a2x6bln2f'.
    """
    url = f"https://www.104.com.tw/company/{company_id}"
    await page.goto(url)
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(3)

    text = await page.inner_text("body")
    return _parse_company_page(text, "", url)


def _parse_company_page(text: str, search_name: str, url: str = "") -> dict:
    """Parse 104 company profile page."""
    result = {
        "source": "104.com.tw",
        "url": url,
    }

    # Employee count patterns
    employee_patterns = [
        r"員工\s*(\d+[\-~～至]\d+)\s*人",
        r"員工人數\s*[：:]\s*(\d+[\-~～至]\d+)",
        r"(\d+[\-~～至]\d+)\s*(?:名|人|位)(?:員工)?",
        r"員工\s*(\d+)\s*人",
    ]
    for pattern in employee_patterns:
        match = re.search(pattern, text)
        if match:
            result["employee_count"] = match.group(1)
            break

    # Industry
    industry_match = re.search(r"產業(?:類別)?[：:]\s*(.+?)(?:\n|$)", text)
    if industry_match:
        result["industry"] = industry_match.group(1).strip()

    # Capital
    capital_match = re.search(r"資本額[：:]\s*([\d,.]+\s*(?:萬|億|元))", text)
    if capital_match:
        result["capital"] = capital_match.group(1).strip()

    # Company description / about
    # 104 typically has a company intro section
    desc_patterns = [
        r"公司簡介[：:]?\s*(.{20,500}?)(?:\n\n|\n(?:福利|產品|聯絡))",
        r"公司介紹[：:]?\s*(.{20,500}?)(?:\n\n|\n(?:福利|產品|聯絡))",
    ]
    for pattern in desc_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            result["description"] = match.group(1).strip()[:500]
            break

    # Job count
    job_match = re.search(r"(\d+)\s*個工作機會", text)
    if job_match:
        result["open_positions"] = int(job_match.group(1))

    # Address
    addr_match = re.search(
        r"公司地址[：:]\s*(.+?)(?:\n|$)", text
    )
    if addr_match:
        result["address"] = addr_match.group(1).strip()

    return result
