import json
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="Phương Tuấn | Chứng khoán Agribank", page_icon="📊", layout="wide")

DATA_FILE = Path(__file__).parent / "data" / "daily_news.json"

st.markdown(
    """
    <style>
    :root { --orange:#F7A21F; --red:#B81D2D; --bg:#F6F7F8; --line:#E4E7EA; }
    .stApp { background: var(--bg); }
    .block-container { max-width: 1500px; padding-top: 1.1rem; }
    .brand-title { font-size: 1.75rem; font-weight: 900; line-height: 1.1; color: var(--red); margin: 0; }
    .brand-sub { color: #65707A; font-size: .82rem; margin-top: .22rem; }
    .section-title { font-size: 1rem; font-weight: 900; color: #2C3136; margin: .4rem 0 .6rem; }
    .card { background:#fff; border:1px solid var(--line); border-radius:14px; padding:14px; min-height:180px; box-shadow:0 2px 10px rgba(30,40,50,.035); }
    .card:hover { box-shadow:0 6px 20px rgba(30,40,50,.07); }
    .pill { display:inline-block; background:#FFF7E5; color:#7A5200; border-radius:999px; padding:4px 8px; font-size:.68rem; font-weight:800; }
    .cat { display:inline-block; background:#FFF1F2; color:var(--red); border-radius:999px; padding:4px 8px; font-size:.68rem; font-weight:800; margin-left:5px; }
    .time { float:right; color:#7B848D; font-size:.67rem; }
    .headline { font-size: 1rem; font-weight: 800; line-height: 1.4; margin-top: .7rem; }
    .summary { font-size: .84rem; line-height:1.55; color:#56616B; margin-top:.45rem; }
    .source { color:#7B848D; font-size:.68rem; margin-top:.75rem; }
    a { color:var(--red) !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

if DATA_FILE.exists():
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
else:
    data = {"updated_at": "—", "cards": []}

cards = data.get("cards", [])

c1, c2 = st.columns([3, 1])
with c1:
    st.markdown('<p class="brand-title">PHƯƠNG TUẤN</p>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sub">CHỨNG KHOÁN AGRIBANK</div>', unsafe_allow_html=True)
with c2:
    st.markdown(f"<div style='text-align:right;color:#7B848D;font-size:.76rem'>Cập nhật<br><b style='color:#B81D2D;font-size:1rem'>{data.get('updated_at','—')}</b></div>", unsafe_allow_html=True)

st.divider()

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
    text = " ".join([
        item.get("headline_vi", ""), item.get("summary_vi", ""),
        item.get("ticker", ""), item.get("tag", ""), item.get("source", "")
    ]).lower()
    if ok_cat and (not q or q in text):
        visible.append(item)

st.markdown('<div class="section-title">TIN TRONG NGÀY</div>', unsafe_allow_html=True)

if not visible:
    st.info("Chưa có tin phù hợp với bộ lọc hiện tại.")
else:
    for start in range(0, len(visible), 3):
        row = visible[start:start+3]
        cols = st.columns(3, gap="medium")
        for col, item in zip(cols, row):
            with col:
                tag = item.get("tag", item.get("ticker", "Thông tin"))
                if item.get("ticker") and not tag.startswith("["):
                    tag = f"[{item.get('exchange','')}: {item.get('ticker')}]"
                url = item.get("source_url") or item.get("url") or "#"
                st.markdown(
                    f"""
                    <div class='card'>
                      <span class='pill'>{tag}</span>
                      <span class='cat'>{item.get('category','—')}</span>
                      <span class='time'>{item.get('published_at','')}</span>
                      <div class='headline'>{item.get('headline_vi','')}</div>
                      <div class='summary'>{item.get('summary_vi','')}</div>
                      <div class='source'>{item.get('source','')} · <a href='{url}' target='_blank'>Nguồn ↗</a></div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.write("")

st.caption("V0 · Dữ liệu đọc từ data/daily_news.json · Bước tiếp theo: nối RSS/Web → xử lý → cập nhật tự động.")
