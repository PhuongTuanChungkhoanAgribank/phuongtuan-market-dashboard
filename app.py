import html
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st

st.set_page_config(
    page_title="Phương Tuấn - Chứng khoán Agribank Chi nhánh Miền Trung",
    page_icon="📊",
    layout="wide",
)

DATA_FILE = Path(__file__).parent / "data" / "daily_news.json"
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

st.markdown(
    """
    <style>
    :root { --orange:#F7A21F; --orange-2:#FFBE45; --red:#B81D2D; --navy:#151B3A; --ink:#1D2530; --muted:#66717D; --bg:#F4F6F8; --line:#E1E5EA; }
    .stApp { background:radial-gradient(circle at 8% 10%,rgba(247,162,31,.055),transparent 25%),radial-gradient(circle at 92% 18%,rgba(184,29,45,.045),transparent 25%),var(--bg); }
    .block-container { max-width:1500px; padding-top:.75rem; padding-bottom:2rem; }
    .hero { position:relative; overflow:hidden; border-radius:18px; min-height:145px; padding:26px 32px 24px; margin-bottom:18px; background:radial-gradient(circle at 88% 20%,rgba(247,162,31,.26),transparent 25%),radial-gradient(circle at 74% 115%,rgba(184,29,45,.28),transparent 33%),linear-gradient(118deg,#11162F 0%,#171D42 48%,#222A5B 100%); box-shadow:0 12px 32px rgba(18,24,55,.16); }
    .hero:before { content:""; position:absolute; inset:0; opacity:.20; background:repeating-linear-gradient(90deg,transparent 0 78px,rgba(255,255,255,.055) 79px 80px),repeating-linear-gradient(0deg,transparent 0 38px,rgba(255,255,255,.045) 39px 40px); pointer-events:none; }
    .hero:after { content:""; position:absolute; width:720px; height:260px; right:-110px; bottom:-145px; transform:rotate(-8deg); border-top:2px solid rgba(247,162,31,.28); border-radius:50%; box-shadow:80px -26px 0 -78px rgba(247,162,31,.28),170px -62px 0 -118px rgba(247,162,31,.22),270px -18px 0 -150px rgba(184,29,45,.30); pointer-events:none; }
    .hero-content { position:relative; z-index:2; }
    .hero-title { color:#fff; font-size:1.55rem; line-height:1.2; font-weight:900; letter-spacing:.01em; margin:0; }
    .hero-title .accent { color:var(--orange-2); }
    .hero-tagline { color:#E9ECF7; font-size:.90rem; font-weight:800; margin-top:.42rem; letter-spacing:.015em; }
    .hero-note { color:rgba(255,255,255,.68); font-size:.72rem; margin-top:.62rem; }
    .update-box { position:absolute; z-index:3; top:25px; right:30px; text-align:right; color:rgba(255,255,255,.65); font-size:.70rem; }
    .update-box b { color:var(--orange-2); font-size:.92rem; }
    .section-title { font-size:1rem; font-weight:900; color:var(--ink); margin:.7rem 0 .65rem; }
    [data-testid="stMetric"] { background:rgba(255,255,255,.72); border:1px solid var(--line); border-radius:12px; padding:10px 14px; }
    [data-testid="stMetricLabel"] { color:var(--muted); } [data-testid="stMetricValue"] { color:var(--navy); }
    .card { background:rgba(255,255,255,.97); border:1px solid var(--line); border-radius:14px; padding:15px; min-height:184px; box-shadow:0 3px 12px rgba(25,35,50,.045); transition:transform .15s ease,box-shadow .15s ease; }
    .card:hover { transform:translateY(-2px); box-shadow:0 9px 24px rgba(25,35,50,.09); }
    .pill { display:inline-block; background:#FFF7E5; color:#7A5200; border-radius:999px; padding:4px 8px; font-size:.67rem; font-weight:800; }
    .cat { display:inline-block; background:#FFF1F2; color:var(--red); border-radius:999px; padding:4px 8px; font-size:.67rem; font-weight:800; margin-left:5px; }
    .time { float:right; color:#8A929B; font-size:.65rem; }
    .headline { color:var(--ink); font-size:.99rem; font-weight:850; line-height:1.42; margin-top:.68rem; }
    .summary { font-size:.82rem; line-height:1.52; color:#5B6672; margin-top:.42rem; }
    .source { color:#7B848D; font-size:.66rem; margin-top:.72rem; } a { color:var(--red) !important; }
    div[role="radiogroup"] { gap:14px; }
    @media (max-width:800px) { .hero { min-height:180px; padding:22px; } .hero-title { font-size:1.18rem; max-width:78%; } .hero-tagline { font-size:.78rem; max-width:78%; } .update-box { top:20px; right:20px; } }
    </style>
    """,
    unsafe_allow_html=True,
)

if DATA_FILE.exists():
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
else:
    data = {"updated_at": "—", "cards": []}

cards = data.get("cards", [])


def clean_prototype_text(text: str) -> str:
    if not text:
        return ""

    # RSS feeds sometimes leave HTML entities in stored data, especially
    # &nbsp; / non-breaking spaces. Decode and normalize them at render time
    # as a second safety layer for older JSON files.
    result = html.unescape(str(text)).replace("\xa0", " ")
    result = re.sub(r"\s+", " ", result)

    replacements = [
        "Prototype: ", "Prototype – ", "Prototype - ",
        "Card này dùng để kiểm tra cách hiển thị nhóm vĩ mô quốc tế. ",
        "Nội dung thực tế sẽ lấy từ nguồn chính thức của Fed. ",
        "Đây là dữ liệu mẫu để kiểm tra giao diện. ",
        "Ở bước tiếp theo hệ thống sẽ lấy tin thật từ Google News RSS và các nguồn đã chốt. ",
        "Thông tin doanh nghiệp được trình bày thuần túy theo sự kiện công bố, không thêm nhận định, dự báo hoặc khuyến nghị. ",
        "Card mẫu minh họa định dạng tin doanh nghiệp: mã cổ phiếu, sự kiện chính, nguồn và liên kết gốc. ",
    ]
    for old in replacements:
        result = result.replace(old, "")
    return re.sub(r"\s+", " ", result).strip()


def display_tag(item: dict) -> str:
    ticker = (item.get("ticker") or "").strip()
    if ticker:
        exchange = (item.get("exchange") or "").strip()
        return f"[{exchange}: {ticker}]" if exchange else f"[{ticker}]"
    tag = (item.get("tag") or "").strip()
    category = (item.get("category") or "").strip()
    return "" if not tag or tag.casefold() == category.casefold() else tag


def display_time(value: str) -> str:
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone(VN_TZ).strftime("%d/%m %H:%M")
    except Exception:
        return value

updated_at = data.get("updated_at", "—")
st.markdown(
    f"""
    <div class="hero">
      <div class="hero-content">
        <div class="hero-title">PHƯƠNG TUẤN <span class="accent">- CHỨNG KHOÁN AGRIBANK</span><br>CHI NHÁNH MIỀN TRUNG</div>
        <div class="hero-tagline">NGƯỜI AGRIBANK LÀM CHỨNG KHOÁN</div>
        <div class="hero-note">Daily Market</div>
      </div>
      <div class="update-box">CẬP NHẬT<br><b>{html.escape(str(updated_at))}</b></div>
    </div>
    """,
    unsafe_allow_html=True,
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Tổng tin", len(cards))
m2.metric("Doanh nghiệp", sum(1 for x in cards if x.get("category") == "DOANH NGHIỆP"))
m3.metric("Vĩ mô", sum(1 for x in cards if x.get("category") == "VĨ MÔ"))
m4.metric("Thế giới", sum(1 for x in cards if x.get("category") == "THẾ GIỚI"))

search = st.text_input("Tìm kiếm", placeholder="Nhập mã cổ phiếu, doanh nghiệp, chủ đề hoặc từ khóa…")
category = st.radio("Bộ lọc", ["Tất cả", "THẾ GIỚI", "TRONG NƯỚC", "VĨ MÔ", "DOANH NGHIỆP", "QUỸ"], horizontal=True, label_visibility="collapsed")

q = (search or "").lower().strip()
visible = []
for item in cards:
    ok_cat = category == "Tất cả" or item.get("category") == category
    headline = clean_prototype_text(item.get("headline_vi", ""))
    summary = clean_prototype_text(item.get("summary_vi", ""))
    text = " ".join([headline, summary, item.get("ticker", ""), item.get("tag", ""), item.get("source", "")]).lower()
    if ok_cat and (not q or q in text):
        visible.append((item, headline, summary))

st.markdown('<div class="section-title">TIN TRONG NGÀY</div>', unsafe_allow_html=True)

if not visible:
    st.info("Chưa có tin phù hợp với bộ lọc hiện tại.")
else:
    for start in range(0, len(visible), 3):
        row = visible[start:start + 3]
        cols = st.columns(3, gap="medium")
        for col, (item, headline, summary) in zip(cols, row):
            with col:
                tag = display_tag(item)
                url = item.get("source_url") or item.get("url") or "#"
                tag_html = f"<span class='pill'>{html.escape(tag)}</span>" if tag else ""
                category_html = f"<span class='cat'>{html.escape(str(item.get('category','—')))}</span>"
                source = html.escape(str(item.get("source", "")))
                headline_html = html.escape(headline)
                summary_html = html.escape(summary)
                url_html = html.escape(str(url), quote=True)
                published_html = html.escape(display_time(str(item.get('published_at', ''))))
                st.markdown(
                    f"""
                    <div class='card'>
                      {tag_html}{category_html}
                      <span class='time'>{published_html}</span>
                      <div class='headline'>{headline_html}</div>
                      <div class='summary'>{summary_html}</div>
                      <div class='source'>{source} · <a href='{url_html}' target='_blank'>Nguồn ↗</a></div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.write("")

st.markdown('<div style="color:#8A929B;font-size:.68rem;margin-top:1rem;">Bản tin cung cấp thông tin, không phải khuyến nghị đầu tư.</div>', unsafe_allow_html=True)
