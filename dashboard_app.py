import os
import math
import numpy as np
import pandas as pd
import streamlit as st
import requests
import folium
import plotly.express as px
import plotly.graph_objects as go
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
from sqlalchemy import create_engine
from dotenv import load_dotenv
from explorar_page import render_explorar
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

load_dotenv()
DATABASE_URL        = os.getenv("DATABASE_URL")
WEATHER_API_KEY     = os.getenv("WEATHER_API_KEY", "")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

# ══════════════════════════════════════════
#  PAGE CONFIG
# ══════════════════════════════════════════
st.set_page_config(
    page_title="Onde é o Rolê? · Recife",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════
#  SESSION STATE
# ══════════════════════════════════════════
_defaults = {
    "page": "executiva",
    "recommendations": [],
    "user_lat": -8.1130,
    "user_lon": -34.8953,
    "user_neighborhood": "Boa Viagem",
    "searched": False,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════
#  CSS GLOBAL
# ══════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── App background ── */
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(ellipse 70% 50% at 20% -10%, rgba(29,78,216,0.22) 0%, transparent 60%),
        radial-gradient(ellipse 50% 40% at 85% 110%, rgba(5,150,105,0.16) 0%, transparent 60%),
        #08101f !important;
}
[data-testid="block-container"] { background: transparent !important; padding-top: 0 !important; }
.main .block-container { padding-top: 1rem !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.5); border-radius: 99px; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #0b1023 !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
section[data-testid="stSidebar"] > div { padding: 0 !important; }
section[data-testid="stSidebar"] * { color: #94a3b8 !important; }

/* ── Nav radio — ícones de linha, sem emoji ── */
[data-testid="stRadio"] > label { display: none !important; }
[data-testid="stRadio"] > div[role="radiogroup"] {
    display: flex !important;
    flex-direction: column !important;
    gap: 3px !important;
}
[data-testid="stRadio"] label {
    position: relative !important;
    background: transparent !important;
    border: none !important;
    border-left: 4px solid transparent !important;
    border-radius: 10px !important;
    padding: 12px 16px 12px 46px !important;
    color: #64748b !important;
    font-weight: 500 !important;
    cursor: pointer !important;
    transition: background 0.15s, color 0.15s, border-color 0.15s !important;
    width: 100% !important;
    margin: 0 !important;
}
[data-testid="stRadio"] label::before {
    content: '';
    position: absolute;
    left: 16px; top: 50%;
    transform: translateY(-50%);
    width: 18px; height: 18px;
    background-repeat: no-repeat;
    background-position: center;
    background-size: contain;
    opacity: .5;
    transition: opacity .15s, filter .15s;
}
/* ícone 1 — Visão Executiva (casa) */
[data-testid="stRadio"] label:nth-of-type(1)::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z'/%3E%3Cpolyline points='9 22 9 12 15 12 15 22'/%3E%3C/svg%3E");
}
/* ícone 2 — Explorar (lupa) */
[data-testid="stRadio"] label:nth-of-type(2)::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='11' cy='11' r='8'/%3E%3Cline x1='21' y1='21' x2='16.65' y2='16.65'/%3E%3C/svg%3E");
}
/* ícone 3 — Análise (barras) */
[data-testid="stRadio"] label:nth-of-type(3)::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cline x1='12' y1='20' x2='12' y2='10'/%3E%3Cline x1='18' y1='20' x2='18' y2='4'/%3E%3Cline x1='6' y1='20' x2='6' y2='16'/%3E%3C/svg%3E");
}
/* ícone 4 — Recomendações (alvo) */
[data-testid="stRadio"] label:nth-of-type(4)::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'/%3E%3Ccircle cx='12' cy='12' r='6'/%3E%3Ccircle cx='12' cy='12' r='2'/%3E%3C/svg%3E");
}
/* ícone 5 — Sobre (info) */
[data-testid="stRadio"] label:nth-of-type(5)::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'/%3E%3Cline x1='12' y1='16' x2='12' y2='12'/%3E%3Cline x1='12' y1='8' x2='12.01' y2='8'/%3E%3C/svg%3E");
}
[data-testid="stRadio"] label:hover {
    background: rgba(255,255,255,0.05) !important;
    color: #cbd5e1 !important;
}
[data-testid="stRadio"] label:hover::before { opacity: .8; }
[data-testid="stRadio"] label:has(input:checked) {
    background: linear-gradient(135deg,rgba(99,102,241,0.22),rgba(99,102,241,0.07)) !important;
    color: white !important;
    border-left: 4px solid #6366f1 !important;
    padding-left: 42px !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.06), 0 4px 14px rgba(99,102,241,0.22) !important;
}
[data-testid="stRadio"] label:has(input:checked)::before {
    opacity: 1;
    filter: brightness(0) invert(1);
}
[data-testid="stRadio"] label:has(input:checked)::after {
    content: '';
    position: absolute;
    right: 14px; top: 50%;
    transform: translateY(-50%);
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #22c55e;
    box-shadow: 0 0 8px rgba(34,197,94,0.7);
}
[data-testid="stRadio"] div[data-testid="stMarkdownContainer"] { display: block !important; }
[data-testid="stRadio"] div[data-testid="stMarkdownContainer"] p {
    white-space: pre-line !important;
    line-height: 1.4 !important;
    font-size: 13px !important;
    color: #94a3b8 !important;
    margin: 0 !important;
}
[data-testid="stRadio"] div[data-testid="stMarkdownContainer"] p::first-line {
    font-size: 15px;
    font-weight: 700;
    color: #cbd5e1;
}
[data-testid="stRadio"] label:has(input:checked) div[data-testid="stMarkdownContainer"] p { color: #c7d2fe !important; }
[data-testid="stRadio"] label:has(input:checked) div[data-testid="stMarkdownContainer"] p::first-line { color: #ffffff; }

/* ── Divider ── */
hr { border-color: rgba(255,255,255,0.06) !important; margin: 14px 0 !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.04) !important;
    border-radius: 12px; padding: 3px; gap: 3px;
    border: 1px solid rgba(255,255,255,0.07);
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important; color: #64748b !important;
    border-radius: 9px; font-size: 13px; font-weight: 600; padding: 8px 18px;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #1d4ed8, #0f766e) !important;
    color: white !important;
}

/* ── Form ── */
[data-testid="stForm"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 16px !important; padding: 20px !important;
}
.stSelectbox > div > div,
.stNumberInput > div > div,
.stTextInput > div > div {
    background: rgba(255,255,255,0.06) !important;
    border-color: rgba(255,255,255,0.1) !important;
    border-radius: 10px !important; color: white !important;
}
.stSelectbox label, .stNumberInput label, .stTextInput label, .stSlider label {
    color: #94a3b8 !important; font-size: 13px !important;
}
.stFormSubmitButton button {
    background: linear-gradient(135deg, #4f46e5, #0f766e) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 600 !important;
    width: 100% !important; font-size: 14px !important;
    box-shadow: 0 4px 16px rgba(79,70,229,0.3) !important;
}

/* ── DataFrame ── */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
}

/* ── Animations ── */
@keyframes fadeUp    { from{opacity:0;transform:translateY(16px)} to{opacity:1;transform:translateY(0)} }
@keyframes slideRight{ from{opacity:0;transform:translateX(-12px)} to{opacity:1;transform:translateX(0)} }
@keyframes popIn     { from{opacity:0;transform:scale(0.92)} to{opacity:1;transform:scale(1)} }

/* ── KPI card ── */
.kpi-card {
    border-radius: 18px; padding: 24px 20px 20px; min-height: 140px;
    position: relative; overflow: hidden;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    animation: popIn 0.45s cubic-bezier(0.34,1.5,0.64,1) both;
    background: linear-gradient(145deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03));
    border: 1px solid rgba(255,255,255,0.12);
    box-shadow: 0 8px 32px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.1);
    cursor: default;
}
.kpi-card:hover { transform: translateY(-4px); box-shadow: 0 16px 40px rgba(0,0,0,0.55), inset 0 1px 0 rgba(255,255,255,0.15); }
.kpi-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 40%;
    background: linear-gradient(180deg, rgba(255,255,255,0.05), transparent);
    border-radius: 18px 18px 0 0; pointer-events: none;
}
.kpi-top  { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 14px; }
.kpi-label{ color: #94a3b8; font-size: 12px; font-weight: 600; letter-spacing: 0.8px; text-transform: uppercase; }
.kpi-icon-wrap {
    width: 40px; height: 40px; border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; flex-shrink: 0; border: 1px solid rgba(255,255,255,0.1);
}
.kpi-value{ font-family:'Inter',sans-serif; font-size:38px; font-weight:800; color:white; line-height:1; margin-bottom:6px; text-shadow:0 2px 10px rgba(0,0,0,0.4); }
.kpi-sub  { color: #64748b; font-size: 12px; line-height: 1.5; }

/* ── Rec card ── */
.rec-card {
    background: linear-gradient(145deg, rgba(255,255,255,0.07), rgba(255,255,255,0.025));
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px; margin-bottom: 12px; overflow: hidden; display: flex;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.07);
    transition: transform 0.2s ease, border-color 0.2s ease;
    animation: fadeUp 0.4s ease both;
}
.rec-card:hover { transform: translateX(3px); border-color: rgba(255,255,255,0.18); }
.rec-img  { width:80px; flex-shrink:0; display:flex; align-items:center; justify-content:center; font-size:28px; border-radius:16px 0 0 16px; }
.rec-body { padding:14px 16px; flex:1; min-width:0; }
.rec-badge{ display:inline-block; font-size:10px; font-weight:700; padding:3px 8px; border-radius:99px; margin-bottom:6px; letter-spacing:0.5px; text-transform:uppercase; }
.rec-name { font-family:'Inter',sans-serif; font-size:14px; font-weight:800; color:white; margin-bottom:5px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.rec-meta { color:#94a3b8; font-size:12px; line-height:1.5; }
.rec-compat{ font-size:11px; font-weight:700; margin-top:6px; padding:2px 8px; border-radius:99px; display:inline-block; }

/* ── Rank item ── */
.rank-item {
    background: linear-gradient(145deg,rgba(255,255,255,0.07),rgba(255,255,255,0.025));
    border:1px solid rgba(255,255,255,0.1); border-radius:14px; padding:16px; margin-bottom:10px;
    display:flex; align-items:center; gap:14px;
    box-shadow:0 4px 16px rgba(0,0,0,0.35),inset 0 1px 0 rgba(255,255,255,0.07);
    transition:transform 0.18s; animation:fadeUp 0.4s ease both;
}
.rank-item:hover{ transform:translateY(-2px); }
.rank-num { width:36px; height:36px; border-radius:10px; flex-shrink:0; display:flex; align-items:center; justify-content:center; font-family:'Inter',sans-serif; font-size:16px; font-weight:800; }
.rank-thumb{ width:52px; height:52px; border-radius:12px; flex-shrink:0; display:flex; align-items:center; justify-content:center; font-size:24px; }
.rank-info { flex:1; min-width:0; }
.rank-name { font-family:'Inter',sans-serif; font-size:13px; font-weight:800; color:white; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; margin-bottom:3px; }
.rank-meta { color:#64748b; font-size:11px; }
.rank-score{ text-align:right; font-family:'Inter',sans-serif; font-size:18px; font-weight:800; color:#22c55e; flex-shrink:0; }
.rank-score small{ display:block; color:#64748b; font-size:10px; font-weight:400; font-family:'Inter',sans-serif; }

/* ── Insight item ── */
.insight-item {
    display:flex; align-items:flex-start; gap:12px; padding:14px 16px; border-radius:12px; margin-bottom:8px;
    background:linear-gradient(135deg,rgba(255,255,255,0.055),rgba(255,255,255,0.02));
    border:1px solid rgba(255,255,255,0.09);
    box-shadow:inset 0 1px 0 rgba(255,255,255,0.06);
    animation:slideRight 0.4s ease both; transition:border-color 0.2s;
}
.insight-item:hover{ border-color:rgba(255,255,255,0.16); }
.ins-icon{ width:34px; height:34px; border-radius:10px; flex-shrink:0; display:flex; align-items:center; justify-content:center; font-size:16px; }
.ins-text{ color:#cbd5e1; font-size:13px; line-height:1.55; }
.ins-text strong{ color:white; }

/* ── Section card ── */
.section-card {
    background:linear-gradient(145deg,rgba(255,255,255,0.055),rgba(255,255,255,0.02));
    border:1px solid rgba(255,255,255,0.09); border-radius:20px; padding:22px 22px 18px;
    box-shadow:0 8px 32px rgba(0,0,0,0.4),inset 0 1px 0 rgba(255,255,255,0.07); height:100%;
}
.section-title{ font-family:'Inter',sans-serif; font-size:15px; font-weight:800; color:white; margin:0 0 16px 0; display:flex; align-items:center; justify-content:space-between; }
.section-title a{ color:#6366f1 !important; font-size:12px; font-weight:600; text-decoration:none; }

/* ── Chart card ── */
.chart-card {
    background:linear-gradient(145deg,rgba(255,255,255,0.055),rgba(255,255,255,0.018));
    border:1px solid rgba(255,255,255,0.09); border-radius:16px; padding:18px 16px 4px;
    box-shadow:0 6px 24px rgba(0,0,0,0.38),inset 0 1px 0 rgba(255,255,255,0.07);
    margin-bottom:8px;
}
.chart-title{ font-family:'Inter',sans-serif; font-size:14px; font-weight:700; color:white; margin-bottom:4px; }
.chart-sub  { font-size:11px; color:#64748b; margin-bottom:2px; }

/* ── Filter bar ── */
.filter-bar {
    background:linear-gradient(145deg,rgba(255,255,255,0.06),rgba(255,255,255,0.025));
    border:1px solid rgba(255,255,255,0.1); border-radius:16px; padding:16px 20px;
    box-shadow:0 4px 20px rgba(0,0,0,0.35),inset 0 1px 0 rgba(255,255,255,0.08);
    margin-bottom:24px;
}

/* ── Page label/title ── */
.page-label{ color:#6366f1; font-size:11px; font-weight:700; letter-spacing:2px; text-transform:uppercase; margin-bottom:4px; }
.page-title{ font-family:'Inter',sans-serif; font-size:28px; font-weight:800; color:white; margin-bottom:4px; line-height:1.2; }
.page-title span{ color:#34d399; }
.page-desc { color:#64748b; font-size:14px; margin-bottom:20px; line-height:1.55; }
.badge-row { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:24px; }
.badge-pill{ display:inline-flex; align-items:center; gap:6px; font-size:12px; font-weight:600; padding:6px 14px; border-radius:99px; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════
#  BANCO DE DADOS
# ══════════════════════════════════════════
if not DATABASE_URL:
    st.error("DATABASE_URL não encontrada no .env")
    st.stop()

engine = create_engine(DATABASE_URL)

@st.cache_data
def load_places():
    return pd.read_sql("SELECT * FROM places", engine)

df_places = load_places()
if df_places.empty:
    st.warning("Nenhum dado encontrado na tabela places.")
    st.stop()

df_places["cost_benefit"] = (
    df_places["average_rating"] / df_places["average_price_level"].replace(0, pd.NA)
).fillna(0)


# ══════════════════════════════════════════
#  CONSTANTS & HELPERS
# ══════════════════════════════════════════
CATEGORY_ICON  = {"gastronomia":"🍽️","lazer":"🎯","cultura":"🎭"}
CATEGORY_COLOR = {"gastronomia":"#f59e0b","lazer":"#3b82f6","cultura":"#8b5cf6"}
CATEGORY_BG    = {
    "gastronomia":"linear-gradient(135deg,#78350f,#451a03)",
    "lazer":      "linear-gradient(135deg,#1e3a5f,#0c1e3a)",
    "cultura":    "linear-gradient(135deg,#3b1a6b,#1a0a30)",
}
PRICE_LABEL = {1:"$",2:"$$",3:"$$$",4:"$$$$"}
BADGE_STYLES = [
    ("Melhor escolha",        "#065f46","#34d399"),
    ("Ótimo custo-benefício", "#1e3a5f","#60a5fa"),
    ("Mais popular",          "#4c1d95","#c4b5fd"),
]
CMAP     = {"gastronomia":"#6366f1","lazer":"#22c55e","cultura":"#f59e0b"}
LEGEND_H = dict(orientation="h",x=0.5,xanchor="center",y=-0.14,
                bgcolor="rgba(0,0,0,0)",font=dict(color="#94a3b8",size=11))
XAXIS_BASE = dict(showgrid=True,gridcolor="rgba(255,255,255,0.05)",gridwidth=1,
                  linecolor="rgba(255,255,255,0.08)",tickfont=dict(color="#64748b",size=11),
                  title_font=dict(color="#94a3b8",size=12),zeroline=False)
YAXIS_BASE = dict(showgrid=True,gridcolor="rgba(255,255,255,0.05)",gridwidth=1,
                  linecolor="rgba(255,255,255,0.08)",tickfont=dict(color="#64748b",size=11),
                  title_font=dict(color="#94a3b8",size=12),zeroline=False)
PLOT_BASE = dict(
    plot_bgcolor ="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter",color="#94a3b8",size=12),
    hoverlabel=dict(bgcolor="rgba(15,23,42,0.95)",bordercolor="rgba(255,255,255,0.12)",
                    font=dict(color="white",size=12)),
)


def haversine(lat1,lon1,lat2,lon2):
    R=6371; dl,dlo=math.radians(lat2-lat1),math.radians(lon2-lon1)
    a=math.sin(dl/2)**2+math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlo/2)**2
    return round(R*2*math.asin(math.sqrt(a)),1)


@st.cache_data(ttl=1800)
def get_weather(lat=-8.0476,lon=-34.8770):
    if not WEATHER_API_KEY:
        return {"temp":28,"description":"clima tropical","icon_url":"https://openweathermap.org/img/wn/02d@2x.png"}
    try:
        url=(f"https://api.openweathermap.org/data/2.5/weather"
             f"?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric&lang=pt_br")
        r=requests.get(url,timeout=8); r.raise_for_status(); d=r.json()
        temp=round(d.get("main",{}).get("temp",28))
        w=d.get("weather",[{}])[0]
        return {"temp":temp,"description":w.get("description","").capitalize(),
                "icon_url":f"https://openweathermap.org/img/wn/{w.get('icon','02d')}@2x.png"}
    except Exception:
        return {"temp":28,"description":"clima indisponível","icon_url":"https://openweathermap.org/img/wn/02d@2x.png"}


HERO_BG_URL=(
    "https://commons.wikimedia.org/wiki/Special:FilePath/"
    "Marco%20Zero%20-%20Recife%20Antigo%20-%20Recife%2C%20Pernambuco%2C%20Brasil%20%28foto%20Panor%C3%A2mica%20night%29.jpg"
)
PLACE_IMAGE_BY_CATEGORY={
    "gastronomia":"https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=500&q=80",
    "lazer":"https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=500&q=80",
    "cultura":"https://commons.wikimedia.org/wiki/Special:FilePath/Pra%C3%A7a%20Rio%20Branco%20%C3%A0%20noite%2C%20Recife%20%28PE%29.jpg",
}
PLACE_IMAGE_BY_SUBCATEGORY={
    "restaurante":"https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=500&q=80",
    "bar":"https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=500&q=80",
    "café":"https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=500&q=80",
    "parque":"https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=500&q=80",
    "museu":"https://images.unsplash.com/photo-1566127992631-137a642a90f4?auto=format&fit=crop&w=500&q=80",
    "teatro":"https://images.unsplash.com/photo-1503095396549-807759245b35?auto=format&fit=crop&w=500&q=80",
    "shopping":"https://images.unsplash.com/photo-1519567241046-7f570eee3ce6?auto=format&fit=crop&w=500&q=80",
}

def _safe_get(data,key,default=None):
    try:
        if data is None:
            return default
        value=data.get(key,default)
        if pd.isna(value):
            return default
        return value
    except Exception:
        return default

def get_place_image(name,category,subcategory=None,row=None):
    for col in ["photo_url","image_url","thumbnail_url","place_photo_url"]:
        v=_safe_get(row,col)
        if v: return str(v)
    ref=_safe_get(row,"photo_reference")
    if ref and GOOGLE_MAPS_API_KEY:
        return f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=500&photo_reference={ref}&key={GOOGLE_MAPS_API_KEY}"
    sub=str(subcategory or _safe_get(row,"subcategory","") or "").lower().strip()
    cat=str(category or _safe_get(row,"category","") or "").lower().strip()
    if sub in PLACE_IMAGE_BY_SUBCATEGORY: return PLACE_IMAGE_BY_SUBCATEGORY[sub]
    return PLACE_IMAGE_BY_CATEGORY.get(cat,"https://images.unsplash.com/photo-1494526585095-c41746248156?auto=format&fit=crop&w=500&q=80")


def kpi_card(label,value,subtitle,icon,accent,bg,delay="0s"):
    st.markdown(f"""
<div class="kpi-card" style="animation-delay:{delay};border-top:2px solid {accent};">
  <div class="kpi-top">
    <div class="kpi-label">{label}</div>
    <div class="kpi-icon-wrap" style="background:{bg};">{icon}</div>
  </div>
  <div class="kpi-value">{value}</div>
  <div class="kpi-sub">{subtitle}</div>
</div>""",unsafe_allow_html=True)

def rec_card(name,category,neighborhood,rating,price_level,distance_km,badge_idx,compat_pct,image_url=None):
    style=BADGE_STYLES[badge_idx%len(BADGE_STYLES)]
    pl=PRICE_LABEL.get(int(price_level) if price_level else 2,"$$")
    c_col="#22c55e" if compat_pct>=90 else "#f59e0b"
    if image_url is None: image_url=get_place_image(name,category)
    st.markdown(f"""
<div class="rec-card">
  <div class="rec-img" style="background-image:linear-gradient(rgba(0,0,0,.08),rgba(0,0,0,.35)),url('{image_url}');background-size:cover;background-position:center;"></div>
  <div class="rec-body">
    <span class="rec-badge" style="background:{style[1]};color:{style[2]};">{style[0]}</span>
    <div class="rec-name" title="{name}">{name}</div>
    <div class="rec-meta">⭐ {rating} &nbsp;·&nbsp; {pl} · {neighborhood}<br>📏 {distance_km} km de você</div>
    <span class="rec-compat" style="background:rgba(34,197,94,0.12);color:{c_col};">{compat_pct}% compatível</span>
  </div>
</div>""",unsafe_allow_html=True)

def rank_item(pos,name,neighborhood,category,rating,price_level,score,delay="0s",image_url=None):
    medals={1:("🥇","rgba(251,191,36,0.15)","#fbbf24"),
            2:("🥈","rgba(148,163,184,0.15)","#94a3b8"),
            3:("🥉","rgba(180,83,9,0.15)","#f97316")}
    medal,bg,color=medals.get(pos,(f"#{pos}","rgba(99,102,241,0.1)","#6366f1"))
    pl=PRICE_LABEL.get(int(price_level) if price_level else 2,"$$")
    if image_url is None: image_url=get_place_image(name,category)
    st.markdown(f"""
<div class="rank-item" style="animation-delay:{delay};">
  <div class="rank-num" style="background:{bg};color:{color};">{medal}</div>
  <div class="rank-thumb" style="background-image:linear-gradient(rgba(0,0,0,.05),rgba(0,0,0,.25)),url('{image_url}');background-size:cover;background-position:center;"></div>
  <div class="rank-info">
    <div class="rank-name" title="{name}">{name}</div>
    <div class="rank-meta">{pl} · {neighborhood} · ⭐ {rating}</div>
  </div>
  <div class="rank-score">{score}<small>score</small></div>
</div>""",unsafe_allow_html=True)

def insight_item(icon,icon_bg,text,delay="0s"):
    st.markdown(f"""
<div class="insight-item" style="animation-delay:{delay};">
  <div class="ins-icon" style="background:{icon_bg};">{icon}</div>
  <div class="ins-text">{text}</div>
</div>""",unsafe_allow_html=True)

def create_smart_map(df,recommendations=None,user_lat=None,user_lon=None):
    clat=user_lat if user_lat else (df["latitude"].mean() if not df.empty else -8.0476)
    clon=user_lon if user_lon else (df["longitude"].mean() if not df.empty else -34.877)
    m=folium.Map(location=[clat,clon],zoom_start=12,tiles="CartoDB dark_matter")
    cl=MarkerCluster().add_to(m)
    if user_lat and user_lon:
        folium.Marker([user_lat,user_lon],popup="Você está aqui",
            icon=folium.Icon(color="red",icon="user")).add_to(m)
    rec_ids={r["id"] for r in recommendations} if recommendations else set()
    if recommendations and user_lat:
        for r in recommendations:
            rows=df[df["id"]==r["id"]]
            if not rows.empty:
                row=rows.iloc[0]
                folium.PolyLine([[user_lat,user_lon],[row["latitude"],row["longitude"]]],
                    color="#22c55e",weight=2,opacity=0.5).add_to(m)
    cc={"gastronomia":"red","lazer":"blue","cultura":"purple"}
    for _,row in df.iterrows():
        is_rec=row["id"] in rec_ids
        folium.Marker([row["latitude"],row["longitude"]],
            popup=f"<b>{row['name']}</b><br>⭐{row['average_rating']} | {row['category']}",
            tooltip=f"{row['name']} ⭐{row['average_rating']}",
            icon=folium.Icon(color="green" if is_rec else cc.get(row["category"],"gray"),
                             icon="star" if is_rec else "info-sign")).add_to(cl)
    return m

def render_filter_bar(df):
    st.markdown('<div class="filter-bar">',unsafe_allow_html=True)
    c1,c2,c3,c4,c5,c6,c7=st.columns([1.2,1.2,1,1.2,1,0.8,0.8])
    ac=sorted(df["category"].dropna().unique())
    sc=c1.selectbox("Categoria",["Todas"]+ac,key="f_cat")
    ds=df if sc=="Todas" else df[df["category"]==sc]
    as_=sorted(ds["subcategory"].dropna().unique())
    ss=c2.selectbox("Subcategoria",["Todas"]+as_,key="f_sub")
    po=sorted(df["average_price_level"].dropna().unique())
    pl={p:PRICE_LABEL.get(int(p),str(p)) for p in po}
    sp=c3.selectbox("Preço",["Todas"]+list(pl.values()),key="f_price")
    an=sorted(df["neighborhood"].dropna().unique())
    sn=c4.selectbox("Bairro",["Todos"]+an,key="f_neigh")
    mr=c5.slider("Avaliação mín.",0.0,5.0,0.0,0.5,key="f_rating")
    c6.markdown("<div style='height:22px'></div>",unsafe_allow_html=True)
    c6.button("Aplicar",use_container_width=True,key="btn_apply")
    c7.markdown("<div style='height:22px'></div>",unsafe_allow_html=True)
    c7.button("Limpar",use_container_width=True,key="btn_clear")
    st.markdown('</div>',unsafe_allow_html=True)
    out=df.copy()
    if sc!="Todas":  out=out[out["category"]==sc]
    if ss!="Todas":  out=out[out["subcategory"]==ss]
    if sp!="Todas":
        inv={v:k for k,v in pl.items()}
        out=out[out["average_price_level"]==inv.get(sp,sp)]
    if sn!="Todos":  out=out[out["neighborhood"]==sn]
    if mr>0:         out=out[out["average_rating"]>=mr]
    return out


# ══════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════
with st.sidebar:
    st.markdown("""
<div style="padding:24px 16px 20px;border-bottom:1px solid rgba(255,255,255,0.06);">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
    <div style="width:32px;height:32px;border-radius:10px;
      background:linear-gradient(135deg,#4f46e5,#0f766e);
      display:flex;align-items:center;justify-content:center;font-size:16px;">📍</div>
    <div>
      <div style="color:white;font-family:'Inter',sans-serif;font-size:14px;font-weight:800;line-height:1.1;">Onde é o Rolê?</div>
      <div style="color:#475569;font-size:10px;letter-spacing:1px;text-transform:uppercase;">Urban Intelligence</div>
    </div>
  </div>
</div>
""",unsafe_allow_html=True)

    st.markdown('<div style="padding:12px 8px 8px;color:#475569;font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;">MENU</div>',unsafe_allow_html=True)

    page=st.radio("nav",
        options=["executiva","explorar","analise","recomendacoes","sobre"],
        format_func=lambda x:{
            "executiva":     "Visão Executiva\nRankings e insights principais",
            "explorar":      "Explorar Recife\nNavegue por todos os locais",
            "analise":       "Análise Exploratória\nPadrões urbanos e tabelas",
            "recomendacoes": "Recomendações\nSugestões personalizadas por perfil",
            "sobre":         "Sobre o Projeto\nMetodologia e visão do produto",
        }[x],
        label_visibility="collapsed",
        key="page_radio")

    st.divider()

    st.markdown(f"""
<div style="padding:0 8px 12px;">
  <div style="color:#475569;font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:10px;">SUA LOCALIZAÇÃO</div>
  <div style="display:flex;align-items:center;gap:8px;">
    <div style="width:8px;height:8px;border-radius:50%;background:#22c55e;flex-shrink:0;box-shadow:0 0 6px rgba(34,197,94,0.6);"></div>
    <div>
      <div style="color:white;font-size:13px;font-weight:600;">{st.session_state.user_neighborhood}</div>
      <div style="color:#475569;font-size:11px;">Recife, PE</div>
    </div>
  </div>
</div>
""",unsafe_allow_html=True)

    with st.expander("📌 Alterar localização"):
        new_lat   =st.number_input("Latitude", value=st.session_state.user_lat, format="%.4f",key="loc_lat")
        new_lon   =st.number_input("Longitude",value=st.session_state.user_lon, format="%.4f",key="loc_lon")
        new_bairro=st.text_input("Bairro",     value=st.session_state.user_neighborhood,      key="loc_bairro")
        if st.button("Atualizar localização",use_container_width=True):
            st.session_state.user_lat=new_lat; st.session_state.user_lon=new_lon
            st.session_state.user_neighborhood=new_bairro; st.rerun()

    st.divider()

    st.markdown(f"""
<div style="padding:0 8px 20px;">
  <div style="color:#475569;font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:12px;">BASE DE DADOS</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:10px;text-align:center;border:1px solid rgba(255,255,255,0.06);">
      <div style="font-family:'Inter',sans-serif;font-size:20px;font-weight:800;color:white;">{len(df_places)}</div>
      <div style="color:#475569;font-size:10px;">lugares</div>
    </div>
    <div style="background:rgba(255,255,255,0.04);border-radius:10px;padding:10px;text-align:center;border:1px solid rgba(255,255,255,0.06);">
      <div style="font-family:'Inter',sans-serif;font-size:20px;font-weight:800;color:white;">{df_places['neighborhood'].nunique()}</div>
      <div style="color:#475569;font-size:10px;">bairros</div>
    </div>
  </div>
</div>
<div style="padding:0 8px 8px;color:#2d3748;font-size:11px;text-align:center;border-top:1px solid rgba(255,255,255,0.04);padding-top:14px;">
  Urban Intelligence © 2024
</div>
""",unsafe_allow_html=True)


# ══════════════════════════════════════════
#  PAGE: VISÃO EXECUTIVA
# ══════════════════════════════════════════
if page=="executiva":
    weather=get_weather(st.session_state.user_lat,st.session_state.user_lon)
    st.markdown(f"""
<div style="background-image:linear-gradient(90deg,rgba(5,10,20,0.96) 0%,rgba(8,16,31,0.88) 42%,rgba(8,16,31,0.42) 78%,rgba(8,16,31,0.22) 100%),url('{HERO_BG_URL}');
  background-size:cover;background-position:center right;
  border-radius:24px;padding:38px 42px 34px;margin-bottom:24px;
  border:1px solid rgba(255,255,255,0.09);
  box-shadow:0 24px 70px rgba(0,0,0,0.65),inset 0 1px 0 rgba(255,255,255,0.08);
  position:relative;overflow:hidden;">
<div style="position:absolute;inset:0;background:radial-gradient(circle at 75% 22%,rgba(56,189,248,0.16),transparent 32%),radial-gradient(circle at 48% 80%,rgba(16,185,129,0.13),transparent 35%);pointer-events:none;"></div>
<div style="position:absolute;top:22px;right:24px;z-index:2;">
  <div style="display:flex;align-items:center;gap:10px;background:rgba(2,6,23,0.55);border:1px solid rgba(255,255,255,0.12);backdrop-filter:blur(14px);padding:10px 14px;border-radius:16px;box-shadow:0 8px 28px rgba(0,0,0,0.35);">
    <img src="{weather['icon_url']}" style="width:42px;height:42px;object-fit:contain;">
    <div>
      <div style="color:white;font-size:22px;font-weight:900;line-height:1;">{weather['temp']}°C</div>
      <div style="color:#cbd5e1;font-size:11px;line-height:1.2;">{weather['description']} · Recife, PE</div>
    </div>
  </div>
</div>
<div style="position:relative;z-index:1;max-width:650px;">
  <div class="page-label">● Recife Antigo — Inteligência Urbana</div>
  <h1 style="font-family:'Inter',sans-serif;color:white;font-size:42px;font-weight:900;margin:0 0 10px;line-height:1.08;letter-spacing:-1.3px;">
    Descubra experiências incríveis<br>em <span style="color:#34d399;">Recife</span>
  </h1>
  <p style="color:#cbd5e1;font-size:16px;max-width:600px;line-height:1.65;margin-bottom:24px;">
    Análise inteligente de restaurantes, lazer e cultura com base em dados reais, clima atual e recomendações personalizadas.
  </p>
  <div class="badge-row">
    <span class="badge-pill" style="background:rgba(99,102,241,0.18);color:#c7d2fe;border:1px solid rgba(99,102,241,0.28);">🔵 Google Places API</span>
    <span class="badge-pill" style="background:rgba(16,185,129,0.14);color:#6ee7b7;border:1px solid rgba(16,185,129,0.22);">🟢 Dados Reais</span>
    <span class="badge-pill" style="background:rgba(139,92,246,0.16);color:#ddd6fe;border:1px solid rgba(139,92,246,0.24);">🟣 Recomendação Inteligente</span>
    <span class="badge-pill" style="background:rgba(245,158,11,0.13);color:#fde68a;border:1px solid rgba(245,158,11,0.22);">🌦️ Clima em tempo real</span>
  </div>
</div>
</div>
""",unsafe_allow_html=True)

    filtered_df=render_filter_bar(df_places)
    if filtered_df.empty:
        st.warning("Nenhum lugar encontrado com os filtros aplicados."); st.stop()

    avg_r=round(filtered_df["average_rating"].mean(),2)
    best_cb=round(filtered_df["cost_benefit"].max(),2)
    avg_p=round(filtered_df["average_price_level"].mean(),1)

    k1,k2,k3,k4=st.columns(4)
    with k1: kpi_card("Lugares encontrados",len(filtered_df),"Total de estabelecimentos","📍","#6366f1","rgba(99,102,241,0.15)","0s")
    with k2: kpi_card("Avaliação média",avg_r,"Baseado em avaliações reais","⭐","#f59e0b","rgba(245,158,11,0.15)","0.08s")
    with k3: kpi_card("Melhor custo-benefício",best_cb,"Score máximo encontrado","🏆","#22c55e","rgba(34,197,94,0.15)","0.16s")
    with k4: kpi_card("Preço médio",avg_p,"Faixa de preço (1–4)","💰","#fb923c","rgba(251,146,60,0.15)","0.24s")

    st.markdown("<br>",unsafe_allow_html=True)

    map_col,rec_col=st.columns([3,2])
    with map_col:
        st.markdown('<div class="section-card">',unsafe_allow_html=True)
        st.markdown('<div class="section-title">🗺️ Mapa inteligente das experiências</div>',unsafe_allow_html=True)
        mapa=create_smart_map(filtered_df,user_lat=st.session_state.user_lat,user_lon=st.session_state.user_lon)
        st_folium(mapa,width=None,height=440,use_container_width=True)
        st.markdown("""
<div style="display:flex;gap:16px;flex-wrap:wrap;margin-top:12px;padding-top:12px;border-top:1px solid rgba(255,255,255,0.06);">
  <span style="color:#94a3b8;font-size:12px;">🔴 Gastronomia</span>
  <span style="color:#94a3b8;font-size:12px;">🔵 Lazer</span>
  <span style="color:#94a3b8;font-size:12px;">🟣 Cultura</span>
  <span style="color:#94a3b8;font-size:12px;">🟢 Recomendação</span>
  <span style="color:#94a3b8;font-size:12px;">🔴 Você</span>
</div>""",unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)

    with rec_col:
        st.markdown('<div class="section-card">',unsafe_allow_html=True)
        st.markdown('<div class="section-title">✨ Recomendado para você</div>',unsafe_allow_html=True)
        top_recs=filtered_df.sort_values("cost_benefit",ascending=False).head(5)
        for i,(_,row) in enumerate(top_recs.iterrows()):
            dist=haversine(st.session_state.user_lat,st.session_state.user_lon,row["latitude"],row["longitude"])
            compat=min(99,int(75+row["average_rating"]*5-i*2))
            rec_card(row["name"],row["category"],row["neighborhood"],
                     row["average_rating"],row["average_price_level"],dist,i,compat,
                     image_url=get_place_image(row["name"],row["category"],row.get("subcategory"),row))
        st.markdown('<div style="text-align:center;padding-top:8px;"><span style="color:#6366f1;font-size:13px;font-weight:600;cursor:pointer;">Ver mais recomendações →</span></div>',unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)

    st.markdown("<br>",unsafe_allow_html=True)

    cb_col,ins_col=st.columns(2)
    with cb_col:
        st.markdown('<div class="section-card">',unsafe_allow_html=True)
        st.markdown('<div class="section-title">💰 Melhor custo-benefício</div>',unsafe_allow_html=True)
        for i,(_,row) in enumerate(filtered_df.sort_values("cost_benefit",ascending=False).head(3).iterrows(),1):
            rank_item(i,row["name"],row["neighborhood"],row["category"],
                      row["average_rating"],row["average_price_level"],
                      round(row["cost_benefit"],2),f"{i*0.08}s",
                      image_url=get_place_image(row["name"],row["category"],row.get("subcategory"),row))
        st.markdown('</div>',unsafe_allow_html=True)

    with ins_col:
        st.markdown('<div class="section-card">',unsafe_allow_html=True)
        st.markdown('<div class="section-title">🧠 Insights inteligentes</div>',unsafe_allow_html=True)
        best_neigh  =filtered_df.groupby("neighborhood")["average_rating"].mean().idxmax()
        best_neigh_r=filtered_df.groupby("neighborhood")["average_rating"].mean().max()
        top_sub     =filtered_df.groupby("subcategory")["average_rating"].mean().idxmax() if "subcategory" in filtered_df.columns else "–"
        price_mode  =filtered_df["average_price_level"].value_counts().idxmax()
        price_pct   =int(filtered_df["average_price_level"].value_counts(normalize=True).max()*100)
        best_cb_cat =filtered_df.groupby("category")["cost_benefit"].mean().idxmax()
        insight_item("📍","rgba(99,102,241,0.15)",f"<strong>{best_neigh}</strong> concentra as melhores avaliações ({best_neigh_r:.2f} ⭐).","0s")
        insight_item("🍽️","rgba(245,158,11,0.15)",f"Faixa <strong>{PRICE_LABEL.get(int(price_mode),'média')}</strong> tem melhor avaliação — {price_pct}% dos lugares.","0.06s")
        insight_item("⭐","rgba(16,185,129,0.15)",f"<strong>{top_sub}</strong> é a subcategoria com maior satisfação.","0.12s")
        insight_item("💡","rgba(139,92,246,0.15)",f"Categoria <strong>{best_cb_cat}</strong> tem melhor equilíbrio qualidade × preço.","0.18s")
        st.markdown('</div>',unsafe_allow_html=True)


# ══════════════════════════════════════════
#  PAGE: EXPLORAR
# ══════════════════════════════════════════
elif page=="explorar":
    render_explorar(df_places,get_image_fn=get_place_image)


# ══════════════════════════════════════════
#  PAGE: ANÁLISE EXPLORATÓRIA
# ══════════════════════════════════════════
elif page=="analise":

    st.markdown('<div class="page-label">📊 ANÁLISE</div>',unsafe_allow_html=True)
    st.markdown('<div class="page-title">Análise <span>Exploratória</span></div>',unsafe_allow_html=True)
    st.markdown('<div class="page-desc">Padrões, distribuições e correlações nos dados urbanos de Recife.</div>',unsafe_allow_html=True)

    filtered_df=render_filter_bar(df_places)
    if filtered_df.empty:
        st.warning("Nenhum dado com os filtros atuais."); st.stop()

    # ── KPIs da página ──
    total    =len(filtered_df)
    avg_rat  =round(filtered_df["average_rating"].mean(),2)
    avg_pri  =round(filtered_df["average_price_level"].mean(),1)
    top_neigh=filtered_df.groupby("neighborhood")["average_rating"].mean().idxmax()

    def mini_kpi(label,value,accent):
        st.markdown(f"""
<div style="background:linear-gradient(145deg,rgba(255,255,255,.07),rgba(255,255,255,.02));
  border:1px solid rgba(255,255,255,.09);border-radius:14px;padding:18px 20px;
  box-shadow:0 4px 16px rgba(0,0,0,.35),inset 0 1px 0 rgba(255,255,255,.07);
  border-top:2px solid {accent};">
  <div style="color:#64748b;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:8px;">{label}</div>
  <div style="color:white;font-family:'Inter',sans-serif;font-size:26px;font-weight:800;line-height:1;">{value}</div>
</div>""",unsafe_allow_html=True)

    m1,m2,m3,m4=st.columns(4)
    with m1: mini_kpi("Locais analisados",total,"#6366f1")
    with m2: mini_kpi("Avaliação média",f"{avg_rat} ⭐","#f59e0b")
    with m3: mini_kpi("Preço médio",f"{avg_pri}/4","#22c55e")
    with m4: mini_kpi("Bairro destaque",top_neigh,"#8b5cf6")

    st.markdown("<br>",unsafe_allow_html=True)

    def cc(content):
        """Wrapper de card glassmorphism para gráficos."""
        st.markdown("""<div style="background:linear-gradient(145deg,rgba(255,255,255,.055),rgba(255,255,255,.018));
  border:1px solid rgba(255,255,255,.09);border-radius:16px;padding:4px 8px 0;
  box-shadow:0 6px 24px rgba(0,0,0,.38),inset 0 1px 0 rgba(255,255,255,.07);">""",unsafe_allow_html=True)
        content()
        st.markdown("</div>",unsafe_allow_html=True)

    # ── LINHA 1: Donut | Avaliação por cat | Preço ──
    r1c1,r1c2,r1c3=st.columns(3)

    with r1c1:
        cat_c=filtered_df["category"].value_counts().reset_index(); cat_c.columns=["category","count"]
        fig=px.pie(cat_c,values="count",names="category",hole=0.62,color="category",color_discrete_map=CMAP)
        fig.update_traces(textinfo="none",
            hovertemplate="<b>%{label}</b><br>%{value} locais (%{percent})<extra></extra>")
        fig.add_annotation(text=f"<b>{total}</b><br>locais",x=0.5,y=0.5,showarrow=False,
            font=dict(size=18,color="white",family="Inter"))
        fig.update_layout(**PLOT_BASE,height=310,showlegend=True,
            legend=dict(**LEGEND_H),
            title=dict(text="Distribuição por categoria",font=dict(color="white",size=14,family="Inter"),x=0),
            margin=dict(t=48,b=60,l=10,r=10))
        def _f1(): st.plotly_chart(fig,use_container_width=True)
        cc(_f1)

    with r1c2:
        avg_cat=(filtered_df.groupby("category")["average_rating"].mean()
                 .reset_index().sort_values("average_rating",ascending=True))
        n=len(avg_cat)
        bar_cols=[f"rgba(99,102,241,{0.45+0.55*(i/max(n-1,1)):.2f})" for i in range(n)]
        fig2=px.bar(avg_cat,x="average_rating",y="category",orientation="h",
                    text=avg_cat["average_rating"].map("{:.2f}".format))
        fig2.update_traces(marker_color=bar_cols,marker_line_width=0,
            textposition="outside",textfont=dict(color="white",size=13),
            hovertemplate="<b>%{y}</b><br>Avaliação: %{x:.2f}<extra></extra>")
        fig2.update_layout(**PLOT_BASE,height=310,showlegend=False,
            xaxis=dict(**XAXIS_BASE,range=[3.5,5.3],title="Avaliação"),
            yaxis=dict(**YAXIS_BASE,title=""),
            title=dict(text="Avaliação média por categoria",font=dict(color="white",size=14,family="Inter"),x=0),
            margin=dict(t=48,b=36,l=10,r=50))
        def _f2(): st.plotly_chart(fig2,use_container_width=True)
        cc(_f2)

    with r1c3:
        price_d=(filtered_df["average_price_level"].value_counts().sort_index().reset_index())
        price_d.columns=["price","count"]
        price_d["label"]=price_d["price"].map({1:"$ Econômico",2:"$$ Moderado",3:"$$$ Premium",4:"$$$$ Luxo"})
        fig3=px.bar(price_d,x="label",y="count",text="count",
                    color="price",color_continuous_scale=["#6366f1","#22c55e","#f59e0b","#ef4444"])
        fig3.update_traces(marker_line_width=0,textposition="outside",
            textfont=dict(color="white",size=13),
            hovertemplate="<b>%{x}</b><br>%{y} locais<extra></extra>")
        fig3.update_layout(**PLOT_BASE,height=310,showlegend=False,coloraxis_showscale=False,
            xaxis=dict(**XAXIS_BASE,title=""),
            yaxis=dict(**YAXIS_BASE,title="Quantidade"),
            title=dict(text="Distribuição por faixa de preço",font=dict(color="white",size=14,family="Inter"),x=0),
            margin=dict(t=48,b=36,l=40,r=24))
        def _f3(): st.plotly_chart(fig3,use_container_width=True)
        cc(_f3)

    st.markdown("<br>",unsafe_allow_html=True)

    # ── LINHA 2: Scatter (com tendência) | Top Bairros ──
    r2c1,r2c2=st.columns([1.2,1])

    with r2c1:
        fig4=px.scatter(filtered_df,x="average_price_level",y="average_rating",
                        color="category",color_discrete_map=CMAP,
                        hover_data={"name":True,"neighborhood":True,
                                    "average_price_level":False,"average_rating":False},
                        size_max=10)
        fig4.update_traces(marker=dict(size=9,opacity=0.82,line=dict(width=0)),
            hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>"
                          "Preço: %{x} · Avaliação: %{y:.1f}<extra></extra>")
        x_v=filtered_df["average_price_level"].values
        y_v=filtered_df["average_rating"].values
        if len(x_v)>2:
            z=np.polyfit(x_v,y_v,1); p=np.poly1d(z)
            xr=np.linspace(x_v.min(),x_v.max(),50)
            fig4.add_trace(go.Scatter(x=xr,y=p(xr),mode="lines",name="Tendência",
                line=dict(color="rgba(255,255,255,0.3)",width=1.5,dash="dot"),showlegend=True))
        fig4.update_layout(**PLOT_BASE,height=360,
            xaxis=dict(**XAXIS_BASE,title="Faixa de preço",
                       tickvals=[1,2,3,4],ticktext=["$","$$","$$$","$$$$"]),
            yaxis=dict(**YAXIS_BASE,title="Avaliação",range=[2.5,5.3]),
            title=dict(text="Avaliação × Preço por categoria",font=dict(color="white",size=14,family="Inter"),x=0),
            legend=dict(**LEGEND_H),
            margin=dict(t=48,b=60,l=48,r=24))
        def _f4(): st.plotly_chart(fig4,use_container_width=True)
        cc(_f4)

    with r2c2:
        top_b=(filtered_df.groupby("neighborhood")["average_rating"]
               .mean().sort_values(ascending=True).tail(8).reset_index())
        top_b.columns=["neighborhood","avg"]
        n=len(top_b)
        bar_cols2=[f"rgba(99,102,241,{0.3+0.7*(i/max(n-1,1)):.2f})" for i in range(n)]
        fig5=px.bar(top_b,x="avg",y="neighborhood",orientation="h",
                    text=top_b["avg"].map("{:.2f}".format))
        fig5.update_traces(marker_color=bar_cols2,marker_line_width=0,
            textposition="outside",textfont=dict(color="white",size=12),
            hovertemplate="<b>%{y}</b><br>Avaliação média: %{x:.2f}<extra></extra>")
        fig5.update_layout(**PLOT_BASE,height=360,
            xaxis=dict(**XAXIS_BASE,range=[3.5,5.4],title="Avaliação média"),
            yaxis=dict(**YAXIS_BASE,title=""),
            title=dict(text="Top bairros por avaliação",font=dict(color="white",size=14,family="Inter"),x=0),
            margin=dict(t=48,b=36,l=10,r=55))
        def _f5(): st.plotly_chart(fig5,use_container_width=True)
        cc(_f5)

    st.markdown("<br>",unsafe_allow_html=True)

    # ── LINHA 3: Top 10 lugares | Locais por bairro+cat ──
    r3c1,r3c2=st.columns(2)

    with r3c1:
        top_pl=(filtered_df.nlargest(10,"average_rating")
                [["name","average_rating","category"]].sort_values("average_rating"))
        fig6=px.bar(top_pl,x="average_rating",y="name",orientation="h",
                    color="category",color_discrete_map=CMAP,
                    text=top_pl["average_rating"].map("{:.1f}".format))
        fig6.update_traces(marker_line_width=0,textposition="outside",
            textfont=dict(color="white",size=11),
            hovertemplate="<b>%{y}</b><br>Avaliação: %{x:.1f}<extra></extra>")
        fig6.update_layout(**PLOT_BASE,height=380,showlegend=True,
            xaxis=dict(**XAXIS_BASE,range=[3.5,5.5],title="Avaliação"),
            yaxis=dict(**YAXIS_BASE,title=""),
            title=dict(text="Top 10 lugares por avaliação",font=dict(color="white",size=14,family="Inter"),x=0),
            legend=dict(**LEGEND_H),
            margin=dict(t=48,b=60,l=10,r=55))
        def _f6(): st.plotly_chart(fig6,use_container_width=True)
        cc(_f6)

    with r3c2:
        bairro_cat=(filtered_df.groupby(["neighborhood","category"])
                    .size().reset_index(name="count"))
        fig7=px.bar(bairro_cat,x="neighborhood",y="count",color="category",
                    color_discrete_map=CMAP,barmode="stack",text="count")
        fig7.update_traces(marker_line_width=0,textposition="inside",
            textfont=dict(color="white",size=10),
            hovertemplate="<b>%{x}</b><br>%{fullData.name}: %{y}<extra></extra>")
        fig7.update_layout(**PLOT_BASE,height=380,
            xaxis=dict(**XAXIS_BASE,title="",tickangle=-30),
            yaxis=dict(**YAXIS_BASE,title="Quantidade"),
            title=dict(text="Locais por bairro e categoria",font=dict(color="white",size=14,family="Inter"),x=0),
            legend=dict(**{**LEGEND_H, "y": -0.2}),
            margin=dict(t=48,b=70,l=40,r=24))
        def _f7(): st.plotly_chart(fig7,use_container_width=True)
        cc(_f7)

    st.markdown("<br>",unsafe_allow_html=True)

    # ── TABELA ──
    st.markdown("""
<div style="color:#94a3b8;font-size:11px;font-weight:700;letter-spacing:2px;
  text-transform:uppercase;margin-bottom:14px;display:flex;align-items:center;gap:10px;">
  📋 TABELA COMPLETA
  <span style="flex:1;height:1px;background:linear-gradient(90deg,rgba(99,102,241,0.4),transparent);"></span>
</div>""",unsafe_allow_html=True)
    st.dataframe(
        filtered_df[["name","category","subcategory","neighborhood",
                     "average_price_level","average_rating","cost_benefit"]]
        .sort_values("average_rating",ascending=False)
        .rename(columns={"name":"Nome","category":"Categoria","subcategory":"Subcategoria",
                         "neighborhood":"Bairro","average_price_level":"Preço",
                         "average_rating":"Avaliação","cost_benefit":"Score C/B"}),
        use_container_width=True,height=320)

    st.markdown("<br><br>",unsafe_allow_html=True)

    # ══════════════════════════════════════════
    #  QUALIDADE DOS DADOS & OUTLIERS
    # ══════════════════════════════════════════
    st.markdown("""
<div style="color:#94a3b8;font-size:11px;font-weight:700;letter-spacing:2px;
  text-transform:uppercase;margin-bottom:14px;display:flex;align-items:center;gap:10px;">
  🔍 QUALIDADE DOS DADOS & OUTLIERS
  <span style="flex:1;height:1px;background:linear-gradient(90deg,rgba(245,158,11,0.4),transparent);"></span>
</div>""",unsafe_allow_html=True)

    def detect_outliers(df,group_col="category",value_col="average_rating"):
        """Detecta outliers por categoria usando o método do IQR (1.5x)."""
        parts=[]
        for _,grp in df.groupby(group_col):
            q1=grp[value_col].quantile(0.25)
            q3=grp[value_col].quantile(0.75)
            iqr=q3-q1
            lower,upper=q1-1.5*iqr,q3+1.5*iqr
            out=grp[(grp[value_col]<lower)|(grp[value_col]>upper)].copy()
            if not out.empty:
                out["limite"]=np.where(out[value_col]<lower,"Abaixo do esperado","Acima do esperado")
                parts.append(out)
        return pd.concat(parts) if parts else df.iloc[0:0]

    outliers_df=detect_outliers(filtered_df)
    pct_foto=(round(filtered_df["photo_url"].notna().sum()/len(filtered_df)*100,1)
              if "photo_url" in filtered_df.columns else None)
    bairro_counts=filtered_df["neighborhood"].value_counts()
    bairro_esparsos=int((bairro_counts<10).sum())

    q1,q2,q3=st.columns(3)
    with q1: mini_kpi("Cobertura de fotos reais",f"{pct_foto}%" if pct_foto is not None else "—","#22c55e")
    with q2: mini_kpi("Bairros com poucos dados (<10)",bairro_esparsos,"#f59e0b")
    with q3: mini_kpi("Outliers de avaliação detectados",len(outliers_df),"#ef4444")

    st.markdown("<br>",unsafe_allow_html=True)

    qc1,qc2=st.columns([1.1,1])

    with qc1:
        fig8=px.box(filtered_df,x="category",y="average_rating",color="category",
                    color_discrete_map=CMAP,points="outliers")
        fig8.update_traces(marker=dict(size=5,opacity=0.7),line=dict(width=1.5))
        fig8.update_layout(**PLOT_BASE,height=340,showlegend=False,
            xaxis=dict(**XAXIS_BASE,title=""),
            yaxis=dict(**YAXIS_BASE,title="Avaliação",range=[1.5,5.3]),
            title=dict(text="Distribuição e outliers por categoria",font=dict(color="white",size=14,family="Inter"),x=0),
            margin=dict(t=48,b=40,l=48,r=24))
        def _f8(): st.plotly_chart(fig8,use_container_width=True)
        cc(_f8)

    with qc2:
        def _f9():
            st.markdown("<div style='padding:14px 16px 6px;'>",unsafe_allow_html=True)
            st.markdown("<div style='color:white;font-size:14px;font-weight:700;margin-bottom:10px;'>"
                        "Lugares fora do padrão (IQR)</div>",unsafe_allow_html=True)
            if outliers_df.empty:
                st.markdown("<div style='color:#64748b;font-size:13px;padding-bottom:14px;'>"
                            "Nenhum outlier detectado com os filtros atuais.</div>",unsafe_allow_html=True)
            else:
                show=outliers_df[["name","average_rating","limite"]].sort_values("average_rating").head(8)
                for _,row in show.iterrows():
                    color="#ef4444" if row["limite"]=="Abaixo do esperado" else "#22c55e"
                    nm=row["name"] if len(row["name"])<=38 else row["name"][:38]+"…"
                    st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;
  border-bottom:1px solid rgba(255,255,255,0.06);">
  <div style="color:#e2e8f0;font-size:12.5px;">{nm}</div>
  <div style="color:{color};font-size:12.5px;font-weight:700;white-space:nowrap;">{row['average_rating']:.1f} ⭐</div>
</div>""",unsafe_allow_html=True)
                st.markdown("<div style='height:6px;'></div>",unsafe_allow_html=True)
            st.markdown("</div>",unsafe_allow_html=True)
        cc(_f9)

    if bairro_esparsos>0:
        st.markdown(f"""
<div style="background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.3);
  border-radius:10px;padding:12px 16px;color:#fcd34d;font-size:13px;margin-top:16px;">
  ⚠️ {bairro_esparsos} bairro(s) têm menos de 10 lugares coletados nos filtros atuais — a média de avaliação
  desses bairros é estatisticamente menos confiável do que a de bairros com mais dados.
</div>""",unsafe_allow_html=True)

    st.markdown("<br><br>",unsafe_allow_html=True)

    # ══════════════════════════════════════════
    #  CLUSTERIZAÇÃO DE BAIRROS (K-Means)
    # ══════════════════════════════════════════
    st.markdown("""
<div style="color:#94a3b8;font-size:11px;font-weight:700;letter-spacing:2px;
  text-transform:uppercase;margin-bottom:6px;display:flex;align-items:center;gap:10px;">
  🧩 CLUSTERIZAÇÃO DE BAIRROS
  <span style="flex:1;height:1px;background:linear-gradient(90deg,rgba(139,92,246,0.4),transparent);"></span>
</div>""",unsafe_allow_html=True)
    st.caption("Agrupamento por K-Means com base em preço médio, avaliação média e mix de categorias de cada bairro.")
    st.markdown("<br>",unsafe_allow_html=True)

    neigh_profile=(filtered_df.groupby("neighborhood")
                   .agg(avg_price=("average_price_level","mean"),
                        avg_rating=("average_rating","mean"),
                        total=("name","count")).reset_index())

    cat_counts=filtered_df.pivot_table(index="neighborhood",columns="category",
                                        values="id",aggfunc="count",fill_value=0)
    cat_pct=cat_counts.div(cat_counts.sum(axis=1),axis=0)
    cat_pct.columns=[f"pct_{c}" for c in cat_pct.columns]
    neigh_profile=neigh_profile.merge(cat_pct.reset_index(),on="neighborhood",how="left").fillna(0)

    n_bairros=len(neigh_profile)

    if n_bairros<4:
        st.info("Poucos bairros nos filtros atuais para agrupar com confiança — amplie os filtros para ver a clusterização.")
    else:
        max_k=min(6,n_bairros-1)
        default_k=min(4,max_k)
        k=st.slider("Número de grupos (K)",2,max_k,default_k,key="cluster_k")

        pct_cols=[c for c in neigh_profile.columns if c.startswith("pct_")]
        feature_cols=["avg_price","avg_rating"]+pct_cols
        X=neigh_profile[feature_cols].values
        X_scaled=StandardScaler().fit_transform(X)

        km=KMeans(n_clusters=k,random_state=42,n_init=10)
        neigh_profile["cluster"]=km.fit_predict(X_scaled).astype(str)

        overall_price=neigh_profile["avg_price"].mean()
        overall_rating=neigh_profile["avg_rating"].mean()

        def label_cluster(row):
            parts=[]
            parts.append("preço elevado" if row["avg_price"]>overall_price else "preço acessível")
            parts.append("bem avaliado" if row["avg_rating"]>overall_rating else "avaliação mediana")
            if pct_cols:
                dom=max(pct_cols,key=lambda c:row.get(c,0))
                parts.append(f"foco em {dom.replace('pct_','')}")
            return ", ".join(parts).capitalize()

        cluster_means=neigh_profile.groupby("cluster")[feature_cols].mean()
        cluster_labels={c:label_cluster(cluster_means.loc[c]) for c in cluster_means.index}
        neigh_profile["cluster_label"]=neigh_profile["cluster"].map(cluster_labels)

        cl_colors=["#6366f1","#22c55e","#f59e0b","#ef4444","#06b6d4","#ec4899"]
        color_map={str(i):cl_colors[i%len(cl_colors)] for i in range(k)}

        clc1,clc2=st.columns([1.3,1])

        with clc1:
            fig9=px.scatter(neigh_profile,x="avg_price",y="avg_rating",
                            color="cluster",color_discrete_map=color_map,
                            size="total",size_max=28,hover_name="neighborhood",
                            hover_data={"cluster":False,"total":True})
            fig9.update_traces(marker=dict(line=dict(width=1,color="rgba(255,255,255,0.3)")))
            fig9.update_layout(**PLOT_BASE,height=380,showlegend=False,
                xaxis=dict(**XAXIS_BASE,title="Preço médio"),
                yaxis=dict(**YAXIS_BASE,title="Avaliação média"),
                title=dict(text="Bairros agrupados por perfil",font=dict(color="white",size=14,family="Inter"),x=0),
                margin=dict(t=48,b=40,l=48,r=24))
            def _f9(): st.plotly_chart(fig9,use_container_width=True)
            cc(_f9)

        with clc2:
            def _f10():
                st.markdown("<div style='padding:14px 16px 6px;'>",unsafe_allow_html=True)
                st.markdown("<div style='color:white;font-size:14px;font-weight:700;margin-bottom:12px;'>"
                            "Grupos encontrados</div>",unsafe_allow_html=True)
                for c in sorted(neigh_profile["cluster"].unique(),key=int):
                    bairros_c=neigh_profile[neigh_profile["cluster"]==c]["neighborhood"].tolist()
                    color=color_map[c]
                    st.markdown(f"""
<div style="margin-bottom:14px;">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
    <div style="width:10px;height:10px;border-radius:50%;background:{color};flex-shrink:0;"></div>
    <div style="color:white;font-size:13px;font-weight:700;">{cluster_labels[c]}</div>
  </div>
  <div style="color:#94a3b8;font-size:12px;padding-left:18px;">{", ".join(bairros_c)}</div>
</div>""",unsafe_allow_html=True)
                st.markdown("</div>",unsafe_allow_html=True)
            cc(_f10)



# ══════════════════════════════════════════
#  PAGE: RECOMENDAÇÕES
# ══════════════════════════════════════════
elif page=="recomendacoes":
    st.markdown('<div class="page-label">🎯 RECOMENDAÇÕES</div>',unsafe_allow_html=True)
    st.markdown('<div class="page-title">Encontre seu <span>próximo rolê</span></div>',unsafe_allow_html=True)
    st.markdown('<div class="page-desc">Personalize sua busca e descubra os melhores lugares com base no seu perfil.</div>',unsafe_allow_html=True)

    form_col,result_col=st.columns([1,1.4])
    with form_col:
        st.markdown('<div class="section-card">',unsafe_allow_html=True)
        st.markdown('<div class="section-title">⚙️ Suas preferências</div>',unsafe_allow_html=True)
        with st.form("rec_form"):
            pref_cat=st.selectbox("Categoria",options=sorted(df_places["category"].dropna().unique()))
            subs=sorted(df_places[df_places["category"]==pref_cat]["subcategory"].dropna().unique())
            pref_sub=st.selectbox("Subcategoria",options=subs if subs else [""])
            budget=st.selectbox("Faixa de preço",options=[1,2,3,4],
                format_func=lambda x:{1:"$ — Econômico",2:"$$ — Moderado",3:"$$$ — Sofisticado",4:"$$$$ — Premium"}[x],index=1)
            c1,c2=st.columns(2)
            ulat=c1.number_input("Latitude", value=st.session_state.user_lat, format="%.4f")
            ulon=c2.number_input("Longitude",value=st.session_state.user_lon, format="%.4f")
            city=st.text_input("Cidade",value="Recife")
            submitted=st.form_submit_button("🔍 Buscar recomendações")
        st.markdown('</div>',unsafe_allow_html=True)
        if submitted:
            st.session_state.user_lat=ulat; st.session_state.user_lon=ulon; st.session_state.searched=True
            try:
                resp=requests.post("http://127.0.0.1:8000/recommendations/",
                    json={"preferred_category":pref_cat,"preferred_subcategory":pref_sub,
                          "budget_preference":budget,"user_latitude":ulat,"user_longitude":ulon,"city":city},timeout=10)
                if resp.status_code==200:
                    st.session_state.recommendations=resp.json()
                    if not st.session_state.recommendations: st.warning("Nenhuma recomendação encontrada.")
                else: st.error(f"Erro na API: {resp.status_code}")
            except requests.exceptions.ConnectionError: st.error("FastAPI offline. Rode: uvicorn main:app --reload")
            except Exception as e: st.error(f"Erro: {e}")

    with result_col:
        if st.session_state.searched and st.session_state.recommendations:
            st.success(f"✅ {len(st.session_state.recommendations)} recomendações encontradas!")
            st.markdown("<br>",unsafe_allow_html=True)
            for i,item in enumerate(st.session_state.recommendations):
                dist=haversine(st.session_state.user_lat,st.session_state.user_lon,
                    item.get("lat",st.session_state.user_lat),item.get("lon",st.session_state.user_lon)) if "lat" in item else "–"
                rec_card(item["name"],item.get("category",""),item.get("neighborhood",""),
                    item.get("rating","–"),item.get("price_level",2),dist,i,
                    min(99,int(60+item.get("score",0)*10)),
                    image_url=get_place_image(item["name"],item.get("category",""),item.get("subcategory",""),item))
                if item.get("reason"): st.caption(f"💬 {item['reason']}")
            st.markdown("<br>",unsafe_allow_html=True)
            st.markdown('<div class="section-title">🗺️ Mapa das recomendações</div>',unsafe_allow_html=True)
            mapa_rec=create_smart_map(df_places,recommendations=st.session_state.recommendations,
                user_lat=st.session_state.user_lat,user_lon=st.session_state.user_lon)
            st_folium(mapa_rec,width=None,height=420,use_container_width=True)
        elif st.session_state.searched:
            st.info("Nenhuma recomendação encontrada para os critérios selecionados.")
        else:
            st.markdown("""
<div style="text-align:center;padding:60px 20px;color:#475569;">
  <div style="font-size:56px;margin-bottom:16px;">🎯</div>
  <div style="font-family:'Inter',sans-serif;font-size:18px;font-weight:800;color:#64748b;margin-bottom:8px;">Suas recomendações aparecem aqui</div>
  <div style="font-size:14px;">Preencha suas preferências ao lado e clique em buscar.</div>
</div>""",unsafe_allow_html=True)


# ══════════════════════════════════════════
#  PAGE: SOBRE
# ══════════════════════════════════════════
elif page=="sobre":
    st.markdown('<div class="page-label">ℹ️ SOBRE</div>',unsafe_allow_html=True)
    st.markdown('<div class="page-title">Sobre o <span>Projeto</span></div>',unsafe_allow_html=True)
    c1,c2=st.columns([1.2,1])
    with c1:
        ti="".join([f'<div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.07);border-radius:10px;padding:10px 14px;font-size:13px;color:#cbd5e1;"><span style="color:#6366f1;font-weight:700;">{t}</span><br><span style="color:#475569;font-size:11px;">{d}</span></div>' for t,d in [
            ("Streamlit","Frontend & Dashboard"),("FastAPI","Backend & Recomendação"),
            ("PostgreSQL","Banco de dados"),("Supabase","Cloud & Hosting"),
            ("Google Places","Coleta de dados"),("Folium","Mapas interativos"),
            ("Plotly","Visualizações"),("Pandas","Análise de dados")]])
        st.markdown(f'<div class="section-card"><div class="section-title">🧬 O que é o Onde é o Rolê?</div><p style="color:#94a3b8;font-size:14px;line-height:1.75;margin-bottom:16px;">Plataforma de inteligência urbana focada em Recife que combina dados reais do <strong style="color:white;">Google Places API</strong> com algoritmos de recomendação para ajudar pessoas a descobrir experiências urbanas com a melhor relação custo-benefício.</p><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">{ti}</div></div>',unsafe_allow_html=True)
    with c2:
        si="".join([f'<div style="display:flex;justify-content:space-between;padding:11px 0;border-bottom:1px solid rgba(255,255,255,0.05);"><span style="color:#94a3b8;font-size:13px;">{l}</span><span style="font-family:Inter,sans-serif;font-weight:800;color:white;font-size:15px;">{v}</span></div>' for l,v in [
            ("Total de lugares",len(df_places)),("Bairros mapeados",df_places["neighborhood"].nunique()),
            ("Categorias",df_places["category"].nunique()),("Avaliação média",f"{df_places['average_rating'].mean():.2f} ⭐"),
            ("Metodologia","CRISP-DM"),("Versão","1.0.0")]])
        st.markdown(f'<div class="section-card"><div class="section-title">📊 Estatísticas</div>{si}</div>',unsafe_allow_html=True)
