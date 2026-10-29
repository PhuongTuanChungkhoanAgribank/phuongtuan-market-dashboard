"""X Insights - free source directory and copy/paste translation workflow."""
import re
from urllib.parse import quote, urlparse

import streamlit as st

st.set_page_config(page_title="X Insights | Agriseco Miền Trung", page_icon="🌐", layout="wide")

ACCOUNTS = [
    ("Javier Blas", "JavierBlas", "Năng lượng & hàng hóa", "Dầu mỏ, năng lượng, thị trường hàng hóa"),
    ("Lisa Abramowicz", "lisaabramowicz1", "Kinh tế Mỹ & Fed", "Lãi suất, kinh tế Mỹ và trái phiếu"),
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
.stApp{background:linear-gradient(150deg,#fffdfa,#fff7eb 65%,#fffdf9);color:#392923}
.block-container{max-width:1390px;padding-top:1.1rem;padding-bottom:2rem}
.x-hero{padding:23px 27px;border:1px solid #efd4a9;border-radius:18px;background:linear-gradient(110deg,#fff,#fff2d9 75%,#ffe5b4);margin-bottom:12px}
.x-title{font-size:1.85rem;font-weight:950;color:#a21e2b;letter-spacing:.025em}
.x-sub{color:#77564b;margin-top:4px}
.x-label{font-size:.78rem;font-weight:800;color:#aa2630}
.x-card{padding:15px;background:#fff;border:1px solid #efd9bb;border-radius:14px;margin-bottom:10px;min-height:134px;box-shadow:0 5px 14px rgba(130,84,26,.045)}
.x-card strong{color:#9f2330}
.x-card .detail{font-size:.84rem;color:#785a50;line-height:1.5;margin:8px 0}
.x-card a{color:#ae222c;text-decoration:none;font-weight:800}
div[data-baseweb="select"]>div,div[data-baseweb="input"],div[data-baseweb="textarea"]{background:#fff!important;border:1px solid #ead4b6!important;border-radius:11px!important;color:#392923!important}
div[data-baseweb="select"] span,div[data-baseweb="input"] input,div[data-baseweb="textarea"] textarea{color:#392923!important}
div[data-baseweb="input"] input::placeholder,div[data-baseweb="textarea"] textarea::placeholder{color:#9c857a!important}
[data-testid="stWidgetLabel"] p{color:#80574d!important;font-weight:700}
[data-testid="stAlert"]{border-radius:12px}
a{color:#ab2430}
@media(max-width:700px){.block-container{padding-top:.6rem}.x-hero{padding:16px;margin-bottom:8px}.x-title{font-size:1.5rem}.x-card{min-height:0}div[data-testid="stVerticalBlock"]{gap:.7rem}}
</style>
<div class="x-hero">
  <div class="x-label">PHƯƠNG TUẤN · CHỨNG KHOÁN AGRIBANK · CHI NHÁNH MIỀN TRUNG</div>
  <div class="x-title">🌐 X INSIGHTS</div>
  <div class="x-sub">Góc nhìn toàn cầu · Theo dõi 9 nguồn X · Không phí API</div>
</div>
""", unsafe_allow_html=True)

st.caption("Nguồn tham khảo đa chiều, gồm cả nhận định cá nhân. Nội dung không đại diện cho Agriseco và không phải khuyến nghị đầu tư.")

tab_sources, tab_translate = st.tabs(["🌐 9 NGUỒN TIN X", "🌍 HỖ TRỢ DỊCH BÀI X"])

with tab_sources:
    st.info("Mở bài gốc ngay trên X. X hiện hạn chế nhúng timeline vào website ngoài, nên bản này không hiển thị khung trắng hoặc giả định đã tải được bài đăng.")
    topic_options = ["Tất cả"] + list(dict.fromkeys(account[2] for account in ACCOUNTS))
    col_topic, col_search = st.columns([1, 2])
    with col_topic:
        topic = st.selectbox("Chủ đề", topic_options)
    with col_search:
        keyword = st.text_input("Tìm tài khoản", placeholder="Tên tác giả, @username, chủ đề…")
    filtered = [
        account for account in ACCOUNTS
        if (topic == "Tất cả" or account[2] == topic)
        and (not keyword or keyword.casefold() in " ".join(account).casefold())
    ]
    st.caption(f"{len(filtered)}/{len(ACCOUNTS)} nguồn tin · Bấm 'Mở X' để xem bài mới nhất")
    if not filtered:
        st.warning("Không tìm thấy tài khoản phù hợp.")
    for i in range(0, len(filtered), 3):
        cols = st.columns(3)
        for col, (name, handle, category, desc) in zip(cols, filtered[i:i+3]):
            profile_url = f"https://x.com/{handle}"
            with col:
                st.markdown(
                    '<div class="x-card">'
                    f'<strong>{name}</strong><div class="detail">@{handle} · {category}<br>{desc}</div>'
                    f'<a href="{profile_url}" target="_blank" rel="noopener noreferrer">Mở X · Xem bài mới nhất ↗</a>'
                    '</div>',
                    unsafe_allow_html=True,
                )
    st.caption("Các liên kết đưa đến chính chủ tài khoản X. Không dùng scraper, API trả phí hay dịch vụ trung gian.")

with tab_translate:
    st.markdown("#### Chuyển bài đăng X sang tiếng Việt miễn phí")
    st.write("**Cách dùng:** Mở X → sao chép nội dung bài đăng → dán vào đây → bấm nút dịch. Google Dịch mở ở tab mới; không cần API hay thanh toán.")
    source = st.selectbox("Tác giả / nguồn", ["Chưa xác định"] + [f"{name} (@{handle})" for name, handle, _, _ in ACCOUNTS])
    post_url = st.text_input("Liên kết bài đăng (không bắt buộc)", placeholder="https://x.com/tacgia/status/...")
    original = st.text_area("Dán nội dung bài đăng gốc", placeholder="Paste tweet / post text here...", height=190, max_chars=12000)
    source_url = post_url.strip()
    is_valid_url = False
    if source_url:
        try:
            parsed = urlparse(source_url)
            is_valid_url = parsed.scheme == "https" and (parsed.hostname or "").lower() in {"x.com", "www.x.com", "twitter.com", "www.twitter.com", "mobile.twitter.com"}
        except ValueError:
            pass
        if not is_valid_url:
            st.warning("Liên kết chưa đúng định dạng x.com hoặc twitter.com. Vui lòng kiểm tra lại.")
    cleaned = original.strip()
    if cleaned:
        if len(cleaned) > 4000:
            st.warning("Văn bản dài trên 4.000 ký tự: nút Google Dịch chỉ chuyển 4.000 ký tự đầu để tránh URL quá dài. Có thể chia thành nhiều đoạn.")
        translate_url = "https://translate.google.com/?sl=auto&tl=vi&op=translate&text=" + quote(cleaned[:4000], safe="")
        st.link_button("🌍 DỊCH SANG TIẾNG VIỆT MIỄN PHÍ ↗", translate_url, use_container_width=True)
        st.caption("Google Dịch là trang web bên ngoài; nội dung đã dán sẽ được đưa vào liên kết để dịch. Không gửi văn bản nếu chứa thông tin riêng tư.")
        template = (
            "X INSIGHTS | BẢN TIN THAM KHẢO\n"
            f"Nguồn: {source}\n"
            f"Link gốc: {source_url if is_valid_url else 'Chưa có'}\n"
            "Chủ đề: [Chọn chủ đề]\n"
            "Thời gian bài đăng: [Điền theo X]\n\n"
            "NỘI DUNG TIẾNG VIỆT:\n[Dán bản dịch tại đây]\n\n"
            "THÔNG TIN / SỐ LIỆU CẦN KIỂM CHỨNG:\n[Điền nếu có]\n\n"
            "TÁC ĐỘNG CÓ THỂ CẦN THEO DÕI:\n[Đánh giá riêng, không tự động suy diễn]\n\n"
            "BẢN GỐC:\n" + cleaned
        )
        with st.expander("📋 Mẫu bản tin để sao chép, biên tập", expanded=False):
            st.code(template, language=None)
            st.download_button(
                "⬇️ Tải mẫu bản tin .txt",
                data=template.encode("utf-8"),
                file_name="x_insights_ban_tin.txt",
                mime="text/plain",
            )
    else:
        st.caption("Dán nội dung vào ô trên để bật nút dịch miễn phí và tạo mẫu bản tin.")

st.divider()
st.caption("X Insights 2.0 · 100% không phí API · Không tự lấy bài đăng, không lưu dữ liệu dán lên máy chủ ứng dụng và không thay đổi dữ liệu Daily Market.")
