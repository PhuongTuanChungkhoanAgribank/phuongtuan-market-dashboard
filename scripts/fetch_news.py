import html
import json
import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

import feedparser
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "daily_news.json"
ARCHIVE_DIR = ROOT / "data" / "archive"
FUND_FILE = ROOT / "data" / "fund_portfolios.json"
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

# World-news layer: broad international coverage plus targeted Vietnamese media.
# Google News RSS is the free aggregation layer. VnExpress also contributes via
# its first-party World RSS channel.
FEEDS = [
    ("THẾ GIỚI", "global markets Reuters OR Bloomberg OR CNBC OR WSJ OR Financial Times"),
    ("THẾ GIỚI", "US markets Wall Street stocks bonds Treasury dollar Fed"),
    ("THẾ GIỚI", "US Iran Israel Middle East conflict oil sanctions geopolitics"),
    ("THẾ GIỚI", "FOMC minutes Federal Reserve meeting minutes Fed rates inflation"),
    ("THẾ GIỚI", "site:federalreserve.gov FOMC minutes statement Federal Reserve"),
    ("THẾ GIỚI", "site:cnbc.com markets Fed stocks bonds economy"),
    ("THẾ GIỚI", "site:bloomberg.com markets economics Fed stocks bonds"),
    ("THẾ GIỚI", "site:reuters.com world markets Fed Iran oil bonds"),
    ("THẾ GIỚI", "site:wsj.com markets Fed economy stocks bonds"),
    ("THẾ GIỚI", "site:ft.com markets economy Fed global markets"),
    ("THẾ GIỚI", "Japan markets BOJ yen Nikkei inflation GDP exports"),
    ("THẾ GIỚI", "site:reuters.com Japan BOJ yen Nikkei economy"),
    ("THẾ GIỚI", "site:cnbc.com Japan BOJ yen Nikkei economy"),
    ("THẾ GIỚI", "Korea KOSPI Bank of Korea won semiconductors exports"),
    ("THẾ GIỚI", "India RBI rupee Sensex Nifty inflation GDP economy"),
    ("THẾ GIỚI", "ASEAN Singapore Indonesia Thailand Malaysia markets economy"),
    ("THẾ GIỚI", "Australia RBA AUD jobs inflation commodities economy"),
    ("THẾ GIỚI", "Taiwan TSMC semiconductors exports economy"),
    ("THẾ GIỚI", "Europe ECB euro STOXX inflation GDP Germany France economy"),
    ("THẾ GIỚI", "site:ecb.europa.eu ECB monetary policy interest rates"),
    ("THẾ GIỚI", "UK Bank of England sterling inflation GDP economy"),
    ("THẾ GIỚI", "Germany DAX Bundesbank inflation industrial production economy"),
    ("THẾ GIỚI", "France Italy Spain Europe markets sovereign bonds economy"),
    ("THẾ GIỚI", "China markets PBOC yuan property exports imports GDP inflation"),
    ("THẾ GIỚI", "site:stats.gov.cn China NBS GDP CPI PPI industrial production"),
    ("THẾ GIỚI", "dollar DXY Treasury yields global bonds FX currencies"),
    ("THẾ GIỚI", "gold silver copper oil Brent WTI commodities"),
    ("THẾ GIỚI", "AI semiconductors Nvidia TSMC Microsoft Amazon Google Meta capex"),
    ("THẾ GIỚI", "OPEC oil production energy LNG natural gas Middle East"),
    ("THẾ GIỚI", "US China tariffs trade war sanctions supply chain geopolitics"),
    ("THẾ GIỚI", "Ukraine Russia Europe NATO sanctions oil gas geopolitics"),
    ("THẾ GIỚI", "site:znews.vn thế giới OR quốc tế OR Mỹ OR Iran OR Trung Quốc OR Nhật Bản OR châu Âu"),
    ("THẾ GIỚI", "site:znews.vn Fed OR FOMC OR dầu OR vàng OR chứng khoán Mỹ OR chứng khoán thế giới"),
    ("THẾ GIỚI", "site:vnexpress.net/the-gioi Mỹ OR Iran OR Trung Quốc OR Nhật Bản OR châu Âu OR Nga OR Ukraine"),
    ("THẾ GIỚI", "site:vietstock.vn thế giới OR chứng khoán Mỹ OR chứng khoán châu Á OR chứng khoán châu Âu OR Fed OR Iran"),
    ("THẾ GIỚI", "site:vietstock.vn vàng thế giới OR dầu thế giới OR giá dầu OR hàng hóa quốc tế OR USD"),
    ("THẾ GIỚI", "site:cafef.vn thế giới OR chứng khoán Mỹ OR Fed OR dầu OR vàng"),
    ("THẾ GIỚI", "site:vneconomy.vn thế giới OR Mỹ OR Trung Quốc OR châu Âu OR Nhật Bản OR Fed"),
    ("VĨ MÔ", "Federal Reserve OR Fed OR inflation OR interest rates OR USD OR Treasury"),
    ("TRONG NƯỚC", "Việt Nam kinh tế OR Chính phủ OR NHNN OR tỷ giá OR lãi suất"),
    ("DOANH NGHIỆP", "Việt Nam doanh nghiệp OR HOSE OR HNX OR UPCOM OR kết quả kinh doanh OR cổ phiếu OR M&A"),
    ("DOANH NGHIỆP", "site:vietstock.vn cổ phiếu OR doanh nghiệp OR công bố thông tin OR kết quả kinh doanh"),
    ("DOANH NGHIỆP", "site:vietnambiz.vn chứng khoán OR cổ phiếu OR doanh nghiệp OR kết quả kinh doanh"),
    ("DOANH NGHIỆP", "site:cafef.vn cổ phiếu OR doanh nghiệp OR kết quả kinh doanh OR công bố thông tin"),
    ("DOANH NGHIỆP", "site:ndh.vn chứng khoán OR doanh nghiệp OR cổ phiếu OR kết quả kinh doanh"),
    ("DOANH NGHIỆP", "site:vneconomy.vn chứng khoán OR doanh nghiệp OR cổ phiếu"),
    ("DOANH NGHIỆP", "site:24hmoney.vn cổ phiếu OR doanh nghiệp OR kết quả kinh doanh"),
    ("QUỸ", "ETF Việt Nam OR FTSE Vietnam OR MSCI Vietnam OR quỹ đầu tư OR quỹ mở"),
    ("QUỸ", "site:dragoncapital.com.vn quỹ danh mục đầu tư OR DCDS OR DCDE OR DCBF OR DCIP"),
    ("QUỸ", "site:dautu.dragoncapital.com.vn quỹ danh mục đầu tư OR DCDS OR DCDE OR DCBF OR DCIP"),
    ("QUỸ", "site:pyn.fi PYN Elite portfolio Vietnam"),
    ("QUỸ", "site:vinacapital.com Vietnam fund portfolio holdings"),
]

DIRECT_RSS_FEEDS = [
    ("THẾ GIỚI", "VnExpress", "https://vnexpress.net/rss/the-gioi.rss"),
]

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; PhuongTuanMarketDashboard/2.0)"}
FETCH_HOURS = 8


def google_news_url(query: str) -> str:
    return "https://news.google.com/rss/search?q=" + quote(query) + "&hl=vi&gl=VN&ceid=VN:vi"


def clean_html(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def strip_source_suffix(text: str) -> str:
    text = clean_html(text)
    return text.rsplit(" - ", 1)[0].strip() if " - " in text else text


def translate_to_vi(text: str) -> str:
    text = clean_html(text)
    if not text or re.search(r"[À-ỹĐđ]", text):
        return text
    try:
        response = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={"client": "gtx", "sl": "auto", "tl": "vi", "dt": "t", "q": text[:4500]},
            headers=HEADERS,
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        return clean_html("".join(part[0] for part in payload[0] if part and part[0])) or text
    except Exception:
        return text


def published_dt(entry):
    raw = entry.get("published") or entry.get("updated")
    if raw:
        try:
            return parsedate_to_datetime(raw).astimezone(timezone.utc)
        except Exception:
            pass
    return datetime.now(timezone.utc)


def source_name(entry, fallback="Google News"):
    source = entry.get("source")
    if isinstance(source, dict):
        return source.get("title", fallback)
    return getattr(source, "title", None) or fallback


def world_region(query: str, title: str, summary: str) -> str:
    text = f"{query} {title} {summary}".casefold()
    groups = [
        ("Mỹ", ["us ", "us markets", "federal reserve", "fed", "fomc", "treasury", "wall street", "cnbc"]),
        ("Trung Quốc", ["china", "pbo", "nbs china", "chinese"]),
        ("Nhật Bản", ["japan", "boj", "yen", "nikkei"]),
        ("EU", ["europe", "eurozone", "ecb", "germany", "france", "italy", "spain", "dax", "stoxx"]),
        ("Anh", ["uk ", "britain", "bank of england", "boe", "sterling", "london"]),
        ("Hàn Quốc", ["korea", "kospi", "bank of korea", "won"]),
        ("Ấn Độ", ["india", "rbi", "rupee", "sensex", "nifty"]),
        ("ASEAN", ["asean", "singapore", "indonesia", "thailand", "malaysia"]),
        ("Australia", ["australia", "rba", "aud ", "sydney"]),
        ("Đài Loan", ["taiwan", "tsmc"]),
        ("Trung Đông", ["iran", "israel", "middle east", "hormuz", "gaza", "saudi", "uae", "qatar", "opec"]),
        ("Đông Âu", ["ukraine", "russia", "nato"]),
    ]
    for region, keys in groups:
        if any(k in text for k in keys):
            return region
    return "Toàn cầu"


def infer_tickers(text: str):
    blocked = {"FED", "ETF", "GDP", "CPI", "PPI", "USD", "CEO", "AI", "ECB", "BOJ", "THE", "AND", "FOR", "NEW", "TOP", "IPO", "NAV", "M&A"}
    found = []
    for item in re.findall(r"(?<![A-Za-z])[A-Z]{3}(?![A-Za-z])", text or ""):
        if item not in blocked and item not in found:
            found.append(item)
    return found


def infer_exchange(text: str) -> str:
    upper = (text or "").upper()
    for exchange in ("UPCOM", "HNX", "HOSE", "HSX"):
        if exchange in upper:
            return "HOSE" if exchange == "HSX" else exchange
    return ""


def importance_score(category: str, title: str, summary: str) -> int:
    text = f"{title} {summary}".lower()
    keywords = ["lãi suất", "tỷ giá", "fed", "fomc", "inflation", "cpi", "pce", "nhnn", "chính phủ", "kết quả kinh doanh", "lợi nhuận", "doanh thu", "etf", "ftse", "msci", "nâng hạng", "giảm lãi suất", "tăng lãi suất", "thuế", "phát hành", "chia cổ tức", "mua lại", "sáp nhập", "m&a", "đại hội cổ đông", "hđqt", "iran", "israel", "middle east", "hormuz", "opec", "oil", "brent", "wti", "ecb", "boj", "japan", "eurozone", "europe", "china", "pbo", "tariff"]
    score = 2 + sum(1 for keyword in keywords if keyword in text)
    if category == "THẾ GIỚI" and any(x in text for x in ("fomc", "fed", "iran", "israel", "oil", "ecb", "boj", "china", "opec")):
        score += 1
    if category in {"VĨ MÔ", "TRONG NƯỚC"} and any(x in text for x in ("fed", "nhnn", "lãi suất", "tỷ giá")):
        score += 1
    return max(1, min(score, 5))


def normalize_key(text: str) -> str:
    text = clean_html(text).casefold()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def build_card(category: str, entry, fallback_source="Google News", query=""):
    published = published_dt(entry)
    title_original = clean_html(entry.get("title", ""))
    summary_original = clean_html(entry.get("summary", ""))
    if not title_original:
        return None
    title = strip_source_suffix(title_original)
    summary = strip_source_suffix(summary_original) if summary_original else ""
    if not summary or summary.casefold() == title_original.casefold():
        summary = "Cập nhật thông tin theo nguồn; không thêm nhận định, dự báo hoặc khuyến nghị."
    title_vi = clean_html(translate_to_vi(title))
    summary_vi = clean_html(translate_to_vi(summary))
    combined = f"{title_original} {summary_original} {source_name(entry, fallback_source)}"
    tickers = infer_tickers(combined) if category == "DOANH NGHIỆP" else []
    ticker = tickers[0] if tickers else ""
    region = world_region(query, title_original, summary_original) if category == "THẾ GIỚI" else ""
    local_dt = published.astimezone(VN_TZ)
    return {
        "category": category,
        "tag": region if category == "THẾ GIỚI" else "",
        "region": region,
        "ticker": ticker,
        "tickers": tickers,
        "exchange": infer_exchange(combined) if ticker else "",
        "headline_vi": title_vi,
        "summary_vi": summary_vi[:650],
        "source": source_name(entry, fallback_source),
        "source_url": entry.get("link", "https://news.google.com/"),
        "published_at": published.isoformat(),
        "published_date_vn": local_dt.strftime("%Y-%m-%d"),
        "published_time_vn": local_dt.strftime("%H:%M"),
        "importance": importance_score(category, title_vi, summary_vi),
    }


def fetch_feed(category: str, query: str):
    response = requests.get(google_news_url(query), headers=HEADERS, timeout=25)
    response.raise_for_status()
    feed = feedparser.parse(response.content)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=FETCH_HOURS)
    results = []
    for entry in feed.entries[:30]:
        if published_dt(entry) < cutoff:
            continue
        card = build_card(category, entry, "Google News", query)
        if card:
            results.append(card)
    return results


def fetch_direct_rss(category: str, source: str, url: str):
    response = requests.get(url, headers=HEADERS, timeout=25)
    response.raise_for_status()
    feed = feedparser.parse(response.content)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=FETCH_HOURS)
    results = []
    for entry in feed.entries[:50]:
        if published_dt(entry) < cutoff:
            continue
        card = build_card(category, entry, source, "VnExpress World RSS")
        if card:
            card["source"] = source
            results.append(card)
    return results


def load_existing():
    if not DATA_FILE.exists():
        return []
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8")).get("cards", [])
    except Exception:
        return []


def load_fund_cards(now_vn):
    """Turn the latest official fund portfolio snapshot into dashboard cards.
    This guarantees QUỸ has useful content even when fund websites publish
    portfolio data rather than RSS news articles.
    """
    if not FUND_FILE.exists():
        return []
    try:
        payload = json.loads(FUND_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

    cards = []
    for fund in payload.get("funds", []):
        name = str(fund.get("fund", "Quỹ")).strip()
        url = str(fund.get("url", "")).strip()
        holdings = fund.get("holdings", []) or []
        valid = []
        seen = set()
        for item in holdings:
            ticker = re.sub(r"[^A-Z0-9.-]", "", str(item.get("ticker", "")).upper())
            if not ticker or ticker in {"NAV", "USD", "EUR", "ETF", "THE", "AND", "PYN", "URL", "GTM", "DOM", "SPA", "YTD", "RNS", "ESG", "CEO", "IPO", "III", "ROE", "VOF"}:
                continue
            if ticker in seen:
                continue
            seen.add(ticker)
            weight = str(item.get("weight_pct", "")).strip()
            if weight:
                valid.append(f"{ticker} ({weight}%)")
            else:
                valid.append(ticker)
            if len(valid) >= 8:
                break
        if not valid:
            continue
        summary = "Danh mục gần nhất: " + ", ".join(valid) + "."
        cards.append({
            "category": "QUỸ",
            "tag": "DANH MỤC QUỸ",
            "region": "",
            "ticker": "",
            "tickers": [v.split(" ")[0] for v in valid],
            "exchange": "",
            "headline_vi": f"{name} - cập nhật danh mục cổ phiếu",
            "summary_vi": summary,
            "source": name,
            "source_url": url,
            "published_at": now_vn.isoformat(),
            "published_date_vn": now_vn.strftime("%Y-%m-%d"),
            "published_time_vn": now_vn.strftime("%H:%M"),
            "importance": 4,
        })
    return cards


def dedupe(cards):
    seen = set()
    output = []
    for card in sorted(cards, key=lambda x: x.get("published_at", ""), reverse=True):
        key = normalize_key(card.get("headline_vi", ""))
        if not key or key in seen:
            continue
        seen.add(key)
        output.append(card)
    return output


def save_snapshot(cards, day):
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    archive_file = ARCHIVE_DIR / f"{day}.json"
    old_cards = []
    if archive_file.exists():
        try:
            old_cards = json.loads(archive_file.read_text(encoding="utf-8")).get("cards", [])
        except Exception:
            pass
    day_cards = [c for c in cards if c.get("published_date_vn") == day]
    archive_cards = dedupe(old_cards + day_cards)
    archive_cards.sort(key=lambda x: x.get("published_at", ""), reverse=True)
    archive_file.write_text(json.dumps({"date": day, "timezone": "Asia/Ho_Chi_Minh", "cards": archive_cards}, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    fresh, errors = [], []
    for category, query in FEEDS:
        try:
            fresh.extend(fetch_feed(category, query))
        except Exception as exc:
            errors.append(f"{category} [{query[:55]}]: {exc}")
    for category, source, url in DIRECT_RSS_FEEDS:
        try:
            fresh.extend(fetch_direct_rss(category, source, url))
        except Exception as exc:
            errors.append(f"{source} RSS: {exc}")

    now_vn = datetime.now(VN_TZ)
    today = now_vn.strftime("%Y-%m-%d")
    fresh.extend(load_fund_cards(now_vn))
    all_recent = dedupe(load_existing() + fresh)
    today_cards = [c for c in all_recent if c.get("published_date_vn") == today]
    if not today_cards:
        print("No fresh news for today; keeping existing dashboard data.")
        return

    limits = {"THẾ GIỚI": 80, "VĨ MÔ": 20, "TRONG NƯỚC": 20, "DOANH NGHIỆP": 150, "QUỸ": 30}
    selected, counts = [], {k: 0 for k in limits}
    for card in sorted(today_cards, key=lambda x: x.get("published_at", ""), reverse=True):
        cat = card.get("category")
        if cat in limits and counts[cat] < limits[cat]:
            selected.append(card)
            counts[cat] += 1

    selected.sort(key=lambda x: x.get("published_at", ""), reverse=True)
    payload = {"updated_at": now_vn.strftime("%d/%m/%Y %H:%M"), "timezone": "Asia/Ho_Chi_Minh", "date": today, "cards": selected}
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    save_snapshot(all_recent, today)

    if errors:
        print("Some feeds failed:")
        for error in errors:
            print("-", error)
    print(f"Updated {len(selected)} cards for {today}; archive saved.")


if __name__ == "__main__":
    main()
