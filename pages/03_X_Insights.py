"""X Insights: free official X profile timelines, separate from Daily Market."""
import html
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="X Insights | Agriseco Miền Trung", page_icon="🌐", layout="wide")

ACCOUNTS = [
    ("Javier Blas", "JavierBlas", "Năng lượng & hàng hóa", "Bình luận năng lượng và thị trường hàng hóa"),
    ("Lisa Abramowicz", "lisaabramowicz1", "Kinh tế Mỹ & Fed", "Lãi suất, kinh tế Mỹ và thị trường vốn"),
    ("Jim Bianco", "biancoresearch", "Kinh tế Mỹ & Fed", "Vĩ mô, trái phiếu và chính sách tiền tệ"),
    ("EndGame Macro", "onechancefreedm", "Vĩ mô & thanh khoản", "Rủi ro hệ thống và phân tích vĩ mô"),
    ("Drop Site", "DropSiteNews", "Địa chính trị", "Tin chính trị và xung đột quốc tế"),
    ("DD Geopolitics", "DD_Geopolitics", "Địa chính trị", "Tin và góc nhìn địa chính trị"),
    ("The Kobeissi Letter", "KobeissiLetter", "Thị trường tài chính", "Dữ liệu kinh tế và thị trường toàn cầu"),
    ("Bull Theory", "BullTheoryio", "Thị trường tài chính", "Tin tức và nghiên cứu thị trường"),
    ("Macro Liquidity by Sunil Reddy", "Macrobysunil", "Vĩ mô & thanh khoản", "Thanh khoản, chu kỳ nợ, vàng và bạc"),
]

st.markdown("""
<style>
.stApp{background:linear-gradient(160deg,#fffdf9,#fff7eb 65%,#fffdf9);color:#392923}
.block-container{max-width:1450px;padding-top:1.25rem}
.x-hero{padding:24px 28px;border:1px solid #f0d8b5;border-radius:18px;background:linear-gradient(110deg,#fff,#fff4dd 75%,#ffe4b1);margin-bottom:20px}
.x-title{font-size:2rem;font-weight:900;color:#a21e2b;letter-spacing:.025em}
.x-sub{color:#77564b;margin-top:4px}
.x-label{font-size:.82rem;font-weight:800;color:#aa2630}
.x-card{padding:12px 16px;background:#fff;border:1px solid #efd9bb;border-radius:14px;margin-bottom:12px}
.x-card a{color:#a21e2b;text-decoration:none;font-weight:800}
[data-testid="stAlert"]{border-radius:12px}
</style>
<div class="x-hero">
<div class="x-label">PHƯƠNG TUẤN · CHỨNG KHOÁN AGRIBANK · CHI NHÁNH MIỀN TRUNG</div>
<div class="x-title">🌐 X INSIGHTS</div>
<div class="x-sub">Góc nhìn toàn cầu · Theo dõi các tài khoản X về kinh tế, tài chính và địa chính trị</div>
</div>
""", unsafe_allow_html=True)

st.info("Bản miễn phí: hiển thị bài đăng công khai qua tiện ích chính thức của X. Nội dung do X cung cấp, không tự động dịch, lưu lịch sử hay xác minh. X có thể yêu cầu đăng nhập hoặc chặn hiển thị nhúng.")
st.caption("Các tài khoản được lựa chọn để tham khảo đa chiều. Quan điểm cá nhân không đại diện cho Agriseco và không cấu thành khuyến nghị đầu tư.")

topics = ["Tất cả"] + list(dict.fromkeys(item[2] for item in ACCOUNTS))
topic = st.selectbox("Lọc theo chủ đề", topics)
keyword = st.text_input("Tìm tài khoản", placeholder="Tên tác giả hoặc @username")
filtered = [a for a in ACCOUNTS if (topic == "Tất cả" or a[2] == topic) and (not keyword or keyword.casefold() in (a[0] + " " + a[1]).casefold())]
st.caption(f"Đang hiển thị {len(filtered)}/{len(ACCOUNTS)} tài khoản · Chọn tài khoản để xem timeline")

if not filtered:
    st.warning("Không có tài khoản phù hợp.")
else:
    labels = [f"{a[0]} · @{a[1]}" for a in filtered]
    chosen = st.selectbox("Tài khoản X", labels)
    name, handle, category, description = filtered[labels.index(chosen)]
    profile = f"https://x.com/{handle}"
    st.markdown(
        f'<div class="x-card"><strong>{html.escape(name)}</strong> · '
        f'<span>{html.escape(category)}</span><p>{html.escape(description)}</p>'
        f'<a href="{profile}" target="_blank" rel="noopener noreferrer">Mở trang X gốc ↗</a></div>',
        unsafe_allow_html=True,
    )
    st.caption("Timeline bên dưới phụ thuộc vào quyền hiển thị của X. Nếu trống, hãy dùng liên kết mở trang X gốc ở trên.")
    widget = f"""<!doctype html><html lang="vi"><head><meta charset="utf-8"></head>
    <body style="margin:0;background:#fff;">
    <a class="twitter-timeline" data-height="740" data-theme="light" data-chrome="noheader nofooter"
       href="{profile}">Bài đăng từ @{handle}</a>
    <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
    </body></html>"""
    components.html(widget, height=760, scrolling=True)

with st.expander("Danh sách đầy đủ 9 nguồn X"):
    for name, handle, category, description in ACCOUNTS:
        st.markdown(f"**[{name}](https://x.com/{handle})** · @{handle} · {category} — {description}")

st.caption("X Insights · Giai đoạn 1: nhúng miễn phí, không dùng API, không lưu hoặc sao chép bài đăng. Daily Market hiện tại giữ nguyên.")
