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
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; PhuongTuanMarketDashboard/2.2)"}
FETCH_HOURS = 24

FEEDS = [
    # THẾ GIỚI
    ("THẾ GIỚI", "global markets Reuters OR Bloomberg OR CNBC OR WSJ OR Financial Times"),
    ("THẾ GIỚI", "US markets Wall Street stocks bonds Treasury dollar Fed"),
    ("THẾ GIỚI", "FOMC minutes Federal Reserve meeting minutes Fed rates inflation"),
    ("THẾ GIỚI", "US Iran Israel Middle East conflict oil sanctions geopolitics"),
    ("THẾ GIỚI", "Japan BOJ yen Nikkei inflation GDP exports"),
    ("THẾ GIỚI", "Europe ECB euro STOXX Germany France inflation GDP"),
    ("THẾ GIỚI", "China PBOC yuan property exports imports GDP inflation"),
    ("THẾ GIỚI", "Korea KOSPI Bank of Korea semiconductors exports"),
    ("THẾ GIỚI", "India RBI rupee Sensex Nifty inflation GDP"),
    ("THẾ GIỚI", "ASEAN Singapore Indonesia Thailand Malaysia markets economy"),
    ("THẾ GIỚI", "gold silver copper oil Brent WTI commodities"),
    ("THẾ GIỚI", "site:znews.vn thế giới OR quốc tế OR Fed OR Iran OR Trung Quốc OR Nhật Bản OR châu Âu"),
    ("THẾ GIỚI", "site:vietstock.vn/the-gioi chứng khoán thế giới OR Fed OR dầu OR vàng OR Iran"),
    ("THẾ GIỚI", "site:vneconomy.vn thế giới OR Mỹ OR Trung Quốc OR châu Âu OR Nhật Bản OR Fed"),

    # TRONG NƯỚC
    ("TRONG NƯỚC", "Việt Nam Chính phủ NHNN tỷ giá lãi suất đầu tư công kinh tế"),
    ("TRONG NƯỚC", "site:cafef.vn Việt Nam NHNN tỷ giá lãi suất đầu tư công chứng khoán"),
    ("TRONG NƯỚC", "site:vietnambiz.vn Việt Nam NHNN tỷ giá lãi suất chính sách chứng khoán"),

    # DOANH NGHIỆP - query ngắn, tách theo nguồn để Google News trả kết quả tốt hơn
    ("DOANH NGHIỆP", "site:cafef.vn/doanh-nghiep cổ phiếu doanh nghiệp kết quả kinh doanh"),
    ("DOANH NGHIỆP", "site:cafef.vn/thi-truong-chung-khoan cổ phiếu doanh nghiệp niêm yết"),
    ("DOANH NGHIỆP", "site:vietstock.vn/doanh-nghiep doanh nghiệp cổ phiếu kết quả kinh doanh"),
    ("DOANH NGHIỆP", "site:vietstock.vn/chung-khoan cổ phiếu niêm yết giao dịch nội bộ cổ tức"),
    ("DOANH NGHIỆP", "site:vietnambiz.vn/doanh-nghiep cổ phiếu doanh nghiệp kết quả kinh doanh"),
    ("DOANH NGHIỆP", "site:vietnambiz.vn/thoi-su/chung-khoan cổ phiếu doanh nghiệp niêm yết"),
    ("DOANH NGHIỆP", "site:24hmoney.vn cổ phiếu doanh nghiệp kết quả kinh doanh"),
    ("DOANH NGHIỆP", "site:vneconomy.vn cổ phiếu doanh nghiệp niêm yết kết quả kinh doanh"),
    ("DOANH NGHIỆP", "HOSE HNX UPCOM cổ tức tăng vốn M&A giao dịch cổ đông lớn kết quả kinh doanh"),

    # THÔNG BÁO CHÍNH THỨC / CẢNH BÁO THỊ TRƯỜNG
    ("THÔNG BÁO", "site:hsx.vn công bố thông tin cảnh báo kiểm soát hạn chế giao dịch đình chỉ niêm yết"),
    ("THÔNG BÁO", "site:hnx.vn công bố thông tin cảnh báo kiểm soát hạn chế giao dịch đình chỉ UPCOM"),
    ("THÔNG BÁO", "site:ssc.gov.vn xử phạt công bố thông tin cảnh báo chứng khoán doanh nghiệp"),
    ("THÔNG BÁO", "site:ssc.gov.vn Ủy ban Chứng khoán xử phạt vi phạm hành chính công bố thông tin"),
    ("THÔNG BÁO", "site:vietstock.vn công bố thông tin HOSE HNX UPCOM cảnh báo kiểm soát"),
]

DIRECT_RSS_FEEDS = [
    ("THẾ GIỚI", "VnExpress", "https://vnexpress.net/rss/the-gioi.rss"),
    ("DOANH NGHIỆP", "CafeF", "https://cafef.vn/doanh-nghiep.rss"),
    ("DOANH NGHIỆP", "CafeF", "https://cafef.vn/thi-truong-chung-khoan.rss"),
    ("THẾ GIỚI", "CafeF", "https://cafef.vn/tai-chinh-quoc-te.rss"),
]


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
        r = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={"client": "gtx", "sl": "auto", "tl": "vi", "dt": "t", "q": text[:4500]},
            headers=HEADERS,
            timeout=15,
        )
        r.raise_for_status()
        payload = r.json()
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
        ("Mỹ", ["federal reserve", "fed", "fomc", "treasury", "wall street", "us markets"]),
        ("Trung Quốc", ["china", "pbo", "yuan", "chinese"]),
        ("Nhật Bản", ["japan", "boj", "yen", "nikkei"]),
        ("EU", ["europe", "eurozone", "ecb", "germany", "france", "stoxx"]),
        ("Hàn Quốc", ["korea", "kospi", "bank of korea"]),
        ("Ấn Độ", ["india", "rbi", "rupee", "sensex", "nifty"]),
        ("ASEAN", ["asean", "singapore", "indonesia", "thailand", "malaysia"]),
        ("Trung Đông", ["iran", "israel", "middle east", "hormuz", "gaza", "opec"]),
        ("Đông Âu", ["ukraine", "russia", "nato"]),
    ]
    for region, keys in groups:
        if any(k in text for k in keys):
            return region
    return "Toàn cầu"


def infer_tickers(text: str):
    blocked = {"FED", "ETF", "GDP", "CPI", "PPI", "USD", "CEO", "AI", "ECB", "BOJ", "THE", "AND", "FOR", "NEW", "TOP", "IPO", "NAV", "HNX", "HSX"}
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
    keywords = ["lãi suất", "tỷ giá", "fed", "fomc", "cpi", "pce", "nhnn", "lợi nhuận", "doanh thu", "cổ tức", "m&a", "đại hội cổ đông", "hđqt", "iran", "israel", "oil", "ecb", "boj", "china", "cảnh báo", "kiểm soát", "đình chỉ", "xử phạt", "công bố thông tin"]
    score = 2 + sum(1 for k in keywords if k in text)
    if category == "THÔNG BÁO":
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
        summary = "Cập nhật theo nguồn công bố; không thêm nhận định, dự báo hoặc khuyến nghị."
    title_vi = clean_html(translate_to_vi(title))
    summary_vi = clean_html(translate_to_vi(summary))
    combined = f"{title_original} {summary_original} {source_name(entry, fallback_source)}"
    tickers = infer_tickers(combined) if category in {"DOANH NGHIỆP", "THÔNG BÁO"} else []
    ticker = tickers[0] if tickers else ""
    region = world_region(query, title_original, summary_original) if category == "THẾ GIỚI" else ""
    tag = region if category == "THẾ GIỚI" else ("CƠ QUAN QUẢN LÝ" if category == "THÔNG BÁO" else "")
    local_dt = published.astimezone(VN_TZ)
    return {
        "category": category,
        "tag": tag,
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
    r = requests.get(google_news_url(query), headers=HEADERS, timeout=25)
    r.raise_for_status()
    feed = feedparser.parse(r.content)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=FETCH_HOURS)
    results = []
    for entry in feed.entries[:40]:
        if published_dt(entry) < cutoff:
            continue
        card = build_card(category, entry, "Google News", query)
        if card:
            results.append(card)
    return results


def fetch_direct_rss(category: str, source: str, url: str):
    r = requests.get(url, headers=HEADERS, timeout=25)
    r.raise_for_status()
    feed = feedparser.parse(r.content)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=FETCH_HOURS)
    results = []
    for entry in feed.entries[:60]:
        if published_dt(entry) < cutoff:
            continue
        card = build_card(category, entry, source, url)
        if card:
            card["source"] = source
            results.append(card)
    return results


def load_existing():
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8")).get("cards", []) if DATA_FILE.exists() else []
    except Exception:
        return []


def dedupe(cards):
    seen, output = set(), []
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
    all_recent = dedupe(load_existing() + fresh)
    today_cards = [c for c in all_recent if c.get("published_date_vn") == today and c.get("category") != "QUỸ"]
    if not today_cards:
        print("No fresh news for today; keeping existing dashboard data.")
        return

    limits = {"THẾ GIỚI": 100, "TRONG NƯỚC": 40, "DOANH NGHIỆP": 180, "THÔNG BÁO": 100}
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
    print(f"Updated {len(selected)} cards for {today}; archive saved. Counts: {counts}")


if __name__ == "__main__":
    main()
