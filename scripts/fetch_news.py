import json
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote

import feedparser
import requests

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "daily_news.json"

# Google News RSS is used as a free aggregation layer. The app only displays
# factual headlines/summaries and links users back to the original source.
FEEDS = [
    ("THẾ GIỚI", "THẾ GIỚI", "global markets OR world economy OR US stocks OR China economy"),
    ("VĨ MÔ", "VĨ MÔ", "Federal Reserve OR Fed OR inflation OR interest rates OR USD OR Treasury"),
    ("TRONG NƯỚC", "TRONG NƯỚC", "Việt Nam kinh tế OR Chính phủ OR NHNN OR tỷ giá OR lãi suất"),
    ("DOANH NGHIỆP", "DOANH NGHIỆP", "Việt Nam doanh nghiệp OR HOSE OR HNX OR kết quả kinh doanh OR cổ phiếu"),
    ("QUỸ", "QUỸ", "ETF Việt Nam OR FTSE Vietnam OR MSCI Vietnam OR quỹ đầu tư"),
]

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; PhuongTuanMarketDashboard/1.0)"}


def google_news_url(query: str) -> str:
    return (
        "https://news.google.com/rss/search?q="
        + quote(query)
        + "&hl=vi&gl=VN&ceid=VN:vi"
    )


def clean_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def translate_to_vi(text: str) -> str:
    """Best-effort free translation through Google's public translate endpoint.
    If translation fails, keep the original text so the pipeline never breaks.
    """
    text = clean_html(text)
    if not text or re.search(r"[À-ỹĐđ]", text):
        return text
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {"client": "gtx", "sl": "auto", "tl": "vi", "dt": "t", "q": text[:4500]}
        response = requests.get(url, params=params, headers=HEADERS, timeout=15)
        response.raise_for_status()
        payload = response.json()
        return "".join(part[0] for part in payload[0] if part and part[0]).strip() or text
    except Exception:
        return text


def published_iso(entry) -> str:
    raw = entry.get("published") or entry.get("updated")
    if raw:
        try:
            dt = parsedate_to_datetime(raw)
            return dt.astimezone(timezone.utc).isoformat()
        except Exception:
            pass
    return datetime.now(timezone.utc).isoformat()


def source_name(entry) -> str:
    source = entry.get("source")
    if isinstance(source, dict):
        return source.get("title", "Google News")
    return getattr(source, "title", None) or "Google News"


def infer_ticker(title: str):
    # Common Vietnamese stock ticker pattern: uppercase 3 letters in brackets
    # or surrounded by punctuation. Avoid treating common acronyms as tickers.
    blocked = {"FED", "ETF", "GDP", "CPI", "PPI", "USD", "CEO", "AI", "ECB", "BOJ", "EU", "M&A"}
    matches = re.findall(r"(?<![A-Za-z])[A-Z]{3}(?![A-Za-z])", title)
    for item in matches:
        if item not in blocked:
            return item
    return ""


def fetch_feed(category: str, tag: str, query: str):
    url = google_news_url(query)
    response = requests.get(url, headers=HEADERS, timeout=25)
    response.raise_for_status()
    feed = feedparser.parse(response.content)
    results = []
    for entry in feed.entries[:8]:
        title_original = clean_html(entry.get("title", ""))
        summary_original = clean_html(entry.get("summary", ""))
        if not title_original:
            continue

        # Google News often appends the publication name after " - ".
        title = title_original.rsplit(" - ", 1)[0].strip()
        summary = re.sub(r"^.*? - ", "", summary_original).strip() if summary_original else ""
        if not summary or summary == title_original:
            summary = "Cập nhật thông tin theo nguồn công bố; không thêm nhận định, dự báo hoặc khuyến nghị."

        title_vi = translate_to_vi(title)
        summary_vi = translate_to_vi(summary)
        ticker = infer_ticker(title_original) if category == "DOANH NGHIỆP" else ""

        results.append(
            {
                "category": category,
                "tag": tag,
                "ticker": ticker,
                "exchange": "HOSE" if ticker else "",
                "headline_vi": title_vi,
                "summary_vi": summary_vi[:500],
                "source": source_name(entry),
                "source_url": entry.get("link", "https://news.google.com/"),
                "published_at": published_iso(entry),
            }
        )
    return results


def dedupe(cards):
    seen = set()
    output = []
    for card in sorted(cards, key=lambda x: x.get("published_at", ""), reverse=True):
        key = re.sub(r"\W+", " ", card.get("headline_vi", "").lower()).strip()
        if not key or key in seen:
            continue
        seen.add(key)
        output.append(card)
    return output


def main():
    cards = []
    errors = []
    for category, tag, query in FEEDS:
        try:
            cards.extend(fetch_feed(category, tag, query))
        except Exception as exc:
            errors.append(f"{category}: {exc}")

    cards = dedupe(cards)
    # Keep the dashboard fast and readable. Prioritize a balanced mix.
    limits = {"THẾ GIỚI": 4, "VĨ MÔ": 4, "TRONG NƯỚC": 4, "DOANH NGHIỆP": 8, "QUỸ": 3}
    selected = []
    counts = {key: 0 for key in limits}
    for card in cards:
        category = card["category"]
        if category in limits and counts[category] < limits[category]:
            selected.append(card)
            counts[category] += 1

    # If every feed failed, preserve the existing data instead of publishing
    # an empty dashboard.
    if not selected:
        if DATA_FILE.exists():
            return
        raise RuntimeError("No RSS items were collected: " + "; ".join(errors))

    selected.sort(key=lambda x: x.get("published_at", ""), reverse=True)
    now = datetime.now().astimezone().strftime("%d/%m/%Y %H:%M")
    payload = {"updated_at": now, "cards": selected}
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if errors:
        print("Some feeds failed:")
        for error in errors:
            print("-", error)
    print(f"Updated {len(selected)} news cards at {now}")


if __name__ == "__main__":
    main()
