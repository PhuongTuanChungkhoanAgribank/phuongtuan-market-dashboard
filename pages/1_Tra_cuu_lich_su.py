import html
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st

st.set_page_config(page_title="Tra cứu lịch sử - Daily Market", page_icon="🔎", layout="wide")
ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_DIR = ROOT / "data" / "archive"
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

st.markdown("""
<style>
.stApp{background:linear-gradient(135deg,#07091E,#111036 50%,#1A0B36);color:#F7F8FF}
.block-container{max-width:1450px}
.result{background:rgba(35,19,68,.92);border:1px solid rgba(154,126,255,.22);border-radius:14px;padding:14px 16px;margin-bottom:10px}
.title{color:#fff;font-weight:850;font-size:1rem;line-height:1.4}.meta{color:#9B9DB8;font-size:.72rem;margin-top:7px}.pill{color:#FFBF45;font-weight:800}.summary{color:#B7B8CD;font-size:.8rem;margin-top:5px;line-height:1.45}
a{color:#F7A21F!important}
</style>
""", unsafe_allow_html=True)

st.title("🔎 TRA CỨU LỊCH SỬ")
st.caption("Kho bản tin đã lưu theo ngày Việt Nam · tìm theo mã cổ phiếu, doanh nghiệp, nguồn hoặc từ khóa")

archive_files = sorted(ARCHIVE_DIR.glob("*.json"), reverse=True) if ARCHIVE_DIR.exists() else []
available_dates = []
for path in archive_files:
    try:
        available_dates.append(date.fromisoformat(path.stem))
    except ValueError:
        pass

if not available_dates:
    st.info("Kho lịch sử chưa có dữ liệu. Sau lần cập nhật đầu tiên, hệ thống sẽ tự tạo archive theo ngày.")
    st.stop()

selected_date = st.date_input("Ngày", value=available_dates[0], min_value=min(available_dates), max_value=max(available_dates), format="DD/MM/YYYY")
query = st.text_input("Tìm mã / doanh nghiệp / từ khóa", placeholder="Ví dụ: VIC, Vingroup, HPG, FTSE, lãi suất…")
category = st.selectbox("Nhóm tin", ["Tất cả", "THẾ GIỚI", "TRONG NƯỚC", "VĨ MÔ", "DOANH NGHIỆP", "QUỸ"])

archive_path = ARCHIVE_DIR / f"{selected_date.isoformat()}.json"
if not archive_path.exists():
    st.warning("Ngày này chưa có snapshot dữ liệu.")
    st.stop()

try:
    payload = json.loads(archive_path.read_text(encoding="utf-8"))
    cards = payload.get("cards", [])
except Exception as exc:
    st.error(f"Không đọc được dữ liệu lịch sử: {exc}")
    st.stop()

q = (query or "").strip().casefold()
results = []
for item in cards:
    if category != "Tất cả" and item.get("category") != category:
        continue
    haystack = " ".join([
        str(item.get("headline_vi", "")), str(item.get("summary_vi", "")),
        str(item.get("ticker", "")), " ".join(item.get("tickers", []) or []),
        str(item.get("source", "")), str(item.get("tag", "")),
    ]).casefold()
    if q and q not in haystack:
        continue
    results.append(item)

st.write(f"**{len(results)} tin** · {selected_date.strftime('%d/%m/%Y')}")

for item in results:
    headline = html.escape(str(item.get("headline_vi", "")))
    summary = html.escape(str(item.get("summary_vi", "")))
    source = html.escape(str(item.get("source", "")))
    category_text = html.escape(str(item.get("category", "")))
    ticker = html.escape(str(item.get("ticker", "")))
    published = item.get("published_at", "")
    try:
        time_text = datetime.fromisoformat(published.replace("Z", "+00:00")).astimezone(VN_TZ).strftime("%d/%m/%Y %H:%M")
    except Exception:
        time_text = html.escape(str(published))
    url = html.escape(str(item.get("source_url", "#")), quote=True)
    code = f" · <span class='pill'>{ticker}</span>" if ticker else ""
    st.markdown(f"""<div class='result'><div class='title'>{headline}</div><div class='summary'>{summary}</div><div class='meta'><span class='pill'>{category_text}</span>{code} · {source} · {time_text} · <a href='{url}' target='_blank'>Nguồn ↗</a></div></div>""", unsafe_allow_html=True)
