import html
import json
import re
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "weekly_fund_portfolios.json"
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; PhuongTuanMarketDashboard/2.2)"}

SOURCES = [
    ("Dragon Capital - DCDS", "Dragon Capital", "https://dautu.dragoncapital.com.vn/dcds"),
    ("Dragon Capital - DCDE", "Dragon Capital", "https://www.dragoncapital.com.vn/individual/vi/product/a0eJ2000001X9qOIAS/dcde"),
    ("PYN Elite", "PYN Fund Management", "https://www.pyn.fi/en/pyn-elite-fund/portfolio/"),
    ("VinaCapital - VOF", "VinaCapital", "https://vof.vinacapital.com/portfolio/holdings/"),
]

TICKER_RE = re.compile(r"\b[A-Z]{3}\b")
WEIGHT_RE = re.compile(r"(\d{1,2}(?:[\.,]\d+)?)\s*%")


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def text(self):
        return re.sub(r"\s+", " ", html.unescape(" ".join(self.parts))).strip()


def clean(text):
    return re.sub(r"\s+", " ", html.unescape(text or "")).strip()


def fetch_source(name, manager, url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    parser = TextParser()
    parser.feed(r.text)
    text = parser.text()
    holdings = []

    for match in TICKER_RE.finditer(text):
        ticker = match.group(0)
        if ticker in {"NAV", "USD", "EUR", "ETF", "THE", "AND", "PYN", "URL", "GTM", "DOM", "SPA", "YTD", "RNS", "ESG", "CEO", "IPO", "III", "ROE", "VOF"}:
            continue
        window = text[match.start():match.start() + 260]
        weight_match = WEIGHT_RE.search(window)
        holdings.append({
            "ticker": ticker,
            "weight_pct": weight_match.group(1).replace(",", ".") if weight_match else "",
            "raw": window[:300],
        })
        if len(holdings) >= 30:
            break

    unique, seen = [], set()
    for h in holdings:
        if h["ticker"] in seen:
            continue
        seen.add(h["ticker"])
        unique.append(h)

    fetched_at = datetime.now(VN_TZ).isoformat()
    return {
        "fund": name,
        "fund_name": name,
        "manager": manager,
        "url": url,
        "source_url": url,
        "fetched_at": fetched_at,
        "updated_at": fetched_at,
        "holdings": unique[:20],
        "note": "Danh mục/tỷ trọng lấy theo trang công bố của quỹ; cập nhật theo tuần, ngày dữ liệu phụ thuộc kỳ công bố của từng quỹ.",
    }


def main():
    result, errors = [], []
    for name, manager, url in SOURCES:
        try:
            result.append(fetch_source(name, manager, url))
        except Exception as exc:
            errors.append(f"{name}: {exc}")
    if not result:
        raise RuntimeError("Không lấy được dữ liệu quỹ: " + "; ".join(errors))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"updated_at": datetime.now(VN_TZ).isoformat(), "update_frequency": "weekly", "funds": result, "errors": errors}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Updated {len(result)} weekly fund sources")
    for e in errors:
        print("-", e)


if __name__ == "__main__":
    main()
