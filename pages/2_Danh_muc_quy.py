import html
import json
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Danh mục Quỹ - Daily Market", page_icon="💰", layout="wide")
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "fund_portfolios.json"

st.markdown("""
<style>
.stApp{background:linear-gradient(135deg,#07091E,#111036 50%,#1A0B36);color:#F7F8FF}.block-container{max-width:1450px}
.fund{background:rgba(35,19,68,.92);border:1px solid rgba(154,126,255,.22);border-radius:16px;padding:18px;margin-bottom:16px}.fund h3{color:#fff;margin:0}.muted{color:#9B9DB8;font-size:.76rem}.holding{display:inline-block;background:rgba(247,162,31,.12);border:1px solid rgba(247,162,31,.25);color:#FFBF45;border-radius:999px;padding:6px 9px;margin:4px;font-weight:800;font-size:.78rem}a{color:#F7A21F!important}
</style>
""", unsafe_allow_html=True)

st.title("💰 DANH MỤC QUỸ")
st.caption("Dữ liệu danh mục và tỷ trọng được lấy từ trang công bố của từng quỹ; không phải nhận định đầu tư.")

if not DATA.exists():
    st.info("Chưa có dữ liệu quỹ. Workflow sẽ tạo dữ liệu sau lần chạy cập nhật đầu tiên.")
    st.stop()

try:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
except Exception as exc:
    st.error(f"Không đọc được dữ liệu quỹ: {exc}")
    st.stop()

st.caption(f"Lần thu thập gần nhất: {payload.get('updated_at','—')}")

for fund in payload.get("funds", []):
    name = html.escape(str(fund.get("fund", "Quỹ")))
    url = html.escape(str(fund.get("url", "#")), quote=True)
    fetched = html.escape(str(fund.get("fetched_at", "")))
    st.markdown(f"<div class='fund'><h3>{name}</h3><div class='muted'>Thu thập: {fetched} · <a href='{url}' target='_blank'>Trang nguồn ↗</a></div>", unsafe_allow_html=True)
    holdings = fund.get("holdings", [])
    if not holdings:
        st.warning("Nguồn chưa trả về bảng danh mục có cấu trúc. Vui lòng mở trang nguồn để xem dữ liệu mới nhất.")
    else:
        chunks=[]
        for item in holdings[:20]:
            ticker=html.escape(str(item.get("ticker", "")))
            weight=html.escape(str(item.get("weight_pct", "")))
            chunks.append(f"<span class='holding'>{ticker}{(' · '+weight+'%') if weight else ''}</span>")
        st.markdown("".join(chunks), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.caption("Lưu ý: ngày dữ liệu danh mục phụ thuộc kỳ công bố của từng quỹ; hệ thống không giả định rằng tỷ trọng là real-time.")
