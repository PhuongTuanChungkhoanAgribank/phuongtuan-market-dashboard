import html
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "fund_portfolios.json"
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; PhuongTuanMarketDashboard/1.0)"}

SOURCES = [
    ("Dragon Capital - DCDS", "https://dautu.dragoncapital.com.vn/dcds"),
    ("Dragon Capital - DCDE", "https://www.dragoncapital.com.vn/individual/vi/product/a0eJ2000001X9qOIAS/dcde"),
    ("PYN Elite", "https://www.pyn.fi/en/pyn-elite-fund/portfolio/"),
    ("VinaCapital - VOF", "https://vof.vinacapital.com/portfolio/holdings/"),
]

TICKER_RE = re.compile(r"\b[A-Z]{3}\b")
WEIGHT_RE = re.compile(r"(\d{1,2}(?:[\.,]\d+)?)\s*%")


def clean(text):
    return re.sub(r"\s+", " ", html.unescape(text or "")).strip()


def fetch_source(name, url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    text = clean(soup.get_text(" ", strip=True))
    holdings = []

    # Prefer HTML tables when the site exposes structured holdings.
    for table in soup.find_all("table"):
        rows = []
        for tr in table.find_all("tr"):
            cells = [clean(x.get_text(" ", strip=True)) for x in tr.find_all(["th", "td"])]
            if cells:
                rows.append(cells)
        for row in rows:
            joined = " | ".join(row)
            tickers = TICKER_RE.findall(joined)
            weights = WEIGHT_RE.findall(joined)
            for ticker in tickers[:3]:
                if ticker in {"NAV", "USD", "EUR", "ETF", "THE", "AND"}:
                    continue
                weight = weights[-1].replace(",", ".") if weights else ""
                holdings.append({"ticker": ticker, "weight_pct": weight, "raw": joined[:400]})

    # PYN/modern pages can expose cards rather than tables. Search text around
    # explicit portfolio-weight phrases as a fallback.
    if not holdings:
        for match in re.finditer(r"([A-Z]{3})", text):
            ticker = match.group(1)
            if ticker in {"NAV", "USD", "EUR", "ETF", "THE", "AND"}:
                continue
            window = text[match.start():match.start() + 220]
            weight_match = WEIGHT_RE.search(window)
            holdings.append({"ticker": ticker, "weight_pct": weight_match.group(1).replace(",", ".") if weight_match else "", "raw": window[:300]})
            if len(holdings) >= 20:
                break

    # Deduplicate while preserving first occurrence.
    unique, seen = [], set()
    for h in holdings:
        if h["ticker"] in seen:
            continue
        seen.add(h["ticker"])
        unique.append(h)

    return {
        "fund": name,
        "url": url,
        "fetched_at": datetime.now(VN_TZ).isoformat(),
        "holdings": unique[:20],
        "note": "Danh mục/tỷ trọng lấy theo trang công bố của quỹ; ngày dữ liệu phụ thuộc kỳ cập nhật của từng quỹ.",
    }


def main():
    result = []
    errors = []
    for name, url in SOURCES:
        try:
            result.append(fetch_source(name, url))
        except Exception as exc:
            errors.append(f"{name}: {exc}")
    if not result:
        raise RuntimeError("Không lấy được dữ liệu quỹ: " + "; ".join(errors))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"updated_at": datetime.now(VN_TZ).isoformat(), "funds": result, "errors": errors}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Updated {len(result)} fund sources")
    for e in errors:
        print("-", e)


if __name__ == "__main__":
    main()
