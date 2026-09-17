import html
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Phương Tuấn - Chứng khoán Agribank Chi nhánh Miền Trung", page_icon="📈", layout="wide")
ROOT = Path(__file__).parent
DATA_FILE = ROOT / "data" / "daily_news.json"
FUND_DATA_FILE = ROOT / "data" / "weekly_fund_portfolios.json"
FETCH_SCRIPT = ROOT / "scripts" / "fetch_news.py"
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

st.markdown("""
<style>
:root{--orange:#F7A21F;--orange2:#FFB52A;--red:#B81D2D;--red2:#CC2D32;--ink:#34231F;--muted:#7E6B63;--cream:#FFF9F0;--line:#F1DEC4}
.stApp{background:radial-gradient(circle at 90% 4%,rgba(247,162,31,.13),transparent 24%),radial-gradient(circle at 5% 35%,rgba(184,29,45,.045),transparent 25%),linear-gradient(180deg,#FFFDF9 0%,#FFF9F0 54%,#FFFDF9 100%);color:var(--ink)}
.stApp:before{content:"";position:fixed;inset:0;pointer-events:none;background:linear-gradient(135deg,transparent 0 74%,rgba(247,162,31,.035) 74% 78%,transparent 78%);z-index:0}
.block-container{position:relative;z-index:1;max-width:1500px;padding-top:.8rem;padding-bottom:2rem}
.hero{position:relative;overflow:hidden;border:1px solid #F4DEC0;border-radius:0 0 24px 24px;min-height:190px;padding:28px 32px 26px;margin:0 0 20px;background:radial-gradient(circle at 90% 18%,rgba(247,162,31,.23),transparent 24%),linear-gradient(118deg,#FFFFFF 0%,#FFF9EE 58%,#FFE8B8 100%);box-shadow:0 14px 36px rgba(118,74,28,.10)}
.hero:before{content:"";position:absolute;right:-80px;top:-125px;width:620px;height:330px;border:44px solid rgba(247,162,31,.10);border-radius:50%;transform:rotate(-10deg);pointer-events:none}.hero:after{content:"";position:absolute;right:-40px;bottom:-175px;width:730px;height:280px;border-top:2px solid rgba(184,29,45,.18);border-radius:50%;box-shadow:0 -15px 0 -8px rgba(247,162,31,.15);pointer-events:none}.hero-glow{position:absolute;right:7%;top:8px;width:360px;height:180px;background:radial-gradient(ellipse,rgba(255,181,42,.20),transparent 68%);pointer-events:none}
.hero-content{position:relative;z-index:2;max-width:72%}.hero-title{color:#8F1722;font-size:1.52rem;line-height:1.18;font-weight:950;letter-spacing:.015em}.hero-title .accent{color:var(--orange)}.hero-tagline{color:#68463D;font-size:.9rem;font-weight:850;margin-top:.48rem}.hero-note{display:inline-block;color:var(--red);font-size:.76rem;font-weight:950;margin-top:.72rem;padding-top:.42rem;border-top:2px solid var(--orange);letter-spacing:.09em}
.update-box{position:absolute;z-index:3;top:24px;right:30px;text-align:right;color:#9B7768;font-size:.68rem}.update-box b{color:var(--red);font-size:.92rem}
.section-title{font-size:1.02rem;font-weight:950;color:#8F1722;margin:1rem 0 .75rem;padding-left:.75rem;border-left:4px solid var(--orange)}
[data-testid="stMetric"]{background:rgba(255,255,255,.92);border:1px solid #F0DEC6;border-radius:15px;padding:11px 15px;box-shadow:0 8px 22px rgba(116,73,32,.07)}[data-testid="stMetricLabel"]{color:#8A6E63!important}[data-testid="stMetricValue"]{color:#9C1F29!important}
[data-testid="stTextInput"] label,[data-testid="stCaptionContainer"],.stCaption{color:#7E6B63!important}div[data-baseweb="input"]{background:#fff!important;border:1px solid #EBD7BC!important;border-radius:12px!important;box-shadow:0 5px 14px rgba(116,73,32,.04)}div[data-baseweb="input"] input{color:#3C2A24!important}div[data-baseweb="input"] input::placeholder{color:#A18F86!important}
div[role="radiogroup"]{gap:9px;flex-wrap:wrap}div[role="radiogroup"] label{background:#FFF7EA;border:1px solid #EFCF9F;border-radius:999px;padding:7px 13px}div[role="radiogroup"] label:hover{background:#FFEDCF;border-color:#F7A21F}div[role="radiogroup"] p{color:#7D342E!important;font-weight:800}div[role="radiogroup"] [data-checked="true"]+div p{color:#B81D2D!important}
.stButton>button{background:linear-gradient(135deg,#F7A21F 0%,#D84A2F 54%,#B81D2D 100%)!important;color:#fff!important;border:0!important;border-radius:12px!important;font-weight:900!important;min-height:42px;box-shadow:0 8px 20px rgba(184,29,45,.18)}.stButton>button:hover{filter:brightness(1.04);transform:translateY(-1px);box-shadow:0 10px 24px rgba(184,29,45,.24)}
.card{background:#FFFFFF;border:1px solid #EFDDC5;border-radius:16px;padding:16px;min-height:205px;box-shadow:0 9px 24px rgba(116,73,32,.07);position:relative;overflow:hidden}.card:before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:linear-gradient(180deg,var(--orange),var(--red))}.pill{display:inline-block;background:#FFF1D8;color:#A85A00;border:1px solid #F5D398;border-radius:999px;padding:4px 8px;font-size:.66rem;font-weight:900}.cat{display:inline-block;background:#FFF0F0;color:#B81D2D;border:1px solid #F1C8CB;border-radius:999px;padding:4px 8px;font-size:.66rem;font-weight:900;margin-left:5px}.time{float:right;color:#A28E84;font-size:.65rem}.headline{color:#5C2725;font-size:1rem;font-weight:900;line-height:1.42;margin-top:.72rem}.summary{font-size:.81rem;line-height:1.52;color:#6F625D;margin-top:.44rem}.source{color:#9A847A;font-size:.65rem;margin-top:.78rem}a{color:#C52A2F!important;font-weight:800}.footer-note{color:#9A847A;font-size:.68rem;margin-top:1.25rem;padding-top:.8rem;border-top:1px solid #F0E1CE}
.fund-card{background:#FFFFFF;border:1px solid #EBCFAD;border-radius:16px;padding:16px;min-height:205px;box-shadow:0 9px 24px rgba(116,73,32,.07)}.fund-name{color:#9C1F29;font-size:1rem;font-weight:900}.fund-meta{color:#9A847A;font-size:.66rem;margin-top:.35rem}.fund-holdings{color:#5F514C;font-size:.82rem;line-height:1.55;margin-top:.75rem}.fund-note{color:#9A847A;font-size:.68rem;margin-top:.7rem}
.history-card{background:linear-gradient(115deg,#FFF7E8,#FFFDF9 58%,#FFF2E8);border:1px solid #EBCB9D;border-radius:16px;padding:14px 16px;margin:12px 0 18px;box-shadow:0 8px 20px rgba(116,73,32,.06)}.history-title{color:#9C1F29;font-size:.98rem;font-weight:900}.history-help{color:#77645C;font-size:.72rem;line-height:1.45;margin-top:.35rem}.history-link{display:inline-block;margin-top:.65rem;padding:7px 11px;border-radius:10px;background:#FFF0D5;border:1px solid #EDC27D;color:#B81D2D!important;font-size:.74rem;font-weight:900;text-decoration:none!important}.history-link:hover{background:#FFE4B5}
.notice-help{color:#77645C;font-size:.72rem;margin:-.4rem 0 .8rem .8rem}
[data-testid="stAlert"]{background:#FFF7EA;color:#5F514C;border-color:#EBCB9D}
@media(max-width:800px){.hero{min-height:210px;padding:22px}.hero-content{max-width:100%}.hero-title{font-size:1.15rem}.hero-tagline{font-size:.76rem}.update-box{top:18px;right:18px}.card{min-height:180px}}
</style>
""",unsafe_allow_html=True)

def load_json(path, fallback):
    try:return json.loads(path.read_text(encoding="utf-8")) if path.exists() else fallback
    except Exception:return fallback

def clean_text(text:str)->str:
    text=html.unescape(str(text or "")).replace("\xa0"," ");text=re.sub(r"\s+"," ",text)
    for old in ("Prototype: ","Prototype – ","Prototype - "):text=text.replace(old,"")
    return text.strip()

def display_tag(item:dict)->str:
    ticker=(item.get("ticker") or "").strip()
    if ticker:
        ex=(item.get("exchange") or "").strip();return f"[{ex}: {ticker}]" if ex else f"[{ticker}]"
    return (item.get("region") or item.get("tag") or "").strip()

def display_time(value:str)->str:
    try:return datetime.fromisoformat(value.replace("Z","+00:00")).astimezone(VN_TZ).strftime("%d/%m %H:%M")
    except Exception:return value or ""

def fund_summary(fund:dict)->str:
    parts=[]
    for item in (fund.get("holdings",[]) or [])[:10]:
        ticker=clean_text(item.get("ticker",""));weight=clean_text(item.get("weight_pct",""))
        if ticker:parts.append(f"{ticker} ({weight}%)" if weight else ticker)
    return ", ".join(parts)

data=load_json(DATA_FILE,{"updated_at":"—","cards":[]});all_cards=data.get("cards",[]);cards=[x for x in all_cards if x.get("category")!="QUỸ"];updated_at=data.get("updated_at","—")
fund_payload=load_json(FUND_DATA_FILE,{"updated_at":"—","funds":[]});funds=fund_payload.get("funds",[]) or []

st.markdown(f'''<div class="hero"><div class="hero-glow"></div><div class="hero-content"><div class="hero-title">PHƯƠNG TUẤN <span class="accent">- CHỨNG KHOÁN AGRIBANK</span><br>CHI NHÁNH MIỀN TRUNG</div><div class="hero-tagline">NGƯỜI AGRIBANK LÀM CHỨNG KHOÁN</div><div class="hero-note">DAILY MARKET</div></div><div class="update-box">DỮ LIỆU CẬP NHẬT<br><b>{html.escape(str(updated_at))}</b></div></div>''',unsafe_allow_html=True)

c1,c2,c3=st.columns([1.55,1.25,2.2])
with c1:
    components.html("""<div style='font-family:Arial,sans-serif;color:#4A342D'><div style='font-size:10px;letter-spacing:.08em;color:#8A7065'>GIỜ HIỆN TẠI · VIỆT NAM</div><div id='clock' style='font-size:16px;font-weight:900;color:#B81D2D'></div><script>function tick(){const n=new Date();document.getElementById('clock').textContent=new Intl.DateTimeFormat('vi-VN',{timeZone:'Asia/Ho_Chi_Minh',hour:'2-digit',minute:'2-digit',second:'2-digit',day:'2-digit',month:'2-digit',year:'numeric',hour12:false}).format(n)}tick();setInterval(tick,1000);</script></div>""",height=42,scrolling=False)
with c2:
    if st.button("🔄 CẬP NHẬT TIN NGAY",use_container_width=True):
        try:
            r=subprocess.run([sys.executable,str(FETCH_SCRIPT)],cwd=str(ROOT),capture_output=True,text=True,timeout=180)
            if r.returncode==0:st.success("Đã cập nhật tin.");st.rerun()
            else:st.error("Cập nhật chưa thành công. Kiểm tra GitHub Actions.")
        except Exception as e:st.error(f"Không thể cập nhật: {e}")
with c3:st.caption("Tự động cập nhật tin: khoảng mỗi 15 phút · GitHub Actions")

world=sum(x.get("category")=="THẾ GIỚI" for x in cards);local=sum(x.get("category")=="TRONG NƯỚC" for x in cards);corp=sum(x.get("category")=="DOANH NGHIỆP" for x in cards);notice=sum(x.get("category")=="THÔNG BÁO" for x in cards)
m=st.columns(6);m[0].metric("Tổng tin",len(cards));m[1].metric("Doanh nghiệp",corp);m[2].metric("Trong nước",local);m[3].metric("Thế giới",world);m[4].metric("Thông báo từ UBCK",notice);m[5].metric("Quỹ theo dõi",len(funds))

search=st.text_input("Tìm kiếm",placeholder="Nhập mã cổ phiếu, doanh nghiệp, chủ đề hoặc từ khóa…")
category=st.radio("Bộ lọc",["Tất cả","THẾ GIỚI","TRONG NƯỚC","DOANH NGHIỆP","THÔNG BÁO TỪ UBCK","QUỸ"],horizontal=True,label_visibility="collapsed")
q=(search or "").casefold().strip()

st.markdown('''<div class="history-card"><div class="history-title">🔎 TRA CỨU LỊCH SỬ</div><div class="history-help">Xem lại bản tin theo <b>ngày quá khứ</b>, mã cổ phiếu, doanh nghiệp hoặc từ khóa. Chọn ngày trước, sau đó nhập từ khóa để thu hẹp kết quả.</div><a class="history-link" href="/Tra_cuu_lich_su" target="_self">MỞ TRA CỨU LỊCH SỬ ↗</a></div>''', unsafe_allow_html=True)

if category=="QUỸ":
    st.markdown('<div class="section-title">DANH MỤC QUỸ · CẬP NHẬT HÀNG TUẦN</div>',unsafe_allow_html=True)
    st.caption(f"Snapshot gần nhất: {fund_payload.get('updated_at','—')} · Danh mục được cập nhật theo kỳ công bố của quỹ, không phải dữ liệu thời gian thực.")
    filtered=[]
    for fund in funds:
        fund_name=fund.get("fund_name") or fund.get("fund") or ""
        blob=" ".join([fund_name,fund.get("manager",""),fund_summary(fund)]).casefold()
        if not q or q in blob:filtered.append(fund)
    if not filtered:st.info("Chưa có dữ liệu danh mục quỹ phù hợp.")
    for i in range(0,len(filtered),3):
        cols=st.columns(3)
        for col,fund in zip(cols,filtered[i:i+3]):
            with col:
                name=html.escape(clean_text(fund.get("fund_name") or fund.get("fund") or "Quỹ"));manager=html.escape(clean_text(fund.get("manager","")));summary=html.escape(fund_summary(fund) or "Chưa trích xuất được danh mục.");url=html.escape((fund.get("source_url") or fund.get("url") or "#"),quote=True);updated=html.escape(clean_text(fund.get("updated_at") or fund.get("fetched_at") or ""))
                meta=" · ".join(x for x in [manager, f"Cập nhật: {updated}" if updated else ""] if x)
                st.markdown(f'<div class="fund-card"><div class="fund-name">{name}</div><div class="fund-meta">{meta}</div><div class="fund-holdings">{summary}</div><div class="fund-note">Danh mục/tỷ trọng theo kỳ công bố gần nhất. · <a href="{url}" target="_blank">Nguồn ↗</a></div></div>',unsafe_allow_html=True)
else:
    selected_category="THÔNG BÁO" if category=="THÔNG BÁO TỪ UBCK" else category
    filtered=[]
    for item in cards:
        if selected_category!="Tất cả" and item.get("category")!=selected_category:continue
        blob=" ".join([item.get("headline_vi",""),item.get("summary_vi",""),item.get("source",""),item.get("ticker",""),item.get("company",""),item.get("region","")]).casefold()
        if q and q not in blob:continue
        filtered.append(item)
    if category=="THÔNG BÁO TỪ UBCK":
        st.markdown('<div class="section-title">THÔNG BÁO TỪ ỦY BAN CHỨNG KHOÁN</div>',unsafe_allow_html=True)
        st.markdown('<div class="notice-help">Nguồn chính thức và ưu tiên: <b>Ủy ban Chứng khoán Nhà nước (SSC), HOSE/HSX và HNX</b> — tập trung cảnh báo, kiểm soát/hạn chế giao dịch, xử phạt và công bố thông tin liên quan doanh nghiệp.</div>',unsafe_allow_html=True)
    else:st.markdown('<div class="section-title">TIN TRONG NGÀY</div>',unsafe_allow_html=True)
    if not filtered:st.info("Chưa có tin phù hợp với bộ lọc hiện tại.")
    for i in range(0,len(filtered),3):
        cols=st.columns(3)
        for col,item in zip(cols,filtered[i:i+3]):
            with col:
                tag=html.escape(display_tag(item));cat_label="THÔNG BÁO TỪ UBCK" if item.get("category")=="THÔNG BÁO" else item.get("category","");cat=html.escape(cat_label);headline=html.escape(clean_text(item.get("headline_vi","")));summary=html.escape(clean_text(item.get("summary_vi","")));source=html.escape(clean_text(item.get("source","")));url=html.escape((item.get("source_url") or item.get("url") or "#"),quote=True);t=html.escape(display_time(item.get("published_at","")))
                st.markdown(f'<div class="card"><span class="pill">{tag or source}</span><span class="cat">{cat}</span><span class="time">{t}</span><div class="headline">{headline}</div><div class="summary">{summary}</div><div class="source">{source} · <a href="{url}" target="_blank">Nguồn ↗</a></div></div>',unsafe_allow_html=True)

st.markdown('<div class="footer-note">PHƯƠNG TUẤN · CHỨNG KHOÁN AGRIBANK CHI NHÁNH MIỀN TRUNG · Bản tin cung cấp thông tin, không phải khuyến nghị đầu tư.</div>',unsafe_allow_html=True)