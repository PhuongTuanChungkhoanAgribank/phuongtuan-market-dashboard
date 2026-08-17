import html
import json
from datetime import date
from pathlib import Path

import streamlit as st

ARCHIVE_DIR = Path(__file__).resolve().parents[1] / "data" / "archive"

st.set_page_config(page_title="Tra cứu lịch sử · Daily Market", page_icon="🔎", layout="wide")

st.markdown("""
<style>
.stApp { background:linear-gradient(135deg,#07091E 0%,#111036 48%,#1A0B36 100%); color:#F7F8FF; }
.block-container { max-width:1500px; }
.title { font-size:1.45rem; font-weight:950; color:#fff; }
.title span { color:#F7A21F; }
.subtitle { color:#B7B9D0; margin:.35rem 0 1.2rem; }
.result { background:linear-gradient(145deg,rgba(35,19,68,.96),rgba(17,14,43,.97)); border:1px solid rgba(154,126,255,.22); border-left:3px solid #F7A21F; border-radius:14px; padding:14px 16px; margin-bottom:10px; }
.meta { color:#FFBF45; font-size:.72rem; font-weight:800; }
.headline { color:#fff; font-size:.96rem; font-weight:850; margin:.35rem 0; line-height:1.4; }
.summary { color:#B7B8CD; font-size:.78rem; line-height:1.5; }
.source { color:#8F91AB; font-size:.68rem; margin-top:.5rem; }
a { color:#F7A21F !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">🔎 TRA CỨU <span>DAILY MARKET</span></div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Tra cứu bản tin đã lưu theo ngày, mã cổ phiếu, doanh nghiệp hoặc từ khóa. Chỉ cung cấp thông tin, không thêm nhận định đầu tư.</div>', unsafe_allow_html=True)

files = sorted(ARCHIVE_DIR.glob("*.json"), reverse=True) if ARCHIVE_DIR.exists() else []
dates = []
for f in files:
    try:
        dates.append(date.fromisoformat(f.stem))
    except ValueError:
        pass

c1, c2 = st.columns([1, 2])
with c1:
    selected_date = st.date_input("Ngày", value=dates[0] if dates else date.today(), min_value=min(dates) if dates else None, max_value=max(dates) if dates else None)
with c2:
    query = st.text_input("Mã / doanh nghiệp / từ khóa", placeholder="Ví dụ: VIC, Vingroup, FPT, FTSE, lãi suất…")

category = st.radio("Nhóm", ["Tất cả", "THẾ GIỚI", "TRONG NƯỚC", "VĨ MÔ", "DOANH NGHIỆP", "QUỸ"], horizontal=True, label_visibility="collapsed")

archive_file = ARCHIVE_DIR / f"{selected_date.isoformat()}.json"
if not archive_file.exists():
    st.info("Chưa có dữ liệu lưu cho ngày này. Dashboard sẽ tự tạo archive từ các lần cập nhật tiếp theo.")
    st.stop()

try:
    cards = json.loads(archive_file.read_text(encoding="utf-8")).get("cards", [])
except Exception:
    cards = []

q = query.casefold().strip()
results = []
for item in cards:
    if category != "Tất cả" and item.get("category") != category:
        continue
    haystack = " ".join([
        str(item.get("ticker", "")), str(item.get("headline_vi", "")),
        str(item.get("summary_vi", "")), str(item.get("source", "")),
    ]).casefold()
    if q and q not in haystack:
        continue
    results.append(item)

st.caption(f"{len(results)} tin · {selected_date.strftime('%d/%m/%Y')}")

if not results:
    st.info("Không tìm thấy tin phù hợp.")
else:
    for item in results:
        ticker = item.get("ticker", "")
        exchange = item.get("exchange", "")
        tag = f"[{exchange}: {ticker}]" if ticker and exchange else (f"[{ticker}]" if ticker else item.get("category", ""))
        title = html.escape(str(item.get("headline_vi", "")))
        summary = html.escape(str(item.get("summary_vi", "")))
        source = html.escape(str(item.get("source", "")))
        url = html.escape(str(item.get("source_url", "#")), quote=True)
        tm = html.escape(str(item.get("published_time_vn", "")))
        st.markdown(f"""
        <div class="result">
          <div class="meta">{html.escape(str(tag))} · {tm}</div>
          <div class="headline">{title}</div>
          <div class="summary">{summary}</div>
          <div class="source">{source} · <a href="{url}" target="_blank">Nguồn ↗</a></div>
        </div>
        """, unsafe_allow_html=True)
