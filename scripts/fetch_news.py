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
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

# Broad news layer. Google News is used as the free RSS aggregator, with targeted
# searches for Vietnamese listed-company coverage so the enterprise section is
# not dependent on one media source.
FEEDS = [
    ("THẾ GIỚI", "global markets OR world economy OR US stocks OR China economy"),
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

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; PhuongTuanMarketDashboard/1.5)"}
# Five-minute runs need a short overlap window to recover an item from a delayed feed.
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


def source_name(entry):
    source = entry.get("source")
    if isinstance(source, dict):
        return source.get("title", "Google News")
    return getattr(source, "title", None) or "Google News"


def infer_tickers(text: str):
    blocked = {
        "FED", "ETF", "GDP", "CPI", "PPI", "USD", "CEO", "AI", "ECB", "BOJ",
        "THE", "AND", "FOR", "NEW", "TOP", "IPO", "NAV", "M&A", "CEO",
    }
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
    keywords = [
        "lãi suất", "tỷ giá", "fed", "fomc", "inflation", "cpi", "pce", "nhnn",
        "chính phủ", "kết quả kinh doanh", "lợi nhuận", "doanh thu", "etf", "ftse",
        "msci", "nâng hạng", "giảm lãi suất", "tăng lãi suất", "thuế", "phát hành",
        "chia cổ tức", "mua lại", "sáp nhập", "m&a", "đại hội cổ đông", "hđqt",
    ]
    score = 2 + sum(1 for keyword in keywords if keyword in text)
    if category in {"VĨ MÔ", "TRONG NƯỚC"} and any(x in text for x in ("fed", "nhnn", "lãi suất", "tỷ giá")):
        score += 1
    return max(1, min(score, 5))


def normalize_key(text: str) -> str:
    text = clean_html(text).casefold()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def fetch_feed(category: str, query: str):
    response = requests.get(google_news_url(query), headers=HEADERS, timeout=25)
    response.raise_for_status()
    feed = feedparser.parse(response.content)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=FETCH_HOURS)
    results = []
    for entry in feed.entries[:40]:
        published = published_dt(entry)
        if published < cutoff:
            continue
        title_original = clean_html(entry.get("title", ""))
        summary_original = clean_html(entry.get("summary", ""))
        if not title_original:
            continue
        title = strip_source_suffix(title_original)
        summary = strip_source_suffix(summary_original) if summary_original else ""
        if not summary or summary.casefold() == title_original.casefold():
            summary = "Cập nhật thông tin theo nguồn; không thêm nhận định, dự báo hoặc khuyến nghị."
        title_vi = clean_html(translate_to_vi(title))
        summary_vi = clean_html(translate_to_vi(summary))
        combined = f"{title_original} {summary_original} {source_name(entry)}"
        tickers = infer_tickers(combined) if category == "DOANH NGHIỆP" else []
        ticker = tickers[0] if tickers else ""
        local_dt = published.astimezone(VN_TZ)
        results.append({
            "category": category,
            "tag": "",
            "ticker": ticker,
            "tickers": tickers,
            "exchange": infer_exchange(combined) if ticker else "",
            "headline_vi": title_vi,
            "summary_vi": summary_vi[:650],
            "source": source_name(entry),
            "source_url": entry.get("link", "https://news.google.com/"),
            "published_at": published.isoformat(),
            "published_date_vn": local_dt.strftime("%Y-%m-%d"),
            "published_time_vn": local_dt.strftime("%H:%M"),
            "importance": importance_score(category, title_vi, summary_vi),
        })
    return results


def load_existing():
    if not DATA_FILE.exists():
        return []
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8")).get("cards", [])
    except Exception:
        return []


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
            errors.append(f"{category} [{query[:45]}]: {exc}")
    now_vn = datetime.now(VN_TZ)
    today = now_vn.strftime("%Y-%m-%d")
    all_recent = dedupe(load_existing() + fresh)
    today_cards = [c for c in all_recent if c.get("published_date_vn") == today]
    if not today_cards:
        print("No fresh news for today; keeping existing dashboard data.")
        return

    # Enterprise news is intentionally much larger than the other categories.
    limits = {"THẾ GIỚI": 15, "VĨ MÔ": 15, "TRONG NƯỚC": 15, "DOANH NGHIỆP": 150, "QUỸ": 30}
    selected, counts = [], {k: 0 for k in limits}
    for card in sorted(today_cards, key=lambda x: x.get("published_at", ""), reverse=True):
        cat = card.get("category")
        if cat in limits and counts[cat] < limits[cat]:
            selected.append(card)
            counts[cat] += 1

    selected.sort(key=lambda x: x.get("published_at", ""), reverse=True)
    payload = {
        "updated_at": now_vn.strftime("%d/%m/%Y %H:%M"),
        "timezone": "Asia/Ho_Chi_Minh",
        "date": today,
        "cards": selected,
    }
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
