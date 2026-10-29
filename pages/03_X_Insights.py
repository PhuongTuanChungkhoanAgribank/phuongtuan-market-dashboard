"""X Insights: 13 curated X sources. No feeds or translation tools."""
import html
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
    ("HFI Research", "HFI_Research", "Năng lượng & hàng hóa", "Phân tích thị trường dầu khí và năng lượng"),
    ("FinGenAI", "ackmeni", "Thị trường tài chính", "Góc nhìn tài chính và thị trường"),
    ("Charlie Bilello", "charliebilello", "Kinh tế Mỹ & Fed", "Biểu đồ và dữ liệu kinh tế, thị trường tài chính"),
    ("Investment Wisdom", "InvestingCanons", "Thị trường tài chính", "Bài học và góc nhìn về đầu tư"),
]

st.markdown("""
<style>
.stApp{background:linear-gradient(150deg,#fffdfa,#fff7eb 65%,#fffdf9);color:#392923}
.block-container{max-width:1390px;padding-top:1.1rem;padding-bottom:2rem}
.x-hero{padding:23px 27px;border:1px solid #efd4a9;border-radius:18px;background:linear-gradient(110deg,#fff,#fff2d9 75%,#ffe5b4);margin-bottom:12px}
.x-title{font-size:1.85rem;font-weight:950;color:#a21e2b}
.x-sub{color:#77564b;margin-top:4px}
.x-label{font-size:.78rem;font-weight:800;color:#aa2630}
.x-card{padding:15px;background:#fff;border:1px solid #efd9bb;border-radius:14px;margin-bottom:10px;min-height:134px;box-shadow:0 5px 14px rgba(130,84,26,.045)}
.x-card strong{color:#9f2330}
.x-card .detail{font-size:.84rem;color:#785a50;line-height:1.5;margin:8px 0}
.x-card a{color:#ae222c;text-decoration:none;font-weight:800}
div[data-baseweb="select"]>div,div[data-baseweb="input"]{background:#fff!important;border:1px solid #ead4b6!important;border-radius:11px!important;color:#392923!important}
div[data-baseweb="select"] span,div[data-baseweb="input"] input{color:#392923!important}
div[data-baseweb="input"] input::placeholder{color:#9c857a!important}
[data-testid="stWidgetLabel"] p{color:#80574d!important;font-weight:700}
@media(max-width:700px){.block-container{padding-top:.6rem}.x-hero{padding:16px;margin-bottom:8px}.x-title{font-size:1.5rem}.x-card{min-height:0}}
</style>
<div class="x-hero">
  <div class="x-label">PHƯƠNG TUẤN · CHỨNG KHOÁN AGRIBANK · CHI NHÁNH MIỀN TRUNG</div>
  <div class="x-title">🌐 X INSIGHTS</div>
  <div class="x-sub">Góc nhìn toàn cầu · 13 tài khoản X đáng theo dõi</div>
</div>
""", unsafe_allow_html=True)

st.caption("Danh sách nguồn tham khảo đa chiều, gồm cả quan điểm cá nhân. Không đại diện cho Agriseco và không phải khuyến nghị đầu tư.")
st.markdown("### 🌐 13 NGUỒN X")
topics = ["Tất cả"] + list(dict.fromkeys(account[2] for account in ACCOUNTS))
left, right = st.columns([1, 2])
with left:
    topic = st.selectbox("Chủ đề", topics)
with right:
    keyword = st.text_input("Tìm tài khoản", placeholder="Tên tác giả, @username, chủ đề…")
filtered = [
    account for account in ACCOUNTS
    if (topic == "Tất cả" or account[2] == topic)
    and (not keyword or keyword.casefold() in " ".join(account).casefold())
]
st.caption(f"{len(filtered)}/{len(ACCOUNTS)} tài khoản · Chọn liên kết để xem bài mới nhất trên X")
if not filtered:
    st.info("Không có tài khoản phù hợp.")

for i in range(0, len(filtered), 3):
    columns = st.columns(3)
    for column, (name, handle, category, description) in zip(columns, filtered[i:i+3]):
        url = f"https://x.com/{handle}"
        with column:
            st.markdown(
                '<div class="x-card">'
                f'<strong>{html.escape(name)}</strong>'
                f'<div class="detail">@{html.escape(handle)} · {html.escape(category)}'
                f'<br>{html.escape(description)}</div>'
                f'<a href="{url}" target="_blank" rel="noopener noreferrer">Mở trang X ↗</a>'
                '</div>',
                unsafe_allow_html=True,
            )
st.caption("X Insights · Danh sách nguồn X miễn phí · Daily Market giữ nguyên.")
