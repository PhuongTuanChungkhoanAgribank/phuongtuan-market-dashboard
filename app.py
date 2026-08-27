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
FETCH_SCRIPT = ROOT / "scripts" / "fetch_news.py"
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

st.markdown("""
<style>
:root{--orange:#F7A21F;--orange2:#FFBF45;--red:#B81D2D;--ink:#F7F8FF}
.stApp{background:radial-gradient(circle at 8% 12%,rgba(247,162,31,.10),transparent 24%),radial-gradient(circle at 88% 18%,rgba(184,29,45,.14),transparent 25%),radial-gradient(circle at 55% 70%,rgba(93,39,173,.16),transparent 34%),linear-gradient(135deg,#07091E 0%,#111036 45%,#1A0B36 100%);color:var(--ink)}
.stApp:before{content:"";position:fixed;inset:0;pointer-events:none;opacity:.22;background:repeating-linear-gradient(90deg,transparent 0 79px,rgba(152,124,255,.11) 80px,transparent 81px),repeating-linear-gradient(0deg,transparent 0 39px,rgba(152,124,255,.07) 40px,transparent 41px);mask-image:linear-gradient(to bottom,black 0%,transparent 72%);z-index:0}
.block-container{position:relative;z-index:1;max-width:1500px;padding-top:.8rem;padding-bottom:2rem}
.hero{position:relative;overflow:hidden;border-radius:0 0 22px 22px;min-height:190px;padding:27px 32px 25px;margin:0 0 20px;background:radial-gradient(circle at 88% 38%,rgba(247,162,31,.23),transparent 20%),radial-gradient(circle at 75% 115%,rgba(184,29,45,.38),transparent 34%),radial-gradient(circle at 56% 60%,rgba(102,43,201,.30),transparent 33%),linear-gradient(115deg,#0B0D2A 0%,#151641 43%,#251044 100%);box-shadow:0 18px 45px rgba(0,0,0,.34)}
.hero:before{content:"";position:absolute;inset:0;opacity:.34;background:repeating-linear-gradient(90deg,transparent 0 78px,rgba(255,255,255,.045) 79px 80px),repeating-linear-gradient(0deg,transparent 0 38px,rgba(255,255,255,.035) 39px 40px);pointer-events:none}
.hero:after{content:"";position:absolute;width:760px;height:310px;right:-55px;bottom:-178px;transform:rotate(-7deg);border-top:2px solid rgba(247,162,31,.38);border-radius:50%;box-shadow:0 -18px 0 -9px rgba(118,71,222,.18),90px -45px 0 -34px rgba(247,162,31,.26),190px -75px 0 -65px rgba(184,29,45,.30);pointer-events:none}
.hero-glow{position:absolute;right:7%;top:12px;width:360px;height:180px;background:radial-gradient(ellipse,rgba(111,57,211,.28),transparent 68%);pointer-events:none}
.hero-content{position:relative;z-index:2;max-width:72%}.hero-title{color:#fff;font-size:1.52rem;line-height:1.18;font-weight:950;letter-spacing:.015em;text-shadow:0 2px 14px rgba(0,0,0,.28)}.hero-title .accent{color:var(--orange)}.hero-tagline{color:#F0F1FF;font-size:.9rem;font-weight:850;margin-top:.48rem}.hero-note{display:inline-block;color:var(--orange);font-size:.76rem;font-weight:900;margin-top:.72rem;padding-top:.42rem;border-top:2px solid var(--orange);letter-spacing:.08em}
.update-box{position:absolute;z-index:3;top:24px;right:30px;text-align:right;color:rgba(255,255,255,.62);font-size:.68rem}.update-box b{color:var(--orange2);font-size:.92rem}
.section-title{font-size:1.02rem;font-weight:950;color:#fff;margin:1rem 0 .75rem;padding-left:.75rem;border-left:4px solid var(--orange)}
[data-testid="stMetric"]{background:linear-gradient(145deg,rgba(40,22,78,.82),rgba(16,16,48,.86));border:1px solid rgba(154,126,255,.18);border-radius:15px;padding:11px 15px;box-shadow:0 8px 24px rgba(0,0,0,.18)}[data-testid="stMetricLabel"]{color:#B8B9D2!important}[data-testid="stMetricValue"]{color:#fff!important}
div[data-baseweb="input"]{background:rgba(255,255,255,.055)!important;border:1px solid rgba(154,126,255,.18)!important;border-radius:12px!important}div[data-baseweb="input"] input{color:#fff!important}div[data-baseweb="input"] input::placeholder{color:#8E90AC!important}
div[role="radiogroup"]{gap:9px}div[role="radiogroup"] label{background:rgba(38,21,75,.62);border:1px solid rgba(154,126,255,.18);border-radius:999px;padding:7px 13px}div[role="radiogroup"] p{color:#E9E9F7!important;font-weight:700}
.stButton>button{background:linear-gradient(135deg,#F7A21F 0%,#B81D2D 100%)!important;color:#fff!important;border:1px solid rgba(255,255,255,.22)!important;border-radius:12px!important;font-weight:900!important;min-height:42px;box-shadow:0 8px 22px rgba(184,29,45,.28)}.stButton>button:hover{filter:brightness(1.08);transform:translateY(-1px)}
.card{background:linear-gradient(145deg,rgba(35,19,68,.96),rgba(17,14,43,.97));border:1px solid rgba(154,126,255,.22);border-radius:16px;padding:16px;min-height:205px;box-shadow:0 10px 28px rgba(0,0,0,.24)}.card:before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:linear-gradient(180deg,var(--orange),var(--red))}.card{position:relative;overflow:hidden}.pill{display:inline-block;background:rgba(247,162,31,.13);color:var(--orange2);border:1px solid rgba(247,162,31,.26);border-radius:999px;padding:4px 8px;font-size:.66rem;font-weight:900}.cat{display:inline-block;background:rgba(184,29,45,.15);color:#FF7784;border:1px solid rgba(184,29,45,.25);border-radius:999px;padding:4px 8px;font-size:.66rem;font-weight:900;margin-left:5px}.time{float:right;color:#8F91B0;font-size:.65rem}.headline{color:#fff;font-size:1rem;font-weight:900;line-height:1.42;margin-top:.72rem}.summary{font-size:.81rem;line-height:1.52;color:#B7B8CD;margin-top:.44rem}.source{color:#8F91AB;font-size:.65rem;margin-top:.78rem}a{color:var(--orange)!important;font-weight:750}.footer-note{color:#777A9A;font-size:.68rem;margin-top:1.25rem;padding-top:.8rem;border-top:1px solid rgba(255,255,255,.08)}
@media(max-width:800px){.hero{min-height:210px;padding:22px}.hero-content{max-width:100%}.hero-title{font-size:1.15rem}.hero-tagline{font-size:.76rem}.update-box{top:18px;right:18px}.card{min-height:180px}}
</style>
""",unsafe_allow_html=True)

def load_data():
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8")) if DATA_FILE.exists() else {"updated_at":"—","cards":[]}
    except Exception:
        return {"updated_at":"—","cards":[]}

def clean_text(text:str)->str:
    text=html.unescape(str(text or "")).replace("\xa0"," ")
    text=re.sub(r"\s+"," ",text)
    for old in ("Prototype: ","Prototype – ","Prototype - "):
        text=text.replace(old,"")
    return text.strip()

def display_tag(item:dict)->str:
    ticker=(item.get("ticker") or "").strip()
    if ticker:
        ex=(item.get("exchange") or "").strip()
        return f"[{ex}: {ticker}]" if ex else f"[{ticker}]"
    return (item.get("region") or item.get("tag") or "").strip()

def display_time(value:str)->str:
    try:return datetime.fromisoformat(value.replace("Z","+00:00")).astimezone(VN_TZ).strftime("%d/%m %H:%M")
    except Exception:return value or ""

data=load_data();cards=data.get("cards",[]);updated_at=data.get("updated_at","—")
st.markdown(f'''<div class="hero"><div class="hero-glow"></div><div class="hero-content"><div class="hero-title">PHƯƠNG TUẤN <span class="accent">- CHỨNG KHOÁN AGRIBANK</span><br>CHI NHÁNH MIỀN TRUNG</div><div class="hero-tagline">NGƯỜI AGRIBANK LÀM CHỨNG KHOÁN</div><div class="hero-note">DAILY MARKET</div></div><div class="update-box">DỮ LIỆU CẬP NHẬT<br><b>{html.escape(str(updated_at))}</b></div></div>''',unsafe_allow_html=True)

c1,c2,c3=st.columns([1.55,1.25,2.2])
with c1:
    components.html("""<div style='font-family:Arial,sans-serif;color:#F7F8FF'><div style='font-size:10px;letter-spacing:.08em;color:#B7B9D0'>GIỜ HIỆN TẠI · VIỆT NAM</div><div id='clock' style='font-size:16px;font-weight:800;color:#FFBF45'></div><script>function tick(){const n=new Date();document.getElementById('clock').textContent=new Intl.DateTimeFormat('vi-VN',{timeZone:'Asia/Ho_Chi_Minh',hour:'2-digit',minute:'2-digit',second:'2-digit',day:'2-digit',month:'2-digit',year:'numeric',hour12:false}).format(n)}tick();setInterval(tick,1000);</script></div>""",height=42,scrolling=False)
with c2:
    if st.button("🔄 CẬP NHẬT TIN NGAY",use_container_width=True):
        try:
            r=subprocess.run([sys.executable,str(FETCH_SCRIPT)],cwd=str(ROOT),capture_output=True,text=True,timeout=120)
            if r.returncode==0: st.success("Đã cập nhật tin."); st.rerun()
            else: st.error("Cập nhật chưa thành công. Kiểm tra GitHub Actions.")
        except Exception as e: st.error(f"Không thể cập nhật: {e}")
with c3: st.caption("Tự động cập nhật tin: mỗi 5 phút · GitHub Actions")

world=sum(x.get("category")=="THẾ GIỚI" for x in cards);local=sum(x.get("category")=="TRONG NƯỚC" for x in cards);corp=sum(x.get("category")=="DOANH NGHIỆP" for x in cards);fund=sum(x.get("category")=="QUỸ" for x in cards)
m1,m2,m3,m4,m5=st.columns(5);m1.metric("Tổng tin",len(cards));m2.metric("Doanh nghiệp",corp);m3.metric("Trong nước",local);m4.metric("Thế giới",world);m5.metric("Quỹ",fund)

search=st.text_input("Tìm kiếm",placeholder="Nhập mã cổ phiếu, doanh nghiệp, chủ đề hoặc từ khóa…");category=st.radio("Bộ lọc",["Tất cả","THẾ GIỚI","TRONG NƯỚC","DOANH NGHIỆP","QUỸ"],horizontal=True,label_visibility="collapsed")
q=(search or "").casefold().strip();visible=[]
for item in cards:
    if category!="Tất cả" and item.get("category")!=category: continue
    headline=clean_text(item.get("headline_vi",""));summary=clean_text(item.get("summary_vi",""));hay=" ".join([headline,summary,item.get("ticker","")," ".join(item.get("tickers",[]) or []),item.get("tag",""),item.get("region",""),item.get("source","")]).casefold()
    if not q or q in hay: visible.append((item,headline,summary))

st.markdown('<div class="section-title">TIN TRONG NGÀY</div>',unsafe_allow_html=True)
if not visible: st.info("Chưa có tin phù hợp với bộ lọc hiện tại.")
else:
    for start in range(0,len(visible),3):
        cols=st.columns(3,gap="medium")
        for col,(item,headline,summary) in zip(cols,visible[start:start+3]):
            with col:
                tag=display_tag(item);url=item.get("source_url") or item.get("url") or "#";tag_html=f"<span class='pill'>{html.escape(tag)}</span>" if tag else "";cat_html=f"<span class='cat'>{html.escape(str(item.get('category','—')))}</span>";source=html.escape(str(item.get('source','')));ph=html.escape(str(display_time(str(item.get('published_at','')))));u=html.escape(str(url),quote=True)
                st.markdown(f"<div class='card'>{tag_html}{cat_html}<span class='time'>{ph}</span><div class='headline'>{html.escape(headline)}</div><div class='summary'>{html.escape(summary)}</div><div class='source'>{source} · <a href='{u}' target='_blank'>Nguồn ↗</a></div></div>",unsafe_allow_html=True);st.write("")
st.markdown('<div class="footer-note">PHƯƠNG TUẤN · CHỨNG KHOÁN AGRIBANK CHI NHÁNH MIỀN TRUNG · Bản tin cung cấp thông tin, không phải khuyến nghị đầu tư.</div>',unsafe_allow_html=True)
